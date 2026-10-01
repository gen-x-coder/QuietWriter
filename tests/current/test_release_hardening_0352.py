from __future__ import annotations

import ast
import json
from pathlib import Path

from quietwriter.crash_logging import _exception_fingerprint


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'quietwriter'
LOCALES = PACKAGE / 'locales'
VISIBLE_CALLS = {
    'QLabel', 'QPushButton', 'QCheckBox', 'QRadioButton', 'QGroupBox',
    'setText', 'setToolTip', 'setAccessibleName', 'setPlaceholderText', 'setWindowTitle',
}
ALLOWED_LITERAL_UI = {'+', '×', 'AI', 'API-key', '/{slug}.jpg', '000-0-00-000000-0'}


def _literal_tr_keys() -> set[str]:
    keys: set[str] = set()
    for path in PACKAGE.rglob('*.py'):
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            if isinstance(node.func, ast.Name) and node.func.id == 'tr':
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    keys.add(first.value)
    return keys


def test_all_literal_translation_keys_exist_in_both_locales():
    required = _literal_tr_keys()
    for language in ('nl', 'en'):
        data = json.loads((LOCALES / f'{language}.json').read_text(encoding='utf-8'))
        missing = sorted(required - set(data))
        assert missing == [], f'{language}.json mist tr()-sleutels: {missing}'


def test_visible_widget_literals_do_not_bypass_translation_gate():
    offenders: list[str] = []
    for path in PACKAGE.rglob('*.py'):
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            else:
                continue
            if name not in VISIBLE_CALLS:
                continue
            first = node.args[0]
            if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
                continue
            value = first.value.strip()
            if not value or value in ALLOWED_LITERAL_UI:
                continue
            offenders.append(f'{path.relative_to(ROOT)}:{node.lineno}: {name}({value!r})')
    assert offenders == [], 'Niet-vertaalde zichtbare UI-literals:\n' + '\n'.join(offenders)


def test_dynamic_ai_section_and_quick_action_keys_exist_in_both_locales():
    expected = {
        *(f'persona.section.{key}.{field}' for key in ('voice_tone','narration','language','rhythm','description','dialogue','emotion_intimacy','scenes_pacing','editorial','avoid','examples','additional') for field in ('title','help')),
        *(f'book_profile.section.{key}.{field}' for key in ('genre_audience','premise','narration','tone','themes','setting','pacing','intensity','persona_overrides','editorial','additional') for field in ('title','help')),
        *(f'book_memory.section.{key}.{field}' for key in ('canon','book_style','decisions','preferences','open_points') for field in ('title','help')),
        *(f'ai.quick.{key}.{field}' for key in ('feedback','persona_check','fact_check') for field in ('label','tooltip','prompt')),
    }
    for language in ('nl', 'en'):
        data = json.loads((LOCALES / f'{language}.json').read_text(encoding='utf-8'))
        missing = sorted(expected - set(data))
        assert missing == [], f'{language}.json mist dynamische UI-sleutels: {missing}'


def _same_source_failure(message: str) -> str:
    try:
        raise RuntimeError(message)
    except RuntimeError as exc:
        return _exception_fingerprint(type(exc), exc.__traceback__)


def test_crash_cooldown_fingerprint_ignores_changing_exception_text():
    first = _same_source_failure('item 17')
    second = _same_source_failure('item 18')
    assert first == second
    assert 'item 17' not in first
    assert 'item 18' not in second
    assert 'RuntimeError|' in first


def test_font_manifest_has_release_fonts_and_local_license_files():
    root = ROOT / 'resources' / 'fonts'
    data = json.loads((root / 'font_manifest.json').read_text(encoding='utf-8'))
    assert [item['family'] for item in data['fonts']] == ['Merriweather', 'Literata', 'Source Serif 4', 'EB Garamond']
    for item in data['fonts']:
        assert item['license'] == 'SIL Open Font License 1.1'
        assert len(item['files']) == 2
        assert (root / item['slug'] / 'OFL.txt').is_file()


def test_release_license_inventory_exists_and_calls_out_dictionary_gate():
    own = (ROOT / 'documents' / 'licenses' / 'LICENSE').read_text(encoding='utf-8')
    third = (ROOT / 'documents' / 'licenses' / 'THIRD_PARTY_LICENSES.md').read_text(encoding='utf-8')
    assert 'Lucas Bonsel' in own
    for term in ('PySide6', 'Python', 'Requests', 'spylls', 'Merriweather', 'Literata', 'Source Serif 4', 'EB Garamond'):
        assert term in third
    assert 'Hunspell' in third and 'nl_NL' in third and 'Revised BSD License' in third
