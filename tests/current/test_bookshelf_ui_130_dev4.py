from pathlib import Path


def source():
    return Path('quietwriter/ui/bookshelf.py').read_text(encoding='utf-8')


def test_shelf_cards_wrap_without_horizontal_scroll_area():
    text = source()
    assert 'class _WrappingCardHost' in text
    assert "scroll.setObjectName('shelfBookScroll')" not in text
    assert 'outer.addWidget(_WrappingCardHost(cards))' in text


def test_book_actions_is_a_full_button_below_open():
    text = source()
    assert "actions_btn = QPushButton(tr('bookshelf.book.actions', 'Boekacties'))" in text
    assert 'lay.addWidget(open_btn)' in text
    assert 'lay.addWidget(actions_btn)' in text


def test_bookshelf_yes_no_dialog_uses_translations():
    text = source()
    assert "yes.setText(tr('common.yes', 'Ja'))" in text
    assert "no.setText(tr('common.no', 'Nee'))" in text
    assert 'QMessageBox.question(' not in text
