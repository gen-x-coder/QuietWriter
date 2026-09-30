from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
THEMES = ROOT / 'quietwriter' / 'themes.py'
EDITOR = ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py'
EDITOR_PAGE = ROOT / 'quietwriter' / 'ui' / 'editor_page.py'
INSERT_PANEL = ROOT / 'quietwriter' / 'ui' / 'insert_panel.py'


def test_spinbox_reserves_real_clickable_button_area():
    source = THEMES.read_text(encoding='utf-8')
    assert 'QSpinBox::up-button' in source
    assert 'QSpinBox::down-button' in source
    assert 'padding: 8px 34px 8px 10px' in source
    assert 'subcontrol-position: top right' in source
    assert 'subcontrol-position: bottom right' in source


def test_scene_break_has_hover_only_delete_affordance():
    source = EDITOR.read_text(encoding='utf-8')
    assert "self.scene_delete_button = QToolButton(self.viewport())" in source
    assert "setObjectName('sceneBreakDelete')" in source
    assert "self.scene_delete_button.hide()" in source
    assert 'def _update_scene_break_hover' in source
    assert 'def _delete_hovered_scene_break' in source
    assert 'remove_scene_break(text, block.position())' in source


def test_flyout_and_scene_break_strings_are_localized():
    source = EDITOR_PAGE.read_text(encoding='utf-8')
    insert_source = INSERT_PANEL.read_text(encoding='utf-8')
    assert "tr('editor.publication_structure'" in source
    assert "tr('insert.scene_break'" in insert_source
    assert "'insert.scene_break.tip'" in insert_source
    for locale in ('nl', 'en'):
        data = json.loads((ROOT / 'quietwriter' / 'locales' / f'{locale}.json').read_text(encoding='utf-8'))
        for key in ('editor.scene_break.delete', 'editor.publication_structure', 'insert.scene_break', 'insert.scene_break.tip'):
            assert data.get(key)
