from pathlib import Path

from quietwriter.persona_profile import empty_profile, parse_persona, render_persona
from quietwriter.book_profile import empty_book_profile, parse_book_profile, render_book_profile
from quietwriter.book_memory import empty_book_memory, parse_book_memory, render_book_memory


ROOT = Path(__file__).resolve().parents[1]


def _source(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_profile_like_fields_roundtrip_literal_markdown_h2_lines():
    persona = empty_profile()
    persona['examples'] = 'Voorbeeld\n## Familie\nBram blijft.\n## Vermijden\nDit is voorbeeldtekst, geen sectie.'
    parsed_persona = parse_persona(render_persona(persona))
    assert parsed_persona['examples'] == persona['examples']
    assert parsed_persona['avoid'] == ''

    profile = empty_book_profile()
    profile['premise'] = 'Premisse\n## Eigen tussenkop\nBlijft hier.\n## Sfeer & toon\nOok dit is letterlijke veldinhoud.'
    parsed_profile = parse_book_profile(render_book_profile(profile))
    assert parsed_profile['premise'] == profile['premise']
    assert parsed_profile['tone'] == ''

    memory = empty_book_memory()
    memory['canon'] = 'Anna is 34.\n## Familie\nHaar broer heet Bram.\n## Besluiten\nBram overleeft.'
    memory['decisions'] = '- Geen proloog'
    parsed_memory = parse_book_memory(render_book_memory(memory))
    assert parsed_memory['canon'] == memory['canon']
    assert parsed_memory['decisions'] == '- Geen proloog'


def test_pdf_layout_uses_writer_dpi_and_explicit_table_keep_together_pass():
    source = _source('quietwriter/exporting/pdf_exporter.py')
    render = source[source.index('    def render_to'):]
    assert 'qdoc.documentLayout().setPaintDevice(writer)' in render
    assert render.index('qdoc.documentLayout().setPaintDevice(writer)') < render.index('qdoc.setHtml(html_text)')
    assert '_keep_pdf_tables_together(qdoc, body_h, QTextTable, QTextFormat)' in render
    assert 'PageBreak_AlwaysBefore' in source
    assert 'table.image-box { border-collapse: collapse; page-break-inside: avoid; }' not in source


def test_planning_conflict_does_not_reapply_pending_data_whose_file_changed():
    source = _source('quietwriter/ui/planning/planning_page.py')
    assert "'planning/notes.md' not in changed" in source
    assert "'planning/characters.json' not in changed" in source
    assert 'planning_changed_files=exc.changed_files' in source
    assert 'create_version_with_file_overrides' in source
    assert 'Lokale planning veilig bewaard' in source


def test_existing_character_edits_are_in_pending_snapshot():
    source = _source('quietwriter/ui/planning/characters_page.py')
    block = source[source.index('    def pending_editor_snapshot'):source.index('    def save_pending')]
    assert "'is_new': False" in block
    assert 'candidate == stored' in block
    assert 'characters_with_snapshot' in block


def test_persona_is_saved_on_navigation_and_close():
    source = _source('quietwriter/ui/main_window.py')
    guard = source[source.index('    def _save_planning_if_active'):source.index('    def show_editor')]
    close = source[source.index('    def closeEvent'):source.index('    def restore_state')]
    assert 'self.stack.currentWidget() is self.persona and self.persona.dirty' in guard
    assert 'self.persona.dirty and self.persona.save() is False' in close


def test_thinking_false_is_not_sent_for_known_non_disableable_model():
    settings = _source('quietwriter/ui/settings_page.py')
    ai = _source('quietwriter/ai/ui.py')
    assert "ai_thinking_can_disable/{provider_name}/{name}" in settings
    assert "capability != 'false'" in ai
    assert "if thinking_disabled:" in ai
