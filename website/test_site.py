import pytest
from website import create_app, import_book, normalize_url
@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('BOOKSITE_PASSWORD','test-secret')
    app=create_app(tmp_path);app.config['TESTING']=True
    return app.test_client(),tmp_path

def login(c):
    c.get('/login')
    with c.session_transaction() as s: token=s['csrf']
    assert c.post('/login',data={'password':'test-secret','csrf':token}).status_code==302
    with c.session_transaction() as s:return s['csrf']

@pytest.mark.parametrize('url',['http://www.bilibili.com/video/BV14VqVBrEhc','https://localhost/video/BV14VqVBrEhc','https://www.bilibili.com@evil.com/video/BV14VqVBrEhc','https://www.bilibili.com:443/video/BV14VqVBrEhc','https://www.bilibili.com/../../etc/passwd'])
def test_reject_urls(url):
    with pytest.raises(ValueError):normalize_url(url)

def test_waiting_retry(client):
    c,root=client
    assert c.get('/').status_code==302
    assert c.post('/',data={}).status_code==403
    token=login(c)
    r=c.post('/',data={'csrf':token,'url':'https://www.bilibili.com/video/BV14VqVBrEhc'})
    location=r.headers['Location'];page=c.get(location).get_data(as_text=True)
    assert 'queued' in page and '不自动转录' in page
    assert c.post(location+'/retry',data={'csrf':token}).status_code==302
    assert c.get(location+'/download').status_code==409

def test_import_auth_download_sanitize(client,tmp_path):
    c,root=client;src=tmp_path/'source.md';src.write_text('# 教材\n<script>alert(1)</script>\n[危险](javascript:alert(1))',encoding='utf-8')
    tid=import_book(root,'真实教材','https://www.bilibili.com/video/BV14VqVBrEhc',src,'真实逐字稿转换；视频画面尚未验证')
    assert c.get('/tasks/'+tid+'/download').status_code==302
    login(c)
    page=c.get('/tasks/'+tid).get_data(as_text=True)
    assert '<script>' not in page and 'href="javascript:' not in page and '真实逐字稿' in page
    assert c.get('/tasks/'+tid+'/download').data==src.read_bytes()
    assert c.get('/tasks/unknown').status_code==404
    assert c.get('/tasks/../../etc/passwd/download').status_code==404

def test_password_required(tmp_path,monkeypatch):
    monkeypatch.delenv('BOOKSITE_PASSWORD',raising=False)
    with pytest.raises(RuntimeError):create_app(tmp_path)

def test_page_dedup_import_assets(client,tmp_path):
    c,root=client;token=login(c);url='https://www.bilibili.com/video/BV14VqVBrEhc?p=2'
    r=c.post('/',data={'csrf':token,'url':url});location=r.headers['Location'];tid=location.rsplit('/',1)[-1]
    assert c.post('/',data={'csrf':token,'url':url}).headers['Location']==location
    assets=tmp_path/'images';assets.mkdir();(assets/'chart.png').write_bytes(b'PNG-test')
    book=tmp_path/'book.md';book.write_text('# 知识\n![图](chart.png)',encoding='utf-8')
    with pytest.raises(ValueError):import_book(root,'课',url,book,'真实',task_id='missing')
    with pytest.raises(ValueError):import_book(root,'课',url.replace('p=2','p=1'),book,'真实',task_id=tid)
    import_book(root,'课',url,book,'真实',task_id=tid,assets_dir=assets)
    assert '/tasks/'+tid+'/assets/chart.png' in c.get(location).get_data(as_text=True)
    assert c.get(location+'/assets/chart.png').data==b'PNG-test'
    c.post('/logout',data={'csrf':token})
    assert c.get(location+'/assets/chart.png').status_code==302
    assert normalize_url(url)==url

def test_symlinks(client,tmp_path):
    c,root=client;book=tmp_path/'book.md';book.write_text('real');link=tmp_path/'link.md';link.symlink_to(book)
    with pytest.raises(ValueError):import_book(root,'课','https://www.bilibili.com/video/BV14VqVBrEhc',link,'真实')
    linked=tmp_path/'linked';linked.symlink_to(root,target_is_directory=True)
    with pytest.raises(ValueError):create_app(linked)

@pytest.mark.parametrize('mode,expected',[('good','waiting_writer'),('none','waiting_input'),('network','failed'),('long','waiting_input')])
def test_worker_cache_and_boundary(client,monkeypatch,mode,expected):
    from website import worker
    import sqlite3
    c,root=client;token=login(c)
    r=c.post('/',data={'csrf':token,'url':'https://www.bilibili.com/video/BV14VqVBrEhc?p=2'});tid=r.headers['Location'].rsplit('/',1)[-1]
    calls=[]
    def metadata(source,**kw):
        calls.append(source)
        if mode=='network':raise OSError('network denied')
        return {'title':'course','parts':[{'page':1,'cid':1,'duration':30},{'page':2,'title':'第二集','cid':2,'duration':1900 if mode=='long' else 1500}]}
    def subtitle(bvid,cid,**kw):
        assert cid==2 and kw['sessdata'] is None
        return {'trustworthy':True,'cues':[{'from':0,'to':15,'content':'真实字幕'}]} if mode=='good' else None
    monkeypatch.setattr(worker.BilibiliParser,'parse_video',metadata)
    monkeypatch.setattr(worker,'fetch_episode_subtitle',subtitle)
    assert worker.run_once(root)
    with sqlite3.connect(root/'library.sqlite3') as db:assert db.execute('SELECT status FROM tasks WHERE id=?',(tid,)).fetchone()[0]==expected
    if mode=='good':
        c.post('/tasks/'+tid+'/retry',data={'csrf':token})
        monkeypatch.setattr(worker.BilibiliParser,'parse_video',lambda *a,**k:pytest.fail('metadata was repeated'))
        monkeypatch.setattr(worker,'fetch_episode_subtitle',lambda *a,**k:pytest.fail('subtitle was repeated'))
        assert worker.run_once(root)
        assert len(calls)==1

def test_untrusted_subtitle_waits(client,monkeypatch):
    from website import worker
    c,root=client;token=login(c)
    r=c.post('/',data={'csrf':token,'url':'https://www.bilibili.com/video/BV14VqVBrEhc'})
    monkeypatch.setattr(worker.BilibiliParser,'parse_video',lambda *a,**k:{'parts':[{'page':1,'cid':1,'duration':300}]})
    monkeypatch.setattr(worker,'fetch_episode_subtitle',lambda *a,**k:{'trustworthy':False,'cues':[{'from':0,'to':300,'content':'内容'}]})
    worker.run_once(root)
    assert 'waiting_input' in c.get(r.headers['Location']).get_data(as_text=True)

def test_restart_recovers_processing_and_corrupt_cache(client,monkeypatch):
    from website import worker
    import sqlite3
    c,root=client;token=login(c)
    r=c.post('/',data={'csrf':token,'url':'https://www.bilibili.com/video/BV14VqVBrEhc'})
    tid=r.headers['Location'].rsplit('/',1)[-1]
    with sqlite3.connect(root/'library.sqlite3') as db:db.execute("UPDATE tasks SET status='processing' WHERE id=?",(tid,))
    (root/(tid+'_metadata.json')).write_text('{interrupted')
    monkeypatch.setattr(worker.BilibiliParser,'parse_video',lambda *a,**k:{'parts':[{'page':1,'cid':1,'duration':300}]})
    monkeypatch.setattr(worker,'fetch_episode_subtitle',lambda *a,**k:None)
    assert worker.run_once(root)
    assert 'waiting_input' in c.get(r.headers['Location']).get_data(as_text=True)

def test_active_retry_refused(client):
    import sqlite3
    c,root=client;token=login(c)
    r=c.post('/',data={'csrf':token,'url':'https://www.bilibili.com/video/BV14VqVBrEhc'})
    tid=r.headers['Location'].rsplit('/',1)[-1]
    with sqlite3.connect(root/'library.sqlite3') as db:db.execute("UPDATE tasks SET status='processing' WHERE id=?",(tid,))
    assert c.post(r.headers['Location']+'/retry',data={'csrf':token}).status_code==409

def test_worker_lock_prevents_duplicate_claim(client):
    import fcntl
    from website import worker
    c,root=client;token=login(c)
    r=c.post('/',data={'csrf':token,'url':'https://www.bilibili.com/video/BV14VqVBrEhc'})
    with (root/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert worker.run_once(root) is False
        assert 'queued' in c.get(r.headers['Location']).get_data(as_text=True)

def test_active_book_import_refused(client,tmp_path):
    import sqlite3
    c,root=client;token=login(c);url='https://www.bilibili.com/video/BV14VqVBrEhc'
    r=c.post('/',data={'csrf':token,'url':url});tid=r.headers['Location'].rsplit('/',1)[-1]
    with sqlite3.connect(root/'library.sqlite3') as db:db.execute("UPDATE tasks SET status='processing' WHERE id=?",(tid,))
    src=tmp_path/'article.md';src.write_text('实际教材')
    with pytest.raises(ValueError):import_book(root,'课',url,src,'真实来源',task_id=tid)
