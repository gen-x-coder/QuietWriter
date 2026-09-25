from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BookMemorySection:
    key: str
    title: str
    help: str


SECTIONS = (
    BookMemorySection(
        'canon',
        'Canon & feiten',
        'Boekbrede feiten die AI later moet blijven weten. Gebruik Planning voor gegevens die daar al gestructureerd staan; voorkom dubbele bronnen van waarheid.',
    ),
    BookMemorySection(
        'book_style',
        'Stijl van dit boek',
        'Stijlpatronen die tijdens het schrijven duidelijk zijn geworden en specifieker zijn dan het Boekprofiel, bijvoorbeeld hoe emoties, beschrijvingen of perspectief in de praktijk worden behandeld.',
    ),
    BookMemorySection(
        'decisions',
        'Besluiten',
        'Keuzes die tijdens schrijven of AI-overleg bewust zijn gemaakt en later niet opnieuw ter discussie hoeven te staan.',
    ),
    BookMemorySection(
        'preferences',
        'Terugkerende voorkeuren',
        'Boekspecifieke voorkeuren die je vaker aan AI hebt gegeven en die bij volgende gesprekken opnieuw relevant zijn.',
    ),
    BookMemorySection(
        'open_points',
        'Open aandachtspunten',
        'Bewust nog onopgeloste vragen, continuïteitspunten of zaken waarop AI je later mag attenderen. Verwijder ze zodra ze niet meer actueel zijn.',
    ),
)

_SECTION_BY_TITLE = {section.title.casefold(): section for section in SECTIONS}


def empty_book_memory() -> dict[str, str]:
    return {section.key: '' for section in SECTIONS}


def parse_book_memory(markdown: str) -> dict[str, str]:
    """Parse human-readable book-memory Markdown without silently dropping text."""
    source = (markdown or '').replace('\r\n', '\n').replace('\r', '\n')
    memory = empty_book_memory()
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
            memory[current_key] = body
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
            if line.strip().casefold() not in {'# boekgeheugen', '# ai-boekgeheugen'}:
                preamble.append(line)
    flush()

    # Memory is new in 0.23.2, but preserve hand-written/unknown Markdown rather
    # than discarding it. Open aandachtspunten is the least destructive visible
    # place to surface such material so the user can reclassify it explicitly.
    extras: list[str] = []
    preamble_text = '\n'.join(preamble).strip()
    if preamble_text:
        extras.append(preamble_text)
    extras.extend(unknown)
    if extras:
        existing = memory['open_points'].strip()
        memory['open_points'] = '\n\n'.join(
            part for part in (existing, '\n\n'.join(extras)) if part
        ).strip()
    return memory


def render_book_memory(memory: dict[str, str]) -> str:
    parts = ['# Boekgeheugen']
    for section in SECTIONS:
        body = (memory.get(section.key) or '').strip()
        parts.append(f'## {section.title}\n\n{body}'.rstrip())
    return '\n\n'.join(parts).rstrip() + '\n'




def append_memory_entry(markdown: str, section_key: str, text: str) -> tuple[str, bool]:
    """Append one normalized bullet to a memory section without duplicating it.

    This is deliberately UI-independent so AI approval can be tested and persisted
    without relying on the BookMemoryPage widget being the active page.
    """
    memory = parse_book_memory(markdown)
    if section_key not in memory:
        return markdown, False
    clean = (text or '').strip()
    if not clean:
        return markdown, False
    current = (memory.get(section_key) or '').rstrip()
    normalized = clean.lstrip('-*').strip().casefold()
    existing = {
        line.strip().lstrip('-*').strip().casefold()
        for line in current.splitlines() if line.strip()
    }
    if normalized in existing:
        return render_book_memory(memory), False
    entry = clean if clean.startswith(('-', '*')) else f'- {clean}'
    memory[section_key] = f'{current}\n{entry}'.strip() if current else entry
    return render_book_memory(memory), True

def default_book_memory_markdown() -> str:
    return render_book_memory(empty_book_memory())


def has_meaningful_book_memory(markdown: str) -> bool:
    memory = parse_book_memory(markdown)
    return any((value or '').strip() for value in memory.values())
