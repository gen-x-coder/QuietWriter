from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_editor_page_imports_qmenu_used_by_tree_context_menu():
    source = (ROOT / "quietwriter" / "ui" / "editor_page.py").read_text(encoding="utf-8")
    imports = source.split("from PySide6.QtWidgets import (", 1)[1].split(")", 1)[0]
    assert "QMenu" in imports
    assert "menu = QMenu(self)" in source


def test_current_page_stack_includes_explicit_page_minimum_size():
    source = (ROOT / "quietwriter" / "ui" / "current_page_stack.py").read_text(encoding="utf-8")
    assert "page.minimumSizeHint().expandedTo(page.minimumSize())" in source
    assert "page.sizeHint().expandedTo(page.minimumSize())" in source


def test_undo_refactor_recommendations_are_already_present():
    editor = (ROOT / "quietwriter" / "ui" / "manuscript_editor.py").read_text(encoding="utf-8")
    page = (ROOT / "quietwriter" / "ui" / "editor_page.py").read_text(encoding="utf-8")
    assert "def reset_undo_history(self):" in editor
    assert "edit_cursor.joinPreviousEditBlock()" in editor
    assert "def _make_block_format(" in editor
    set_chapter = page.split("    def _set_editor_chapter(self, chapter):", 1)[1].split("    def ", 1)[0]
    assert "self.editor.reset_undo_history()" in set_chapter
    on_change = page.split("    def on_text_changed(self):", 1)[1].split("    def ", 1)[0]
    assert "self.editor.schedule_formatting()" not in on_change
