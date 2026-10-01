from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_brand_assets_are_packaged():
    app_icon = ROOT / 'quietwriter' / 'resources' / 'quietwriter.ico'
    assert app_icon.is_file()
    assert app_icon.suffix == '.ico'
    icons = ROOT / 'quietwriter' / 'icons'
    assert (icons / 'quietwriter.svg').is_file()
    assert (icons / 'quietwriter-small.svg').is_file()
    assert (icons / 'quietwriter-wordmark.svg').is_file()


def test_app_uses_local_per_machine_log_and_windows_app_id():
    source = (ROOT / 'quietwriter' / 'app.py').read_text(encoding='utf-8')
    assert 'QStandardPaths.AppLocalDataLocation' in source
    assert "local_data / 'logs' / 'crash.log'" in source
    assert "SetCurrentProcessExplicitAppUserModelID('LucasBonsel.QuietWriter')" in source
    assert 'QIcon(str(app_icon_path()))' in source


def test_crash_logger_covers_python_threads_and_qt_messages():
    source = (ROOT / 'quietwriter' / 'crash_logging.py').read_text(encoding='utf-8')
    assert 'faulthandler.enable(_LOG_HANDLE, all_threads=True)' in source
    assert 'sys.excepthook = exception_hook' in source
    assert 'threading.excepthook = thread_exception_hook' in source
    assert 'qInstallMessageHandler' in source
    assert 'log_exception(exc_type, exc_value, exc_tb)' in source


def test_splash_and_about_use_wordmark():
    splash = (ROOT / 'quietwriter' / 'ui' / 'splash.py').read_text(encoding='utf-8')
    about = (ROOT / 'quietwriter' / 'ui' / 'about_page.py').read_text(encoding='utf-8')
    assert "themed_svg_pixmap('quietwriter-wordmark', 300)" in splash
    assert "themed_svg_pixmap('quietwriter-wordmark', 360" in about
    assert "colour_key='hero_text'" in about


@pytest.fixture
def app():
    QtWidgets = pytest.importorskip('PySide6.QtWidgets')
    instance = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield instance


def test_crash_notice_is_non_modal_and_offers_log_button(app, tmp_path):
    from quietwriter.ui.crash_notice import CrashUiBridge

    bridge = CrashUiBridge(tmp_path / 'crash.log')
    bridge.notify('Testfout', 'detailregel')
    app.processEvents()
    assert bridge._box is not None
    box = bridge._box
    assert not box.isModal()
    assert 'detailregel' in box.informativeText()
    texts = [button.text() for button in box.buttons()]
    assert any('Logbestand' in text or 'log file' in text.lower() for text in texts)
    box.close()
    app.processEvents()
