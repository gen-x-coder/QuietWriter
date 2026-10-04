from pathlib import Path
import pytest

from quietwriter.storage import Library


def make(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Bloktest')
    lib.track_book(book)
    return lib, book


def test_blocked_book_rejects_late_writes_until_reopened(tmp_path):
    lib, book = make(tmp_path)
    chapter = book.sections[0].chapters[0]
    before = (book.path / chapter.file).read_bytes()
    lib.block_book(book)
    with pytest.raises(RuntimeError, match='geblokkeerd'):
        lib.save_chapter(book, chapter, 'MAG NIET')
    assert (book.path / chapter.file).read_bytes() == before

    # Explicit reopening/retracking is the only operation that clears the block.
    reopened = lib.load_book(book.path)
    lib.track_book(reopened)
    lib.save_chapter(reopened, reopened.sections[0].chapters[0], 'MAG WEL')
    assert (reopened.path / reopened.sections[0].chapters[0].file).read_text(encoding='utf-8') == 'MAG WEL'


def test_untrack_does_not_leave_a_write_block(tmp_path):
    lib, book = make(tmp_path)
    lib.untrack_book(book)
    lib.track_book(book)
    lib.verify_book_unchanged(book)
