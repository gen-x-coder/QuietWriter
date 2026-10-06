from pathlib import Path

import pytest

pytest.importorskip('PySide6')

from quietwriter.update_checker import is_newer_version
from quietwriter.themes import stylesheet


def test_local_version_can_be_ahead_of_latest_stable():
    assert is_newer_version('1.0.13', '1.0.0') is True
    assert is_newer_version('1.0.0', '1.0.13') is False


def test_radio_indicators_have_explicit_contrast_in_all_themes():
    from quietwriter.themes import THEMES
    for name in THEMES:
        css = stylesheet(name)
        assert 'QRadioButton::indicator' in css
        assert 'border: 2px solid' in css
        assert 'QRadioButton::indicator:checked' in css


def test_first_run_counter_shrinks_when_tour_is_disabled(tmp_path: Path):
    pytest.importorskip('PySide6')
    from PySide6.QtWidgets import QApplication
    from quietwriter.ui.first_run_wizard import FirstRunWizard

    class Settings:
        def __init__(self): self.values = {'language': 'nl'}
        def value(self, key, default=None, type=None):
            value = self.values.get(key, default)
            return bool(value) if type is bool else value
        def setValue(self, key, value): self.values[key] = value
        def remove(self, key): self.values.pop(key, None)
        def sync(self): pass

    app = QApplication.instance() or QApplication([])
    wizard = FirstRunWizard(Settings(), tmp_path / 'QuietWriter')
    try:
        wizard.tour_enabled.setChecked(False)
        wizard.pages.setCurrentIndex(wizard.tour_choice_index)
        wizard._update_nav()
        assert wizard.progress.text() == 'Stap 6 van 6'
    finally:
        wizard.close()
