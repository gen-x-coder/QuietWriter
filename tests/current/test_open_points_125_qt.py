import os

import pytest

pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox

from quietwriter.placeholders import marker_ranges, strip_open_point_markers, wrap_open_point
from quietwriter.ui.manuscript_editor import ManuscriptEditor


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _editor(app, source):
    ed = ManuscriptEditor()
    ed.setPlainText(source)
    ed.show()
    ed.setFocus()
    app.processEvents()
    return ed


def _select(ed, start, end):
    cursor = ed.textCursor()
    cursor.setPosition(start)
    cursor.setPosition(end, QTextCursor.KeepAnchor)
    ed.setTextCursor(cursor)


def test_ctrl_x_crossing_marker_is_blocked_on_real_qt_path(app, monkeypatch):
    source, *_ = wrap_open_point('Voor de haven na.', 5, 13)
    ed = _editor(app, source)
    try:
        opening = marker_ranges(source)[0]
        _select(ed, max(0, opening[0] - 2), opening[1] + 3)
        seen = []
        monkeypatch.setattr(QMessageBox, 'information', lambda *a, **k: seen.append(True))
        QTest.keyClick(ed, Qt.Key_X, Qt.ControlModifier)
        app.processEvents()
        assert ed.source_text() == source
        assert seen
    finally:
        ed.close()


def test_ctrl_v_over_marker_is_blocked_on_real_qt_path(app, monkeypatch):
    source, *_ = wrap_open_point('Voor de haven na.', 5, 13)
    ed = _editor(app, source)
    try:
        opening = marker_ranges(source)[0]
        _select(ed, max(0, opening[0] - 2), opening[1] + 3)
        QApplication.clipboard().setText('PLAK')
        seen = []
        monkeypatch.setattr(QMessageBox, 'information', lambda *a, **k: seen.append(True))
        QTest.keyClick(ed, Qt.Key_V, Qt.ControlModifier)
        app.processEvents()
        assert ed.source_text() == source
        assert seen
    finally:
        ed.close()


def test_copy_never_puts_marker_syntax_on_system_clipboard(app):
    source, *_ = wrap_open_point('Voor de haven na.', 5, 13)
    ed = _editor(app, source)
    try:
        _select(ed, 0, len(source))
        ed.copy()
        app.processEvents()
        copied = QApplication.clipboard().text()
        assert 'qw:todo' not in copied
        assert copied == strip_open_point_markers(source)
    finally:
        ed.close()


def test_arrow_key_skips_managed_marker_in_one_step(app):
    source, *_ = wrap_open_point('Voor de haven na.', 5, 13)
    ed = _editor(app, source)
    try:
        opening = marker_ranges(source)[0]
        cursor = ed.textCursor()
        cursor.setPosition(opening[0])
        ed.setTextCursor(cursor)
        app.processEvents()
        QTest.keyClick(ed, Qt.Key_Right)
        app.processEvents()
        assert ed.textCursor().position() == opening[1]
    finally:
        ed.close()
