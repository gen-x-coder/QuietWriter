"""Inventory of raw QMessageBox convenience calls for translation review.

Run with: python tools/check_qt_dialog_buttons.py
Read-only inventory; does not modify code or create translations.
"""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1] / 'quietwriter'
pattern = re.compile(r'QMessageBox\.(?:information|warning|critical|question)\s*\(')
for path in sorted(root.rglob('*.py')):
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if pattern.search(line):
            print(f'{path.relative_to(root)}:{number}: {line.strip()}')
