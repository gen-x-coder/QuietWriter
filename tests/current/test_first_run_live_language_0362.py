from __future__ import annotations

from pathlib import Path

import pytest


class FakeSettings:
    def __init__(self, values=None):
        self.values = dict(values or {})

    def value(self, key, default=None, type=None):
        value = self.values.get(key, default)
        if type is bool:
            return bool(value)
        return value

    def setValue(self, key, value):
        self.values[key] = value

    def sync(self):
        pass


def test_first_run_language_switch_retranslates_open_wizard(tmp_path: Path):
    pytest.importorskip('PySide6')
    from PySide6.QtWidgets import QApplication

    from quietwriter.i18n import current_locale, set_locale
    from quietwriter.ui.first_run_wizard import FirstRunWizard

    app = QApplication.instance() or QApplication([])
    assert app is not None
    set_locale('nl')
    settings = FakeSettings({'language': 'nl'})
    wizard = FirstRunWizard(settings, tmp_path / 'QuietWriter')

    assert wizard.windowTitle() == 'Welkom bij QuietWriter'
    assert wizard.next_btn.text() == 'Volgende'

    wizard.language.setCurrentIndex(wizard.language.findData('en'))

    assert current_locale() == 'en'
    assert wizard.windowTitle() == 'Welcome to QuietWriter'
    assert wizard.next_btn.text() == 'Next'
    assert wizard.back_btn.text() == 'Back'
    assert wizard.skip_btn.text() == 'Skip'

    wizard.pages.setCurrentIndex(1)
    assert wizard.progress.text() == 'Step 2 of 4'

    wizard._commit()
    assert settings.values['language'] == 'en'
    wizard.close()
    set_locale('nl')


def test_documentation_is_split_between_user_dev_and_licenses():
    root = Path(__file__).resolve().parents[2]
    assert (root / 'documents' / 'CHANGELOG.md').is_file()
    assert (root / 'documents' / 'ROADMAP.md').is_file()
    assert (root / 'documents' / 'dev' / 'PLAN_1_0.md').is_file()
    assert (root / 'documents' / 'dev' / 'FIRST_RUN_DESIGN_035.md').is_file()
    assert (root / 'documents' / 'licenses' / 'LICENSE').is_file()
    assert (root / 'documents' / 'licenses' / 'THIRD_PARTY_LICENSES.md').is_file()
    assert not (root / 'PLAN_1_0.md').exists()
    assert not (root / 'FIRST_RUN_DESIGN_035.md').exists()
    assert not (root / 'CHANGELOG.md').exists()
