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
    assert "self.canvas = CurrentPageStack()" in source
    assert "self.blank = QWidget()" in source
    assert "self.canvas.setCurrentWidget(self.blank)" in source


def test_character_and_outline_share_primary_page_header_language():
    characters = (ROOT / 'quietwriter' / 'ui' / 'planning' / 'characters_page.py').read_text(encoding='utf-8')
    outline = (ROOT / 'quietwriter' / 'ui' / 'planning' / 'outline_page.py').read_text(encoding='utf-8')
    assert "QLabel(tr('planning.characters.title', 'Personages'))" in characters
    assert "QPushButton(tr('planning.characters.new', 'Nieuw personage'))" in characters
    assert "add.setObjectName('primaryButton')" in characters
    assert "QLabel(tr('planning.outline.title', 'Outline'))" in outline
    assert "QPushButton(tr('planning.outline.new_scene', 'Nieuwe scène'))" in outline
    assert "add.setObjectName('primaryButton')" in outline
    assert "QPushButton('+')" not in characters


def test_character_list_keeps_quiet_micro_label_below_page_header():
    source = (ROOT / 'quietwriter' / 'ui' / 'planning' / 'characters_page.py').read_text(encoding='utf-8')
    assert "QLabel(tr('planning.characters.list_heading', 'PERSONAGES'))" in source
    assert "setObjectName('planningMicroLabel')" in source


def test_planning_notes_use_same_page_margins_and_nearly_full_available_width():
    source = (ROOT / 'quietwriter' / 'ui' / 'planning' / 'notes_page.py').read_text(encoding='utf-8')
    assert 'lay.setContentsMargins(28,24,34,30)' in source
    assert "QLabel(tr('planning.notes.title', 'Notities'))" in source
    assert 'self.editor.max_text_width = 100000' in source
    assert 'self.editor.min_side_margin = 8' in source
