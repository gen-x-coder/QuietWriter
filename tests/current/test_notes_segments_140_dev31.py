# Import the pure parser without initializing the PySide6 planning package.
import importlib.util
from pathlib import Path

source_file = Path(__file__).resolve().parents[2] / 'quietwriter/ui/planning/note_segments.py'
spec = importlib.util.spec_from_file_location('qw_note_segments', source_file)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
split_notes = module.split_notes


def test_fenced_markdown_headers_are_not_cards():
    source = '## Eerste\n\n```python\n## niet echt\n```\n\n## Tweede\ntekst\n'
    segments = split_notes(source)
    assert [segment[2] for segment in segments] == ['Eerste', 'Tweede']
    assert '## niet echt' in segments[0][3]
    assert ''.join(source[a:b] for a, b, _, _ in segments) == source


def test_tilde_fences_and_long_backtick_fences():
    source = '~~~\n## code\n~~~\n## Echt\n````\n## verborgen\n```\n## nog verborgen\n````\n'
    segments = split_notes(source)
    assert [segment[2] for segment in segments] == [None, 'Echt']
    assert '## nog verborgen' in segments[1][3]


def test_legacy_preamble_and_crlf_are_not_modified():
    source = 'oude tekst\r\n\r\n## Eerste\r\ninhoud\r\n## Tweede\r\nlaatste'
    segments = split_notes(source)
    assert [segment[2] for segment in segments] == [None, 'Eerste', 'Tweede']
    assert ''.join(source[a:b] for a, b, _, _ in segments) == source


def test_blank_or_non_level_two_headings_are_content():
    source = '# Sectie\n## \n### Geen kaart\n## Een kaart\ninhoud'
    segments = split_notes(source)
    assert [segment[2] for segment in segments] == [None, 'Een kaart']


def test_replacing_one_card_does_not_touch_others():
    original = 'Eerste vrije tekst\r\n\r\n## A\r\nEen inhoud\r\n\r\n## B\r\nTwee\r\n'
    segments = split_notes(original)
    replace_note = module.replace_note
    a, b, _, _ = segments[1]
    result = replace_note(original, a, b, '## A aangepast\r\nNieuw\r\n')
    assert result[:a] == original[:a]
    assert result.endswith(original[segments[2][0]:])
    assert '## A aangepast\r\nNieuw' in result


def test_replacing_stale_or_invalid_card_fails_closed():
    import pytest
    replace_note = module.replace_note
    original = '## A\nTekst\n## B\nMeer\n'
    a, b, _, _ = split_notes(original)[0]
    with pytest.raises(ValueError):
        replace_note(original + 'anders', a, b + 2, '## fout\n')
    with pytest.raises(ValueError):
        replace_note(original, -1, b, '## fout\n')


def test_blank_whitespace_heading_is_not_a_note():
    source = '##    \ngeen titel\n## Een echte\ninhoud\n'
    assert [row[2] for row in split_notes(source)] == [None, 'Een echte']
