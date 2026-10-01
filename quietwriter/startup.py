from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication, QDialog

from .first_run import should_show_first_run
from .i18n import set_locale, tr
from .icon_theme import set_icon_theme
from .ollama import OllamaClient
from .themes import stylesheet
from .ui.first_run_wizard import FirstRunWizard


def apply_saved_appearance(app: QApplication, settings) -> None:
    set_locale(str(settings.value('language', 'nl') or 'nl'))
    set_icon_theme(str(settings.value('theme', 'Helder') or 'Helder'))
    app.setStyleSheet(stylesheet(settings.value('theme', 'Helder')))


def run_first_setup(app: QApplication, settings, default_root: Path, splash, *, force: bool = False) -> Path | None:
    if not should_show_first_run(settings, default_root, force=force):
        return Path(settings.value('workspace', str(default_root)))
    splash.hide()
    wizard = FirstRunWizard(settings, default_root)
    if wizard.exec() != QDialog.DialogCode.Accepted:
        splash.close()
        return None
    apply_saved_appearance(app, settings)
    splash.show()
    return Path(settings.value('workspace', str(default_root)))


def discover_startup_models(settings, splash) -> list[dict]:
    if not settings.value('ai_enabled', True, bool):
        splash.set_status(tr('splash.ai_skipped', 'AI staat uit · editor wordt gestart'))
        return []
    provider = str(settings.value('ai_provider', 'ollama') or 'ollama').lower()
    if provider != 'ollama':
        splash.set_status(tr('splash.ai_skipped', 'AI staat uit · editor wordt gestart'))
        return []
    splash.set_status(tr('splash.ollama', 'Ollama controleren…'))
    client = OllamaClient(settings.value('ollama_url', 'http://127.0.0.1:11434'))
    try:
        models = client.model_info(timeout=1.8)
        model_names = [m['name'] for m in models]
        splash.set_status(tr('splash.ollama_found', 'Ollama gevonden · {count} modellen', count=len(models)))
        if model_names and not settings.value('ollama_model', ''):
            settings.setValue('ollama_model', model_names[0])
        return models
    except Exception:
        splash.set_status(tr('splash.ollama_unavailable', 'Ollama niet bereikbaar · editor blijft beschikbaar'))
        return []
