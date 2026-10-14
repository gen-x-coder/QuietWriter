from pathlib import Path
from quietwriter import APP_NAME, __version__
from quietwriter.ai.prompting import build_system_prompt
from quietwriter.ai.response_guard import guard_memory_claims
from quietwriter.update_pilot_gate import PILOT_MARKER, pilot_enabled

ROOT = Path(__file__).resolve().parents[2]

def test_startup_contract():
    assert APP_NAME == 'QuietWriter'
    assert __version__.startswith('1.5.0-dev.')

def test_reader_prompt_covers_followup_ghostwriting_and_canon():
    prompt = build_system_prompt(persona='', book_profile='', book_memory='Pip heeft blauwe ogen', planning_text='', context_label='hoofdstuk', context_text='')
    for phrase in ('nog twee alinea', 'auteurscanon', 'geen doorlopende fictieve', 'NOOIT zelf feiten'):
        assert phrase in prompt

def test_memory_claim_is_not_confirmed_by_ai():
    assert 'Gebruik **Onthouden**' in guard_memory_claims('Ik heb dit opgeslagen in het boekgeheugen.')

def test_pilot_requires_empty_file_at_active_workspace(tmp_path):
    assert not pilot_enabled(tmp_path)
    (tmp_path / PILOT_MARKER).touch()
    assert pilot_enabled(tmp_path)
    (tmp_path / PILOT_MARKER).write_text('true')
    assert not pilot_enabled(tmp_path)

def test_all_experimental_updater_ui_is_marker_gated():
    settings = (ROOT / 'quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    main = (ROOT / 'quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    assert 'if updater_pilot:' in settings
    assert settings.index('if updater_pilot:') < settings.index("tr('settings.updates.download',")
    assert 'if pilot_enabled(self.library.root):' in main
    assert 'self.auto_update_download.setEnabled(False)' in settings
