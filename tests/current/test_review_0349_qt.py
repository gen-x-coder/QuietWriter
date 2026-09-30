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


def test_acknowledge_notice_keeps_chapter_planning_off_and_persists(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        library = Library(root / 'library')
        book = library.create_book('Testboek')
        settings_path = root / 'settings.ini'
        settings = QSettings(str(settings_path), QSettings.IniFormat)
        assert not settings.contains('ai_use_chapter_planning')

        window = MainWindow(settings, library, [])
        window.open_book(book)
        window.show()
        app.processEvents()
        ai = window.editor_page.ai
        ai.context_panel.show()
        app.processEvents()

        assert not ai.chapter_planning_notice_row.isHidden()
        assert not ai.chapter_planning_check.isChecked()
        ai.chapter_planning_notice_ack.click()
        app.processEvents()
        assert ai.chapter_planning_notice_row.isHidden()
        assert not ai.chapter_planning_check.isChecked()
        assert settings.value('ai_use_chapter_planning', True, bool) is False
        window.close()

        settings2 = QSettings(str(settings_path), QSettings.IniFormat)
        window2 = MainWindow(settings2, library, [])
        window2.open_book(library.load_book(book.path))
        window2.show()
        app.processEvents()
        ai2 = window2.editor_page.ai
        assert ai2.chapter_planning_notice_row.isHidden()
        assert not ai2.chapter_planning_check.isChecked()
        window2.close()
