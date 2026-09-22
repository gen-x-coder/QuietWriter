from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton

from ..i18n import tr


class SelectionToolbar(QFrame):
    """Compact theme-aware toolbar shown after a stable text selection."""

    actionRequested = Signal(str)

    ACTIONS = (
        ('paragraph', '¶', 'format.paragraph', 'Normale alinea'),
        ('heading', 'H', 'format.heading', 'Tussenkop'),
        ('bullet', '•', 'format.bullet', 'Opsomming'),
        ('numbered', '1.', 'format.numbered', 'Genummerde lijst'),
        ('quote', '❝', 'format.quote', 'Citaat'),
        ('code', '</>', 'format.code', 'Code'),
        ('bold', 'B', 'format.bold', 'Vet'),
        ('italic', 'I', 'format.italic', 'Cursief'),
        ('underline', 'U', 'format.underline', 'Onderstrepen'),
        ('strike', 'S', 'format.strike', 'Doorhalen'),
    )

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setObjectName('selectionToolbar')
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(2)
        self.buttons = {}
        for action, label, key, default in self.ACTIONS:
            btn = QPushButton(label)
            btn.setObjectName('formatButton')
            btn.setToolTip(tr(key, default))
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda checked=False, a=action: self.actionRequested.emit(a))
            lay.addWidget(btn)
            self.buttons[action] = btn
