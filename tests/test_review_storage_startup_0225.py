"""Regression coverage for QuietWriter 0.22.5 storage/startup hardening."""
from __future__ import annotations

import copy
import json
import sqlite3
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from quietwriter.search import BookSearchIndex
from quietwriter.storage import Library

ROOT = Path(__file__).resolve().parents[1]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')


def test_corrupt_search_cache_is_rebuilt_instead_of_blocking_startup():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / 'book_search.db'
        db.write_bytes(b'not a sqlite database')
        index = BookSearchIndex(db)
        try:
            assert index.search('missing', 'iets') == []
            with sqlite3.connect(db) as conn:
                row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chapters'").fetchone()
                assert row == ('chapters',)
        finally:
            index.close()


def test_search_cache_rebuild_failure_is_best_effort():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td) / 'workspace')
        book = lib.create_book('Cache')
        index = BookSearchIndex(lib.cache_dir / 'book_search.db')
        try:
            index.conn.close()
            # A closed/corrupt cache must never propagate through editor save paths.
            assert index.rebuild_book(book) in {True, False}
        finally:
            index.close()


def test_new_book_does_not_inherit_legacy_cover_with_same_slug():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td) / 'workspace')
        old = lib.create_book('Zomer')
        old_data = json.loads(old.manifest_path.read_text(encoding='utf-8'))
        old_data['metadata'].pop('cover_file', None)  # simulate pre-0.20 manifest
        old.manifest_path.write_text(json.dumps(old_data), encoding='utf-8')
        (old.path / 'assets' / 'manifest.json').unlink()
        legacy = lib.covers_dir / 'zomer.jpg'
        legacy.write_bytes(b'legacy-cover')

        legacy_book = lib.load_book(old.path)
        assert legacy_book.metadata['cover_file'] == 'zomer.jpg'
        assert lib.cover_path(legacy_book) == legacy

        new = lib.create_book('Zomer')
        fresh = lib.load_book(new.path)
        assert 'cover_file' in json.loads(new.manifest_path.read_text(encoding='utf-8'))['metadata']
        assert fresh.metadata['cover_file'] == ''
        assert lib.cover_path(fresh) is None


def test_remove_cover_never_deletes_slug_fallback_of_another_book():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td) / 'workspace')
        owner = lib.create_book('Zomer')
        owner_data = json.loads(owner.manifest_path.read_text(encoding='utf-8'))
        owner_data['metadata'].pop('cover_file', None)
        owner.manifest_path.write_text(json.dumps(owner_data), encoding='utf-8')
        (owner.path / 'assets' / 'manifest.json').unlink()
        legacy = lib.covers_dir / 'zomer.png'
        legacy.write_bytes(b'owner')
        owner = lib.load_book(owner.path)

        other = lib.create_book('Zomer')
        lib.remove_cover(other)
        assert legacy.exists()
        assert lib.cover_path(owner) == legacy


def test_failed_delete_keeps_revision_tracking_active():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td) / 'workspace')
        book = lib.create_book('Delete')
        lib.track_book(book)
        with mock.patch('quietwriter.storage.shutil.move', side_effect=OSError('locked')):
            with pytest.raises(OSError):
                lib.delete_book(book)
        assert lib.tracked_revision(book) is not None
        assert book.path.exists()


def test_save_chapter_refreshes_tracking_when_last_used_manifest_write_fails():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td) / 'workspace')
        book = lib.create_book('Last used')
        chapter = book.sections[0].chapters[0]
        lib.track_book(book)
        original_write = lib._write_manifest_unchecked

        with mock.patch.object(lib, '_write_manifest_unchecked', side_effect=OSError('manifest locked')):
            # last_used is best effort: manuscript text itself is the save.
            lib.save_chapter(book, chapter, 'Nieuwe tekst')

        assert (book.path / chapter.file).read_text(encoding='utf-8') == 'Nieuwe tekst'
        # A second save must not see our own first chapter write as external.
        with mock.patch.object(lib, '_write_manifest_unchecked', wraps=original_write):
            lib.save_chapter(book, chapter, 'Nog een regel')
        assert (book.path / chapter.file).read_text(encoding='utf-8') == 'Nog een regel'


def test_book_details_uses_candidate_and_only_adopts_after_success():
    source = _source('quietwriter/ui/book_details.py')
    save = source.split('    def save(self):', 1)[1].split('    def delete_book(self):', 1)[0]
    assert 'candidate = copy.deepcopy(self.book)' in save
    assert 'candidate.title = title' in save
    assert 'candidate.metadata.update' in save
    assert 'self.book.title = candidate.title' in save
    assert 'self.book.metadata = copy.deepcopy(candidate.metadata)' in save
    # The live shared book may only be touched after the guarded candidate commit.
    assert save.index('self.book.title = candidate.title') > save.index('self.library.save_book_details(self.book, candidate, self.pending_cover)')



def test_book_details_cover_transaction_rolls_back_files_on_manifest_failure():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        book = lib.create_book('Omslag')
        local = book.path / 'assets' / 'cover' / 'cover.jpg'
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(b'old-cover')
        book.metadata['cover_file'] = 'assets/cover/cover.jpg'
        lib.save_manifest(book)
        lib.track_book(book)

        candidate = copy.deepcopy(book)
        candidate.title = 'Nieuwe titel'
        source = root / 'new.png'
        source.write_bytes(b'new-cover')
        with mock.patch.object(lib, 'save_manifest', side_effect=OSError('manifest locked')):
            with pytest.raises(OSError):
                lib.save_book_details(book, candidate, source)

        assert local.read_bytes() == b'old-cover'
        assert not (book.path / 'assets' / 'cover' / 'cover.png').exists()
        assert book.title == 'Omslag'
        assert book.metadata['cover_file'] == 'assets/cover/cover.jpg'

def test_startup_handles_unreachable_workspace_with_visible_choice():
    app_source = _source('quietwriter/app.py')
    source = _source('quietwriter/ui/workspace_recovery.py')
    assert 'open_library_with_recovery(root, settings, splash)' in app_source
    assert 'def open_library_with_recovery(' in source
    assert 'except OSError as exc:' in source
    assert 'QMessageBox' in source
    assert 'QFileDialog.getExistingDirectory' in source
    assert "startup.workspace_unavailable" in source
    assert "startup.choose_workspace" in source
    assert "startup.exit" in source
