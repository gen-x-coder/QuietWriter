from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_planning_navigation_and_character_list_share_fixed_width():
    planning = (ROOT / 'quietwriter' / 'ui' / 'planning' / 'planning_page.py').read_text(encoding='utf-8')
    characters = (ROOT / 'quietwriter' / 'ui' / 'planning' / 'characters_page.py').read_text(encoding='utf-8')
    assert 'PLANNING_PANEL_WIDTH = 190' in planning
    assert "side.setFixedWidth(PLANNING_PANEL_WIDTH)" in planning
    assert "side.setFixedWidth(190)" in characters

def test_character_page_has_real_blank_canvas_state():
    source = (ROOT / 'quietwriter' / 'ui' / 'planning' / 'characters_page.py').read_text(encoding='utf-8')
    assert "self.canvas = QStackedWidget()" in source
    assert "self.blank = QWidget()" in source
    assert "self.canvas.setCurrentWidget(self.blank)" in source

def test_planning_notes_use_nearly_full_available_width():
    source = (ROOT / 'quietwriter' / 'ui' / 'planning' / 'notes_page.py').read_text(encoding='utf-8')
    assert 'lay.setContentsMargins(18,18,18,18)' in source
    assert 'self.editor.max_text_width = 100000' in source
    assert 'self.editor.min_side_margin = 8' in source
