
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QVBoxLayout, QWidget
)
from .dialogs import confirm
from ..i18n import tr

class TrashPage(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        root = QVBoxLayout(self); root.setContentsMargins(42, 34, 42, 34)
        top = QHBoxLayout()
        title = QLabel(tr('trash.title', 'Prullenbak')); title.setObjectName('title')
        self.restore_btn = QPushButton(tr('trash.restore', 'Herstellen')); self.restore_btn.setObjectName('primaryButton'); self.restore_btn.clicked.connect(self.restore_selected)
        self.delete_btn = QPushButton(tr('trash.delete_selected', 'Selectie definitief verwijderen')); self.delete_btn.setObjectName('dangerButton'); self.delete_btn.clicked.connect(self.delete_selected)
        self.empty_btn = QPushButton(tr('trash.empty_button', 'Prullenbak legen')); self.empty_btn.setObjectName('dangerButton'); self.empty_btn.clicked.connect(self.empty_trash)
        top.addWidget(title); top.addStretch(); top.addWidget(self.restore_btn); top.addWidget(self.delete_btn); top.addWidget(self.empty_btn)
        info = QLabel(tr('trash.info', 'Selecteer één of meer boeken. Definitief verwijderen kan niet ongedaan worden gemaakt.'))
        info.setObjectName('muted')
        self.list = QListWidget(); self.list.setSelectionMode(QListWidget.ExtendedSelection)
        self.list.itemSelectionChanged.connect(self._update_actions)
        self.list.itemActivated.connect(lambda _item: self.restore_selected())
        self.empty = QLabel(tr('trash.empty', 'De prullenbak is leeg.')); self.empty.setObjectName('muted'); self.empty.setAlignment(Qt.AlignCenter)
        root.addLayout(top); root.addWidget(info); root.addSpacing(10); root.addWidget(self.empty); root.addWidget(self.list, 1)
        self.refresh()

    def refresh(self):
        rows = self.main.library.list_trashed_books()
        self.list.clear()
        for row in rows:
            dt = datetime.fromtimestamp(row['deleted']).strftime('%d-%m-%Y %H:%M')
            item = QListWidgetItem(tr('trash.row', '{title}   ·   verwijderd {date}', title=row['title'], date=dt))
            item.setData(Qt.UserRole, str(row['path']))
            self.list.addItem(item)
        self.empty.setVisible(not rows); self.list.setVisible(bool(rows))
        self.empty_btn.setEnabled(bool(rows)); self._update_actions()

    def _update_actions(self):
        has_selection = bool(self.list.selectedItems())
        self.restore_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def selected_paths(self):
        return [Path(i.data(Qt.UserRole)) for i in self.list.selectedItems()]

    def restore_selected(self):
        paths = self.selected_paths()
        if not paths:
            QMessageBox.information(self, tr('trash.title', 'Prullenbak'), tr('trash.select_first', 'Selecteer eerst één of meer boeken.'))
            return
        for p in paths:
            try: self.main.library.restore_trashed_book(p)
            except Exception as e: QMessageBox.warning(self, tr('trash.restore_error_title', 'Herstellen'), str(e))
        self.main.start.refresh(); self.refresh()

    def delete_selected(self):
        paths = self.selected_paths()
        if not paths:
            QMessageBox.information(self, tr('trash.title', 'Prullenbak'), tr('trash.select_first', 'Selecteer eerst één of meer boeken.'))
            return
        if not confirm(self, tr('trash.delete_title', 'Definitief verwijderen'), tr('trash.delete_confirm', 'Wil je {count} geselecteerde item(s) definitief verwijderen?', count=len(paths))):
            return
        for p in paths:
            self.main.library.permanently_delete_trashed_book(p)
        self.refresh()

    def empty_trash(self):
        if not confirm(self, tr('trash.empty_title', 'Prullenbak legen'), tr('trash.empty_confirm', 'Wil je alle boeken in de prullenbak definitief verwijderen?')):
            return
        self.main.library.empty_trash(); self.refresh()
