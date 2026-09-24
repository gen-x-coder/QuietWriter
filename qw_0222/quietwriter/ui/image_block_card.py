from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QToolButton, QVBoxLayout

from ..i18n import tr


class ImageBlockCard(QFrame):
    """Visual, non-editable representation of one managed Markdown image block.

    The Markdown source remains in QTextDocument.  This widget only shields that
    implementation detail from writers and exposes explicit edit/delete actions.
    Clicking the card itself merely selects the block; it never opens an editor.
    """

    selected = Signal(int)
    editRequested = Signal(int)
    deleteRequested = Signal(int)

    def __init__(self, block_number: int, parent=None):
        super().__init__(parent)
        self.block_number = block_number
        self._is_selected = False
        self._editable = True
        self._theme_key = None
        self.setObjectName('imageBlockCard')
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.ArrowCursor)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 10, 10, 10)
        root.setSpacing(12)

        self.preview = QLabel()
        self.preview.setObjectName('imageBlockPreview')
        self.preview.setFixedSize(136, 96)
        self.preview.setAlignment(Qt.AlignCenter)
        root.addWidget(self.preview)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(4)
        self.alt_label = QLabel()
        self.alt_label.setObjectName('imageBlockAlt')
        self.alt_label.setWordWrap(True)
        self.caption_label = QLabel()
        self.caption_label.setObjectName('imageBlockCaption')
        self.caption_label.setWordWrap(True)
        self.missing_label = QLabel()
        self.missing_label.setObjectName('imageBlockMissing')
        self.missing_label.setWordWrap(True)
        text_col.addWidget(self.alt_label)
        text_col.addWidget(self.caption_label)
        text_col.addWidget(self.missing_label)
        text_col.addStretch(1)
        root.addLayout(text_col, 1)

        actions = QVBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(4)
        self.edit_button = QToolButton()
        self.edit_button.setText(tr('image_block.edit', 'Bewerken'))
        self.edit_button.setCursor(Qt.PointingHandCursor)
        self.edit_button.setToolTip(tr('image_block.edit_tip', 'Alt-tekst, onderschrift of afbeelding wijzigen'))
        self.delete_button = QToolButton()
        self.delete_button.setText(tr('image_block.delete', 'Verwijderen'))
        self.delete_button.setCursor(Qt.PointingHandCursor)
        self.delete_button.setToolTip(tr('image_block.delete_tip', 'Afbeelding uit het manuscript verwijderen'))
        self.edit_button.clicked.connect(lambda: self.editRequested.emit(self.block_number))
        self.delete_button.clicked.connect(lambda: self.deleteRequested.emit(self.block_number))
        actions.addWidget(self.edit_button)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)
        root.addLayout(actions)

    def set_theme(self, theme: dict):
        key = (theme.get('panel'), theme.get('panel2'), theme.get('border'), theme.get('focus'),
               theme.get('text'), theme.get('muted'), theme.get('warning'), theme.get('hover'),
               theme.get('accent_soft'), self._is_selected)
        if key == self._theme_key:
            return
        self._theme_key = key
        border = theme['focus'] if self._is_selected else theme['border']
        background = theme['panel2'] if self._is_selected else theme['panel']
        self.setStyleSheet(f'''
            QFrame#imageBlockCard {{
                background: {background};
                border: {2 if self._is_selected else 1}px solid {border};
                border-radius: 9px;
            }}
            QLabel#imageBlockPreview {{
                background: {theme['panel2']};
                border: 1px solid {theme['border']};
                border-radius: 6px;
                color: {theme['muted']};
            }}
            QLabel#imageBlockAlt {{ color: {theme['text']}; font-weight: 600; }}
            QLabel#imageBlockCaption {{ color: {theme['muted']}; }}
            QLabel#imageBlockMissing {{ color: {theme['warning']}; font-size: 11px; }}
            QToolButton {{
                color: {theme['text']};
                border: 0;
                border-radius: 5px;
                padding: 5px 8px;
            }}
            QToolButton:hover {{ background: {theme['hover']}; }}
            QToolButton:pressed {{ background: {theme['accent_soft']}; }}
            QToolButton:disabled {{ color: {theme['muted']}; }}
        ''')

    def set_selected(self, selected: bool, theme: dict):
        if self._is_selected == bool(selected):
            return
        self._is_selected = bool(selected)
        self._theme_key = None
        self.set_theme(theme)

    def set_editable(self, editable: bool):
        self._editable = bool(editable)
        self.edit_button.setVisible(self._editable)
        self.delete_button.setVisible(self._editable)

    def set_data(self, ref, asset_path: Path | None):
        self.alt_label.setText(ref.alt.strip() or tr('image_block.image', 'Afbeelding'))
        self.caption_label.setText(ref.caption.strip() or tr('image_block.no_caption', 'Geen onderschrift'))
        pixmap = QPixmap(str(asset_path)) if asset_path and Path(asset_path).is_file() else QPixmap()
        if pixmap.isNull():
            self.preview.setPixmap(QPixmap())
            self.preview.setText(tr('image_block.image', 'Afbeelding'))
            self.missing_label.setText(
                tr('image_block.preview_unavailable', 'Preview niet beschikbaar')
                if asset_path else tr('image_block.asset_missing', 'Afbeeldingsbestand niet beschikbaar')
            )
            return
        self.preview.setText('')
        self.preview.setPixmap(pixmap.scaled(
            self.preview.size() - QSize(8, 8),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        ))
        self.missing_label.clear()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Deliberately *not* edit-on-click. A card click only selects the
            # media block. Editing is explicit via the button or Enter.
            self.selected.emit(self.block_number)
            event.accept()
            return
        super().mousePressEvent(event)
