from pathlib import Path

from quietwriter.ai.planning_context import _planning_unavailable_message
from quietwriter.planning_validation import FuturePlanningFormatError
from quietwriter.storage import CorruptSourceError


def test_planning_unavailable_message_is_reason_only_and_translation_safe_for_ui_composition():
    future = _planning_unavailable_message(FuturePlanningFormatError('planning/outline.json', 2))
    corrupt = _planning_unavailable_message(CorruptSourceError('planning/outline.json'))
    assert future.startswith('Gemaakt met een nieuwere QuietWriter')
    assert corrupt == 'Planning kan niet betrouwbaar worden gelezen.'
    assert 'Planning-context niet beschikbaar:' not in future
    assert 'Planning-context niet beschikbaar:' not in corrupt


def test_ai_busy_state_uses_loaded_store_as_the_book_state_source():
    source = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    assert "has_book = self.store is not None" in source
    assert "self.planning_context_button.setEnabled(not busy and has_book)" in source


def test_context_dialog_compacts_bullet_spacing_without_changing_prompt_builder():
    source = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    assert "replace('\\n\\n- ', '\\n- ')" in source
    assert 'self._compact_planning_display(planning.text)' in source
    assert 'self._compact_planning_display(chapter_preview.text)' in source


def test_program_separator_is_only_needed_when_collapsed_scroll_area_overflows():
    source = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    assert "if key == 'program':" in source
    assert 'visible = visible and self._program_separator_needed()' in source
    assert 'verticalScrollBar().maximum() > 0' in source
