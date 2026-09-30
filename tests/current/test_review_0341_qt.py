import json
import os
import tempfile
from pathlib import Path

import pytest

pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from quietwriter.storage import Library
from quietwriter.themes import stylesheet
from quietwriter.ui.main_window import MainWindow


@pytest.fixture(scope='module')
def app():
    instance = QApplication.instance() or QApplication([])
    instance.setStyleSheet(stylesheet('Helder'))
    return instance


def _settings(path: Path, *, expanded=True):
    settings = QSettings(str(path), QSettings.IniFormat)
    settings.setValue('workspace', str(path.parent / 'workspace'))
    settings.setValue('spell_enabled', True)
    settings.setValue('ai_enabled', True)
    settings.setValue('advanced_options', True)
    settings.setValue('nav_expanded', expanded)
    return settings


def test_status_word_count_returns_after_temporary_message(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); lib = Library(root / 'workspace')
        window = MainWindow(_settings(root / 'settings.ini'), lib, [])
        window.show(); app.processEvents()
        window.open_book(lib.create_book('Status')); app.processEvents()
        assert 'Boek: 0 woorden · Hoofdstuk 1 van 1: 0 woorden' in window.status.currentMessage()
        window.status.showMessage('Tijdelijke melding', 20)
        QTest.qWait(80); app.processEvents()
        assert 'Boek: 0 woorden · Hoofdstuk 1 van 1: 0 woorden' in window.status.currentMessage()
        window.close()


def test_collapsed_rail_has_visible_group_separators(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); lib = Library(root / 'workspace')
        window = MainWindow(_settings(root / 'settings.ini', expanded=False), lib, [])
        window.show(); app.processEvents()
        window.open_book(lib.create_book('Separators')); app.processEvents()
        visible = [sep for sep in window._rail_separator_widgets.values() if not sep.isHidden()]
        assert len(visible) >= 2
        assert not window._rail_separator_widgets['current_book'].isHidden()
        assert not window._rail_separator_widgets['ai_context'].isHidden()
        assert all(sep.contentsRect().height() == 2 for sep in visible)
        window.close()


@pytest.mark.parametrize(('relative', 'payload', 'context_text', 'planning_text'), [
    ('planning/outline.json', {'version': 1, 'scenes': 5}, 'kan niet betrouwbaar worden gelezen', 'alleen-lezen'),
    ('planning/outline.json', {'version': 1, 'scenes': [{'id': 's1', 'character_ids': None}]}, 'kan niet betrouwbaar worden gelezen', 'alleen-lezen'),
    ('planning/characters.json', {'version': 1, 'characters': [{'id': 'c1', 'relations': 5}]}, 'kan niet betrouwbaar worden gelezen', 'alleen-lezen'),
    ('planning/outline.json', {'version': 2, 'scenes': []}, 'nieuwere QuietWriter', 'Werk QuietWriter bij'),
])
def test_wrong_planning_shape_does_not_block_book_open(app, relative, payload, context_text, planning_text):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); lib = Library(root / 'workspace')
        book = lib.create_book('Vormfout')
        path = book.path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding='utf-8')
        book = lib.load_book(book.path)
        window = MainWindow(_settings(root / 'settings.ini'), lib, [])
        window.show(); app.processEvents()
        window.open_book(book); app.processEvents()
        assert window.active_book() is not None
        assert window.stack.currentWidget() is window.editor_page
        window.editor_page.show_chapter_context(); app.processEvents()
        assert context_text in window.editor_page.chapter_context.message.text()
        window.show_planning(); app.processEvents()
        assert window.planning_page.source_warning.isVisible()
        assert planning_text in window.planning_page.source_warning.text()
        window.close()
