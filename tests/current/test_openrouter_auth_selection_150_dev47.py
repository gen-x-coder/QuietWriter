from unittest.mock import patch
from quietwriter.ai.providers import ProviderFactory


class FakeSettings:
    def __init__(self, **values):
        self.values = values

    def value(self, key, default=None):
        return self.values.get(key, default)


def test_manual_mode_does_not_use_browser_key():
    with patch('quietwriter.ai.openrouter_auth.stored_key', return_value='browser-secret') as stored:
        provider = ProviderFactory.for_name(FakeSettings(openrouter_auth_method='manual', openrouter_api_key='bad-manual'), 'openrouter')
    assert provider.api_key == 'bad-manual'
    stored.assert_not_called()


def test_browser_mode_does_not_fall_back_to_manual_key():
    with patch('quietwriter.ai.openrouter_auth.stored_key', return_value=''):
        provider = ProviderFactory.for_name(FakeSettings(openrouter_auth_method='browser', openrouter_api_key='manual-secret'), 'openrouter')
    assert provider.api_key == ''


def test_browser_mode_uses_vault_regardless_of_manual_key():
    with patch('quietwriter.ai.openrouter_auth.stored_key', return_value='browser-secret'):
        provider = ProviderFactory.for_name(FakeSettings(openrouter_auth_method='browser', openrouter_api_key='invalid-manual'), 'openrouter')
    assert provider.api_key == 'browser-secret'


def test_legacy_settings_keep_old_precedence():
    with patch('quietwriter.ai.openrouter_auth.stored_key', return_value='browser-secret'):
        provider = ProviderFactory.for_name(FakeSettings(openrouter_api_key='manual-secret'), 'openrouter')
    assert provider.api_key == 'browser-secret'


def test_settings_retain_manual_key_after_browser_login():
    from pathlib import Path
    source = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    segment = source.split('def _openrouter_login_finished', 1)[1].split('def _openrouter_disconnect', 1)[0]
    assert 'self.openrouter_key.clear()' not in segment
    assert "setValue('openrouter_api_key', '')" not in segment
    assert "self.openrouter_manual_row.setVisible(is_openrouter and not browser_mode)" in source
    assert "self.openrouter_browser_row.setVisible(is_openrouter and browser_mode)" in source
