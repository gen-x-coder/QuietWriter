from __future__ import annotations

from dataclasses import dataclass, field

from .manuscript_markup import serialize_block_source, serialize_inline_text
from .media.markup import build_image_markdown


@dataclass(frozen=True)
class ImportAsset:
    key: str
    filename: str
    media_type: str
    data: bytes


@dataclass(frozen=True)
class ImportInlineRun:
    """Writer-visible imported text plus semantic inline styles.

    Import readers should describe meaning here instead of emitting QuietWriter
    source punctuation directly. The serializer owns escaping and markup syntax.
    """

    text: str
    styles: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ImportBlock:
    kind: str = 'paragraph'
    runs: tuple[ImportInlineRun, ...] = ()
    number: int = 1
    asset_key: str = ''
    alt: str = ''
    caption: str = ''

    @property
    def visible_text(self) -> str:
        return ''.join(run.text for run in self.runs)


@dataclass(frozen=True)
class ImportChapter:
    title: str
    blocks: tuple[ImportBlock, ...] = ()


@dataclass(frozen=True)
class ImportSection:
    title: str | None
    chapters: tuple[ImportChapter, ...] = ()


@dataclass(frozen=True)
class ImportDocument:
    title: str
    sections: tuple[ImportSection, ...]
    author: str = ''
    language: str = ''
    warnings: tuple[str, ...] = ()
    assets: tuple[ImportAsset, ...] = ()
    metadata: dict = field(default_factory=dict)


def serialize_import_block(block: ImportBlock, image_refs: dict[str, str] | None = None) -> str | None:
    """Serialize one neutral import block to canonical QuietWriter source."""
    if block.kind == 'image':
        reference = (image_refs or {}).get(block.asset_key, '')
        if not reference:
            return None
        return build_image_markdown(reference, alt=block.alt, caption=block.caption)
    inline = ''.join(serialize_inline_text(run.text, run.styles) for run in block.runs)
    return serialize_block_source(block.kind, inline, number=block.number)


def serialize_import_chapter(chapter: ImportChapter, image_refs: dict[str, str] | None = None) -> str:
    lines = [serialize_import_block(block, image_refs=image_refs) for block in chapter.blocks]
    return '\n'.join(line for line in lines if line is not None).rstrip('\n')


def serialize_import_document(document: ImportDocument, image_refs: dict[str, str] | None = None):
    """Return the legacy section/chapter shape consumed by current storage UI.

    Keeping this adapter at the boundary lets readers evolve independently from
    QuietWriter's on-disk syntax and from the existing book-creation workflow.
    """
    return tuple(
        (
            section.title,
            tuple(
                {'title': chapter.title, 'text': serialize_import_chapter(chapter, image_refs=image_refs)}
                for chapter in section.chapters
            ),
        )
        for section in document.sections
    )
