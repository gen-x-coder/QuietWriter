from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_settings_uses_explicit_main_reference_for_committed_apply():
    source = (ROOT / 'quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert 'def __init__(self, settings: QSettings, main, models=None):' in source
    assert 'self.main = main' in source
    assert 'self.main.settings_saved(old_root, writing_layout_changed=writing_layout_changed)' in source
    assert "hasattr(self.parent(), 'settings_saved')" not in source


def test_spell_dictionary_load_happens_after_spell_panel_exists():
    source = (ROOT / 'quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    create = source.index('self.spell = SpellPanel(self)')
    load = source.index('self.load_dictionary_from_settings()', create)
    assert load > create


def test_ai_and_advanced_switches_have_live_rail_preview_but_saved_return_logic_stays_committed():
    settings = (ROOT / 'quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    main = (ROOT / 'quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    assert 'self.ai_enabled.toggled.connect(self._preview_feature_switches)' in settings
    assert 'self.advanced_options.toggled.connect(self._preview_feature_switches)' in settings
    assert 'def preview_feature_visibility(' in main
    preview = main[main.index('    def preview_feature_visibility'):main.index('    # Compatibility name', main.index('    def preview_feature_visibility'))]
    assert 'self._render_rail(state)' in preview
    assert '_apply_committed_navigation_effects' not in preview
    assert 'setCurrentWidget' not in preview
    assert "self.main._apply_feature_visibility()" in settings


def test_advanced_options_checkbox_does_not_repeat_its_row_label():
    source = (ROOT / 'quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert 'self.advanced_options = QCheckBox()' in source
    assert "self.advanced_options = QCheckBox(tr('settings.general.advanced_options'" not in source


def test_planning_has_page_level_title_and_explanation_in_both_locales():
    source = (ROOT / 'quietwriter/ui/planning/planning_page.py').read_text(encoding='utf-8')
    assert "tr('planning.title', 'Planning')" in source
    assert "tr('planning.info'" in source
    assert "info.setObjectName('muted')" in source
    assert 'info.setWordWrap(True)' in source
    for language in ('nl', 'en'):
        data = json.loads((ROOT / f'quietwriter/locales/{language}.json').read_text(encoding='utf-8'))
        assert data['planning.title']
        assert data['planning.info']
