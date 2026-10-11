"""Automatic-backup selection and conservative retention."""
from datetime import datetime, timedelta
import os
from pathlib import Path

import pytest

from quietwriter.automatic_backups import BackupError, create_backup
from quietwriter.backup_schedule import needs_daily_backup, latest_backup, prune_automatic_backups
from quietwriter.storage import Library


def test_new_book_due_then_not_again_same_day(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Dagelijkse kopie')
    lib.track_book(book)
    dest = tmp_path / 'backups'
    assert needs_daily_backup(book, dest)
    output = create_backup(lib, book, dest, automatic=True)
    assert output.name.startswith('auto_')
    assert latest_backup(dest, book.id) == output
    assert not needs_daily_backup(book, dest)


def test_only_backup_changed_book_after_a_day(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Boek')
    lib.track_book(book)
    dest = tmp_path / 'backup'
    first = create_backup(lib, book, dest, automatic=True)
    yesterday = (datetime.now() - timedelta(days=2)).timestamp()
    # Simulate an unchanged book whose content predates the successful backup.
    old_source = (datetime.now() - timedelta(days=3)).timestamp()
    for file in Path(book.path).rglob('*'):
        if file.is_file():
            os.utime(file, (old_source, old_source))
    os.utime(first, (yesterday, yesterday))
    assert not needs_daily_backup(book, dest)
    lib.save_chapter(book, book.sections[0].chapters[0], 'Nieuwe tekst')
    assert needs_daily_backup(book, dest)


def test_retention_never_deletes_manual_backups(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Bewaren')
    lib.track_book(book)
    dest = tmp_path / 'backup'
    manual = create_backup(lib, book, dest)
    generated = []
    for offset in range(35, -1, -1):
        archive = create_backup(lib, book, dest, automatic=True)
        timestamp = (datetime.now() - timedelta(days=offset)).timestamp()
        os.utime(archive, (timestamp, timestamp))
        generated.append(archive)
    deleted = prune_automatic_backups(dest, book.id, newest_success=generated[-1])
    assert deleted
    assert manual.exists()
    assert generated[-1].exists()
    assert len(list(manual.parent.glob('auto_*.qwbook'))) <= 11


def test_retention_rejects_unverified_new_backup(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Bescherm eerdere kopieën')
    lib.track_book(book)
    dest = tmp_path / 'backup'
    good = create_backup(lib, book, dest, automatic=True)
    broken = good.parent / 'auto_invalid.qwbook'
    broken.write_bytes(b'broken')
    with pytest.raises(BackupError):
        prune_automatic_backups(dest, book.id, newest_success=broken)
    assert good.exists() and broken.exists()
