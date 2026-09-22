from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton

from ..i18n import tr


class SelectionToolbar(QFrame):
    """Compact theme-aware toolbar shown after a stable text selection."""

    actionRequested = Signal(str)

    ACTIONS = (
        ('paragraph', '¶', 'format.paragraph', 'Normale alinea'),
        ('heading', 'H₁', 'format.heading', 'Tussenkop'),
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
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus)
        self.setObjectName('selectionToolbar')
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(7, 7, 7, 7)
        lay.setSpacing(3)
        self.buttons = {}
        for action, label, key, default in self.ACTIONS:
            btn = QPushButton(label)
            btn.setObjectName('formatButton')
            btn.setToolTip(tr(key, default))
            btn.setFixedSize(44, 42)
            btn.setCheckable(True)
            btn.setFocusPolicy(Qt.NoFocus)
            font = QFont(btn.font())
            font.setPointSize(17 if action != 'code' else 13)
            if action == 'bold':
                font.setWeight(QFont.Weight.Bold)
            elif action == 'italic':
                font.setItalic(True)
            elif action == 'underline':
                font.setUnderline(True)
            elif action == 'strike':
                font.setStrikeOut(True)
            btn.setFont(font)
            btn.clicked.connect(lambda checked=False, a=action: self.actionRequested.emit(a))
            lay.addWidget(btn)
            self.buttons[action] = btn

    def set_states(self, states: dict[str, bool]):
        for action, button in self.buttons.items():
            button.setChecked(bool(states.get(action, False)))
