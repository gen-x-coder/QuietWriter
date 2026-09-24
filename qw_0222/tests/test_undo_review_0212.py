"""Regression coverage for the externally reviewed 0.21.2 undo fix.

The source checks always run. Runtime Qt checks skip cleanly where PySide6 is not
installed; they are intended to execute in the Windows development/release
environment as well.
"""
from pathlib import Path
import os
import unittest

ROOT = Path(__file__).resolve().parents[1]
EDITOR_SOURCE = ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py'


def _source() -> str:
    return EDITOR_SOURCE.read_text(encoding='utf-8')


def test_undo_redo_overrides_suppress_format_scheduling():
    source = _source()
    undo = source.split('    def undo(self):', 1)[1].split('    def redo(self):', 1)[0]
    redo = source.split('    def redo(self):', 1)[1].split('    def reset_undo_history', 1)[0]
    for method in (undo, redo):
        assert 'self._suppress_formatting_schedule = True' in method
        assert 'self._suppress_formatting_schedule = False' in method
        assert 'self._format_join_previous = False' in method
    assert 'super().undo()' in undo
    assert 'super().redo()' in redo


def test_standard_undo_redo_keys_route_through_editor_overrides():
    source = _source()
    assert 'QKeySequence' in source.split('from PySide6.QtGui import', 1)[1].split('\nfrom PySide6.QtWidgets', 1)[0]
    key_method = source.split('    def keyPressEvent(self, event):', 1)[1].split('    def ', 1)[0]
    assert 'event.matches(QKeySequence.StandardKey.Undo)' in key_method
    assert 'self.undo(); event.accept(); return' in key_method
    assert 'event.matches(QKeySequence.StandardKey.Redo)' in key_method
    assert 'self.redo(); event.accept(); return' in key_method


def test_active_empty_uses_normal_line_height_and_bottom_margin_rules():
    source = _source()
    method = source.split('    def _make_block_format(', 1)[1].split('    def _set_block_format(', 1)[0]
    # Only a durable blank separator gets MinimumHeight / compact bottom margin.
    assert "if kind == 'empty' and not active_empty:" in method
    assert "elif kind == 'empty' and not active_empty:" in method
    # A just-created continuation paragraph may still be indented immediately.
    assert "kind == 'empty' and active_empty and previous_kind == 'normal'" in method


os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QKeyEvent, QTextCursor
    from PySide6.QtWidgets import QApplication
    from quietwriter.ui.manuscript_editor import ManuscriptEditor
    HAVE_QT = True
except Exception:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, 'PySide6 is not available in this test environment')
class UndoReviewQtRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def _press(editor, key, modifiers=None, text=''):
        if modifiers is None:
            modifiers = Qt.NoModifier
        event = QKeyEvent(QEvent.KeyPress, key, modifiers, text)
        editor.keyPressEvent(event)
        QApplication.processEvents()

    def _editor_with_first_sentence(self):
        editor = ManuscriptEditor()
        first = 'Dit is een proef tekst.'
        editor.blockSignals(True)
        editor.setPlainText(first)
        editor.blockSignals(False)
        editor.apply_visual_formatting()
        editor.reset_undo_history()
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.End)
        editor.setTextCursor(cursor)
        return editor, first

    def test_ctrl_z_converges_past_first_character_and_enter(self):
        editor, first = self._editor_with_first_sentence()
        try:
            self._press(editor, Qt.Key_Return, Qt.NoModifier, '\r')
            for ch in 'En dit is een tweede tekst na een enter.':
                self._press(editor, 0, Qt.NoModifier, ch)
            self.assertEqual(editor.toPlainText(), first + '\nEn dit is een tweede tekst na een enter.')

            # Use the same keyboard route as a real user. Repeated Ctrl+Z must
            # eventually reach the state before the Enter without a reappearing E.
            for _ in range(80):
                if editor.toPlainText() == first:
                    break
                self.assertTrue(editor.document().isUndoAvailable())
                self._press(editor, Qt.Key_Z, Qt.ControlModifier)
            self.assertEqual(editor.toPlainText(), first)
        finally:
            editor.close()

    def test_ctrl_z_redo_ctrl_z_round_trip_is_stable(self):
        editor, first = self._editor_with_first_sentence()
        try:
            self._press(editor, Qt.Key_Return, Qt.NoModifier, '\r')
            for ch in 'Een tweede zin.':
                self._press(editor, 0, Qt.NoModifier, ch)
            full = first + '\nEen tweede zin.'
            self.assertEqual(editor.toPlainText(), full)

            for _ in range(50):
                if editor.toPlainText() == first:
                    break
                self._press(editor, Qt.Key_Z, Qt.ControlModifier)
            self.assertEqual(editor.toPlainText(), first)

            for _ in range(50):
                if editor.toPlainText() == full:
                    break
                if not editor.document().isRedoAvailable():
                    break
                self._press(editor, Qt.Key_Y, Qt.ControlModifier)
            self.assertEqual(editor.toPlainText(), full)

            for _ in range(50):
                if editor.toPlainText() == first:
                    break
                self._press(editor, Qt.Key_Z, Qt.ControlModifier)
            self.assertEqual(editor.toPlainText(), first)
        finally:
            editor.close()

    def test_active_empty_format_matches_normal_except_indent_context(self):
        editor = ManuscriptEditor()
        try:
            active_empty = editor._make_block_format('empty', 'normal', active_empty=True)
            normal = editor._make_block_format('normal', 'normal')
            self.assertEqual(active_empty.lineHeightType(), normal.lineHeightType())
            self.assertEqual(active_empty.lineHeight(), normal.lineHeight())
            self.assertEqual(active_empty.bottomMargin(), normal.bottomMargin())
            self.assertEqual(active_empty.textIndent(), normal.textIndent())
        finally:
            editor.close()
