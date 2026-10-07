from pathlib import Path


def test_live_theme_refreshes_item_level_manuscript_tree_colours():
    editor = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    assert 'def apply_tree_theme' in editor
    assert "item.setForeground(1, QColor(theme['accent']))" in editor
    main = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    assert 'self.editor_page.apply_tree_theme(theme_name)' in main
