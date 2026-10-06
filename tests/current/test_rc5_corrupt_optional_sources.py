from pathlib import Path

import pytest

from quietwriter.ai.context import read_optional_source
from quietwriter.storage import Library


def _broken_utf8():
    raise UnicodeDecodeError('utf-8', b'\xff', 0, 1, 'invalid start byte')


def test_optional_ai_source_omits_corrupt_utf8():
    text, ok = read_optional_source(_broken_utf8)
    assert text == ''
    assert ok is False


def test_optional_ai_source_keeps_valid_text():
    text, ok = read_optional_source(lambda: '# geldig\n')
    assert text == '# geldig\n'
    assert ok is True


def test_persona_page_has_read_only_corrupt_startup_path():
    source = Path('quietwriter/ui/persona_page.py').read_text(encoding='utf-8')
    assert 'except UnicodeDecodeError:' in source
    assert "self._corrupt_source = True" in source
    assert "self.edit.setReadOnly(True)" in source
    assert "persona.corrupt_readonly" in source
    assert "archive/persona/" in source
    assert "if self._corrupt_source:" in source


def test_ai_send_uses_optional_source_reader_for_all_fixed_context():
    source = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    body = source.split('def _continue_send', 1)[1].split('def stop_ai', 1)[0]
    assert 'read_optional_source(self.main.library.read_persona)' in body
    assert 'read_optional_source(lambda: self.main.library.read_book_profile(active_book))' in body
    assert 'read_optional_source(lambda: self.main.library.read_book_memory(active_book))' in body
    assert 'ai.context.source_corrupt_piece' in body


@pytest.mark.parametrize('filename', ['nl.json', 'en.json'])
def test_rc5_locale_keys_are_present(filename):
    import json
    data = json.loads((Path('quietwriter/locales') / filename).read_text(encoding='utf-8'))
    for key in (
        'persona.corrupt_readonly',
        'ai.context.fixed_preview_dynamic',
        'ai.context.none_available',
        'ai.context.corrupt_sources_preview',
        'ai.context.source_corrupt_piece',
    ):
        assert key in data
