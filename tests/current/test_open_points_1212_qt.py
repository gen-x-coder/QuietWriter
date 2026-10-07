import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
pytest.importorskip('PySide6')
pytestmark = pytest.mark.qt

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from quietwriter.placeholders import wrap_open_point
from quietwriter.storage import Library
from quietwriter.ui.open_points_panel import OpenPointsPanel


def _app():
    return QApplication.instance() or QApplication([])


def test_live_refresh_preserves_selected_open_point_and_scroll(tmp_path):
    app = _app()
    library = Library(tmp_path / 'library')
    book = library.create_book('Veel punten')
    section = book.sections[0]

    chapters = [section.chapters[0]]
    for index in range(1, 45):
        chapters.append(library.add_chapter(book, section, f'Hoofdstuk {index + 1}'))

    point_ids = []
    for index, chapter in enumerate(chapters):
        marked, point_id, *_ = wrap_open_point(
            f'Tekst punt {index}.', 0, len(f'Tekst punt {index}.'),
            point_id=f'{index:012x}'
        )
        point_ids.append(point_id)
        library.save_chapter(book, chapter, marked)

    panel = OpenPointsPanel(library)
    panel.resize(320, 260)
    panel.show()
    panel.refresh(book)
    app.processEvents(); QTest.qWait(20)

    target_row = 35
    panel.list.setCurrentRow(target_row)
    panel.list.verticalScrollBar().setValue(panel.list.verticalScrollBar().maximum() - 5)
    app.processEvents()
    old_scroll = panel.list.verticalScrollBar().value()
    selected_before = panel.list.currentItem().data(Qt.UserRole)  # Qt.UserRole

    # Mimic a normal live refresh after textChanged. The selected point still
    # exists, so both keyboard position and viewport should remain stable.
    panel.refresh(book)
    app.processEvents(); QTest.qWait(20)

    assert panel.list.currentItem() is not None
    assert panel.list.currentItem().data(Qt.UserRole) == selected_before
    assert panel.list.currentRow() == target_row
    assert panel.list.verticalScrollBar().value() == min(
        old_scroll, panel.list.verticalScrollBar().maximum()
    )
    panel.close()
