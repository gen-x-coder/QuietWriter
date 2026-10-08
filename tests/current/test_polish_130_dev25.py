from pathlib import Path


def test_planning_button_stays_available_without_scenes_when_help_enabled():
    source = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    assert 'overlay_available = bool(planning_help_enabled and available)' in source
    assert 'if not scenes:' not in source[source.find('def _toggle_planning_overlay'):source.find('def _planning_overlay_closed')]
    assert "Geen planning voor dit hoofdstuk." in source


def test_empty_search_result_uses_same_panel_background():
    panel = Path('quietwriter/ui/search_panel.py').read_text(encoding='utf-8')
    theme = Path('quietwriter/themes.py').read_text(encoding='utf-8')
    assert "self.empty.setObjectName('searchEmptyResults')" in panel
    assert "self.results.setObjectName('searchResults')" in panel
    assert "self.result_area.setObjectName('searchResultArea')" in panel
    assert 'QWidget#searchResultArea, QListWidget#searchResults, QLabel#searchEmptyResults' in theme
    assert "background: {t['panel']}" in theme
