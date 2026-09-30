"""Regression coverage for QuietWriter 0.22.7 review-round-4 fixes."""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from quietwriter.media.markup import is_searchable_range, replace_searchable_text, searchable_matches
from quietwriter.storage import Library

ROOT = Path(__file__).resolve().parents[2]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')


def test_legacy_cover_with_empty_cover_file_is_migrated_if_media_manifest_is_absent():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td) / 'workspace')
        old = lib.create_book('Zomer')
        # Simulate a pre-0.20 book that was later opened by a release which wrote
        # cover_file="" but did not create the 0.20+ book-local media marker.
        data = json.loads(old.manifest_path.read_text(encoding='utf-8'))
        data['metadata']['cover_file'] = ''
        old.manifest_path.write_text(json.dumps(data), encoding='utf-8')
        (old.path / 'assets' / 'manifest.json').unlink()
        legacy = lib.covers_dir / 'zomer.jpg'
        legacy.write_bytes(b'legacy-cover')

        loaded = lib.load_book(old.path)
        assert loaded.metadata['cover_file'] == 'zomer.jpg'
        assert lib.cover_path(loaded) == legacy

        # A normal touch persists the one-time explicit ownership migration.
        touched = lib.touch_book(loaded)
        stored = json.loads(touched.manifest_path.read_text(encoding='utf-8'))
        assert stored['metadata']['cover_file'] == 'zomer.jpg'


def test_new_book_with_same_slug_never_adopts_global_legacy_cover():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td) / 'workspace')
        legacy = lib.covers_dir / 'zomer.jpg'
        legacy.write_bytes(b'legacy-cover')
        fresh = lib.create_book('Zomer')
        loaded = lib.load_book(fresh.path)
        assert (fresh.path / 'assets' / 'manifest.json').exists()
        assert loaded.metadata['cover_file'] == ''
        assert lib.cover_path(loaded) is None


def test_search_replace_rejects_matches_that_touch_image_boundary_syntax():
    source = '![Een foto](../assets/images/abc.png "Mijn foto")'

    right_edge = re.compile(re.escape('foto '), re.IGNORECASE)
    left_edge = re.compile(re.escape(' Een'), re.IGNORECASE)

    assert searchable_matches(source, right_edge) == []
    assert searchable_matches(source, left_edge) == []
    assert replace_searchable_text(source, right_edge, 'beeld ') == source
    assert replace_searchable_text(source, left_edge, 'Het') == source


def test_visible_alt_and_caption_text_remain_replaceable():
    source = '![Een foto](../assets/images/abc.png "Mijn foto")'
    changed = replace_searchable_text(source, re.compile(re.escape('foto'), re.IGNORECASE), 'beeld')
    assert changed == '![Een beeld](../assets/images/abc.png "Mijn beeld")'
    assert is_searchable_range(source, source.index('foto'), source.index('foto') + 4)


def test_editor_collect_and_current_replace_use_protected_range_filter():
    source = _source('quietwriter/ui/editor_page.py')
    collect = source.split('    def collect_search_matches(self):', 1)[1].split('    def do_search(self):', 1)[0]
    current = source.split('    def replace_current_match(self):', 1)[1].split('    def replace_all_matches(self):', 1)[0]
    assert 'searchable_matches(text, rx)' in collect
    assert 'is_searchable_range(source, cur.selectionStart(), cur.selectionEnd())' in current


def test_planning_same_book_adoption_preserves_unrelated_pending_state():
    planning = _source('quietwriter/ui/planning/planning_page.py')
    assert 'def adopt_book(self, book, *, reload_kind=None, changed_files=None):' in planning
    assert "reload_kind != 'notes' and self.notes_page.dirty" in planning
    assert "reload_kind != 'characters'" in planning
    assert 'self.notes_page.restore_pending_text(pending_notes)' in planning
    assert 'self.characters_page.restore_editor_snapshot(pending_character)' in planning
    assert 'planning_reload_kind=kind' in planning
    assert "overrides['planning/notes.md']" in planning
    assert 'self.notes_page.timer.stop()' in planning

    characters = _source('quietwriter/ui/planning/characters_page.py')
    assert 'def pending_editor_snapshot(self):' in characters
    assert 'def restore_editor_snapshot(self, snapshot):' in characters


def test_book_details_navigation_saves_editor_and_same_book_adopt_preserves_dirty_form():
    main = _source('quietwriter/ui/main_window.py')
    open_details = main.split('    def open_current_book_details(self):', 1)[1].split('    def show_export(self):', 1)[0]
    adopt = main.split('    def adopt_active_book', 1)[1].split('    def _nav_button', 1)[0]
    assert 'if self.editor_page.save() is False: return' in open_details
    assert 'details.has_pending_changes()' in adopt
    assert 'details.adopt_book_preserving_form(' in adopt and "prepared=prepared['details']" in adopt

    details = _source('quietwriter/ui/book_details.py')
    assert 'def has_pending_changes(self) -> bool:' in details
    assert 'def adopt_book_preserving_form(self, book, *, prepared=None, show_message: bool = True):' in details
    assert 'merge_scalar_fields(current, previous, incoming, keys)' in details
    assert 'self._apply_form_values(merged)' in details
    assert "{'book.json': self.library.manifest_text(local_candidate)}" in details
