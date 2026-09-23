from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExportAsset:
    """Immutable binary asset captured with an export snapshot.

    Covers and inline manuscript images use the same neutral snapshot model so
    renderers never need to read live book media after the snapshot is built.
    """

    id: str
    filename: str
    media_type: str
    data: bytes
    role: str = 'inline'


@dataclass(frozen=True)
class ExportChapter:
    id: str
    title: str
    markdown: str


@dataclass(frozen=True)
class ExportSection:
    id: str
    title: str
    chapters: tuple[ExportChapter, ...] = ()


@dataclass(frozen=True)
class ExportItem:
    key: str
    kind: str
    data: dict = field(default_factory=dict)
    text: str = ''


@dataclass(frozen=True)
class ExportDocument:
    """Complete read-only publication snapshot consumed by exporters."""

    id: str
    title: str
    author: str
    language: str
    slug: str
    metadata: dict
    sections: tuple[ExportSection, ...]
    front_matter: tuple[ExportItem, ...]
    back_matter: tuple[ExportItem, ...]
    assets: tuple[ExportAsset, ...] = ()
    cover_asset_id: str | None = None
    epub_isbn: str = ''
    missing_assets: tuple[str, ...] = ()

    @property
    def chapter_count(self) -> int:
        return sum(len(section.chapters) for section in self.sections)

    @property
    def inline_asset_count(self) -> int:
        return sum(1 for asset in self.assets if asset.role == 'inline')

    @property
    def cover_asset(self) -> ExportAsset | None:
        if not self.cover_asset_id:
            return None
        return next((asset for asset in self.assets if asset.id == self.cover_asset_id), None)
