from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_search_panel_keeps_fixed_results_region_and_avoids_double_zero_message():
    source = (ROOT / "quietwriter" / "ui" / "search_panel.py").read_text(encoding="utf-8")
    assert "QStackedLayout" in source
    assert "lay.addWidget(self.result_area, 1)" in source
    assert "self.result_stack.setCurrentWidget(self.empty if active and not rows else self.results)" in source
    assert "if active and rows else ''" in source


def test_internal_paste_collapses_selection_after_insert():
    source = (ROOT / "quietwriter" / "ui" / "manuscript_editor.py").read_text(encoding="utf-8")
    assert "caret.setPosition(min(position + len(insertion), max_pos))" in source
    assert "self._selection_range = None" in source


def test_planning_button_follows_planning_help_setting():
    source = (ROOT / "quietwriter" / "ui" / "editor_page.py").read_text(encoding="utf-8")
    # Since dev.25 the button remains a stable Planning entry point for any
    # ordinary chapter while Planning help is enabled, even without scenes.
    assert "overlay_available = bool(planning_help_enabled and available)" in source
    assert "self.planning_overlay_button.setVisible(overlay_available)" in source
    assert "self.planning_overlay.hide()" in source
