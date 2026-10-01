from __future__ import annotations

DEFAULT_TEXT_WIDTH = 'normal'
TEXT_WIDTHS = {
    'extra_narrow': 720,
    'narrow': 850,
    'normal': 1000,
    'wide': 1180,
    'extra_wide': 1360,
}


def normalize_text_width(value) -> str:
    value = str(value or DEFAULT_TEXT_WIDTH).strip().lower()
    return value if value in TEXT_WIDTHS else DEFAULT_TEXT_WIDTH


def text_width_pixels(value) -> int:
    return TEXT_WIDTHS[normalize_text_width(value)]
