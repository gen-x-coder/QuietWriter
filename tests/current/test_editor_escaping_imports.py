import ast
from pathlib import Path


def test_manuscript_editor_imports_all_literal_escape_helpers():
    source = Path('quietwriter/ui/manuscript_editor.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    imported = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == 'manuscript_markup' and node.level == 2:
            imported.update(alias.name for alias in node.names)
    assert {
        'escape_literal_typed_char',
        'escape_literal_space_prefix',
        'escape_literal_text',
        'unescape_literal_text',
    } <= imported
