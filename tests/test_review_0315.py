from pathlib import Path


def block(source: str, start: str, end: str) -> str:
    return source[source.index(start):source.index(end, source.index(start))]


def test_adopt_preflight_runs_before_any_page_rebind():
    source = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    adopt = block(source, '    def adopt_active_book', '    def _prepare_active_book_adoption')
    assert adopt.index('prepared = self._prepare_active_book_adoption') < adopt.index('self.editor_page.adopt_live_book')
    assert "prepared=prepared['profile']" in adopt
    assert "prepared=prepared['memory']" in adopt
    assert "prepared=prepared['details']" in adopt


def test_preflight_owns_conflict_recovery_writes():
    main = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    prepare = block(main, '    def _prepare_active_book_adoption', '    def preserve_local_and_close_future_book')
    assert 'self.book_profile_page.prepare_adoption(book)' in prepare
    assert 'self.book_memory_page.prepare_adoption(book)' in prepare
    assert 'details.prepare_adoption(book)' in prepare

    for filename in ('book_profile_page.py', 'book_memory_page.py', 'book_details.py'):
        source = Path('quietwriter/ui') / filename
        text = source.read_text(encoding='utf-8')
        assert 'def prepare_adoption(' in text
        prepare_start = text.index('    def prepare_adoption(')
        adopt_marker = '    def adopt_book_preserving_form(' if filename == 'book_details.py' else '    def adopt_book('
        prepare_end = text.index(adopt_marker, prepare_start)
        assert "kind='conflict_local'" in text[prepare_start:prepare_end]


def test_prepared_commit_has_no_recovery_write_and_notices_are_deferred():
    for filename in ('book_profile_page.py', 'book_memory_page.py'):
        text = (Path('quietwriter/ui') / filename).read_text(encoding='utf-8')
        adopt = block(text, '    def adopt_book(', '    def show_adoption_message')
        assert "kind='conflict_local'" not in adopt

    details = Path('quietwriter/ui/book_details.py').read_text(encoding='utf-8')
    adopt = block(details, '    def adopt_book_preserving_form(', '    def show_adoption_message')
    assert "kind='conflict_local'" not in adopt

    main = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    adopt_main = block(main, '    def adopt_active_book', '    def _prepare_active_book_adoption')
    assert adopt_main.index('self.library.track_book(book)') < adopt_main.index('show_adoption_message')
