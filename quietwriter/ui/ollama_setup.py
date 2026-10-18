"""Ollama instellen vanuit Instellingen → AI Meelezer (1.7).

Eén rustig blok met drie toestanden:

* niet gevonden → korte uitleg, **Ollama downloaden** (officiële pagina) en **Opnieuw zoeken**;
* draait zonder model → een korte lijst modellen, het passende voorgeselecteerd, en **Model downloaden**;
* klaar → één regel, plus **Ander model downloaden…** voor wie meer wil.

Kijken en downloaden gebeuren in een thread; de interface blijft bruikbaar.
Er wordt niets in de instellingen geschreven: na een download haalt de
instellingenpagina de modellen opnieuw op en kiest het nieuwe model als concept,
dat pas met Opslaan bewaard wordt.
"""
from __future__ import annotations

import threading

from PySide6.QtCore import QLocale, QObject, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from ..ai import ollama_setup as core
from ..i18n import current_locale, tr
from .form_controls import QuietComboBox


class _Bridge(QObject):
    checked = Signal(int, str, list)
    progress = Signal(object, str)
    pulled = Signal(str, str)   # naam, foutmelding ('' = gelukt, 'stopped' = gestopt)


def level_text(level: str) -> str:
    return {
        'light': tr('ollama_setup.level.light', 'licht, voor de meeste laptops (8 GB werkgeheugen)'),
        'medium': tr('ollama_setup.level.medium', 'gemiddeld (16 GB werkgeheugen)'),
        'strong': tr('ollama_setup.level.strong', 'sterk (32 GB werkgeheugen of een flinke videokaart)'),
    }[level]


class _WrapLabel(QLabel):
    """Afbrekend label dat zijn hoogte zelf vasthoudt (het instellingenraster doet dat niet betrouwbaar)."""
    def __init__(self, text=''):
        super().__init__(text)
        self.setWordWrap(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    def _sync(self):
        needed = self.heightForWidth(max(1, self.width()))
        if needed > 0:
            self.setMinimumHeight(needed)

    def setText(self, text):
        super().setText(text)
        self._sync()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync()


class OllamaSetupBox(QWidget):
    def __init__(self, url_getter, on_model_ready=None, parent=None, *, ram_gb='auto',
                 checker=None, puller=None):
        super().__init__(parent)
        self.setObjectName('ollamaSetupBox')
        self._url_getter = url_getter
        self._on_model_ready = on_model_ready
        self._checker = checker or core.check_ollama
        self._puller = puller or core.pull_model
        self._ram = core.total_ram_gb() if ram_gb == 'auto' else ram_gb
        self._stop = threading.Event()
        self._busy = False
        self._chooser_open = False
        self._check_id = 0
        self.state = ''
        self.models: list[str] = []

        self._bridge = _Bridge(self)
        self._bridge.checked.connect(self._checked)
        self._bridge.progress.connect(self._progress)
        self._bridge.pulled.connect(self._pulled)

        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(8)
        self.setMinimumWidth(660)
        self.status = _WrapLabel('')
        self.status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(self.status)

        row = QHBoxLayout(); row.setSpacing(8)
        self.download_ollama = QPushButton(tr('ollama_setup.download_ollama', 'Ollama downloaden'))
        self.download_ollama.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(core.OLLAMA_DOWNLOAD_URL)))
        self.retry = QPushButton(tr('ollama_setup.retry', 'Opnieuw zoeken'))
        self.retry.setObjectName('secondaryButton'); self.retry.clicked.connect(self.refresh)
        self.more = QPushButton(tr('ollama_setup.more', 'Ander model downloaden…'))
        self.more.setObjectName('secondaryButton'); self.more.clicked.connect(self._show_chooser)
        for button in (self.download_ollama, self.retry, self.more):
            row.addWidget(button)
        row.addStretch(1)
        lay.addLayout(row)

        self.chooser = QWidget(); cl = QVBoxLayout(self.chooser); cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(6)
        pick = QHBoxLayout(); pick.setSpacing(8)
        self.model_choice = QuietComboBox()
        suggested = core.suggested_model(self._ram)
        locale = QLocale(current_locale())   # 7,6 in het Nederlands, 7.6 in het Engels
        for model in core.RECOMMENDED_MODELS:
            text = tr('ollama_setup.model_item', '{name} — {level} · ongeveer {size} GB',
                      name=model.name, level=level_text(model.level), size=locale.toString(model.size_gb, 'f', 1))
            if model == suggested:
                text += ' · ' + tr('ollama_setup.suggested', 'past bij deze computer')
            self.model_choice.addItem(text, model.name)
        self.model_choice.setCurrentIndex(self.model_choice.findData(suggested.name))
        self.pull_button = QPushButton(tr('ollama_setup.pull', 'Model downloaden'))
        self.pull_button.clicked.connect(self.start_pull)
        self.stop_button = QPushButton(tr('ollama_setup.stop', 'Stoppen'))
        self.stop_button.setObjectName('secondaryButton'); self.stop_button.clicked.connect(self._stop.set)
        pick.addWidget(self.model_choice, 1); pick.addWidget(self.pull_button); pick.addWidget(self.stop_button)
        cl.addLayout(pick)
        self.progress = QProgressBar(); self.progress.setRange(0, 1000); self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        cl.addWidget(self.progress)
        lay.addWidget(self.chooser)
        self.pull_status = _WrapLabel(''); self.pull_status.setObjectName('settingsFieldHelp')
        lay.addWidget(self.pull_status)

        self._apply('checking')

    # ---- toestand -------------------------------------------------------
    def _apply(self, state: str):
        self.state = state
        url = self._url_getter()
        texts = {
            'checking': tr('ollama_setup.checking', 'Zoeken naar Ollama…'),
            core.MISSING: tr('ollama_setup.missing',
                             'Ollama is niet gevonden op {url}. Ollama is een gratis programma dat AI-modellen op je eigen computer draait. Installeer het, start het en klik dan op Opnieuw zoeken.',
                             url=url),
            core.NO_MODELS: tr('ollama_setup.no_models',
                               'Ollama draait, maar heeft nog geen model. Kies er hieronder één; het passende staat al klaar. Het downloaden kan even duren.'),
            core.READY: tr('ollama_setup.ready', 'Ollama draait, met {count} model(len).', count=len(self.models)),
        }
        self.status.setText(texts[state])
        self.download_ollama.setVisible(state == core.MISSING)
        self.retry.setVisible(not self._busy)
        self.retry.setEnabled(state != 'checking')
        show_chooser = state == core.NO_MODELS or (state == core.READY and (self._chooser_open or self._busy))
        self.more.setVisible(state == core.READY and not show_chooser)
        self.chooser.setVisible(show_chooser)
        self.pull_status.setVisible(bool(self.pull_status.text()))
        self._update_pull_controls()

    def _update_pull_controls(self):
        self.pull_button.setVisible(not self._busy)
        self.model_choice.setEnabled(not self._busy)
        self.stop_button.setVisible(self._busy)
        self.progress.setVisible(self._busy)

    def _show_chooser(self):
        self._chooser_open = True
        self.pull_status.clear()
        self._apply(self.state)

    # ---- zoeken ---------------------------------------------------------
    def refresh(self):
        if self._busy:
            return
        # Alleen het antwoord op de laatste vraag telt (review dev19): een trage
        # oudere controle mag de status van een nieuwere niet overschrijven.
        self._check_id += 1
        request = self._check_id
        self._apply('checking')
        url = self._url_getter()
        checker, bridge = self._checker, self._bridge

        def work():
            try:
                state, models = checker(url)
            except Exception:
                state, models = core.MISSING, []
            try:
                bridge.checked.emit(request, state, list(models))
            except RuntimeError:
                pass   # venster al gesloten
        threading.Thread(target=work, daemon=True).start()

    def _checked(self, request: int, state: str, models: list):
        if request != self._check_id or self._busy:
            return
        self.models = list(models)
        self._apply(state)

    # ---- downloaden -----------------------------------------------------
    def start_pull(self):
        name = str(self.model_choice.currentData() or '')
        if not name or self._busy:
            return
        self._busy = True
        self._stop.clear()
        self.progress.setValue(0)
        self.pull_status.setText(tr('ollama_setup.pull_starting', '{name} downloaden…', name=name))
        self._apply(self.state)
        url = self._url_getter()

        def work():
            try:
                self._puller(url, name, on_progress=lambda f, s: self._bridge.progress.emit(f, s),
                             should_stop=self._stop.is_set)
            except core.PullCancelled:
                result = 'stopped'
            except Exception as exc:  # netwerk, onbekende naam, schijf vol …
                result = str(exc) or exc.__class__.__name__
            else:
                result = ''
            try:
                self._bridge.pulled.emit(name, result)
            except RuntimeError:
                pass   # venster al gesloten
        threading.Thread(target=work, daemon=True).start()

    def _progress(self, fraction, status: str):
        if fraction is None:
            self.progress.setRange(0, 0)   # bezig, zonder percentage
        else:
            self.progress.setRange(0, 1000); self.progress.setValue(int(fraction * 1000))
            self.pull_status.setText(tr('ollama_setup.pull_percent', 'Downloaden: {percent}%', percent=int(fraction * 100)))

    def _pulled(self, name: str, error: str):
        self._busy = False
        self.progress.setRange(0, 1000)
        if error == 'stopped':
            self.pull_status.setText(tr('ollama_setup.pull_stopped',
                                        'Gestopt. Wat al binnen is bewaart Ollama; opnieuw downloaden gaat verder waar het was.'))
            self._apply(self.state)
            return
        if error:
            self.pull_status.setText(tr('ollama_setup.pull_failed', 'Downloaden lukte niet: {error}', error=error))
            self._apply(self.state)
            return
        self.pull_status.setText(tr('ollama_setup.pull_done', '{name} is klaar en staat hierboven als model gekozen. Klik op Opslaan om het te bewaren.', name=name))
        if name not in self.models:
            self.models.append(name)
        self._chooser_open = False
        self._apply(core.READY)
        if self._on_model_ready:
            self._on_model_ready(name)

    def stop(self):
        """Bij sluiten: een lopende download netjes laten stoppen."""
        self._stop.set()
