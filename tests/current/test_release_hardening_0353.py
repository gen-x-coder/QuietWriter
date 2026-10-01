from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / 'quietwriter'


def test_modules_using_tr_bind_the_name():
    """Catch the exact startup-blocker class even where Qt runtime is unavailable."""
    offenders = []
    for path in PKG.rglob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        uses_tr = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'tr' for n in ast.walk(tree))
        if not uses_tr:
            continue
        bound = False
        for n in tree.body:
            if isinstance(n, ast.ImportFrom):
                if any(alias.asname == 'tr' or (alias.name == 'tr' and alias.asname is None) for alias in n.names):
                    bound = True
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == 'tr':
                bound = True
        if not bound and path.name != 'i18n.py':
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_locales_still_have_identical_keysets():
    nl = json.loads((PKG/'locales/nl.json').read_text(encoding='utf-8'))
    en = json.loads((PKG/'locales/en.json').read_text(encoding='utf-8'))
    assert set(nl) == set(en)


def test_remaining_release_strings_use_translation_contracts():
    editor = (PKG/'ui/editor_page.py').read_text(encoding='utf-8')
    manuscript = (PKG/'ui/manuscript_editor.py').read_text(encoding='utf-8')
    ai = (PKG/'ai/ui.py').read_text(encoding='utf-8')
    spell = (PKG/'ui/spell_panel.py').read_text(encoding='utf-8')
    assert "editor.status.book.one" in editor
    assert "editor.replace_all.confirm" in editor
    assert "format.menu" in manuscript
    assert "ai.you" in ai
    assert "spell.position" in spell


def test_planning_translates_display_without_changing_canonical_values():
    outline = (PKG/'ui/planning/outline_page.py').read_text(encoding='utf-8')
    chars = (PKG/'ui/planning/characters_page.py').read_text(encoding='utf-8')
    assert "self.status.addItem(tr(key, label), value)" in outline
    assert "editable_combo_value(self.status, default='idee')" in outline
    assert "relation_display(relation.type)" in chars
    assert "editable_combo_value(self.rel_type, default='kent')" in chars


def test_font_licenses_do_not_contain_ofl_template_placeholders():
    for path in (ROOT/'resources/fonts').glob('*/OFL.txt'):
        text = path.read_text(encoding='utf-8')
        assert '<Copyright Holder>' not in text
        assert '<Reserved Font Name>' not in text
