from __future__ import annotations

import html
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

from .cover import render_cover
from .markup import markdown_to_xhtml, markdown_to_xhtml_with_headings
from .models import ExportDocument, ExportItem
from .templates import template_css


XHTML_NS = 'http://www.w3.org/1999/xhtml'
OPF_NS = 'http://www.idpf.org/2007/opf'
DC_NS = 'http://purl.org/dc/elements/1.1/'


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


def _item_label(key: str, language: str) -> str:
    code = (language or 'nl').lower().split('-', 1)[0]
    return _ITEM_LABELS.get(code, _ITEM_LABELS['en']).get(key, key.replace('_', ' ').title())


def _xhtml(title: str, body: str, language: str = 'nl', body_class: str = '') -> str:
    cls = f' class="{html.escape(body_class, quote=True)}"' if body_class else ''
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<html xmlns="{XHTML_NS}" xml:lang="{html.escape(language, quote=True)}" lang="{html.escape(language, quote=True)}">\n'
        '<head>\n'
        f'  <title>{html.escape(title)}</title>\n'
        '  <meta charset="utf-8"/>\n'
        '  <link rel="stylesheet" type="text/css" href="../styles/book.css"/>\n'
        '</head>\n'
        f'<body{cls}>\n{body}\n</body>\n</html>\n'
    )


def _publication_item_body(item: ExportItem, document: ExportDocument, image_hrefs: dict[str, str] | None = None) -> str:
    data = item.data or {}
    if item.key == 'title_page':
        title = str(data.get('title') or document.title)
        subtitle = str(data.get('subtitle') or '').strip()
        author = str(data.get('author') or document.author).strip()
        publisher = str(data.get('publisher') or '').strip()
        parts = [f'<section class="title-page"><h1>{html.escape(title)}</h1>']
        if subtitle: parts.append(f'<p class="subtitle">{html.escape(subtitle)}</p>')
        if author: parts.append(f'<p class="author">{html.escape(author)}</p>')
        if publisher: parts.append(f'<p class="publisher">{html.escape(publisher)}</p>')
        parts.append('</section>')
        return ''.join(parts)
    if item.key == 'copyright':
        rows: list[str] = ['<section class="copyright-page">']
        author = str(data.get('author') or document.author).strip()
        year = str(data.get('year') or '').strip()
        publisher = str(data.get('publisher') or '').strip()
        edition = str(data.get('edition') or '').strip()
        if author or year: rows.append(f'<p>© {html.escape(year)} {html.escape(author)}</p>')
        if edition: rows.append(f'<p>{html.escape(edition)}</p>')
        if publisher: rows.append(f'<p>{html.escape(publisher)}</p>')
        isbn = str(data.get('isbn_epub') or '').strip()
        if isbn: rows.append(f'<p>ISBN EPUB: {html.escape(isbn)}</p>')
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
        if quote: rows.append(f'<blockquote><p>{html.escape(quote)}</p></blockquote>')
        if source: rows.append(f'<p class="source">{html.escape(source)}</p>')
        rows.append('</section>')
        return ''.join(rows)
    if item.kind == 'text':
        return markdown_to_xhtml(item.text, image_hrefs)
    return ''


def _toc_body(
    document: ExportDocument,
    chapter_paths: list[tuple[str, str]],
    section_paths: list[tuple[str, str]],
    chapter_headings: dict[str, list[tuple[str, str]]] | None = None,
    depth: str = 'chapters',
) -> str:
    def local_href(href: str) -> str:
        return href[5:] if href.startswith('text/') else href

    include_headings = str(depth or 'chapters') == 'headings'
    chapter_headings = chapter_headings or {}

    def chapter_row(chref: str, ctitle: str) -> str:
        parts = [f'<li><a href="{html.escape(local_href(chref), quote=True)}">{html.escape(ctitle)}</a>']
        headings = chapter_headings.get(chref, ()) if include_headings else ()
        if headings:
            parts.append('<ol>')
            base = local_href(chref)
            for heading_id, label in headings:
                href = f'{base}#{heading_id}'
                parts.append(f'<li><a href="{html.escape(href, quote=True)}">{html.escape(label)}</a></li>')
            parts.append('</ol>')
        parts.append('</li>')
        return ''.join(parts)

    by_section: dict[str, list[tuple[str, str]]] = {}
    chapter_index = 0
    for section in document.sections:
        rows = []
        for _chapter in section.chapters:
            rows.append(chapter_paths[chapter_index]); chapter_index += 1
        by_section[section.id] = rows
    heading = _item_label('contents', document.language)
    parts = [f'<section><h1 class="chapter-title">{html.escape(heading)}</h1><ol class="contents-list">']
    for section, section_href in zip(document.sections, section_paths, strict=True):
        chapters = by_section.get(section.id, [])
        if len(document.sections) > 1 or section.id != 'root':
            href, label = section_href
            parts.append(f'<li><a href="{html.escape(local_href(href), quote=True)}">{html.escape(label)}</a>')
            if chapters:
                parts.append('<ol>')
                for chref, ctitle in chapters:
                    parts.append(chapter_row(chref, ctitle))
                parts.append('</ol>')
            parts.append('</li>')
        else:
            for chref, ctitle in chapters:
                parts.append(chapter_row(chref, ctitle))
    parts.append('</ol></section>')
    return ''.join(parts)


def export_epub(document: ExportDocument, destination: Path, settings: dict) -> Path:
    destination = Path(destination)
    epub = dict(settings.get('epub') or {})
    template = str(epub.get('template') or 'classic')
    include_cover = bool(epub.get('include_cover', True))
    cover_mode = str(epub.get('cover_mode') or 'artwork_only')
    show_section_titles = bool(epub.get('show_section_titles', True))
    language = document.language or 'nl'

    files: dict[str, bytes] = {}
    manifest: list[tuple[str, str, str, str]] = []  # id, href, media, properties
    spine: list[str] = []
    nav_entries: list[tuple[str, str]] = []
    xhtml_labels: dict[str, str] = {}

    css = template_css(template).encode('utf-8')
    files['EPUB/styles/book.css'] = css
    manifest.append(('css', 'styles/book.css', 'text/css', ''))

    image_hrefs: dict[str, str] = {}
    inline_index = 0
    for asset in document.assets:
        if asset.role != 'inline':
            continue
        inline_index += 1
        href = f'images/{asset.filename}'
        files['EPUB/' + href] = asset.data
        manifest.append((f'inline-image-{inline_index:03d}', href, asset.media_type, ''))
        # XHTML lives in EPUB/text, hence ../images. Source Markdown references
        # are resolved by basename because managed UUID filenames are unique.
        image_hrefs[asset.filename] = f'../{href}'

    # Cover image + cover page come first in reading order when requested.
    if include_cover and document.cover_asset:
        rendered = render_cover(document.cover_asset, document.title, document.author, cover_mode)
        img_href = f'images/{rendered.filename}'
        files['EPUB/' + img_href] = rendered.data
        manifest.append(('cover-image', img_href, rendered.media_type, 'cover-image'))
        cover_body = f'<div class="cover-page"><img src="../{html.escape(img_href, quote=True)}" alt="{html.escape(document.title, quote=True)}"/></div>'
        files['EPUB/text/cover.xhtml'] = _xhtml(document.title, cover_body, language, 'cover-page').encode('utf-8')
        xhtml_labels['EPUB/text/cover.xhtml'] = document.title
        manifest.append(('cover-page', 'text/cover.xhtml', 'application/xhtml+xml', ''))
        spine.append('cover-page')

    item_counter = 0
    contents_placeholder: tuple[int, int, ExportItem] | None = None
    for item in document.front_matter:
        if item.key == 'contents':
            contents_placeholder = (len(spine), len(nav_entries), item); item_counter += 1; continue
        item_id = f'front-{item_counter:02d}-{item.key}'
        href = f'text/{item_id}.xhtml'
        body = _publication_item_body(item, document, image_hrefs)
        label = _item_label(item.key, language)
        files['EPUB/' + href] = _xhtml(label, body, language).encode('utf-8')
        xhtml_labels['EPUB/' + href] = label
        manifest.append((item_id, href, 'application/xhtml+xml', ''))
        spine.append(item_id)
        nav_entries.append((href, label))
        item_counter += 1

    chapter_paths: list[tuple[str, str]] = []
    chapter_headings: dict[str, list[tuple[str, str]]] = {}
    section_paths: list[tuple[str, str]] = []
    multiple_sections = len(document.sections) > 1 or any(s.id != 'root' for s in document.sections)
    for sidx, section in enumerate(document.sections, 1):
        if multiple_sections and show_section_titles:
            sid = f'section-{sidx:03d}'
            shref = f'text/{sid}.xhtml'
            sbody = f'<section class="section-page"><h1 class="section-title">{html.escape(section.title)}</h1></section>'
            files['EPUB/' + shref] = _xhtml(section.title, sbody, language).encode('utf-8')
            xhtml_labels['EPUB/' + shref] = section.title
            manifest.append((sid, shref, 'application/xhtml+xml', ''))
            spine.append(sid); nav_entries.append((shref, section.title))
            section_paths.append((shref, section.title))
        else:
            # ToC can link to first chapter when no dedicated section page exists.
            section_paths.append(('', section.title))

        first_chapter_href = ''
        for cidx, chapter in enumerate(section.chapters, 1):
            cid = f'chapter-{sidx:03d}-{cidx:03d}'
            href = f'text/{cid}.xhtml'
            if not first_chapter_href: first_chapter_href = href
            chapter_body, headings = markdown_to_xhtml_with_headings(chapter.markdown, image_hrefs)
            body = f'<article><h1 class="chapter-title">{html.escape(chapter.title)}</h1>{chapter_body}</article>'
            files['EPUB/' + href] = _xhtml(chapter.title, body, language).encode('utf-8')
            xhtml_labels['EPUB/' + href] = chapter.title
            manifest.append((cid, href, 'application/xhtml+xml', ''))
            spine.append(cid); nav_entries.append((href, chapter.title)); chapter_paths.append((href, chapter.title))
            chapter_headings[href] = headings
        if section_paths[-1][0] == '':
            section_paths[-1] = (first_chapter_href, section.title)

    # Generated in-book contents page belongs at the configured front-matter position.
    if contents_placeholder is not None:
        spine_index, nav_index, contents_item = contents_placeholder
        toc_id = 'front-contents'
        toc_href = 'text/contents.xhtml'
        toc_label = _item_label('contents', language)
        toc_depth = str((contents_item.data or {}).get('depth') or 'chapters')
        toc_body = _toc_body(document, chapter_paths, section_paths, chapter_headings, toc_depth)
        files['EPUB/' + toc_href] = _xhtml(toc_label, toc_body, language).encode('utf-8')
        xhtml_labels['EPUB/' + toc_href] = toc_label
        manifest.append((toc_id, toc_href, 'application/xhtml+xml', ''))
        # Insert at the exact position occupied by Contents in the publication
        # structure, even though its links can only be generated after chapters.
        spine.insert(spine_index, toc_id)
        nav_entries.insert(nav_index, (toc_href, toc_label))

    back_counter = 0
    for item in document.back_matter:
        item_id = f'back-{back_counter:02d}-{item.key}'
        href = f'text/{item_id}.xhtml'
        body = _publication_item_body(item, document, image_hrefs)
        label = _item_label(item.key, language)
        files['EPUB/' + href] = _xhtml(label, body, language).encode('utf-8')
        xhtml_labels['EPUB/' + href] = label
        manifest.append((item_id, href, 'application/xhtml+xml', ''))
        spine.append(item_id)
        nav_entries.append((href, label))
        back_counter += 1

    # EPUB 3 navigation document. When the configured generated contents
    # includes manuscript headings, expose the same chapter-local anchors here
    # as nested navigation entries.
    nav_include_headings = False
    if contents_placeholder is not None:
        nav_include_headings = str((contents_placeholder[2].data or {}).get('depth') or 'chapters') == 'headings'
    nav_rows: list[str] = []
    for href, label in nav_entries:
        nav_rows.append(f'<li><a href="{html.escape(href, quote=True)}">{html.escape(label)}</a>')
        headings = chapter_headings.get(href, ()) if nav_include_headings else ()
        if headings:
            nav_rows.append('<ol>')
            for heading_id, heading_label in headings:
                target = f'{href}#{heading_id}'
                nav_rows.append(f'<li><a href="{html.escape(target, quote=True)}">{html.escape(heading_label)}</a></li>')
            nav_rows.append('</ol>')
        nav_rows.append('</li>')
    nav_list = ''.join(nav_rows)
    nav_heading = _item_label('contents', language)
    nav_body = f'<nav epub:type="toc" id="toc"><h1>{html.escape(nav_heading)}</h1><ol>{nav_list}</ol></nav>'
    nav_doc = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<html xmlns="{XHTML_NS}" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{html.escape(language, quote=True)}" lang="{html.escape(language, quote=True)}">'
        f'<head><title>{html.escape(nav_heading)}</title><meta charset="utf-8"/><link rel="stylesheet" type="text/css" href="styles/book.css"/></head><body>{nav_body}</body></html>'
    )
    files['EPUB/nav.xhtml'] = nav_doc.encode('utf-8')
    xhtml_labels['EPUB/nav.xhtml'] = nav_heading
    manifest.append(('nav', 'nav.xhtml', 'application/xhtml+xml', 'nav'))

    if document.epub_isbn:
        identifier = document.epub_isbn if document.epub_isbn.lower().startswith('urn:') else f'urn:isbn:{document.epub_isbn}'
    else:
        identifier = f'urn:uuid:{document.id}'
    modified = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    manifest_xml = ''.join(
        f'<item id="{html.escape(mid, quote=True)}" href="{html.escape(href, quote=True)}" media-type="{media}"' +
        (f' properties="{html.escape(props, quote=True)}"' if props else '') + '/>'
        for mid, href, media, props in manifest
    )
    spine_xml = ''.join(f'<itemref idref="{html.escape(item, quote=True)}"/>' for item in spine)
    creator = f'<dc:creator>{html.escape(document.author)}</dc:creator>' if document.author else ''
    package = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<package xmlns="{OPF_NS}" xmlns:dc="{DC_NS}" version="3.0" unique-identifier="pub-id" xml:lang="{html.escape(language, quote=True)}">'
        '<metadata>'
        f'<dc:identifier id="pub-id">{html.escape(identifier)}</dc:identifier>'
        f'<dc:title>{html.escape(document.title)}</dc:title>{creator}'
        f'<dc:language>{html.escape(language)}</dc:language>'
        f'<meta property="dcterms:modified">{modified}</meta>'
        '</metadata>'
        f'<manifest>{manifest_xml}</manifest>'
        f'<spine>{spine_xml}</spine>'
        '</package>'
    )
    files['EPUB/package.opf'] = package.encode('utf-8')
    files['META-INF/container.xml'] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '<rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles>'
        '</container>'
    ).encode('utf-8')

    # Catch malformed XML before creating a file. This is intentionally a small
    # built-in validator, not a replacement for epubcheck.
    for name, data in files.items():
        if name.endswith(('.xhtml', '.opf', '.xml')):
            try:
                ET.fromstring(data)
            except ET.ParseError as exc:
                label = xhtml_labels.get(name, name)
                raise ValueError(f'Ongeldige EPUB-XHTML in {label}: {exc}') from exc

    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=destination.name + '.', suffix='.tmp', dir=str(destination.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with zipfile.ZipFile(tmp, 'w') as zf:
            zf.writestr('mimetype', b'application/epub+zip', compress_type=zipfile.ZIP_STORED)
            for name, data in files.items():
                zf.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
        os.replace(tmp, destination)
    finally:
        try:
            if tmp.exists(): tmp.unlink()
        except OSError:
            pass
    return destination
