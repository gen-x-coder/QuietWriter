"""Regression gates from Claude's dev33 independent review."""
import ast
from pathlib import Path
from quietwriter.spell_engine import WordDictionary


def test_planning_dialogs_import_qmessagebox():
    for name in ('characters_page.py', 'planning_page.py'):
        source = Path('quietwriter/ui/planning', name).read_text(encoding='utf-8')
        tree = ast.parse(source)
        imported = {
            alias.asname or alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module == 'PySide6.QtWidgets'
            for alias in node.names
        }
        assert 'QMessageBox' in imported, name


def test_suggest_does_not_return_dutch_ij_ligature():
    class FakeHunspell:
        def suggest(self, word):
            return iter(['vrĳheid', 'VRĲHEID', 'vrijheid'])

    d = WordDictionary()
    d.hunspell = FakeHunspell()
    assert d.suggest('vrijheidd') == ['vrijheid', 'VRIJHEID']
