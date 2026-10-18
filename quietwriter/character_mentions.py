"""Welke personages komen in een hoofdstuk voor? Alleen lezen, nooit hernoemen.

Een personage wordt herkend aan:
- de volledige naam ("Anna de Vries");
- de voornaam (eerste woord van de naam), als die met een hoofdletter begint
  en minstens drie letters heeft ("Anna");
- elke bijnaam uit het veld *Ook bekend als* ("An, mevrouw De Vries").

Een naam die bij meer dan één personage hoort (twee keer "Roos" als voornaam,
of dezelfde bijnaam) telt voor niemand: QuietWriter weet dan niet wie bedoeld
is. De volledige naam blijft wel werken.

Hoofdlettergevoelig en alleen hele woorden: "Roos" telt, "roos" en "Roosje" niet.
Dat mist soms een naam aan het begin van een zin die ook een gewoon woord is,
maar raakt nooit gewone woorden midden in een zin. Er wordt niets in de tekst
gemarkeerd of veranderd.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from .manuscript_text import text_for_search
from .placeholders import strip_open_point_markers

_ALIAS_SPLIT = re.compile(r'[,;\n]+')


def _term_sources(character) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(expliciet, automatisch): volledige naam en bijnamen, en de voornaam."""
    name = ' '.join(str(getattr(character, 'name', '') or '').split())
    explicit: list[str] = []
    automatic: list[str] = []
    if name:
        explicit.append(name)
        first = name.split(' ')[0]
        if first != name and len(first) >= 3 and first[:1].isupper():
            automatic.append(first)
    for alias in _ALIAS_SPLIT.split(str(getattr(character, 'aliases', '') or '')):
        alias = ' '.join(alias.split())
        if alias and alias not in explicit:
            explicit.append(alias)
    automatic = [t for t in automatic if t not in explicit]
    return tuple(explicit), tuple(automatic)


def character_terms(character) -> tuple[str, ...]:
    explicit, automatic = _term_sources(character)
    return (*explicit[:1], *automatic, *explicit[1:])


@lru_cache(maxsize=512)
def _pattern(terms: tuple[str, ...]):
    if not terms:
        return None
    alternatives = '|'.join(re.escape(term) for term in sorted(terms, key=len, reverse=True))
    return re.compile(rf'(?<!\w)(?:{alternatives})(?!\w)')


def plain_text(source: str) -> str:
    return text_for_search(strip_open_point_markers(source or ''))


def unambiguous_terms(characters) -> dict[str, tuple[str, ...]]:
    """Per personage-id alleen de namen die eenduidig bij dat personage horen.

    - Een naam die je zelf opgaf (volledige naam, Ook bekend als) wint van een
      automatische voornaam van een ander personage.
    - Twee keer dezelfde zelf opgegeven naam, of twee keer dezelfde voornaam:
      telt voor niemand.
    """
    sources = {c.id: _term_sources(c) for c in characters}
    explicit_owners: dict[str, set[str]] = {}
    automatic_owners: dict[str, set[str]] = {}
    for cid, (explicit, automatic) in sources.items():
        for term in explicit:
            explicit_owners.setdefault(term, set()).add(cid)
        for term in automatic:
            automatic_owners.setdefault(term, set()).add(cid)
    result = {}
    for cid, (explicit, automatic) in sources.items():
        keep = [t for t in explicit if len(explicit_owners[t]) == 1]
        keep += [t for t in automatic if t not in explicit_owners and len(automatic_owners[t]) == 1]
        result[cid] = tuple(keep)
    return result


def mention_counts(text: str, characters) -> dict[str, int]:
    """Aantal vermeldingen per personage-id in *platte* tekst (zie ``plain_text``)."""
    result: dict[str, int] = {}
    usable = unambiguous_terms(characters)
    # Langste namen eerst over de hele cast, zodat "Roos van Dijk" niet ook
    # als losse "Roos" van een ander personage telt.
    for character in characters:
        pattern = _pattern(usable.get(character.id, ()))
        if pattern is None:
            continue
        count = len(pattern.findall(_mask_longer_names(text, character.id, usable)))
        if count:
            result[character.id] = count
    return result


def _mask_longer_names(text: str, cid: str, usable: dict[str, tuple[str, ...]]) -> str:
    """Blank langere namen van *andere* personages die een term van ``cid`` bevatten."""
    mine = usable.get(cid, ())
    longer = [t for other, items in usable.items() if other != cid for t in items
              if any(term != t and re.search(rf'(?<!\w){re.escape(term)}(?!\w)', t) for term in mine)]
    if not longer:
        return text
    pattern = _pattern(tuple(longer))
    return pattern.sub(lambda m: ' ' * len(m.group(0)), text)


@dataclass(frozen=True)
class ChapterMention:
    id: str
    name: str
    count: int
    first_here: bool | None   # True: in geen eerder hoofdstuk; None: onbekend (eerder hoofdstuk onleesbaar)


def chapter_mentions(chapter_id: str, chapter_texts: list[tuple[str, str]], characters) -> tuple[ChapterMention, ...]:
    """Personages in ``chapter_id``, met "eerste keer" t.o.v. eerdere hoofdstukken.

    ``chapter_texts`` is de boekvolgorde: (hoofdstuk-id, platte tekst of
    ``None`` als dat hoofdstuk ontbreekt of onleesbaar is). Is een eerder
    hoofdstuk onbekend, dan is "voor het eerst" ook onbekend (``None``) en wordt
    het niet getoond: geen schijnzekerheid.
    Volgorde van het resultaat: meest genoemd eerst, daarna op naam.
    """
    seen_before: set[str] = set()
    history_complete = True
    here: dict[str, int] = {}
    for cid, text in chapter_texts:
        if cid == chapter_id:
            here = mention_counts(text or '', characters)
            break
        if text is None:
            history_complete = False
            continue
        seen_before.update(mention_counts(text, characters))
    by_id = {c.id: c for c in characters}

    def first(cid):
        if cid in seen_before:
            return False
        return True if history_complete else None

    rows = [ChapterMention(cid, by_id[cid].name, count, first(cid))
            for cid, count in here.items() if cid in by_id]
    rows.sort(key=lambda row: (-row.count, row.name.lower()))
    return tuple(rows)


class ChapterTextCache:
    """Platte tekst per hoofdstukbestand, alleen opnieuw lezen na een wijziging.

    Geeft ``None`` voor een ontbrekend of onleesbaar bestand: dat is iets
    anders dan een leeg hoofdstuk (corrupt is niet leeg).
    """

    def __init__(self):
        self._cache: dict[str, tuple[tuple[int, int], str | None]] = {}

    def text(self, path) -> str | None:
        key = str(path)
        try:
            stat = path.stat()
        except OSError:
            self._cache.pop(key, None)
            return None
        stamp = (stat.st_mtime_ns, stat.st_size)
        cached = self._cache.get(key)
        if cached and cached[0] == stamp:
            return cached[1]
        try:
            text = plain_text(path.read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError):
            text = None
        self._cache[key] = (stamp, text)
        return text
