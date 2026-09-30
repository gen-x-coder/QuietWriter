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


def _settings(path: Path):
    settings = QSettings(str(path), QSettings.IniFormat)
    settings.setValue('spell_enabled', True)
    settings.setValue('ai_enabled', True)
    settings.setValue('advanced_options', True)
    settings.setValue('nav_expanded', True)
    return settings


def test_settings_save_and_spell_presentation_do_not_dirty_or_rewrite_chapter(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        book = lib.create_book('Geen valse dirty')
        window = MainWindow(_settings(root / 'settings.ini'), lib, [])
        window.open_book(book)
        chapter = next(c for sec in window.active_book().sections for c in sec.chapters)
        path = Path(window.active_book().path) / chapter.file
        before = path.read_bytes()

        window.open_settings()
        window.settings_page.save_settings()
        app.processEvents()
        assert window.editor_page.dirty is False
        assert not window.editor_page.autosave_timer.isActive()
        assert path.read_bytes() == before

        # A presentation-only spelling rehighlight must remain clean too.
        window.editor_page.highlighter.rehighlight()
        app.processEvents()
        assert window.editor_page.dirty is False
        assert not window.editor_page.autosave_timer.isActive()
        assert path.read_bytes() == before
        window.close()


def test_live_preview_updates_group_gap_and_preserves_open_ai_panel(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        book = lib.create_book('Preview')
        window = MainWindow(_settings(root / 'settings.ini'), lib, [])
        window.open_book(book)
        window.rail_expanded = True
        window._apply_nav_width(False)

        # Keep AI panel open before entering Settings.
        window.editor_page.right.setCurrentWidget(window.editor_page.ai)
        window.editor_page.right.show()
        window.open_settings()
        window.settings_page.ai_enabled.setChecked(False)
        window.settings_page.advanced_options.setChecked(False)
        app.processEvents()
        assert window.writing_group_label.isHidden()
        assert window.integrity_gap.isHidden()
        assert window.editor_page.right.currentWidget() is window.editor_page.ai

        # Toggling the rail during preview must keep preview state.
        window.toggle_nav(); window.toggle_nav()
        app.processEvents()
        assert window.writing_group_label.isHidden()
        assert window.integrity_gap.isHidden()

        # Leave without saving: committed state and panel are restored/preserved.
        window.show_editor()
        app.processEvents()
        assert not window.persona_button.isHidden()
        assert not window.integrity_button.isHidden()
        assert window.editor_page.right.currentWidget() is window.editor_page.ai
        window.close()
