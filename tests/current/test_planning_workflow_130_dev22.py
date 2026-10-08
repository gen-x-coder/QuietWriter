from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_scene_status_is_a_closed_choice_not_free_text():
    source = (ROOT / 'quietwriter' / 'ui' / 'planning' / 'outline_page.py').read_text(encoding='utf-8')
    assert "self.status=QComboBox(); self.status.setEditable(False)" in source
    assert "self.status.setEditText(scene.status)" not in source


def test_first_character_is_selected_when_planning_opens():
    source = (ROOT / 'quietwriter' / 'ui' / 'planning' / 'characters_page.py').read_text(encoding='utf-8')
    assert "self.refresh_list(keep_id=self.characters[0].id)" in source


def test_editor_has_planning_overlay_and_explicit_done_action():
    source = (ROOT / 'quietwriter' / 'ui' / 'editor_page.py').read_text(encoding='utf-8')
    assert "class PlanningOverlay(QFrame)" in source
    assert "planning.overlay.button" in source
    assert "planning.overlay.mark_written" in source
    assert "scene.status = 'geschreven'" in source


def test_ghost_text_includes_scene_status():
    source = (ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py').read_text(encoding='utf-8')
    section = source[source.index('def _ghost_detail_lines'):source.index('def _paint_planning_ghosts')]
    assert "planning.ghost.status" in section
    assert "planning.status.written" in section


def test_chapter_scrollbar_track_uses_page_background():
    themes = (ROOT / 'quietwriter' / 'themes.py').read_text(encoding='utf-8')
    assert "QTreeWidget#manuscriptTree QScrollBar::groove:vertical {{ background: {t['bg']}; border: 0; }}" in themes
    assert "QTreeWidget#manuscriptTree QScrollBar::add-page:vertical, QTreeWidget#manuscriptTree QScrollBar::sub-page:vertical {{ background: {t['bg']}; }}" in themes
