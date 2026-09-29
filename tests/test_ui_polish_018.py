from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / 'quietwriter' / 'ui' / 'settings_page.py'
EDITOR = ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py'
TOOLBAR = ROOT / 'quietwriter' / 'ui' / 'selection_toolbar.py'
THEMES = ROOT / 'quietwriter' / 'themes.py'


def test_settings_use_horizontal_row_language_and_sections():
    source = SETTINGS.read_text(encoding='utf-8')
    assert "row.setObjectName('settingsRow')" in source
    assert "label.setObjectName('settingsFieldLabel')" in source
    assert "detail.setObjectName('settingsFieldHelp')" in source
    assert "label.setObjectName('settingsSectionTitle')" in source
    assert "self._add_settings_section(al, tr('settings.section.typography', 'Schrijftypografie'))" in source
    assert "self._add_settings_section(al, tr('settings.section.manuscript', 'Manuscript'))" in source


def test_font_preview_is_beside_font_selector():
    source = SETTINGS.read_text(encoding='utf-8')
    assert "font_control = QWidget()" in source
    assert "fh = QHBoxLayout(font_control)" in source
    assert "fh.addWidget(self.editor_font, 0, Qt.AlignTop); fh.addWidget(preview_card, 1)" in source


def test_autosave_help_explains_always_on_save():
    source = SETTINGS.read_text(encoding='utf-8')
    assert 'Ctrl+S' in source
    assert 'slaat wijzigingen automatisch op' in source
    assert 'self.autosave = QCheckBox' not in source


def test_settings_save_button_tracks_dirty_state():
    source = SETTINGS.read_text(encoding='utf-8')
    assert 'def _current_form_state(self):' in source
    assert 'def _update_dirty_state(self, *_):' in source
    assert 'self.save_btn.setEnabled(False)' in source
    assert 'self._saved_form_state = self._current_form_state()' in source


def test_selection_toolbar_is_non_activating():
    source = TOOLBAR.read_text(encoding='utf-8')
    assert 'Qt.WindowDoesNotAcceptFocus' in source
    assert 'Qt.WA_ShowWithoutActivating' in source
    assert 'btn.setFocusPolicy(Qt.NoFocus)' in source


def test_editor_context_menu_keeps_standard_edit_actions_and_adds_formatting():
    source = EDITOR.read_text(encoding='utf-8')
    assert 'def contextMenuEvent(self, event):' in source
    assert 'menu = self.createStandardContextMenu()' in source
    assert "formatting = menu.addMenu('Opmaak')" in source
    assert "paragraph_menu = formatting.addMenu('Alineastijl')" in source
    assert "('bold', 'Vet')" in source
    assert "('heading', 'Tussenkop')" in source


def test_settings_theme_has_shared_row_styles():
    source = THEMES.read_text(encoding='utf-8')
    assert 'QFrame#settingsRow' in source
    assert 'QLabel#settingsFieldHelp' in source
    assert 'QLabel#settingsSectionTitle' in source
