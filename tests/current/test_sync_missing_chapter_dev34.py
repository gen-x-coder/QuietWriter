"""Cloud placeholders must never be copied or snapshotted as an empty manuscript."""
import pytest
from quietwriter.storage import Library, ChapterNotAvailableError


def _book_with_missing_chapter(tmp_path):
    library = Library(tmp_path / 'workspace')
    book = library.create_book('Sync test')
    section = book.sections[0]
    chapter = section.chapters[0]
    source = book.path / chapter.file
    source.unlink()
    return library, book, chapter, source


def test_duplicate_missing_manuscript_never_creates_empty_copy(tmp_path):
    library, book, chapter, source = _book_with_missing_chapter(tmp_path)
    before = {x.name for x in (book.path / 'chapters').iterdir()}
    with pytest.raises(ChapterNotAvailableError):
        library.duplicate_chapter(book, chapter.id)
    assert not source.exists()
    assert before == {x.name for x in (book.path / 'chapters').iterdir()}


def test_conflict_snapshot_missing_manuscript_is_not_complete(tmp_path):
    library, book, chapter, source = _book_with_missing_chapter(tmp_path)
    with pytest.raises(ChapterNotAvailableError):
        library.create_version_from_state(book)
    assert not source.exists()
    assert not any(p.name == 'book.json' for p in library._history_root(book).rglob('book.json'))
