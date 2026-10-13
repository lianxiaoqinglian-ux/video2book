"""Small authenticated local textbook library."""
import os, re, secrets, sqlite3, hmac
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from functools import wraps
import bleach, markdown
from flask import Flask, request, session, abort, redirect, url_for, render_template_string, send_file

STYLE='<style>body{max-width:960px;margin:40px auto;padding:0 20px;font:18px/1.7 sans-serif}input{padding:8px;width:70%}button{padding:8px}pre{overflow:auto}img{max-width:100%}</style>'

def normalize_url(value):
    p=urlsplit(value.strip())
    if p.scheme!='https' or p.netloc not in ('www.bilibili.com','bilibili.com') or p.fragment:
        raise ValueError('请提交 https://www.bilibili.com/video/BV… 链接')
    m=re.fullmatch(r'/video/(BV[0-9A-Za-z]{10})/?',p.path)
    if not m: raise ValueError('仅支持规范 Bilibili 视频链接')
    q=parse_qs(p.query,keep_blank_values=True)
    if p.query and (set(q)!={'p'} or len(q['p'])!=1 or not q['p'][0].isdigit() or not 1<=int(q['p'][0])<=10000):raise ValueError('非法分集参数')
    return 'https://www.bilibili.com/video/'+m[1]+(('?p='+str(int(q['p'][0]))) if q else '')

def create_app(data_dir):
    password=os.environ.get('BOOKSITE_PASSWORD')
    if not password: raise RuntimeError('请设置 BOOKSITE_PASSWORD')
    from .storage import safe_path, local_images
    original=Path(data_dir).absolute()
    if any(p.is_symlink() for p in [original,*original.parents]):raise ValueError('禁止符号链接')
    root=original.resolve(); root.mkdir(parents=True,exist_ok=True)
    root.chmod(0o700)
    key=safe_path(root,'secret.key')
    safe_path(root,'library.sqlite3')
    try:
        fd=os.open(key,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as f:f.write(secrets.token_hex(32))
    except FileExistsError: pass
    app=Flask(__name__); app.secret_key=key.read_text().strip()
    app.config.update(SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Strict',MAX_CONTENT_LENGTH=1024*1024)
    app.config['DATA_ROOT']=root
    def db():
        c=sqlite3.connect(root/'library.sqlite3');c.row_factory=sqlite3.Row;return c
    with db() as c:
        c.execute('CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY,title TEXT,source TEXT,status TEXT,provenance TEXT,created TEXT DEFAULT CURRENT_TIMESTAMP)')
    def auth(fn):
        @wraps(fn)
        def wrapped(*a,**kw):
            if not session.get('logged_in'): return redirect(url_for('login'))
            return fn(*a,**kw)
        return wrapped
    @app.before_request
    def csrf():
        session.setdefault('csrf',secrets.token_urlsafe(32))
        if request.method=='POST' and not hmac.compare_digest(request.form.get('csrf',''),session['csrf']):abort(403)
    @app.after_request
    def security_headers(response):
        response.headers["Content-Security-Policy"]="default-src 'self'; style-src 'unsafe-inline'; img-src 'self'; frame-ancestors 'none'; form-action 'self'"
        response.headers["X-Content-Type-Options"]="nosniff"
        response.headers["Referrer-Policy"]="no-referrer"
        response.headers["Cache-Control"]="no-store"
        return response
    def page(body,**kw):
        return render_template_string(STYLE+'<a href="/">教材库</a> '+body,csrf=session['csrf'],**kw)
    def task(tid):
        with db() as c:r=c.execute('SELECT * FROM tasks WHERE id=?',(tid,)).fetchone()
        if not r:abort(404)
        return r
    @app.route('/login',methods=['GET','POST'])
    def login():
        error=''
        if request.method=='POST':
            if hmac.compare_digest(request.form.get('password','').encode(),password.encode()):
                session.clear();session['logged_in']=True;session['csrf']=secrets.token_urlsafe(32)
                return redirect(url_for('index'))
            error='密码错误'
        return page('<h1>登录</h1><p>{{error}}</p><form method="post"><input type="hidden" name="csrf" value="{{csrf}}"><input type="password" name="password" required><button>登录</button></form>',error=error)
    @app.post('/logout')
    @auth
    def logout():session.clear();return redirect(url_for('login'))
    @app.route('/',methods=['GET','POST'])
    @auth
    def index():
        error=''
        if request.method=='POST':
            try: source=normalize_url(request.form.get('url',''))
            except ValueError as e:error=str(e)
            else:
                with db() as c:existing=c.execute('SELECT id FROM tasks WHERE source=? ORDER BY rowid LIMIT 1',(source,)).fetchone()
                if existing:return redirect(url_for('detail',tid=existing['id']))
                tid=secrets.token_hex(16)
                with db() as c:c.execute('INSERT INTO tasks(id,title,source,status,provenance) VALUES(?,?,?,?,?)',(tid,'待处理课程',source,'queued','尚未转换：等待 worker 获取元数据和字幕；缺字幕时需要真实输入，不自动转录。'))
                return redirect(url_for('detail',tid=tid))
        with db() as c:rows=c.execute('SELECT * FROM tasks ORDER BY created DESC,rowid DESC').fetchall()
        return page('<h1>私人视频教材库</h1><p>提交链接保存任务；当前版本需要导入真实教材，不自动调用转录或模型。</p><p>{{error}}</p><form method="post"><input type="hidden" name="csrf" value="{{csrf}}"><input name="url" placeholder="https://www.bilibili.com/video/BV…" required><button>提交</button></form><h2>历史任务</h2>{% for t in rows %}<p><a href="{{url_for(\'detail\',tid=t.id)}}">{{t.title}}</a> — {{t.status}}</p>{% endfor %}<form action="/logout" method="post"><input type="hidden" name="csrf" value="{{csrf}}"><button>退出</button></form>',rows=rows,error=error)
    @app.get('/tasks/<tid>')
    @auth
    def detail(tid):
        r=task(tid);html=''
        if r['status']=='completed':
            raw=safe_path(root,r['id']+'.md').read_text(encoding='utf-8')
            html=bleach.clean(markdown.markdown(local_images(raw,tid),extensions=['tables','fenced_code']),tags=set(bleach.sanitizer.ALLOWED_TAGS)|{'p','h1','h2','h3','h4','h5','h6','pre','br','hr','table','thead','tbody','tr','th','td','img'},attributes={'a':['href','title'],'img':['src','alt','title']},protocols=['https','http'],strip=True)
        return page('<h1>{{t.title}}</h1><p>状态：{{t.status}}</p><p>来源：<a href="{{t.source}}">{{t.source}}</a></p><p>{{t.provenance}}</p>{% if t.status=="completed" %}<a href="{{url_for(\'download\',tid=t.id)}}">下载 Markdown</a><article>{{html|safe}}</article>{% else %}<form method="post" action="{{url_for(\'retry\',tid=t.id)}}"><input type="hidden" name="csrf" value="{{csrf}}"><button>重试（保留产物）</button></form>{% endif %}',t=r,html=html)
    @app.get('/tasks/<tid>/download')
    @auth
    def download(tid):
        r=task(tid)
        if r['status']=='processing':abort(409)
        if r['status']!='completed':abort(409)
        return send_file(safe_path(root,r['id']+'.md'),as_attachment=True,download_name='textbook.md')
    @app.post('/tasks/<tid>/retry')
    @auth
    def retry(tid):
        r=task(tid)
        if r['status']=='processing':abort(409)
        if r['status']!='completed':
            with db() as c:
                changed=c.execute("UPDATE tasks SET status=? WHERE id=? AND status NOT IN ('processing','completed')",('queued',tid)).rowcount
                if not changed:abort(409)
        return redirect(url_for('detail',tid=tid))
    @app.get('/tasks/<tid>/assets/<name>')
    @auth
    def asset(tid,name):
        r=task(tid)
        if r["status"]!="completed":abort(409)
        if not re.fullmatch(r"[A-Za-z0-9_.-]+\.(png|jpg|jpeg)",name,re.I):abort(404)
        try:p=safe_path(safe_path(root,r["id"]+"_assets"),name)
        except ValueError:abort(404)
        if not p.is_file():abort(404)
        return send_file(p)
    return app

def import_book(data_dir,title,source_url,markdown_path,provenance,task_id=None,assets_dir=None):
    from .storage import safe_path, copy_assets
    app=create_app(data_dir);root=app.config['DATA_ROOT'];source=normalize_url(source_url)
    path=Path(markdown_path).absolute()
    if any(p.is_symlink() for p in [path,*path.parents]):raise ValueError('禁止符号链接')
    text=path.read_text(encoding='utf-8')
    if not text.strip():raise ValueError('教材不能为空')
    tid=task_id or secrets.token_hex(16)
    with sqlite3.connect(root/'library.sqlite3') as c:
        c.execute('BEGIN IMMEDIATE')
        existing=c.execute('SELECT source,status FROM tasks WHERE id=?',(tid,)).fetchone()
        if task_id and (not existing or existing[0]!=source):raise ValueError('任务不存在或来源不一致')
        if existing and existing[1]=='processing':raise ValueError('任务正在处理，请稍后导入')
        target=safe_path(root,tid+'.md')
        if assets_dir:copy_assets(root,tid,assets_dir)
        temp=safe_path(root,tid+'.new.md')
        with temp.open('w',encoding='utf-8') as f:
            f.write(text);f.flush();os.fsync(f.fileno())
        temp.chmod(0o600);os.replace(temp,target)
        if task_id:c.execute('UPDATE tasks SET title=?,status=?,provenance=? WHERE id=?',(title,'completed',provenance,tid))
        else:c.execute('INSERT INTO tasks(id,title,source,status,provenance) VALUES(?,?,?,?,?)',(tid,title,source,'completed',provenance))
    return tid
