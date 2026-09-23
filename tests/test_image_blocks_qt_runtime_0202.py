import os
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

try:
    from PySide6.QtCore import QEventLoop, QTimer
    from PySide6.QtGui import QImage
    from PySide6.QtWidgets import QApplication
    from quietwriter.ui.manuscript_editor import ManuscriptEditor
except Exception:
    pytest.skip('PySide6 runtime not available', allow_module_level=True)


def pump(ms=20):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def test_image_card_stays_inside_reserved_block_and_card_click_does_not_edit():
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as td:
        image_path = Path(td) / 'sample.png'
        image = QImage(80, 50, QImage.Format_ARGB32)
        image.fill(0xFF6688AA)
        assert image.save(str(image_path))

        editor = ManuscriptEditor()
        editor.resize(760, 520)
        editor.set_image_resolver(lambda _ref: image_path)
        editor.setPlainText(
            'Alinea boven.\n\n'
            '![Alt](../assets/images/example.png "Onderschrift")\n\n'
            'Alinea onder.'
        )
        editor.show()
        editor.apply_visual_formatting()
        editor.refresh_image_blocks()
        pump(60)

        assert len(editor._image_cards) == 1
        block = editor.document().findBlockByNumber(2)
        assert block.isValid()
        card = editor._image_cards[2]
        assert card.isVisible()

        doc_rect = editor.document().documentLayout().blockBoundingRect(block)
        reserved_height = max(editor.IMAGE_BLOCK_HEIGHT, round(doc_rect.height()))
        assert card.height() <= reserved_height

        edits = []
        editor.imageEditRequested.connect(edits.append)
        card.selected.emit(2)
        pump()
        assert edits == []
        card.editRequested.emit(2)
        pump()
        assert edits == [2]

        next_block = block.next().next()  # blank separator, then prose
        assert next_block.isValid()
        next_top = editor._block_viewport_top(next_block)
        assert card.geometry().bottom() < next_top
        editor.close()
