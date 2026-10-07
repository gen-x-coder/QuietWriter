import pytest

pytest.importorskip("PySide6")

pytestmark = pytest.mark.qt

from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from quietwriter.ui.manuscript_editor import ManuscriptEditor
from quietwriter.ui.presentation_highlighter import ManuscriptHighlighter


def _cursor_x(editor, pos):
    cursor = QTextCursor(editor.document())
    cursor.setPosition(pos)
    return editor.cursorRect(cursor).x()


def test_hidden_todo_marker_is_near_zero_width_without_collapsing_bold_marker():
    app = QApplication.instance() or QApplication([])
    editor = ManuscriptEditor()
    editor.show()
    highlighter = ManuscriptHighlighter(editor)

    opening = '<!--qw:todo:12345678-->'
    text = f'voor {opening}de haven<!--/qw:todo--> na **vet** einde'
    editor.setPlainText(text)
    highlighter.rehighlight()
    QTest.qWait(20)

    marker_start = text.index(opening)
    marker_end = marker_start + len(opening)
    todo_shift = _cursor_x(editor, marker_end) - _cursor_x(editor, marker_start)
    assert abs(todo_shift) <= 2

    bold_start = text.index('**vet**')
    bold_content = bold_start + 2
    bold_shift = _cursor_x(editor, bold_content) - _cursor_x(editor, bold_start)
    assert 0 <= bold_shift <= 2

    editor.close()
    app.processEvents()
