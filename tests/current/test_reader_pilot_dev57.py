from pathlib import Path
from quietwriter import APP_NAME, __version__
from quietwriter.ai.prompting import build_system_prompt
from quietwriter.ai.response_guard import guard_memory_claims

ROOT = Path(__file__).resolve().parents[2]

def test_startup_contract():
    assert APP_NAME == 'QuietWriter'
    assert __version__ == '1.7.1'

def test_reader_prompt_covers_followup_ghostwriting_and_canon():
    prompt = build_system_prompt(persona='', book_profile='', book_memory='Pip heeft blauwe ogen', planning_text='', context_label='hoofdstuk', context_text='')
    for phrase in ('nog twee alinea', 'auteurscanon', 'geen doorlopende fictieve', 'NOOIT zelf feiten'):
        assert phrase in prompt

def test_memory_claim_is_not_confirmed_by_ai():
    assert 'Gebruik **Onthouden**' in guard_memory_claims('Ik heb dit opgeslagen in het boekgeheugen.')
