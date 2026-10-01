from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_about_wordmark_uses_hero_text_colour():
    source = (ROOT / 'quietwriter' / 'ui' / 'about_page.py').read_text(encoding='utf-8')
    assert "colour_key='hero_text'" in source


def test_first_run_contract_does_not_use_workspace_as_sole_trigger():
    text = (ROOT / 'FIRST_RUN_DESIGN_035.md').read_text(encoding='utf-8')
    assert '`first_run_done`' in text
    assert 'workspace` is **geen** betrouwbare first-run-indicator' in text
    assert 'bestaande gebruiker' in text.lower()


def test_ci_installs_linux_qt_runtime_dependencies():
    text = (ROOT / '.github' / 'workflows' / 'tests.yml').read_text(encoding='utf-8')
    for package in ('libegl1', 'libgl1', 'libxkbcommon0', 'libfontconfig1', 'libdbus-1-3'):
        assert package in text


def test_crash_logging_keeps_qt_messages_on_stderr_without_previous_handler():
    source = (ROOT / 'quietwriter' / 'crash_logging.py').read_text(encoding='utf-8')
    assert 'sys.__stderr__.write' in source
    assert 'def log_exception(' in source


def test_app_has_modal_startup_failure_path():
    source = (ROOT / 'quietwriter' / 'app.py').read_text(encoding='utf-8')
    assert 'show_startup_error' in source
    assert "label='Opstartfout'" in source
    assert 'notify=False' in source
    assert 'splash.close()' in source


def test_branding_renderer_is_hidpi_aware():
    source = (ROOT / 'quietwriter' / 'icon_theme.py').read_text(encoding='utf-8')
    assert 'devicePixelRatio' in source
    assert 'setDevicePixelRatio' in source
    assert 'for dpr in (1.0, 2.0)' in source


@pytest.fixture
def app():
    QtWidgets = pytest.importorskip('PySide6.QtWidgets')
    instance = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield instance


def test_repeating_crashes_are_coalesced_into_one_notice(app, tmp_path):
    from quietwriter.ui.crash_notice import CrashUiBridge

    bridge = CrashUiBridge(tmp_path / 'crash.log')
    for _ in range(50):
        bridge.notify('Timerfout', 'RuntimeError: boom')
    app.processEvents()

    assert bridge._box is not None
    assert bridge._extra_count == 49
    assert '49' in bridge._box.informativeText()
    open_boxes = [w for w in app.topLevelWidgets() if w.__class__.__name__ == 'QMessageBox' and w.isVisible()]
    assert len(open_boxes) == 1

    bridge._box.close()
    app.processEvents()


def test_same_crash_is_suppressed_for_cooldown_after_close(app, tmp_path):
    from quietwriter.ui.crash_notice import CrashUiBridge

    bridge = CrashUiBridge(tmp_path / 'crash.log')
    bridge.notify('Timerfout', 'RuntimeError: boom')
    app.processEvents()
    assert bridge._box is not None
    bridge._box.close()
    app.processEvents()
    assert bridge._box is None

    bridge.notify('Timerfout', 'RuntimeError: boom')
    app.processEvents()
    assert bridge._box is None
