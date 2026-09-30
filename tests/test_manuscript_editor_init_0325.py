import ast
from pathlib import Path


def test_manuscript_editor_init_has_no_nested_method_or_early_return():
    source = Path('quietwriter/ui/manuscript_editor.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'ManuscriptEditor')
    init = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == '__init__')

    nested_defs = [
        node for statement in init.body for node in ast.walk(statement)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node is not init
    ]
    returns = [node for statement in init.body for node in ast.walk(statement) if isinstance(node, ast.Return)]
    assert nested_defs == []
    assert returns == []
