from pathlib import Path


def test_planning_pages_have_explanations_and_names_only():
    chars = Path("quietwriter/ui/planning/characters_page.py").read_text(encoding="utf-8")
    outline = Path("quietwriter/ui/planning/outline_page.py").read_text(encoding="utf-8")
    assert "planning.characters.page_description" in chars
    assert "planning.outline.description" in outline
    assert "QListWidgetItem(c.name)" in chars
    assert "f'\\n{c.role}'" not in chars


def test_context_navigation_uses_page_background():
    editor = Path("quietwriter/ui/editor_page.py").read_text(encoding="utf-8")
    themes = Path("quietwriter/themes.py").read_text(encoding="utf-8")
    assert "manuscriptSidebar" in editor
    assert "QFrame#planningSidebar {{ background: {t['bg']}" in themes
    assert "QFrame#planningListPanel {{ background: {t['bg']}" in themes
    assert "QWidget#manuscriptSidebar {{ background: {t['bg']}" in themes
    assert "QTreeWidget#manuscriptTree {{ background: transparent" in themes
