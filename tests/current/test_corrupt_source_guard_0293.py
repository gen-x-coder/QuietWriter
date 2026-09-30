import pytest

from quietwriter.storage import CorruptSourceError, Library
from quietwriter.planning_storage import PlanningStore

BAD = b'geldige start\xffongeldig'


def make(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Corrupt guard')
    return lib, book


def corrupt_then_track(lib, book, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(BAD)
    lib.track_book(book)
    return path.read_bytes()


def test_chapter_normal_save_cannot_replace_invalid_utf8(tmp_path):
    lib, book = make(tmp_path); chapter = book.sections[0].chapters[0]
    path = book.path / chapter.file; before = corrupt_then_track(lib, book, path)
    with pytest.raises(CorruptSourceError): lib.save_chapter(book, chapter, 'mag niet')
    assert path.read_bytes() == before


def test_book_memory_normal_save_cannot_replace_invalid_utf8(tmp_path):
    lib, book = make(tmp_path); path = lib.book_memory_path(book); before = corrupt_then_track(lib, book, path)
    with pytest.raises(CorruptSourceError): lib.save_book_memory(book, '# nieuw')
    assert path.read_bytes() == before


def test_book_profile_normal_save_cannot_replace_invalid_utf8(tmp_path):
    lib, book = make(tmp_path); path = lib.book_profile_path(book); before = corrupt_then_track(lib, book, path)
    with pytest.raises(CorruptSourceError): lib.save_book_profile(book, '# nieuw')
    assert path.read_bytes() == before


def test_planning_notes_normal_save_cannot_replace_invalid_utf8(tmp_path):
    lib, book = make(tmp_path); store = PlanningStore(lib); path = store.root(book) / 'notes.md'; before = corrupt_then_track(lib, book, path)
    with pytest.raises(CorruptSourceError): store.save_notes(book, 'mag niet')
    assert path.read_bytes() == before


def test_valid_empty_text_file_remains_writable(tmp_path):
    lib, book = make(tmp_path); path = lib.book_memory_path(book); path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b''); lib.track_book(book)
    lib.save_book_memory(book, '# geldig')
    assert path.read_text(encoding='utf-8') == '# geldig'
