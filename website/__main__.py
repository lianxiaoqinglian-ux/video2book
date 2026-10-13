import argparse
from . import create_app, import_book

def main():
    import sys
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/video2book'))
    from src.core.console import enable_utf8_console
    enable_utf8_console()
    p=argparse.ArgumentParser(description='本地私人教材库');p.add_argument('--data-dir',required=True);p.add_argument('--port',type=int,default=8765)
    sub=p.add_subparsers(dest='command');i=sub.add_parser('import-book');i.add_argument('--title',required=True);i.add_argument('--source-url',required=True);i.add_argument('--markdown',required=True);i.add_argument('--provenance',required=True);i.add_argument('--task-id');i.add_argument('--assets-dir')
    w=sub.add_parser('worker');w.add_argument('--loop',action='store_true')
    d=sub.add_parser('provider-check');d.add_argument('--live',action='store_true')
    a=p.parse_args()
    if a.command=='provider-check':
        from .provider_check import check_provider
        import json
        result=check_provider(a.live);print(json.dumps(result,ensure_ascii=False,indent=2))
        if a.live and not result['live_model_verified']:raise SystemExit(1)
    elif a.command=='import-book':print(import_book(a.data_dir,a.title,a.source_url,a.markdown,a.provenance,a.task_id,a.assets_dir))
    elif a.command=='worker':
        from .worker import run_once
        import time
        while True:
            worked=run_once(a.data_dir)
            if not a.loop:break
            if not worked:time.sleep(2)
    else:create_app(a.data_dir).run(host='127.0.0.1',port=a.port,debug=False)
if __name__=='__main__':main()
