import json
from pathlib import Path

import pytest

from quietwriter.document_view import visible_text
from quietwriter.manuscript_profile import (
    AmbiguousManuscriptSyntaxError,
    current_manifest_value,
    migrate_legacy_source_to_current,
    migration_source_state,
    profile_from_manifest,
)
from quietwriter.storage import Library, StorageWriteError


def _legacy_book(library: Library, text_by_chapter: list[str]):
    folder = library.books_dir / 'legacy-syntax'
    (folder / 'chapters').mkdir(parents=True)
    chapters = []
    for index, text in enumerate(text_by_chapter, 1):
        rel = f'chapters/{index}.md'
        (folder / rel).write_text(text, encoding='utf-8', newline='')
        chapters.append({'id': f'c{index}', 'title': f'Hoofdstuk {index}', 'file': rel})
    manifest = {
        'format': 2,
        'id': 'legacy-syntax-id',
        'title': 'Legacy syntax',
        'metadata': {},
        'sections': [{'id': 'root', 'title': 'Manuscript', 'chapters': chapters}],
    }
    (folder / 'book.json').write_text(json.dumps(manifest), encoding='utf-8')
    return library.load_book(folder)


def test_pre_escape_migration_only_changes_backslashes_current_reader_would_hide():
    original = r'\\server\share en C:\Users\lucas\.config / regex a\.b / \#tag / pijl \->'
    migrated, count = migrate_legacy_source_to_current(original)
    assert count == 1  # only the first slash of the UNC pair is hidden by escape-v1
    assert visible_text(migrated) == original
    assert r'C:\Users\lucas\.config' in migrated
    assert r'regex a\.b' in migrated


def test_escape_era_unmarked_source_is_detected_without_rewriting_bytes(tmp_path):
    library = Library(tmp_path)
    original = 'nummer \\*31623455 en 5\\*3\n\\- Kom je mee?\n1944\\. Het was koud.\nC:\\\\pad\\\\naar'
    book = _legacy_book(library, [original])
    library.track_book(book)
    assert migration_source_state([original]) == 'escape-era'

    migrated, report, checkpoint = library.migrate_manuscript_syntax(book)
    assert checkpoint
    assert report.mode == 'escape-era'
    assert report.changed_chapters == 0
    assert report.escaped_backslashes == 0
    assert library.read_chapter(migrated, migrated.sections[0].chapters[0]) == original
    assert profile_from_manifest(migrated.extra_manifest).is_current


def test_ambiguous_all_even_backslashes_require_explicit_choice(tmp_path):
    library = Library(tmp_path)
    original = r'C:\\pad\\naar'
    book = _legacy_book(library, [original])
    library.track_book(book)
    assert migration_source_state([original]) == 'ambiguous'
    with pytest.raises(AmbiguousManuscriptSyntaxError):
        library.migrate_manuscript_syntax(book)


def test_explicit_legacy_migration_creates_checkpoint_and_marks_manifest(tmp_path):
    library = Library(tmp_path)
    original = r'\\server\share en C:\Users\lucas\.config'
    book = _legacy_book(library, [original, 'Gewone tekst zonder backslash.'])
    library.track_book(book)

    migrated, report, checkpoint = library.migrate_manuscript_syntax(book)

    assert checkpoint
    assert report.changed_chapters == 1
    assert report.escaped_backslashes == 1
    assert visible_text(library.read_chapter(migrated, migrated.sections[0].chapters[0])) == original
    data = json.loads(migrated.manifest_path.read_text(encoding='utf-8'))
    assert data['manuscript_syntax'] == current_manifest_value()
    assert profile_from_manifest(data).is_current

    snapshot = library.load_version(migrated, checkpoint)
    snap_data = json.loads(snapshot.manifest_path.read_text(encoding='utf-8'))
    assert 'manuscript_syntax' not in snap_data
    assert library.read_chapter(snapshot, snapshot.sections[0].chapters[0]) == original


def test_syntax_migration_is_noop_when_book_is_already_current(tmp_path):
    library = Library(tmp_path)
    book = library.create_book('Actueel')
    library.track_book(book)
    same, report, checkpoint = library.migrate_manuscript_syntax(book)
    assert same.id == book.id
    assert report.changed_chapters == 0
    assert report.escaped_backslashes == 0
    assert checkpoint is None


def test_failed_syntax_migration_restores_live_book_from_checkpoint(tmp_path, monkeypatch):
    import quietwriter.storage as storage_module

    library = Library(tmp_path)
    originals = [r'\\server\share', r'\\host\share']
    book = _legacy_book(library, originals)
    library.track_book(book)

    real_write = storage_module._safe_atomic_write_text
    chapter_writes = 0

    def failing_write(path, text, *args, **kwargs):
        nonlocal chapter_writes
        path = Path(path)
        if path.parent.name == 'chapters' and path.parent.parent == book.path:
            chapter_writes += 1
            if chapter_writes == 2:
                raise StorageWriteError(path, OSError('simulated'))
        return real_write(path, text, *args, **kwargs)

    monkeypatch.setattr(storage_module, '_safe_atomic_write_text', failing_write)
    with pytest.raises(StorageWriteError):
        library.migrate_manuscript_syntax(book, assume_escape_era=False)

    live = library.load_book(book.path)
    assert not profile_from_manifest(live.extra_manifest).explicit
    assert [library.read_chapter(live, ch) for ch in live.sections[0].chapters] == originals
