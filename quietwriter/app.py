
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from . import APP_NAME
from .crash_logging import enable_crash_logging
from .icon_theme import icon, set_icon_theme
from .i18n import set_locale, tr
from .font_catalog import register_bundled_fonts
from .ollama import OllamaClient
from .storage import Library
from .themes import stylesheet
from .ui.main_window import MainWindow
from .ui.splash import Splash
from .ui.workspace_recovery import open_library_with_recovery



def run():
    app=QApplication(sys.argv); app.setApplicationName(APP_NAME); app.setOrganizationName('QuietWriter')
    # Use a fresh font with an explicit valid point size. On some Windows/Qt
    # combinations QFontDatabase.systemFont() can carry pointSize=-1; copying
    # that font into widgets later produces the Qt warning
    # 'QFont::setPointSize: Point size <= 0 (-1)'.
    app_font = QFont('Segoe UI', 10)
    app.setFont(app_font)

    settings=QSettings('QuietWriter','QuietWriter')
    root=Path(settings.value('workspace', str(Path.home()/APP_NAME)))
    enable_crash_logging(root / 'logs' / 'crash.log')
    set_locale(str(settings.value('language', 'nl') or 'nl'))
    set_icon_theme(str(settings.value('theme','Helder') or 'Helder'))
    app.setWindowIcon(icon('books'))
    app.setStyleSheet(stylesheet(settings.value('theme','Helder')))

    # Keep the splash alive throughout real startup work.  There is deliberately
    # no artificial timeout: it closes only after MainWindow is exposed.
    splash=Splash()
    splash.show()
    splash.set_status(tr('splash.fonts', 'Lettertypen laden…'))

    # Register QuietWriter's bundled writing fonts for this process only. They
    # are deliberately not installed into Windows. Missing binaries are safe:
    # the typography layer simply falls back to available system fonts.
    register_bundled_fonts()

    splash.set_status(tr('splash.workspace', 'Werkmap controleren…'))
    library = open_library_with_recovery(root, settings, splash)
    if library is None:
        splash.close()
        return 1

    splash.set_status(tr('splash.ollama', 'Ollama controleren…'))
    client=OllamaClient(settings.value('ollama_url','http://127.0.0.1:11434'))
    try:
        infos=client.model_info(timeout=1.8)
        models=[m['name'] for m in infos]
        splash.set_status(tr('splash.ollama_found', 'Ollama gevonden · {count} modellen', count=len(models)))
        if models and not settings.value('ollama_model',''):
            settings.setValue('ollama_model', models[0])
    except Exception:
        models=[]
        splash.set_status(tr('splash.ollama_unavailable', 'Ollama niet bereikbaar · editor blijft beschikbaar'))

    splash.set_status(tr('splash.interface', 'Interface opbouwen…'))
    win=MainWindow(settings,library,models)
    splash.set_status(tr('splash.window', 'Venster voorbereiden…'))
    win.show()
    splash.finish_when_ready(win)
    return app.exec()
