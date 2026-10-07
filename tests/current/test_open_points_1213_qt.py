import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
pytest.importorskip('PySide6')
pytestmark = pytest.mark.qt

from PySide6.QtCore import QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from quietwriter.placeholders import wrap_open_point
from quietwriter.storage import Library


def _app():
    return QApplication.instance() or QApplication([])


def _book(library, title, count):
    book = library.create_book(title)
    section = book.sections[0]
    chapters = [section.chapters[0]] + [
        library.add_chapter(book, section, f'H{i + 1}') for i in range(1, count)
    ]
    for index, chapter in enumerate(chapters):
        text = f'Tekst punt {index}.'
        marked, *_ = wrap_open_point(text, 0, len(text), point_id=f'{index:012x}')
        library.save_chapter(book, chapter, marked)
    return book


def _window(tmp_path):
    from quietwriter.ui.main_window import MainWindow
    library = Library(tmp_path / 'library')
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.IniFormat)
    return library, settings, MainWindow


def test_resolving_selected_point_keeps_scroll_position(tmp_path):
    app = _app()
    library, settings, MainWindow = _window(tmp_path)
    book = _book(library, 'Groot', 150)
    window = MainWindow(settings, library, [])
    window.open_book(book); window.resize(1024, 683); window.show()
    page = window.editor_page
    page.show_open_points(); app.processEvents(); QTest.qWait(30)
    lst = page.open_points.list
    bar = lst.verticalScrollBar()

    row = lst.count() - 10
    chapter_id, point_id = lst.item(row).data(Qt.UserRole)
    page.jump_to_open_point(chapter_id, point_id); app.processEvents()
    lst.setCurrentRow(row)
    bar.setValue(bar.maximum()); app.processEvents()
    before = bar.value()

    page.resolve_current_open_point()  # synchronous refresh; selected point disappears
    app.processEvents(); QTest.qWait(400)

    assert lst.count() == 149
    assert bar.value() >= min(before, bar.maximum()) - 1
    window.close()


def test_switching_book_starts_open_points_list_at_top(tmp_path):
    app = _app()
    library, settings, MainWindow = _window(tmp_path)
    first = _book(library, 'Groot', 150)
    second = _book(library, 'Ander', 60)
    window = MainWindow(settings, library, [])
    window.open_book(first); window.resize(1024, 683); window.show()
    page = window.editor_page
    page.show_open_points(); app.processEvents(); QTest.qWait(30)
    bar = page.open_points.list.verticalScrollBar()
    bar.setValue(bar.maximum()); app.processEvents()
    assert bar.value() > 0

    window.open_book(second); app.processEvents(); QTest.qWait(400)
    if not (page.right.isVisible() and page.right.currentWidget() is page.open_points):
        page.show_open_points(); app.processEvents()

    assert page.open_points.list.count() == 60
    assert bar.value() == 0
    window.close()
