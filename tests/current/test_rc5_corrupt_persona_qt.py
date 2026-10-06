import os
from pathlib import Path

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

pytest.importorskip('PySide6')
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from quietwriter.storage import Library
from quietwriter.ui.main_window import MainWindow
from quietwriter.ui.persona_page import PersonaPage


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _settings(path: Path, workspace: Path):
    settings = QSettings(str(path), QSettings.IniFormat)
    settings.setValue('workspace', str(workspace))
    settings.setValue('spell_enabled', False)
    settings.setValue('ai_enabled', False)
    settings.setValue('advanced_options', True)
    return settings


def test_corrupt_persona_opens_read_only_instead_of_crashing(app, tmp_path: Path):
    lib = Library(tmp_path)
    lib.persona_path().write_bytes(b'\xff')

    page = PersonaPage(lib)
    try:
        assert page._corrupt_source is True
        assert page.edit.isReadOnly() is True
        assert page.save_button.isEnabled() is False
        assert 'archive/persona/' in page.edit.toPlainText()
        assert page.save() is True
    finally:
        page.close()


def test_mainwindow_builds_with_corrupt_persona(app, tmp_path: Path):
    workspace = tmp_path / 'workspace'
    lib = Library(workspace)
    lib.persona_path().write_bytes(b'\xff')

    window = MainWindow(_settings(tmp_path / 'settings.ini', workspace), lib, [])
    try:
        assert window.persona._corrupt_source is True
        assert window.persona.edit.isReadOnly() is True
    finally:
        window.close()
