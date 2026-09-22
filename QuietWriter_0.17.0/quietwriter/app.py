
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from . import APP_NAME
from .icon_theme import icon, set_icon_theme
from .font_catalog import register_bundled_fonts
from .ollama import OllamaClient
from .storage import Library
from .themes import stylesheet
from .ui.main_window import MainWindow
from .ui.splash import Splash

def run():
    app=QApplication(sys.argv); app.setApplicationName(APP_NAME); app.setOrganizationName('QuietWriter')
    # Use a fresh font with an explicit valid point size. On some Windows/Qt
    # combinations QFontDatabase.systemFont() can carry pointSize=-1; copying
    # that font into widgets later produces the Qt warning
    # 'QFont::setPointSize: Point size <= 0 (-1)'.
    app_font = QFont('Segoe UI', 10)
    app.setFont(app_font)
    # Register QuietWriter's bundled writing fonts for this process only. They
    # are deliberately not installed into Windows. Missing binaries are safe:
    # the typography layer simply falls back to available system fonts.
    register_bundled_fonts()
    settings=QSettings('QuietWriter','QuietWriter')
    set_icon_theme(str(settings.value('theme','Helder') or 'Helder'))
    app.setWindowIcon(icon('books'))
    app.setStyleSheet(stylesheet(settings.value('theme','Helder')))
    splash=Splash(); splash.show(); splash.set_status('Instellingen laden…')
    root=Path(settings.value('workspace', str(Path.home()/APP_NAME)))
    splash.set_status('Werkmap controleren…'); library=Library(root)
    splash.set_status('Ollama controleren…')
    client=OllamaClient(settings.value('ollama_url','http://127.0.0.1:11434'))
    try:
        infos=client.model_info(timeout=1.8); models=[m['name'] for m in infos]; splash.set_status(f'Ollama gevonden · {len(models)} modellen')
        if models and not settings.value('ollama_model',''):
            settings.setValue('ollama_model', models[0])
    except Exception:
        models=[]; splash.set_status('Ollama niet bereikbaar · editor blijft beschikbaar')
    QTimer.singleShot(450, splash.accept); splash.exec()
    win=MainWindow(settings,library,models); win.show(); return app.exec()
