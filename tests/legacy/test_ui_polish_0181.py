from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
SETTINGS = ROOT / "quietwriter" / "ui" / "settings_page.py"
TOOLBAR = ROOT / "quietwriter" / "ui" / "selection_toolbar.py"
THEMES = ROOT / "quietwriter" / "themes.py"


def test_settings_rows_use_stable_invisible_columns():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "grid = QGridLayout(row)" in source
    assert "grid.setColumnMinimumWidth(0, 320)" in source
    assert "info.setFixedWidth(320)" in source
    assert "control_host.setMinimumWidth(320)" in source


def test_font_preview_is_a_real_preview_card_beside_selector():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "preview_card.setObjectName('fontPreviewCard')" in source
    assert "self.font_preview_meta.setObjectName('fontPreviewMeta')" in source
    assert "preview_card.setMinimumWidth(420)" in source
    assert "fh.addWidget(self.editor_font, 0, Qt.AlignTop); fh.addWidget(preview_card, 1)" in source


def test_workspace_control_has_useful_minimum_width():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "box.setMinimumWidth(680)" in source
    assert "self.root.setMinimumWidth(540)" in source


def test_selection_toolbar_tooltips_work_on_nonactivating_window():
    source = TOOLBAR.read_text(encoding="utf-8")
    assert "Qt.WA_AlwaysShowToolTips" in source
    assert "btn.setToolTipDuration(7000)" in source
    assert "btn.setAccessibleName(tooltip)" in source
    assert "tr(f'{key}.tip'" in source


def test_combo_box_styling_is_consistent_and_rounded():
    source = THEMES.read_text(encoding="utf-8")
    assert "QComboBox::drop-down" in source
    assert "border-radius: 9px" in source


def test_dutch_and_english_locale_have_new_settings_and_tooltip_keys():
    nl = json.loads((ROOT / "quietwriter" / "locales" / "nl.json").read_text(encoding="utf-8"))
    en = json.loads((ROOT / "quietwriter" / "locales" / "en.json").read_text(encoding="utf-8"))
    keys = [
        "settings.appearance.font_sample",
        "settings.storage.workspace_help",
        "settings.general.autosave_help",
        "format.quote.tip",
        "format.numbered.tip",
        "about.title",
    ]
    for key in keys:
        assert key in nl
        assert key in en
        assert nl[key]
        assert en[key]
