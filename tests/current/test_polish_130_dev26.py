from pathlib import Path


def test_empty_planning_overlay_keeps_labels_compact_at_top():
    source = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    assert "title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)" in source
    assert "help_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)" in source
    assert "self.empty.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)" in source
    assert "self.empty_filler.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)" in source
    assert "self.empty_filler.setVisible(False)" in source
    assert "height = max(150, min(220, self.sizeHint().height()))" in source
    assert "self.scroll.setVisible(bool(scenes))" in source
