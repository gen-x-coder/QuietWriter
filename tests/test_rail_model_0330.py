from itertools import product
from pathlib import Path

from quietwriter.ui.rail_model import (
    RAIL_GROUPS,
    RAIL_ITEMS,
    RailState,
    build_rail_view,
    fallback_destination,
)


ROOT = Path(__file__).resolve().parents[1]


def test_manual_expected_cold_start():
    view = build_rail_view(RailState(False, True, True))
    assert view.visible_items == ('bookshelf', 'persona', 'settings', 'trash')
    assert view.visible_groups == ('library', 'program')


def test_manual_expected_open_book_everything_on():
    view = build_rail_view(RailState(True, True, True))
    assert view.visible_items == (
        'bookshelf',
        'contents', 'planning', 'media', 'book_details', 'export', 'integrity',
        'book_memory', 'book_profile',
        'persona', 'settings', 'trash',
    )
    assert view.visible_groups == ('library', 'current_book', 'ai_context', 'program')


def test_manual_expected_open_book_ai_and_advanced_off():
    view = build_rail_view(RailState(True, False, False))
    assert view.visible_items == (
        'bookshelf',
        'contents', 'planning', 'media', 'book_details', 'export',
        'settings', 'trash',
    )
    assert view.visible_groups == ('library', 'current_book', 'program')


def test_rail_invariants_for_every_effective_state():
    item_by_key = {item.key: item for item in RAIL_ITEMS}
    group_keys = {group.key for group in RAIL_GROUPS}
    assert len(item_by_key) == len(RAIL_ITEMS)

    for has_book, ai_enabled, advanced in product((False, True), repeat=3):
        state = RailState(has_book, ai_enabled, advanced)
        view = build_rail_view(state)
        visible = set(view.visible_items)
        groups = set(view.visible_groups)

        assert groups <= group_keys
        for group in groups:
            assert any(item_by_key[key].group == group for key in visible)
        for key in visible:
            assert item_by_key[key].group in groups

        if not has_book:
            assert not any(item_by_key[key].requires_book for key in visible)
        if not ai_enabled:
            assert 'persona' not in visible
            assert 'book_memory' not in visible
            assert 'book_profile' not in visible
            assert 'ai_context' not in groups
        if not advanced:
            assert 'integrity' not in visible


def test_fallback_destination_is_central_and_deterministic():
    open_no_ai = RailState(True, False, True)
    closed = RailState(False, True, True)
    assert fallback_destination('book_memory', open_no_ai) == 'contents'
    assert fallback_destination('integrity', RailState(True, True, False)) == 'contents'
    assert fallback_destination('contents', closed) == 'bookshelf'
    assert fallback_destination('settings', open_no_ai) == 'settings'


def test_renderer_is_visibility_only_and_commit_owns_side_effects():
    source = (ROOT / 'quietwriter' / 'ui' / 'main_window.py').read_text(encoding='utf-8')
    render = source[source.index('    def _render_rail'):source.index('    def _render_feature_buttons')]
    assert '.setVisible(' in render
    assert 'setCurrentWidget' not in render
    assert '.right.' not in render
    assert 'QSettings' not in render
    assert 'self.settings' not in render

    commit = source[source.index('    def _apply_committed_navigation_effects'):source.index('    def _set_feature_visibility')]
    assert 'fallback_destination' in commit
    assert 'setCurrentWidget' in commit
    assert 'self.editor_page.right.hide()' in commit


def test_left_rail_uses_scroll_container_and_reserved_width():
    source = (ROOT / 'quietwriter' / 'ui' / 'main_window.py').read_text(encoding='utf-8')
    assert "self.rail_scroll = QScrollArea()" in source
    assert 'self.rail_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)' in source
    assert 'button_width = 194 if self.rail_expanded else 48' in source
