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
    settings.setValue('autosave', False)
    settings.setValue('ai_enabled', False)
    return settings


def test_adopt_active_book_rebinds_every_page_to_one_object(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        settings = _settings(root / 'settings.ini')
        book = lib.create_book('Live book')
        window = MainWindow(settings, lib, [])
        window.open_book(book)

        live = window.active_book()
        assert live is window.editor_page.book
        assert live is window.planning_page.book
        assert live is window.book_details_page.book
        assert live is window.export_page.book

        old_chapter_id = window.editor_page.chapter.id
        external_lib = Library(root / 'workspace')
        external = external_lib.load_book(live.path)
        added = external_lib.add_chapter(external, external.sections[0], 'Extern hoofdstuk')
        external_lib.save_chapter(external, added, 'tekst van B')

        latest = lib.load_book(live.path)
        window.adopt_active_book(latest, old_chapter_id)

        assert latest is window.active_book()
        assert latest is window.editor_page.book
        assert latest is window.planning_page.book
        assert latest is window.book_details_page.book
        assert latest is window.export_page.book
        assert window.editor_page.chapter.id == old_chapter_id
        assert any(c.id == added.id for s in latest.sections for c in s.chapters)
        assert any(c is window.editor_page.chapter for s in latest.sections for c in s.chapters)

        window.close()
