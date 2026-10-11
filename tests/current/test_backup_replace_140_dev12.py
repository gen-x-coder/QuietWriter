"""Recovery must preserve the old book until a validated copy is ready."""
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from quietwriter.storage import Library
from quietwriter.automatic_backups import create_backup
from quietwriter.backup_restore import replace_existing_book, RestoreError


def fixture(tmp_path):
    lib = Library(tmp_path / 'work')
    book = lib.create_book('Test')
    chapter = book.sections[0].chapters[0]
    lib.save_chapter(book, chapter, 'Before')
    book = lib.load_book(book.path)
    lib.track_book(book)
    old = create_backup(lib, book, tmp_path / 'backup')
    lib.save_chapter(book, chapter, 'After')
    book = lib.load_book(book.path)
    lib.track_book(book)
    return lib, book, chapter, old


def test_restoring_keeps_prior_version_as_separate_manual_backup(tmp_path):
    lib, book, chapter, old = fixture(tmp_path)
    restored, safety = replace_existing_book(lib, old, tmp_path / 'backup', expected_id=book.id)
    assert lib.read_chapter(restored, chapter) == 'Before'
    assert safety.exists() and safety != old
    separate = Library(tmp_path / 'read_safety')
    from quietwriter.qwbook_io import import_qwbook
    previous = import_qwbook(separate, safety)
    assert separate.read_chapter(previous, chapter) == 'After'
    assert len(lib.list_books()) == 1


def test_failing_swap_rolls_back_original_book(tmp_path):
    lib, book, chapter, old = fixture(tmp_path)
    real_replace = os.replace
    def fail_install(src, dst):
        if Path(src).name == book.path.name and 'restore-' in str(src):
            raise OSError('simulated interrupted replacement')
        return real_replace(src, dst)
    # Intercept the promotion of staged book; leave rollback functional.
    def fail_staged(src, dst):
        if str(dst) == str(book.path) and '/books/' in str(src).replace('\\', '/'):
            raise OSError('simulated interrupted replacement')
        return real_replace(src, dst)
    with patch('quietwriter.backup_restore.os.replace', side_effect=fail_staged):
        with pytest.raises(RestoreError):
            replace_existing_book(lib, old, tmp_path / 'backup')
    assert lib.read_chapter(lib.load_book(book.path), chapter) == 'After'


def test_wrong_identity_never_changes_book(tmp_path):
    lib, book, chapter, old = fixture(tmp_path)
    with pytest.raises(RestoreError):
        replace_existing_book(lib, old, tmp_path / 'backup', expected_id='different')
    assert lib.read_chapter(lib.load_book(book.path), chapter) == 'After'


def test_windows_cleanup_lock_after_success_is_not_restore_failure(tmp_path):
    """An antivirus/OneDrive cleanup lock cannot turn a successful swap into failure."""
    import quietwriter.backup_restore as mod
    lib, book, chapter, old = fixture(tmp_path)
    real_rmtree = mod.shutil.rmtree
    def locked_cleanup(path, *args, **kwargs):
        if 'restore-' in Path(path).name:
            raise PermissionError(32, 'file in use by another process')
        return real_rmtree(path, *args, **kwargs)
    with patch.object(mod.shutil, 'rmtree', side_effect=locked_cleanup):
        restored, safety = replace_existing_book(lib, old, tmp_path / 'backup')
    assert lib.read_chapter(restored, chapter) == 'Before'
    assert safety.is_file()
    assert list((lib.root / '.restore-staging').glob('restore-*'))
    # This simulation leaves staging intentionally; the next run retries cleanup.
