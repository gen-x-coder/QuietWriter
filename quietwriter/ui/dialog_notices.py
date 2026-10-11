"""One-button notices with localized QuietWriter controls.

Do not use these wrappers for questions or other dialogs requiring a choice.
"""
from PySide6.QtWidgets import QMessageBox
from ..i18n import tr


def _notice(icon, parent, title, message):
    dialog = QMessageBox(parent)
    dialog.setIcon(icon)
    dialog.setWindowTitle(str(title))
    dialog.setText(str(message))
    dialog.addButton(tr('common.close', 'Sluiten'), QMessageBox.AcceptRole)
    return dialog.exec()


def notice_information(parent, title, message):
    return _notice(QMessageBox.Information, parent, title, message)


def notice_warning(parent, title, message):
    return _notice(QMessageBox.Warning, parent, title, message)


def notice_critical(parent, title, message):
    return _notice(QMessageBox.Critical, parent, title, message)
