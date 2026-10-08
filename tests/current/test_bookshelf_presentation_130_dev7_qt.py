import os
import tempfile
from pathlib import Path

import pytest
pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from quietwriter.storage import Library
from quietwriter.ui.main_window import MainWindow
from quietwriter.ui.bookshelf import StartPage
import quietwriter.ui.bookshelf as bookshelf_module


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _clear_global_demo_settings():
    settings = QSettings('QuietWriter', 'QuietWriter')
    settings.clear()
    settings.sync()


def test_enabling_presentation_mode_closes_open_private_book(app):
    _clear_global_demo_settings()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        settings = QSettings(str(root / 'settings.ini'), QSettings.IniFormat)
        lib = Library(root / 'workspace')
        private = lib.shelves.create_shelf('Privé', private=True)
        book = lib.create_book('Geheim boek')
        lib.shelves.move_book(book.id, private.id)
        window = MainWindow(settings, lib, [])
        try:
            window.open_book(book)
            assert window.active_book() is not None
            window.start.demo_toggle.setChecked(True)
            app.processEvents()
            assert window.start.demo_mode_enabled() is True
            assert window.active_book() is None
            assert window.editor_page.book is None
            assert window.stack.currentWidget() is window.start
        finally:
            window.search_index.close()
            window.close()
            app.processEvents()
            _clear_global_demo_settings()


def test_presentation_mode_blocks_private_open_route(app):
    _clear_global_demo_settings()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        settings = QSettings(str(root / 'settings.ini'), QSettings.IniFormat)
        lib = Library(root / 'workspace')
        private = lib.shelves.create_shelf('Privé', private=True)
        book = lib.create_book('Geheim boek')
        lib.shelves.move_book(book.id, private.id)
        window = MainWindow(settings, lib, [])
        try:
            window.start.demo_toggle.setChecked(True)
            app.processEvents()
            window.open_book(book)
            app.processEvents()
            assert window.active_book() is None
            assert window.editor_page.book is None
            assert window.stack.currentWidget() is window.start
        finally:
            window.search_index.close()
            window.close()
            app.processEvents()
            _clear_global_demo_settings()


def test_word_count_cache_reuses_unchanged_chapters_and_invalidates_on_write(app, monkeypatch):
    _clear_global_demo_settings()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        book = lib.create_book('Cachetest')
        chapter = book.sections[0].chapters[0]
        lib.save_chapter(book, chapter, 'een twee drie')

        calls = []
        original = bookshelf_module.count_words
        def counted(text):
            calls.append(text)
            return original(text)
        monkeypatch.setattr(bookshelf_module, 'count_words', counted)

        page = StartPage(lib)
        page.refresh()
        first_calls = len(calls)
        assert first_calls >= 1
        page.refresh()
        assert len(calls) == first_calls

        chapter_path = book.path / chapter.file
        chapter_path.write_text('een twee drie vier vijf', encoding='utf-8')
        page.refresh()
        assert len(calls) == first_calls + 1
        page.deleteLater()
        app.processEvents()
        _clear_global_demo_settings()


def test_search_uses_200ms_single_shot_debounce(app):
    _clear_global_demo_settings()
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td) / 'workspace')
        page = StartPage(lib)
        assert page._search_refresh_timer.isSingleShot()
        assert page._search_refresh_timer.interval() == 200
        page.search.setText('abc')
        assert page._search_refresh_timer.isActive()
        page.deleteLater()
        app.processEvents()
        _clear_global_demo_settings()
