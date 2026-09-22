
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QVBoxLayout, QWidget
)
from .dialogs import confirm

class TrashPage(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        root = QVBoxLayout(self); root.setContentsMargins(42, 34, 42, 34)
        top = QHBoxLayout()
        title = QLabel('Prullenbak'); title.setObjectName('title')
        self.restore_btn = QPushButton('Herstellen'); self.restore_btn.setObjectName('primaryButton'); self.restore_btn.clicked.connect(self.restore_selected)
        self.delete_btn = QPushButton('Selectie definitief verwijderen'); self.delete_btn.setObjectName('dangerButton'); self.delete_btn.clicked.connect(self.delete_selected)
        self.empty_btn = QPushButton('Prullenbak legen'); self.empty_btn.setObjectName('dangerButton'); self.empty_btn.clicked.connect(self.empty_trash)
        top.addWidget(title); top.addStretch(); top.addWidget(self.restore_btn); top.addWidget(self.delete_btn); top.addWidget(self.empty_btn)
        info = QLabel('Selecteer één of meer boeken. Definitief verwijderen kan niet ongedaan worden gemaakt.')
        info.setObjectName('muted')
        self.list = QListWidget(); self.list.setSelectionMode(QListWidget.ExtendedSelection)
        self.empty = QLabel('De prullenbak is leeg.'); self.empty.setObjectName('muted'); self.empty.setAlignment(Qt.AlignCenter)
        root.addLayout(top); root.addWidget(info); root.addSpacing(10); root.addWidget(self.empty); root.addWidget(self.list, 1)
        self.refresh()

    def refresh(self):
        rows = self.main.library.list_trashed_books()
        self.list.clear()
        for row in rows:
            dt = datetime.fromtimestamp(row['deleted']).strftime('%d-%m-%Y %H:%M')
            item = QListWidgetItem(f"{row['title']}   ·   verwijderd {dt}")
            item.setData(Qt.UserRole, str(row['path']))
            self.list.addItem(item)
        self.empty.setVisible(not rows); self.list.setVisible(bool(rows))
        self.restore_btn.setEnabled(bool(rows)); self.delete_btn.setEnabled(bool(rows)); self.empty_btn.setEnabled(bool(rows))

    def selected_paths(self):
        return [Path(i.data(Qt.UserRole)) for i in self.list.selectedItems()]

    def restore_selected(self):
        paths = self.selected_paths()
        if not paths:
            QMessageBox.information(self, 'Prullenbak', 'Selecteer eerst één of meer boeken.')
            return
        for p in paths:
            try: self.main.library.restore_trashed_book(p)
            except Exception as e: QMessageBox.warning(self, 'Herstellen', str(e))
        self.main.start.refresh(); self.refresh()

    def delete_selected(self):
        paths = self.selected_paths()
        if not paths:
            QMessageBox.information(self, 'Prullenbak', 'Selecteer eerst één of meer boeken.')
            return
        if not confirm(self, 'Definitief verwijderen', f'Wil je {len(paths)} geselecteerde item(s) definitief verwijderen?'):
            return
        for p in paths:
            self.main.library.permanently_delete_trashed_book(p)
        self.refresh()

    def empty_trash(self):
        if not confirm(self, 'Prullenbak legen', 'Wil je alle boeken in de prullenbak definitief verwijderen?'):
            return
        self.main.library.empty_trash(); self.refresh()
