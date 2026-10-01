from pathlib import Path

from quietwriter.ai.quick_actions import QUICK_ACTIONS, QUICK_ACTION_BY_KEY


def test_quick_actions_are_small_editable_reader_prompt_templates():
    assert [action.key for action in QUICK_ACTIONS] == [
        'feedback', 'persona_check', 'fact_check'
    ]
    assert [action.label for action in QUICK_ACTIONS] == [
        'Feedback', 'Persona-check', 'Feitencheck'
    ]
    assert 'rewrite_selection' not in QUICK_ACTION_BY_KEY
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


def test_reader_actions_do_not_offer_replacement_manuscript_text():
    feedback = QUICK_ACTION_BY_KEY['feedback'].prompt.lower()
    persona = QUICK_ACTION_BY_KEY['persona_check'].prompt.lower()
    assert 'schrijf of herschrijf geen manuscripttekst' in feedback
    assert 'geen vervangende manuscripttekst' in persona


def test_ai_panel_exposes_quick_actions_without_auto_send():
    ai = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    editor = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    assert "quick_label = QLabel(tr('ai.quick_actions', 'Snelacties'))" in ai
    assert "button.setObjectName('suggestionButton')" in ai
    assert 'def _apply_quick_action(self, key: str):' in ai
    start = ai.index('    def _apply_quick_action(self, key: str):')
    end = ai.index('    def _update_busy_buttons(self):', start)
    body = ai[start:end]
    assert "self.input.setPlainText(tr(f'ai.quick.{action.key}.prompt', action.prompt))" in body
    assert 'self.send(' not in body
    assert 'action.requires_selection and not self._has_manuscript_selection()' in body
    assert 'self.editor.selectionChanged.connect(self.ai.refresh_quick_actions)' in editor
    assert 'self.ai.refresh_quick_actions()' in editor
