from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from quietwriter.ai.openrouter_provider import OpenRouterProvider


class FakeResponse:
    ok = True
    status_code = 200
    text = ''

    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


def test_openrouter_marks_zero_text_pricing_as_free():
    response = FakeResponse({'data': [
        {'id': 'vendor/free-by-price', 'pricing': {'prompt': '0', 'completion': '0'}},
        {'id': 'vendor/paid', 'pricing': {'prompt': '0.000001', 'completion': '0'}},
        {'id': 'vendor/explicit:free', 'pricing': {}},
        {'id': 'openrouter/free', 'pricing': {}},
    ]})
    with patch('quietwriter.ai.openrouter_provider.requests.get', return_value=response):
        models = OpenRouterProvider('key').list_models()
    free = {model['name']: model['free'] for model in models}
    assert free == {
        'vendor/free-by-price': True,
        'vendor/paid': False,
        'vendor/explicit:free': True,
        'openrouter/free': True,
    }


def test_settings_put_free_openrouter_models_first_and_support_free_only_filter():
    source = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert "models.sort(key=lambda name: 0 if info_by_name.get(name, {}).get('free') is True else 1)" in source
    assert "models = [name for name in models if info_by_name.get(name, {}).get('free') is True]" in source
    assert "icons.append('🆓')" in source
    assert "settings.value('openrouter_free_only', False, bool)" in source
    assert "'openrouter_free_only': self.openrouter_free_only.isChecked()" in source


def test_locales_explain_free_marker_and_refresh_semantics():
    nl = Path('quietwriter/locales/nl.json').read_text(encoding='utf-8')
    en = Path('quietwriter/locales/en.json').read_text(encoding='utf-8')
    assert 'Alleen gratis modellen tonen' in nl
    assert '🆓 = gratis via OpenRouter' in nl
    assert 'Show free models only' in en
    assert '🆓 = free via OpenRouter' in en
