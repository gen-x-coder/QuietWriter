import os
import tempfile
from pathlib import Path

import pytest

pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication

from quietwriter.storage import Library
from quietwriter.ui.main_window import MainWindow


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _settings(path: Path, workspace: Path):
    settings = QSettings(str(path), QSettings.IniFormat)
    settings.setValue('workspace', str(workspace))
    settings.setValue('spell_enabled', True)
    settings.setValue('ai_enabled', True)
    settings.setValue('advanced_options', True)
    return settings


def _open_foreword(window):
    window.editor_page.open_publication_item('foreword')
    window.stack.setCurrentWidget(window.editor_page)
    QApplication.processEvents()
    return window.editor_page.publication_editor.free_text


def test_publication_presentation_pass_does_not_dirty(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        workspace = root / 'workspace'
        lib = Library(workspace)
        book = lib.create_book('Publicatie baseline')
        path = Path(book.path) / 'publication' / 'texts' / 'foreword.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('Voorwoord met 10\u00a0euro.\nEen\u2028regel.', encoding='utf-8')
        book = lib.load_book(book.path)

        window = MainWindow(_settings(root / 'settings.ini', workspace), lib, [])
        window.open_book(book)
        page = _open_foreword(window)
        original = path.read_bytes()
        assert page.dirty is False

        page.editor.presentation_highlighter.rehighlight()
        app.processEvents()
        assert page.dirty is False
        assert not page.timer.isActive()
        assert path.read_bytes() == original
        window.close()


def test_publication_edit_undo_and_save_move_clean_baseline(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        workspace = root / 'workspace'
        lib = Library(workspace)
        book = lib.create_book('Publicatie save')
        path = Path(book.path) / 'publication' / 'texts' / 'foreword.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('Tekst met 10\u00a0euro.', encoding='utf-8')
        book = lib.load_book(book.path)

        window = MainWindow(_settings(root / 'settings.ini', workspace), lib, [])
        window.open_book(book)
        page = _open_foreword(window)
        cursor = page.editor.textCursor(); cursor.movePosition(QTextCursor.End); cursor.insertText('x')
        app.processEvents()
        assert page.dirty is True
        page.editor.undo(); app.processEvents()
        assert page.dirty is False
        assert not page.timer.isActive()

        cursor = page.editor.textCursor(); cursor.movePosition(QTextCursor.End); cursor.insertText('y')
        app.processEvents()
        assert window.editor_page.publication_editor.save_pending() is True
        assert page.dirty is False
        assert page._clean_text == page.editor.source_text()
        assert '10\u00a0euro' in path.read_text(encoding='utf-8')
        window.close()
