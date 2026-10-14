from quietwriter import APP_NAME, __version__
from quietwriter.ai.prompting import build_system_prompt
from quietwriter.ai.response_guard import guard_memory_claims


def test_app_constants_and_version():
    assert APP_NAME == 'QuietWriter'
    assert __version__.startswith('1.5.0-dev.')


def test_author_can_define_new_canon_without_manuscript_evidence():
    prompt = build_system_prompt(persona='', book_profile='', book_memory='', planning_text='', context_label='test', context_text='')
    assert 'auteurscanon' in prompt
    assert 'niet in het manuscript voorkomen' in prompt
    assert 'NOOIT zelf feiten' in prompt
    assert '1–3 zinnen' in prompt


def test_false_saved_claim_corrected():
    output = guard_memory_claims('Ik heb deze informatie genoteerd in het boekgeheugen onder Decisions. Laat iets weten.')
    assert 'heb deze informatie genoteerd' in output
    assert 'Gebruik **Onthouden**' in output
    assert 'Laat iets weten.' in output


def test_future_save_promise_corrected():
    output = guard_memory_claims('Ik noteer dit direct in het boekgeheugen voor dit boek. Goed punt.')
    assert 'noteer dit direct' in output
    assert 'Gebruik **Onthouden**' in output
    assert 'Goed punt.' in output


def test_normal_analysis_not_changed():
    original = 'De auteur heeft Pip geen haar gegeven. Dit staat nog niet in de tekst.'
    assert guard_memory_claims(original) == original


def test_not_changed_when_app_confirms_storage():
    original = 'QuietWriter bevestigt: Opgeslagen in Boekgeheugen.'
    assert guard_memory_claims(original) == original
