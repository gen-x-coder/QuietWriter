from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox

from ..i18n import tr
from ..storage import Library


def open_library_with_recovery(root: Path, settings, splash):
    """Open the workspace with visible recovery for an unreachable path."""
    candidate = Path(root)
    original = candidate
    while True:
        try:
            library = Library(candidate)
        except OSError as exc:
            box = QMessageBox(splash)
            box.setIcon(QMessageBox.Critical)
            box.setWindowTitle(tr('startup.workspace_unavailable_title', 'Werkmap niet bereikbaar'))
            box.setText(tr(
                'startup.workspace_unavailable',
                'QuietWriter kan de werkmap niet openen:\n{path}',
                path=str(candidate),
            ))
            box.setInformativeText(str(exc))
            choose = box.addButton(
                tr('startup.choose_workspace', 'Andere map kiezen…'),
                QMessageBox.AcceptRole,
            )
            box.addButton(tr('startup.exit', 'Afsluiten'), QMessageBox.RejectRole)
            box.setDefaultButton(choose)
            box.exec()
            if box.clickedButton() is not choose:
                return None

            start = candidate if candidate.exists() else candidate.parent
            selected = QFileDialog.getExistingDirectory(
                splash,
                tr('startup.choose_workspace_title', 'Kies QuietWriter-werkmap'),
                str(start),
            )
            if not selected:
                return None
            candidate = Path(selected)
            splash.set_status(tr('splash.workspace', 'Werkmap controleren…'))
            continue

        if candidate != original:
            settings.setValue('workspace', str(candidate))
        return library
