from pathlib import Path


def test_book_word_label_removed_from_contents_panel():
    source = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    assert 'self.book_words' not in source
    assert "book_text = f'Boek: {total:,}'" in source
    assert "chapter_text = f'Hoofdstuk {chapter_index} van {chapter_total}: {words:,}'" in source


def test_planning_validation_has_single_shared_validator():
    store = Path('quietwriter/planning_storage.py').read_text(encoding='utf-8')
    integrity = Path('quietwriter/integrity.py').read_text(encoding='utf-8')
    validator = Path('quietwriter/planning_validation.py').read_text(encoding='utf-8')
    assert 'validate_planning_payload' in store
    assert 'validate_planning_payload' in integrity
    assert 'class FuturePlanningFormatError' in validator
