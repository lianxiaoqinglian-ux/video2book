"""Single-thread metadata/subtitle worker. Never synthesizes missing course facts."""
import json, sqlite3, sys, os, fcntl
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from . import create_app, normalize_url
from .storage import safe_path
from .generation import enabled, generate_book, _atomic
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/video2book'))
from src.core.parser import BilibiliParser
from src.core.subtitles import fetch_episode_subtitle

def _read_cache(path):
    try:
        value=json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value,dict) else None
    except (OSError,ValueError):
        return None

def _write_cache(path,value):
    temp=path.with_suffix('.new.json')
    with temp.open('w',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False)
        f.flush();os.fsync(f.fileno())
    os.replace(temp,path)

def run_once(data_dir):
    root=create_app(data_dir).config['DATA_ROOT']
    # Ubuntu target: one cross-process lock guards claim, recovery and writes.
    with safe_path(root,'worker.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return False
        return _run_locked(root)

def _run_locked(root):
    with sqlite3.connect(root/'library.sqlite3') as c:
        c.row_factory=sqlite3.Row
        c.execute('BEGIN IMMEDIATE')
        c.execute("UPDATE tasks SET status='queued' WHERE status='processing'")
        eligible = "('queued','waiting_writer')" if enabled() else "('queued')"
        row=c.execute("SELECT * FROM tasks WHERE status IN "+eligible+" ORDER BY rowid LIMIT 1").fetchone()
        if not row:return False
        c.execute("UPDATE tasks SET status='processing' WHERE id=?",(row['id'],))
    tid=row['id'];status='failed';message=''
    try:
        source=normalize_url(row['source']);p=urlsplit(source)
        bvid=p.path.rsplit('/',1)[-1];page=int(parse_qs(p.query).get('p',['1'])[0])
        meta=safe_path(root,tid+'_metadata.json');transcript=safe_path(root,tid+'_transcript.json')
        info=_read_cache(meta)
        if info is None:
            info=BilibiliParser.parse_video(source,sessdata=None)
            _write_cache(meta,info)
        selected=next((part for part in info.get('parts',[]) if part.get('page')==page),None)
        if not selected:raise ValueError('元数据没有指定分集')
        if not 0<float(selected.get('duration',0))<=1800:
            status='waiting_input';message='第一阶段仅处理单集30分钟以内；需要人工确认范围。'
        else:
            sub=_read_cache(transcript)
            if sub is None:
                diagnosis={}
                sub=fetch_episode_subtitle(bvid,int(selected['cid']),sessdata=None,duration_sec=float(selected['duration']),次数=1,诊断=diagnosis)
                if sub:_write_cache(transcript,sub)
                elif '接口请求异常' in str(diagnosis.get('reason','')):raise RuntimeError('字幕网络接口失败：'+str(diagnosis['reason']))
            if sub and sub.get('trustworthy') is True:
                status='waiting_writer';message='已缓存真实平台字幕及时间线，等待教材写作；尚未生成教材。'
                if enabled():
                    generated=generate_book(root,tid,selected,sub)
                    body=generated['markdown'].read_text(encoding='utf-8')
                    _atomic(safe_path(root,tid+'.md'),body)
                    status='completed';message='由SiliconFlow模型按原版learning提示词生成，已通过本块机器门禁；原声准确性、画面完整性及练习答案未人工核查。来源为真实平台字幕，时间线保存在字幕侧车。'
            else:status='waiting_input';message=('已取得字幕但可信性未通过，需要人工核查；未转换。' if sub else '匿名接口没有可用中文字幕，需要真实字幕或听音通道；未转换。')
        title=selected.get('title') or info.get('title') or row['title']
    except Exception as e:
        title=row['title'];message='处理失败：'+str(e)[:500]
    with sqlite3.connect(root/'library.sqlite3') as c:
        c.execute('UPDATE tasks SET status=?,title=?,provenance=? WHERE id=?',(status,title,message,tid))
    with safe_path(root,tid+'_events.jsonl').open('a',encoding='utf-8') as log:
        log.write(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'status':status,'message':message},ensure_ascii=False)+'\n')
    return True
