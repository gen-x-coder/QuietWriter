import pytest

pytest.importorskip("PySide6")
pytestmark = pytest.mark.qt

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel

from quietwriter.storage import Library
from quietwriter.ui.chapter_context_panel import ChapterContextPanel
from quietwriter.ui.settings_page import SettingsPage


def _app():
    return QApplication.instance() or QApplication([])


def test_chapter_context_empty_heading_stays_at_top(tmp_path):
    app = _app()
    panel = ChapterContextPanel(Library(tmp_path / "workspace"))
    panel.resize(380, 760)
    panel.show()
    panel.clear("Nog geen scènes gekoppeld.")
    QTest.qWait(20)
    assert panel.panel_help.title.geometry().top() <= 32
    assert panel.open_button.geometry().bottom() >= 700
    panel.close()
    app.processEvents()


def test_full_width_wrapped_label_gets_enough_height():
    _app()
    label = QLabel("Bron: meegeleverd · nl_NL · met .aff-regels\n" + ("C:/erg/lange/woordenboeken/map/" * 8))
    label.setWordWrap(True)
    label.setMaximumWidth(820)
    SettingsPage._reserve_wrapped_label_height(label, 600)
    assert label.minimumHeight() >= label.heightForWidth(600)
