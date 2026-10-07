from __future__ import annotations

import re
from dataclasses import dataclass

from .manuscript_syntax import escape_ranges

MANUSCRIPT_SYNTAX_KEY = 'manuscript_syntax'
CURRENT_MANUSCRIPT_SYNTAX_VERSION = 2
CURRENT_MANUSCRIPT_SYNTAX_FEATURES = frozenset({'escape-v1', 'soft-break-u2028'})


class ManuscriptSyntaxError(RuntimeError):
    pass


class FutureManuscriptSyntaxError(ManuscriptSyntaxError):
    pass


class AmbiguousManuscriptSyntaxError(ManuscriptSyntaxError):
    pass


@dataclass(frozen=True)
class ManuscriptSyntaxProfile:
    version: int
    features: frozenset[str]
    explicit: bool = True

    @property
    def is_current(self) -> bool:
        return (
            self.explicit
            and self.version == CURRENT_MANUSCRIPT_SYNTAX_VERSION
            and self.features == CURRENT_MANUSCRIPT_SYNTAX_FEATURES
        )


@dataclass(frozen=True)
class ManuscriptSyntaxMigration:
    changed_chapters: int
    escaped_backslashes: int
    mode: str = 'legacy'


# Delimiters that only the escape-aware editor (1.2.19+) deliberately wrote.
# A doubled backslash is excluded because it is ambiguous with legacy UNC/path
# prose and is handled separately.
_ESCAPE_ERA_INLINE_RE = re.compile(r"\\[*~`<]")
_ESCAPE_ERA_STRUCTURAL_RE = re.compile(r"(?m)^(?:\\[-*>#]|\\!|\d+\\\.\s)")


def has_escape_era_fingerprint(source: str) -> bool:
    """Return True when source contains a strong 1.2.19+ editor fingerprint."""
    text = source or ''
    return bool(_ESCAPE_ERA_INLINE_RE.search(text) or _ESCAPE_ERA_STRUCTURAL_RE.search(text))


def has_ambiguous_backslash_pairs(source: str) -> bool:
    """Return True for all-even backslash runs without a stronger fingerprint.

    Escape-aware QuietWriter doubles a writer-visible backslash. Legacy prose can
    also contain pairs (notably UNC paths), so this shape alone is ambiguous.
    """
    text = source or ''
    if not text or has_escape_era_fingerprint(text):
        return False
    saw_pair = False
    i = 0
    while i < len(text):
        if text[i] != '\\':
            i += 1
            continue
        j = i
        while j < len(text) and text[j] == '\\':
            j += 1
        run = j - i
        if run >= 2:
            saw_pair = True
        if run % 2:
            return False
        i = j
    return saw_pair


def migration_source_state(sources: list[str] | tuple[str, ...]) -> str:
    """Classify unversioned source as escape-era, legacy or ambiguous."""
    values = [str(item or '') for item in sources]
    if any(has_escape_era_fingerprint(item) for item in values):
        return 'escape-era'
    if any(has_ambiguous_backslash_pairs(item) for item in values):
        return 'ambiguous'
    return 'legacy'


def migrate_legacy_source_to_current(source: str) -> tuple[str, int]:
    """Preserve pre-escape visible text under the current escape grammar.

    Only backslashes that the *current* reader would hide need another slash.
    Unrelated legacy backslashes are left byte-for-byte alone. This is both safer
    and smaller than the old ``replace('\\', '\\\\')`` migration.
    """
    text = source or ''
    starts = {a for a, _b in escape_ranges(text)}
    if not starts:
        return text, 0
    out: list[str] = []
    for i, ch in enumerate(text):
        if i in starts:
            out.append('\\')
        out.append(ch)
    return ''.join(out), len(starts)


def current_manifest_value() -> dict:
    return {
        'version': CURRENT_MANUSCRIPT_SYNTAX_VERSION,
        'features': sorted(CURRENT_MANUSCRIPT_SYNTAX_FEATURES),
    }


def profile_from_manifest(data: dict) -> ManuscriptSyntaxProfile:
    """Read syntax capabilities without mutating an older manifest."""
    if not isinstance(data, dict):
        raise ManuscriptSyntaxError('book.json bevat geen JSON-object.')
    raw = data.get(MANUSCRIPT_SYNTAX_KEY)
    if raw is None:
        return ManuscriptSyntaxProfile(version=1, features=frozenset(), explicit=False)
    if not isinstance(raw, dict):
        raise ManuscriptSyntaxError('manuscript_syntax moet een JSON-object zijn.')
    version = raw.get('version')
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise ManuscriptSyntaxError(f'Ongeldige manuscriptsyntaxversie: {version!r}.')
    if version > CURRENT_MANUSCRIPT_SYNTAX_VERSION:
        raise FutureManuscriptSyntaxError(
            f'Dit boek gebruikt manuscriptsyntax {version}; deze QuietWriter ondersteunt maximaal '
            f'{CURRENT_MANUSCRIPT_SYNTAX_VERSION}.'
        )
    features_raw = raw.get('features', [])
    if not isinstance(features_raw, list) or not all(isinstance(item, str) and item for item in features_raw):
        raise ManuscriptSyntaxError('manuscript_syntax.features moet een lijst met niet-lege strings zijn.')
    features = frozenset(features_raw)
    unknown = features - CURRENT_MANUSCRIPT_SYNTAX_FEATURES
    if unknown:
        raise FutureManuscriptSyntaxError(
            'Dit boek gebruikt onbekende manuscriptfuncties: ' + ', '.join(sorted(unknown)) + '.'
        )
    return ManuscriptSyntaxProfile(version=version, features=features, explicit=True)
