
from PySide6.QtCore import Qt, QSettings, Signal, QMimeData
from PySide6.QtGui import QColor, QDrag, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTreeWidget

from ..themes import THEMES

class ManuscriptTree(QTreeWidget):
    chapterDropped = Signal(str, str, str, bool)

    MIME_TYPE = 'application/x-quietwriter-chapter'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHeaderHidden(True)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.Fixed)
        self.header().setMinimumSectionSize(0)
        self.setColumnWidth(1, 58)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(False)
        # Crucial: do NOT use InternalMove. QTreeWidget would then mutate its own
        # item model during a drag, independently of book.json. QuietWriter uses
        # a custom QDrag and only changes the book model after a validated drop.
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setRootIsDecorated(True)
        self.setItemsExpandable(True)
        self.setIndentation(14)
        self.setUniformRowHeights(True)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self._drag_allowed = False
        self._drag_item = None
        self._drop_item = None
        self._drop_before = True


    def mouseMoveEvent(self, event):
        idx = self.indexAt(event.position().toPoint())
        item = self.itemAt(event.position().toPoint())
        data = item.data(0, Qt.UserRole) if item else None
        over_handle = bool(idx.isValid() and idx.column() == 1 and data and data[0] == 'chapter')
        self.viewport().setCursor(Qt.OpenHandCursor if over_handle else Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        idx = self.indexAt(event.position().toPoint())
        data = item.data(0, Qt.UserRole) if item else None
        # Only the six-dot handle in column 1 can start a drag.
        self._drag_allowed = bool(item and idx.isValid() and idx.column() == 1 and data and data[0] == 'chapter')
        self._drag_item = item if self._drag_allowed else None
        if self._drag_allowed:
            self.viewport().setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def startDrag(self, supportedActions):
        if not self._drag_allowed or not self._drag_item:
            return
        data = self._drag_item.data(0, Qt.UserRole)
        if not data or data[0] != 'chapter':
            return
        mime = QMimeData()
        mime.setData(self.MIME_TYPE, data[1].encode('utf-8'))
        drag = QDrag(self)
        drag.setMimeData(mime)
        # Small neutral drag image; this does not detach/move the tree item.
        pix = QPixmap(max(180, self.visualItemRect(self._drag_item).width()), max(28, self.visualItemRect(self._drag_item).height()))
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setPen(QColor(THEMES.get(str(QSettings('QuietWriter','QuietWriter').value('theme','Helder')), THEMES['Helder'])['muted']))
        painter.drawText(pix.rect().adjusted(8, 0, -8, 0), Qt.AlignVCenter | Qt.AlignLeft, self._drag_item.text(0))
        painter.end()
        drag.setPixmap(pix)
        drag.exec(Qt.MoveAction)
        self.viewport().setCursor(Qt.ArrowCursor)
        self._drag_allowed = False
        self._drag_item = None
        self._drop_item = None
        self.viewport().update()

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if not event.mimeData().hasFormat(self.MIME_TYPE):
            event.ignore(); return
        target = self.itemAt(event.position().toPoint())
        if not target:
            self._drop_item = None; self.viewport().update(); event.ignore(); return
        tdata = target.data(0, Qt.UserRole)
        source_id = bytes(event.mimeData().data(self.MIME_TYPE)).decode('utf-8', errors='ignore')
        if not tdata or tdata[0] not in ('chapter', 'section') or (tdata[0] == 'chapter' and tdata[1] == source_id):
            self._drop_item = None; self.viewport().update(); event.ignore(); return
        rect = self.visualItemRect(target)
        self._drop_item = target
        self._drop_before = event.position().y() < rect.center().y()
        self.viewport().update()
        event.setDropAction(Qt.MoveAction)
        event.accept()

    def dragLeaveEvent(self, event):
        self._drop_item = None
        self.viewport().update()
        event.accept()

    def dropEvent(self, event):
        try:
            if not event.mimeData().hasFormat(self.MIME_TYPE):
                event.ignore(); return
            source_id = bytes(event.mimeData().data(self.MIME_TYPE)).decode('utf-8', errors='ignore')
            target = self._drop_item or self.itemAt(event.position().toPoint())
            if not source_id or not target:
                event.ignore(); return
            tdata = target.data(0, Qt.UserRole)
            if not tdata or tdata[0] not in ('chapter', 'section'):
                event.ignore(); return
            self.chapterDropped.emit(source_id, tdata[0], tdata[1], self._drop_before)
            event.setDropAction(Qt.MoveAction)
            event.accept()
        finally:
            self._drag_item = None
            self._drop_item = None
            self._drag_allowed = False
            self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._drop_item:
            r = self.visualItemRect(self._drop_item)
            y = r.top() if self._drop_before else r.bottom()
            p = QPainter(self.viewport())
            p.setPen(QPen(self.palette().color(QPalette.Highlight), 3))
            p.drawLine(8, y, max(8, self.viewport().width() - 8), y)
