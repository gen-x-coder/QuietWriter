import json
import re
from pathlib import Path

from quietwriter.i18n import set_locale, tr

LOCALE_DIR = Path('quietwriter/locales')
CODES = ('nl', 'en', 'de', 'fr', 'es')
PH = re.compile(r'\{[^{}]+\}')


def _load(code):
    return json.loads((LOCALE_DIR / f'{code}.json').read_text(encoding='utf-8'))


def test_all_five_locales_have_identical_keys_placeholders_and_no_literal_backslash_n():
    en = _load('en')
    for code in CODES:
        data = _load(code)
        assert set(data) == set(en)
        for key in en:
            assert sorted(PH.findall(str(data[key]))) == sorted(PH.findall(str(en[key])))
            assert r'\n' not in str(data[key])


def test_new_languages_are_selectable_and_core_labels_are_translated():
    expected = {'de': 'Einstellungen', 'fr': 'Paramètres', 'es': 'Ajustes'}
    try:
        for code, label in expected.items():
            assert set_locale(code) == code
            assert tr('settings.title') == label
            assert tr('open_points.panel_title') != 'Open points'
    finally:
        set_locale('nl')


def test_non_english_locale_falls_back_to_english_before_code_default(monkeypatch):
    from quietwriter import i18n
    original = i18n.load_locale
    def fake(code='nl'):
        if code == 'de': return {}
        if code == 'en': return {'x.test': 'English fallback'}
        return original(code)
    monkeypatch.setattr(i18n, 'load_locale', fake)
    assert i18n.tr('x.test', 'Code default', code='de') == 'English fallback'
