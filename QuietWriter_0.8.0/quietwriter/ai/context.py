from __future__ import annotations
from dataclasses import dataclass, field
import json, re


@dataclass
class ContextBundle:
    label: str
    text: str
    sources: list[dict] = field(default_factory=list)
    pieces: list[str] = field(default_factory=list)


class ContextBuilder:
    def __init__(self, main, provider=None):
        self.main = main
        self.provider = provider

    def _chapter_text(self, book, current_chapter, chapter):
        if current_chapter and chapter.id == current_chapter.id:
            return self.main.editor_page.editor.toPlainText()
        return self.main.library.read_chapter(book, chapter)

    def _library_sources(self, prompt: str, limit=18) -> list[dict]:
        # Snelle lokale eerste trap: FTS + metadata/tags. Geen netwerk/LLM op de UI-thread.
        candidates = self.main.story_index.search(prompt, limit=limit)
        if not candidates: return []
        words = set(re.findall(r"[\wÀ-ÿ'-]+", prompt.casefold()))
        for c in candidates:
            tags = {t.strip().casefold() for t in str(c.get('tags','')).split(',') if t.strip()}
            c['_tag_hits'] = len(words & tags)
        candidates.sort(key=lambda c: (-c.get('_tag_hits',0), float(c.get('score', 0) or 0)))
        return candidates

    def library_bundle_from_rows(self, rows: list[dict], limit=5) -> ContextBundle:
        parts=[]; sources=[]
        max_story_chars = int(self.main.settings.value('ai_story_chars', 18000) or 18000)
        for h in rows[:limit]:
            try:
                d=self.main.story_index.get(h['path']); body=d['body']
            except Exception:
                body=h.get('snippet','')
            if len(body) > max_story_chars:
                body = body[:max_story_chars] + '\n\n[… verhaal ingekort voor AI-context …]'
            parts.append(f"# {h.get('title','')}\nTags: {h.get('tags','')}\nSynopsis: {h.get('synopsis','')}\n\n{body}")
            sources.append({'title': h.get('title',''), 'path': h.get('path',''), 'tags': h.get('tags','')})
        pieces=['Schrijverspersona', f'Verhalenbibliotheek: {len(sources)} verhalen']
        return ContextBundle('relevante verhalen uit bibliotheek', '\n\n'.join(parts) if parts else '(Geen relevante oude verhalen gevonden.)', sources=sources, pieces=pieces)

    def build(self, mode: str, prompt: str) -> ContextBundle:
        ep = self.main.editor_page; book = ep.book; chapter = ep.chapter
        if not book or not chapter:
            return ContextBundle('geen manuscript geopend', '', pieces=['Schrijverspersona'])

        selected = ep.editor.textCursor().selectedText().replace('\u2029','\n').strip()
        pieces = ['Schrijverspersona']
        if selected:
            pieces.append('Geselecteerde tekst')
            return ContextBundle('geselecteerde tekst', selected, pieces=pieces)

        if mode == 'Huidig hoofdstuk':
            pieces.append(f'Hoofdstuk: {chapter.title}')
            return ContextBundle(f'hoofdstuk: {chapter.title}', ep.editor.toPlainText(), pieces=pieces)

        if mode == 'Huidige sectie':
            section, _ = ep.find_chapter(chapter.id); parts=[]
            for c in section.chapters:
                parts.append(f'# {c.title}\n{self._chapter_text(book, chapter, c)}')
            pieces.append(f'Sectie: {section.title}')
            return ContextBundle(f'sectie: {section.title}', '\n\n'.join(parts), pieces=pieces)

        if mode == 'Hele boek':
            parts=[]
            for s in book.sections:
                if s.id != 'root': parts.append(f'## {s.title}')
                for c in s.chapters:
                    parts.append(f'# {c.title}\n{self._chapter_text(book, chapter, c)}')
            pieces.append(f'Boek: {book.title}')
            return ContextBundle(f'boek: {book.title}', '\n\n'.join(parts), pieces=pieces)

        hits = self._library_sources(prompt, 18)
        return self.library_bundle_from_rows(hits, 5)
