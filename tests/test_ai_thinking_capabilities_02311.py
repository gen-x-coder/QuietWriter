from pathlib import Path
from unittest.mock import patch

from quietwriter.ai.ollama_provider import OllamaProvider


class FakeResponse:
    def __init__(self, data, *, ok=True, status_code=200, text=''):
        self._data = data
        self.ok = ok
        self.status_code = status_code
        self.text = text

    def json(self):
        return self._data


def test_ollama_capabilities_list_marks_thinking_model():
    capability = OllamaProvider._thinking_capability({
        'capabilities': ['completion', 'tools', 'thinking']
    })
    assert capability['thinking_supported'] is True
    assert capability['thinking_can_disable'] is None
    assert capability['thinking_control_known'] is False


def test_qwen_and_deepseek_cli_style_show_responses_receive_thinking_capability():
    for architecture in ('qwen3', 'deepseek2'):
        capability = OllamaProvider._thinking_capability({
            'capabilities': ['tools', 'thinking', 'completion'],
            'details': {'family': architecture},
        })
        assert capability['thinking_supported'] is True
        assert capability['thinking_can_disable'] is None


def test_detailed_thinking_metadata_still_takes_precedence_over_capability_list():
    capability = OllamaProvider._thinking_capability({
        'capabilities': ['thinking'],
        'thinking': {'values': ['low', 'medium', 'high'], 'default': 'medium'},
    })
    assert capability['thinking_supported'] is True
    assert capability['thinking_can_disable'] is False
    assert capability['thinking_control_known'] is True


def test_model_refresh_keeps_capabilities_from_api_show():
    tags = FakeResponse({'models': [
        {'name': 'qwen3:4b', 'size': 1},
        {'name': 'deepseek-r1:8b', 'size': 1},
    ]})
    shows = [
        FakeResponse({'capabilities': ['completion', 'tools', 'thinking']}),
        FakeResponse({'capabilities': ['tools', 'thinking', 'completion']}),
    ]
    with patch('quietwriter.ai.ollama_provider.requests.get', return_value=tags), \
         patch('quietwriter.ai.ollama_provider.requests.post', side_effect=shows):
        models = OllamaProvider().list_models()
    assert [m['thinking_supported'] for m in models] == [True, True]
    assert [m['thinking_can_disable'] for m in models] == [None, None]


def test_settings_brain_marker_is_based_on_thinking_support_not_only_known_disable_flag():
    source = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert "supported = info.get('thinking_supported') is True" in source
    assert "label = f'🧠 {name}' if supported else name" in source
    assert 'enabled = enabled and can_disable is not False' in source


def test_dutch_help_explains_capability_only_fallback():
    source = Path('quietwriter/locales/nl.json').read_text(encoding='utf-8')
    assert '🧠 = de provider meldt dat dit model thinking/reasoning ondersteunt.' in source
    assert 'sommige modelvarianten' in source
