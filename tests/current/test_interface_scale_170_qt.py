"""1.7.0: Interfacegrootte (de hele interface groter of kleiner, na herstart)."""
import os

import pytest
pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from quietwriter.interface_scale import SCALES, SETTING_KEY, apply_interface_scale, normalize_scale


class _Settings(dict):
    def value(self, key, default=None):
        return self.get(key, default)


@pytest.mark.parametrize('raw, expected', [
    (100, 100), ('125', 125), ('150%', 150), (120, 125), (112, 110), (300, 175), (60, 80), (10, 100), (400, 100),
    ('', 100), (None, 100), ('groot', 100), (0, 100), (-5, 100), (1.25, 100),
])
def test_normalize_scale(raw, expected):
    assert normalize_scale(raw) == expected


def test_scale_sets_qt_scale_factor_only_when_needed():
    env = {}
    assert apply_interface_scale(_Settings({SETTING_KEY: 125}), env) == 1.25
    assert env == {'QT_SCALE_FACTOR': '1.25'}
    env = {}
    assert apply_interface_scale(_Settings(), env) is None
    assert env == {}
    env = {}
    assert apply_interface_scale(_Settings({SETTING_KEY: 90}), env) == 0.9
    assert env['QT_SCALE_FACTOR'] == '0.9'


def test_users_own_environment_wins():
    env = {'QT_SCALE_FACTOR': '2'}
    assert apply_interface_scale(_Settings({SETTING_KEY: 80}), env) is None
    assert env == {'QT_SCALE_FACTOR': '2'}


def test_broken_settings_never_block_startup():
    class Broken:
        def value(self, *args):
            raise RuntimeError('register onleesbaar')
    env = {}
    assert apply_interface_scale(Broken(), env) is None and env == {}


def test_settings_page_saves_scale_and_says_restart(tmp_path):
    app = QApplication.instance() or QApplication([])
    from quietwriter.storage import Library
    from quietwriter.ui.main_window import MainWindow
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.IniFormat)
    settings.setValue('workspace', str(tmp_path / 'workspace'))
    window = MainWindow(settings, Library(tmp_path / 'workspace'), [])
    try:
        page = window.settings_page
        page.begin_session()
        assert [page.interface_scale.itemData(i) for i in range(page.interface_scale.count())] == list(SCALES)
        assert page.interface_scale.currentData() == 100
        page.interface_scale.setCurrentIndex(page.interface_scale.findData(125))
        assert page._current_form_state() != page._saved_form_state
        page.save_settings()
        assert int(settings.value(SETTING_KEY)) == 125
        assert 'herstart' in page.save_feedback.text()
        settings.setValue(SETTING_KEY, 'onzin')
        page.begin_session()
        assert page.interface_scale.currentData() == 100
    finally:
        window.close()
