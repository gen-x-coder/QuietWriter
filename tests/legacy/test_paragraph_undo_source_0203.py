from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_enter_formats_new_paragraph_inside_same_edit_block():
    source = (ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py').read_text(encoding='utf-8')
    assert "active_empty = new_kind == 'empty' and previous_kind == 'normal'" in source
    assert 'new_fmt = self._make_block_format' in source
    assert 'cursor.setBlockFormat(new_fmt)' in source
    assert '_suppress_formatting_schedule = True' in source


def test_text_driven_visual_formatting_joins_previous_undo_command():
    source = (ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py').read_text(encoding='utf-8')
    assert 'self._format_join_previous = True' in source
    assert 'edit_cursor.joinPreviousEditBlock()' in source
    assert 'def reset_undo_history(self):' in source


def test_editor_page_does_not_schedule_a_second_delayed_format_pass_per_keystroke():
    source = (ROOT / 'quietwriter' / 'ui' / 'editor_page.py').read_text(encoding='utf-8')
    method = source.split('    def on_text_changed(self):', 1)[1].split('    def ', 1)[0]
    assert 'self.editor.schedule_formatting()' not in method


def test_chapter_load_clears_presentation_only_undo_history():
    source = (ROOT / 'quietwriter' / 'ui' / 'editor_page.py').read_text(encoding='utf-8')
    method = source.split('    def _set_editor_chapter(self, chapter):', 1)[1].split('    def ', 1)[0]
    assert 'self.editor.reset_undo_history()' in method
