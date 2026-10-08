import os
from pathlib import Path

import pytest
pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel

from quietwriter.storage import Library
from quietwriter.ui.book_details import BookDetailsPage
from quietwriter.ui.bookshelf import StartPage
from quietwriter.ui.main_window import MainWindow


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def test_tracking_is_opt_in_and_owned_by_settings_not_bookdetails(app, tmp_path):
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.IniFormat)
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Roman')
    page = BookDetailsPage(lib, settings, book)
    assert not hasattr(page, 'progress_tracking')
    assert settings.value('writing_progress_enabled', False, bool) is False
    page.word_goal.setValue(80000)
    assert page.save() is True
    assert settings.value('writing_progress_enabled', False, bool) is False
    loaded = lib.load_book(book.path)
    assert loaded.metadata['writing_goal_words'] == 80000


def test_bookshelf_shows_goal_progress_only_for_book_with_goal(app, tmp_path):
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.IniFormat)
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Roman')
    ch = book.sections[0].chapters[0]
    lib.save_chapter(book, ch, 'een twee drie vier')
    book.metadata['writing_goal_words'] = 10
    lib.save_manifest(book)
    page = StartPage(lib, settings)
    texts = [w.text() for w in page.findChildren(QLabel)]
    assert any('4' in text and '10' in text for text in texts)


def test_positive_save_delta_pauses_when_disabled_and_resumes_without_catchup(app, tmp_path):
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.IniFormat)
    settings.setValue('writing_progress_enabled', True)
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Roman')
    book.metadata['writing_goal_words'] = 50000
    lib.save_manifest(book)
    win = MainWindow(settings, lib, [])
    win.open_book(lib.load_book(book.path)); app.processEvents()
    ed = win.editor_page.editor
    progress_file = tmp_path / 'progress.json'
    win.editor_page.writing_progress.path = progress_file
    win.editor_page.writing_progress._data = {'schema_version': 1, 'books': {}}

    QTest.keyClicks(ed, 'een twee drie vier vijf')
    assert win.editor_page.save() is True
    assert win.editor_page.writing_progress.today(book.id) == 5

    # Deleting saved text is work, but never subtracts from today's counter.
    ed.setPlainText('een twee drie')
    win.editor_page.dirty = True
    assert win.editor_page.save() is True
    assert win.editor_page.writing_progress.today(book.id) == 5

    # Disabled means no collection, and re-enabling may not count the disabled period retroactively.
    settings.setValue('writing_progress_enabled', False)
    ed.setPlainText('een twee drie vier vijf zes zeven')
    win.editor_page.dirty = True
    assert win.editor_page.save() is True
    assert win.editor_page.writing_progress.today(book.id) == 5

    settings.setValue('writing_progress_enabled', True)
    ed.setPlainText('een twee drie vier vijf zes zeven acht negen')
    win.editor_page.dirty = True
    assert win.editor_page.save() is True
    assert win.editor_page.writing_progress.today(book.id) == 7
    win.close()
