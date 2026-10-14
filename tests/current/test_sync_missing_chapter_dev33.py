"""A cloud-missing manuscript must never silently become an empty file."""
from pathlib import Path
import pytest
from quietwriter.storage import Library, Book, Chapter, ChapterNotAvailableError


def test_missing_referenced_chapter_never_becomes_empty_or_writable(tmp_path):
    library = Library(tmp_path / 'workspace')
    book_dir = library.books_dir / 'remote-book'
    book_dir.mkdir()
    book = Book(id='remote', title='Op laptop', path=book_dir)
    chapter = Chapter(id='synced-metadata', title='Hoofdstuk', file='chapters/synced.md')
    with pytest.raises(ChapterNotAvailableError):
        library.read_chapter(book, chapter)
    with pytest.raises(ChapterNotAvailableError):
        library.save_chapter(book, chapter, 'NIET SCHRIJVEN')
    assert not (book_dir / chapter.file).exists()


def test_truly_empty_existing_chapter_is_still_editable(tmp_path):
    library = Library(tmp_path / 'workspace')
    book_dir = library.books_dir / 'new-book'
    (book_dir / 'chapters').mkdir(parents=True)
    chapter = Chapter(id='new', title='Nieuw', file='chapters/new.md')
    path = book_dir / chapter.file
    path.write_text('', encoding='utf-8')
    book = Book(id='new', title='Nieuw', path=book_dir)
    assert library.read_chapter(book, chapter) == ''
