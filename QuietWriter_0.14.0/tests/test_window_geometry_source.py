from pathlib import Path


def test_window_geometry_uses_validated_rect_not_opaque_restore_geometry():
    source = (Path(__file__).parents[1] / 'quietwriter' / 'ui' / 'main_window.py').read_text(encoding='utf-8')
    assert "window_geometry_v2" in source
    assert "_safe_window_geometry" in source
    assert "restoreGeometry(" not in source
    assert "self.saveGeometry(" not in source
    assert "window_maximized" in source
