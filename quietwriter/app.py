from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSettings, QStandardPaths, QTimer
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from . import APP_NAME
from .crash_logging import enable_crash_logging, log_exception, set_error_notifier
from .font_catalog import register_bundled_fonts
from .icon_theme import app_icon_path
from .i18n import tr
from .runtime_profile import RuntimeProfile, parse_runtime_args, profile_for
from .startup import apply_saved_appearance, discover_startup_models, run_first_setup
from .smoke_test import SmokeTestContext
from .ui.crash_notice import CrashUiBridge, show_startup_error
from .ui.main_window import MainWindow
from .ui.splash import Splash
from .ui.workspace_recovery import open_library_with_recovery


def _set_windows_app_id(profile: RuntimeProfile) -> None:
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(profile.app_user_model_id)
    except Exception:
        pass


def run():
    smoke_test = '--smoke-test' in sys.argv
    argv = [arg for arg in sys.argv if arg != '--smoke-test']
    profile, force_first_run, qt_argv = parse_runtime_args(argv)
    if smoke_test:
        profile = profile_for('dev')
        force_first_run = False
    _set_windows_app_id(profile)
    app = QApplication(qt_argv)
    app.setApplicationName(profile.qt_application_name)
    app.setOrganizationName('QuietWriter')
    app.setFont(QFont('Segoe UI', 10))
    smoke = SmokeTestContext.create() if smoke_test else None
    if smoke is not None:
        settings = smoke.settings
        local_data = smoke.local_data
    else:
        settings = QSettings('QuietWriter', profile.settings_application)
        local_data = Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation) or (Path.home() / f'.quietwriter-{profile.key}'))
    log_path = enable_crash_logging(local_data / 'logs' / 'crash.log')
    crash_ui = CrashUiBridge(log_path)
    set_error_notifier(smoke.notify if smoke is not None else crash_ui.notify)
    apply_saved_appearance(app, settings)
    app.setWindowIcon(QIcon(str(app_icon_path())))
    splash = Splash(); splash.show()
    try:
        splash.set_status(tr('splash.fonts', 'Lettertypen laden…')); register_bundled_fonts()
        root = run_first_setup(app, settings, profile.default_workspace, splash, force=force_first_run)
        if root is None:
            return 0
        splash.set_status(tr('splash.workspace', 'Werkmap controleren…'))
        library = open_library_with_recovery(root, settings, splash)
        if library is None:
            splash.close(); return 1
        models = discover_startup_models(settings, splash)
        splash.set_status(tr('splash.interface', 'Interface opbouwen…'))
        win=MainWindow(settings,library,models)
        win._crash_ui_bridge = crash_ui
        splash.set_status(tr('splash.window', 'Venster voorbereiden…')); win.show(); splash.finish_when_ready(win)
        if not smoke_test and settings.value('auto_update_check', False, bool):
            QTimer.singleShot(1800, lambda: win.check_for_updates(silent=True))
        if smoke_test:
            QTimer.singleShot(1500, app.quit)
    except Exception as exc:
        log_exception(type(exc), exc, exc.__traceback__, label='Opstartfout', notify=False)
        splash.close(); QApplication.processEvents()
        details = f'{type(exc).__name__}: {exc}'
        if smoke is not None:
            return smoke.startup_failed(details)
        show_startup_error(log_path, details)
        return 1
    exit_code = app.exec()
    return smoke.final_exit_code(exit_code) if smoke is not None else exit_code
