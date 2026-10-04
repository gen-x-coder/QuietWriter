from __future__ import annotations
from dataclasses import dataclass, field

from ..media.markup import text_for_ai
from ..i18n import tr


def read_optional_source(reader) -> tuple[str, bool]:
    """Read optional AI context without letting corrupt UTF-8 break the Meelezer.

    Corrupt optional context is omitted from the prompt. The caller remains
    responsible for making that omission visible to the user.
    """
    try:
        return reader(), True
    except UnicodeDecodeError:
        return '', False


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
            return ContextBundle(tr('ai.context.none_open', 'geen manuscript geopend'), '', [tr('context.persona', 'Schrijverspersona')])

        selected = ep.editor.textCursor().selectedText().replace('\u2029', '\n').strip()
        pieces = [tr('context.persona', 'Schrijverspersona'), tr('context.book_profile', 'Boekprofiel'), tr('context.book_memory', 'Boekgeheugen')]
        if selected:
            pieces.append(tr('ai.context.selected_text', 'Geselecteerde tekst'))
            return ContextBundle(tr('ai.context.selected_text_label', 'geselecteerde tekst'), text_for_ai(selected), pieces)

        if mode in ('chapter', 'Huidig hoofdstuk'):
            pieces.append(tr('ai.context.chapter_piece', 'Hoofdstuk: {title}', title=chapter.title))
            return ContextBundle(tr('ai.context.chapter_label', 'hoofdstuk: {title}', title=chapter.title), text_for_ai(ep.editor.toPlainText()), pieces)

        if mode in ('section', 'Huidige sectie'):
            section, _ = ep.find_chapter_in_book(chapter.id)
            if section is None:
                pieces.append(tr('ai.context.section_unavailable_piece', 'Sectie niet beschikbaar'))
                return ContextBundle(tr('ai.context.section_unavailable_label', 'sectie niet beschikbaar'), '', pieces)
            parts = [f'# {c.title}\n{self._chapter_text(book, chapter, c)}' for c in section.chapters]
            pieces.append(tr('ai.context.section_piece', 'Sectie: {title}', title=section.title))
            return ContextBundle(tr('ai.context.section_label', 'sectie: {title}', title=section.title), '\n\n'.join(parts), pieces)

        if mode in ('book', 'Hele boek'):
            parts = []
            for section in book.sections:
                if section.id != 'root':
                    parts.append(f'## {section.title}')
                for c in section.chapters:
                    parts.append(f'# {c.title}\n{self._chapter_text(book, chapter, c)}')
            pieces.append(tr('ai.context.book_piece', 'Boek: {title}', title=book.title))
            return ContextBundle(tr('ai.context.book_label', 'boek: {title}', title=book.title), '\n\n'.join(parts), pieces)

        pieces.append(tr('ai.context.chapter_piece', 'Hoofdstuk: {title}', title=chapter.title))
        return ContextBundle(tr('ai.context.chapter_label', 'hoofdstuk: {title}', title=chapter.title), text_for_ai(ep.editor.toPlainText()), pieces)
