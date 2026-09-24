from __future__ import annotations

from pathlib import Path
import json
import re

from ..storage import _safe_atomic_write_text
from .models import ExportDocument


# Stable public Markdown contract used by the user's existing publishing flow.
PUBLIC_FRONTMATTER_ORDER = (
    'title', 'date', 'slug', 'description', 'meta', 'intro', 'author', 'tags',
)


_YAML_AMBIGUOUS = {
    'null', '~', 'true', 'false', 'yes', 'no', 'on', 'off',
    '.nan', '.inf', '+.inf', '-.inf',
}
_YAML_NUMBER_RE = re.compile(r'^[+-]?(?:\d[\d_]*)(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?$')


def _needs_yaml_quotes(text: str) -> bool:
    if not text:
        return False
    lowered = text.casefold()
    if lowered in _YAML_AMBIGUOUS or _YAML_NUMBER_RE.fullmatch(text):
        return True
    if '\n' in text or '\r' in text or '\t' in text:
        return True
    if text[0] in "-?:,[]{}#&*!|>\"'%@`" or text[-1].isspace():
        return True
    # A colon is safe in plain YAML when it is not followed by whitespace,
    # which keeps ISO timestamps such as 2025-12-10T16:00 unchanged.
    if re.search(r':(?:\s|$)', text) or re.search(r'\s#', text):
        return True
    return False


def _scalar(value) -> str:
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    text = str(value).strip()
    if not _needs_yaml_quotes(text):
        return text
    # JSON string syntax is a valid YAML double-quoted scalar and gives us
    # deterministic escaping for quotes, backslashes and embedded newlines
    # without adding PyYAML as a runtime dependency.
    return json.dumps(text, ensure_ascii=False)


def render_publication_frontmatter(document: ExportDocument) -> str:
    """Render the fixed public Markdown frontmatter in a stable field order.

    This intentionally stays separate from ``markdown_io.render_frontmatter``.
    The latter is QuietWriter's richer lossless import/round-trip format; the
    Export page produces the compact public format used by existing workflows.
    """
    md = dict(document.metadata or {})
    values = {
        'title': document.title,
        'date': md.get('date', ''),
        'slug': document.slug,
        'description': md.get('description', ''),
        'meta': md.get('meta', ''),
        'intro': md.get('intro', ''),
        'author': document.author or md.get('author', ''),
        'tags': md.get('tags', ''),
    }
    rows = [f'{key}: {_scalar(values.get(key, ""))}' for key in PUBLIC_FRONTMATTER_ORDER]
    return '---\n' + '\n'.join(rows) + '\n---\n'


def _plain_single_chapter(document: ExportDocument):
    chapters = [chapter for section in document.sections for chapter in section.chapters]
    if len(chapters) != 1:
        return None
    chapter = chapters[0]
    # Files imported without an H1 become a single chapter named after the book.
    # Do not invent a heading when exporting them back to the public format.
    if chapter.title.strip().casefold() == document.title.strip().casefold():
        return chapter
    return None


def export_markdown(document: ExportDocument, destination: Path, settings: dict | None = None) -> Path:
    """Export the fixed public Markdown format.

    The header and structural markers are part of the format, not user options.
    ``settings`` remains accepted so callers from 0.19.1 stay compatible.
    """
    parts: list[str] = [render_publication_frontmatter(document).rstrip()]

    plain = _plain_single_chapter(document)
    if plain is not None:
        if plain.markdown.strip():
            parts.append(plain.markdown.strip())
    else:
        multiple_sections = len(document.sections) > 1 or any(section.id != 'root' for section in document.sections)
        for section in document.sections:
            if multiple_sections:
                parts.append(f'<!-- quietwriter-section: {section.title} -->')
            for chapter in section.chapters:
                parts.append(f'# {chapter.title}')
                if chapter.markdown.strip():
                    parts.append(chapter.markdown.strip())

    _safe_atomic_write_text(Path(destination), '\n\n'.join(parts).rstrip() + '\n')
    return Path(destination)
