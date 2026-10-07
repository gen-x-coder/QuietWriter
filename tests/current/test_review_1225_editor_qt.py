import pytest

PySide6 = pytest.importorskip('PySide6')
from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from quietwriter.document_view import parse_document, visible_block_text
from quietwriter.ui.manuscript_editor import ManuscriptEditor


def _app():
    return QApplication.instance() or QApplication([])


def _editor(text=''):
    app = _app()
    ed = ManuscriptEditor(); ed.resize(800, 400); ed.show(); QTest.qWait(10)
    ed.setPlainText(text); ed.document().clearUndoRedoStacks()
    c = ed.textCursor(); c.movePosition(QTextCursor.End); ed.setTextCursor(c)
    app.processEvents()
    return ed


def _type(ed, text):
    for ch in text:
        if ch == '\n': QTest.keyClick(ed, Qt.Key_Return)
        else: QTest.keyClicks(ed, ch)
    _app().processEvents()


def _visible(ed):
    return [(b.kind, visible_block_text(b)) for b in parse_document(ed.source_text()).blocks if b.kind != 'empty']


def test_escape_is_atomic_for_backspace_and_cursor():
    ed = _editor(); _type(ed, 'a*')
    assert ed.source_text() == r'a\*'
    QTest.keyClick(ed, Qt.Key_Backspace); _type(ed, 'b')
    assert ed.source_text() == 'ab'
    assert _visible(ed) == [('paragraph', 'ab')]

    ed = _editor(); _type(ed, '5*3')
    QTest.keyClick(ed, Qt.Key_Left); QTest.keyClick(ed, Qt.Key_Left)
    assert ed.textCursor().position() != 2


def test_delete_enter_backspace_cannot_create_structure_from_prose():
    ed = _editor(); _type(ed, 'In 1944. Het was koud.')
    c=ed.textCursor(); c.setPosition(0); c.setPosition(3, QTextCursor.KeepAnchor); ed.setTextCursor(c)
    QTest.keyClick(ed, Qt.Key_Delete)
    assert _visible(ed) == [('paragraph', '1944. Het was koud.')]

    ed = _editor(); _type(ed, 'Hij riep - Kom je mee?')
    c=ed.textCursor(); c.setPosition(ed.source_text().index('- Kom')); ed.setTextCursor(c)
    QTest.keyClick(ed, Qt.Key_Return)
    assert _visible(ed)[-1] == ('paragraph', '- Kom je mee?')

    ed = _editor(); _type(ed, 'x- Kom')
    c=ed.textCursor(); c.setPosition(1); ed.setTextCursor(c); QTest.keyClick(ed, Qt.Key_Backspace)
    assert _visible(ed) == [('paragraph', '- Kom')]


def test_internal_clipboard_preserves_formatting_but_plain_text_is_visible():
    ed = _editor('Hij was **heel** moe en *erg* stil.')
    c=ed.textCursor(); c.setPosition(0); c.movePosition(QTextCursor.End, QTextCursor.KeepAnchor); ed.setTextCursor(c)
    mime=ed.createMimeDataFromSelection()
    assert mime.text() == 'Hij was heel moe en erg stil.'
    assert mime.hasFormat(ed.QW_SOURCE_MIME)
    c.movePosition(QTextCursor.End); ed.setTextCursor(c); QTest.keyClick(ed, Qt.Key_Return)
    ed.insertFromMimeData(mime)
    assert _visible(ed)[1][1] == _visible(ed)[0][1]
    assert '**heel**' in ed.source_text() and '*erg*' in ed.source_text()


def test_external_paste_of_image_markdown_stays_literal():
    ed=_editor(); raw='![foto](assets/images/0123456789abcdef0123456789abcdef.png)'
    mime=QMimeData(); mime.setText(raw); ed.insertFromMimeData(mime)
    assert _visible(ed) == [('paragraph', raw)]


def test_shift_enter_stays_inside_one_document_block():
    ed=_editor(); _type(ed, 'Regel een'); QTest.keyClick(ed, Qt.Key_Return, Qt.ShiftModifier); _type(ed, '- twee')
    view=parse_document(ed.source_text())
    assert len([b for b in view.blocks if b.kind != 'empty']) == 1
    assert view.blocks[0].kind == 'paragraph'


def test_nbsp_survives_explicit_formatting():
    ed=_editor('tien\u00a0procent en meer')
    c=ed.textCursor(); c.setPosition(0); c.setPosition(len('tien\u00a0procent'), QTextCursor.KeepAnchor); ed.setTextCursor(c)
    ed._selection_range=(c.selectionStart(), c.selectionEnd())
    ed.apply_format_action('bold')
    assert '\u00a0' in ed.source_text()


def test_removing_structural_prefix_space_never_exposes_escape():
    ed = _editor(); _type(ed, '- '); QTest.keyClick(ed, Qt.Key_Backspace)
    assert ed.source_text() == r'\-'
    assert _visible(ed) == [('paragraph', '-')]


def test_external_paste_midline_does_not_write_structural_escape():
    for raw in ('1944. Het jaar', '- Kom mee', '## kop', '> citaat'):
        ed = _editor(); _type(ed, 'Begin ')
        mime = QMimeData(); mime.setText(raw); ed.insertFromMimeData(mime)
        assert _visible(ed) == [('paragraph', 'Begin ' + raw)]
        assert '\\-' not in ed.source_text() and '\\>' not in ed.source_text() and '\\##' not in ed.source_text()
        if raw.startswith('1944.'):
            assert '1944\\.' not in ed.source_text()


def test_selection_ending_inside_escape_does_not_delete_visible_escape_character():
    ed = _editor(); _type(ed, 'a*b')
    assert ed.source_text() == r'a\*b'
    c = ed.textCursor(); c.setPosition(0); c.setPosition(2, QTextCursor.KeepAnchor); ed.setTextCursor(c)
    QTest.keyClick(ed, Qt.Key_Delete)
    assert _visible(ed) == [('paragraph', '*b')]
