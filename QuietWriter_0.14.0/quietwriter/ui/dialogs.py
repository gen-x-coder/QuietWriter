from PySide6.QtWidgets import QMessageBox
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
