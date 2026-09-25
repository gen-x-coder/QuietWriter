from pathlib import Path

from quietwriter.ai.prompting import build_system_prompt
from quietwriter.book_memory import append_memory_entry, parse_book_memory, default_book_memory_markdown


def test_approved_memory_entry_is_plain_markdown_and_deduplicated():
    source = default_book_memory_markdown()
    updated, changed = append_memory_entry(source, 'canon', 'Eva rijdt in een blauwe Volvo.')
    assert changed is True
    memory = parse_book_memory(updated)
    assert '- Eva rijdt in een blauwe Volvo.' in memory['canon']

    again, changed_again = append_memory_entry(updated, 'canon', 'Eva rijdt in een blauwe Volvo.')
    assert changed_again is False
    assert parse_book_memory(again)['canon'].count('Eva rijdt in een blauwe Volvo.') == 1


def test_planning_context_is_explicit_and_near_question_context_in_system_prompt():
    planning = '# Geselecteerde personages\n\n## Anna\n- Rol: hoofdpersoon\n\n# Geselecteerde scènes\n\n## De kelder\n- Synopsis: Anna vindt de sleutel.'
    prompt = build_system_prompt(
        persona='Rustige stijl.',
        book_profile='Psychologische thriller.',
        book_memory='Eva rijdt in een gele auto.',
        planning_text=planning,
        context_label='Geselecteerde tekst',
        context_text='Eva stapt in haar blauwe auto.',
    )
    assert 'Voor deze vraag heeft de gebruiker expliciet Planning-context geselecteerd.' in prompt
    assert '## Anna' in prompt
    assert '## De kelder' in prompt
    assert 'Anna vindt de sleutel.' in prompt
    assert 'GESELECTEERDE PLANNINGCONTEXT' in prompt
    assert prompt.index('CONTEXT (Geselecteerde tekst)') < prompt.index('GESELECTEERDE PLANNINGCONTEXT')


def test_ai_ui_exposes_memory_save_result_and_exact_planning_context():
    ai = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    assert "self.memory_feedback = QLabel()" in ai
    assert "Opgeslagen in Boekgeheugen." in ai
    assert "Niet opgeslagen:" in ai
    assert "page.adopt_book(book)" in ai
    assert "Geselecteerde Planning-context:" in ai
    assert "lines.extend(['', 'Geselecteerde Planning-context:', planning_text])" in ai
    assert "build_system_prompt(" in ai


def test_book_memory_suggestion_rebinds_to_active_book_before_save():
    page = Path('quietwriter/ui/book_memory_page.py').read_text(encoding='utf-8')
    assert 'active = self.main.active_book()' in page
    assert 'self.adopt_book(active)' in page
    assert 'append_memory_entry(source, section_key, clean)' in page


def test_memory_suggestion_does_not_resync_stale_editor_before_persisting():
    """Regression for 0.23.5: programmatic append must survive a stale visible field."""
    page = Path('quietwriter/ui/book_memory_page.py').read_text(encoding='utf-8')
    add_start = page.index('    def add_suggestion(')
    add_end = page.index('    def _resolve_external_change(', add_start)
    add_body = page[add_start:add_end]
    save_start = page.index('    def save(')
    save_end = page.index('    def add_suggestion(', save_start)
    save_body = page[save_start:save_end]

    assert 'self._store_editor()' in add_body
    assert 'append_memory_entry(source, section_key, clean)' in add_body
    assert 'self._persist_memory_state()' in add_body
    assert 'self.save()' not in add_body
    assert 'self._store_editor()' in save_body
    assert 'return self._persist_memory_state()' in save_body
