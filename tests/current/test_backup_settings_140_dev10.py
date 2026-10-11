from pathlib import Path

def test_backup_privacy_and_manual_independence():
    src = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert 'visible_book_ids(' in src
    assert 'demo_mode=True' in src
    assert 'self._visible_backup_books() if b.id == book_id' in src
    assert 'self.backup_now.setEnabled(self.backup_enabled.isChecked())' not in src
    assert 'self.backup_book.setCurrentIndex(index if index >= 0 else -1)' in src
