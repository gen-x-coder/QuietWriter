import os
import tempfile
from pathlib import Path

import pytest
pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from quietwriter.storage import Library
from quietwriter.ui.bookshelf import StartPage
from quietwriter.ui.main_window import MainWindow
import quietwriter.ui.bookshelf as bookshelf_module


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def test_start_page_uses_runtime_profile_settings(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        settings = QSettings(str(root / 'dev-settings.ini'), QSettings.IniFormat)
        settings.setValue('bookshelf_demo_mode', True)
        settings.sync()
        lib = Library(root / 'workspace')
        page = StartPage(lib, settings)
        try:
            assert page.settings is settings
            assert page.demo_mode_enabled() is True
            page.demo_toggle.setChecked(False)
            settings.sync()
            assert settings.value('bookshelf_demo_mode', True, bool) is False
        finally:
            page.deleteLater()
            app.processEvents()


def _private_book_window(root: Path):
    settings = QSettings(str(root / 'dev-settings.ini'), QSettings.IniFormat)
    lib = Library(root / 'workspace')
    private = lib.shelves.create_shelf('Privé', private=True)
    book = lib.create_book('Geheim boek')
    lib.shelves.move_book(book.id, private.id)
    window = MainWindow(settings, lib, [])
    window.open_book(book)
    return window, settings


def test_presentation_reverts_in_same_settings_store_when_close_fails(app, monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        window, settings = _private_book_window(Path(td))
        try:
            monkeypatch.setattr(window, 'go_home', lambda: None)
            window.start.demo_toggle.setChecked(True)
            app.processEvents()
            settings.sync()
            assert window.active_book() is not None
            assert window.start.demo_toggle.isChecked() is False
            assert window.start.demo_mode_enabled() is False
            assert settings.value('bookshelf_demo_mode', True, bool) is False
        finally:
            window.search_index.close()
            window.close()
            app.processEvents()


def test_presentation_reverts_after_unexpected_close_exception(app, monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        window, settings = _private_book_window(Path(td))
        try:
            def explode():
                raise PermissionError('simulated unexpected close failure')
            monkeypatch.setattr(window, 'go_home', explode)
            window.start.demo_toggle.setChecked(True)
            app.processEvents()
            settings.sync()
            assert window.active_book() is not None
            assert window.start.demo_toggle.isChecked() is False
            assert window.start.demo_mode_enabled() is False
            assert settings.value('bookshelf_demo_mode', True, bool) is False
        finally:
            window.search_index.close()
            window.close()
            app.processEvents()


def test_word_count_cache_survives_new_start_page(app, monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        book = lib.create_book('Cachetest')
        chapter = book.sections[0].chapters[0]
        lib.save_chapter(book, chapter, 'een twee drie vier')
        cache_file = root / 'local' / 'word-counts.json'
        monkeypatch.setattr(StartPage, '_word_count_cache_path', lambda self: cache_file)

        calls = []
        original = bookshelf_module.count_words
        def counted(text):
            calls.append(text)
            return original(text)
        monkeypatch.setattr(bookshelf_module, 'count_words', counted)

        first = StartPage(lib)
        first_calls = len(calls)
        assert first_calls >= 1
        assert cache_file.exists()
        first.deleteLater(); app.processEvents()

        second = StartPage(lib)
        try:
            assert len(calls) == first_calls
            assert second._word_count_cache
        finally:
            second.deleteLater(); app.processEvents()
