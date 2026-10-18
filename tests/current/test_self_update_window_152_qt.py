"""Echt hoofdvenster + echte threads, nep-Velopack: controleert dat signalen uit
de daemonthread in de UI-thread aankomen en dat bijwerken pas na normaal
afsluiten wordt toegepast."""
import os
import tempfile
import time
from pathlib import Path

import pytest
pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from quietwriter.self_update import SelfUpdater
from quietwriter.storage import Library
from quietwriter.ui.main_window import MainWindow
from .test_self_update_151 import FakeInfo, FakeManager

pytestmark = pytest.mark.qt


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _wait(app, condition, timeout=5.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        app.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    return False


def _window(root):
    settings = QSettings(str(root / 'settings.ini'), QSettings.IniFormat)
    return MainWindow(settings, Library(root / 'workspace'), [])


def test_manual_check_without_newer_package_asks_github_for_the_stable_version(app):
    with tempfile.TemporaryDirectory() as td:
        window = _window(Path(td))
        try:
            window._self_updater_instance = SelfUpdater(manager_factory=lambda: FakeManager(None))
            asked = []
            window._update_checker.check = lambda: asked.append(True)
            window.check_for_updates(silent=False)
            assert _wait(app, lambda: asked and window._update_op is None)
            assert window._update_check_silent is False
        finally:
            window.search_index.close(); window.close(); app.processEvents()


def test_silent_check_without_velopack_update_asks_github_silently(app):
    # 1.6.1: een release zonder releases.win.json (bijwerken nog dicht) moet
    # bij het opstarten toch gemeld worden; zonder nieuwe versie blijft het stil.
    with tempfile.TemporaryDirectory() as td:
        window = _window(Path(td))
        try:
            window._self_updater_instance = SelfUpdater(manager_factory=lambda: FakeManager(None))
            asked = []
            window._update_checker.check = lambda: asked.append(True)
            window.check_for_updates(silent=True)
            assert _wait(app, lambda: asked and window._update_op is None)
            assert window._update_check_silent is True
        finally:
            window.search_index.close(); window.close(); app.processEvents()


def test_download_then_normal_close_then_apply_then_quit(app):
    with tempfile.TemporaryDirectory() as td:
        window = _window(Path(td))
        manager = FakeManager(FakeInfo('1.5.9'))
        window._self_updater_instance = SelfUpdater(manager_factory=lambda: manager)
        quits = []
        window._quit_application = lambda: quits.append(True)
        try:
            update = window._self_updater().check()
            window._download_self_update(update)
            assert _wait(app, lambda: quits)
            assert 'download' in manager.calls
            assert manager.calls[-1] == ('apply', False, True, None)
            assert not window.isVisible()
        finally:
            window.search_index.close(); app.processEvents()
