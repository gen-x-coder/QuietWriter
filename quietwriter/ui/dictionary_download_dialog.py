"""Woordenboek downloaden (1.7): kiezen, downloaden, controleren, klaar."""
from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QProgressBar, QPushButton, QVBoxLayout,
)

from ..dictionary_download import CATALOG, DownloadCancelled, RollbackIncomplete, install, is_installed, update_available
from ..i18n import tr


def _size(num: int) -> str:
    return f'{num / 1_000_000:.1f} MB'.replace('.', ',')


class _Worker(QObject):
    progress = Signal(int)
    finished = Signal(str)        # locale
    failed = Signal(str)          # melding
    rollback_failed = Signal(str) # melding: het vorige woordenboek kwam niet helemaal terug
    cancelled = Signal()

    def __init__(self, entry, root: Path, installer=install):
        super().__init__()
        self.entry = entry
        self.root = root
        self.installer = installer
        self._cancel = threading.Event()
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run, name='quietwriter-dictionary', daemon=True)
        self.thread.start()

    def cancel(self):
        self._cancel.set()

    def _emit(self, signal, *args):
        try:
            signal.emit(*args)
        except RuntimeError:
            pass

    def _run(self):
        try:
            self.installer(self.entry, self.root, progress=lambda v: self._emit(self.progress, int(v)),
                           cancelled=self._cancel.is_set)
            self._emit(self.finished, self.entry.locale)
        except DownloadCancelled:
            self._emit(self.cancelled)
        except RollbackIncomplete as exc:
            self._emit(self.rollback_failed, str(exc))
        except Exception as exc:  # netwerk, schijf, controle: altijd netjes melden
            self._emit(self.failed, str(exc) or type(exc).__name__)


class DictionaryDownloadDialog(QDialog):
    def __init__(self, root: Path, parent=None, *, installer=install, preselect: str | None = None):
        super().__init__(parent)
        self.root = Path(root)
        self.installer = installer
        self.installed_locale: str | None = None
        self.worker: _Worker | None = None
        self.setWindowTitle(tr('dictionary_download.title', 'Woordenboek downloaden'))
        self.resize(560, 520)
        layout = QVBoxLayout(self); layout.setSpacing(10)
        intro = QLabel(tr('dictionary_download.intro', 'Kies een woordenboek. QuietWriter haalt het op bij de woordenboekbibliotheek van LibreOffice en controleert elk bestand voordat het wordt gebruikt. Er gaat niets van je tekst mee.'))
        intro.setWordWrap(True); intro.setObjectName('muted')
        layout.addWidget(intro)
        self.list = QListWidget(); self.list.setObjectName('dictionaryDownloadList')
        layout.addWidget(self.list, 1)
        self.progress = QProgressBar(); self.progress.setRange(0, 100); self.progress.hide()
        self.status = QLabel(''); self.status.setWordWrap(True)
        layout.addWidget(self.progress); layout.addWidget(self.status)
        buttons = QHBoxLayout()
        self.close_btn = QPushButton(tr('common.close', 'Sluiten')); self.close_btn.setObjectName('secondaryButton')
        self.cancel_btn = QPushButton(tr('common.cancel', 'Annuleren')); self.cancel_btn.setObjectName('secondaryButton'); self.cancel_btn.hide()
        self.download_btn = QPushButton(tr('dictionary_download.download', 'Downloaden')); self.download_btn.setObjectName('primaryButton')
        buttons.addWidget(self.close_btn); buttons.addStretch(1); buttons.addWidget(self.cancel_btn); buttons.addWidget(self.download_btn)
        layout.addLayout(buttons)
        self.close_btn.clicked.connect(self.reject)
        self.cancel_btn.clicked.connect(self._cancel)
        self.download_btn.clicked.connect(self.start_download)
        self.list.currentRowChanged.connect(self._selection_changed)
        self._fill(preselect)

    def _fill(self, select: str | None = None):
        self.list.clear()
        # 35 talen (dev14): op naam, in de taal van de app, zodat je ze vindt.
        self.entries = sorted(CATALOG, key=lambda e: e.label.casefold())
        self._updates = set()
        for entry in self.entries:
            done = is_installed(self.root, entry.locale)
            if done and update_available(self.root, entry):
                self._updates.add(entry.locale)
                state = tr('dictionary_download.update', '↻ nieuwere versie beschikbaar')
            elif done:
                state = tr('dictionary_download.installed', '✓ op deze computer')
            else:
                state = ''
            details = f'{entry.author} · {entry.license} · {_size(entry.size)}'
            item = QListWidgetItem(f'{entry.label}  {state}\n{details}'.rstrip())
            item.setData(Qt.UserRole, entry.locale)
            self.list.addItem(item)
        if select is None and self._updates:
            select = next(e.locale for e in self.entries if e.locale in self._updates)
        row = next((i for i, e in enumerate(self.entries) if e.locale == select), 0)
        self.list.setCurrentRow(row)

    def selected(self):
        row = self.list.currentRow()
        entries = getattr(self, 'entries', ())
        return entries[row] if 0 <= row < len(entries) else None

    def _selection_changed(self, *_):
        entry = self.selected()
        if entry is None:
            return
        if entry.locale in getattr(self, '_updates', set()):
            text = tr('dictionary_download.update_button', 'Bijwerken')
        elif is_installed(self.root, entry.locale):
            text = tr('dictionary_download.download_again', 'Opnieuw downloaden')
        else:
            text = tr('dictionary_download.download', 'Downloaden')
        self.download_btn.setText(text)

    def start_download(self):
        entry = self.selected()
        if entry is None or self.worker is not None:
            return
        self.worker = _Worker(entry, self.root, self.installer)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(self._finished)
        self.worker.failed.connect(self._failed)
        self.worker.rollback_failed.connect(self._rollback_failed)
        self.worker.cancelled.connect(self._cancelled)
        self._busy(True, tr('dictionary_download.busy', '{label} wordt gedownload en gecontroleerd…', label=entry.label))
        self.worker.start()

    def _busy(self, busy: bool, message: str = ''):
        self.progress.setVisible(busy); self.progress.setValue(0)
        self.cancel_btn.setVisible(busy)
        self.download_btn.setEnabled(not busy); self.list.setEnabled(not busy); self.close_btn.setEnabled(not busy)
        self.status.setText(message)

    def _cancel(self):
        if self.worker is not None:
            self.worker.cancel()

    def _finished(self, locale: str):
        self.worker = None
        self.installed_locale = locale
        self._busy(False, tr('dictionary_download.done', 'Klaar. Het woordenboek staat in je werkmap en is meteen te kiezen.'))
        self._fill(locale)

    def _failed(self, message: str):
        self.worker = None
        self._busy(False, tr('dictionary_download.failed', 'Downloaden is niet gelukt. Er is niets veranderd. Probeer het later opnieuw.\n\n{error}', error=message))

    def _rollback_failed(self, message: str):
        self.worker = None
        self._busy(False, tr('dictionary_download.rollback_failed',
                             'Downloaden is niet gelukt, en het vorige woordenboek kon niet helemaal worden teruggezet. Er staat een reservekopie in de woordenboekmap. Probeer het opnieuw te downloaden.\n\n{error}',
                             error=message))
        self._fill(self.selected().locale if self.selected() else None)

    def _cancelled(self):
        self.worker = None
        self._busy(False, tr('dictionary_download.cancelled', 'Gestopt. Er is niets veranderd.'))

    def reject(self):
        if self.worker is not None:
            self.worker.cancel()
            return
        super().reject()
