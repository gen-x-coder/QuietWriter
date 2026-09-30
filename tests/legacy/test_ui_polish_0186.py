from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def test_opening_book_selects_the_first_opened_chapter():
    source = (ROOT / 'quietwriter' / 'ui' / 'editor_page.py').read_text(encoding='utf-8')
    adopt = source[source.index('    def adopt_live_book'):source.index('    def _on_tree_drag_started')]
    assert 'next((c for section in book.sections for c in section.chapters), None)' in adopt
    assert 'self._set_editor_chapter(chapter)' in adopt
    assert 'self.select_tree_chapter(cid)' in adopt


def test_manuscript_selection_is_row_based_with_one_custom_accent():
    tree = (ROOT / 'quietwriter' / 'ui' / 'manuscript_tree.py').read_text(encoding='utf-8')
    theme = (ROOT / 'quietwriter' / 'themes.py').read_text(encoding='utf-8')
    assert 'self.setSelectionBehavior(QAbstractItemView.SelectRows)' in tree
    assert "data[0] == 'chapter'" in tree
    assert 'painter.drawLine(x, selection_rect.top() + 3, x, selection_rect.bottom() - 3)' in tree
    assert "QTreeWidget#manuscriptTree::item:selected {{ border-left" not in theme
    assert 'QTreeWidget#manuscriptTree::item {{ border-radius: 0px; }}' in theme


def test_ai_can_be_disabled_without_discarding_configuration():
    settings = (ROOT / 'quietwriter' / 'ui' / 'settings_page.py').read_text(encoding='utf-8')
    main = (ROOT / 'quietwriter' / 'ui' / 'main_window.py').read_text(encoding='utf-8')
    editor = (ROOT / 'quietwriter' / 'ui' / 'editor_page.py').read_text(encoding='utf-8')
    assert "settings.value('ai_enabled', True, bool)" in settings
    assert "'ai_enabled': self.ai_enabled.isChecked()" in settings
    assert 'for control in self._ai_controls:' in settings
    rail = (ROOT / 'quietwriter' / 'ui' / 'rail_model.py').read_text(encoding='utf-8')
    assert 'self.ai_button.setVisible(bool(ai_enabled))' in main
    assert "RailItemSpec('persona', 'program', requires_ai=True)" in rail
    assert "RailItemSpec('book_profile', 'ai_context', requires_book=True, requires_ai=True)" in rail
    assert "RailItemSpec('book_memory', 'ai_context', requires_book=True, requires_ai=True)" in rail
    assert "if not self.main.settings.value('ai_enabled', True, bool):" in editor


def test_ai_enable_copy_exists_in_both_locales():
    for language in ('nl', 'en'):
        data = json.loads((ROOT / 'quietwriter' / 'locales' / f'{language}.json').read_text(encoding='utf-8'))
        assert data['settings.ai.enable']
        assert data['settings.ai.enable_help']
        assert data['settings.section.ai_usage']
        assert 'QuietWriter' in data['settings.ai.intro']
