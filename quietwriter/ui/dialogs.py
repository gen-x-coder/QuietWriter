from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QLineEdit, QMessageBox, QVBoxLayout
)
from ..i18n import tr


def confirm(parent, title: str, text: str, default_no: bool = True) -> bool:
    """Central Ja/Nee confirmation dialog using translated button labels."""
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Warning)
    box.setWindowTitle(title)
    box.setText(text)
    yes = box.addButton(tr('common.yes', 'Ja'), QMessageBox.YesRole)
    no = box.addButton(tr('common.no', 'Nee'), QMessageBox.NoRole)
    box.setDefaultButton(no if default_no else yes)
    box.exec()
    return box.clickedButton() is yes


def prompt_text(parent, title: str, label: str, text: str = '') -> tuple[str, bool]:
    """QuietWriter-owned single-line prompt with reliable translated buttons.

    QInputDialog builds parts of its native button box lazily on some Qt/Windows
    combinations. Renaming those buttons before ``exec()`` is therefore not
    reliable. Keeping this tiny dialog under our own control also makes every
    rename/create flow consistent with the rest of QuietWriter.
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(10)

    prompt = QLabel(label)
    edit = QLineEdit(text)
    edit.selectAll()
    layout.addWidget(prompt)
    layout.addWidget(edit)

    buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
    save = buttons.button(QDialogButtonBox.Save)
    cancel = buttons.button(QDialogButtonBox.Cancel)
    if save is not None:
        save.setText(tr('common.save', 'Opslaan'))
        save.setObjectName('primaryButton')
    if cancel is not None:
        cancel.setText(tr('common.cancel', 'Annuleren'))
        cancel.setObjectName('secondaryButton')
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    accepted = dialog.exec() == QDialog.Accepted
    return edit.text(), accepted
