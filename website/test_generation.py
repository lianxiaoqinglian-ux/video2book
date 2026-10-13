"""New adapter contract tests; synthetic owned teaching fixtures, not course conversion."""
import json, sqlite3
from pathlib import Path
import pytest
from website import create_app

SOURCE='MySQL DB DBMS SQL SELECT：数据库持久保存数据，DBMS是管理软件，SQL用于表达查询。\n'*35
BOOK='# 数据库入门\n\n'+('MySQL DB DBMS SQL SELECT：数据库是数据集合，管理软件通过SQL查询数据。\n\n'*35)

@pytest.fixture
def configured(tmp_path,monkeypatch):
    monkeypatch.setenv('BOOKSITE_PASSWORD','local-test')
    monkeypatch.setenv('SILICONFLOW_API_KEY','test-key-not-real')
    monkeypatch.setenv('BOOKSITE_AUTO_WRITE','1')
    create_app(tmp_path)
    return tmp_path

class Reply:
    status_code=200
    def __init__(self,content=BOOK,finish='stop'):self.content,self.finish=content,finish
    def json(self):return {'choices':[{'finish_reason':self.finish,'message':{'content':self.content}}],'usage':{'prompt_tokens':100,'completion_tokens':200,'total_tokens':300}}

def payload():return {'title':'入门','page':1,'cid':123,'duration':300}
def captions():return {'trustworthy':True,'cues':[{'from':0,'to':300,'content':SOURCE}]}

def test_real_contract_and_resume(configured,monkeypatch):
    from website.generation import generate_book
    calls=[]
    def post(url,**kw):
        calls.append(kw)
        assert url=='https://api.siliconflow.cn/v1/chat/completions'
        assert kw['allow_redirects'] is False and kw['timeout']==(10,180)
        assert kw['headers']['Authorization']=='Bearer test-key-not-real'
        assert kw['json']['model']=='Qwen/Qwen3.5-122B-A10B'
        assert SOURCE in kw['json']['messages'][1]['content']
        return Reply()
    monkeypatch.setattr('website.generation.requests.post',post)
    first=generate_book(configured,'a'*32,payload(),captions())
    second=generate_book(configured,'a'*32,payload(),captions())
    assert first['status']=='accepted' and second['status']=='accepted' and len(calls)==1
    assert first['grounding']['status']=='ok' and first['usage']['total_tokens']==300
    assert first['markdown'].read_text()==BOOK

@pytest.mark.parametrize('reply',[Reply('摘要'),Reply(BOOK,'length'),Reply('无关内容\n'*400)])
def test_rejects_bad_or_truncated(configured,monkeypatch,reply):
    from website.generation import generate_book,GenerationError
    monkeypatch.setattr('website.generation.requests.post',lambda *a,**k:reply)
    with pytest.raises(GenerationError):generate_book(configured,'b'*32,payload(),captions())

@pytest.mark.parametrize('code',[401,402,403,429,500])
def test_http_failures_are_safe(configured,monkeypatch,code):
    from website.generation import generate_book,GenerationError
    response=Reply();response.status_code=code
    monkeypatch.setattr('website.generation.requests.post',lambda *a,**k:response)
    with pytest.raises(GenerationError) as e:generate_book(configured,'c'*32,payload(),captions())
    assert str(code) in str(e.value) and 'test-key-not-real' not in str(e.value)

def test_missing_key_or_untrusted_makes_no_call(configured,monkeypatch):
    from website.generation import generate_book,GenerationError
    monkeypatch.setattr('website.generation.requests.post',lambda *a,**k:pytest.fail('no request permitted'))
    monkeypatch.delenv('SILICONFLOW_API_KEY')
    with pytest.raises(GenerationError):generate_book(configured,'d'*32,payload(),captions())
    monkeypatch.setenv('SILICONFLOW_API_KEY','test-key-not-real')
    with pytest.raises(GenerationError):generate_book(configured,'d'*32,payload(),{'trustworthy':False,'cues':[]})

def test_timeout_does_not_blindly_rebill(configured,monkeypatch):
    import requests
    from website.generation import generate_book,GenerationError
    calls=[]
    def timed_out(*a,**kw):calls.append(1);raise requests.Timeout()
    monkeypatch.setattr('website.generation.requests.post',timed_out)
    for _ in range(2):
        with pytest.raises(GenerationError):generate_book(configured,'e'*32,payload(),captions())
    assert len(calls)==1

def test_worker_uses_cached_captions_to_publish(configured,monkeypatch):
    from website import worker
    tid='f'*32
    with sqlite3.connect(configured/'library.sqlite3') as c:
        c.execute('INSERT INTO tasks(id,title,source,status,provenance) VALUES(?,?,?,?,?)',(tid,'课','https://www.bilibili.com/video/BV14VqVBrEhc','waiting_writer','真实字幕缓存'))
    (configured/(tid+'_metadata.json')).write_text(json.dumps({'parts':[payload()]}))
    (configured/(tid+'_transcript.json')).write_text(json.dumps(captions()))
    monkeypatch.setattr(worker.BilibiliParser,'parse_video',lambda *a,**kw:pytest.fail('metadata must be reused'))
    monkeypatch.setattr(worker,'fetch_episode_subtitle',lambda *a,**kw:pytest.fail('captions must be reused'))
    monkeypatch.setattr('website.generation.requests.post',lambda *a,**kw:Reply())
    assert worker.run_once(configured)
    with sqlite3.connect(configured/'library.sqlite3') as c:assert c.execute('SELECT status FROM tasks WHERE id=?',(tid,)).fetchone()[0]=='completed'
    assert (configured/(tid+'.md')).read_text().find('数据库入门')>=0
    assert worker.run_once(configured) is False

def test_provider_probe_lists_only_requested_model(monkeypatch):
    from website.provider_check import check_provider
    monkeypatch.setenv('SILICONFLOW_API_KEY','not-a-real-key')
    class Inventory:
        status_code=200
        def json(self):return {'data':[{'id':'Qwen/Qwen3.5-122B-A10B'}]}
    monkeypatch.setattr('website.provider_check.requests.get',lambda *a,**kw:Inventory())
    r=check_provider(live=True)
    assert r['live_model_verified'] and not r['inference_tested'] and not r['price_verified']
    assert 'not-a-real-key' not in str(r)

def test_provider_probe_no_key_does_not_request(monkeypatch):
    from website.provider_check import check_provider
    monkeypatch.delenv('SILICONFLOW_API_KEY',raising=False)
    monkeypatch.setattr('website.provider_check.requests.get',lambda *a,**kw:pytest.fail('missing key must not be sent'))
    assert check_provider(live=True)['status']=='missing_key'
