from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')


def _method(source: str, name: str, next_name: str) -> str:
    start = source.index(f'    def {name}')
    end = source.index(f'    def {next_name}', start)
    return source[start:end]


def test_main_window_closes_history_preview_when_leaving_editor():
    source = _source('quietwriter/ui/main_window.py')
    block = _method(source, '_mode_changed', '_leave_settings_preview')
    assert 'if not in_editor and self.editor_page.preview_live_book:' in block
    assert 'self.editor_page.exit_history_preview()' in block


def test_search_replace_is_read_only_during_history_preview():
    source = _source('quietwriter/ui/editor_page.py')
    current = _method(source, 'replace_current_match', 'replace_all_matches')
    all_matches = _method(source, 'replace_all_matches', '_remember_panel_widths')
    assert 'if self.preview_live_book:' in current
    assert 'return' in current.split("q=self.search.query.text()", 1)[0]
    assert 'if self.preview_live_book:' in all_matches
    assert 'return' in all_matches.split('rows=self.collect_search_matches()', 1)[0]


def test_spell_change_is_read_only_during_history_preview():
    source = _source('quietwriter/ui/spell_panel.py')
    block = _method(source, 'change', 'ignore')
    assert 'if self.editor_page.preview_live_book:' in block
    assert 'return' in block.split('if not self.rows', 1)[0]


def test_normal_conflict_resolver_never_operates_on_archive_snapshot():
    source = _source('quietwriter/ui/editor_page.py')
    block = _method(source, '_resolve_external_change', '_handle_verification_error')
    preview_guard = block.index('if self.preview_live_book:')
    drag_guard = block.index('if self.tree.is_dragging:')
    assert preview_guard < drag_guard
    assert 'self.exit_history_preview(reload_latest=True)' in block[:drag_guard]


def test_restore_conflict_has_dedicated_preview_safe_path():
    source = _source('quietwriter/ui/editor_page.py')
    block = _method(source, 'restore_preview_version', 'show_history')
    external = block[block.index('except ExternalModificationError:'):block.index('except RevisionVerificationError')]
    assert 'self.exit_history_preview(reload_latest=True)' in external
    assert '_handle_concurrency_issue' not in external
    assert 'Herstel is niet uitgevoerd' in external
    assert 'self.main.adopt_active_book(restored, wanted)' in block


def test_preview_exit_does_not_retrack_stale_live_book_on_normal_exit():
    source = _source('quietwriter/ui/editor_page.py')
    block = _method(source, 'exit_history_preview', 'restore_preview_version')
    assert 'if reloaded:' in block
    assert 'self.main.adopt_active_book(adopted, wanted)' in block
    assert 'self._rebind_live_editor_after_preview(adopted, wanted)' in block
    assert 'Never re-track a stale in-memory Book' in block
