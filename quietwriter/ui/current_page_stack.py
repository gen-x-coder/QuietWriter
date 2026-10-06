from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QStackedWidget, QSizePolicy


class CurrentPageStack(QStackedWidget):
    """QStackedWidget whose layout hints come only from the visible page.

    Qt's default QStackedWidget reports the largest minimum/size hint of all
    children, including hidden pages.  In a desktop application with scrollable
    forms that can make the whole top-level window demand the height of an
    inactive page.  This stack keeps hidden pages out of top-level geometry
    negotiation while preserving normal stacked-widget behaviour.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.currentChanged.connect(self._current_page_changed)

    def _current_page_changed(self, _index: int) -> None:
        self.updateGeometry()
        parent = self.parentWidget()
        if parent is not None:
            parent.updateGeometry()

    def minimumSizeHint(self) -> QSize:
        page = self.currentWidget()
        if page is None:
            return QSize(0, 0)
        hint = page.minimumSizeHint().expandedTo(page.minimumSize())
        return QSize(max(0, hint.width()), max(0, hint.height()))

    def sizeHint(self) -> QSize:
        page = self.currentWidget()
        if page is None:
            return QSize(0, 0)
        hint = page.sizeHint().expandedTo(page.minimumSize())
        return QSize(max(0, hint.width()), max(0, hint.height()))
