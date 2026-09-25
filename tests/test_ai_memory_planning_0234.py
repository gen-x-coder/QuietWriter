from pathlib import Path

from quietwriter.ai.memory_suggestions import (
    MemorySuggestion, extract_memory_suggestions, proposal_instruction,
)
from quietwriter.ai.planning_context import PlanningSelection, build_planning_context, options_for_book
from quietwriter.planning_models import Character, Relation, Scene
from quietwriter.planning_storage import PlanningStore
from quietwriter.storage import Library


def test_memory_proposals_are_stripped_from_visible_answer():
    response = (
        'De alinea werkt, maar de auto botst met het bestaande boekgeheugen.\n\n'
        '[[QW_MEMORY|canon]]Eva rijdt vanaf hoofdstuk 8 in een blauwe Volvo.[[/QW_MEMORY]]\n'
        '[[QW_MEMORY|decisions]]De kleurwijziging is bewust en vervangt de oude gele auto.[[/QW_MEMORY]]'
    )
    visible, suggestions = extract_memory_suggestions(response)
    assert visible == 'De alinea werkt, maar de auto botst met het bestaande boekgeheugen.'
    assert suggestions == [
        MemorySuggestion('canon', 'Eva rijdt vanaf hoofdstuk 8 in een blauwe Volvo.'),
        MemorySuggestion('decisions', 'De kleurwijziging is bewust en vervangt de oude gele auto.'),
    ]


def test_invalid_or_empty_memory_marker_is_not_silently_interpreted():
    invalid = 'Antwoord.\n[[QW_MEMORY|unknown]]Niet opslaan.[[/QW_MEMORY]]'
    visible, suggestions = extract_memory_suggestions(invalid)
    assert suggestions == []
    assert 'unknown' in visible
    empty_visible, empty_suggestions = extract_memory_suggestions('[[QW_MEMORY|canon]]   [[/QW_MEMORY]]')
    assert empty_suggestions == []
    assert 'QW_MEMORY' in empty_visible


def test_memory_proposal_instruction_is_small_model_friendly():
    instruction = proposal_instruction()
    assert 'maximaal twee' in instruction
    assert 'canon, book_style, decisions, preferences en open_points' in instruction
    assert 'JSON' not in instruction


def test_planning_context_only_contains_explicit_selection(tmp_path: Path):
    lib = Library(tmp_path)
    book = lib.create_book('Planningcontext')
    lib.track_book(book)
    store = PlanningStore(lib)
    anna = Character(name='Anna', role='hoofdpersoon', motivation='haar broer vinden')
    bram = Character(name='Bram', role='buurman', fears='hoogte')
    anna.relations.append(Relation(target_id=bram.id, type='buur', description='wantrouwt hem'))
    store.save_characters(book, [anna, bram])
    chapter = book.sections[0].chapters[0]
    scene = Scene(
        title='De kelder', chapter_id=chapter.id, synopsis='Anna vindt een sleutel.',
        character_ids=[anna.id], location='kelder', goal='de deur openen', status='uitgewerkt'
    )
    other = Scene(title='Niet geselecteerd', synopsis='Mag niet in context.')
    store.save_scenes(book, [scene, other])
    store.save_notes(book, 'Let op de tijdlijn van donderdag.')

    selection = PlanningSelection(character_ids={anna.id}, scene_ids={scene.id}, include_notes=True)
    text, labels = build_planning_context(lib, book, selection)
    assert '## Anna' in text
    assert 'Motivatie: haar broer vinden' in text
    assert 'buur met Bram' in text
    assert '## De kelder' in text
    assert 'Anna vindt een sleutel.' in text
    assert 'Let op de tijdlijn van donderdag.' in text
    assert '## Bram' not in text
    assert 'Mag niet in context.' not in text
    assert labels == ['1 personage', '1 scène', 'notities']


def test_planning_options_and_empty_selection(tmp_path: Path):
    lib = Library(tmp_path)
    book = lib.create_book('Opties')
    lib.track_book(book)
    store = PlanningStore(lib)
    store.save_characters(book, [Character(name='Lina')])
    store.save_scenes(book, [Scene(title='Ontmoeting')])
    options = options_for_book(lib, book)
    assert [item.label for item in options.characters] == ['Lina']
    assert [item.label for item in options.scenes] == ['Ontmoeting']
    assert options.notes_available is False
    assert build_planning_context(lib, book, PlanningSelection()) == ('', [])


def test_ai_source_has_active_memory_check_user_approval_and_planning_picker():
    ai = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    prompting = Path('quietwriter/ai/prompting.py').read_text(encoding='utf-8')
    memory_page = Path('quietwriter/ui/book_memory_page.py').read_text(encoding='utf-8')
    dialog = Path('quietwriter/ui/planning_context_dialog.py').read_text(encoding='utf-8')
    assert 'vergelijk relevante feiten en besluiten uit het boekgeheugen actief' in prompting
    assert "self.memory_accept = QPushButton('Onthouden')" in ai
    assert "self.memory_edit = QPushButton('Bewerken')" in ai
    assert "self.memory_ignore = QPushButton('Negeren')" in ai
    assert 'extract_memory_suggestions(self.current_assistant)' in ai
    assert 'page.add_suggestion' in ai
    assert 'def add_suggestion(self, section_key: str, text: str)' in memory_page
    assert "QPushButton('Planning-context…')" in ai
    assert 'PlanningContextDialog' in ai
    assert 'Qt.ItemIsUserCheckable' in dialog
    assert 'GESELECTEERDE PLANNINGCONTEXT' in prompting


def test_memory_protocol_is_hidden_during_streaming():
    ai = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    assert "marker_at = stream_text.find('[[QW_MEMORY|')" in ai
    assert 'stream_text = stream_text[:marker_at].rstrip()' in ai
