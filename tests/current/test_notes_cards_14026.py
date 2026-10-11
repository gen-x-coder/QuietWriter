from pathlib import Path


def test_notes_responsive_grid_and_title_safety():
    source = Path('quietwriter/ui/planning/notes_page.py').read_text(encoding='utf-8')
    assert 'QGridLayout' in source
    assert 'self.card_scroll.viewport().installEventFilter(self)' in source
    assert 'self._card_columns()' in source
    assert 'index // columns, index % columns' in source
    assert 'title_field.textChanged.connect' in source
    assert 'save_button.setEnabled(bool(title_field.text().strip()))' in source
