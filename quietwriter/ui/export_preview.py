"""Exportvoorbeeld tonen (1.7): EPUB in een eigen leesvenster, de rest in het eigen programma."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QTextBrowser, QVBoxLayout

from ..exporting.preview import PreviewError, epub_preview_page
from ..i18n import tr
from .dialog_notices import notice_warning


class EpubPreviewDialog(QDialog):
    """Rustig leesvenster voor het EPUB-voorbeeld (geen modale vraag; gewoon sluiten)."""

    def __init__(self, epub_path: Path, parent=None):
        super().__init__(parent)
        self.epub_path = Path(epub_path)
        self.setWindowTitle(tr('export.preview.epub_title', 'Voorbeeld van je e-book'))
        self.resize(720, 820)
        layout = QVBoxLayout(self); layout.setContentsMargins(18, 16, 18, 16); layout.setSpacing(10)
        note = QLabel(tr('export.preview.epub_note',
                         'Zo ongeveer ziet je e-book eruit. Een e-reader past letter en bladspiegel aan; dit is alleen een voorbeeld, er is niets opgeslagen.'))
        note.setObjectName('muted'); note.setWordWrap(True)
        self.browser = QTextBrowser(); self.browser.setObjectName('epubPreview'); self.browser.setOpenExternalLinks(False)
        page = epub_preview_page(self.epub_path)
        self.browser.setSearchPaths([str(page.parent)])
        self.browser.setSource(QUrl.fromLocalFile(str(page)))
        buttons = QHBoxLayout()
        open_other = QPushButton(tr('export.preview.open_other', 'Openen in ander programma'))
        open_other.setObjectName('secondaryButton')
        open_other.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.epub_path))))
        close = QPushButton(tr('common.close', 'Sluiten')); close.setObjectName('primaryButton'); close.clicked.connect(self.close)
        buttons.addWidget(open_other); buttons.addStretch(1); buttons.addWidget(close)
        layout.addWidget(note); layout.addWidget(self.browser, 1); layout.addLayout(buttons)
        self.setAttribute(Qt.WA_DeleteOnClose, True)


def show_preview(parent, path: Path, format_name: str, opener=None):
    """Toon het voorbeeld. Geeft het EPUB-venster terug (zodat het blijft bestaan) of None."""
    path = Path(path)
    opener = opener or (lambda target: QDesktopServices.openUrl(QUrl.fromLocalFile(str(target))))
    if format_name == 'epub':
        try:
            dialog = EpubPreviewDialog(path, parent)
        except PreviewError as exc:
            # Te groot of onverwacht: dan in het eigen e-bookprogramma, als dat er is.
            notice_warning(parent, tr('export.preview.title', 'Voorbeeld'),
                           tr('export.preview.epub_failed', 'QuietWriter kan dit e-book hier niet tonen ({error}). Het wordt geopend in een ander programma, als dat er is.', error=exc))
        else:
            dialog.show()
            return dialog
    if not opener(path):
        notice_warning(parent, tr('export.preview.title', 'Voorbeeld'),
                       tr('export.preview.no_app', 'Er is geen programma gevonden om dit bestand te openen. Het voorbeeld staat hier:\n{path}', path=path))
    return None
