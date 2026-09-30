from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMessageBox

from ..i18n import tr


class CrashUiBridge(QObject):
    """Thread-safe bridge from exception hooks to one non-blocking Qt notice."""

    error = Signal(str, str)

    def __init__(self, log_path: Path, parent=None):
        super().__init__(parent)
        self.log_path = Path(log_path)
        self._boxes: list[QMessageBox] = []
        self.error.connect(self._show_error)

    def notify(self, summary: str, details: str) -> None:
        self.error.emit(str(summary), str(details))

    def _show_error(self, summary: str, details: str) -> None:
        parent = QApplication.activeWindow()
        box = QMessageBox(parent)
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
        self._boxes.append(box)

        def clicked(button):
            if button is open_button:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.log_path)))

        def finished(_result):
            try:
                self._boxes.remove(box)
            except ValueError:
                pass
            box.deleteLater()

        box.buttonClicked.connect(clicked)
        box.finished.connect(finished)
        box.show()
