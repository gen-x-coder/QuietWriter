from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
)

from ..i18n import tr
from .current_page_stack import CurrentPageStack
from .image_insert_widget import ImageInsertWidget


class InsertPanel(QWidget):
    """Right-side insertion workflow for manuscript block elements."""

    sceneBreakRequested = Signal()
    imageInsertRequested = Signal(str, str, str)
    imageEditRequested = Signal(str, str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.stack = CurrentPageStack()
        root.addWidget(self.stack)

        self.menu_page = QWidget()
        layout = QVBoxLayout(self.menu_page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel(tr('insert.title', 'Toevoegen'))
        title.setObjectName('sectionTitle')
        description = QLabel(tr(
            'insert.description',
            'Voeg een element toe op de huidige positie in het manuscript.'
        ))
        description.setObjectName('muted')
        description.setWordWrap(True)

        scene_card = self._choice_card(
            tr('insert.scene_break', 'Scènebreuk'),
            tr('insert.scene_break.description', 'Markeer een duidelijke overgang tussen twee scènes.'),
        )
        self.scene_break_button = QPushButton(tr('insert.add', 'Toevoegen'))
        self.scene_break_button.setObjectName('secondaryButton')
        self.scene_break_button.setToolTip(tr('insert.scene_break.tip', 'Voeg een scènebreuk toe op de cursorpositie'))
        self.scene_break_button.clicked.connect(self.sceneBreakRequested.emit)
        scene_card.layout().addWidget(self.scene_break_button)

        image_card = self._choice_card(
            tr('insert.image.title', 'Afbeelding'),
            tr('insert.image.card_description', 'Plaats een JPG- of PNG-afbeelding tussen twee alinea’s.'),
        )
        self.image_button = QPushButton(tr('insert.add', 'Toevoegen'))
        self.image_button.setObjectName('secondaryButton')
        self.image_button.setToolTip(tr('insert.image.tip', 'Voeg een afbeelding toe op de cursorpositie'))
        self.image_button.clicked.connect(self.show_image_page)
        image_card.layout().addWidget(self.image_button)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addSpacing(4)
        layout.addWidget(scene_card)
        layout.addWidget(image_card)
        layout.addStretch(1)

        self.image_page = ImageInsertWidget()
        self.image_page.cancelRequested.connect(self.show_menu_page)
        self.image_page.insertRequested.connect(self.imageInsertRequested.emit)
        self.image_page.editRequested.connect(self.imageEditRequested.emit)

        self.stack.addWidget(self.menu_page)
        self.stack.addWidget(self.image_page)
        self.stack.setCurrentWidget(self.menu_page)

    @staticmethod
    def _choice_card(title_text: str, description_text: str) -> QFrame:
        card = QFrame()
        card.setObjectName('insertChoiceCard')
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 10, 10)
        card_layout.setSpacing(10)
        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(3)
        title = QLabel(title_text)
        title.setObjectName('sectionTitle')
        description = QLabel(description_text)
        description.setObjectName('muted')
        description.setWordWrap(True)
        text_col.addWidget(title)
        text_col.addWidget(description)
        card_layout.addLayout(text_col, 1)
        return card

    def show_image_page(self):
        self.image_page.reset()
        self.stack.setCurrentWidget(self.image_page)

    def show_image_edit_page(self, source_path, alt: str, caption: str, display_name: str = ''):
        self.image_page.set_edit_mode(source_path, alt, caption, display_name)
        self.stack.setCurrentWidget(self.image_page)

    def show_menu_page(self):
        self.stack.setCurrentWidget(self.menu_page)
        self.scene_break_button.setFocus()

    def reset(self):
        self.image_page.reset()
        self.stack.setCurrentWidget(self.menu_page)
