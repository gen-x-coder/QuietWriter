"""Regressions for the data-safety findings in Claude's dev.35 review."""
from pathlib import Path

from quietwriter.storage import Library
from quietwriter.automatic_backups import create_backup, BackupError
from quietwriter.spell_engine import WordDictionary
from quietwriter.qwbook_io import export_qwbook
from quietwriter.backup_restore import replace_existing_book
from quietwriter.revisions import ExternalModificationError
import pytest


def test_backup_never_accepts_external_change_as_editor_baseline(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Gedeeld boek')
    book = lib.load_book(book.path)
    lib.track_book(book)
    chapter = book.sections[0].chapters[0]
    path = book.path / chapter.file
    path.write_text('externe tekst', encoding='utf-8')
    revision = lib.tracked_revision(book)
    with pytest.raises(BackupError):
        create_backup(lib, book, tmp_path / 'backups')
    assert lib.tracked_revision(book) == revision
    with pytest.raises(ExternalModificationError):
        lib.save_chapter(book, chapter, 'lokale tekst')
    assert path.read_text(encoding='utf-8') == 'externe tekst'


def test_backup_unopened_book_does_not_track_it(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Niet geopend')
    lib.untrack_book(book)
    target = create_backup(lib, book, tmp_path / 'backups')
    assert target.exists()
    assert lib.tracked_revision(book) is None


def test_spelling_without_aff_normalizes_opentaal_ij(tmp_path):
    dic = tmp_path / 'nl_NL.dic'
    dic.write_text('2\nvrĳheid\nbĳvoorbeeld\n', encoding='utf-8')
    dictionary = WordDictionary()
    dictionary.load_dic(dic)
    assert dictionary.known('vrijheid')
    assert 'vrijheid' in dictionary.suggest('vrijheidd')
    assert all('ĳ' not in suggestion for suggestion in dictionary.suggest('vrijheidd'))


def test_restore_archive_without_history_preserves_live_history(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Met geschiedenis')
    lib.create_version(book)
    lib.create_version(book)
    exported = export_qwbook(lib, book, tmp_path / 'zonder.qwbook', include_history=False)
    restored, _ = replace_existing_book(lib, exported, tmp_path / 'backups', expected_id=book.id)
    assert len(lib.list_versions(restored)) >= 2


def test_partial_legacy_version_cannot_be_listed_or_restored(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Twee hoofdstukken')
    first = book.sections[0].chapters[0]
    lib.add_chapter(book, book.sections[0], 'Tweede')
    book = lib.load_book(book.path)
    version = lib.create_version(book)
    missing = version['path'] / book.sections[0].chapters[1].file
    missing.unlink()
    assert all(row['id'] != version['id'] or row['kind'] for row in lib.list_versions(book))
    with pytest.raises((ValueError, FileNotFoundError)):
        lib.load_version(book, version['id'])


def test_permanent_book_deletion_removes_archived_text(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Geheim')
    lib.create_version(book)
    lib.delete_book(book)
    for row in lib.list_trashed_books():
        if row.get('book_id') == book.id:
            lib.permanently_delete_trashed_book(row['path'])
    assert not (lib.archive_dir / book.id).exists()
