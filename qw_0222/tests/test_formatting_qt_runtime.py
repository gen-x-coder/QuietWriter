"""Runtime Qt regression tests for manuscript formatting.

These tests skip cleanly on development/test hosts without PySide6. They are
intended to run in the Windows release environment as well, where they catch
binding and presentation regressions that source-grep tests cannot.
"""
import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

try:
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QTextBlockFormat, QTextCursor, QTextCharFormat, QFont, QKeyEvent
    from PySide6.QtWidgets import QApplication
    from quietwriter.ui.manuscript_editor import ManuscriptEditor
    from quietwriter.ui.selection_toolbar import SelectionToolbar
    HAVE_QT = True
except Exception:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, 'PySide6 is not available in this test environment')
class FormattingQtRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_toolbar_set_states_clears_previous_checked_state(self):
        toolbar = SelectionToolbar()
        toolbar.set_states({'bold': True, 'italic': True})
        self.assertTrue(toolbar.buttons['bold'].isChecked())
        self.assertTrue(toolbar.buttons['italic'].isChecked())
        toolbar.set_states({'underline': True})
        self.assertFalse(toolbar.buttons['bold'].isChecked())
        self.assertFalse(toolbar.buttons['italic'].isChecked())
        self.assertTrue(toolbar.buttons['underline'].isChecked())
        toolbar.close()

    def test_one_format_action_is_one_undo_step(self):
        editor = ManuscriptEditor()
        editor.setPlainText('Een belangrijk woord.')
        cursor = editor.textCursor()
        start = editor.toPlainText().index('belangrijk')
        end = start + len('belangrijk')
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        editor.setTextCursor(cursor)
        editor._selection_range = (start, end)
        editor.apply_format_action('bold')
        self.assertEqual(editor.toPlainText(), 'Een **belangrijk** woord.')
        editor.undo()
        self.assertEqual(editor.toPlainText(), 'Een belangrijk woord.')
        editor.close()

    def test_combined_inline_formats_are_composed(self):
        editor = ManuscriptEditor()
        editor.setPlainText('***tekst***')
        editor.presentation_highlighter.rehighlight()
        block = editor.document().firstBlock()
        # Position 3 is the first visible character after the *** opening markers.
        fmt = block.layout().formats()
        visible = None
        for rng in fmt:
            if rng.start <= 3 < rng.start + rng.length:
                visible = rng.format
                break
        self.assertIsNotNone(visible)
        self.assertEqual(visible.fontWeight(), QFont.Weight.Bold)
        self.assertTrue(visible.fontItalic())
        editor.close()

    def test_block_format_line_height_call_executes(self):
        editor = ManuscriptEditor()
        editor.setPlainText('Een alinea')
        block = editor.document().firstBlock()
        fmt = editor._make_block_format('normal', None)
        cursor = QTextCursor(block)
        cursor.setBlockFormat(fmt)
        self.assertGreater(block.blockFormat().lineHeight(), 0)
        editor.close()


    def test_enter_indents_immediately_before_first_character(self):
        editor = ManuscriptEditor()
        editor.blockSignals(True)
        editor.setPlainText('Dit is een proef tekst.')
        editor.blockSignals(False)
        editor.apply_visual_formatting()
        editor.reset_undo_history()
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.End)
        editor.setTextCursor(cursor)

        event = QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier, '\r')
        editor.keyPressEvent(event)

        block = editor.textCursor().block()
        self.assertEqual(block.text(), '')
        self.assertAlmostEqual(
            block.blockFormat().textIndent(),
            float(editor.manuscript_style.paragraph_indent_px),
            places=3,
        )

        editor.insertPlainText('   ')
        editor.apply_visual_formatting()
        self.assertAlmostEqual(
            editor.textCursor().block().blockFormat().textIndent(),
            float(editor.manuscript_style.paragraph_indent_px),
            places=3,
        )
        editor.close()

    def test_undo_can_cross_first_character_and_enter_after_indented_paragraph(self):
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

        editor.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier, '\r'))
        editor.insertPlainText('E')
        editor.apply_visual_formatting()
        editor.insertPlainText('n dit is een tweede tekst na een enter.')
        editor.apply_visual_formatting()
        self.assertEqual(
            editor.toPlainText(),
            first + '\nEn dit is een tweede tekst na een enter.',
        )

        # Undo may group typing bursts differently per Qt version, but repeated
        # undo must pass the first character and Enter *without* injecting a
        # compensating reformat command between undo steps.
        for _ in range(16):
            if editor.toPlainText() == first:
                break
            self.assertTrue(editor.document().isUndoAvailable())
            editor.undo()
        self.assertEqual(editor.toPlainText(), first)
        editor.close()

    def test_double_enter_preserves_real_blank_paragraph(self):
        editor = ManuscriptEditor()
        editor.setPlainText('Eerste alinea')
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.End)
        editor.setTextCursor(cursor)
        for _ in range(2):
            event = QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier, '\r')
            editor.keyPressEvent(event)
        editor.apply_visual_formatting()
        self.assertEqual(editor.toPlainText(), 'Eerste alinea\n\n')
        self.assertEqual(editor.document().blockCount(), 3)
        blank = editor.document().findBlockByNumber(1)
        self.assertTrue(blank.isValid())
        self.assertEqual(blank.text(), '')
        minimum_type = QTextBlockFormat.MinimumHeight
        minimum_type = int(minimum_type.value) if hasattr(minimum_type, 'value') else int(minimum_type)
        actual_type = blank.blockFormat().lineHeightType()
        actual_type = int(actual_type.value) if hasattr(actual_type, 'value') else int(actual_type)
        self.assertEqual(actual_type, minimum_type)
        self.assertGreater(blank.blockFormat().lineHeight(), 0)
        editor.close()


if __name__ == '__main__':
    unittest.main()

@unittest.skipUnless(HAVE_QT, 'PySide6 is not available in this test environment')
class FormattingFocusQtRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_selection_toolbar_does_not_accept_keyboard_focus(self):
        from PySide6.QtCore import Qt
        toolbar = SelectionToolbar()
        self.assertTrue(bool(toolbar.windowFlags() & Qt.WindowDoesNotAcceptFocus))
        self.assertEqual(toolbar.focusPolicy(), Qt.NoFocus)
        for button in toolbar.buttons.values():
            self.assertEqual(button.focusPolicy(), Qt.NoFocus)
        toolbar.close()
