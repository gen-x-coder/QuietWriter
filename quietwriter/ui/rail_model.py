from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class RailState:
    """Effective application state used to derive the left navigation."""

    has_book: bool
    ai_enabled: bool
    advanced_enabled: bool


@dataclass(frozen=True)
class RailItemSpec:
    key: str
    group: str
    requires_book: bool = False
    requires_ai: bool = False
    requires_advanced: bool = False

    def visible(self, state: RailState) -> bool:
        return (
            (not self.requires_book or state.has_book)
            and (not self.requires_ai or state.ai_enabled)
            and (not self.requires_advanced or state.advanced_enabled)
        )


@dataclass(frozen=True)
class RailGroupSpec:
    key: str
    title: str


@dataclass(frozen=True)
class RailViewModel:
    state: RailState
    visible_items: tuple[str, ...]
    visible_groups: tuple[str, ...]

    def is_item_visible(self, key: str) -> bool:
        return key in self.visible_items

    def is_group_visible(self, key: str) -> bool:
        return key in self.visible_groups


RAIL_GROUPS: tuple[RailGroupSpec, ...] = (
    RailGroupSpec('library', 'BIBLIOTHEEK'),
    RailGroupSpec('current_book', 'HUIDIG BOEK'),
    RailGroupSpec('ai_context', 'AI-CONTEXT'),
    RailGroupSpec('program', 'PROGRAMMA'),
)

# This is the single source of truth for left-rail membership and visibility.
# Rendering code must not add feature-specific conditions on top of this table.
RAIL_ITEMS: tuple[RailItemSpec, ...] = (
    RailItemSpec('bookshelf', 'library'),
    RailItemSpec('darlings', 'library'),
    RailItemSpec('contents', 'current_book', requires_book=True),
    RailItemSpec('planning', 'current_book', requires_book=True),
    RailItemSpec('media', 'current_book', requires_book=True),
    RailItemSpec('book_details', 'current_book', requires_book=True),
    RailItemSpec('export', 'current_book', requires_book=True),
    RailItemSpec('integrity', 'current_book', requires_book=True, requires_advanced=True),
    RailItemSpec('book_memory', 'ai_context', requires_book=True, requires_ai=True),
    RailItemSpec('book_profile', 'ai_context', requires_book=True, requires_ai=True),
    RailItemSpec('persona', 'program', requires_ai=True),
    RailItemSpec('settings', 'program'),
    RailItemSpec('trash', 'program'),
)


def build_rail_view(state: RailState) -> RailViewModel:
    visible_items = tuple(item.key for item in RAIL_ITEMS if item.visible(state))
    visible_set = set(visible_items)
    visible_groups = tuple(
        group.key
        for group in RAIL_GROUPS
        if any(item.group == group.key and item.key in visible_set for item in RAIL_ITEMS)
    )
    return RailViewModel(state, visible_items, visible_groups)


def fallback_destination(current_key: str | None, state: RailState) -> str:
    """Return a valid navigation destination when the current page disappears.

    A still-visible page is retained. Hidden book/AI/advanced pages fall back to
    Contents while a book is open, otherwise to the Bookshelf.
    """

    view = build_rail_view(state)
    if current_key and view.is_item_visible(current_key):
        return current_key
    return 'contents' if state.has_book else 'bookshelf'
