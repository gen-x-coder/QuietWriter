"""Regression: rail animation must not reread and rescale book cover on every repaint."""
import os
from pathlib import Path

import pytest
pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import QApplication
from quietwriter.ui.bookshelf import BookCover


def test_book_cover_cache_survives_multiple_paints(tmp_path):
    app = QApplication.instance() or QApplication([])
    cover_file = tmp_path / 'cover.png'
    pix = QPixmap(500, 700)
    pix.fill(QColor('red'))
    assert pix.save(str(cover_file))
    class Lib:
        def cover_path(self, book):
            return cover_file
        def default_cover_path(self):
            return None
    class Book:
        title = 'Boek'
    widget = BookCover(Lib(), Book())
    try:
        first = widget._cover_pixmap(cover_file)
        assert first is not None
        assert first.size().width() >= widget.width()
        assert widget._cover_pixmap(cover_file) is first
        widget.grab()
        widget.grab()
        assert widget._cover_pixmap(cover_file) is first
        other = tmp_path / 'other.png'
        pix.fill(QColor('blue'))
        assert pix.save(str(other))
        second = widget._cover_pixmap(other)
        assert second is not None and second is not first
        assert widget._cover_pixmap(tmp_path / 'missing.png') is None
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()
