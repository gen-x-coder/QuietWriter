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
    # 1.7.0: de knop Planning (popup) naast Tekstbreedte is weggehaald op verzoek
    # van Lucas: dubbelop met "In dit hoofdstuk", waar nu ook "✓ Klaar" staat.
    page = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    panel = Path('quietwriter/ui/chapter_context_panel.py').read_text(encoding='utf-8')
    assert 'planning_overlay' not in page and 'class PlanningOverlay' not in page
    assert 'planning.overlay.mark_written' in panel and 'markWritten' in panel
    assert "scene.status = 'geschreven'" in page
