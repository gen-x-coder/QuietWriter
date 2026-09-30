from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_editor_dirty_state_compares_source_text_not_presentation_events():
    source = (ROOT / 'quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    assert "self._clean_text = ''" in source
    assert 'if current_text == self._clean_text:' in source
    assert 'self.autosave_timer.stop()' in source
    assert 'def _editor_source_text(self):' in source
    manuscript = (ROOT / 'quietwriter/ui/manuscript_editor.py').read_text(encoding='utf-8')
    assert "toRawText().replace('\\u2029', '\\n')" in manuscript
    assert 'return self.editor.source_text()' in source
    assert 'self._clean_text = self._editor_source_text()' in source


def test_preview_width_uses_effective_preview_values_and_does_not_close_ai_panel():
    source = (ROOT / 'quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    assert 'self._feature_visibility_preview = None' in source
    assert 'preview = self._feature_visibility_preview or {}' in source
    assert "preview.get('ai_enabled'" in source
    assert "preview.get('advanced'" in source
    preview = source[source.index('    def preview_feature_visibility'):source.index('    # Compatibility name')]
    assert '_apply_committed_navigation_effects' not in preview
    commit = source[source.index('    def _apply_committed_navigation_effects'):source.index('    def _set_feature_visibility')]
    assert 'hidden_right' in commit
    assert 'self.editor_page.right.hide()' in commit
    assert 'fallback_destination' in commit


def test_failed_settings_sync_restores_previous_qsettings_and_preview():
    source = (ROOT / 'quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    save = source[source.index('    def save_settings(self):'):source.index('    def begin_session(self):')]
    assert 'previous = {' in save
    assert 'if self.settings.status() != QSettings.Status.NoError:' in save
    assert 'self.settings.remove(key)' in save
    assert 'self.restore_preview()' in save
    # Runtime application only happens after a successful sync.
    assert save.index("if self.settings.status() != QSettings.Status.NoError:") < save.index('self.main.settings_saved(')
