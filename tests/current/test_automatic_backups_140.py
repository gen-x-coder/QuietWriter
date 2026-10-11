from pathlib import Path
import zipfile

import pytest

from quietwriter.automatic_backups import (BackupError, create_backup,
                                           validate_archive, validate_backup_root)
from quietwriter.storage import Library


def test_rejects_workspace_and_all_ancestors_and_children(tmp_path):
    workspace = tmp_path / 'books'
    workspace.mkdir()
    for bad in (workspace, tmp_path, workspace / 'backup'):
        with pytest.raises(BackupError):
            validate_backup_root(workspace, bad)
    assert validate_backup_root(workspace, tmp_path / 'separate') == tmp_path / 'separate'


def test_rejects_linked_backup_path(tmp_path):
    workspace = tmp_path / 'books'
    workspace.mkdir()
    link = tmp_path / 'linked'
    try:
        link.symlink_to(workspace, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip('Symlinks unavailable on this system')
    with pytest.raises(BackupError):
        validate_backup_root(workspace, link / 'elsewhere')


def test_creates_verified_backups_without_overwrite(tmp_path):
    lib = Library(tmp_path / 'work')
    book = lib.create_book('Back-upboek')
    lib.track_book(book)
    first = create_backup(lib, book, tmp_path / 'external')
    second = create_backup(lib, book, tmp_path / 'external')
    assert first != second
    assert first.exists() and second.exists()
    assert validate_archive(first, book.id)['history_included'] is True
    assert validate_archive(second, book.id)['ai_chat_included'] is True


def test_corrupted_payload_is_detected(tmp_path):
    lib = Library(tmp_path / 'work')
    book = lib.create_book('Beschadiging')
    lib.track_book(book)
    backup = create_backup(lib, book, tmp_path / 'external')
    with zipfile.ZipFile(backup, 'r') as source:
        contents = [(info, source.read(info.filename)) for info in source.infolist()]
    with zipfile.ZipFile(backup, 'w') as target:
        for info, content in contents:
            if info.filename == 'book/book.json':
                content += b'bad'
            target.writestr(info, content)
    with pytest.raises(BackupError):
        validate_archive(backup, book.id)


def test_unregistered_partial_history_not_included(tmp_path):
    import shutil
    lib = Library(tmp_path / 'work')
    book = lib.create_book('History race')
    lib.track_book(book)
    lib.create_version(book)
    half = lib.archive_dir / book.id / 'uncommitted-copytree'
    half.mkdir()
    shutil.copy2(Path(book.path) / 'book.json', half / 'book.json')
    output = create_backup(lib, book, tmp_path / 'external')
    with zipfile.ZipFile(output) as archive:
        assert not any('uncommitted-copytree' in n for n in archive.namelist())


def test_verify_before_publication_even_if_cleanup_is_locked(tmp_path, monkeypatch):
    from quietwriter import automatic_backups as backups
    lib = Library(tmp_path / 'work')
    book = lib.create_book('Safe')
    lib.track_book(book)
    def fail(*args):
        raise BackupError('bad validation')
    monkeypatch.setattr(backups, 'validate_archive', fail)
    with pytest.raises(BackupError):
        create_backup(lib, book, tmp_path / 'external')
    assert not list((tmp_path / 'external').rglob('*.qwbook'))


def test_backup_fsync_before_publish(tmp_path, monkeypatch):
    import os
    lib = Library(tmp_path / 'work')
    book = lib.create_book('Fsync')
    lib.track_book(book)
    calls = []
    orig_sync, orig_replace = os.fsync, os.replace
    def sync(fd):
        calls.append('sync')
        return orig_sync(fd)
    def replace(a, b):
        if str(b).endswith('.qwbook'):
            calls.append('publish')
        return orig_replace(a, b)
    monkeypatch.setattr(os, 'fsync', sync)
    monkeypatch.setattr(os, 'replace', replace)
    create_backup(lib, book, tmp_path / 'external')
    assert 'sync' in calls and calls.index('sync') < calls.index('publish')


def test_retry_transient_windows_lock(tmp_path, monkeypatch):
    import os
    lib = Library(tmp_path / 'work')
    book = lib.create_book('Lock')
    lib.track_book(book)
    orig = os.replace
    failures = []
    def sometimes_locked(a, b):
        if str(b).endswith('.qwbook') and len(failures) < 2:
            failures.append(1)
            raise PermissionError(32, 'sharing violation')
        return orig(a, b)
    monkeypatch.setattr(os, 'replace', sometimes_locked)
    output = create_backup(lib, book, tmp_path / 'external')
    assert output.is_file() and len(failures) == 2


def test_streams_media_without_buffering_whole_file(tmp_path):
    import os
    lib = Library(tmp_path / 'work')
    book = lib.create_book('Big Media')
    lib.track_book(book)
    media = Path(book.path) / 'assets' / 'images'
    media.mkdir(parents=True, exist_ok=True)
    (media / 'photo.jpg').write_bytes(os.urandom(12 * 1024 * 1024))
    output = create_backup(lib, book, tmp_path / 'external')
    assert validate_archive(output, book.id)['book_id'] == book.id


def test_fsync_uses_writable_handle(tmp_path, monkeypatch):
    import os
    from quietwriter import automatic_backups as backups
    lib = Library(tmp_path / 'work')
    book = lib.create_book('Windows writable flush')
    lib.track_book(book)
    original = os.fsync
    seen = []
    def inspect(fd):
        # A Windows read-only descriptor cannot be flushed. Inspect the mode
        # on POSIX to enforce the same precondition in cross-platform CI.
        if os.name == 'posix':
            import fcntl
            seen.append(fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_ACCMODE)
        return original(fd)
    monkeypatch.setattr(backups.os, 'fsync', inspect)
    create_backup(lib, book, tmp_path / 'external')
    if seen:
        assert seen[0] in (os.O_WRONLY, os.O_RDWR)


def test_legacy_daily_history_is_preserved(tmp_path):
    import shutil
    lib = Library(tmp_path / 'work')
    book = lib.create_book('Legacy')
    lib.track_book(book)
    folder = lib.archive_dir / book.id / '2025-05-01'
    shutil.copytree(book.path, folder)
    assert any(row['id'] == '2025-05-01' for row in lib.list_versions(book))
    path = create_backup(lib, book, tmp_path / 'external')
    with zipfile.ZipFile(path) as archive:
        assert any(name.startswith('history/2025-05-01/') for name in archive.namelist())


def test_backup_conflict_and_blocked_book_return_backup_error(tmp_path):
    lib = Library(tmp_path / 'work')
    book = lib.create_book('Conflict')
    lib.track_book(book)
    chapter = book.sections[0].chapters[0]
    (Path(book.path) / chapter.file).write_text('extern gewijzigd', encoding='utf-8')
    with pytest.raises(BackupError, match='buiten QuietWriter'):
        create_backup(lib, book, tmp_path / 'external')
    book = lib.load_book(book.path)
    lib.track_book(book)
    lib.block_book(book)
    with pytest.raises(BackupError, match='geblokkeerd'):
        create_backup(lib, book, tmp_path / 'external')
