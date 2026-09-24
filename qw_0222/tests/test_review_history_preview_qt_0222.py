import os
import tempfile
from pathlib import Path

import pytest

pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QMessageBox

from quietwriter.storage import Library
from quietwriter.ui.main_window import MainWindow
import quietwriter.ui.editor_page as editor_page_module


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _settings(path: Path):
    settings = QSettings(str(path), QSettings.IniFormat)
    settings.setValue('autosave', False)
    settings.setValue('ai_enabled', False)
    return settings


def _book_with_version(root: Path):
    lib = Library(root / 'workspace')
    book = lib.create_book('History test')
    chapter = book.sections[0].chapters[0]
    lib.save_chapter(book, chapter, 'Tekst uit het archief.')
    version = lib.create_version(book, kind='manual')
    lib.save_chapter(book, chapter, 'Actuele live tekst.')
    return lib, book, chapter.id, version


def test_leaving_editor_closes_preview_and_never_writes_archive(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib, book, chapter_id, version = _book_with_version(root)
        window = MainWindow(_settings(root / 'settings.ini'), lib, [])
        window.open_book(book)

        archive_chapter = Path(version['path']) / window.editor_page.chapter.file
        before = archive_chapter.read_bytes()
        window.editor_page.enter_history_preview(version['id'])
        assert window.editor_page.preview_live_book is not None
        assert window.editor_page.book.path == Path(version['path'])

        # Programmatic replacement must be blocked even though the historical
        # editor contains a matching string.
        window.editor_page.search.query.setText('archief')
        window.editor_page.search.replace.setText('BESCHADIGD')
        window.editor_page.replace_all_matches()
        assert archive_chapter.read_bytes() == before
        assert 'BESCHADIGD' not in window.editor_page.editor.toPlainText()

        # Moving to Planning exits preview and binds Planning to the live book.
        window.show_planning()
        assert window.editor_page.preview_live_book is None
        assert window.editor_page.book is window.active_book()
        assert window.planning_page.book is window.active_book()
        assert window.active_book().path == book.path
        assert archive_chapter.read_bytes() == before

        # Export follows the same rule after a second preview.
        window.show_editor()
        window.editor_page.enter_history_preview(version['id'])
        window.show_export()
        assert window.editor_page.preview_live_book is None
        assert window.export_page.book is window.active_book()
        assert window.export_page.book.path == book.path
        assert archive_chapter.read_bytes() == before
        window.close()


def test_restore_conflict_exits_preview_and_adopts_newest_live_disk(app, monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib, book, chapter_id, version = _book_with_version(root)
        window = MainWindow(_settings(root / 'settings.ini'), lib, [])
        window.open_book(book)
        window.editor_page.enter_history_preview(version['id'])

        archive_book = Path(version['path'])
        archive_before = {
            path.relative_to(archive_book): path.read_bytes()
            for path in archive_book.rglob('*') if path.is_file()
        }

        # Simulate Dropbox/computer B changing the live chapter while A is in
        # history preview. The Library in the window still tracks the old state.
        other = Library(root / 'workspace')
        external = other.load_book(book.path)
        _, external_chapter = next(
            (section, chapter)
            for section in external.sections
            for chapter in section.chapters
            if chapter.id == chapter_id
        )
        other.save_chapter(external, external_chapter, 'Tekst van computer B.')

        monkeypatch.setattr(editor_page_module, 'confirm', lambda *args, **kwargs: True)
        warnings = []
        monkeypatch.setattr(QMessageBox, 'warning', lambda *args, **kwargs: warnings.append(args[2] if len(args) > 2 else ''))

        window.editor_page.restore_preview_version()

        assert window.editor_page.preview_live_book is None
        assert window.editor_page.book is window.active_book()
        assert window.active_book().path == book.path
        assert window.editor_page.editor.toPlainText() == 'Tekst van computer B.'
        assert warnings

        archive_after = {
            path.relative_to(archive_book): path.read_bytes()
            for path in archive_book.rglob('*') if path.is_file()
        }
        assert archive_after == archive_before
        window.close()
