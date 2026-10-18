from pathlib import Path


def test_no_hidden_download_or_pilot_settings_remain():
    source = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert 'auto_update_download' not in source
    # 1.6.1: "Testkopie" is alleen een statusregel (pilotbestand naast de exe),
    # nooit een instelling die een gebruiker kan aanzetten.
    pilot_lines = [line for line in source.splitlines() if 'pilot' in line]
    assert pilot_lines and all('setValue' not in l and 'settings.value' not in l and 'QCheckBox' not in l
                               for l in pilot_lines)
    assert 'mode_pilot' in source
    assert 'self.show_update_status(' in source


def test_update_checks_respect_saved_user_choice():
    source = Path('quietwriter/app.py').read_text(encoding='utf-8')
    assert "settings.value('auto_update_check', False, bool)" in source
    assert 'check_for_updates(silent=True)' in source


def test_update_release_must_be_official_and_stable():
    source = Path('quietwriter/update_checker.py').read_text(encoding='utf-8')
    assert "payload.get('prerelease')" in source
    assert "payload.get('draft')" in source
    assert 'https://github.com/gen-x-coder/QuietWriter/releases/tag/' in source
