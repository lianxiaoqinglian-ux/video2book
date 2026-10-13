import argparse
from . import create_app, import_book

def main():
    p=argparse.ArgumentParser(description='本地私人教材库');p.add_argument('--data-dir',required=True);p.add_argument('--port',type=int,default=8765)
    sub=p.add_subparsers(dest='command');i=sub.add_parser('import-book');i.add_argument('--title',required=True);i.add_argument('--source-url',required=True);i.add_argument('--markdown',required=True);i.add_argument('--provenance',required=True);i.add_argument('--task-id');i.add_argument('--assets-dir')
    w=sub.add_parser('worker');w.add_argument('--loop',action='store_true')
    a=p.parse_args()
    if a.command=='import-book':print(import_book(a.data_dir,a.title,a.source_url,a.markdown,a.provenance,a.task_id,a.assets_dir))
    elif a.command=='worker':
        from .worker import run_once
        import time
        while True:
            worked=run_once(a.data_dir)
            if not a.loop:break
            if not worked:time.sleep(2)
    else:create_app(a.data_dir).run(host='127.0.0.1',port=a.port,debug=False)
if __name__=='__main__':main()
