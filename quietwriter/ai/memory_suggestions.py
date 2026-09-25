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
    r"\[\[QW_MEMORY\|(?P<key>[a-z_]+)\]\]\s*(?P<text>.*?)\s*\[\[/QW_MEMORY\]\]",
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
        if key not in _VALID_KEYS or not text:
            continue
        suggestions.append(MemorySuggestion(key, text))
        spans.append(match.span())

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
