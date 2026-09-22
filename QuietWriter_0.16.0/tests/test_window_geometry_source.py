from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_window_geometry_uses_qt_native_restore_while_custom_clamp_is_reviewed():
    source = (ROOT / "quietwriter" / "ui" / "main_window.py").read_text(encoding="utf-8")
    assert "self.settings.setValue('geometry', self.saveGeometry())" in source
    assert "self.restoreGeometry(g)" in source
    assert "window_geometry_v2" not in source
    assert "def _safe_window_geometry" not in source
