from pathlib import Path
import json


def test_no_selection_has_distinct_restore_prompt():
    source = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert "if not bid else tr('settings.backup.no_choices'" in source
    assert "settings.backup.choose_book_first" in source

def test_restore_messages_reuse_common_close():
    source = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert source.count("tr('common.close', 'Sluiten')") >= 2
    assert "settings.backup.ok" not in source

def test_backup_translations_clean_and_parallel():
    langs = ['nl', 'en', 'de', 'fr', 'es']
    tables = [json.loads(Path(f'quietwriter/locales/{lang}.json').read_text(encoding='utf-8')) for lang in langs]
    assert all(set(t) == set(tables[0]) for t in tables)
    for t in tables:
        assert t['settings.backup.choose_book_first']
        assert t['settings.backup.book']
        assert t['common.close']
        assert 'settings.backup.ok' not in t
