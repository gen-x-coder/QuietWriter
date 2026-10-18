"""Overzicht van sneltoetsen (Ctrl+/ of F1).

Eén lijst, één venster tegelijk. Voeg hier een regel toe wanneer je ergens
een nieuwe sneltoets introduceert.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QGridLayout, QLabel, QVBoxLayout

from ..i18n import tr

# (toetsen, vertaalsleutel, Nederlandse standaardtekst)
SHORTCUTS: tuple[tuple[str, str, str], ...] = (
    ('Ctrl+S', 'shortcuts.save', 'Nu opslaan'),
    ('Ctrl+Z', 'shortcuts.undo', 'Ongedaan maken'),
    ('Ctrl+Y', 'shortcuts.redo', 'Opnieuw'),
    ('Ctrl+B', 'shortcuts.bold', 'Vet (bij een selectie)'),
    ('Ctrl+I', 'shortcuts.italic', 'Cursief (bij een selectie)'),
    ('Ctrl+U', 'shortcuts.underline', 'Onderstrepen (bij een selectie)'),
    ('Ctrl+Shift+S', 'shortcuts.strike', 'Doorhalen (bij een selectie)'),
    ('Ctrl+Shift+Enter', 'shortcuts.scene_break', 'Scènebreuk invoegen'),
    ('Ctrl+Alt+F', 'shortcuts.footnote_v2', 'Voetnoot invoegen; in de noot (of Enter): terug naar de tekst'),
    ('Ctrl+Shift+L', 'shortcuts.toggle_contents', 'Inhoud tonen of verbergen'),
    ('Ctrl+Shift+R', 'shortcuts.toggle_right', 'Rechterpaneel tonen of verbergen'),
    ('F5', 'shortcuts.refresh_shelf', 'Boekenkast vernieuwen'),
    ('Esc', 'shortcuts.close_panel', 'Paneel of venster sluiten'),
    ('Ctrl+/  ·  F1', 'shortcuts.this_overview', 'Dit overzicht'),
)


class ShortcutsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('shortcuts.title', 'Sneltoetsen'))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(6)
        for row, (keys, key, default) in enumerate(SHORTCUTS):
            keys_label = QLabel(keys)
            keys_label.setObjectName('shortcutKeys')
            keys_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            grid.addWidget(keys_label, row, 0, Qt.AlignLeft | Qt.AlignTop)
            text = QLabel(tr(key, default))
            text.setWordWrap(True)
            grid.addWidget(text, row, 1)
        layout.addLayout(grid)
        hint = QLabel(tr(
            'shortcuts.hint',
            'Werkt een sneltoets niet? Dan gebruikt een ander programma op je computer, zoals grafische of toetsenbordsoftware, die combinatie misschien al.',
        ))
        hint.setObjectName('muted')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        buttons = QDialogButtonBox()
        close = buttons.addButton(tr('common.close', 'Sluiten'), QDialogButtonBox.AcceptRole)
        close.clicked.connect(self.accept)
        layout.addWidget(buttons)
        self.setMinimumWidth(460)


def show_shortcuts(parent) -> ShortcutsDialog:
    """Toon het overzicht; een tweede aanroep brengt het bestaande venster naar voren."""
    existing = getattr(parent, '_shortcuts_dialog', None)
    if existing is not None and existing.isVisible():
        existing.raise_()
        existing.activateWindow()
        return existing
    dialog = ShortcutsDialog(parent)
    dialog.setAttribute(Qt.WA_DeleteOnClose, True)
    parent._shortcuts_dialog = dialog
    dialog.destroyed.connect(lambda *_: setattr(parent, '_shortcuts_dialog', None))
    dialog.show()
    return dialog
