from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_scene_fields_visible_and_taller():
    source = (ROOT / 'quietwriter/ui/planning/outline_page.py').read_text(encoding='utf-8')
    assert 'e.setFixedHeight(108)' in source
    assert 'form.addRow(field_label(tr(\'planning.outline.field.goal\'' in source  # dev15
    assert 'form.addRow(field_label(tr(\'planning.outline.field.notes\'' in source


def test_notes_keep_original_markdown_storage():
    source = (ROOT / 'quietwriter/ui/planning/notes_page.py').read_text(encoding='utf-8')
    store = (ROOT / 'quietwriter/planning_storage.py').read_text(encoding='utf-8')
    assert '## ' in source and 'self.owner.persist_notes(source_text)' in source
    assert "self.root(book) / 'notes.md'" in store
    assert 'planning.notes.new' in source


def test_chapter_bars_use_subtle_accent():
    source = (ROOT / 'quietwriter/themes.py').read_text(encoding='utf-8')
    assert "border-left: 3px solid {t['accent']}" in source
