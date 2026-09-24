from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QWidget,
)

from ..i18n import tr


class ImageInsertWidget(QWidget):
    """Shared insert/edit flow for managed manuscript images.

    Insert mode only previews an external source file; the book media store copies
    it after the user confirms. Edit mode reuses the same UI and can either update
    alt/caption only or explicitly replace the immutable underlying asset.
    """

    insertRequested = Signal(str, str, str)
    editRequested = Signal(str, str, str, bool)
    cancelRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.source_path: Path | None = None
        self._preview_pixmap: QPixmap | None = None
        self._mode = 'insert'
        self._replacement_selected = False
        self._display_name = ''

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        self.title = QLabel()
        self.title.setObjectName('sectionTitle')
        self.description = QLabel()
        self.description.setObjectName('muted')
        self.description.setWordWrap(True)

        self.preview_frame = QFrame()
        self.preview_frame.setObjectName('settingsCard')
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        self.preview = QLabel()
        self.preview.setObjectName('muted')
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(150)
        self.preview.setMaximumHeight(220)
        preview_layout.addWidget(self.preview)

        self.file_label = QLabel('')
        self.file_label.setObjectName('muted')
        self.file_label.setWordWrap(True)
        self.choose_button = QPushButton()
        self.choose_button.setObjectName('secondaryButton')
        self.choose_button.clicked.connect(self.choose_file)

        alt_label = QLabel(tr('insert.image.alt', 'Alt-tekst'))
        self.alt_edit = QLineEdit()
        self.alt_edit.setPlaceholderText(tr(
            'insert.image.alt.placeholder',
            'Korte beschrijving voor toegankelijkheid'
        ))
        self.alt_edit.setToolTip(tr(
            'insert.image.alt.tip',
            'Beschrijf kort wat op de afbeelding te zien is. Deze tekst wordt ook in EPUB gebruikt.'
        ))

        caption_label = QLabel(tr('insert.image.caption', 'Onderschrift'))
        self.caption_edit = QLineEdit()
        self.caption_edit.setPlaceholderText(tr(
            'insert.image.caption.placeholder',
            'Optioneel onderschrift onder de afbeelding'
        ))

        buttons = QHBoxLayout()
        self.cancel_button = QPushButton(tr('common.cancel', 'Annuleren'))
        self.cancel_button.setObjectName('secondaryButton')
        self.primary_button = QPushButton()
        self.primary_button.setObjectName('primaryButton')
        self.primary_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancelRequested.emit)
        self.primary_button.clicked.connect(self._emit_primary)
        buttons.addWidget(self.cancel_button)
        buttons.addStretch(1)
        buttons.addWidget(self.primary_button)

        root.addWidget(self.title)
        root.addWidget(self.description)
        root.addWidget(self.preview_frame)
        root.addWidget(self.file_label)
        root.addWidget(self.choose_button)
        root.addSpacing(6)
        root.addWidget(alt_label)
        root.addWidget(self.alt_edit)
        root.addWidget(caption_label)
        root.addWidget(self.caption_edit)
        root.addStretch(1)
        root.addLayout(buttons)

        QWidget.setTabOrder(self.choose_button, self.alt_edit)
        QWidget.setTabOrder(self.alt_edit, self.caption_edit)
        QWidget.setTabOrder(self.caption_edit, self.cancel_button)
        QWidget.setTabOrder(self.cancel_button, self.primary_button)
        self.reset()

    def reset(self):
        self._mode = 'insert'
        self._replacement_selected = False
        self._display_name = ''
        self.source_path = None
        self._preview_pixmap = None
        self.preview.setPixmap(QPixmap())
        self.preview.setText(tr('insert.image.no_file', 'Nog geen afbeelding gekozen'))
        self.file_label.clear()
        self.alt_edit.clear()
        self.caption_edit.clear()
        self.title.setText(tr('insert.image.title', 'Afbeelding'))
        self.description.setText(tr(
            'insert.image.description',
            'Voeg een JPG- of PNG-afbeelding toe als eigen blok in het manuscript.'
        ))
        self.choose_button.setText(tr('insert.image.choose', 'Afbeelding kiezen…'))
        self.primary_button.setText(tr('insert.image.insert', 'Invoegen'))
        self.primary_button.setEnabled(False)
        self.choose_button.setFocus()

    def set_edit_mode(self, source_path: Path | None, alt: str, caption: str, display_name: str = ''):
        self._mode = 'edit'
        self._replacement_selected = False
        self._display_name = display_name or (Path(source_path).name if source_path else '')
        self.source_path = Path(source_path) if source_path else None
        self._preview_pixmap = None
        self.title.setText(tr('insert.image.edit_title', 'Afbeelding bewerken'))
        self.description.setText(tr(
            'insert.image.edit_description',
            'Pas de beschrijving of het onderschrift aan, of vervang de afbeelding.'
        ))
        self.choose_button.setText(tr('insert.image.replace', 'Afbeelding vervangen…'))
        self.primary_button.setText(tr('common.save', 'Opslaan'))
        self.alt_edit.setText(alt or '')
        self.caption_edit.setText(caption or '')
        self.primary_button.setEnabled(True)
        self._load_preview(self.source_path)
        self.file_label.setText(self._display_name)
        self.alt_edit.setFocus()

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr('insert.image.choose_title', 'Kies een afbeelding'),
            '',
            tr('insert.image.filter', 'Afbeeldingen (*.jpg *.jpeg *.png)')
        )
        if path:
            self.set_source(Path(path), replacement=(self._mode == 'edit'))

    def set_source(self, path: Path, *, replacement: bool = False):
        path = Path(path)
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            if self._mode == 'insert':
                self.source_path = None
                self._display_name = ''
                self.file_label.setText(path.name)
            else:
                # In edit mode the invalid candidate was never accepted; keep the
                # current file name/source visible so the UI cannot imply success.
                self.file_label.setText(self._display_name)
            self._preview_pixmap = None
            self.preview.setPixmap(QPixmap())
            self.preview.setText(tr('insert.image.invalid', 'Deze afbeelding kan niet worden gelezen.'))
            self.primary_button.setEnabled(self._mode == 'edit')
            return
        self.source_path = path
        self._preview_pixmap = pixmap
        self._display_name = path.name
        self._replacement_selected = bool(replacement)
        self.file_label.setText(path.name)
        self.primary_button.setEnabled(True)
        self._refresh_preview()
        self.alt_edit.setFocus()

    def _load_preview(self, path: Path | None):
        if path is None:
            self._preview_pixmap = None
            self.preview.setPixmap(QPixmap())
            self.preview.setText(tr('image_block.preview_unavailable', 'Preview niet beschikbaar'))
            return
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self._preview_pixmap = None
            self.preview.setPixmap(QPixmap())
            self.preview.setText(tr('image_block.preview_unavailable', 'Preview niet beschikbaar'))
            return
        self._preview_pixmap = pixmap
        self._refresh_preview()

    def _refresh_preview(self):
        if not self._preview_pixmap:
            return
        size = self.preview.size()
        if size.width() <= 0 or size.height() <= 0:
            return
        scaled = self._preview_pixmap.scaled(
            max(1, size.width() - 8), max(1, size.height() - 8),
            Qt.KeepAspectRatio, Qt.SmoothTransformation,
        )
        self.preview.setText('')
        self.preview.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_preview()

    def _emit_primary(self):
        alt = self.alt_edit.text().strip()
        caption = self.caption_edit.text().strip()
        if self._mode == 'edit':
            self.editRequested.emit(
                str(self.source_path or ''), alt, caption, self._replacement_selected
            )
            return
        if not self.source_path:
            return
        self.insertRequested.emit(str(self.source_path), alt, caption)
