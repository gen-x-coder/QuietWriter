import json
import os
import tempfile
from pathlib import Path

import pytest
pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication

from quietwriter.storage import Library
from quietwriter.ui.bookshelf import StartPage
import quietwriter.ui.bookshelf as bookshelf_module


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def test_word_count_cache_uses_hashed_chapter_keys(app, monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        book = lib.create_book('GEHEIMTITEL roman')
        chapter = book.sections[0].chapters[0]
        lib.save_chapter(book, chapter, 'een twee drie vier')
        cache_file = root / 'local' / 'word-counts.json'
        monkeypatch.setattr(StartPage, '_word_count_cache_path', lambda self: cache_file)

        page = StartPage(lib)
        try:
            raw = json.loads(cache_file.read_text(encoding='utf-8'))
            assert raw
            assert all(len(key) == 64 and set(key) <= set('0123456789abcdef') for key in raw)
            assert 'geheimtitel' not in cache_file.read_text(encoding='utf-8').lower()
            assert str(book.path) not in cache_file.read_text(encoding='utf-8')
        finally:
            page.deleteLater(); app.processEvents()


def test_old_path_key_cache_is_rebuilt_without_retaining_title(app, monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        book = lib.create_book('GEHEIMTITEL roman')
        chapter = book.sections[0].chapters[0]
        lib.save_chapter(book, chapter, 'een twee drie')
        cache_file = root / 'local' / 'word-counts.json'
        cache_file.parent.mkdir(parents=True)
        chapter_path = Path(book.path) / chapter.file
        stat = chapter_path.stat()
        cache_file.write_text(json.dumps({str(chapter_path): [stat.st_mtime_ns, stat.st_size, 999]}), encoding='utf-8')
        monkeypatch.setattr(StartPage, '_word_count_cache_path', lambda self: cache_file)

        calls = []
        original = bookshelf_module.count_words
        def counted(text):
            calls.append(text)
            return original(text)
        monkeypatch.setattr(bookshelf_module, 'count_words', counted)

        page = StartPage(lib)
        try:
            raw = json.loads(cache_file.read_text(encoding='utf-8'))
            assert calls
            assert list(raw.values())[0][2] == 3
            assert all(len(key) == 64 and set(key) <= set('0123456789abcdef') for key in raw)
            assert 'geheimtitel' not in cache_file.read_text(encoding='utf-8').lower()
        finally:
            page.deleteLater(); app.processEvents()
