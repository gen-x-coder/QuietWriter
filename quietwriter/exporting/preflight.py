from __future__ import annotations

from dataclasses import dataclass

from ..media.markup import find_image_references
from .models import ExportDocument
from .pdf_exporter import pdf_float_caption_safe


@dataclass(frozen=True)
class PreflightItem:
    level: str  # ok, warning, error, info
    key: str
    value: str = ''


@dataclass(frozen=True)
class PreflightReport:
    items: tuple[PreflightItem, ...]

    @property
    def can_export(self) -> bool:
        return not any(item.level == 'error' for item in self.items)


def run_preflight(document: ExportDocument, format_name: str, settings: dict) -> PreflightReport:
    rows: list[PreflightItem] = []
    rows.append(PreflightItem('ok' if document.title.strip() else 'error', 'title', document.title.strip()))
    rows.append(PreflightItem('ok' if document.author else 'warning', 'author', document.author))
    rows.append(PreflightItem('ok' if document.language else 'error', 'language', document.language))
    rows.append(PreflightItem('ok' if document.chapter_count else 'error', 'chapters', str(document.chapter_count)))
    if document.missing_assets:
        rows.append(PreflightItem('error', 'missing_assets', '\n'.join(document.missing_assets)))
    elif document.inline_asset_count:
        rows.append(PreflightItem('ok', 'images', str(document.inline_asset_count)))
        if format_name == 'markdown':
            rows.append(PreflightItem('error', 'markdown_images_pending', str(document.inline_asset_count)))

    if format_name == 'pdf':
        fallback_count = 0
        sources = [chapter.markdown for section in document.sections for chapter in section.chapters]
        sources.extend(item.text for item in (*document.front_matter, *document.back_matter) if item.kind == 'text')
        for source in sources:
            for ref in find_image_references(source):
                if ref.wrap and ref.align in {'left', 'right'} and not pdf_float_caption_safe(ref.caption):
                    fallback_count += 1
        if fallback_count:
            rows.append(PreflightItem('warning', 'pdf_wrap_fallback', str(fallback_count)))

    if format_name == 'epub':
        epub = settings.get('epub', {})
        include_cover = bool(epub.get('include_cover', True))
        if include_cover and document.cover_asset:
            rows.append(PreflightItem('ok', 'cover', document.cover_asset.filename))
        elif include_cover:
            rows.append(PreflightItem('warning', 'cover_missing'))
        else:
            rows.append(PreflightItem('info', 'cover_disabled'))
        rows.append(PreflightItem('ok' if document.epub_isbn else 'info', 'isbn', document.epub_isbn))

    return PreflightReport(tuple(rows))
