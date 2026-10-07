from __future__ import annotations

"""Shared writer-visible manuscript projections for non-rendering consumers.

This module keeps word count, search text and AI context out of the media layer.
The semantic work remains owned by :mod:`quietwriter.document_view`; these small
functions are the stable consumer-facing boundary.
"""

from .document_view import count_visible_words, text_for_ai_context, visible_text


def count_words(source: str) -> int:
    return count_visible_words(source or '')


def text_for_search(source: str) -> str:
    return visible_text(source or '')


def text_for_ai(source: str) -> str:
    return text_for_ai_context(source or '')
