import os
import tempfile
from pathlib import Path

import pytest

pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from quietwriter.planning_models import Character, Scene
from quietwriter.planning_storage import PlanningStore
from quietwriter.storage import Library
from quietwriter.themes import stylesheet
from quietwriter.ui.main_window import MainWindow


@pytest.fixture(scope='module')
def app():
    instance = QApplication.instance() or QApplication([])
    instance.setStyleSheet(stylesheet('Helder'))
    return instance


def _settings(path: Path, *, ai=True, advanced=True, expanded=True):
    settings = QSettings(str(path), QSettings.IniFormat)
    settings.setValue('workspace', str(path.parent / 'workspace'))
    settings.setValue('spell_enabled', True)
    settings.setValue('ai_enabled', ai)
    settings.setValue('advanced_options', advanced)
    settings.setValue('nav_expanded', expanded)
    return settings


def test_program_and_scroll_nav_share_one_selection_group(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); lib = Library(root / 'workspace')
        window = MainWindow(_settings(root / 'settings.ini'), lib, [])
        window.show(); app.processEvents()
        window.open_book(lib.create_book('Selectie')); app.processEvents()

        window.show_persona(); app.processEvents()
        assert window.persona_button.isChecked()
        window.show_editor(); app.processEvents()
        assert window.write_button.isChecked()
        assert not window.persona_button.isChecked()

        window.open_settings(); app.processEvents()
        assert window.settings_button.isChecked()
        window.return_from_settings(); app.processEvents()
        assert not window.settings_button.isChecked()

        window.show_trash(); app.processEvents()
        assert window.trash_button.isChecked()
        window.show_planning(); app.processEvents()
        assert window.planning_button.isChecked()
        assert not window.trash_button.isChecked()
        window.close()


def test_active_scroll_item_is_brought_into_view(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); lib = Library(root / 'workspace')
        window = MainWindow(_settings(root / 'settings.ini', expanded=True), lib, [])
        window.resize(1280, 700); window.show(); app.processEvents()
        window.open_book(lib.create_book('Scroll')); app.processEvents()
        window.rail_scroll.verticalScrollBar().setValue(0)
        window.show_book_profile(); app.processEvents()
        assert window.book_profile_button.isChecked()
        assert window.rail_scroll.verticalScrollBar().value() > 0
        window.close()


def test_in_this_chapter_panel_uses_saved_planning_and_ignores_ai_switch(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); lib = Library(root / 'workspace')
        settings = _settings(root / 'settings.ini', ai=False)
        window = MainWindow(settings, lib, [])
        window.show(); app.processEvents()
        book = lib.create_book('Context')
        chapter = next(c for section in book.sections for c in section.chapters)
        store = PlanningStore(lib)
        person = Character(id='p1', name='Mara', role='Hoofdpersoon')
        scene = Scene(id='s1', chapter_id=chapter.id, title='De ontmoeting', synopsis='Mara komt binnen.', character_ids=['p1'])
        store.save_characters(book, [person])
        store.save_scenes(book, [scene])
        # Re-open after Planning writes refreshed the tracked revision.
        book = lib.load_book(book.path)
        window.open_book(book); app.processEvents()

        assert not window.chapter_context_button.isHidden()
        assert window.ai_button.isHidden()
        window.editor_page.show_chapter_context(); app.processEvents()
        panel = window.editor_page.chapter_context
        assert panel.isVisible()
        labels = [w.text() for w in panel.findChildren(type(panel.message))]
        joined = '\n'.join(labels)
        assert 'De ontmoeting' in joined
        assert 'Mara' in joined
        window.close()


def test_context_hidden_for_publication_history_and_corrupt_chapter(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); lib = Library(root / 'workspace')
        window = MainWindow(_settings(root / 'settings.ini'), lib, [])
        window.show(); app.processEvents()
        book = lib.create_book('Randgevallen')
        window.open_book(book); app.processEvents()
        assert not window.chapter_context_button.isHidden()

        window.editor_page._set_publication_context(); window.sync_tool_buttons(); app.processEvents()
        assert window.chapter_context_button.isHidden()

        # Return to the live manuscript and emulate the protected corrupt state.
        chapter = next(c for section in book.sections for c in section.chapters)
        window.editor_page._set_editor_chapter(chapter); app.processEvents()
        window.editor_page._chapter_corrupt = True
        window.editor_page.refresh_chapter_context(); window.sync_tool_buttons(); app.processEvents()
        assert window.chapter_context_button.isHidden()
        window.close()
