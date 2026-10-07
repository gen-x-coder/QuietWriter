import json
from pathlib import Path


def test_panel_help_contract_is_shared_across_right_panels():
    panel_help = Path('quietwriter/ui/panel_help.py').read_text(encoding='utf-8')
    assert "help/{panel_id}/dismissed" in panel_help
    assert "common.understood" in panel_help
    assert "panelHelpButton" in panel_help
    assert "collapse_temporarily" in panel_help

    expected = {
        'search_panel.py': "'search'",
        'chapter_context_panel.py': "'chapter_context'",
        'open_points_panel.py': "'open_points'",
        'spell_panel.py': "'spell'",
        'history_panel.py': "'history'",
        'darlings_actions_panel.py': "'darlings'",
    }
    for filename, panel_id in expected.items():
        source = Path('quietwriter/ui', filename).read_text(encoding='utf-8')
        assert 'PanelHelp(' in source
        assert panel_id in source
    ai = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    assert 'PanelHelp(' in ai and "'ai'" in ai
    assert 'self.panel_help.collapse_temporarily()' in ai


def test_open_point_first_use_modal_is_removed():
    source = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    assert '_explain_open_points_once' not in source
    assert "open_points/explained" not in source


def test_help_reset_and_notice_styling_are_present():
    settings = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert "def _reset_panel_help" in settings
    assert "beginGroup('help')" in settings
    assert "settings.help.reset_button" in settings
    ai = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    assert "setObjectName('noticePanel')" in ai
    theme = Path('quietwriter/themes.py').read_text(encoding='utf-8')
    assert 'QWidget#noticePanel' in theme and "warning_soft" in theme


def test_panel_help_locale_keys_match_in_all_five_languages():
    required = {
        'panel_help.toggle', 'panel_help.region', 'settings.section.help',
        'settings.help.label', 'settings.help.reset_button', 'settings.help.help',
        'settings.help.reset_done', 'panel_help.search', 'panel_help.chapter_context',
        'panel_help.open_points', 'panel_help.ai', 'panel_help.spell',
        'panel_help.history', 'panel_help.darlings',
    }
    old = {'chapter_context.intro', 'open_points.panel_intro', 'open_points.explain_title', 'open_points.explain_text'}
    for lang in ('nl', 'en', 'de', 'fr', 'es'):
        data = json.loads(Path(f'quietwriter/locales/{lang}.json').read_text(encoding='utf-8'))
        assert required <= data.keys()
        assert not (old & data.keys())
        for key in required:
            text = data[key]
            assert isinstance(text, str) and text.strip()
