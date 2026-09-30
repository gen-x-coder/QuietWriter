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


def _settings(path: Path):
    settings = QSettings(str(path), QSettings.IniFormat)
    settings.setValue('workspace', str(path.parent / 'workspace'))
    settings.setValue('spell_enabled', True)
    settings.setValue('ai_enabled', True)
    settings.setValue('advanced_options', True)
    return settings


def test_chapter_planning_toggle_controls_exact_saved_preview_text(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); lib = Library(root / 'workspace')
        book = lib.create_book('Chapter Planning')
        chapter = next(c for sec in book.sections for c in sec.chapters)
        store = PlanningStore(lib)
        store.save_characters(book, [Character(id='c1', name='Anna')])
        store.save_scenes(book, [Scene(
            id='s1', chapter_id=chapter.id, title='Aankomst', synopsis='SYNOPSIS_AUTO_0347',
            character_ids=['c1'], goal='DOEL_AUTO_0347',
        )])
        book = lib.load_book(book.path)

        window = MainWindow(_settings(root / 'settings.ini'), lib, [])
        window.open_book(book); window.show(); app.processEvents()
        ai = window.editor_page.ai
        preview = ai._chapter_planning_preview()
        assert 'SYNOPSIS_AUTO_0347' in preview.text
        assert ai.chapter_planning_check.isEnabled()
        assert not ai.chapter_planning_check.isChecked()
        assert not ai.chapter_planning_notice_row.isHidden()
        assert ai._active_chapter_planning_text() == ''

        ai.chapter_planning_check.setChecked(True); app.processEvents()
        assert ai._active_chapter_planning_text() == preview.text
        assert window.settings.value('ai_use_chapter_planning', False, bool) is True
        assert ai.chapter_planning_notice_row.isHidden()

        ai.chapter_planning_check.setChecked(False); app.processEvents()
        assert ai._active_chapter_planning_text() == ''
        assert window.settings.value('ai_use_chapter_planning', True, bool) is False
        window.force_return_to_bookshelf(); app.processEvents()
        assert not ai.planning_context_button.isEnabled()
        assert not ai.chapter_planning_check.isEnabled()
        window.close()
