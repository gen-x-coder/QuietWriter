"""Regression cases from the 1.4 review, addressed in 1.5 dev.2."""
import importlib.util
from pathlib import Path

from quietwriter.markdown_io import split_book_body


def _notes():
    module_path = Path(__file__).resolve().parents[2] / 'quietwriter/ui/planning/note_segments.py'
    spec = importlib.util.spec_from_file_location('qw_notes_regression', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_late_unheaded_prose_keeps_its_section():
    source = '<!-- quietwriter-section: Eerst -->\n# Hoofdstuk\nA\n<!-- quietwriter-section: Laatst -->\nTekst zonder kop\n'
    sections = split_book_body(source, 'Boek')
    assert [section for section, _ in sections] == ['Eerst', 'Laatst']
    assert sections[0][1][0]['text'] == 'A'
    assert 'Tekst zonder kop' in sections[1][1][0]['text']


def test_late_prose_does_not_migrate_to_first_section():
    source = '<!-- quietwriter-section: Eerst -->\n# Een\nA\n<!-- quietwriter-section: Laatst -->\n# Twee\nB\n'
    sections = split_book_body(source, 'Boek')
    assert [item['title'] for _, chapters in sections for item in chapters] == ['Een', 'Twee']


def test_note_unicode_line_separators_do_not_corrupt_character_offsets():
    notes = _notes()
    original = '## Eén\nabc\u2028xyz\x85ff\n## Twee\r\nrest\u2029regel'
    segments = notes.split_notes(original)
    assert [x[2] for x in segments] == ['Eén', 'Twee']
    assert ''.join(original[a:b] for a, b, _, _ in segments) == original
    a, b, _, _ = segments[0]
    changed = notes.replace_note(original, a, b, '## Eén\nGewijzigd\n')
    assert changed.endswith(original[segments[1][0]:])
