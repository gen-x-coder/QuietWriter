from pathlib import Path

from quietwriter.ai.quick_actions import QUICK_ACTIONS, QUICK_ACTION_BY_KEY


def test_quick_actions_are_small_editable_prompt_templates():
    assert [action.key for action in QUICK_ACTIONS] == [
        'feedback', 'rewrite_selection', 'persona_check', 'fact_check'
    ]
    assert [action.label for action in QUICK_ACTIONS] == [
        'Feedback', 'Herschrijf selectie', 'Persona-check', 'Feitencheck'
    ]
    assert QUICK_ACTION_BY_KEY['rewrite_selection'].requires_selection is True
    assert all(action.prompt.strip() for action in QUICK_ACTIONS)
    assert all('verstuur' not in action.prompt.lower() for action in QUICK_ACTIONS)


def test_feedback_and_fact_check_use_existing_context_layers():
    feedback = QUICK_ACTION_BY_KEY['feedback'].prompt
    facts = QUICK_ACTION_BY_KEY['fact_check'].prompt
    assert 'schrijverspersona' in feedback.lower()
    assert 'boekprofiel' in feedback.lower()
    assert 'boekgeheugen' in feedback.lower()
    assert 'planning-context' in feedback.lower()
    assert 'boekgeheugen' in facts.lower()
    assert 'planning-context' in facts.lower()
    assert 'actuele manuscripttekst' in facts.lower()


def test_rewrite_is_selection_only_and_preserves_story_intent():
    action = QUICK_ACTION_BY_KEY['rewrite_selection']
    assert action.requires_selection
    prompt = action.prompt.lower()
    assert 'uitsluitend de geselecteerde tekst' in prompt
    assert 'behoud betekenis, feiten, perspectief en bedoeling' in prompt
    assert 'geef alleen de herschreven tekst' in prompt


def test_ai_panel_exposes_quick_actions_without_auto_send():
    ai = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    editor = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    assert "quick_label = QLabel('Snelacties')" in ai
    assert "button.setObjectName('suggestionButton')" in ai
    assert 'def _apply_quick_action(self, key: str):' in ai
    start = ai.index('    def _apply_quick_action(self, key: str):')
    end = ai.index('    def _update_busy_buttons(self):', start)
    body = ai[start:end]
    assert 'self.input.setPlainText(action.prompt)' in body
    assert 'self.send(' not in body
    assert 'action.requires_selection and not self._has_manuscript_selection()' in body
    assert 'self.editor.selectionChanged.connect(self.ai.refresh_quick_actions)' in editor
    assert 'self.ai.refresh_quick_actions()' in editor
