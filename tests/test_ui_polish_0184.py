from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
BOOKSHELF = ROOT / 'quietwriter' / 'ui' / 'bookshelf.py'


def test_bookshelf_uses_centered_content_axis_and_responsive_grid():
    source = BOOKSHELF.read_text(encoding='utf-8')
    assert 'CONTENT_MAX_WIDTH = 1440' in source
    assert 'scroll.setAlignment(Qt.AlignTop | Qt.AlignHCenter)' in source
    assert "self.cards_host.setMaximumWidth(CONTENT_MAX_WIDTH)" in source
    assert "self.grid.setAlignment(Qt.AlignTop | Qt.AlignHCenter)" in source
    assert 'columns = max(1' in source


def test_bookshelf_cards_and_new_card_share_dimensions():
    source = BOOKSHELF.read_text(encoding='utf-8')
    assert 'CARD_WIDTH = 210' in source
    assert 'CARD_HEIGHT = 400' in source
    assert "self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)" in source
    assert "create.setFixedSize(CARD_WIDTH, CARD_HEIGHT)" in source


def test_bookshelf_sorting_is_locale_independent():
    source = BOOKSHELF.read_text(encoding='utf-8')
    assert 'self.sorting.addItem' in source
    assert 'self.sorting.currentData()' in source
    assert "order == 'title_az'" in source
    assert "order == 'title_za'" in source
    assert "order == 'words'" in source


def test_bookshelf_strings_exist_in_both_locales():
    keys = (
        'bookshelf.title', 'bookshelf.subtitle', 'bookshelf.open', 'bookshelf.words',
        'bookshelf.count.one', 'bookshelf.count.many', 'bookshelf.sort.recent',
        'bookshelf.sort.title_az', 'bookshelf.sort.title_za', 'bookshelf.sort.words',
        'bookshelf.search.placeholder', 'bookshelf.no_results', 'bookshelf.new_book',
        'bookshelf.create', 'bookshelf.import',
    )
    for locale in ('nl', 'en'):
        data = json.loads((ROOT / 'quietwriter' / 'locales' / f'{locale}.json').read_text(encoding='utf-8'))
        for key in keys:
            assert data.get(key)
