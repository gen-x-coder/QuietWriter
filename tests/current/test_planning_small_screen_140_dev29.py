"""Regression guard for responsive planning dialogs without requiring a Qt runtime."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_note_dialog_respects_available_screen():
    source = (ROOT / 'quietwriter/ui/planning/notes_page.py').read_text(encoding='utf-8')
    assert 'screen.availableGeometry()' in source
    assert 'dialog.setMinimumSize(320, 240)' in source
    assert "buttons.accepted.connect(dialog.accept)" in source


def test_scene_dialog_keeps_actions_outside_scroll():
    source = (ROOT / 'quietwriter/ui/planning/outline_page.py').read_text(encoding='utf-8')
    assert 'screen.availableGeometry()' in source
    assert 'self.setMinimumSize(340, 280)' in source
    assert 'root.addWidget(self.form_scroll,1)' in source
    assert 'root.addWidget(buttons)' in source
