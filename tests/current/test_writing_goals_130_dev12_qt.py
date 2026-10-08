import os

import pytest
pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QDate, QSettings
from PySide6.QtWidgets import QApplication, QLabel

from quietwriter.storage import Library
from quietwriter.ui.book_details import BookDetailsPage


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def test_goal_date_is_explicit_compact_and_defaults_to_today(app, tmp_path):
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.IniFormat)
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Roman')
    page = BookDetailsPage(lib, settings, book)

    assert page.goal_date.date() == QDate.currentDate()
    assert bool(page.goal_date_mode.currentData()) is False
    assert page.goal_date.maximumWidth() <= 180
    assert page.goal_date.isEnabled() is False

    page.word_goal.setValue(80000)
    assert page.goal_date_mode.isEnabled() is True
    assert page.goal_date.isEnabled() is False
    page.goal_date_mode.setCurrentIndex(page.goal_date_mode.findData(True))
    assert page.goal_date.isEnabled() is True
    assert page._goal_date_iso() == QDate.currentDate().toString('yyyy-MM-dd')


def test_bookdetails_goal_and_cover_use_settings_style_section_labels(app, tmp_path):
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.IniFormat)
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Roman')
    page = BookDetailsPage(lib, settings, book)
    labels = [w for w in page.findChildren(QLabel) if w.objectName() == 'settingsFieldLabel']
    texts = {w.text() for w in labels}
    assert 'Schrijfdoel' in texts
    assert 'Boekomslag' in texts
