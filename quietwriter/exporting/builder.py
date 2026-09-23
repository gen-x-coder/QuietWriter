from __future__ import annotations

import copy
import mimetypes
from pathlib import Path

from ..publication_models import BACK_MATTER, FRONT_MATTER
from ..publication_storage import PublicationStore
from ..storage import slugify
from ..media.markup import find_image_references
from ..media.store import MediaStore, MediaError
from .models import ExportAsset, ExportChapter, ExportDocument, ExportItem, ExportSection


_MEDIA_TYPES = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.webp': 'image/webp',
}


def _asset_for_cover(path: Path | None) -> ExportAsset | None:
    if not path or not Path(path).is_file():
        return None
    path = Path(path)
    media_type = _MEDIA_TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    return ExportAsset(
        id='cover-source',
        filename=path.name,
        media_type=media_type,
        data=path.read_bytes(),
        role='cover',
    )


def _inline_assets_for_markdown(media: MediaStore, book, source_file: str, markdown: str, assets_by_file: dict[str, ExportAsset], missing: list[str]):
    for ref in find_image_references(markdown):
        try:
            asset, data = media.read_verified_reference(book, source_file, ref.path)
        except MediaError as exc:
            label = ref.alt.strip() or Path(ref.path).name
            message = f'{label}: {exc}'
            if message not in missing:
                missing.append(message)
            continue
        if asset.file in assets_by_file:
            continue
        assets_by_file[asset.file] = ExportAsset(
            id=f'inline-{asset.id}', filename=Path(asset.file).name,
            media_type=asset.media_type, data=data, role='inline',
        )


def build_export_document(library, book) -> ExportDocument:
    """Capture one coherent, immutable snapshot of the current saved book."""

    library.verify_book_unchanged(book)
    metadata = copy.deepcopy(book.metadata or {})
    publication_store = PublicationStore(library)
    publication = publication_store.load(book)
    media = MediaStore(library)
    inline_assets: dict[str, ExportAsset] = {}
    missing_assets: list[str] = []

    sections: list[ExportSection] = []
    for section in book.sections:
        chapter_rows: list[ExportChapter] = []
        for chapter in section.chapters:
            markdown = library.read_chapter(book, chapter)
            _inline_assets_for_markdown(media, book, chapter.file, markdown, inline_assets, missing_assets)
            chapter_rows.append(ExportChapter(id=chapter.id, title=chapter.title, markdown=markdown))
        sections.append(ExportSection(id=section.id, title=section.title, chapters=tuple(chapter_rows)))

    def publication_items(definitions, zone: str) -> tuple[ExportItem, ...]:
        rows: list[ExportItem] = []
        enabled = set(publication.enabled)
        for key, _label, kind in definitions:
            if key not in enabled:
                continue
            data = {}
            text = ''
            if key == 'title_page':
                data = copy.deepcopy(publication.title_page)
            elif key == 'copyright':
                data = copy.deepcopy(publication.copyright)
            elif key == 'epigraph':
                data = copy.deepcopy(publication.epigraph)
            elif key == 'contents':
                data = copy.deepcopy(publication.contents)
            elif kind == 'text':
                text = publication_store.load_text(book, key)
                _inline_assets_for_markdown(media, book, f'publication/texts/{key}.md', text, inline_assets, missing_assets)
            rows.append(ExportItem(key=key, kind=kind, data=data, text=text))
        return tuple(rows)

    cover = _asset_for_cover(library.cover_path(book))
    assets = tuple(([cover] if cover else []) + list(inline_assets.values()))
    title_page_author = str((publication.title_page or {}).get('author') or '').strip()
    author = str(metadata.get('author') or title_page_author).strip()
    language = str(metadata.get('language') or 'nl').strip() or 'nl'
    copyright_data = publication.copyright or {}
    epub_isbn = str(copyright_data.get('isbn_epub') or '').strip()

    # Verify once more after every source file was read. This catches a sync tool
    # replacing a chapter/publication file while the snapshot was being built.
    library.verify_book_unchanged(book)

    return ExportDocument(
        id=book.id,
        title=book.title,
        author=author,
        language=language,
        slug=str(metadata.get('slug') or slugify(book.title)),
        metadata=metadata,
        sections=tuple(sections),
        front_matter=publication_items(FRONT_MATTER, 'front'),
        back_matter=publication_items(BACK_MATTER, 'back'),
        assets=assets,
        cover_asset_id=cover.id if cover else None,
        epub_isbn=epub_isbn,
        missing_assets=tuple(missing_assets),
    )
