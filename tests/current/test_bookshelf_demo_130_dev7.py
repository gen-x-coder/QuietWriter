from pathlib import Path


def bookshelf_source():
    return Path('quietwriter/ui/bookshelf.py').read_text(encoding='utf-8')


def test_bookshelf_uses_bookcase_copy_and_demo_toggle():
    text = bookshelf_source()
    assert "tr('bookshelf.title', 'Boekenkast')" in text
    assert "self.demo_toggle = QPushButton()" in text
    assert "self._update_demo_toggle()" in text
    assert "self.settings.setValue('bookshelf_demo_mode', enabled)" in text


def test_demo_filters_books_and_shelves_before_rendering():
    text = bookshelf_source()
    assert 'visible_book_ids = self.library.shelves.visible_book_ids(' in text
    assert 'visible_shelf_ids = set(self.library.shelves.visible_shelf_ids(' in text
    assert 'visible_shelves = tuple(s for s in loaded.state.shelves if s.id in visible_shelf_ids)' in text
    assert 'visible_shelves,' in text


def test_demo_hides_unreadable_book_error_names():
    text = bookshelf_source()
    assert "load_errors = [] if demo_mode else" in text


def test_related_pages_use_demo_visibility():
    darlings = Path('quietwriter/ui/darlings_page.py').read_text(encoding='utf-8')
    trash = Path('quietwriter/ui/trash_page.py').read_text(encoding='utf-8')
    assert 'self.main.start.demo_mode_enabled()' in darlings
    assert 'visible_book_ids(source_ids, demo_mode=True)' in darlings
    assert 'self.main.start.demo_mode_enabled()' in trash
    assert "visible_book_ids([row.get(\'book_id\')], demo_mode=True)" in trash


def test_demo_toggle_has_explicit_on_off_status():
    text = bookshelf_source()
    assert "bookshelf.demo_mode.on" in text
    assert "bookshelf.demo_mode.off" in text
    themes = Path('quietwriter/themes.py').read_text(encoding='utf-8')
    assert 'QPushButton#secondaryButton:checked' in themes
