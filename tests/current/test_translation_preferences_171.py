"""1.7.1: translation screen choices persist without a separate save action."""
import os

import pytest


@pytest.mark.qt
def test_translation_screen_remembers_choices_across_reopening(tmp_path):
    pytest.importorskip('PySide6')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication
    from quietwriter import i18n
    from quietwriter.ui.translations_page import TranslationsPage

    app = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.IniFormat)
    i18n.set_user_translation_dir(tmp_path / 'translations')
    (tmp_path / 'translations').mkdir()
    try:
        first = TranslationsPage(settings)
        first.target.setCurrentIndex(first.target.findData('de'))
        first.reference.setCurrentIndex(first.reference.findData('fr'))
        first.sort_choice.setCurrentIndex(first.sort_choice.findData('incomplete'))
        first.only_missing.setChecked(True)
        settings.sync()
        assert settings.value('translations/target') == 'de'
        assert settings.value('translations/reference') == 'fr'
        assert settings.value('translations/sort') == 'incomplete'
        assert settings.value('translations/only_missing', False, bool)
        first.deleteLater()
        second = TranslationsPage(settings)
        assert second.target.currentData() == 'de'
        assert second.reference.currentData() == 'fr'
        assert second.sort_choice.currentData() == 'incomplete'
        assert second.only_missing.isChecked()
    finally:
        i18n.set_user_translation_dir(None)
    assert app is not None
