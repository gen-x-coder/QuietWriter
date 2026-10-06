from __future__ import annotations

from pathlib import Path
import time

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMessageBox

from ..i18n import tr


class CrashUiBridge(QObject):
    """Thread-safe bridge from exception hooks to one non-blocking Qt notice.

    Repeated failures must never turn into a storm of dialogs.  Every exception
    is still logged by ``crash_logging``; the UI only coalesces notifications.
    """

    error = Signal(str, str, str)
    _REPEAT_COOLDOWN_SECONDS = 60.0

    def __init__(self, log_path: Path, parent=None):
        super().__init__(parent)
        self.log_path = Path(log_path)
        self._box: QMessageBox | None = None
        self._summary = ''
        self._details = ''
        self._extra_count = 0
        self._last_closed_fingerprint: str | tuple[str, str] | None = None
        self._last_closed_at = 0.0
        self.error.connect(self._show_error)

    def notify(self, summary: str, details: str, fingerprint: str = '') -> None:
        self.error.emit(str(summary), str(details), str(fingerprint or ''))

    def _fingerprint(self, summary: str, details: str, fingerprint: str = ''):
        # crash_logging supplies exception type + final traceback location.
        # Fallback keeps direct/test calls compatible.
        return str(fingerprint) if fingerprint else (str(summary), str(details))

    def _informative_text(self) -> str:
        text = self._details
        if self._extra_count:
            suffix = tr(
                'crash.more_errors',
                'En nog {count} fouten. Zie het logbestand voor alle details.',
                count=self._extra_count,
            )
            text = f'{text}\n\n{suffix}' if text else suffix
        return text

    def _show_error(self, summary: str, details: str, source_fingerprint: str = '') -> None:
        fingerprint = self._fingerprint(summary, details, source_fingerprint)

        # While one notice is open, fold every new error into that same notice.
        if self._box is not None:
            self._extra_count += 1
            self._box.setInformativeText(self._informative_text())
            return

        # After dismissing a notice, do not immediately re-open it for the same
        # repeating failure.  Logging continues independently for every error.
        if (
            fingerprint == self._last_closed_fingerprint
            and (time.monotonic() - self._last_closed_at) < self._REPEAT_COOLDOWN_SECONDS
        ):
            return

        parent = QApplication.activeWindow()
        box = QMessageBox(parent)
        self._box = box
        self._summary = summary
        self._details = details
        self._extra_count = 0

        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(tr('crash.title', 'Onverwachte fout'))
        box.setText(tr(
            'crash.text',
            'Er ging iets mis. QuietWriter heeft de fout gelogd. Controleer voor de zekerheid je laatste wijziging.',
        ))
        if details:
            box.setInformativeText(details)
        open_button = box.addButton(tr('crash.open_log', 'Logbestand openen'), QMessageBox.ActionRole)
        box.addButton(tr('common.close', 'Sluiten'), QMessageBox.RejectRole)
        box.setModal(False)

        def clicked(button):
            if button is open_button:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.log_path)))

        def finished(_result):
            self._last_closed_fingerprint = fingerprint
            self._last_closed_at = time.monotonic()
            self._box = None
            box.deleteLater()

        box.buttonClicked.connect(clicked)
        box.finished.connect(finished)
        box.show()


def show_startup_error(log_path: Path, details: str = '') -> None:
    """Show a modal startup failure before the normal Qt event loop exists."""
    box = QMessageBox()
    box.setIcon(QMessageBox.Critical)
    box.setWindowTitle(tr('crash.startup_title', 'QuietWriter kon niet starten'))
    box.setText(tr(
        'crash.startup_text',
        'QuietWriter kon niet volledig worden gestart. De fout is opgeslagen in het logbestand.',
    ))
    if details:
        box.setInformativeText(details)
    open_button = box.addButton(tr('crash.open_log', 'Logbestand openen'), QMessageBox.ActionRole)
    box.addButton(tr('common.close', 'Sluiten'), QMessageBox.RejectRole)
    box.setModal(True)
    box.exec()
    if box.clickedButton() is open_button:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(log_path)))
