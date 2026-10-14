from __future__ import annotations

from dataclasses import dataclass
import re

from ..book_memory import SECTIONS


@dataclass(frozen=True)
class MemorySuggestion:
    section_key: str
    text: str


_VALID_KEYS = {section.key for section in SECTIONS}
_BLOCK_RE = re.compile(
    r"\[\[\s*QW_MEMORY\s*\|\s*(?P<key>[a-z_]+)\s*\]\]\s*(?P<text>.*?)\s*\[\[\s*/QW_MEMORY\s*\]\]",
    flags=re.IGNORECASE | re.DOTALL,
)


def extract_memory_suggestions(response: str) -> tuple[str, list[MemorySuggestion]]:
    """Strip QuietWriter memory proposal blocks from model-visible output.

    The format is intentionally tiny and line-oriented so small local models can
    produce it without JSON/function-calling support. Invalid/empty blocks are
    left visible instead of being silently interpreted.
    """
    source = response or ''
    suggestions: list[MemorySuggestion] = []
    spans: list[tuple[int, int]] = []
    for match in _BLOCK_RE.finditer(source):
        key = match.group('key').lower()
        text = match.group('text').strip()
        # Hide every complete internal marker, even when invalid or beyond the
        # two proposal limit. Never show raw protocol tokens to the writer.
        spans.append(match.span())
        if key in _VALID_KEYS and text and len(suggestions) < 2:
            suggestions.append(MemorySuggestion(key, text))

    if not spans:
        return source.strip(), []

    chunks: list[str] = []
    cursor = 0
    for start, end in spans:
        chunks.append(source[cursor:start])
        cursor = end
    chunks.append(source[cursor:])
    visible = ''.join(chunks)
    visible = re.sub(r'\n{3,}', '\n\n', visible).strip()
    return visible, suggestions


def proposal_instruction() -> str:
    return (
        "Als tijdens het gesprek nieuwe, blijvend bruikbare kennis voor dit boek expliciet wordt "
        "vastgesteld, mag je maximaal twee geheugenvoorstellen toevoegen. Doe dit alleen voor "
        "duurzame feiten, bewuste schrijfbesluiten, boekspecifieke stijlregels, terugkerende voorkeuren "
        "of open aandachtspunten; niet voor speculatie of gegevens die al in Planning horen. "
        "Gebruik exact dit verborgen formaat, na je normale antwoord:\n"
        "[[QW_MEMORY|canon]]tekst[[/QW_MEMORY]]\n"
        "Geldige categorieën zijn canon, book_style, decisions, preferences en open_points. "
        "Voeg geen blok toe als er niets zinvols te onthouden is."
    )


def visible_stream_text(response: str) -> str:
    """Do not flash internal memory instructions in the live chat.

    Models can send the opening marker token by token, so hiding only the
    complete marker leaks partial markup. Keep any possible marker prefix hidden
    until the stream establishes whether it is ordinary user-facing text.
    """
    source = response or ''
    marker = '[[QW_MEMORY'
    upper = source.upper()
    complete = upper.find(marker)
    if complete >= 0:
        return source[:complete].rstrip()
    # A streaming response can stop partway through the private tag.
    for size in range(min(len(marker) - 1, len(source)), 1, -1):
        if upper.endswith(marker[:size]):
            return source[:-size].rstrip()
    return source
