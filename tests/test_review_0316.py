from pathlib import Path


def block(source: str, start: str, end: str) -> str:
    i = source.index(start)
    return source[i:source.index(end, i)]


def test_memory_and_profile_preflight_preserve_dirty_local_text_when_disk_utf8_is_corrupt():
    cases = {
        'book_memory_page.py': ('ai/memory.md', 'render_book_memory(local_memory)'),
        'book_profile_page.py': ('ai/boekprofiel.md', 'render_book_profile(local_profile)'),
    }
    for filename, (relative, renderer) in cases.items():
        source = (Path('quietwriter/ui') / filename).read_text(encoding='utf-8')
        prepare = block(source, '    def prepare_adoption(', '    def adopt_book(')
        assert 'except UnicodeDecodeError:' in prepare
        assert "'mode': 'corrupt'" in prepare
        assert "kind='conflict_local'" in prepare
        assert relative in prepare
        assert renderer in prepare


def test_memory_and_profile_corrupt_plan_commits_readonly_without_merge_write():
    for filename in ('book_memory_page.py', 'book_profile_page.py'):
        source = (Path('quietwriter/ui') / filename).read_text(encoding='utf-8')
        adopt = block(source, '    def adopt_book(', '    def show_adoption_message')
        assert "plan.get('mode') == 'corrupt'" in adopt
        assert 'self.set_book(book, force=True)' in adopt
        assert 'create_version_with_file_overrides' not in adopt


def test_memory_and_profile_detect_corrupt_source_before_showing_normal_conflict_dialog():
    cases = {
        'book_memory_page.py': 'read_book_memory(self.book)',
        'book_profile_page.py': 'read_book_profile(self.book)',
    }
    for filename, read_call in cases.items():
        source = (Path('quietwriter/ui') / filename).read_text(encoding='utf-8')
        resolve = block(source, '    def _resolve_external_change(', '        changed =')
        assert read_call in resolve
        assert 'except UnicodeDecodeError:' in resolve
        assert 'self.main.adopt_active_book(latest, preferred_chapter_id)' in resolve


def test_planning_notes_corruption_is_preserved_in_main_preflight_and_not_restored_dirty():
    main = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    prepare = block(main, '    def _prepare_active_book_adoption', '    def preserve_local_and_close_future_book')
    assert 'planning_notes_corrupt = False' in prepare
    assert "{'planning/notes.md': notes_page.editor.toPlainText()}" in prepare
    assert "kind='conflict_local'" in prepare
    assert "'planning_notes_corrupt_preserved': planning_notes_corrupt_preserved" in prepare

    adopt = block(main, '    def adopt_active_book', '    def _prepare_active_book_adoption')
    assert "planning_changed.add('planning/notes.md')" in adopt
    assert 'show_corrupt_adoption_message()' in adopt


def test_planning_notes_corrupt_source_bypasses_normal_mine_disk_dialog():
    source = Path('quietwriter/ui/planning/planning_page.py').read_text(encoding='utf-8')
    resolve = block(source, '    def _resolve_external_change(', '        # A modal conflict dialog')
    assert "if kind == 'notes':" in resolve
    assert 'self.store.load_notes(self.book)' in resolve
    assert 'except UnicodeDecodeError:' in resolve
    assert "changed_files.add('planning/notes.md')" in resolve
    assert 'self.main.adopt_active_book(' in resolve
