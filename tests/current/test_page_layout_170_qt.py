"""1.7.0-dev15: één vorm voor formulier- en documentpagina's (roadmap 6.2)."""
import os

import pytest
pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QLabel, QListWidget

from quietwriter.storage import Library
from quietwriter.ui.page_layout import PAGE_MARGINS


@pytest.fixture
def window(tmp_path):
    app = QApplication.instance() or QApplication([])
    from quietwriter.ui.main_window import MainWindow
    lib = Library(tmp_path / 'ws')
    book = lib.create_book('Vorm')
    settings = QSettings(str(tmp_path / 's.ini'), QSettings.IniFormat)
    settings.setValue('workspace', str(lib.root))
    w = MainWindow(settings, lib, [])
    w.open_book(book)
    yield w
    w.close()


def test_document_pages_use_the_same_subnavigation_as_settings_and_planning(window):
    for page in (window.book_profile_page, window.book_memory_page, window.persona):
        lists = [w for w in page.findChildren(QListWidget) if w.objectName() == 'contextSectionList']
        assert len(lists) == 1, page
        assert 'Onderdelen' not in {label.text() for label in page.findChildren(QLabel)}


def test_pages_share_the_same_outer_margins(window):
    window.open_current_book_details()
    for page in (window.book_details_page, window.book_profile_page, window.book_memory_page, window.persona,
                 window.darlings_page, window.media_manager_page, window.integrity_page, window.trash):
        margins = page.layout().contentsMargins()
        assert (margins.left(), margins.top(), margins.right()) == PAGE_MARGINS[:3], type(page).__name__
