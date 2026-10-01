
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSettings, QStandardPaths
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from . import APP_NAME
from .crash_logging import enable_crash_logging, log_exception, set_error_notifier
from .icon_theme import app_icon_path, set_icon_theme
from .i18n import set_locale, tr
from .font_catalog import register_bundled_fonts
from .ollama import OllamaClient
from .storage import Library
from .themes import stylesheet
from .ui.main_window import MainWindow
from .ui.crash_notice import CrashUiBridge, show_startup_error
from .ui.splash import Splash
from .ui.workspace_recovery import open_library_with_recovery



def _set_windows_app_id() -> None:
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('LucasBonsel.QuietWriter')
    except Exception:
        # Branding must never make startup fail on unusual Windows shells.
        pass


def run():
    _set_windows_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName('QuietWriter')
    app_font = QFont('Segoe UI', 10)
    app.setFont(app_font)

    settings = QSettings('QuietWriter', 'QuietWriter')
    root = Path(settings.value('workspace', str(Path.home() / APP_NAME)))
    local_data = Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation) or (Path.home() / '.quietwriter'))
    log_path = enable_crash_logging(local_data / 'logs' / 'crash.log')
    crash_ui = CrashUiBridge(log_path)
    set_error_notifier(crash_ui.notify)
    set_locale(str(settings.value('language', 'nl') or 'nl'))
    set_icon_theme(str(settings.value('theme', 'Helder') or 'Helder'))
    app.setWindowIcon(QIcon(str(app_icon_path())))
    app.setStyleSheet(stylesheet(settings.value('theme', 'Helder')))

    splash = Splash()
    splash.show()

    try:
        splash.set_status(tr('splash.fonts', 'Lettertypen laden…'))
        register_bundled_fonts()

        splash.set_status(tr('splash.workspace', 'Werkmap controleren…'))
        library = open_library_with_recovery(root, settings, splash)
        if library is None:
            splash.close()
            return 1

        splash.set_status(tr('splash.ollama', 'Ollama controleren…'))
        client = OllamaClient(settings.value('ollama_url', 'http://127.0.0.1:11434'))
        try:
            models = client.model_info(timeout=1.8)
            model_names = [m['name'] for m in models]
            splash.set_status(tr('splash.ollama_found', 'Ollama gevonden · {count} modellen', count=len(models)))
            if model_names and not settings.value('ollama_model', ''):
                settings.setValue('ollama_model', model_names[0])
        except Exception:
            models = []
            splash.set_status(tr('splash.ollama_unavailable', 'Ollama niet bereikbaar · editor blijft beschikbaar'))

        splash.set_status(tr('splash.interface', 'Interface opbouwen…'))
        win=MainWindow(settings,library,models)
        win._crash_ui_bridge = crash_ui
        splash.set_status(tr('splash.window', 'Venster voorbereiden…'))
        win.show()
        splash.finish_when_ready(win)
    except Exception as exc:
        # Before app.exec() a non-modal crash notice cannot be relied upon. Log
        # the exception directly, remove the always-on-top splash and show one
        # modal diagnostic dialog with access to the local log.
        log_exception(type(exc), exc, exc.__traceback__, label='Opstartfout', notify=False)
        splash.close()
        QApplication.processEvents()
        show_startup_error(log_path, f'{type(exc).__name__}: {exc}')
        return 1

    return app.exec()
