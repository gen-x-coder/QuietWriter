from pathlib import Path
import os
import pytest

pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from quietwriter.storage import Library
from quietwriter.ui.main_window import MainWindow


def test_closing_from_bookshelf_preserves_editor_pane_preferences(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    workspace = tmp_path / 'workspace'
    lib = Library(workspace)
    settings_path = tmp_path / 'settings.ini'
    settings = QSettings(str(settings_path), QSettings.IniFormat)
    settings.setValue('spell_enabled', False)
    settings.setValue('ai_enabled', False)
    settings.setValue('advanced_options', False)

    window = MainWindow(settings, lib, [])
    window.editor_page.manuscript.setVisible(True)
    window.editor_page.right.setVisible(False)
    window.stack.setCurrentWidget(window.start)
    window.close()

    settings2 = QSettings(str(settings_path), QSettings.IniFormat)
    assert settings2.value('manuscript_visible', False, bool) is True
    assert settings2.value('right_visible', True, bool) is False
