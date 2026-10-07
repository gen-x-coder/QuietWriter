from __future__ import annotations

import json
import re
from pathlib import Path

from .storage import Book, slugify

SECTION_MARKER_RE = re.compile(r'^<!--\s*quietwriter-section:\s*(.*?)\s*-->\s*$', re.IGNORECASE)
CHAPTER_RE = re.compile(r'^#\s+(.+?)\s*$')
META_RE = re.compile(r'^([A-Za-z_][\w-]*):\s*(.*)$')

CORE_EXPORT_ORDER = [
    'title', 'date', 'slug', 'description', 'intro', 'meta',
    'image', 'image_alt', 'author', 'tags', 'published', 'synopsis'
]
# Canonieke frontmattervelden die QuietWriter bij iedere export opneemt.
# Lege waarden worden bewust behouden zodat de export een stabiel schema heeft.
ALWAYS_EXPORT_FIELDS = set(CORE_EXPORT_ORDER)
INTERNAL_METADATA = {
    'last_used', 'cover_file', 'source_file', 'extra'
}


def _clean_scalar(value) -> str:
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    return str(value).strip()


def _decode_frontmatter_scalar(value: str) -> str:
    """Decode the quoted scalar forms emitted by QuietWriter exports.

    This is intentionally not a general YAML parser. Double-quoted values are
    emitted as JSON-compatible strings by ``exporting.markdown_exporter``;
    single-quoted YAML scalars only need doubled apostrophes unescaped.
    """
    value = str(value or '').strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            decoded = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
        return decoded if isinstance(decoded, str) else value
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


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
            metadata[m.group(1).lower()] = _decode_frontmatter_scalar(m.group(2))
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




def _import_inline_runs(text: str):
    """Convert the supported Markdown inline subset to neutral semantic runs."""
    from .document_view import inline_runs
    from .import_document import ImportInlineRun

    runs = inline_runs(text or '')
    if not runs:
        return (ImportInlineRun(text or ''),) if text else ()
    return tuple(ImportInlineRun(run.text, run.styles) for run in runs)


def _import_blocks(text: str):
    """Parse external Markdown prose into neutral QuietWriter import blocks.

    External Markdown follows the normal paragraph rule: adjacent ordinary
    source lines belong to one paragraph until a blank line. QuietWriter's
    canonical one-line-per-paragraph representation is only created later by
    the serializer.
    """
    from .import_document import ImportBlock

    source = (text or '').replace('\r\n', '\n').replace('\r', '\n')
    lines = source.split('\n')
    blocks = []
    paragraph_parts: list[str] = []

    def flush_paragraph():
        nonlocal paragraph_parts
        if not paragraph_parts:
            return
        value = ''.join(paragraph_parts).strip()
        if value:
            blocks.append(ImportBlock('paragraph', _import_inline_runs(value)))
        paragraph_parts = []

    for raw in lines:
        line = raw.rstrip('\n')
        if not line.strip():
            flush_paragraph()
            continue

        stripped = line.strip()
        # Structural Markdown blocks are only recognized at the physical line
        # boundary. They are serialized later by the same QuietWriter writer as
        # DOCX imports.
        if stripped == '***':
            flush_paragraph()
            blocks.append(ImportBlock('scene'))
            continue
        if line.startswith('## '):
            flush_paragraph()
            blocks.append(ImportBlock('heading', _import_inline_runs(line[3:].strip())))
            continue
        if line.startswith('> '):
            flush_paragraph()
            blocks.append(ImportBlock('quote', _import_inline_runs(line[2:].strip())))
            continue
        bullet = re.match(r'^[-*]\s+(.+)$', line)
        if bullet:
            flush_paragraph()
            blocks.append(ImportBlock('bullet', _import_inline_runs(bullet.group(1))))
            continue
        numbered = re.match(r'^(\d+)\.\s+(.+)$', line)
        if numbered:
            flush_paragraph()
            blocks.append(ImportBlock('numbered', _import_inline_runs(numbered.group(2)), number=int(numbered.group(1))))
            continue

        # CommonMark hard line break: two trailing spaces or a trailing
        # backslash. QuietWriter stores this semantically as U+2028 inside the
        # paragraph, not as a second paragraph.
        hard_break = False
        value = line
        if value.endswith('\\') and not value.endswith('\\\\'):
            value = value[:-1]
            hard_break = True
        elif len(value) >= 2 and value.endswith('  '):
            value = value.rstrip(' ')
            hard_break = True

        if paragraph_parts and not paragraph_parts[-1].endswith('\u2028'):
            paragraph_parts.append(' ')
        paragraph_parts.append(value.strip())
        if hard_break:
            paragraph_parts.append('\u2028')

    flush_paragraph()
    return tuple(blocks)


def read_markdown_import_document(path: Path):
    """Read an external Markdown book into the neutral import model."""
    from .import_document import ImportChapter, ImportDocument, ImportSection

    path = Path(path)
    text = path.read_text(encoding='utf-8-sig', errors='replace')
    metadata, body = split_frontmatter(text)
    title = (metadata.get('title') or path.stem).strip() or path.stem
    groups = split_book_body(body, title)
    sections = tuple(
        ImportSection(
            section_title,
            tuple(
                ImportChapter(
                    (item.get('title') or title).strip() or title,
                    _import_blocks(item.get('text', '')),
                )
                for item in chapters
            ),
        )
        for section_title, chapters in groups
    )
    return ImportDocument(
        title=title,
        sections=sections,
        author=str(metadata.get('author') or ''),
        language=str(metadata.get('language') or ''),
        metadata=dict(metadata),
    )

def parse_markdown_book(path: Path) -> dict:
    """Compatibility wrapper around the neutral Markdown import reader."""
    from .import_document import serialize_import_document

    imported = read_markdown_import_document(Path(path))
    sections = [
        (title, [dict(chapter) for chapter in chapters])
        for title, chapters in serialize_import_document(imported)
    ]
    metadata = dict(imported.metadata or {})
    body_parts = []
    for section_title, chapters in sections:
        if section_title:
            body_parts.append(f'<!-- quietwriter-section: {section_title} -->')
        for chapter in chapters:
            body_parts.append(f'# {chapter["title"]}')
            if chapter.get('text'):
                body_parts.append(chapter['text'])
    return {
        'title': imported.title,
        'metadata': metadata,
        'sections': sections,
        'body': '\n\n'.join(body_parts).strip(),
    }


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
        # Canonieke velden worden altijd geschreven, ook als ze leeg zijn.
        # Daardoor is iedere export voorspelbaar en direct bruikbaar als sjabloon.
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
    for section in book.sections:
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

    # A scene break belongs between text blocks, never inside a sentence. If the
    # cursor is already at the start of a line, keep it there so the break is
    # inserted before that line. Otherwise finish the current line first.
    line_start = text.rfind('\n', 0, position) + 1
    if position != line_start:
        line_end = text.find('\n', position)
        position = len(text) if line_end < 0 else line_end

    before, after = text[:position], text[position:]

    # If the cursor is directly beside an existing break (ignoring whitespace),
    # inserting again is a no-op. This prevents adjacent duplicate scene breaks.
    left = before.rstrip('\n')
    right = after.lstrip('\n').lstrip(' \t')
    left_tail = left.rstrip()
    right_head = right.lstrip()
    left_has_break = bool(re.search(r'(?:^|\n)\s*\*\*\*\s*$', left_tail))
    right_has_break = bool(re.match(r'^\s*\*\*\*(?:\s*(?:\n|$))', right_head))
    if left_has_break or right_has_break:
        return text, position
    prefix = '' if not left else '\n\n'
    suffix = '' if not right else '\n\n'
    new_text = left + prefix + '***' + suffix + right
    caret = len(left + prefix + '***' + suffix)
    return new_text, caret


def remove_scene_break(text: str, position: int) -> tuple[str, int]:
    """Remove the scene-break line at ``position`` and normalize surrounding blanks.

    Returns ``(new_text, caret_position)``. If the addressed line is not exactly a
    Markdown scene break (``***`` ignoring surrounding whitespace), the input is
    returned unchanged.
    """
    position = max(0, min(position, len(text)))
    line_start = text.rfind('\n', 0, position) + 1
    line_end = text.find('\n', position)
    if line_end < 0:
        line_end = len(text)
    if text[line_start:line_end].strip() != '***':
        return text, position

    before = text[:line_start].rstrip('\n')
    after = text[line_end:].lstrip('\n')
    if before and after:
        new_text = before + '\n\n' + after
        caret = len(before) + 2
    elif before:
        new_text = before
        caret = len(before)
    else:
        new_text = after
        caret = 0
    return new_text, caret
