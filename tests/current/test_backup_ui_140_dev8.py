"""Regression guards for the dev.8 restore flow and persistent errors."""
from pathlib import Path


def test_restore_uses_existing_import_instead_of_writing_directly():
    settings = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert 'self._import_or_replace_backup(Path(path))' in settings
    assert 'self.main.import_book(str(source))' in settings
    assert 'replace_existing_book(' in settings
    assert 'self._refresh_backup_books()' in settings


def test_backup_errors_remain_visible_until_success():
    settings = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    main = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    assert "self.settings.setValue(f'backup/error/{book_id}', str(error))" in settings
    assert "self.settings.setValue(f'backup/error/{book_id}', '')" in settings
    assert "self.settings.setValue(f'backup/error/{book_id}', message)" in main
    assert "if is_change:" in main
    assert "self.settings.setValue(f'backup/error/{book_id}', '')" in main


def test_restore_locales_keep_parity():
    import json
    keys = ['settings.backup.restore', 'settings.backup.restore_label',
            'settings.backup.restore_help', 'settings.backup.restore_filter',
            'settings.backup.last_error']
    for language in ('nl', 'en', 'de', 'fr', 'es'):
        values = json.loads(Path(f'quietwriter/locales/{language}.json').read_text(encoding='utf-8'))
        assert all(values.get(key) for key in keys)
