from quietwriter.ai.model_suitability import suitable_for_writing


def test_code_specialists_are_hidden():
    for name in (
        'qwen/qwen2.5-coder-32b-instruct', 'mistral/devstral-small',
        'bigcode/starcoder2-15b', 'openai/gpt-5.1-codex-mini',
        'moonshotai/kimi-k2.7-code', 'openrouter/pareto-code',
        'poolside/laguna-xs-2.1',
    ):
        assert not suitable_for_writing({'name': name})
    assert not suitable_for_writing({'name': 'bytedance/seed-2.0-code', 'description': 'Coding specialist'})


def test_general_models_remain_visible():
    for name in ('openrouter/free', 'openai/gpt-4.1', 'anthropic/claude-opus-4.6',
                 'google/gemini-2.5-flash', 'qwen/qwen3.5-9b'):
        assert suitable_for_writing({'name': name, 'description': 'Optimized for coding and developer tasks'})


def test_output_modalities_filter():
    assert not suitable_for_writing({'name': 'vendor/painter', 'output_modalities': ['image']})
    assert not suitable_for_writing({'name': 'vendor/speaker', 'output_modalities': ['audio']})
    assert suitable_for_writing({'name': 'vendor/multimodal', 'output_modalities': ['image', 'text']})
    assert suitable_for_writing({'name': 'vendor/legacy'})
    assert suitable_for_writing({'name': 'openrouter/free', 'output_modalities': ['image']})
