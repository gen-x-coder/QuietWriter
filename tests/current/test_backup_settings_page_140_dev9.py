"""Static guard for dev.9's settings navigation and backup controls.

Real Qt geometry and interactions are checked in the Windows acceptance test.
"""
from pathlib import Path


def test_backups_have_separate_page_and_manual_controls_remain_enabled():
    source = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert "self._add_settings_category(nav_lay, tr('settings.backup.page'" in source
    assert "self._add_settings_category(nav_lay, tr('settings.general'" in source
    assert source.index("self._add_settings_category(nav_lay, tr('settings.general'") < source.index("self._add_settings_category(nav_lay, tr('settings.backup.page'")
    assert 'self.backup_enabled.toggled.connect(self._update_backup_controls)' in source
    assert 'self._backup_controls = (' not in source
    assert 'self.backup_now.setEnabled(not busy and self.backup_book.currentData() is not None)' in source
    assert 'self.backup_status = WrappedHeightLabel' in source
