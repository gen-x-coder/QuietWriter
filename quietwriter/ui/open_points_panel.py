from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from ..i18n import tr
from ..placeholders import parse_open_points
from ..open_points_storage import OpenPointStore
from .panel_help import PanelHelp


class OpenPointsPanel(QWidget):
    """Book-level overview of persistent open points in manuscript chapters."""

    openPointRequested = Signal(str, str)
    addRequested = Signal()

    def __init__(self, library, settings=None):
        super().__init__()
        self.library = library
        self.store = OpenPointStore(library)
        self.book = None

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        self.panel_help = PanelHelp(
            settings, 'open_points', tr('open_points.panel_title', 'Open punten'),
            tr('panel_help.open_points', 'Markeer woorden of passages die je later nog wilt aanvullen, in plaats van XXX of TODO te typen. QuietWriter houdt ze hier bij en waarschuwt je vóór een export. De markering zelf komt nooit in je export terecht.')
        )
        root.addWidget(self.panel_help)

        self.summary = QLabel('')
        self.summary.setObjectName('muted')
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)

        self.list = QListWidget()
        self.list.setObjectName('openPointsList')
        self.list.setAlternatingRowColors(False)
        self.list.itemActivated.connect(self._activate)
        self.list.itemDoubleClicked.connect(self._activate)
        root.addWidget(self.list, 1)

        self.add_button = QPushButton(tr('open_points.add', 'Open punt toevoegen'))
        self.add_button.setObjectName('secondaryButton')
        self.add_button.clicked.connect(self.addRequested.emit)
        root.addWidget(self.add_button)

    def refresh(self, book, *, current_chapter_id: str | None = None, current_source: str | None = None) -> None:
        same_book = (self.book is not None and book is not None
                     and getattr(self.book, 'id', None) == getattr(book, 'id', None))
        self.book = book

        selected_key = None
        current_item = self.list.currentItem()
        if current_item is not None:
            data = current_item.data(Qt.UserRole)
            if data and len(data) == 2:
                selected_key = (str(data[0]), str(data[1]))
        scroll_value = self.list.verticalScrollBar().value() if same_book else 0

        self.list.clear()
        if book is None:
            self.summary.setText(tr('open_points.panel_no_book', 'Open een boek om de open punten te bekijken.'))
            self.add_button.setEnabled(False)
            return

        self.add_button.setEnabled(True)
        try:
            notes = self.store.load_notes(book)
        except Exception:
            notes = {}
        rows = []
        for section in book.sections:
            for chapter in section.chapters:
                if current_chapter_id and chapter.id == current_chapter_id and current_source is not None:
                    source = current_source
                else:
                    try:
                        source = self.library.read_chapter(book, chapter)
                    except (OSError, UnicodeError):
                        continue
                for point in parse_open_points(source, notes):
                    snippet = ' '.join(point.text.split()).strip() or '[…]'
                    if len(snippet) > 90:
                        snippet = snippet[:87].rstrip() + '…'
                    note = ' '.join(point.note.split()).strip()
                    rows.append((chapter, point, snippet, note))

        count = len(rows)
        if count == 0:
            self.summary.setText(tr(
                'open_points.panel_empty',
                'Geen open punten. Gebruik Toevoegen → Open punt wanneer je iets later wilt aanvullen.'
            ))
        elif count == 1:
            self.summary.setText(tr('open_points.panel_count_one', '1 open punt in dit boek.'))
        else:
            self.summary.setText(tr('open_points.panel_count_many', '{count} open punten in dit boek.', count=count))

        selected_row = -1
        for row, (chapter, point, snippet, note) in enumerate(rows):
            label = f'{chapter.title}\n{snippet}'
            if note:
                label += f'\n{tr("open_points.panel_note", "Notitie")}: {note}'
            item = QListWidgetItem(label)
            key = (str(chapter.id), str(point.id))
            item.setData(Qt.UserRole, key)
            item.setToolTip(tr('open_points.panel_open_tip', 'Dubbelklik of druk Enter om naar dit open punt te gaan.'))
            self.list.addItem(item)
            if selected_key == key:
                selected_row = row

        # Live refreshes should not throw the user back to the top of a long
        # list. Restore the selected logical point (if it still exists) and the
        # previous scroll position without emitting activation/navigation
        # signals while rebuilding the widget.
        # QListView lays out new items lazily; force it now so the scrollbar
        # maximum is current before restoring the previous value.
        self.list.doItemsLayout()
        self.list.blockSignals(True)
        try:
            if selected_row >= 0:
                self.list.setCurrentRow(selected_row)
            self.list.verticalScrollBar().setValue(
                min(scroll_value, self.list.verticalScrollBar().maximum())
            )
        finally:
            self.list.blockSignals(False)

    def _activate(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.UserRole)
        if not data or len(data) != 2:
            return
        self.openPointRequested.emit(str(data[0]), str(data[1]))
