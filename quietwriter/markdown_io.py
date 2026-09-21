from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .storage import Book, Chapter, Section, slugify

SECTION_MARKER_RE = re.compile(r'^<!--\s*quietwriter-section:\s*(.*?)\s*-->\s*$', re.IGNORECASE)
CHAPTER_RE = re.compile(r'^#\s+(.+?)\s*$')
META_RE = re.compile(r'^([A-Za-z_][\w-]*):\s*(.*)$')

CORE_EXPORT_ORDER = [
    'title', 'date', 'slug', 'description', 'meta', 'intro', 'synopsis',
    'author', 'tags', 'image', 'published'
]
INTERNAL_METADATA = {
    'last_used', 'cover_file', 'source_file', 'extra'
}


def _clean_scalar(value) -> str:
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    return str(value).strip()


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Parse the simple YAML-style frontmatter QuietWriter uses.

    Unknown single-line fields are preserved. This deliberately avoids a YAML
    dependency because the user's existing files use simple key: value fields.
    """
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    metadata: dict[str, str] = {}
    if not lines or lines[0].strip() != '---':
        return metadata, text.strip('\n')
    end = None
    for i in range(1, min(len(lines), 300)):
        if lines[i].strip() == '---':
            end = i
            break
        m = META_RE.match(lines[i])
        if m:
            metadata[m.group(1).lower()] = m.group(2).strip()
    if end is None:
        return {}, text.strip('\n')
    return metadata, '\n'.join(lines[end + 1:]).strip('\n')


def split_book_body(body: str, fallback_title: str) -> list[tuple[str | None, list[dict]]]:
    """Split Markdown into optional QuietWriter sections and # chapters.

    Section markers are HTML comments so exported files remain ordinary Markdown
    and renderers/websites simply ignore them.
    """
    lines = body.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    groups: list[tuple[str | None, list[dict]]] = []
    current_section: str | None = None
    current_chapters: list[dict] = []
    current_title: str | None = None
    current_lines: list[str] = []
    preface: list[str] = []

    def flush_chapter():
        nonlocal current_title, current_lines, current_chapters
        if current_title is not None:
            current_chapters.append({'title': current_title, 'text': '\n'.join(current_lines).strip()})
            current_title = None
            current_lines = []

    def flush_group():
        nonlocal current_chapters
        flush_chapter()
        if current_chapters:
            groups.append((current_section, current_chapters))
            current_chapters = []

    for line in lines:
        sec = SECTION_MARKER_RE.match(line)
        if sec:
            flush_group()
            current_section = sec.group(1).strip() or 'Nieuwe sectie'
            continue
        chap = CHAPTER_RE.match(line)
        if chap:
            if current_title is None and not current_chapters and preface:
                # Text before the first chapter becomes its own chapter to avoid loss.
                current_chapters.append({'title': 'Inleiding', 'text': '\n'.join(preface).strip()})
                preface = []
            flush_chapter()
            current_title = chap.group(1).strip()
            current_lines = []
            continue
        if current_title is None:
            if line.strip() or preface:
                preface.append(line)
        else:
            current_lines.append(line)

    flush_group()
    if preface:
        if groups:
            groups[0][1].insert(0, {'title': 'Inleiding', 'text': '\n'.join(preface).strip()})
        else:
            groups = [(current_section, [{'title': fallback_title, 'text': '\n'.join(preface).strip()}])]
    if not groups:
        groups = [(None, [{'title': fallback_title, 'text': body.strip()}])]
    return groups


def parse_markdown_book(path: Path) -> dict:
    path = Path(path)
    text = path.read_text(encoding='utf-8', errors='replace')
    metadata, body = split_frontmatter(text)
    title = (metadata.get('title') or path.stem).strip() or path.stem
    sections = split_book_body(body, title)
    return {'title': title, 'metadata': metadata, 'sections': sections, 'body': body}


def render_frontmatter(book: Book, image_ref: str = '') -> str:
    md = dict(book.metadata or {})
    md['title'] = book.title
    md['slug'] = md.get('slug') or slugify(book.title)
    if image_ref:
        md['image'] = image_ref

    extra = md.get('extra') if isinstance(md.get('extra'), dict) else {}
    rows = []
    emitted = set()
    for key in CORE_EXPORT_ORDER:
        value = _clean_scalar(md.get(key, ''))
        if value:
            rows.append(f'{key}: {value}')
            emitted.add(key)
    # Preserve imported unknown fields, then other harmless metadata fields.
    for source in (extra, md):
        for key, value in source.items():
            key = str(key).lower()
            if key in emitted or key in INTERNAL_METADATA or key in CORE_EXPORT_ORDER:
                continue
            scalar = _clean_scalar(value)
            if scalar and '\n' not in scalar:
                rows.append(f'{key}: {scalar}')
                emitted.add(key)
    return '---\n' + '\n'.join(rows) + '\n---\n'


def export_book_markdown(library, book: Book, destination: Path, image_ref: str = '', include_frontmatter: bool = True,
                         include_section_markers: bool = True) -> Path:
    destination = Path(destination)
    parts: list[str] = []
    if include_frontmatter:
        parts.append(render_frontmatter(book, image_ref=image_ref).rstrip())

    multiple_sections = len(book.sections) > 1 or any(sec.id != 'root' for sec in book.sections)
    for sec_index, section in enumerate(book.sections):
        if include_section_markers and multiple_sections:
            parts.append(f'<!-- quietwriter-section: {section.title} -->')
        for chapter in section.chapters:
            parts.append(f'# {chapter.title}')
            text = library.read_chapter(book, chapter).strip()
            if text:
                parts.append(text)

    content = '\n\n'.join(parts).rstrip() + '\n'
    # Reuse the robust Windows/sync-safe writer from storage without exposing temp files.
    from .storage import _safe_atomic_write_text
    _safe_atomic_write_text(destination, content)
    return destination


def insert_scene_break(text: str, position: int) -> tuple[str, int]:
    """Insert a Markdown scene break on its own line at/near the cursor.

    The break is separated by blank lines and duplicates are avoided. Returns the
    new text and caret position after the break.
    """
    position = max(0, min(position, len(text)))
    before, after = text[:position], text[position:]

    # Put the scene break between paragraphs: complete the current line first.
    left = before.rstrip('\n')
    right = after.lstrip('\n')
    if left.rstrip().endswith('***') and (not right or right.startswith('\n')):
        return text, position
    prefix = '' if not left else '\n\n'
    suffix = '' if not right else '\n\n'
    new_text = left + prefix + '***' + suffix + right
    caret = len(left + prefix + '***' + suffix)
    return new_text, caret
