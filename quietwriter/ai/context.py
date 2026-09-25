from __future__ import annotations
from dataclasses import dataclass, field

from ..media.markup import text_for_ai


@dataclass
class ContextBundle:
    label: str
    text: str
    pieces: list[str] = field(default_factory=list)


class ContextBuilder:
    """Bouw uitsluitend manuscriptcontext voor de normale schrijfchat."""

    def __init__(self, main):
        self.main = main

    def _chapter_text(self, book, current_chapter, chapter):
        if current_chapter and chapter.id == current_chapter.id:
            return text_for_ai(self.main.editor_page.editor.toPlainText())
        try:
            return text_for_ai(self.main.library.read_chapter(book, chapter))
        except (OSError, UnicodeError) as exc:
            return f'[Hoofdstuk “{chapter.title}” kon niet worden gelezen: {exc}]'

    def build(self, mode: str) -> ContextBundle:
        ep = self.main.editor_page
        book = ep.book
        chapter = ep.chapter
        if not book or not chapter:
            return ContextBundle('geen manuscript geopend', '', ['Schrijverspersona'])

        selected = ep.editor.textCursor().selectedText().replace('\u2029', '\n').strip()
        pieces = ['Schrijverspersona', 'Boekprofiel', 'Boekgeheugen']
        if selected:
            pieces.append('Geselecteerde tekst')
            return ContextBundle('geselecteerde tekst', text_for_ai(selected), pieces)

        if mode == 'Huidig hoofdstuk':
            pieces.append(f'Hoofdstuk: {chapter.title}')
            return ContextBundle(f'hoofdstuk: {chapter.title}', text_for_ai(ep.editor.toPlainText()), pieces)

        if mode == 'Huidige sectie':
            section, _ = ep.find_chapter_in_book(chapter.id)
            if section is None:
                pieces.append('Sectie niet beschikbaar')
                return ContextBundle('sectie niet beschikbaar', '', pieces)
            parts = [f'# {c.title}\n{self._chapter_text(book, chapter, c)}' for c in section.chapters]
            pieces.append(f'Sectie: {section.title}')
            return ContextBundle(f'sectie: {section.title}', '\n\n'.join(parts), pieces)

        if mode == 'Hele boek':
            parts = []
            for section in book.sections:
                if section.id != 'root':
                    parts.append(f'## {section.title}')
                for c in section.chapters:
                    parts.append(f'# {c.title}\n{self._chapter_text(book, chapter, c)}')
            pieces.append(f'Boek: {book.title}')
            return ContextBundle(f'boek: {book.title}', '\n\n'.join(parts), pieces)

        pieces.append(f'Hoofdstuk: {chapter.title}')
        return ContextBundle(f'hoofdstuk: {chapter.title}', text_for_ai(ep.editor.toPlainText()), pieces)
