from pathlib import Path


def test_openrouter_filter_waits_for_catalog_metadata_and_never_erases_empty_selection():
    source = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert "filter_active = self.openrouter_free_only.isChecked() and bool(info_by_name)" in source
    assert "if provider_name in self._ai_model_drafts and selected:" in source
    assert "current == 'openrouter/free' or current.endswith(':free')" in source
    save_body = source.split('def save_settings', 1)[1]
    assert 'self._remember_current_ai_model(provider)' not in save_body


def test_editor_toolbar_keeps_text_width_compact_and_title_elided():
    source = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    assert 'self.text_width_combo.setFixedWidth(112)' in source
    assert "tl.addWidget(QLabel(tr('editor.text_width'" not in source
    assert 'Qt.ElideRight' in source
    assert 'self.book_title_label.setMinimumWidth(0)' in source
    assert 'QSizePolicy.Ignored' in source
