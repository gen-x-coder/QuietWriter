import os
import tempfile
from pathlib import Path

import pytest

pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from quietwriter.storage import Library
from quietwriter.themes import stylesheet
from quietwriter.ui.main_window import MainWindow


@pytest.fixture(scope='module')
def app():
    instance = QApplication.instance() or QApplication([])
    instance.setStyleSheet(stylesheet('Helder'))
    return instance


def _settings(path: Path, *, expanded=False):
    settings = QSettings(str(path), QSettings.IniFormat)
    settings.setValue('workspace', str(path.parent / 'workspace'))
    settings.setValue('spell_enabled', True)
    settings.setValue('ai_enabled', True)
    settings.setValue('advanced_options', True)
    settings.setValue('nav_expanded', expanded)
    return settings


def test_planning_context_button_enabled_after_real_open_book_route(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); lib = Library(root / 'workspace')
        window = MainWindow(_settings(root / 'settings.ini'), lib, [])
        window.show(); app.processEvents()
        assert not window.editor_page.ai.planning_context_button.isEnabled()
        window.open_book(lib.create_book('Planning button')); app.processEvents()
        assert window.editor_page.ai.planning_context_button.isEnabled()
        window.close()


def test_program_separator_hidden_when_middle_does_not_scroll_and_visible_when_it_does(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); lib = Library(root / 'workspace')
        window = MainWindow(_settings(root / 'settings.ini', expanded=False), lib, [])
        window.open_book(lib.create_book('Responsive separator'))

        window.resize(1280, 1000); window.show(); app.processEvents()
        assert window.rail_scroll.verticalScrollBar().maximum() == 0
        assert window._rail_separator_widgets['program'].isHidden()

        window.resize(1280, 520); app.processEvents()
        # On a short window the middle navigation scrolls; the fixed PROGRAMMA
        # block gets a separator because the text group labels are collapsed.
        assert window.rail_scroll.verticalScrollBar().maximum() > 0
        assert not window._rail_separator_widgets['program'].isHidden()
        window.close()
