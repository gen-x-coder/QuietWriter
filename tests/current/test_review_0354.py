from __future__ import annotations

from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[2]


def _load_combo_helper():
    path = ROOT / "quietwriter" / "ui" / "planning" / "combo_value.py"
    spec = importlib.util.spec_from_file_location("qw_combo_value_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.editable_combo_value


class FakeCombo:
    def __init__(self, items, index=0, text=None):
        self.items = items
        self.index = index
        self.text = items[index][0] if text is None and index >= 0 else (text or "")
    def currentText(self): return self.text
    def currentIndex(self): return self.index
    def itemText(self, i): return self.items[i][0]
    def itemData(self, i): return self.items[i][1]
    def findText(self, text):
        return next((i for i, (label, _data) in enumerate(self.items) if label == text), -1)


def test_editable_combo_keeps_selected_canonical_value():
    value = _load_combo_helper()
    c = FakeCombo([("idea", "idee"), ("written", "geschreven")], index=1)
    assert value(c, default="idee") == "geschreven"


def test_editable_combo_preserves_custom_existing_scene_status():
    value = _load_combo_helper()
    c = FakeCombo([("idee", "idee"), ("uitgewerkt", "uitgewerkt")], index=-1, text="in revisie")
    assert value(c, default="idee") == "in revisie"


def test_editable_combo_preserves_new_custom_text_after_previous_selection():
    value = _load_combo_helper()
    c = FakeCombo([("idee", "idee"), ("uitgewerkt", "uitgewerkt")], index=1, text="eerste versie")
    assert value(c, default="idee") == "eerste versie"


def test_editable_combo_maps_typed_translated_label_to_canonical_data():
    value = _load_combo_helper()
    c = FakeCombo([("idea", "idee"), ("written", "geschreven")], index=0, text="written")
    assert value(c, default="idee") == "geschreven"


def test_editable_combo_preserves_custom_relation_after_previous_selection():
    value = _load_combo_helper()
    c = FakeCombo([("parent of", "ouder van"), ("partner of", "partner van")], index=0, text="neighbor of")
    assert value(c, default="kent") == "neighbor of"


def test_custom_scene_load_clears_combo_index_before_edit_text():
    src = (ROOT / "quietwriter/ui/planning/outline_page.py").read_text(encoding="utf-8")
    assert "self.status.setCurrentIndex(-1)" in src
    assert "editable_combo_value(self.status, default='idee')" in src


def test_relation_uses_same_editable_combo_contract():
    src = (ROOT / "quietwriter/ui/planning/characters_page.py").read_text(encoding="utf-8")
    assert "editable_combo_value(self.rel_type, default='kent')" in src


def test_ci_filters_pyflakes_to_undefined_names():
    workflow = (ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
    checker = (ROOT / "tools/check_undefined_names.py").read_text(encoding="utf-8")
    assert "python tools/check_undefined_names.py" in workflow
    assert "messages.UndefinedName" in checker
    assert "python -m pyflakes quietwriter" not in workflow


def test_main_requires_python_312_before_importing_app():
    src = (ROOT / "main.py").read_text(encoding="utf-8")
    guard = src.index("_require_supported_python()")
    app_import = src.index("from quietwriter.app import run")
    assert guard < app_import
    assert "sys.version_info >= (3, 12)" in src
