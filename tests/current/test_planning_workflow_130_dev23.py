from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_planning_button_is_a_real_toggle_and_popup_syncs_back():
    source = (ROOT / 'quietwriter' / 'ui' / 'editor_page.py').read_text(encoding='utf-8')
    assert 'self.planning_overlay_button.setCheckable(True)' in source
    assert 'self.planning_overlay_button.toggled.connect(self._toggle_planning_overlay)' in source
    assert 'self.planning_overlay.closed.connect(self._planning_overlay_closed)' in source
    assert 'QTimer.singleShot(0, self._sync_planning_overlay_button)' in source


def test_planning_overlay_prefers_narrow_tall_shape():
    source = (ROOT / 'quietwriter' / 'ui' / 'editor_page.py').read_text(encoding='utf-8')
    assert "width_cap = max(320, int(owner_width * 0.30))" in source
    assert "int(owner_width * 0.26)" in source
    assert "height_cap = max(420, int(owner_height * 0.82))" in source
    assert "int(owner_height * 0.76)" in source


def test_status_labels_are_title_cased_in_dropdown_and_ghost():
    outline = (ROOT / 'quietwriter' / 'ui' / 'planning' / 'outline_page.py').read_text(encoding='utf-8')
    ghost = (ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py').read_text(encoding='utf-8')
    assert "('idee', 'planning.status.idea', 'Idee')" in outline
    assert "('uitgewerkt', 'planning.status.developed', 'Uitgewerkt')" in outline
    assert "('geschreven', 'planning.status.written', 'Geschreven')" in outline
    assert "tr('planning.status.idea', 'Idee')" in ghost
    assert "tr('planning.status.written', 'Geschreven')" in ghost


def test_chapter_scrollbar_groove_and_pages_follow_page_background():
    themes = (ROOT / 'quietwriter' / 'themes.py').read_text(encoding='utf-8')
    assert "QTreeWidget#manuscriptTree QScrollBar::groove:vertical {{ background: {t['bg']}; border: 0; }}" in themes
    assert "QTreeWidget#manuscriptTree QScrollBar::add-page:vertical, QTreeWidget#manuscriptTree QScrollBar::sub-page:vertical {{ background: {t['bg']}; }}" in themes
