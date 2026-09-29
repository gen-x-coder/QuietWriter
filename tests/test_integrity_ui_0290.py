from pathlib import Path
import pytest

from quietwriter.integrity import BookIntegrityChecker
from quietwriter.storage import BookBlockedError, Library


def make(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Hersteltest')
    lib.track_book(book)
    return lib, book


def test_blocked_book_has_domain_error(tmp_path):
    lib, book = make(tmp_path)
    lib.block_book(book)
    with pytest.raises(BookBlockedError):
        lib.verify_book_unchanged(book)


def test_integrity_repair_stays_explicit_and_creates_checkpoint(tmp_path):
    lib, book = make(tmp_path)
    rel = book.sections[0].chapters[0].file
    target = Path(book.path) / rel
    target.write_text('goede versie', encoding='utf-8')
    lib.refresh_book_revision(book)
    lib.create_version(book, kind='manual')
    target.unlink()
    lib.refresh_book_revision(book)

    checker = BookIntegrityChecker()
    report = checker.audit_folder(book.path)
    issue = next(i for i in report.errors if i.path == rel)
    assert issue.recoverable
    assert not target.exists()  # audit itself never repairs
    assert checker.latest_recovery_file(lib, book, rel) is not None

    checker.restore_file_from_history(lib, book, rel)
    assert target.read_text(encoding='utf-8') == 'goede versie'
    assert any(v['kind'] == 'pre_integrity_repair' for v in lib.list_versions(book))


def test_no_history_copy_means_no_recovery_source(tmp_path):
    lib, book = make(tmp_path)
    rel = book.sections[0].chapters[0].file
    (Path(book.path) / rel).unlink()
    lib.refresh_book_revision(book)
    checker = BookIntegrityChecker()
    assert checker.latest_recovery_file(lib, book, rel) is None

def test_legacy_book_stays_legacy_until_explicit_migration(tmp_path):
    import json
    lib, book = make(tmp_path)
    data = json.loads(book.manifest_path.read_text(encoding='utf-8'))
    data['format'] = 1
    book.manifest_path.write_text(json.dumps(data), encoding='utf-8')

    legacy = lib.load_book(book.path)
    assert legacy.format_version == 1
    lib.track_book(legacy)
    touched = lib.touch_book(legacy)
    assert json.loads(touched.manifest_path.read_text(encoding='utf-8'))['format'] == 1

    migrated, result, checkpoint = lib.migrate_book_format(touched)
    assert result.changed
    assert checkpoint is not None
    assert migrated.format_version == 2
    assert json.loads(migrated.manifest_path.read_text(encoding='utf-8'))['format'] == 2
