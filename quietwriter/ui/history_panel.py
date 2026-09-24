
from datetime import datetime

from PySide6.QtCore import QDate, QLocale, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget
)

from ..i18n import current_locale, tr

class HistoryPanel(QWidget):
    versionSelected = Signal(str)
    currentSelected = Signal()
    createRequested = Signal()
    starChanged = Signal(str, bool)

    def __init__(self, editor_page):
        super().__init__()
        self.editor_page = editor_page
        self.book = None
        self.rows = []
        lay = QVBoxLayout(self); lay.setContentsMargins(18,18,18,18); lay.setSpacing(10)
        title = QLabel(tr('history.title', 'Versiegeschiedenis')); title.setObjectName('sectionTitle')
        self.starred_only = QCheckBox(tr('history.starred_only', 'Alleen versies met ster'))
        self.starred_only.stateChanged.connect(self.refresh)
        self.create_btn = QPushButton(tr('history.create', '+ Nieuwe versie maken')); self.create_btn.setObjectName('primaryButton')
        self.create_btn.clicked.connect(self.createRequested.emit)
        self.list = QListWidget()
        self.list.itemClicked.connect(self._clicked)
        self.list.itemActivated.connect(self._clicked)
        self.list.currentItemChanged.connect(self._selection_changed)
        self.star_btn = QPushButton(tr('history.star_add', '☆ Ster toevoegen')); self.star_btn.setObjectName('secondaryButton')
        self.star_btn.clicked.connect(self._toggle_star)
        self.star_btn.setEnabled(False)
        self.empty = QLabel(tr('history.empty', 'Nog geen oudere versies beschikbaar.'))
        self.empty.setObjectName('muted'); self.empty.setAlignment(Qt.AlignCenter); self.empty.setWordWrap(True)
        lay.addWidget(title); lay.addWidget(self.starred_only); lay.addWidget(self.create_btn)
        lay.addWidget(self.empty); lay.addWidget(self.list, 1); lay.addWidget(self.star_btn)

    def set_book(self, book):
        self.book = book
        self.refresh()

    @staticmethod
    def _format_stamp(value: str) -> tuple[str, str]:
        try:
            dt = datetime.fromisoformat(value)
        except Exception:
            dt = datetime.now()
        locale = QLocale('en_US' if current_locale() == 'en' else 'nl_NL')
        date_label = locale.toString(QDate(dt.year, dt.month, dt.day), 'd MMMM yyyy')
        return date_label, dt.strftime('%H:%M')

    def refresh(self, *_):
        self.list.clear(); self.rows = []
        if not self.book:
            self.empty.show(); self.star_btn.setEnabled(False); return
        try:
            rows = self.editor_page.main.library.list_versions(self.book)
        except Exception:
            rows = []
        if self.starred_only.isChecked():
            rows = [r for r in rows if r.get('starred')]
        self.rows = rows
        self.empty.setVisible(not rows)
        # The live manuscript is always available as a first item.
        current = QListWidgetItem(tr('history.current', 'Huidige versie'))
        current.setData(Qt.UserRole, None)
        current.setToolTip(tr('history.current_tip', 'Terug naar de huidige, bewerkbare versie'))
        self.list.addItem(current)
        last_group = None
        today_label = self._format_stamp(datetime.now().isoformat())[0]
        number_locale = QLocale('en_US' if current_locale() == 'en' else 'nl_NL')
        for row in rows:
            date_label, time_label = self._format_stamp(row['created_at'])
            group = tr('history.today', 'Vandaag') if date_label == today_label else date_label
            if group != last_group:
                header = QListWidgetItem(group.upper())
                header.setFlags(Qt.NoItemFlags)
                header.setData(Qt.UserRole, '__header__')
                self.list.addItem(header); last_group = group
            star = '★' if row.get('starred') else '☆'
            kind_key = {
                'daily':'history.kind.daily', 'manual':'history.kind.manual',
                'pre_restore':'history.kind.pre_restore', 'chapter_delete':'history.kind.chapter_delete',
                'conflict_external':'history.kind.conflict_external', 'conflict_local':'history.kind.conflict_local',
            }.get(row.get('kind'), 'history.kind.version')
            kind = tr(kind_key, 'Versie')
            chapters = number_locale.toString(int(row.get('chapters', 0)))
            words = number_locale.toString(int(row.get('words', 0)))
            stats = tr('history.stats', '{chapters} hoofdstukken · {words} woorden', chapters=chapters, words=words)
            text = f'{star}  {time_label}  ·  {kind}\n{stats}'
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, row['id'])
            item.setData(Qt.UserRole + 1, bool(row.get('starred')))
            self.list.addItem(item)
        self.star_btn.setEnabled(False)

    def select_version(self, version_id: str | None):
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item.data(Qt.UserRole) == version_id:
                self.list.setCurrentItem(item); return

    def _clicked(self, item):
        data = item.data(Qt.UserRole)
        if data == '__header__': return
        if data is None:
            self.currentSelected.emit()
        elif data:
            self.versionSelected.emit(str(data))

    def _selection_changed(self, current, previous):
        if not current:
            self.star_btn.setEnabled(False); return
        data = current.data(Qt.UserRole)
        if not data or data == '__header__':
            self.star_btn.setEnabled(False); return
        starred = bool(current.data(Qt.UserRole + 1))
        self.star_btn.setEnabled(True)
        self.star_btn.setText(tr('history.star_remove', '★ Ster verwijderen') if starred else tr('history.star_add', '☆ Ster toevoegen'))

    def _toggle_star(self):
        item = self.list.currentItem()
        if not item: return
        version_id = item.data(Qt.UserRole)
        if not version_id or version_id == '__header__': return
        starred = not bool(item.data(Qt.UserRole + 1))
        self.starChanged.emit(str(version_id), starred)
