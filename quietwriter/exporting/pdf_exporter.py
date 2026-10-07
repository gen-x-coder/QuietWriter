from __future__ import annotations

import html
import os
import re
import tempfile
from pathlib import Path

from .markup import inline_to_xhtml
from ..document_view import content_inline_runs, iter_content_blocks
from .models import ExportDocument, ExportItem


PDF_FLOAT_CAPTION_MAX_CHARS = 90
PDF_FLOAT_CAPTION_MAX_WORDS = 14

_PAPER_MM = {
    'A5': (148.0, 210.0),
    'A4': (210.0, 297.0),
}

_MARGIN_PRESETS = {
    'compact': (13.0, 13.0, 15.0, 14.0),
    'standard': (16.0, 16.0, 18.0, 17.0),
    'wide': (20.0, 20.0, 22.0, 20.0),
}

_TEMPLATE_LABELS = {
    'classic': 'Klassiek',
    'modern': 'Modern',
    'literary': 'Literair',
}

_ITEM_LABELS = {
    'nl': {
        'title_page': 'Titelpagina', 'copyright': 'Copyright', 'dedication': 'Opdracht',
        'epigraph': 'Epigraaf', 'contents': 'Inhoud', 'foreword': 'Voorwoord',
        'preface': 'Inleiding', 'afterword': 'Nawoord', 'acknowledgements': 'Dankwoord',
        'about_author': 'Over de auteur',
    },
    'en': {
        'title_page': 'Title page', 'copyright': 'Copyright', 'dedication': 'Dedication',
        'epigraph': 'Epigraph', 'contents': 'Contents', 'foreword': 'Foreword',
        'preface': 'Preface', 'afterword': 'Afterword', 'acknowledgements': 'Acknowledgements',
        'about_author': 'About the author',
    },
}

_BULLET_RE = re.compile(r'^[-*]\s+(.+)$')
_NUMBER_RE = re.compile(r'^\d+\.\s+(.+)$')


def _item_label(key: str, language: str) -> str:
    code = (language or 'nl').lower().split('-', 1)[0]
    return _ITEM_LABELS.get(code, _ITEM_LABELS['en']).get(key, key.replace('_', ' ').title())


def pdf_float_caption_safe(caption: str) -> bool:
    """Whether a wrapped PDF image has a short enough caption for Qt floats.

    The standalone spike showed that QTextDocument's float implementation is
    reliable for short captions, but a long multi-line caption can overlap the
    neighbouring text. PDF therefore falls back to a normal aligned block when
    the caption grows beyond this deliberately conservative limit.
    """
    value = ' '.join(str(caption or '').split())
    if not value:
        return True
    return len(value) <= PDF_FLOAT_CAPTION_MAX_CHARS and len(value.split()) <= PDF_FLOAT_CAPTION_MAX_WORDS


def _pdf_options(settings: dict) -> dict:
    raw = dict((settings or {}).get('pdf') or {})
    paper = str(raw.get('paper_size') or 'A5').upper()
    if paper not in _PAPER_MM:
        paper = 'A5'
    margin = str(raw.get('margin_preset') or 'standard').lower()
    if margin not in _MARGIN_PRESETS:
        margin = 'standard'
    template = str(raw.get('template') or 'classic').lower()
    if template not in _TEMPLATE_LABELS:
        template = 'classic'
    return {
        'paper_size': paper,
        'margin_preset': margin,
        'template': template,
        'page_numbers': bool(raw.get('page_numbers', True)),
        'running_header': bool(raw.get('running_header', True)),
        'show_section_titles': bool(raw.get('show_section_titles', True)),
    }


def _asset_urls(document: ExportDocument) -> dict[str, str]:
    result: dict[str, str] = {}
    for asset in document.assets:
        if asset.role != 'inline':
            continue
        url = f'qw-asset://{asset.id}'
        result[asset.filename] = url
        result[Path(asset.filename).name] = url
    return result


def _image_url(reference: str, image_urls: dict[str, str]) -> str | None:
    normalized = str(reference or '').replace('\\', '/')
    return image_urls.get(normalized) or image_urls.get(Path(normalized).name)


def _template_css(template: str) -> str:
    if template == 'modern':
        return '''
body { font-family: Georgia, "Times New Roman", serif; font-size: 10.8pt; color: #202020; }
h1, h2, h3 { font-family: Arial, Helvetica, sans-serif; }
h1.chapter-title, h1.section-title { font-size: 17pt; font-weight: normal; margin: 0 0 18px 0; }
h2 { font-size: 13pt; margin: 14px 0 7px 0; page-break-after: avoid; }
p { margin: 0 0 8px 0; line-height: 145%; text-align: left; }
p.indent { text-indent: 0; }
blockquote { border-left: 2px solid #777; margin: 12px 0; padding-left: 12px; }
'''
    if template == 'literary':
        return '''
body { font-family: Georgia, "Times New Roman", serif; font-size: 10.8pt; color: #211e1a; }
h1.chapter-title, h1.section-title { font-size: 17pt; font-weight: normal; letter-spacing: 1px; text-align: center; margin: 0 0 22px 0; }
h2 { font-size: 12.5pt; font-style: italic; font-weight: normal; margin: 15px 0 8px 0; page-break-after: avoid; }
p { margin: 0 0 5px 0; line-height: 150%; text-align: justify; }
p.indent { text-indent: 1.45em; }
blockquote { margin: 14px 24px; font-style: italic; }
'''
    return '''
body { font-family: Georgia, "Times New Roman", serif; font-size: 10.8pt; color: #202020; }
h1.chapter-title, h1.section-title { font-size: 17pt; font-weight: normal; text-align: center; margin: 0 0 20px 0; }
h2 { font-size: 12.5pt; margin: 14px 0 7px 0; page-break-after: avoid; }
p { margin: 0 0 5px 0; line-height: 140%; text-align: justify; }
p.indent { text-indent: 1.25em; }
blockquote { margin: 12px 22px; font-style: italic; }
'''


def _base_css(template: str) -> str:
    return _template_css(template) + '''
h1 { page-break-after: avoid; }
ul, ol { margin-top: 4px; margin-bottom: 8px; }
li { margin-bottom: 3px; }
.scene-break { text-align: center; margin: 14px 0; letter-spacing: 5px; }
.caption { font-family: Arial, Helvetica, sans-serif; font-size: 8pt; color: #555; text-align: center; text-indent: 0; margin: 4px 2px 2px 2px; line-height: 120%; }
.title-page { text-align: center; margin-top: 150px; }
.title-page h1 { font-size: 23pt; font-weight: normal; text-align: center; margin-bottom: 18px; }
.title-page .subtitle { font-size: 13pt; text-align: center; text-indent: 0; }
.title-page .author { margin-top: 42px; text-align: center; text-indent: 0; }
.title-page .publisher { margin-top: 36px; text-align: center; text-indent: 0; font-size: 9pt; }
.copyright-page { font-size: 9pt; }
.epigraph-page { text-align: center; margin-top: 130px; }
.epigraph-page blockquote { margin-left: 25px; margin-right: 25px; }
.epigraph-page .source { text-align: center; text-indent: 0; font-style: italic; }
.section-page { text-align: center; margin-top: 160px; }
.contents-list { list-style: none; margin-left: 0; padding-left: 0; }
.contents-list li { margin: 5px 0; }
.contents-section { font-weight: bold; margin-top: 10px; }
.page-section { }
.page-break { page-break-before: always; }
table.image-box { border-collapse: collapse; }
table.image-box td { padding: 0; }
'''


def _image_table(attrs: dict, href: str, body_width_px: float) -> str:
    fractions = {'small': .30, 'medium': .50, 'large': .70, 'full': 1.0}
    image_width = str(attrs.get('width') or 'full')
    image_align = str(attrs.get('align') or 'center')
    image_wrap = bool(attrs.get('wrap'))
    image_caption = str(attrs.get('caption') or '')
    image_alt = str(attrs.get('alt') or '')

    width = max(90, int(body_width_px * fractions.get(image_width, 1.0)))
    align = image_align if image_align in {'left', 'center', 'right'} else 'center'
    requested_wrap = bool(image_wrap and align in {'left', 'right'} and image_width != 'full')
    wrap = requested_wrap and pdf_float_caption_safe(image_caption)

    if wrap:
        if align == 'left':
            style = f'float:left; width:{width}px; margin:4px 14px 9px 0;'
        else:
            style = f'float:right; width:{width}px; margin:4px 0 9px 14px;'
    else:
        if align == 'left':
            margin = '7px auto 12px 0'
        elif align == 'right':
            margin = '7px 0 12px auto'
        else:
            margin = '8px auto 12px auto'
        style = f'width:{width}px; margin:{margin};'

    caption = (
        f'<tr><td><p class="caption">{html.escape(image_caption)}</p></td></tr>'
        if image_caption else ''
    )
    alt = html.escape(image_alt, quote=True)
    return (
        f'<table class="image-box" cellspacing="0" cellpadding="0" style="{style}">'
        f'<tr><td><img src="{html.escape(href, quote=True)}" width="{width}" alt="{alt}"/></td></tr>'
        f'{caption}</table>'
    )


def _markdown_to_pdf_html(markdown: str, image_urls: dict[str, str], body_width_px: float) -> str:
    blocks: list[str] = []
    list_kind: str | None = None
    list_items: list[tuple[str, tuple]] = []
    after_break_or_heading = True

    def flush_list():
        nonlocal list_kind, list_items
        if list_kind and list_items:
            tag = 'ol' if list_kind == 'ol' else 'ul'
            blocks.append(f'<{tag}>' + ''.join(f'<li>{inline_to_xhtml(item, runs)}</li>' for item, runs in list_items) + f'</{tag}>')
        list_kind = None
        list_items = []

    for block in iter_content_blocks((markdown or '').replace('\r\n', '\n').replace('\r', '\n')):
        if block.kind == 'image':
            flush_list()
            attrs = block.attrs or {}
            image_path = str(attrs.get('path') or '')
            if image_path:
                href = _image_url(image_path, image_urls)
                if href:
                    blocks.append(_image_table(attrs, href, body_width_px))
                else:
                    fallback = str(attrs.get('alt') or attrs.get('caption') or 'Afbeelding ontbreekt')
                    blocks.append(f'<p><em>[{html.escape(fallback)}]</em></p>')
            after_break_or_heading = True
            continue

        if block.kind == 'scene':
            flush_list()
            blocks.append('<div class="scene-break">* * *</div>')
            after_break_or_heading = True
            continue

        content = block.text[block.content_start-block.start:block.content_end-block.start].strip()
        runs = content_inline_runs(block)
        if block.kind == 'heading':
            flush_list()
            blocks.append(f'<h2>{inline_to_xhtml(content, runs)}</h2>')
            after_break_or_heading = True
            continue
        if block.kind == 'quote':
            flush_list()
            blocks.append(f'<blockquote><p>{inline_to_xhtml(content, runs)}</p></blockquote>')
            after_break_or_heading = True
            continue
        if block.kind in {'bullet', 'numbered'}:
            wanted = 'ol' if block.kind == 'numbered' else 'ul'
            if list_kind and list_kind != wanted:
                flush_list()
            list_kind = wanted
            list_items.append((content, runs))
            after_break_or_heading = False
            continue

        flush_list()
        klass = '' if after_break_or_heading else ' class="indent"'
        blocks.append(f'<p{klass}>{inline_to_xhtml(content, runs)}</p>')
        after_break_or_heading = False

    flush_list()
    return ''.join(blocks)


def _publication_item_html(item: ExportItem, document: ExportDocument, image_urls: dict[str, str], body_width_px: float) -> str:
    data = item.data or {}
    if item.key == 'title_page':
        title = str(data.get('title') or document.title)
        subtitle = str(data.get('subtitle') or '').strip()
        author = str(data.get('author') or document.author).strip()
        publisher = str(data.get('publisher') or '').strip()
        rows = [f'<section class="title-page"><h1>{html.escape(title)}</h1>']
        if subtitle:
            rows.append(f'<p class="subtitle">{html.escape(subtitle)}</p>')
        if author:
            rows.append(f'<p class="author">{html.escape(author)}</p>')
        if publisher:
            rows.append(f'<p class="publisher">{html.escape(publisher)}</p>')
        rows.append('</section>')
        return ''.join(rows)

    if item.key == 'copyright':
        rows = ['<section class="copyright-page"><h1>Copyright</h1>']
        author = str(data.get('author') or document.author).strip()
        year = str(data.get('year') or '').strip()
        publisher = str(data.get('publisher') or '').strip()
        edition = str(data.get('edition') or '').strip()
        if author or year:
            rows.append(f'<p>© {html.escape(year)} {html.escape(author)}</p>')
        if edition:
            rows.append(f'<p>{html.escape(edition)}</p>')
        if publisher:
            rows.append(f'<p>{html.escape(publisher)}</p>')
        isbn = str(data.get('isbn_pdf') or '').strip()
        if isbn:
            rows.append(f'<p>ISBN PDF: {html.escape(isbn)}</p>')
        clauses = data.get('clauses') or {}
        for clause in clauses.values():
            if isinstance(clause, dict) and clause.get('enabled') and str(clause.get('text') or '').strip():
                rows.append(f'<p>{html.escape(str(clause["text"]).strip())}</p>')
        rows.append('</section>')
        return ''.join(rows)

    if item.key == 'epigraph':
        quote = str(data.get('quote') or '').strip()
        source = str(data.get('source') or '').strip()
        rows = ['<section class="epigraph-page">']
        if quote:
            rows.append(f'<blockquote><p>{html.escape(quote)}</p></blockquote>')
        if source:
            rows.append(f'<p class="source">{html.escape(source)}</p>')
        rows.append('</section>')
        return ''.join(rows)

    if item.kind == 'text':
        label = _item_label(item.key, document.language)
        return f'<h1 class="chapter-title">{html.escape(label)}</h1>' + _markdown_to_pdf_html(item.text, image_urls, body_width_px)

    return ''


def _contents_html(document: ExportDocument, *, show_section_titles: bool) -> str:
    multiple_sections = len(document.sections) > 1 or any(section.id != 'root' for section in document.sections)
    rows = ['<h1 class="chapter-title">' + html.escape(_item_label('contents', document.language)) + '</h1>', '<ul class="contents-list">']
    for section in document.sections:
        if multiple_sections and show_section_titles:
            rows.append(f'<li class="contents-section">{html.escape(section.title)}</li>')
        for chapter in section.chapters:
            rows.append(f'<li>{html.escape(chapter.title)}</li>')
    rows.append('</ul>')
    return ''.join(rows)


def build_pdf_html(document: ExportDocument, settings: dict, body_width_px: float) -> tuple[str, bool]:
    """Build conservative Qt-rich-text HTML and report whether page 1 is a title page."""
    options = _pdf_options(settings)
    image_urls = _asset_urls(document)
    segments: list[tuple[str, str]] = []  # (kind, html)

    for item in document.front_matter:
        if item.key == 'contents':
            segments.append(('contents', _contents_html(document, show_section_titles=options['show_section_titles'])))
        else:
            body = _publication_item_html(item, document, image_urls, body_width_px)
            if body:
                segments.append((item.key, body))

    multiple_sections = len(document.sections) > 1 or any(section.id != 'root' for section in document.sections)
    for section in document.sections:
        if multiple_sections and options['show_section_titles']:
            segments.append(('section', f'<section class="section-page"><h1 class="section-title">{html.escape(section.title)}</h1></section>'))
        for chapter in section.chapters:
            chapter_html = (
                f'<h1 class="chapter-title">{html.escape(chapter.title)}</h1>'
                + _markdown_to_pdf_html(chapter.markdown, image_urls, body_width_px)
            )
            segments.append(('chapter', chapter_html))

    for item in document.back_matter:
        body = _publication_item_html(item, document, image_urls, body_width_px)
        if body:
            segments.append((item.key, body))

    if not segments:
        segments.append(('chapter', f'<h1 class="chapter-title">{html.escape(document.title)}</h1>'))

    rendered: list[str] = []
    for index, (_kind, body) in enumerate(segments):
        break_class = ' page-break' if index else ''
        rendered.append(f'<div class="page-section{break_class}">{body}</div>')

    first_is_title = bool(segments and segments[0][0] == 'title_page')
    css = _base_css(options['template'])
    return f'<html><head><style>{css}</style></head><body>{"".join(rendered)}</body></html>', first_is_title


def _paper_and_margins(settings: dict) -> tuple[str, tuple[float, float], tuple[float, float, float, float]]:
    options = _pdf_options(settings)
    return options['paper_size'], _PAPER_MM[options['paper_size']], _MARGIN_PRESETS[options['margin_preset']]


def _keep_pdf_tables_together(qdoc, body_h: float, QTextTable, QTextFormat) -> int:
    """Move image tables that cross a QTextDocument page boundary to the next page.

    Qt rich-text CSS does not implement ``page-break-inside: avoid``.  The PDF
    renderer therefore performs a small layout pass after HTML parsing: any
    QTextTable whose bounding rectangle crosses a body-page boundary receives
    an explicit AlwaysBefore page-break policy.  Re-layout can move later tables,
    so repeat a few times until stable.
    """
    moved_total = 0
    if body_h <= 0:
        return 0

    def tables(frame):
        for child in frame.childFrames():
            if isinstance(child, QTextTable):
                yield child
            yield from tables(child)

    for _pass in range(4):
        changed = 0
        layout = qdoc.documentLayout()
        for table in list(tables(qdoc.rootFrame())):
            rect = layout.frameBoundingRect(table)
            if not rect.isValid() or rect.height() <= 0:
                continue
            top_page = int(max(0.0, rect.top()) // body_h)
            # Subtract a tiny epsilon so an exact page-edge does not count as a split.
            bottom = max(rect.top(), rect.bottom() - 0.01)
            bottom_page = int(max(0.0, bottom) // body_h)
            if bottom_page <= top_page:
                continue
            fmt = table.format()
            policy = fmt.pageBreakPolicy()
            wanted = policy | QTextFormat.PageBreakFlag.PageBreak_AlwaysBefore
            if policy == wanted:
                continue
            fmt.setPageBreakPolicy(wanted)
            table.setFormat(fmt)
            changed += 1
            moved_total += 1
        if not changed:
            break
        # Querying documentSize forces the dirty document layout to recalculate.
        qdoc.documentLayout().documentSize()
    return moved_total


def export_pdf(document: ExportDocument, destination: Path, settings: dict) -> Path:
    """Export one immutable snapshot to a paginated PDF using Qt only.

    The renderer intentionally mirrors the proven standalone PDF spike. It uses
    QTextDocument for rich-text pagination and QPdfWriter/QPainter for control of
    margins, running headers and page numbers. No external PDF dependency is
    introduced.
    """
    try:
        from PySide6.QtCore import QMarginsF, QRectF, QSizeF, QUrl, Qt
        from PySide6.QtGui import QColor, QFont, QImage, QPageLayout, QPageSize, QPainter, QPdfWriter, QTextDocument, QTextFormat, QTextTable
    except Exception as exc:  # pragma: no cover - application dependency at runtime
        raise RuntimeError('PDF-export vereist de PySide6/Qt-omgeving van QuietWriter.') from exc

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    options = _pdf_options(settings)
    paper_name, (paper_w_mm, paper_h_mm), margins = _paper_and_margins(settings)
    left_mm, right_mm, top_mm, bottom_mm = margins

    dpi = 144
    header_mm = 6.0 if options['running_header'] else 0.0
    footer_mm = 6.0 if options['page_numbers'] else 0.0
    header_gap_mm = 3.0 if header_mm else 0.0
    footer_gap_mm = 3.0 if footer_mm else 0.0

    def mm(value: float) -> float:
        return value * dpi / 25.4

    page_w = mm(paper_w_mm)
    page_h = mm(paper_h_mm)
    left = mm(left_mm)
    right = mm(right_mm)
    top = mm(top_mm)
    bottom = mm(bottom_mm)
    header_h = mm(header_mm)
    footer_h = mm(footer_mm)
    header_gap = mm(header_gap_mm)
    footer_gap = mm(footer_gap_mm)

    body_x = left
    body_y = top + header_h + header_gap
    body_w = page_w - left - right
    body_h = page_h - body_y - bottom - footer_h - footer_gap
    if body_w <= 0 or body_h <= 0:
        raise ValueError('De gekozen PDF-marges laten geen bruikbaar tekstvlak over.')

    html_text, first_is_title = build_pdf_html(document, settings, body_w)

    fd, tmp_name = tempfile.mkstemp(prefix=destination.name + '.', suffix='.tmp.pdf', dir=str(destination.parent))
    os.close(fd)
    tmp = Path(tmp_name)

    def render_to(path: Path) -> None:
        writer = QPdfWriter(str(path))
        writer.setResolution(dpi)
        page_id = QPageSize.PageSizeId.A4 if paper_name == 'A4' else QPageSize.PageSizeId.A5
        writer.setPageSize(QPageSize(page_id))
        writer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
        writer.setTitle(document.title)
        writer.setCreator('QuietWriter')

        qdoc = QTextDocument()
        # The PDF body rectangle already owns all page margins. QTextDocument's
        # default 4 px documentMargin can otherwise create an extra empty last
        # page when content ends only a few pixels below a page boundary.
        qdoc.setDocumentMargin(0)
        # QTextDocument otherwise converts CSS pt sizes using the screen DPI
        # (typically 96), while QPdfWriter renders at 144 dpi.  Bind the layout
        # to the writer before HTML parsing so 10.8 pt is truly 10.8 pt in PDF.
        qdoc.documentLayout().setPaintDevice(writer)
        qdoc.setDefaultFont(QFont('Georgia', 11))
        qdoc.setPageSize(QSizeF(body_w, body_h))

        for asset in document.assets:
            if asset.role != 'inline':
                continue
            image = QImage.fromData(asset.data)
            if image.isNull():
                raise ValueError(f'Afbeelding kon niet worden gelezen voor PDF: {asset.filename}')
            qdoc.addResource(QTextDocument.ResourceType.ImageResource, QUrl(f'qw-asset://{asset.id}'), image)

        qdoc.setHtml(html_text)
        _keep_pdf_tables_together(qdoc, body_h, QTextTable, QTextFormat)
        page_count = int(qdoc.pageCount())
        if page_count < 1:
            raise ValueError('PDF-export leverde geen pagina\'s op.')

        painter = QPainter(writer)
        if not painter.isActive():
            raise RuntimeError('PDF-renderer kon niet worden gestart.')

        meta_color = QColor('#666666')
        header_font = QFont('Arial', 8)
        footer_font = QFont('Arial', 8)

        try:
            for page_index in range(page_count):
                if page_index:
                    writer.newPage()

                painter.save()
                painter.setClipRect(QRectF(body_x, body_y, body_w, body_h))
                painter.translate(body_x, body_y - page_index * body_h)
                qdoc.drawContents(painter, QRectF(0, page_index * body_h, body_w, body_h))
                painter.restore()

                # A configured title page is intentionally clean. All later pages
                # can carry running matter; when no title page exists, numbering
                # starts immediately on physical page one.
                if first_is_title and page_index == 0:
                    continue

                visible_page = page_index if first_is_title else page_index + 1
                painter.save()
                painter.setPen(meta_color)

                if options['running_header']:
                    painter.setFont(header_font)
                    painter.drawText(
                        QRectF(left, top, body_w, header_h),
                        Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                        document.title,
                    )

                if options['page_numbers']:
                    painter.setFont(footer_font)
                    painter.drawText(
                        QRectF(left, page_h - bottom - footer_h, body_w, footer_h),
                        Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                        str(visible_page),
                    )
                painter.restore()
        finally:
            painter.end()

    try:
        render_to(tmp)
        if not tmp.exists() or tmp.stat().st_size == 0:
            raise ValueError('PDF-export leverde een leeg bestand op.')
        os.replace(tmp, destination)
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass

    return destination
