from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_planning_button_is_a_real_toggle_and_popup_syncs_back():
    # 1.7.0: de knop Planning (popup) naast Tekstbreedte is weggehaald op verzoek
    # van Lucas: dubbelop met "In dit hoofdstuk", waar nu ook "✓ Klaar" staat.
    page = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    panel = Path('quietwriter/ui/chapter_context_panel.py').read_text(encoding='utf-8')
    assert 'planning_overlay' not in page and 'class PlanningOverlay' not in page
    assert 'planning.overlay.mark_written' in panel and 'markWritten' in panel
    assert "scene.status = 'geschreven'" in page


def test_planning_overlay_prefers_narrow_tall_shape():
    # 1.7.0: de knop Planning (popup) naast Tekstbreedte is weggehaald op verzoek
    # van Lucas: dubbelop met "In dit hoofdstuk", waar nu ook "✓ Klaar" staat.
    page = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    panel = Path('quietwriter/ui/chapter_context_panel.py').read_text(encoding='utf-8')
    assert 'planning_overlay' not in page and 'class PlanningOverlay' not in page
    assert 'planning.overlay.mark_written' in panel and 'markWritten' in panel
    assert "scene.status = 'geschreven'" in page


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
