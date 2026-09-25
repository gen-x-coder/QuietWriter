from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from quietwriter.ai.ollama_provider import OllamaProvider
from quietwriter.ai.openrouter_provider import OpenRouterProvider


class FakeResponse:
    def __init__(self, lines):
        self.ok = True
        self.status_code = 200
        self._lines = list(lines)
        self.text = ''

    def json(self):
        return {}

    def iter_lines(self, decode_unicode=True):
        yield from self._lines

    def close(self):
        pass


def test_ollama_thinking_off_is_top_level_request_field():
    response = FakeResponse([json.dumps({'message': {'content': 'ok'}, 'done': True})])
    provider = OllamaProvider()
    with patch('quietwriter.ai.ollama_provider.requests.post', return_value=response) as post:
        chunks = list(provider.stream_chat('model', [{'role': 'user', 'content': 'test'}], think=False))
    assert ''.join(c.content for c in chunks) == 'ok'
    payload = post.call_args.kwargs['json']
    assert payload['think'] is False
    assert 'options' not in payload or 'think' not in payload['options']


def test_openrouter_thinking_off_uses_reasoning_request_field():
    response = FakeResponse([
        'data: ' + json.dumps({'choices': [{'delta': {'content': 'ok'}}]}),
        'data: [DONE]',
    ])
    provider = OpenRouterProvider('key')
    with patch('quietwriter.ai.openrouter_provider.requests.post', return_value=response) as post:
        chunks = list(provider.stream_chat(
            'model', [{'role': 'user', 'content': 'test'}], reasoning={'enabled': False}
        ))
    assert ''.join(c.content for c in chunks) == 'ok'
    payload = post.call_args.kwargs['json']
    assert payload['reasoning'] == {'enabled': False}


def test_ai_panel_uses_compact_bottom_controls():
    source = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    assert "self.context_toggle = QPushButton('Context')" in source
    assert "self.quick_toggle = QPushButton('Snelacties')" in source
    assert "self.context_panel.hide()" in source
    assert "ai_quick_actions_expanded" in source
    assert "self.context = QComboBox(); self.context.addItems(['Huidig hoofdstuk', 'Huidige sectie', 'Hele boek'])" in source
    assert "self.context_view_button.clicked.connect(self._show_context_dialog)" in source
    assert 'def _toggle_context_controls' in source
    assert 'def _toggle_quick_actions' in source


def test_ai_settings_expose_thinking_and_quick_action_preferences():
    source = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert "settings.value('ai_disable_thinking', False, bool)" in source
    assert "self.settings.setValue('ai_disable_thinking', self.ai_disable_thinking.isChecked())" in source
    assert "settings.value('ai_quick_actions_expanded', False, bool)" in source
    assert "self.settings.setValue('ai_quick_actions_expanded', self.ai_quick_actions_expanded.isChecked())" in source


def test_ai_send_maps_thinking_off_per_provider():
    source = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    assert "provider_options['think'] = False" in source
    assert "provider_options['reasoning'] = {'enabled': False}" in source
    assert 'ProviderChatWorker(provider,model,messages,options=provider_options)' in source
