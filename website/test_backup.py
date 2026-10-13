import json
import sqlite3
import stat
import zipfile

import pytest
from tools.private_backup import MANIFEST, create_backup, restore_backup, verify_backup


def test_roundtrip_and_live_sqlite(tmp_path):
    source = tmp_path / 'source'; source.mkdir()
    (source / 'book.md').write_text('# 私有教材', encoding='utf-8')
    (source / 'assets').mkdir(); (source / 'assets' / 'image.png').write_bytes(b'PNG')
    (source / 'provenance.json').write_text('{"source":"local"}')
    (source / 'secret.key').write_text('private')
    (source / 'video.mp4').write_bytes(b'media')
    (source / 'signed.json').write_text('{"url":"https://example.com/?X-Amz-Signature=hidden"}')
    (source / 'config.json').write_text('{"password":"do-not-include"}')
    connection = sqlite3.connect(source / 'library.sqlite3')
    connection.execute('PRAGMA journal_mode=WAL')
    connection.execute('CREATE TABLE books(title TEXT)')
    connection.execute("INSERT INTO books VALUES ('private book')"); connection.commit()
    archive = tmp_path / 'backup.zip'
    result = create_backup(source, archive)
    assert set(result['files']) == {'book.md', 'assets/image.png', 'provenance.json', 'library.sqlite3'}
    assert archive.stat().st_mode & 0o777 == 0o600
    restored = tmp_path / 'restored'; restore_backup(archive, restored)
    with sqlite3.connect(restored / 'library.sqlite3') as db:
        assert db.execute('SELECT title FROM books').fetchone() == ('private book',)
        assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',)
    connection.close()
    verify_backup(archive, restored)
    (restored / 'extra.txt').write_text('extra')
    with pytest.raises(ValueError, match='extra'): verify_backup(archive, restored)
    (restored / 'extra.txt').unlink(); (restored / 'book.md').unlink()
    with pytest.raises(ValueError, match='Missing'): verify_backup(archive, restored)


def test_hash_corruption(tmp_path):
    source = tmp_path / 'source'; source.mkdir(); (source / 'book.md').write_text('original')
    archive = tmp_path / 'backup.zip'; create_backup(source, archive)
    corrupt = tmp_path / 'corrupt.zip'
    with zipfile.ZipFile(archive) as original, zipfile.ZipFile(corrupt, 'w') as target:
        for name in original.namelist():
            target.writestr(name, b'corrupt' if name == 'book.md' else original.read(name))
    with pytest.raises(ValueError, match='Checksum'): verify_backup(corrupt)
    restore_backup(archive, tmp_path / 'restored')
    (tmp_path / 'restored/book.md').write_text('damaged')
    with pytest.raises(ValueError, match='checksum'): verify_backup(archive, tmp_path / 'restored')


def test_symlinks_and_nested_output(tmp_path):
    source = tmp_path / 'source'; source.mkdir(); (source / 'book.md').write_text('original')
    with pytest.raises(ValueError): create_backup(source, source / 'nested/backup.zip')
    (source / 'link.md').symlink_to(source / 'book.md')
    with pytest.raises(ValueError, match='Symbolic'): create_backup(source, tmp_path / 'backup.zip')
    (source / 'link.md').unlink()
    linked = tmp_path / 'linked'; linked.symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError, match='Symbolic'): create_backup(linked, tmp_path / 'backup.zip')


@pytest.mark.parametrize('name', ['../escape.md', '/absolute.md', 'folder/../../escape.md', 'folder\\escape.md', 'C:/escape.md'])
def test_archive_traversal(tmp_path, name):
    archive = tmp_path / 'unsafe.zip'
    with zipfile.ZipFile(archive, 'w') as target:
        target.writestr(name, 'danger')
        target.writestr(MANIFEST, json.dumps({'version': 1, 'files': {}}))
    with pytest.raises(ValueError, match='Unsafe'): restore_backup(archive, tmp_path / 'restored')
    assert not (tmp_path / 'restored').exists()


@pytest.mark.parametrize('mode', ['missing', 'extra', 'symlink'])
def test_archive_members(tmp_path, mode):
    source = tmp_path / 'source'; source.mkdir(); (source / 'book.md').write_text('original')
    original = tmp_path / 'backup.zip'; create_backup(source, original)
    archive = tmp_path / 'changed.zip'
    with zipfile.ZipFile(original) as src, zipfile.ZipFile(archive, 'w') as target:
        for name in src.namelist():
            if mode == 'missing' and name == 'book.md': continue
            if mode == 'symlink' and name == 'book.md':
                info = zipfile.ZipInfo(name); info.external_attr = (stat.S_IFLNK | 0o777) << 16
                target.writestr(info, src.read(name))
            else: target.writestr(name, src.read(name))
        if mode == 'extra': target.writestr('extra.md', 'extra')
    with pytest.raises(ValueError): verify_backup(archive)
