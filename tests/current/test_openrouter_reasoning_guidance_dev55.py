"""Prevent silent reasoning overrides and retain user-facing guidance."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_error_guidance_prioritizes_mandatory_reasoning():
    source = (ROOT / 'quietwriter/ai/ui.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    method = next(n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == '_friendly_error')
    start, end = method.lineno, method.end_lineno
    code = '\n'.join(source.splitlines()[start-1:end])
    assert 'reasoning' in code and 'cannot be disabled' in code
    assert 'ai.error.reasoning_required' in code
    assert code.index('ai.error.reasoning_required') < code.index('ai.error.key')

def test_no_silent_openrouter_retry():
    source = (ROOT / 'quietwriter/ai/openrouter_provider.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'stream_chat')
    code = '\n'.join(source.splitlines()[method.lineno-1:method.end_lineno])
    posts = [n for n in ast.walk(method) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == 'requests' and n.func.attr == 'post']
    assert len(posts) == 1
    assert "payload.update({k:v" in code

def test_localized_guidance_present():
    for lang in ('nl', 'en', 'de', 'fr', 'es'):
        data = json.loads((ROOT / 'quietwriter/locales' / f'{lang}.json').read_text(encoding='utf-8'))
        guidance = data['ai.error.reasoning_required']
        assert 'Thinking' in guidance and guidance.strip()
