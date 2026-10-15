"""Cloud sync hints and refresh must not mutate manuscripts."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtWidgets import QApplication
from quietwriter.storage import Library
from quietwriter.ui.bookshelf import StartPage

@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])

def test_bookshelf_refresh_tracks_later_book(app, tmp_path):
    library = Library(tmp_path / 'work')
    page = StartPage(library)
    try:
        assert page.refresh_button.text()
        initial = page._sync_signature
        book = library.create_book('Van andere computer')
        assert page._disk_book_signature() != initial
        page.show()
        app.processEvents()
        page._refresh_if_changed()
        assert page._sync_signature == page._disk_book_signature()
        assert '1' in page.count.text()
        assert (book.path / 'book.json').is_file()
    finally:
        page.close(); page.deleteLater(); app.processEvents()

def test_partial_metadata_and_conflict_are_non_destructive(app, tmp_path):
    library = Library(tmp_path / 'work')
    pending = library.books_dir / 'incomplete-book'
    pending.mkdir()
    book = library.create_book('Conflict')
    chapter = book.sections[0].chapters[0]
    conflict = book.path / 'chapters' / "chapter (conflicted copy).md"
    conflict.write_text('bewaar mij', encoding='utf-8')
    original = book.path / chapter.file
    before = original.read_bytes()
    page = StartPage(library)
    try:
        assert page.sync_hint.isVisible() or not page.isVisible()
        assert 'sync' in page.sync_hint.text().lower() or 'synchron' in page.sync_hint.text().lower()
        page.refresh_button.click()
        assert conflict.read_text(encoding='utf-8') == 'bewaar mij'
        assert original.read_bytes() == before
    finally:
        page.close(); page.deleteLater(); app.processEvents()
