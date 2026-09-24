from pathlib import Path

from quietwriter.persona_profile import (
    EXAMPLE_PERSONAS, SECTIONS, default_persona_markdown, parse_persona, render_persona,
)
from quietwriter.storage import Library


def test_persona_has_structured_human_readable_markdown():
    md = default_persona_markdown()
    assert md.startswith('# Schrijverspersona\n')
    for section in SECTIONS:
        assert f'## {section.title}' in md
    assert 'Beschrijf hier jouw schrijfstijl' in md


def test_legacy_freeform_persona_is_preserved_without_loss():
    legacy = '# Schrijversprofiel\n\n## Algemene stijl\n\nRauw en direct.\n\n## Erotiek\n\nZintuiglijk en expliciet wanneer de scène daarom vraagt.\n'
    profile = parse_persona(legacy)
    assert profile['additional'] == legacy.strip()
    migrated = render_persona(profile)
    assert 'Rauw en direct.' in migrated
    assert '## Erotiek' in migrated
    assert 'Zintuiglijk en expliciet' in migrated


def test_structured_persona_roundtrips_and_preserves_unknown_sections():
    source = '# Schrijverspersona\n\n## Stem & toon\n\nWarm.\n\n## Eigen oude rubriek\n\nNiet verliezen.\n\n## Vermijden\n\nClichés.\n'
    profile = parse_persona(source)
    assert profile['voice_tone'] == 'Warm.'
    assert profile['avoid'] == 'Clichés.'
    assert '## Eigen oude rubriek' in profile['additional']
    roundtrip = parse_persona(render_persona(profile))
    assert roundtrip['voice_tone'] == 'Warm.'
    assert roundtrip['avoid'] == 'Clichés.'
    assert 'Niet verliezen.' in roundtrip['additional']


def test_three_example_personas_use_same_markdown_contract():
    assert len(EXAMPLE_PERSONAS) == 3
    assert {x['name'] for x in EXAMPLE_PERSONAS.values()} == {'Jane Austen', 'Arthur Conan Doyle', 'Virginia Woolf'}
    for example in EXAMPLE_PERSONAS.values():
        values = example['values']
        assert set(values) == {section.key for section in SECTIONS}
        md = render_persona(values)
        assert parse_persona(md) == values
        assert '# Schrijverspersona' in md


def test_new_workspace_gets_structured_writer_persona(tmp_path: Path):
    lib = Library(tmp_path)
    persona = lib.read_persona()
    assert persona == default_persona_markdown()
    assert lib.persona_path() == tmp_path / 'persona' / 'schrijver.md'


def test_persona_page_and_navigation_use_structured_reload_source():
    source = Path('quietwriter/ui/persona_page.py').read_text(encoding='utf-8')
    main = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    assert 'parse_persona(self.library.read_persona())' in source
    assert 'render_persona(self.profile)' in source
    assert 'ExamplePersonaDialog' in source
    assert 'self.persona.reload()' in main
    assert 'self.persona.edit.setPlainText(self.library.read_persona())' not in main
