from pathlib import Path


def test_planning_button_stays_available_without_scenes_when_help_enabled():
    # 1.7.0: de knop Planning (popup) naast Tekstbreedte is weggehaald op verzoek
    # van Lucas: dubbelop met "In dit hoofdstuk", waar nu ook "✓ Klaar" staat.
    page = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    panel = Path('quietwriter/ui/chapter_context_panel.py').read_text(encoding='utf-8')
    assert 'planning_overlay' not in page and 'class PlanningOverlay' not in page
    assert 'planning.overlay.mark_written' in panel and 'markWritten' in panel
    assert "scene.status = 'geschreven'" in page


def test_empty_search_result_uses_same_panel_background():
    panel = Path('quietwriter/ui/search_panel.py').read_text(encoding='utf-8')
    theme = Path('quietwriter/themes.py').read_text(encoding='utf-8')
    assert "self.empty.setObjectName('searchEmptyResults')" in panel
    assert "self.results.setObjectName('searchResults')" in panel
    assert "self.result_area.setObjectName('searchResultArea')" in panel
    assert 'QWidget#searchResultArea, QListWidget#searchResults, QLabel#searchEmptyResults' in theme
    assert "background: {t['panel']}" in theme
