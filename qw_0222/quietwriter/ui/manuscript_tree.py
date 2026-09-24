from PySide6.QtCore import Qt, QSettings, Signal, QMimeData, QTimer
from PySide6.QtGui import QColor, QDrag, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTreeWidget

from ..themes import THEMES


class ManuscriptTree(QTreeWidget):
    chapterDropped = Signal(str, str, str, bool)
    dragStarted = Signal()
    dragFinished = Signal()
    keyboardActivated = Signal(object)

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
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setRootIsDecorated(True)
        self.setItemsExpandable(True)
        self.setIndentation(14)
        self.setUniformRowHeights(True)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self._drag_allowed = False
        self._drag_item = None
        self._drop_target = None
        self._drop_line_y = None
        self._drop_before = True
        self._pending_drop = None
        # The guard starts on handle mouse-press, not only in startDrag().
        # QAbstractItemView may move focus while processing that press, which can
        # synchronously fire e.g. chapter-title editingFinished handlers. Those
        # handlers must already know that rebuilding the tree is unsafe.
        self._dragging = False
        self._drag_exec_active = False
        self._finish_scheduled = False

    @property
    def is_dragging(self):
        return self._dragging

    def _begin_drag_guard(self):
        if self._dragging:
            return
        self._dragging = True
        self._finish_scheduled = False
        self._pending_drop = None
        self.dragStarted.emit()

    def _schedule_drag_finish(self):
        if self._finish_scheduled:
            return
        self._finish_scheduled = True
        pending_drop = self._pending_drop
        self._pending_drop = None
        # Keep the guard active until the next event-loop turn. This guarantees
        # that startDrag()/mouseReleaseEvent() and Qt's native drag machinery
        # have fully unwound before EditorPage is allowed to rebuild the tree.
        QTimer.singleShot(0, lambda p=pending_drop: self._finish_drag(p))

    def _finish_drag(self, pending_drop):
        self._finish_scheduled = False
        self._drag_exec_active = False
        self._drag_allowed = False
        self._drag_item = None
        self._drop_target = None
        self._drop_line_y = None
        self._dragging = False
        self.viewport().setCursor(Qt.ArrowCursor)
        self.viewport().update()
        try:
            if pending_drop is not None:
                source_id, target_type, target_id, before = pending_drop
                self.chapterDropped.emit(source_id, target_type, target_id, before)
        finally:
            # Always release EditorPage's drag guards, including cancelled drags
            # and failures in a connected drop handler.
            self.dragFinished.emit()

    def mouseMoveEvent(self, event):
        idx = self.indexAt(event.position().toPoint())
        item = self.itemAt(event.position().toPoint())
        data = item.data(0, Qt.UserRole) if item else None
        over_handle = bool(idx.isValid() and idx.column() == 1 and data and data[0] == 'chapter')
        self.viewport().setCursor(Qt.OpenHandCursor if over_handle else Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        # QTreeWidget exposes itemActivated, but its mouse activation semantics
        # vary by platform. Keep single-click opening unchanged and provide one
        # explicit, predictable keyboard path instead.
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and event.modifiers() == Qt.NoModifier:
            item = self.currentItem()
            if item is not None:
                self.keyboardActivated.emit(item)
                event.accept()
                return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        idx = self.indexAt(event.position().toPoint())
        data = item.data(0, Qt.UserRole) if item else None
        previous_current = self.currentItem()
        # Only the six-dot handle in column 1 can start a drag. Start the guard
        # before calling QTreeWidget.mousePressEvent(): the base implementation
        # may change focus, which can synchronously trigger editingFinished and
        # other callbacks that would otherwise clear this tree mid-press.
        self._drag_allowed = bool(item and idx.isValid() and idx.column() == 1 and data and data[0] == 'chapter')
        self._drag_item = item if self._drag_allowed else None

        # The tree highlight represents the content currently shown in the
        # editor. Merely grabbing another chapter's drag handle or expanding a
        # structural row must not move that highlight away from the text the
        # user is still reading/editing. Voorwerk/Achterwerk may become current
        # only through their explicit 'wijzig' action in column 1.
        structural_click = bool(data and data[0] in ('section', 'manuscript_group'))
        explicit_group_edit = bool(
            data and data[0] == 'manuscript_group' and idx.isValid()
            and idx.column() == 1 and data[1] in ('front', 'back')
        )
        preserve_current = self._drag_allowed or (structural_click and not explicit_group_edit)

        if self._drag_allowed:
            self._begin_drag_guard()
            self.viewport().setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

        if preserve_current:
            if previous_current is not None:
                self.setCurrentItem(previous_current)
            else:
                self.clearSelection()
                self.setCurrentItem(None)

    def mouseReleaseEvent(self, event):
        armed_without_native_drag = self._dragging and not self._drag_exec_active
        super().mouseReleaseEvent(event)
        # A click on the handle that never crossed Qt's drag threshold still
        # entered the guard in mousePressEvent. Release it after the press/release
        # sequence has completely unwound.
        if armed_without_native_drag and self._dragging:
            self._schedule_drag_finish()

    def startDrag(self, supportedActions):
        if not self._drag_allowed or not self._drag_item:
            if self._dragging:
                self._schedule_drag_finish()
            return
        data = self._drag_item.data(0, Qt.UserRole)
        if not data or data[0] != 'chapter':
            self._schedule_drag_finish()
            return

        # Normally the guard was started in mousePressEvent. Keep this fallback
        # for programmatic/Qt initiated drags so every path has identical safety.
        self._begin_drag_guard()

        # Convert everything needed by the native drag to plain Python/Qt value
        # objects *before* entering QDrag.exec(). Do not retain QTreeWidgetItem
        # wrappers across the nested native drag loop.
        source_id = str(data[1])
        source_title = self._drag_item.text(0)
        rect = self.visualItemRect(self._drag_item)
        self._drag_item = None

        mime = QMimeData()
        mime.setData(self.MIME_TYPE, source_id.encode('utf-8'))
        drag = QDrag(self)
        drag.setMimeData(mime)
        pix = QPixmap(max(180, rect.width()), max(28, rect.height()))
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        try:
            painter.setPen(QColor(THEMES.get(str(QSettings('QuietWriter', 'QuietWriter').value('theme', 'Helder')), THEMES['Helder'])['muted']))
            painter.drawText(pix.rect().adjusted(8, 0, -8, 0), Qt.AlignVCenter | Qt.AlignLeft, source_title)
        finally:
            painter.end()
        drag.setPixmap(pix)

        self._drag_exec_active = True
        try:
            drag.exec(Qt.MoveAction)
        finally:
            # QDrag.exec() runs a nested native event loop. Never emit the drop
            # or dragFinished synchronously from here: schedule one event-loop
            # turn later, after the native drag and this virtual method returned.
            self._drag_exec_active = False
            self._drag_allowed = False
            self._drag_item = None
            self._drop_target = None
            self._drop_line_y = None
            self.viewport().setCursor(Qt.ArrowCursor)
            self.viewport().update()
            self._schedule_drag_finish()

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
            self._drop_target = None
            self._drop_line_y = None
            self.viewport().update()
            event.ignore()
            return
        tdata = target.data(0, Qt.UserRole)
        source_id = bytes(event.mimeData().data(self.MIME_TYPE)).decode('utf-8', errors='ignore')
        if not tdata or tdata[0] not in ('chapter', 'section') or (tdata[0] == 'chapter' and tdata[1] == source_id):
            self._drop_target = None
            self._drop_line_y = None
            self.viewport().update()
            event.ignore()
            return

        # Never retain the target QTreeWidgetItem during the native drag. A
        # Shiboken wrapper that outlives the underlying C++ item is a native
        # crash risk. Store only immutable identifiers and the already computed
        # paint coordinate.
        rect = self.visualItemRect(target)
        self._drop_before = event.position().y() < rect.center().y()
        self._drop_target = (str(tdata[0]), str(tdata[1]))
        self._drop_line_y = int(rect.top() if self._drop_before else rect.bottom())
        self.viewport().update()
        event.setDropAction(Qt.MoveAction)
        event.accept()

    def dragLeaveEvent(self, event):
        self._drop_target = None
        self._drop_line_y = None
        self.viewport().update()
        event.accept()

    def dropEvent(self, event):
        # Never rebuild/mutate the QTreeWidget while Qt is dispatching the
        # active QDropEvent or while QDrag.exec() is still running. Only plain
        # Python values survive beyond this event; no QTreeWidgetItem wrapper is
        # kept alive across the native drag boundary.
        try:
            if not event.mimeData().hasFormat(self.MIME_TYPE):
                event.ignore(); return
            source_id = bytes(event.mimeData().data(self.MIME_TYPE)).decode('utf-8', errors='ignore')
            target_data = self._drop_target
            if target_data is None:
                target = self.itemAt(event.position().toPoint())
                tdata = target.data(0, Qt.UserRole) if target else None
                if tdata and tdata[0] in ('chapter', 'section'):
                    target_data = (str(tdata[0]), str(tdata[1]))
            if not source_id or target_data is None:
                event.ignore(); return
            target_type, target_id = target_data
            self._pending_drop = (source_id, target_type, target_id, bool(self._drop_before))
            event.setDropAction(Qt.MoveAction)
            event.accept()
        finally:
            self._drop_target = None
            self._drop_line_y = None
            self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)

        # IMPORTANT: there must be at most one active QPainter for the viewport.
        # 0.18.8 created one painter for the selection accent and then, while
        # that painter was still alive, a second painter for the drop line. On
        # Windows this can produce a native access violation inside QPainter.
        selection_rect = None
        if not self._dragging:
            current = self.currentItem()
            data = current.data(0, Qt.UserRole) if current else None
            if current and current.isSelected() and data and data[0] == 'chapter':
                rect = self.visualItemRect(current)
                if rect.isValid():
                    selection_rect = rect

        drop_y = self._drop_line_y
        if selection_rect is None and drop_y is None:
            return

        painter = QPainter(self.viewport())
        if not painter.isActive():
            return
        try:
            painter.setPen(QPen(self.palette().color(QPalette.Highlight), 3))
            if selection_rect is not None:
                x = max(1, selection_rect.left() + 1)
                painter.drawLine(x, selection_rect.top() + 3, x, selection_rect.bottom() - 3)
            if drop_y is not None:
                y = max(0, min(int(drop_y), self.viewport().height() - 1))
                painter.drawLine(8, y, max(8, self.viewport().width() - 8), y)
        finally:
            painter.end()
