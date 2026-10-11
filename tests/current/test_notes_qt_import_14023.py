"""The Notes page must never import QTextCursor from QtWidgets."""
import ast
from pathlib import Path


def test_notes_cursor_import_is_from_qtgui_if_used():
    root = Path(__file__).resolve().parents[2]
    tree = ast.parse((root / 'quietwriter/ui/planning/notes_page.py').read_text(encoding='utf-8'))
    imports = {node.module: {alias.name for alias in node.names} for node in tree.body if isinstance(node, ast.ImportFrom)}
    assert 'QTextCursor' not in imports.get('PySide6.QtWidgets', set())
    if 'QTextCursor' in {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}:
        assert 'QTextCursor' in imports.get('PySide6.QtGui', set())
