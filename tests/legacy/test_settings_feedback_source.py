from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_settings_has_single_explicit_commit_action_with_feedback():
    source = (ROOT / 'quietwriter' / 'ui' / 'settings_page.py').read_text(encoding='utf-8')
    assert "QPushButton('Terug zonder opslaan')" not in source
    assert 'def cancel(self):' not in source
    assert "QPushButton(tr('common.save', 'Opslaan'))" in source
    assert "self.save_feedback = QLabel(tr('settings.saved', 'Opgeslagen'), self)" in source
    assert 'self._show_saved_feedback(language_restart=' in source


def test_settings_navigation_away_restores_live_preview():
    source = (ROOT / 'quietwriter' / 'ui' / 'main_window.py').read_text(encoding='utf-8')
    assert 'def _leave_settings_preview(self):' in source
    assert 'self.settings_page.restore_preview()' in source


def test_settings_toast_is_theme_aware():
    source = (ROOT / 'quietwriter' / 'themes.py').read_text(encoding='utf-8')
    assert 'QLabel#settingsToast' in source


def test_model_refresh_does_not_persist_unsaved_settings():
    source = (ROOT / 'quietwriter' / 'ui' / 'settings_page.py').read_text(encoding='utf-8')
    start = source.index('    def refresh_models(self):')
    end = source.index('    def save_settings(self):')
    refresh_source = source[start:end]
    assert "self.settings.setValue('ai_provider'" not in refresh_source
    assert 'ProviderFactory.from_settings(FormSettings())' in refresh_source


def test_save_flushes_qsettings_before_confirmation():
    source = (ROOT / 'quietwriter' / 'ui' / 'settings_page.py').read_text(encoding='utf-8')
    assert 'self.settings.sync()' in source
    assert 'QSettings.Status.NoError' in source
