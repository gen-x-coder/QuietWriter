from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
THEMES = ROOT / 'quietwriter' / 'themes.py'
EDITOR_PAGE = ROOT / 'quietwriter' / 'ui' / 'editor_page.py'
MAIN_WINDOW = ROOT / 'quietwriter' / 'ui' / 'main_window.py'
INSERT_PANEL = ROOT / 'quietwriter' / 'ui' / 'insert_panel.py'


def test_spinbox_arrows_are_explicit_visible_assets():
    source = THEMES.read_text(encoding='utf-8')
    assert 'QSpinBox::up-arrow' in source
    assert 'QSpinBox::down-arrow' in source
    assert 'spin-up.svg' in source
    assert 'spin-down.svg' in source
    assert (ROOT / 'quietwriter' / 'icons' / 'spin-up.svg').exists()
    assert (ROOT / 'quietwriter' / 'icons' / 'spin-down.svg').exists()


def test_insert_is_a_regular_right_side_panel_not_a_popup_menu():
    editor = EDITOR_PAGE.read_text(encoding='utf-8')
    main = MAIN_WINDOW.read_text(encoding='utf-8')
    panel = INSERT_PANEL.read_text(encoding='utf-8')
    assert 'self.insert = InsertPanel()' in editor
    assert 'self.right.addWidget(self.insert)' in editor
    assert 'self._toggle_right_widget(self.insert, self.insert.scene_break_button)' in editor
    assert 'QMenu(self.main)' not in editor
    assert "self.insert_button = trb('insert'" in main
    assert "currentWidget() is self.editor_page.insert" in main
    assert 'CurrentPageStack' in panel


def test_insert_scene_break_closes_panel_after_action():
    source = EDITOR_PAGE.read_text(encoding='utf-8')
    assert 'def _insert_scene_break_from_panel' in source
    assert 'self.insert_scene_break()' in source
    assert 'self.right.hide()' in source
    assert 'self.main.sync_tool_buttons()' in source


def test_insert_strings_exist_in_both_locales():
    keys = (
        'insert.title', 'insert.description', 'insert.scene_break',
        'insert.scene_break.description', 'insert.scene_break.tip', 'insert.add',
    )
    for locale in ('nl', 'en'):
        data = json.loads((ROOT / 'quietwriter' / 'locales' / f'{locale}.json').read_text(encoding='utf-8'))
        for key in keys:
            assert data.get(key)
