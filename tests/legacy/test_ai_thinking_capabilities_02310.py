from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from quietwriter.ai.ollama_provider import OllamaProvider
from quietwriter.ai.openrouter_provider import OpenRouterProvider


class FakeResponse:
    def __init__(self, data, *, ok=True, status_code=200, text=''):
        self._data = data
        self.ok = ok
        self.status_code = status_code
        self.text = text

    def json(self):
        return self._data

    def close(self):
        pass


def test_ollama_marks_boolean_thinking_model_as_disableable():
    tags = FakeResponse({'models': [{'name': 'qwen3:latest', 'size': 123}]})
    show = FakeResponse({'thinking': {'values': [True, False], 'default': True}})
    with patch('quietwriter.ai.ollama_provider.requests.get', return_value=tags), \
         patch('quietwriter.ai.ollama_provider.requests.post', return_value=show) as post:
        models = OllamaProvider().list_models()
    assert models[0]['thinking_supported'] is True
    assert models[0]['thinking_can_disable'] is True
    assert models[0]['thinking_default'] is True
    assert post.call_args.kwargs['json'] == {'model': 'qwen3:latest'}


def test_ollama_does_not_mark_values_false_only_as_thinking_model():
    capability = OllamaProvider._thinking_capability(
        {'thinking': {'values': [False], 'default': False}}
    )
    assert capability['thinking_supported'] is False
    assert capability['thinking_can_disable'] is False


def test_ollama_named_levels_without_false_are_not_marked_disableable():
    capability = OllamaProvider._thinking_capability(
        {'thinking': {'values': ['low', 'medium', 'high'], 'default': 'medium'}}
    )
    assert capability['thinking_supported'] is True
    assert capability['thinking_can_disable'] is False


def test_ollama_missing_thinking_metadata_is_unknown_and_safe():
    capability = OllamaProvider._thinking_capability({})
    assert capability['thinking_supported'] is None
    assert capability['thinking_can_disable'] is None


def test_openrouter_uses_supported_parameters_for_reasoning_capability():
    response = FakeResponse({'data': [
        {'id': 'vendor/reasoner', 'supported_parameters': ['temperature', 'reasoning']},
        {'id': 'vendor/plain', 'supported_parameters': ['temperature']},
    ]})
    with patch('quietwriter.ai.openrouter_provider.requests.get', return_value=response):
        models = OpenRouterProvider('key').list_models()
    assert models[0]['thinking_can_disable'] is True
    assert models[1]['thinking_can_disable'] is False


def test_settings_model_combo_keeps_raw_model_id_separate_from_brain_label():
    source = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert "icons.append('🧠')" in source
    assert "label = f\"{' '.join(icons)} {name}\" if icons else name" in source
    assert 'self.model.addItem(label, name)' in source
    assert 'self.model.findData(current)' in source
    assert 'return str(data if data is not None else self.model.currentText()).strip()' in source
    assert 'self.model.currentIndexChanged.connect(self._update_thinking_control)' in source
    assert 'enabled = enabled and can_disable is not False' in source


def test_settings_explain_brain_marker_without_claiming_universal_quality_gain():
    source = Path('quietwriter/locales/nl.json').read_text(encoding='utf-8')
    assert '🧠 = de provider meldt dat dit model thinking/reasoning ondersteunt.' in source
    assert 'vaak sneller en directer' in source
    assert 'Het effect verschilt per model.' in source
