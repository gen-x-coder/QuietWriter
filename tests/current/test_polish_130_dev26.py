from pathlib import Path


def test_empty_planning_overlay_keeps_labels_compact_at_top():
    # 1.7.0: de knop Planning (popup) naast Tekstbreedte is weggehaald op verzoek
    # van Lucas: dubbelop met "In dit hoofdstuk", waar nu ook "✓ Klaar" staat.
    page = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    panel = Path('quietwriter/ui/chapter_context_panel.py').read_text(encoding='utf-8')
    assert 'planning_overlay' not in page and 'class PlanningOverlay' not in page
    assert 'planning.overlay.mark_written' in panel and 'markWritten' in panel
    assert "scene.status = 'geschreven'" in page
