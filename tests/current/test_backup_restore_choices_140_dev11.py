from pathlib import Path


def test_restore_choices_follow_selected_visible_book():
    source = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert 'self._refresh_restore_choices()' in source
    assert 'any(b.id == bid for b in self._visible_backup_books())' in source
    assert "self.backup_restore_choices.addItem(f'{stamp} · {kind}', str(path))" in source
    assert 'candidate.parent.resolve() != folder.resolve()' in source


def test_manual_restore_begins_in_backup_root_without_book():
    source = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert 'initial = Path(root).expanduser() if root else Path.home()' in source
    assert 'self.backup_path.setReadOnly(True)' in source
    assert 'self.backup_path.setMinimumWidth(400)' in source
