import json, re, shutil
from pathlib import Path

def safe_path(root, name):
    root=Path(root)
    if root.is_symlink() or any(p.is_symlink() for p in [root,*root.parents]):raise ValueError('禁止符号链接')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+',name) or name in ('.','..'):raise ValueError('非法文件名')
    path=root/name
    if path.is_symlink():raise ValueError('禁止符号链接')
    return path

def copy_assets(root,tid,directory):
    source=Path(directory)
    if any(p.is_symlink() for p in [source,*source.parents]):raise ValueError('禁止符号链接')
    dest=safe_path(root,tid+'_assets');dest.mkdir(exist_ok=True)
    for p in source.iterdir():
        if p.is_symlink():raise ValueError('禁止符号链接')
        if p.suffix.lower() not in ('.png','.jpg','.jpeg'):continue
        if p.stat().st_size>5*1024*1024:raise ValueError('图片超过5MB')
        target=safe_path(dest,p.name)
        if p.is_file():shutil.copyfile(p,target)

def local_images(text,tid):
    def rewrite(m):
        name=m[2]
        if re.fullmatch(r'[A-Za-z0-9_.-]+\.(?:png|jpg|jpeg)',name,re.I):
            return '!['+m[1]+'](/tasks/'+tid+'/assets/'+name+')'
        return m[0]
    return re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',rewrite,text)
