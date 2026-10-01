from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def test_chapter_drop_is_deferred_until_after_native_drag_loop():
    source = (ROOT / 'quietwriter' / 'ui' / 'manuscript_tree.py').read_text(encoding='utf-8')
    start_drag = source[source.index('    def startDrag'):source.index('    def dragEnterEvent')]
    drop = source[source.index('    def dropEvent'):source.index('    def paintEvent')]
    assert 'drag.exec(Qt.MoveAction)' in start_drag
    assert 'self._schedule_drag_finish()' in start_drag
    assert start_drag.index('drag.exec(Qt.MoveAction)') < start_drag.rindex('self._schedule_drag_finish()')
    assert 'self._pending_drop = (source_id' in drop
    assert 'self.chapterDropped.emit' not in drop
    assert 'self._drop_target = None' in drop
    schedule = source[source.index('    def _schedule_drag_finish'):source.index('    def _finish_drag')]
    finish = source[source.index('    def _finish_drag'):source.index('    def mouseMoveEvent')]
    assert 'QTimer.singleShot(0' in schedule
    assert 'pending_drop = self._pending_drop' in schedule
    assert 'self.chapterDropped.emit' in finish


def test_ai_visibility_is_reapplied_after_restored_window_state():
    source = (ROOT / 'quietwriter' / 'ui' / 'main_window.py').read_text(encoding='utf-8')
    assert 'self.restore_state(); self._apply_feature_visibility();' in source
    sync = source[source.index('    def sync_tool_buttons'):source.index('    def closeEvent')]
    assert "ai_enabled = self.settings.value('ai_enabled', True, bool)" in sync
    assert 'self.ai_button.setVisible(ai_enabled)' in sync
    commit = source[source.index('    def _apply_committed_navigation_effects'):source.index('    def _set_feature_visibility')]
    assert 'self.editor_page.right.setCurrentWidget(self.editor_page.search)' in commit
    assert 'self.editor_page.right.hide()' in commit
    preview = source[source.index('    def preview_feature_visibility'):source.index('    # Compatibility name')]
    assert 'self.editor_page.right.hide()' not in preview


def test_program_language_is_selectable_and_persisted():
    settings = (ROOT / 'quietwriter' / 'ui' / 'settings_page.py').read_text(encoding='utf-8')
    app = (ROOT / 'quietwriter' / 'app.py').read_text(encoding='utf-8')
    assert "self.language.addItem(tr('language.english', 'Engels'), 'en')" in settings
    assert "'language': new_language" in settings
    assert "self.language.findData(language_value)" in settings
    assert "set_locale(str(settings.value('language', 'nl') or 'nl'))" in app


def test_language_copy_exists_in_both_locales():
    for language in ('nl', 'en'):
        data = json.loads((ROOT / 'quietwriter' / 'locales' / f'{language}.json').read_text(encoding='utf-8'))
        assert data['language.dutch']
        assert data['language.english']
        assert data['settings.general.language_help']
        assert data['settings.saved_restart_language']
