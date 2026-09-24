from pathlib import Path
import tempfile

from quietwriter.storage import Library

ROOT = Path(__file__).resolve().parents[1]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')


def test_touch_book_never_writes_stale_bookshelf_structure_back():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td))
        book = lib.create_book('Dropbox test')
        stale = lib.load_book(book.path)

        # Simulate another computer adding a chapter after the bookshelf loaded.
        external = lib.load_book(book.path)
        second = lib.add_chapter(external, external.sections[0], 'Van computer B')
        lib.save_chapter(external, second, 'extern')

        touched = lib.touch_book(stale)
        reloaded = lib.load_book(book.path)
        titles = [c.title for section in reloaded.sections for c in section.chapters]

        assert 'Van computer B' in titles
        assert any(c.id == second.id for section in touched.sections for c in section.chapters)
        assert touched is not stale


def test_main_window_has_one_central_active_book_adoption_path():
    source = _source('quietwriter/ui/main_window.py')
    assert 'self._active_book = None' in source
    assert 'def active_book(self):' in source
    adopt = source[source.index('    def adopt_active_book'):source.index('    def _nav_button')]
    assert 'self._active_book = book' in adopt
    assert 'self.editor_page.adopt_live_book(book, preferred_chapter_id)' in adopt
    assert 'self.planning_page.adopt_book(book, reload_kind=planning_reload_kind)' in adopt
    assert 'self._replace_book_details_page(book)' in adopt
    assert 'self.export_page.set_book(book)' in adopt


def test_planning_conflict_uses_three_way_outcome_and_central_adoption():
    planning = _source('quietwriter/ui/planning/planning_page.py')
    assert "return 'mine'" in planning
    assert "result='disk'" in planning
    assert "return 'failed'" in planning
    assert 'self.main.adopt_active_book(latest, preferred_chapter_id, planning_reload_kind=kind)' in planning

    characters = _source('quietwriter/ui/planning/characters_page.py')
    outline = _source('quietwriter/ui/planning/outline_page.py')
    assert "if result == 'failed':" in characters
    assert "if result == 'disk':" in characters
    assert "if result == 'failed': self.scenes=before" in outline
    # Disk acceptance must not restore the old in-memory scene snapshot.
    assert "if result != 'mine': self.scenes=before" not in outline


def test_editor_conflict_and_publication_conflict_adopt_central_live_book():
    source = _source('quietwriter/ui/editor_page.py')
    adopt_disk = source[source.index('    def _adopt_disk_book'):source.index('    def _ensure_current_chapter_in')]
    assert 'self.main.adopt_active_book(latest, preferred_chapter_id)' in adopt_disk

    persist = source[source.index('    def persist_publication_change'):source.index('    def _set_publication_context')]
    assert 'self.main.adopt_active_book(latest, preferred_chapter_id)' in persist


def test_book_details_identity_is_refreshed_on_live_book_adoption():
    source = _source('quietwriter/ui/main_window.py')
    details = source[source.index('    def open_current_book_details'):source.index('    def show_export')]
    assert 'self.book_details_page.book is not book' in details
    replace = source[source.index('    def _replace_book_details_page'):source.index('    def open_current_book_details')]
    assert 'was_current' in replace
