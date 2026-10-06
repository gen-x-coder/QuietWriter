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

    def remove(self, key):
        self.values.pop(key, None)

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
    assert wizard.progress.text() == 'Step 2 of 9'

    wizard._commit()
    assert settings.values['language'] == 'en'
    assert settings.values['auto_update_check'] is False
    wizard.close()
    set_locale('nl')


def test_documentation_is_consolidated_and_licenses_are_separate():
    root = Path(__file__).resolve().parents[2]
    for name in (
        'PROJECT_GUIDE.md',
        'ARCHITECTURE_AND_DATA_SAFETY.md',
        'PRODUCT_AND_UI_PHILOSOPHY.md',
        'HISTORY_AND_LESSONS.md',
        'ROADMAP_AND_IDEAS.md',
        'TEST_STRATEGY.md',
        'RELEASE_BRANDING_AND_OPERATIONS.md',
        'CHANGELOG.md',
    ):
        assert (root / 'documents' / name).is_file()
    assert not (root / 'documents' / 'dev').exists()
    assert (root / 'documents' / 'licenses' / 'LICENSE').is_file()
    assert (root / 'documents' / 'licenses' / 'THIRD_PARTY_LICENSES.md').is_file()
