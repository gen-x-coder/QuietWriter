from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BookProfileSection:
    key: str
    title: str
    help: str


SECTIONS = (
    BookProfileSection('genre_audience', 'Genre & doelgroep', 'Genre, subgenre, beoogde lezers en eventuele verwachtingen die je bewust wilt volgen of doorbreken.'),
    BookProfileSection('premise', 'Kernpremisse', 'Waar gaat dit boek in essentie over? Beschrijf de centrale situatie, belofte of vraag zonder de hele synopsis te herhalen.'),
    BookProfileSection('narration', 'Vertelperspectief & tijd', 'Perspectief, verteltijd, vertelafstand en eventuele regels voor wisselende perspectieven.'),
    BookProfileSection('tone', 'Sfeer & toon', 'De gewenste sfeer van dit specifieke boek en hoe die eventueel afwijkt van je algemene schrijverspersona.'),
    BookProfileSection('themes', 'Thema’s & motieven', 'Terugkerende thema’s, motieven, contrasten of ideeën die het boek inhoudelijk bij elkaar houden.'),
    BookProfileSection('setting', 'Setting & wereld', 'De brede wereld, periode en omgeving van het boek. Bewaar concrete canonfeiten zoveel mogelijk in Planning; noteer hier vooral de regels en sfeer van de wereld.'),
    BookProfileSection('pacing', 'Tempo & spanningsboog', 'Gewenst verteltempo, opbouw van spanning en rust, hoofdstukritme en de manier waarop informatie wordt gedoseerd.'),
    BookProfileSection('intensity', 'Relaties, romantiek & intensiteit', 'Hoe dit boek omgaat met relaties, romantiek, intimiteit, conflict, geweld en emotionele intensiteit.'),
    BookProfileSection('persona_overrides', 'Afwijkingen van schrijverspersona', 'Alleen de bewuste uitzonderingen voor dit boek. Deze instructies hebben voor dit project voorrang op je algemene schrijverspersona.'),
    BookProfileSection('editorial', 'Redactionele aandachtspunten', 'Specifieke zaken waarop AI bij dit boek moet letten, bijvoorbeeld perspectiefdiscipline, doelgroep, spanningsniveau of terugkerende valkuilen.'),
    BookProfileSection('additional', 'Aanvullende instructies', 'Vrije boekinstructies die niet goed in de andere onderdelen passen.'),
)

_SECTION_BY_TITLE = {section.title.casefold(): section for section in SECTIONS}


def empty_book_profile() -> dict[str, str]:
    return {section.key: '' for section in SECTIONS}


def parse_book_profile(markdown: str) -> dict[str, str]:
    """Parse human-readable book-profile Markdown and preserve unknown content."""
    source = (markdown or '').replace('\r\n', '\n').replace('\r', '\n')
    profile = empty_book_profile()
    lines = source.split('\n')
    preamble: list[str] = []
    unknown: list[str] = []
    current_key: str | None = None
    current_title: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_key, current_title, current_lines
        if current_title is None:
            return
        body = '\n'.join(current_lines).strip()
        if current_key is not None:
            profile[current_key] = body
        else:
            block = f'## {current_title}'
            if body:
                block += f'\n\n{body}'
            unknown.append(block)
        current_key = None
        current_title = None
        current_lines = []

    for line in lines:
        if line.startswith('## '):
            flush()
            title = line[3:].strip()
            section = _SECTION_BY_TITLE.get(title.casefold())
            current_key = section.key if section else None
            current_title = title
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)
        else:
            if line.strip().casefold() not in {'# boekprofiel', '# ai-boekprofiel'}:
                preamble.append(line)
    flush()

    extras: list[str] = []
    preamble_text = '\n'.join(preamble).strip()
    if preamble_text:
        extras.append(preamble_text)
    extras.extend(unknown)
    if extras:
        existing = profile['additional'].strip()
        profile['additional'] = '\n\n'.join(part for part in (existing, '\n\n'.join(extras)) if part).strip()
    return profile


def render_book_profile(profile: dict[str, str]) -> str:
    parts = ['# Boekprofiel']
    for section in SECTIONS:
        body = (profile.get(section.key) or '').strip()
        parts.append(f'## {section.title}\n\n{body}'.rstrip())
    return '\n\n'.join(parts).rstrip() + '\n'


def default_book_profile_markdown() -> str:
    return render_book_profile(empty_book_profile())


def has_meaningful_book_profile(markdown: str) -> bool:
    profile = parse_book_profile(markdown)
    return any((value or '').strip() for value in profile.values())
