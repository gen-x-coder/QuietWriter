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


def _settings(path: Path, *, spell=True, ai=True, advanced=True):
    settings = QSettings(str(path), QSettings.IniFormat)
    settings.setValue('spell_enabled', spell)
    settings.setValue('ai_enabled', ai)
    settings.setValue('advanced_options', advanced)
    return settings


def test_mainwindow_builds_when_spelling_is_disabled(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        window = MainWindow(_settings(root / 'settings.ini', spell=False), lib, [])
        assert window.editor_page.highlighter.spell_active is False
        assert window.spell_button.isHidden()
        window.close()


def test_settings_save_applies_spelling_and_hidden_return_target_immediately(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        book = lib.create_book('Instellingen runtime')
        window = MainWindow(_settings(root / 'settings.ini'), lib, [])
        window.open_book(book)

        # Give the highlighter a deterministic active dictionary state so this
        # test catches a missed settings_saved() callback without depending on
        # a bundled Hunspell dictionary.
        window.editor_page.dictionary.words = {'goed'}
        window.editor_page.highlighter.set_active(True)
        window.editor_page.highlighter.rehighlight()
        assert window.editor_page.highlighter.spell_active is True

        window.show_book_memory()
        window.open_settings()
        assert window._settings_return_page is window.book_memory_page

        # Rail preview is immediate, before Save.
        window.settings_page.ai_enabled.setChecked(False)
        window.settings_page.advanced_options.setChecked(False)
        app.processEvents()
        assert window.book_memory_button.isHidden()
        assert window.integrity_button.isHidden()

        window.settings_page.spell_enabled.setChecked(False)
        window.settings_page.save_settings()
        app.processEvents()

        # The committed callback must run while Settings is still open.
        assert window.editor_page.highlighter.spell_active is False
        assert window.spell_button.isHidden()
        # The now-hidden origin is redirected only on the committed pass.
        assert window._settings_return_page is window.editor_page

        window.return_from_settings()
        assert window.stack.currentWidget() is window.editor_page
        window.close()
