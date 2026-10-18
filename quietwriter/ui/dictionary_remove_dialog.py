"""Woordenboek verwijderen (1.7): kiezen uit wat QuietWriter zelf heeft, dan verwijderen.

Alleen woordenboeken in de werkmap van QuietWriter staan in de lijst: gedownload
of zelf toegevoegd. Woordenboeken van ONLYOFFICE, LibreOffice en OpenOffice zijn
nooit van QuietWriter en worden dus ook nooit aangeraakt.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout

from ..dictionary_catalog import DictionaryCatalog
from ..dictionary_download import installed_marker
from ..i18n import tr


class DictionaryRemoveDialog(QDialog):
    def __init__(self, root: Path, parent=None, *, preselect: str | None = None):
        super().__init__(parent)
        self.root = Path(root)
        self.removed: list[str] = []
        self.setWindowTitle(tr('dictionary_remove.title', 'Woordenboek verwijderen'))
        self.resize(520, 440)
        layout = QVBoxLayout(self); layout.setSpacing(10)
        intro = QLabel(tr('dictionary_remove.intro', 'Hier staan de woordenboeken die je in QuietWriter hebt gedownload of toegevoegd. Woordenboeken van ONLYOFFICE, LibreOffice en OpenOffice blijven altijd staan.'))
        intro.setWordWrap(True); intro.setObjectName('muted')
        layout.addWidget(intro)
        self.list = QListWidget(); self.list.setObjectName('dictionaryRemoveList')
        layout.addWidget(self.list, 1)
        self.empty = QLabel(tr('dictionary_remove.empty', 'Er staan geen woordenboeken in QuietWriter zelf. Er is hier dus niets te verwijderen.'))
        self.empty.setWordWrap(True); self.empty.setObjectName('muted')
        layout.addWidget(self.empty)
        self.status = QLabel(''); self.status.setWordWrap(True)
        layout.addWidget(self.status)
        buttons = QHBoxLayout()
        self.close_btn = QPushButton(tr('common.close', 'Sluiten')); self.close_btn.setObjectName('secondaryButton')
        self.remove_btn = QPushButton(tr('dictionary_remove.button', 'Verwijderen')); self.remove_btn.setObjectName('primaryButton')
        buttons.addWidget(self.close_btn); buttons.addStretch(1); buttons.addWidget(self.remove_btn)
        layout.addLayout(buttons)
        self.close_btn.clicked.connect(self.accept)
        self.remove_btn.clicked.connect(self.remove_selected)
        self._fill(preselect)

    def _catalog(self) -> DictionaryCatalog:
        # Alleen de werkmap: Office-mappen doen hier niet mee.
        return DictionaryCatalog(self.root, extra_roots=[], create=False)

    def entries(self):
        return [entry for entry in self._catalog().entries() if entry.source == 'Werkmap']

    def _fill(self, select: str | None = None):
        self.list.clear()
        entries = self.entries()
        for entry in entries:
            marker = installed_marker(self.root, entry.locale)
            if marker:
                origin = tr('dictionary_remove.downloaded', 'Gedownload · {author} · {license}',
                            author=marker.get('author', ''), license=marker.get('license', ''))
            else:
                origin = tr('dictionary_remove.added', 'Zelf toegevoegd')
            item = QListWidgetItem(f'{entry.label}\n{origin}')
            item.setData(Qt.UserRole, entry.locale)
            self.list.addItem(item)
        self.list.setVisible(bool(entries))
        self.empty.setVisible(not entries)
        self.remove_btn.setEnabled(bool(entries))
        row = next((i for i, e in enumerate(entries) if e.locale == select), 0)
        if entries:
            self.list.setCurrentRow(row)

    def selected_locale(self) -> str | None:
        item = self.list.currentItem()
        return str(item.data(Qt.UserRole)) if item is not None else None

    def remove_selected(self):
        locale = self.selected_locale()
        if not locale:
            return
        catalog = self._catalog()
        entry = catalog.get(locale, 'Werkmap')
        label = entry.label if entry else locale
        if catalog.remove_custom(locale):
            self.removed.append(locale)
            self.status.setText(tr('dictionary_remove.done', '{label} is verwijderd. Je kunt het altijd opnieuw downloaden of toevoegen.', label=label))
        else:
            self.status.setText(tr('settings.spelling.remove_failed', 'Het woordenboek kon niet worden verwijderd.'))
        self._fill()
