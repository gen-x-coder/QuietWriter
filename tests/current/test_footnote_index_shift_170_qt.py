"""ChatGPT-review dev15: een notenveld met focus mag nooit in een verschoven noot schrijven."""
import os

import pytest
pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from quietwriter.ui.footnote_strip import FootnoteStrip
from quietwriter.ui.manuscript_editor import ManuscriptEditor


@pytest.fixture
def setup():
    app = QApplication.instance() or QApplication([])
    editor = ManuscriptEditor()
    strip = FootnoteStrip(editor)
    editor.attach_footnote_strip(strip)
    editor.resize(900, 600); editor.show()
    editor.setPlainText('Een^[A] twee^[B] drie^[C].')
    strip.refresh(); app.processEvents()
    yield app, editor, strip
    editor.close()


def _notes(editor):
    source = editor.source_text()
    return [source[cs:ce] for _s, cs, ce, _e in editor.footnote_spans()]


def _focus(app, strip, index):
    edit = strip.rows[index].edit
    edit.setFocus(); app.processEvents()
    cursor = edit.textCursor(); cursor.movePosition(QTextCursor.End); edit.setTextCursor(cursor)
    return edit


def _remove_first_note(editor):
    start, _cs, _ce, end = editor.footnote_spans()[0]
    cursor = QTextCursor(editor.document())
    cursor.setPosition(start); cursor.setPosition(end, QTextCursor.KeepAnchor)
    cursor.insertText('')


def test_typing_after_a_note_before_it_was_removed(setup):
    app, editor, strip = setup
    edit = _focus(app, strip, 1)                    # B
    _remove_first_note(editor)                      # A weg: B wordt nummer 1
    strip.refresh(); app.processEvents()
    QTest.keyClicks(edit if edit.hasFocus() else strip.rows[0].edit, 'x')
    notes = _notes(editor)
    assert 'C' in notes and notes.count('C') == 1   # C nooit overschreven
    assert notes in (['Bx', 'C'], ['B', 'C'])


def test_typing_after_a_note_was_inserted_before_it(setup):
    app, editor, strip = setup
    edit = _focus(app, strip, 1)                    # B
    cursor = QTextCursor(editor.document()); cursor.setPosition(0)
    cursor.insertText('Nul^[N] ')                   # nieuwe noot vóór alles
    strip.refresh(); app.processEvents()
    focused = next((r.edit for r in strip.rows if r.edit.hasFocus()), None)
    if focused is not None:
        QTest.keyClicks(focused, 'x')
    notes = _notes(editor)
    assert notes[0] == 'N' and notes[1] in ('A',) and notes[3] == 'C'
    assert notes[2] in ('B', 'Bx')


def test_external_change_with_same_count_does_not_get_overwritten(setup):
    app, editor, strip = setup
    edit = _focus(app, strip, 1)                    # B, focus
    # Van buiten (herladen van schijf): noot 2 krijgt een andere tekst, aantal blijft gelijk.
    _s, cs, ce, _e = editor.footnote_spans()[1]
    cursor = QTextCursor(editor.document()); cursor.setPosition(cs); cursor.setPosition(ce, QTextCursor.KeepAnchor)
    cursor.insertText('Nieuw')
    strip.refresh(); app.processEvents()
    QTest.keyClicks(edit, 'x')
    notes = _notes(editor)
    assert notes[1].replace('x', '', 1) == 'Nieuw'  # de wijziging van buiten blijft; nooit terug naar 'Bx'
    assert notes[0] == 'A' and notes[2] == 'C'
