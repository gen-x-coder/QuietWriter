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
    assert {x['name'] for x in EXAMPLE_PERSONAS.values()} == {'Chantal van Gastel', 'Saskia Noort', 'Carry Slee'}
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


def test_persona_save_refuses_external_change_and_preserves_disk(tmp_path: Path):
    from quietwriter.storage import PersonaExternalModificationError

    lib = Library(tmp_path)
    expected = lib.capture_persona_revision()
    external = lib.read_persona() + '\nREGEL_VAN_ANDERE_COMPUTER\n'
    lib.persona_path().write_text(external, encoding='utf-8')

    try:
        lib.save_persona('# Mijn lokale versie\n', expected_revision=expected)
    except PersonaExternalModificationError:
        pass
    else:
        raise AssertionError('Externe persona-wijziging moet vóór overschrijven worden geweigerd')

    assert lib.read_persona() == external


def test_persona_recovery_copy_is_separate_from_live_file(tmp_path: Path):
    lib = Library(tmp_path)
    original = lib.read_persona()
    target = lib.create_persona_recovery('lokale versie\n', kind='conflict_local')

    assert target.parent == tmp_path / 'archive' / 'persona'
    assert target.name.endswith('__conflict_local.md')
    assert target.read_text(encoding='utf-8') == 'lokale versie\n'
    assert lib.read_persona() == original


def test_persona_page_has_explicit_external_conflict_flow():
    source = Path('quietwriter/ui/persona_page.py').read_text(encoding='utf-8')
    assert 'PersonaExternalModificationError' in source
    assert 'expected_revision=self._loaded_revision' in source
    assert "create_persona_recovery(disk_text, kind='conflict_external')" in source
    assert "create_persona_recovery(local_text, kind='conflict_local')" in source
