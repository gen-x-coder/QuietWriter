"""Exportvoorbeeld (1.7): precies hetzelfde bestand als de export, maar in een tijdelijke map.

Er wordt niets in de exportmap geschreven en er worden geen exportinstellingen
opgeslagen. Word, PDF en Markdown opent de UI in het programma van de
gebruiker; voor EPUB (Windows heeft daar meestal niets voor) maakt
``epub_preview_page`` één leesbare HTML-pagina uit de hoofdstukken, die
QuietWriter zelf toont.
"""
from __future__ import annotations

import posixpath
import re
import shutil
import tempfile
import time
import uuid
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from .runner import FORMAT_SUFFIXES

PREVIEW_FORMATS = ('epub', 'pdf', 'docx', 'submission', 'markdown')
PREVIEW_DIR_NAME = 'QuietWriter-voorbeeld'


def preview_root() -> Path:
    return Path(tempfile.gettempdir()) / PREVIEW_DIR_NAME


KEEP_SECONDS = 24 * 3600   # oudere voorbeeldmappen worden bij een nieuw voorbeeld opgeruimd


def cleanup_old_previews(now: float | None = None) -> None:
    """Ruim voorbeeldmappen van meer dan een dag oud op. Wat nog open staat, blijft gewoon staan."""
    root = preview_root()
    if not root.is_dir():
        return
    now = time.time() if now is None else now
    for folder in root.iterdir():
        try:
            if folder.is_dir() and now - folder.stat().st_mtime > KEEP_SECONDS:
                shutil.rmtree(folder, ignore_errors=True)
        except OSError:
            continue


def preview_destination(document, format_name: str) -> Path:
    """Tijdelijk doel in een eigen, nieuwe map per voorbeeld (review dev19).

    Zo vervangt een nieuw voorbeeld nooit een vorig voorbeeld dat nog open staat,
    ook niet bij twee QuietWriter-vensters tegelijk. 'voorbeeld' staat in de naam
    zodat het nooit met een echte export verward wordt.
    """
    if format_name not in PREVIEW_FORMATS:
        raise ValueError(f'Geen voorbeeld voor {format_name}')
    cleanup_old_previews()
    folder = preview_root() / f'{time.strftime("%Y%m%d-%H%M%S")}-{uuid.uuid4().hex[:8]}'
    folder.mkdir(parents=True, exist_ok=False)
    return folder / f'{document.slug}-voorbeeld{FORMAT_SUFFIXES[format_name]}'


class PreviewError(Exception):
    """Het e-book kon niet als voorbeeld getoond worden (te groot of onverwachte inhoud)."""


# Ruime grenzen: een QuietWriter-boek met veel afbeeldingen blijft er ver onder.
MAX_ENTRIES = 5000
MAX_UNPACKED_BYTES = 1024 * 1024 * 1024   # 1 GB


def _inside(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise PreviewError(f'Verwijzing buiten het e-book: {path.name}')
    return resolved


_NS = {'c': 'urn:oasis:names:tc:opendocument:xmlns:container', 'opf': 'http://www.idpf.org/2007/opf'}
_BODY_RE = re.compile(r'<body[^>]*>(.*?)</body>', re.S | re.I)
_SCRIPT_RE = re.compile(r'<script\b.*?</script>', re.S | re.I)


def epub_preview_page(epub_path: Path, work_dir: Path | None = None) -> Path:
    """Pak de EPUB uit en schrijf één HTML-pagina met alle hoofdstukken in leesvolgorde.

    De pagina staat in de map van de hoofdstukken, zodat afbeeldingen met hun
    gewone relatieve pad blijven werken. Geeft het pad van die pagina terug.
    """
    epub_path = Path(epub_path)
    work_dir = Path(work_dir) if work_dir else epub_path.with_suffix('')
    shutil.rmtree(work_dir, ignore_errors=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(epub_path) as archive:
        entries = archive.infolist()
        if len(entries) > MAX_ENTRIES or sum(entry.file_size for entry in entries) > MAX_UNPACKED_BYTES:
            raise PreviewError('Het e-book is te groot om hier als voorbeeld te tonen.')
        for entry in entries:
            # Nooit buiten de werkmap schrijven.
            clean = posixpath.normpath(entry.filename)
            if clean.startswith('../') or clean.startswith('/') or clean == '..':
                continue
            archive.extract(entry, work_dir)
    try:
        container = ElementTree.parse(work_dir / 'META-INF' / 'container.xml')
        rootfile = container.find('.//c:rootfile', _NS).get('full-path')
        opf_path = _inside(work_dir / rootfile, work_dir)
        opf = ElementTree.parse(opf_path)
    except (OSError, AttributeError, ElementTree.ParseError) as exc:
        raise PreviewError(f'Het e-book is onleesbaar: {exc}') from exc
    manifest = {item.get('id'): item.get('href') for item in opf.findall('.//opf:manifest/opf:item', _NS)}
    hrefs = [manifest[ref.get('idref')] for ref in opf.findall('.//opf:spine/opf:itemref', _NS)
             if manifest.get(ref.get('idref'))]
    chapters = [_inside(opf_path.parent / href, work_dir) for href in hrefs]
    chapters = [path for path in chapters if path.is_file()]
    base = chapters[0].parent if chapters else opf_path.parent
    parts = []
    for path in chapters:
        text = path.read_text(encoding='utf-8', errors='replace')
        match = _BODY_RE.search(text)
        body = _SCRIPT_RE.sub('', match.group(1) if match else text)
        if path.parent != base:
            # Andere map: afbeeldingen anders aanwijzen is te veel moeite voor een voorbeeld.
            body = re.sub(r'<img\b[^>]*>', '', body)
        parts.append(f'<div class="qw-preview-chapter">{body}</div>')
    css_links = ''.join(
        f'<link rel="stylesheet" href="{posixpath.relpath(_inside(opf_path.parent / href, work_dir).as_posix(), base.as_posix())}"/>'
        for href in manifest.values() if href and href.endswith('.css'))
    page = base / 'quietwriter-voorbeeld.html'
    page.write_text(
        '<!DOCTYPE html><html><head><meta charset="utf-8"/>' + css_links +
        '<style>.qw-preview-chapter{margin-bottom:3em;} img{max-width:100%;}</style></head><body>'
        + ''.join(parts) + '</body></html>',
        encoding='utf-8')
    return page
