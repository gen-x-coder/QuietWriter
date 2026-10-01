from pathlib import Path


def test_ai_ui_imports_translation_helper():
    source = (Path(__file__).parents[2] / "quietwriter" / "ai" / "ui.py").read_text(encoding="utf-8")
    assert "from ..i18n import tr" in source
    assert "tr(\'ai.thinking_base\'" in source or 'tr("ai.thinking_base"' in source
