"""Protect translated one-button notices and safety confirmations."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / 'quietwriter' / 'ui'


def test_planning_and_integrity_use_translated_dialogs():
    selected = [ROOT / 'integrity_page.py', *sorted((ROOT / 'planning').glob('*.py'))]
    offenders = []
    for path in selected:
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'QMessageBox' and node.func.attr in {'question','information','warning','critical'}:
                offenders.append(f'{path.relative_to(ROOT)}:{node.lineno}')
    assert not offenders, f'Untranslated Qt dialog: {offenders}'


def test_integrity_safety_choices_use_central_no_default():
    src = (ROOT / 'integrity_page.py').read_text(encoding='utf-8')
    assert src.count('approved = confirm(') == 2
    assert src.count('if not approved:') == 2
    central = (ROOT / 'dialogs.py').read_text(encoding='utf-8')
    assert "tr('common.yes', 'Ja')" in central
    assert "tr('common.no', 'Nee')" in central
    assert 'box.setDefaultButton(no if default_no else yes)' in central
