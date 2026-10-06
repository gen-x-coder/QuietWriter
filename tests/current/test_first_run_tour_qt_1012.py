from __future__ import annotations

from pathlib import Path

import pytest


class FakeSettings:
    def __init__(self, values=None):
        self.values = dict(values or {})
    def value(self, key, default=None, type=None):
        value = self.values.get(key, default)
        return bool(value) if type is bool else value
    def setValue(self, key, value):
        self.values[key] = value
    def remove(self, key):
        self.values.pop(key, None)
    def sync(self):
        pass


def test_first_run_can_skip_optional_tour_and_persists_update_choice(tmp_path: Path):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    from quietwriter.ui.first_run_wizard import FirstRunWizard

    app = QApplication.instance() or QApplication([])
    settings = FakeSettings({"language": "nl", "first_run_requested": True})
    wizard = FirstRunWizard(settings, tmp_path / "QuietWriter")
    wizard.auto_update_check.setChecked(True)
    wizard.tour_enabled.setChecked(False)
    wizard.pages.setCurrentIndex(wizard.tour_choice_index)
    assert wizard.next_btn.text() == "Voltooien"
    wizard._next()
    assert settings.values["auto_update_check"] is True
    assert settings.values["first_run_done"] is True
    assert "first_run_requested" not in settings.values
    wizard.close()
