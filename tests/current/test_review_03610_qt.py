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


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _settings(path: Path, model: str):
    s = QSettings(str(path), QSettings.IniFormat)
    s.setValue('ai_enabled', True)
    s.setValue('ai_provider', 'openrouter')
    s.setValue('openrouter_model', model)
    s.setValue('openrouter_free_only', True)
    s.setValue('advanced_options', True)
    s.sync()
    return s


@pytest.mark.parametrize('model', ['meta/llama:free', 'anthropic/claude-x'])
def test_free_filter_does_not_erase_saved_model_before_catalog_refresh(app, model):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        settings = _settings(root / 'settings.ini', model)
        lib = Library(root / 'workspace')
        window = MainWindow(settings, lib, [])
        window.open_settings()
        page = window.settings_page
        assert page.openrouter_free_only.isChecked()
        assert page._selected_ai_model() == model
        page.theme.setCurrentText(page.theme.itemText((page.theme.currentIndex() + 1) % page.theme.count()))
        page.save_settings()
        settings.sync()
        assert str(settings.value('openrouter_model', '')) == model
        window.close()
        window.search_index.close()
        app.processEvents()
        window.search_index.close()
        app.processEvents()


def test_long_book_title_with_reader_open_does_not_force_wide_window(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        settings = QSettings(str(root / 'settings.ini'), QSettings.IniFormat)
        settings.setValue('ai_enabled', True)
        settings.setValue('advanced_options', True)
        lib = Library(root / 'workspace')
        book = lib.create_book('De verloren haven van Antwerpen en nog een bijzonder lange subtitel')
        window = MainWindow(settings, lib, [])
        window.open_book(book)
        window.editor_page.right.setCurrentWidget(window.editor_page.ai)
        window.editor_page.right.show()
        app.processEvents()
        assert window.minimumSizeHint().width() <= 1100
        assert window.editor_page.book_title_label.toolTip() == book.title
        window.close()
