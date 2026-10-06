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


def _settings(path: Path):
    settings = QSettings(str(path), QSettings.IniFormat)
    settings.setValue('spell_enabled', True)
    settings.setValue('ai_enabled', True)
    settings.setValue('advanced_options', True)
    return settings


def test_special_source_characters_do_not_create_false_dirty_and_are_not_rewritten(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        book = lib.create_book('Bijzondere tekens')
        chapter = next(c for sec in book.sections for c in sec.chapters)
        path = Path(book.path) / chapter.file
        original = '\ufeffHij betaalde 10\u00a0euro.\nEen\u2028regel.\nEen\u2029alinea.'
        path.write_text(original, encoding='utf-8')
        book = lib.load_book(book.path)

        window = MainWindow(_settings(root / 'settings.ini'), lib, [])
        window.open_book(book)
        before = path.read_bytes()

        # Presentation work must compare Qt's source representation with the
        # baseline captured from the same representation, not with raw disk text.
        window.editor_page.highlighter.rehighlight()
        app.processEvents()
        assert window.editor_page.dirty is False
        assert not window.editor_page.autosave_timer.isActive()
        assert path.read_bytes() == before
        window.close()


def test_normal_save_preserves_nbsp_and_unicode_line_separator(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        book = lib.create_book('Typografische bron')
        chapter = next(c for sec in book.sections for c in sec.chapters)
        path = Path(book.path) / chapter.file
        original = 'Hij betaalde 10\u00a0euro op p.\u00a05.\nEen\u2028regel.'
        path.write_text(original, encoding='utf-8')
        book = lib.load_book(book.path)

        window = MainWindow(_settings(root / 'settings.ini'), lib, [])
        window.open_book(book)
        cursor = window.editor_page.editor.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText('x')
        app.processEvents()
        assert window.editor_page.dirty is True
        assert window.editor_page.save() is True

        saved = path.read_text(encoding='utf-8')
        assert '10\u00a0euro' in saved
        assert 'p.\u00a05' in saved
        assert '\u2028' in saved
        assert saved.endswith('x')
        window.close()
