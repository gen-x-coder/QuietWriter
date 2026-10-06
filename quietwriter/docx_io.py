from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.image.image import Image as DocxImage
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Mm

from .manuscript_markup import is_scene_break_line, parse_inline_spans
from .media.markup import image_reference_for_line
from .i18n import tr


@dataclass(frozen=True)
class DocxImportResult:
    title: str
    sections: tuple[tuple[str | None, tuple[dict, ...]], ...]
    author: str = ''
    language: str = ''
    warnings: tuple[str, ...] = ()



def _normalize_language_tag(value: str | None) -> str:
    raw = str(value or '').strip().replace('_', '-')
    if not raw:
        return ''
    parts = [part for part in raw.split('-') if part]
    if not parts:
        return ''
    if len(parts) == 1:
        return parts[0].lower()
    return '-'.join([parts[0].lower()] + [part.upper() if len(part) in (2, 3) else part for part in parts[1:]])


def _document_default_language(doc: Document) -> str:
    """Return Word's default document language, if explicitly stored."""
    try:
        defaults = doc.styles.element.find(qn('w:docDefaults'))
        if defaults is None:
            return ''
        rpr_default = defaults.find(qn('w:rPrDefault'))
        if rpr_default is None:
            return ''
        rpr = rpr_default.find(qn('w:rPr'))
        if rpr is None:
            return ''
        lang = rpr.find(qn('w:lang'))
        if lang is None:
            return ''
        value = lang.get(qn('w:val')) or lang.get(qn('w:eastAsia')) or ''
        normalized = _normalize_language_tag(value)
        return normalized.split('-', 1)[0] if normalized else ''
    except Exception:
        return ''

def _style_name(paragraph) -> str:
    try:
        return str(paragraph.style.name or '')
    except Exception:
        return ''


def _run_is_code(run) -> bool:
    try:
        if run.style and str(run.style.name or '') == 'QuietWriter Code':
            return True
    except Exception:
        pass
    try:
        name = str(run.font.name or '').lower()
    except Exception:
        name = ''
    return name in {'consolas', 'courier new', 'courier', 'liberation mono'}


def _wrap_run(text: str, run) -> str:
    if not text:
        return ''
    # A DOCX run may contain hard line breaks. Keep those as source newlines.
    code = _run_is_code(run) and '`' not in text
    bold = bool(run.bold)
    italic = bool(run.italic)
    underline = bool(run.underline)
    strike = bool(getattr(run.font, 'strike', False))

    out = text
    if code:
        out = f'`{out}`'
    else:
        if bold and italic:
            out = f'***{out}***'
        elif bold:
            out = f'**{out}**'
        elif italic:
            out = f'*{out}*'
        if underline:
            out = f'<u>{out}</u>'
        if strike:
            out = f'~~{out}~~'
    return out


def _run_signature(run) -> tuple[bool, bool, bool, bool, bool]:
    return (
        bool(_run_is_code(run)),
        bool(run.bold),
        bool(run.italic),
        bool(run.underline),
        bool(getattr(run.font, 'strike', False)),
    )


def _wrap_text_for_signature(text: str, sig: tuple[bool, bool, bool, bool, bool]) -> str:
    if not text:
        return ''
    code, bold, italic, underline, strike = sig
    out = text
    if code and '`' not in text:
        out = f'`{out}`'
    else:
        if bold and italic:
            out = f'***{out}***'
        elif bold:
            out = f'**{out}**'
        elif italic:
            out = f'*{out}*'
        if underline:
            out = f'<u>{out}</u>'
        if strike:
            out = f'~~{out}~~'
    return out


def _paragraph_runs_including_hyperlinks(paragraph):
    """Yield textual runs in document order, including runs inside hyperlinks."""
    try:
        for item in paragraph.iter_inner_content():
            # python-docx 1.2 exposes Hyperlink.runs; normal Run has .text directly.
            runs = getattr(item, 'runs', None)
            if runs is not None and not hasattr(item, 'bold'):
                for run in runs:
                    yield run
            else:
                yield item
        return
    except Exception:
        pass
    # Compatibility fallback for older python-docx: preserve direct runs rather
    # than losing the whole paragraph.
    yield from paragraph.runs


def paragraph_to_markdown(paragraph) -> str:
    # Word frequently splits one visually continuous formatted phrase over
    # multiple runs. Merge adjacent runs with the same effective formatting
    # before adding Markdown markers, otherwise **a****b** changes semantics.
    chunks: list[tuple[tuple[bool, bool, bool, bool, bool], str]] = []
    for run in _paragraph_runs_including_hyperlinks(paragraph):
        text = str(getattr(run, 'text', '') or '')
        if not text:
            continue
        sig = _run_signature(run)
        if chunks and chunks[-1][0] == sig:
            chunks[-1] = (sig, chunks[-1][1] + text)
        else:
            chunks.append((sig, text))
    body = ''.join(_wrap_text_for_signature(text, sig) for sig, text in chunks)
    style = _style_name(paragraph).lower()
    if not body:
        return ''
    if style.startswith('list bullet'):
        return f'- {body}'
    if style.startswith('list number'):
        return f'1. {body}'
    if style in {'quote', 'intense quote'}:
        return f'> {body}'
    return body



def _paragraph_has_page_break(paragraph) -> bool:
    try:
        for br in paragraph._p.xpath('.//w:br'):
            if br.get(qn('w:type')) == 'page':
                return True
        return bool(paragraph._p.xpath('./w:pPr/w:pageBreakBefore'))
    except Exception:
        return False


def _page_chunks(paragraphs) -> list[list]:
    pages: list[list] = [[]]
    for paragraph in paragraphs:
        pages[-1].append(paragraph)
        if _paragraph_has_page_break(paragraph):
            pages.append([])
    return [page for page in pages if any((p.text or '').strip() for p in page)]


def _generic_word_title(value: str) -> bool:
    return value.strip().lower() in {'', 'document', 'word document', 'microsoft word document'}


def _display_heading(paragraph) -> bool:
    text = (paragraph.text or '').strip()
    if not text or len(text) > 140:
        return False
    style = _style_name(paragraph).lower()
    if style in {'title', 'subtitle'} or re.match(r'^heading\s+[1-6]$', style, re.I):
        return True
    sizes = [run.font.size.pt for run in paragraph.runs if run.text.strip() and run.font.size]
    return bool(sizes and max(sizes) >= 18)


def _page_to_chapters(page, chapter_offset: int = 0) -> list[dict]:
    chapters: list[dict] = []
    split_internal = len(page) > 25
    title_parts: list[str] = []
    body: list[str] = []

    def flush():
        nonlocal title_parts, body
        if not title_parts and not any(line.strip() for line in body):
            body = []
            return
        if not title_parts:
            first = next((line.strip() for line in body if line.strip()), 'Hoofdstuk')
            title_parts = [first[:97].rstrip() + ('…' if len(first) > 97 else '')]
            removed = False
            kept = []
            for line in body:
                if not removed and line.strip() == first:
                    removed = True
                    continue
                kept.append(line)
            body = kept
        chapters.append({'title': ' — '.join(title_parts), 'text': '\n'.join(body).rstrip('\n')})
        title_parts, body = [], []

    for paragraph in page:
        text = (paragraph.text or '').strip()
        if _display_heading(paragraph):
            # Adjacent display headings form one logical title (e.g. Title + Subtitle).
            # Only split an already-started page chunk when it is long enough to
            # plausibly contain multiple naturally-paginated Word pages.
            if split_internal and body and any(line.strip() for line in body):
                flush()
            elif body and any(line.strip() for line in body):
                body.append(paragraph_to_markdown(paragraph))
                continue
            if text:
                title_parts.append(text.replace('\n', ' '))
            continue
        md = paragraph_to_markdown(paragraph)
        if not title_parts and not body and text:
            # Layout-heavy templates often use Normal for a short page title,
            # but a page may also simply start with prose. Never truncate or
            # consume a long first paragraph as a synthetic title.
            clean = text.replace('\n', ' ').strip()
            if len(clean) <= 80:
                title_parts = [clean]
                continue
            number = chapter_offset + len(chapters) + 1
            title_parts = [tr('docx.import.fallback_part', 'Deel {number}', number=number)]
            body.append(md)
            continue
        body.append(md)
    flush()
    return chapters


def _parse_page_oriented_docx(doc, source: Path, paragraphs, warnings: list[str]) -> DocxImportResult:
    pages = _page_chunks(paragraphs)
    chapters: list[dict] = []
    for page in pages:
        chapters.extend(_page_to_chapters(page, chapter_offset=len(chapters)))

    core_title = str(doc.core_properties.title or '').strip()
    if _generic_word_title(core_title) and pages:
        first_nonempty = next(((p.text or '').strip() for p in pages[0] if (p.text or '').strip()), '')
        core_title = first_nonempty or source.stem
    return DocxImportResult(
        title=core_title or source.stem,
        author=str(doc.core_properties.author or '').strip(),
        language=_document_default_language(doc),
        sections=((None, tuple(chapters)),),
        warnings=tuple(warnings),
    )

def parse_docx_book(source: Path) -> DocxImportResult:
    """Read a DOCX conservatively into QuietWriter sections/chapters.

    QuietWriter-created DOCX files use custom paragraph styles for unambiguous
    section/chapter boundaries. For ordinary Word documents, Heading 1 is treated
    as chapter headings unless Heading 2 is also present; with Heading 2 present,
    Heading 1 becomes a section and Heading 2 a chapter.
    """
    source = Path(source)
    doc = Document(str(source))
    warnings: list[str] = []
    if doc.tables:
        warnings.append(tr('docx.import.tables_not_imported', '{count} tabel(len) zijn niet geïmporteerd.', count=len(doc.tables)))
    try:
        image_count = sum(1 for rel in doc.part.rels.values() if rel.reltype == RT.IMAGE)
    except Exception:
        image_count = 0
    if image_count:
        warnings.append(tr('docx.import.images_not_imported', '{count} afbeelding(en) uit het Word-document zijn nog niet geïmporteerd.', count=image_count))

    paragraphs = list(doc.paragraphs)
    styles = [_style_name(p) for p in paragraphs]
    has_qw = any(s in {'QuietWriter Section', 'QuietWriter Chapter'} for s in styles)
    has_h2 = any(re.match(r'^Heading\s+2$', s, re.I) for s in styles)
    page_break_count = sum(1 for p in paragraphs if _paragraph_has_page_break(p))
    first_heading = next((i for i, s in enumerate(styles) if re.match(r'^Heading\s+[1-6]$', s, re.I)), None)
    breaks_before_heading = 0 if first_heading is None else sum(1 for p in paragraphs[:first_heading] if _paragraph_has_page_break(p))
    has_title_style = any(str(s).lower() in {'title', 'subtitle'} for s in styles)
    if not has_qw and page_break_count >= 2 and (has_title_style or breaks_before_heading >= 1):
        return _parse_page_oriented_docx(doc, source, paragraphs, warnings)

    groups: list[tuple[str | None, list[dict]]] = []
    current_section: str | None = None
    current_title: str | None = None
    current_lines: list[str] = []
    preamble: list[str] = []

    def ensure_group(title: str | None):
        nonlocal current_section
        if not groups or groups[-1][0] != title:
            groups.append((title, []))
        current_section = title

    def flush_chapter():
        nonlocal current_title, current_lines, preamble
        if current_title is None:
            return
        if not groups:
            ensure_group(current_section)
        text = '\n'.join(current_lines).rstrip('\n')
        groups[-1][1].append({'title': current_title, 'text': text})
        current_title = None
        current_lines = []

    def start_chapter(title: str):
        nonlocal current_title, current_lines, preamble
        flush_chapter()
        if not groups:
            ensure_group(current_section)
        current_title = title.strip() or 'Hoofdstuk'
        current_lines = []
        if preamble:
            current_lines.extend(preamble)
            preamble = []

    for p in paragraphs:
        style = _style_name(p)
        text = ''.join(run.text for run in p.runs).strip()
        is_section = style == 'QuietWriter Section' or (not has_qw and has_h2 and bool(re.match(r'^Heading\s+1$', style, re.I)))
        is_chapter = style == 'QuietWriter Chapter' or (
            not has_qw and ((has_h2 and bool(re.match(r'^Heading\s+2$', style, re.I))) or (not has_h2 and bool(re.match(r'^Heading\s+1$', style, re.I))))
        )
        if is_section and text:
            flush_chapter()
            ensure_group(text)
            continue
        if is_chapter and text:
            start_chapter(text)
            continue
        md = paragraph_to_markdown(p)
        if current_title is None:
            # QuietWriter DOCX files contain a generated title/front-matter area
            # before the first explicit chapter. Those publication pages are not
            # manuscript chapters on re-import. External DOCX files keep their
            # pre-heading text as a first chapter.
            if not has_qw:
                preamble.append(md)
        else:
            current_lines.append(md)

    flush_chapter()
    if preamble:
        if not groups:
            groups.append((None, []))
        title = str(doc.core_properties.title or '').strip() or source.stem
        groups[-1][1].insert(0, {'title': title, 'text': '\n'.join(preamble).rstrip('\n')})
    if not any(chapters for _, chapters in groups):
        title = str(doc.core_properties.title or '').strip() or source.stem
        groups = [(None, [{'title': title, 'text': ''}])]

    return DocxImportResult(
        title=str(doc.core_properties.title or '').strip() or source.stem,
        author=str(doc.core_properties.author or '').strip(),
        language=_document_default_language(doc),
        sections=tuple((section, tuple(chapters)) for section, chapters in groups),
        warnings=tuple(warnings),
    )


def _ensure_styles(doc: Document):
    styles = doc.styles
    if 'QuietWriter Section' not in styles:
        style = styles.add_style('QuietWriter Section', WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = styles['Heading 1']
    if 'QuietWriter Chapter' not in styles:
        style = styles.add_style('QuietWriter Chapter', WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = styles['Heading 2']
    if 'QuietWriter Code' not in styles:
        style = styles.add_style('QuietWriter Code', WD_STYLE_TYPE.CHARACTER)
        style.font.name = 'Consolas'
        style.font.size = Pt(10)


def _append_inline(paragraph, source: str, doc: Document):
    spans = parse_inline_spans(source)
    if not spans:
        paragraph.add_run(source)
        return
    marker_positions: set[int] = set()
    for span in spans:
        for a, b in span.marker_ranges:
            marker_positions.update(range(a, b))

    def active_at(pos: int) -> frozenset[str]:
        return frozenset(span.kind for span in spans if span.content_start <= pos < span.content_end)

    start = None
    styles = frozenset()
    for i in range(len(source) + 1):
        if i < len(source) and i in marker_positions:
            if start is not None:
                _add_run(paragraph, source[start:i], styles, doc)
                start = None
            continue
        current = active_at(i) if i < len(source) else frozenset()
        if start is None:
            start = i
            styles = current
        elif current != styles or i == len(source):
            _add_run(paragraph, source[start:i], styles, doc)
            start = i
            styles = current
    if start is not None and start < len(source):
        _add_run(paragraph, source[start:], styles, doc)


def _add_run(paragraph, text: str, styles: frozenset[str], doc: Document):
    if not text:
        return
    run = paragraph.add_run(text)
    run.bold = 'bold' in styles
    run.italic = 'italic' in styles
    run.underline = 'underline' in styles
    run.font.strike = 'strike' in styles
    if 'code' in styles:
        run.style = doc.styles['QuietWriter Code']



def _language_tag(language: str) -> str:
    value = (language or '').strip().replace('_', '-').lower()
    if value.startswith('nl'):
        return 'nl-NL'
    if value.startswith('en'):
        return 'en-US'
    if value.startswith('de'):
        return 'de-DE'
    if value.startswith('fr'):
        return 'fr-FR'
    if value.startswith('es'):
        return 'es-ES'
    return language or 'nl-NL'


def _set_rpr_language(rpr, tag: str):
    lang = rpr.find(qn('w:lang'))
    if lang is None:
        lang = OxmlElement('w:lang')
        rpr.append(lang)
    lang.set(qn('w:val'), tag)
    lang.set(qn('w:eastAsia'), tag)


def _set_document_language(doc: Document, language: str):
    tag = _language_tag(language)
    styles_el = doc.styles.element
    defaults = styles_el.find(qn('w:docDefaults'))
    if defaults is None:
        defaults = OxmlElement('w:docDefaults')
        styles_el.insert(0, defaults)
    rpr_default = defaults.find(qn('w:rPrDefault'))
    if rpr_default is None:
        rpr_default = OxmlElement('w:rPrDefault'); defaults.append(rpr_default)
    rpr = rpr_default.find(qn('w:rPr'))
    if rpr is None:
        rpr = OxmlElement('w:rPr'); rpr_default.append(rpr)
    _set_rpr_language(rpr, tag)
    for style_name in ('Normal', 'Title', 'Subtitle', 'Heading 1', 'Heading 2', 'Heading 3', 'Quote', 'List Bullet', 'List Number', 'QuietWriter Section', 'QuietWriter Chapter'):
        try:
            style = doc.styles[style_name]
        except KeyError:
            continue
        rpr = style.element.get_or_add_rPr()
        _set_rpr_language(rpr, tag)


def _content_box(section):
    return (
        int(section.page_width - section.left_margin - section.right_margin),
        max(1, int(section.page_height - section.top_margin - section.bottom_margin - Pt(18))),
    )


def _add_picture_fit(paragraph, data: bytes, max_width: int, max_height: int, *, allow_upscale: bool = False):
    image = DocxImage.from_blob(data)
    width, height = int(image.width), int(image.height)
    if width <= 0 or height <= 0:
        return paragraph.add_run().add_picture(BytesIO(data))
    scale = min(max_width / width, max_height / height)
    if not allow_upscale:
        scale = min(scale, 1.0)
    width = max(1, int(width * scale)); height = max(1, int(height * scale))
    return paragraph.add_run().add_picture(BytesIO(data), width=width, height=height)

def _asset_map(export_document) -> dict[str, object]:
    result = {}
    for asset in export_document.assets:
        if asset.role != 'inline':
            continue
        result[asset.filename] = asset
        result[Path(asset.filename).name] = asset
    return result


def _append_markdown(doc: Document, markdown: str, export_document):
    assets = _asset_map(export_document)
    for raw in (markdown or '').replace('\r\n', '\n').replace('\r', '\n').split('\n'):
        stripped = raw.strip()
        image = image_reference_for_line(stripped) if stripped else None
        if image:
            p = doc.add_paragraph()
            asset = assets.get(Path(image.path).name) or assets.get(image.path)
            if asset:
                try:
                    max_width, max_height = _content_box(doc.sections[-1])
                    _add_picture_fit(p, asset.data, max_width, max_height)
                except Exception:
                    _append_inline(p, image.alt or Path(image.path).name, doc)
            else:
                _append_inline(p, image.alt or Path(image.path).name, doc)
            if image.caption:
                cp = doc.add_paragraph()
                cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = cp.add_run(image.caption); r.italic = True
            continue
        if is_scene_break_line(raw):
            p = doc.add_paragraph('***')
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            continue
        if stripped.startswith('## '):
            p = doc.add_paragraph(style='Heading 3')
            _append_inline(p, stripped[3:], doc)
            continue
        if stripped.startswith('> '):
            p = doc.add_paragraph(style='Quote')
            _append_inline(p, stripped[2:], doc)
            continue
        if re.match(r'^[-*]\s+', stripped):
            p = doc.add_paragraph(style='List Bullet')
            _append_inline(p, re.sub(r'^[-*]\s+', '', stripped), doc)
            continue
        if re.match(r'^\d+\.\s+', stripped):
            p = doc.add_paragraph(style='List Number')
            _append_inline(p, re.sub(r'^\d+\.\s+', '', stripped), doc)
            continue
        p = doc.add_paragraph()
        _append_inline(p, raw, doc)


def export_docx(export_document, destination: Path, settings: dict | None = None) -> Path:
    """Export a QuietWriter snapshot to an editable DOCX document."""
    destination = Path(destination)
    doc = Document()
    for section in doc.sections:
        section.page_width = Mm(210)
        section.page_height = Mm(297)
    _ensure_styles(doc)
    _set_document_language(doc, export_document.language)
    doc.core_properties.title = export_document.title
    doc.core_properties.author = export_document.author

    if export_document.cover_asset:
        cover_p = doc.add_paragraph()
        cover_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        max_width, max_height = _content_box(doc.sections[-1])
        try:
            _add_picture_fit(cover_p, export_document.cover_asset.data, max_width, max_height, allow_upscale=True)
        except Exception:
            pass

    title = doc.add_paragraph(style='Title')
    if export_document.cover_asset:
        title.paragraph_format.page_break_before = True
    title.add_run(export_document.title)
    if export_document.author:
        author = doc.add_paragraph()
        author.alignment = WD_ALIGN_PARAGRAPH.CENTER
        author.add_run(export_document.author)
    doc.add_page_break()

    # Textual publication front matter remains editable Word text. Structured
    # title/copyright widgets are deliberately not duplicated beyond the title page.
    for item in export_document.front_matter:
        if item.kind == 'text' and item.text.strip():
            _append_markdown(doc, item.text, export_document)
            doc.add_page_break()

    multiple_sections = len(export_document.sections) > 1
    started_chapter = False
    for section in export_document.sections:
        show_section = multiple_sections or (section.title and section.id != 'root' and section.title.lower() != 'manuscript')
        if show_section:
            section_p = doc.add_paragraph(section.title, style='QuietWriter Section')
            if started_chapter:
                section_p.paragraph_format.page_break_before = True
        for chapter_index, chapter in enumerate(section.chapters):
            chapter_p = doc.add_paragraph(chapter.title, style='QuietWriter Chapter')
            if started_chapter and not (show_section and chapter_index == 0):
                chapter_p.paragraph_format.page_break_before = True
            _append_markdown(doc, chapter.markdown, export_document)
            started_chapter = True

    for item in export_document.back_matter:
        if item.kind == 'text' and item.text.strip():
            doc.add_page_break()
            _append_markdown(doc, item.text, export_document)

    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + '.tmp')
    doc.save(str(tmp))
    tmp.replace(destination)
    return destination
