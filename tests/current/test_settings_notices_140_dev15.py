from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_settings_notifications_use_quietwriter_translated_close():
    source = (ROOT / 'quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert "dialog.addButton(tr('common.close', 'Sluiten'), QMessageBox.AcceptRole)" in source
    assert 'QMessageBox.information(' not in source
    assert 'QMessageBox.warning(' not in source
    assert '_translated_notice(QMessageBox.Information' in source
    assert '_translated_notice(QMessageBox.Warning' in source


def test_close_translation_is_reused_in_all_five_languages():
    import json
    for lang in ('nl', 'en', 'de', 'fr', 'es'):
        data = json.loads((ROOT / 'quietwriter/locales' / (lang + '.json')).read_text(encoding='utf-8'))
        assert data['common.close'].strip()
