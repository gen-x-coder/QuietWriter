import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_windows_writing_font_uses_grayscale_antialiasing_and_full_hinting():
    source = read('quietwriter/typography.py')
    assert "sys.platform.startswith('win')" in source
    assert 'QFont.HintingPreference.PreferFullHinting' in source
    assert 'QFont.StyleStrategy.PreferAntialias' in source
    assert 'QFont.StyleStrategy.NoSubpixelAntialias' in source
    assert 'return tune_writing_font(font)' in source


def test_font_preview_uses_same_writing_typography_as_editor():
    source = read('quietwriter/ui/settings_page.py')
    assert 'typography_from_values(family, max(14, size)).body_font()' in source
    assert 'self.font_preview.setFont(font)' in source


def test_publication_pages_have_explicit_dirty_save_actions():
    editor = read('quietwriter/ui/publication/publication_editor.py')
    contents = read('quietwriter/ui/publication/contents_page.py')
    copyright_page = read('quietwriter/ui/publication/copyright_page.py')
    themes = read('quietwriter/themes.py')

    assert "self.save_button=QPushButton(tr('common.save', 'Opslaan'))" in editor
    assert 'self.save_button.setEnabled(False)' in editor
    assert 'self.dirty=True; self.save_button.setEnabled(True); self.timer.start()' in editor
    assert "self.save_button = QPushButton(tr('common.save', 'Opslaan'))" in contents
    assert 'self.save_button.setEnabled(True)' in contents
    assert "self.save_button=QPushButton(tr('common.save', 'Opslaan'))" in copyright_page
    assert 'self.save_button.setEnabled(True)' in copyright_page
    assert 'QPushButton#primaryButton:disabled' in themes


def test_history_and_trash_have_keyboard_and_selection_polish():
    history = read('quietwriter/ui/history_panel.py')
    trash = read('quietwriter/ui/trash_page.py')
    assert 'self.list.itemActivated.connect(self._clicked)' in history
    assert "tr('history.today', 'Vandaag')" in history
    assert "number_locale.toString(int(row.get('words', 0)))" in history
    assert 'self.list.itemSelectionChanged.connect(self._update_actions)' in trash
    assert 'self.list.itemActivated.connect(lambda _item: self.restore_selected())' in trash
    assert 'self.restore_btn.setEnabled(has_selection)' in trash
    assert 'self.delete_btn.setEnabled(has_selection)' in trash


def test_noninteractive_scene_cards_do_not_advertise_clickability():
    themes = read('quietwriter/themes.py')
    assert 'QFrame#sceneCard {' in themes
    assert 'QFrame#sceneCard:hover' not in themes


def test_remaining_polish_locale_keys_exist_in_both_languages():
    required = {
        'planning.nav.characters', 'planning.nav.outline', 'planning.nav.notes',
        'planning.characters.title', 'planning.characters.new', 'common.save',
        'publication.setup.title', 'publication.setup.done', 'publication.saved',
        'publication.item.title_page', 'publication.item.contents',
        'editor.tree.front', 'editor.tree.book', 'editor.tree.back',
        'history.title', 'history.today', 'history.restore_confirm',
        'trash.title', 'trash.restore', 'trash.delete_confirm', 'trash.empty_confirm',
    }
    for language in ('nl', 'en'):
        data = json.loads(read(f'quietwriter/locales/{language}.json'))
        missing = required - set(data)
        assert not missing, f'{language} mist locale-keys: {sorted(missing)}'
