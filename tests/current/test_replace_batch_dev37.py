"""Multi-chapter replacement checks on disposable books; never touches real data."""
import pytest
import quietwriter.storage as storage
from quietwriter.storage import Library, ChapterNotAvailableError


def setup_book(tmp_path):
    lib = Library(tmp_path / 'library')
    book = lib.create_book('Multi replace')
    first = book.sections[0].chapters[0]
    other = lib.add_chapter(book, book.sections[0], 'second')
    lib.save_chapter(book, first, 'hello first')
    lib.save_chapter(book, other, 'hello second')
    return lib, book, first, other


def test_batch_changes_both(tmp_path):
    lib,book,a,b=setup_book(tmp_path)
    assert lib.replace_chapters_guarded(book, {a.id:('hello first','bye first'),b.id:('hello second','bye second')})==2
    assert lib.read_chapter(book,a)=='bye first'
    assert lib.read_chapter(book,b)=='bye second'


def test_missing_second_blocks_first(tmp_path):
    lib,book,a,b=setup_book(tmp_path)
    (book.path / b.file).unlink()
    with pytest.raises(Exception):
        lib.replace_chapters_guarded(book, {a.id:('hello first','bye first'),b.id:('hello second','bye second')})
    assert lib.read_chapter(book,a)=='hello first'


def test_changed_second_blocks_first(tmp_path):
    lib,book,a,b=setup_book(tmp_path)
    with pytest.raises(Exception):
        lib.replace_chapters_guarded(book, {a.id:('hello first','bye first'),b.id:('different','bye second')})
    assert lib.read_chapter(book,a)=='hello first'


def test_second_write_failure_restores_first(tmp_path, monkeypatch):
    lib,book,a,b=setup_book(tmp_path)
    real=storage._safe_atomic_write_bytes
    target=book.path / b.file
    def flaky(path, data, *args, **kwargs):
        if path == target:
            raise OSError('simulated sharing violation')
        return real(path,data,*args,**kwargs)
    monkeypatch.setattr(storage,'_safe_atomic_write_bytes',flaky)
    with pytest.raises(OSError):
        lib.replace_chapters_guarded(book,{a.id:('hello first','bye first'),b.id:('hello second','bye second')})
    assert lib.read_chapter(book,a)=='hello first'
    assert lib.read_chapter(book,b)=='hello second'
