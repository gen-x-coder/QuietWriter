from pathlib import Path

import pytest

from quietwriter.exporting.settings import ExportSettingsStore, default_export_settings
from quietwriter.integrity import BookIntegrityChecker
from quietwriter.revisions import ExternalModificationError
from quietwriter.storage import CorruptSourceError, Library


def make_book(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Review 0.31.4')
    lib.track_book(book)
    return lib, book


def test_export_store_validate_source_rejects_truncated_json(tmp_path):
    lib, book = make_book(tmp_path)
    store = ExportSettingsStore(lib)
    path = store.path(book)
    path.parent.mkdir(parents=True, exist_ok=True)
    original = b'{"version":1,"format":"pdf"'
    path.write_bytes(original)
    lib.refresh_book_revision(book)

    with pytest.raises(CorruptSourceError):
        store.validate_source(book)
    assert path.read_bytes() == original


def test_export_store_detects_external_chapter_change_before_settings_write(tmp_path):
    lib, book = make_book(tmp_path)
    store = ExportSettingsStore(lib)
    store.save(book, default_export_settings())
    settings_before = store.path(book).read_bytes()

    chapter = book.sections[0].chapters[0]
    chapter_path = Path(book.path) / chapter.file
    chapter_path.write_text('extern gewijzigd', encoding='utf-8')

    changed = default_export_settings()
    changed['format'] = 'pdf'
    with pytest.raises(ExternalModificationError):
        store.save(book, changed)
    assert store.path(book).read_bytes() == settings_before


def test_integrity_reports_corrupt_publication_text_recoverable(tmp_path):
    lib, book = make_book(tmp_path)
    path = Path(book.path) / 'publication' / 'texts' / 'foreword.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'voorwoord-\xff')

    report = BookIntegrityChecker().audit_folder(book.path)
    issue = next(i for i in report.errors if i.path == 'publication/texts/foreword.md')
    assert issue.code == 'aux_text_invalid'
    assert issue.recoverable is True


def test_integrity_can_restore_corrupt_publication_text_from_history(tmp_path):
    lib, book = make_book(tmp_path)
    path = Path(book.path) / 'publication' / 'texts' / 'foreword.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('goed voorwoord', encoding='utf-8')
    lib.refresh_book_revision(book)
    lib.create_version(book, kind='manual')

    path.write_bytes(b'kapot-\xff')
    lib.refresh_book_revision(book)
    checker = BookIntegrityChecker()
    assert checker.latest_recovery_file(lib, book, 'publication/texts/foreword.md') is not None
    checker.restore_file_from_history(lib, book, 'publication/texts/foreword.md')
    assert path.read_text(encoding='utf-8') == 'goed voorwoord'


def test_export_page_has_guarded_persistence_and_external_reload_by_source():
    source = Path('quietwriter/ui/export_page.py').read_text(encoding='utf-8')
    assert 'def _persist_settings(self) -> bool:' in source
    assert 'except ExternalModificationError as exc:' in source
    assert 'self._resolve_external_change(exc)' in source
    assert 'De nieuwste versie is geladen. Kies je exportinstelling opnieuw.' in source
    assert 'self.store.validate_source(book)' in source
