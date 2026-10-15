import pytest
from quietwriter.ai.openrouter_provider import OpenRouterProvider


@pytest.mark.parametrize('url', [
    'http://openrouter.ai/api/v1',
    'https://evil.example/api/v1',
    'https://openrouter.ai.evil.example/api/v1',
    'https://openrouter.ai@evil.example/api/v1',
    'https://openrouter.ai/api/v1/../other',
    'https://openrouter.ai/api/v1?token=1',
    'https://openrouter.ai/api/v1#fragment',
    'https://openrouter.ai:8443/api/v1',
])
def test_reject_alternative_endpoints(url):
    with pytest.raises(ValueError, match='Ongeldig OpenRouter-adres'):
        OpenRouterProvider('secret', base_url=url)


def test_accept_official_endpoint():
    assert OpenRouterProvider('secret').base_url == 'https://openrouter.ai/api/v1'
    assert OpenRouterProvider('secret', 'https://openrouter.ai/api/v1/').base_url == 'https://openrouter.ai/api/v1'
