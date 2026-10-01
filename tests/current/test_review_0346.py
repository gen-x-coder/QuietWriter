from pathlib import Path


def test_ai_panel_initializes_busy_button_state_on_cold_start():
    source = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    marker = "        self._refresh_idle_context_summary()\n        self._update_busy_buttons()\n\n    def is_busy"
    assert marker in source


def test_planning_error_context_is_self_describing_in_conversation_context():
    source = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    assert "ai.context.planning_unavailable_piece" in source
    assert 'error=planning.error' in source
