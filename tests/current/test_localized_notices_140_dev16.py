"""Guard against unlocalized default OK on one-button Qt notices."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / 'quietwriter' / 'ui'


def test_single_button_notices_use_localized_helper():
    offenders = []
    for path in UI.glob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == 'QMessageBox'
                    and node.func.attr in {'information', 'warning', 'critical'}):
                offenders.append(f'{path.name}:{node.lineno}')
    assert not offenders, 'Untranslated default OK button: ' + ', '.join(offenders)


def test_notice_helper_reuses_existing_close_key():
    source = (UI / 'dialog_notices.py').read_text(encoding='utf-8')
    assert "tr('common.close', 'Sluiten')" in source
    assert 'dialog.addButton(' in source
