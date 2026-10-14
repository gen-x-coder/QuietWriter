import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest
pytest.importorskip("PySide6")
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from quietwriter.ui.darlings_actions_panel import DarlingsActionsPanel
from quietwriter.ui.panel_help import PanelHelp

def test_compact_help_without_acknowledge_button(tmp_path):
    app = QApplication.instance() or QApplication([])
    help_box = PanelHelp(QSettings(str(tmp_path / "test.ini"), QSettings.IniFormat),
                         "darlings", "Bewaarplaats", "Korte uitleg", show_dismiss_button=False)
    help_box.resize(300, 130)
    help_box.show()
    app.processEvents()
    assert help_box.block.isVisible()
    assert not help_box.ok.isVisible()
    assert help_box.toggle.isVisible()
    help_box.toggle.click()
    assert not help_box.block.isVisible()
    help_box.toggle.click()
    assert help_box.block.isVisible()
    help_box.close()
