import os
import tempfile
from pathlib import Path

import pytest

pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from quietwriter.storage import Library
from quietwriter.ui.main_window import MainWindow




@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _settings(path: Path):
    settings = QSettings(str(path), QSettings.IniFormat)
    settings.setValue('workspace', str(path.parent / 'workspace'))
    settings.setValue('spell_enabled', True)
    settings.setValue('ai_enabled', True)
    settings.setValue('advanced_options', True)
    settings.setValue('nav_expanded', True)
    return settings


def test_cold_start_hides_all_current_book_navigation(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        window = MainWindow(_settings(root / 'settings.ini'), lib, [])
        window.show(); app.processEvents()

        assert window.active_book() is None
        for button in (
            window.write_button, window.planning_button, window.book_memory_button,
            window.book_profile_button, window.media_button, window.book_details_button,
            window.export_button, window.integrity_button,
        ):
            assert button.isHidden()
        assert window.book_group_label.isHidden()

        book = lib.create_book('Navigatie')
        window.open_book(book); app.processEvents()
        assert not window.write_button.isHidden()
        assert not window.planning_button.isHidden()
        assert not window.media_button.isHidden()
        assert not window.book_details_button.isHidden()
        assert not window.export_button.isHidden()
        assert not window.book_group_label.isHidden()

        window.go_home(); app.processEvents()
        assert window.active_book() is None
        assert window.book_group_label.isHidden()
        assert window.write_button.isHidden()
        window.close()


def test_settings_presentation_pass_does_not_dirty_or_create_planning_notes(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        book = lib.create_book('Notities')
        notes_path = Path(book.path) / 'planning' / 'notes.md'
        window = MainWindow(_settings(root / 'settings.ini'), lib, [])
        window.open_book(book); app.processEvents()
        notes = window.planning_page.notes_page
        assert notes.dirty is False
        assert not notes_path.exists()

        old_root = str(window.settings.value('workspace', ''))
        window.settings_saved(old_root)
        app.processEvents()
        assert notes.dirty is False
        assert not notes.timer.isActive()
        QTest.qWait(2800); app.processEvents()
        assert not notes_path.exists()
        window.close()


def test_planning_notes_preserve_typographic_source_on_save(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        book = lib.create_book('Bronnotities')
        notes_path = Path(book.path) / 'planning' / 'notes.md'
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        notes_path.write_text('Notitie met 10\u00a0euro.\nEen\u2028regel.', encoding='utf-8')
        book = lib.load_book(book.path)

        window = MainWindow(_settings(root / 'settings.ini'), lib, [])
        window.open_book(book); app.processEvents()
        notes = window.planning_page.notes_page
        cursor = notes.editor.textCursor(); cursor.movePosition(QTextCursor.End); cursor.insertText('x')
        app.processEvents()
        assert notes.dirty is True
        assert notes.save() is True
        saved = notes_path.read_text(encoding='utf-8')
        assert '10\u00a0euro' in saved
        assert '\u2028' in saved
        assert saved.endswith('x')
        window.close()
