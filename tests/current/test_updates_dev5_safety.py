from pathlib import Path


def test_update_download_stays_disabled_until_secure_engine_is_shipped():
    source = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert 'self.auto_update_download.setEnabled(False)' in source
    assert "'auto_update_download': False" in source
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
