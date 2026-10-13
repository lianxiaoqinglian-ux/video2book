"""Local, private, checksum-verified backups; no upload or credential storage."""
from __future__ import annotations
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import stat
import sys
import tempfile
import zipfile

MANIFEST = 'backup-manifest.json'
ALLOWED = {'.md', '.html', '.txt', '.json', '.png', '.jpg', '.jpeg', '.webp', '.svg', '.sqlite', '.sqlite3', '.db'}
BLOCKED = {'.git', '.aws', '.ssh', '.codex', '.agents', '__pycache__'}
SENSITIVE_NAME = re.compile(r'(^|[._-])(secret|secrets|credential|credentials|cookie|cookies|token|tokens|password|signed[-_]?urls?)([._-]|$)|^\.env', re.I)
SENSITIVE_DATA = re.compile(rb'-----BEGIN (?:\w+ )?PRIVATE KEY-----|[?&](?:x-amz-signature|x-goog-signature|signature|token|access_token|auth_key|wssecret|w_rid|sign)=|["\'](?:password|passwd|secret|client_secret|api[_-]?key|access_token|token|cookie|cookies|sessdata|bili_jct|authorization|private_key)["\']\s*:\s*["\'][^"\']+', re.I)


def no_links(path: Path):
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError('Symbolic links are forbidden')


def safe_name(name):
    p = PurePosixPath(name)
    if not name or '\\' in name or '\x00' in name or p.is_absolute() or '..' in p.parts or ':' in name or str(p) != name:
        raise ValueError('Unsafe archive path')
    return name


def digest(data):
    return hashlib.sha256(data).hexdigest()


def create_backup(source, destination):
    source, destination = Path(source).absolute(), Path(destination).absolute()
    no_links(source); no_links(destination)
    source, destination = source.resolve(), destination.resolve()
    if not source.is_dir() or destination == source or source in destination.parents:
        raise ValueError('Destination must be outside the source directory')
    if destination.exists():
        raise ValueError('Destination already exists')
    entries, excluded = {}, []
    with tempfile.TemporaryDirectory() as temporary:
        for path in sorted(source.rglob('*')):
            no_links(path)
            if path.is_dir():
                continue
            name = safe_name(path.relative_to(source).as_posix())
            if name == MANIFEST or any(p in BLOCKED or SENSITIVE_NAME.search(p) for p in path.relative_to(source).parts) or path.suffix.lower() not in ALLOWED:
                excluded.append(name); continue
            if not path.is_file():
                raise ValueError('Only regular files are supported')
            if path.suffix.lower() in {'.sqlite', '.sqlite3', '.db'}:
                snapshot = Path(temporary) / 'snapshot.sqlite3'
                with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as original, closing(sqlite3.connect(snapshot)) as backup:
                    original.backup(backup)
                    backup.execute('PRAGMA journal_mode=DELETE')
                data = snapshot.read_bytes()
                snapshot.unlink()
            else:
                data = path.read_bytes()
            if SENSITIVE_DATA.search(data):
                excluded.append(name); continue
            entries[name] = data
        if not entries:
            raise ValueError('No eligible files')
        manifest = {'version': 1, 'files': {n: {'sha256': digest(d), 'size': len(d)} for n, d in entries.items()}, 'excluded': excluded}
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, 'wb') as output, zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
                for name, data in entries.items():
                    info = zipfile.ZipInfo(name); info.external_attr = (stat.S_IFREG | 0o600) << 16
                    archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED)
                archive.writestr(MANIFEST, json.dumps(manifest, ensure_ascii=False, sort_keys=True))
            verify_backup(destination)
        except BaseException:
            destination.unlink(missing_ok=True)
            raise
    return manifest


def verify_backup(archive_path, restored_dir=None):
    archive_path = Path(archive_path); no_links(archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        for info in archive.infolist():
            safe_name(info.filename)
            if stat.S_ISLNK(info.external_attr >> 16) or info.is_dir():
                raise ValueError('Archive links and directory entries are forbidden')
        if len(names) != len(set(names)) or MANIFEST not in names:
            raise ValueError('Duplicate entries or missing manifest')
        manifest = json.loads(archive.read(MANIFEST))
        if manifest.get('version') != 1 or not isinstance(manifest.get('files'), dict):
            raise ValueError('Invalid manifest')
        for name in manifest['files']:
            safe_name(name)
        if set(names) != set(manifest['files']) | {MANIFEST}:
            raise ValueError('Missing or extra archive files')
        for name, expected in manifest['files'].items():
            data = archive.read(name)
            if digest(data) != expected['sha256'] or len(data) != expected['size']:
                raise ValueError('Checksum mismatch: ' + name)
    if restored_dir is not None:
        root = Path(restored_dir); no_links(root)
        actual = set()
        for path in root.rglob('*'):
            no_links(path)
            if path.is_file(): actual.add(path.relative_to(root).as_posix())
        if actual != set(manifest['files']):
            raise ValueError('Missing or extra restored files')
        for name, expected in manifest['files'].items():
            data = (root / name).read_bytes()
            if digest(data) != expected['sha256'] or len(data) != expected['size']:
                raise ValueError('Restored checksum mismatch: ' + name)
    return manifest


def restore_backup(archive_path, destination):
    manifest = verify_backup(archive_path)
    destination = Path(destination); no_links(destination)
    if destination.exists():
        raise ValueError('Restore destination must not exist')
    destination.mkdir(parents=True, mode=0o700)
    with zipfile.ZipFile(archive_path) as archive:
        for name in manifest['files']:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with os.fdopen(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as output:
                output.write(archive.read(name))
    verify_backup(archive_path, destination)
    return manifest


def main():
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/video2book'))
    from src.core.console import enable_utf8_console
    enable_utf8_console()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    backup = sub.add_parser('create'); backup.add_argument('source_dir'); backup.add_argument('destination_file')
    verify = sub.add_parser('verify'); verify.add_argument('archive'); verify.add_argument('restored_dir', nargs='?')
    restore = sub.add_parser('restore'); restore.add_argument('archive'); restore.add_argument('destination_dir')
    args = parser.parse_args()
    try:
        if args.command == 'create': result = create_backup(args.source_dir, args.destination_file)
        elif args.command == 'verify': result = verify_backup(args.archive, args.restored_dir)
        else: result = restore_backup(args.archive, args.destination_dir)
    except (ValueError, OSError, sqlite3.Error, zipfile.BadZipFile, KeyError) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps({'verified_files': len(result['files']), 'excluded_files': len(result.get('excluded', []))}))


if __name__ == '__main__':
    main()
