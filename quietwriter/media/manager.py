from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .markup import find_image_references
from .models import MediaAsset
from .store import MediaStore, MediaError


@dataclass(frozen=True)
class MediaUsage:
    source_file: str
    count: int


@dataclass(frozen=True)
class MediaInventoryItem:
    id: str
    file: str
    original_name: str
    media_type: str
    width: int
    height: int
    size: int
    status: str  # used, unused, missing, modified
    reference_count: int
    usages: tuple[MediaUsage, ...]
    history_reference_count: int = 0
    history_versions: tuple[str, ...] = ()
    history_safe: bool = True

    @property
    def unused(self) -> bool:
        return self.reference_count == 0

    @property
    def can_cleanup(self) -> bool:
        return self.unused and self.history_safe


@dataclass(frozen=True)
class UntrackedMediaFile:
    file: str
    size: int
    reference_count: int
    usages: tuple[MediaUsage, ...]


@dataclass(frozen=True)
class MediaInventory:
    items: tuple[MediaInventoryItem, ...]
    untracked_files: tuple[UntrackedMediaFile, ...]
    source_errors: tuple[str, ...]
    cover_file: str = ''
    cover_size: int = 0

    @property
    def used_count(self) -> int:
        return sum(1 for item in self.items if item.reference_count > 0)

    @property
    def unused_count(self) -> int:
        return sum(1 for item in self.items if item.unused)

    @property
    def problem_count(self) -> int:
        return sum(1 for item in self.items if item.status in {'missing', 'modified'}) + len(self.untracked_files)

    @property
    def can_cleanup(self) -> bool:
        return not self.source_errors and any(item.can_cleanup for item in self.items)


@dataclass(frozen=True)
class MediaCleanupResult:
    removed_ids: tuple[str, ...]
    removed_files: tuple[str, ...]
    leftover_files: tuple[str, ...]
    checkpoint_version_id: str = ''


class MediaCleanupError(MediaError):
    pass


def _markdown_sources(root: Path) -> tuple[Path, ...]:
    """All book-owned Markdown sources that could reference a book asset.

    Scanning all Markdown, not only manuscript chapters, makes cleanup safe for
    manually entered image syntax in publication/profile/planning files too.
    """
    if not root.exists():
        return ()
    return tuple(sorted(
        path for path in root.rglob('*.md')
        if path.is_file() and 'assets' not in path.relative_to(root).parts
    ))


def _usage_map(root: Path) -> tuple[dict[str, dict[str, int]], tuple[str, ...]]:
    root = Path(root)
    resolved_root = root.resolve()
    result: dict[str, dict[str, int]] = {}
    errors: list[str] = []
    for source in _markdown_sources(root):
        try:
            text = source.read_text(encoding='utf-8')
        except (OSError, UnicodeError) as exc:
            try:
                relative_source = source.relative_to(root).as_posix()
            except ValueError:
                relative_source = source.name
            errors.append(f'{relative_source}: {exc}')
            continue
        relative_source = source.relative_to(root).as_posix()
        base = source.parent.resolve()
        for ref in find_image_references(text):
            try:
                target = (base / Path(ref.path)).resolve()
                relative = target.relative_to(resolved_root).as_posix()
            except (OSError, ValueError):
                continue
            if not relative.startswith('assets/images/'):
                continue
            per_source = result.setdefault(relative, {})
            per_source[relative_source] = per_source.get(relative_source, 0) + 1
    return result, tuple(errors)




def _merge_usage_maps(*maps: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
    merged: dict[str, dict[str, int]] = {}
    for usage_map in maps:
        for relative, per_source in usage_map.items():
            target = merged.setdefault(relative, {})
            for source, count in per_source.items():
                target[source] = target.get(source, 0) + int(count)
    return merged

def _usage_rows(per_source: dict[str, int] | None) -> tuple[MediaUsage, ...]:
    return tuple(
        MediaUsage(source_file=source, count=count)
        for source, count in sorted((per_source or {}).items())
    )


class MediaManager:
    """Inspect and safely clean book-local inline image assets.

    Cleanup is intentionally more conservative than export. It refuses to infer
    "unused" when a Markdown source could not be read, verifies the live book
    revision before mutation, and checks that every historical snapshot that
    references a live asset owns its own binary copy before the live copy may be
    deleted.
    """

    def __init__(self, library):
        self.library = library
        self.store = MediaStore(library)

    def _trash_usage(self, book) -> tuple[dict[str, dict[str, int]], tuple[str, ...]]:
        """References held by recoverable chapters in the chapter trash.

        A trashed chapter is still user-restorable content. Its Markdown paths
        are interpreted relative to the chapter's original live location, not
        relative to ``trash/``, so an image used only by that chapter remains
        protected until the trash entry itself is permanently deleted.
        """
        resolved_root = Path(book.path).resolve()
        result: dict[str, dict[str, int]] = {}
        errors: list[str] = []
        for entry in self.library.list_trashed_chapters():
            if str(entry.get('book_id') or '') != str(book.id):
                continue
            source = Path(entry['path'])
            label = f"Prullenbak: {entry.get('title') or source.stem}"
            try:
                text = source.read_text(encoding='utf-8')
            except (OSError, UnicodeError) as exc:
                errors.append(f'{label}: {exc}')
                continue
            chapter_file = str(entry.get('chapter_file') or f'chapters/{source.name}')
            base = (Path(book.path) / chapter_file).parent.resolve()
            for ref in find_image_references(text):
                try:
                    target = (base / Path(ref.path)).resolve()
                    relative = target.relative_to(resolved_root).as_posix()
                except (OSError, ValueError):
                    continue
                if not relative.startswith('assets/images/'):
                    continue
                per_source = result.setdefault(relative, {})
                per_source[label] = per_source.get(label, 0) + 1
        return result, tuple(errors)

    def _history_usage(self, book, relative_files: set[str]) -> dict[str, tuple[int, tuple[str, ...], bool]]:
        state = {name: {'count': 0, 'versions': [], 'safe': True} for name in relative_files}
        history_root = Path(self.library.archive_dir) / book.id
        if not history_root.is_dir() or not relative_files:
            return {name: (0, (), True) for name in relative_files}

        for snapshot in sorted(path for path in history_root.iterdir() if path.is_dir() and (path / 'book.json').is_file()):
            usages, errors = _usage_map(snapshot)
            snapshot_manifest_files: set[str] = set()
            manifest_path = snapshot / 'assets' / 'manifest.json'
            if manifest_path.is_file():
                try:
                    import json
                    raw = json.loads(manifest_path.read_text(encoding='utf-8'))
                    for row in (raw.get('images') or {}).values():
                        if isinstance(row, dict) and row.get('file'):
                            snapshot_manifest_files.add(Path(str(row['file'])).as_posix())
                except (OSError, UnicodeError, ValueError, TypeError):
                    # A malformed historical manifest should never make live
                    # cleanup *less* conservative. If sources are unreadable too,
                    # treat missing binaries as unsafe below.
                    snapshot_manifest_files = set(relative_files)
            for relative in relative_files:
                count = sum(usages.get(relative, {}).values())
                row = state[relative]
                if count:
                    row['count'] += count
                    row['versions'].append(snapshot.name)
                    if not (snapshot / relative).is_file():
                        row['safe'] = False
                elif errors and relative in snapshot_manifest_files and not (snapshot / relative).is_file():
                    # We could not inspect all historical Markdown. A manifest
                    # entry without its own binary may depend on the live UUID
                    # surviving restore, so cleanup must not remove that fallback.
                    row['safe'] = False
        return {
            name: (int(row['count']), tuple(row['versions']), bool(row['safe']))
            for name, row in state.items()
        }

    def inspect(self, book, *, include_history: bool = True) -> MediaInventory:
        manifest = self.store.load_manifest(book)
        assets = tuple(MediaAsset.from_dict(asset_id, row) for asset_id, row in manifest['images'].items())
        live_usages, live_errors = _usage_map(Path(book.path))
        trash_usages, trash_errors = self._trash_usage(book)
        usages = _merge_usage_maps(live_usages, trash_usages)
        source_errors = tuple(live_errors) + tuple(trash_errors)
        relative_files = {Path(asset.file).as_posix() for asset in assets if asset.file}
        history = self._history_usage(book, relative_files) if include_history else {
            name: (0, (), True) for name in relative_files
        }

        items: list[MediaInventoryItem] = []
        for asset in assets:
            relative = Path(asset.file).as_posix()
            path = Path(book.path) / relative
            per_source = usages.get(relative, {})
            reference_count = sum(per_source.values())
            if not path.is_file():
                status = 'missing'
            else:
                try:
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                except OSError:
                    digest = ''
                if digest != asset.sha256:
                    status = 'modified'
                elif reference_count:
                    status = 'used'
                else:
                    status = 'unused'
            history_count, history_versions, history_safe = history.get(relative, (0, (), True))
            items.append(MediaInventoryItem(
                id=asset.id,
                file=relative,
                original_name=asset.original_name,
                media_type=asset.media_type,
                width=asset.width,
                height=asset.height,
                size=asset.size,
                status=status,
                reference_count=reference_count,
                usages=_usage_rows(per_source),
                history_reference_count=history_count,
                history_versions=history_versions,
                history_safe=history_safe,
            ))

        managed_files = {Path(item.file).as_posix() for item in items}
        untracked: list[UntrackedMediaFile] = []
        images_dir = self.store.images_dir(book)
        if images_dir.is_dir():
            for path in sorted(p for p in images_dir.rglob('*') if p.is_file()):
                relative = path.relative_to(book.path).as_posix()
                if relative in managed_files:
                    continue
                per_source = usages.get(relative, {})
                try:
                    size = path.stat().st_size
                except OSError:
                    size = 0
                untracked.append(UntrackedMediaFile(
                    file=relative,
                    size=size,
                    reference_count=sum(per_source.values()),
                    usages=_usage_rows(per_source),
                ))

        cover = self.library.cover_path(book)
        cover_file = ''
        cover_size = 0
        if cover and Path(cover).is_file():
            try:
                cover_file = Path(cover).relative_to(book.path).as_posix()
            except ValueError:
                cover_file = str(cover)
            try:
                cover_size = Path(cover).stat().st_size
            except OSError:
                cover_size = 0

        return MediaInventory(
            items=tuple(sorted(items, key=lambda item: (item.status != 'used', item.original_name.casefold(), item.file))),
            untracked_files=tuple(untracked),
            source_errors=source_errors,
            cover_file=cover_file,
            cover_size=cover_size,
        )

    def cleanup_unused(self, book, asset_ids=None) -> MediaCleanupResult:
        """Remove unreferenced manifest assets after one recoverable checkpoint.

        Untracked/orphan files are deliberately not deleted automatically in this
        first manager version. They remain visible diagnostics until a later,
        separately reviewable cleanup rule is introduced.
        """
        self.library.verify_book_unchanged(book)
        inventory = self.inspect(book, include_history=True)
        if inventory.source_errors:
            raise MediaCleanupError(
                'Media opruimen is geblokkeerd omdat niet alle Markdownbronnen konden worden gelezen.'
            )
        wanted = None if asset_ids is None else {str(asset_id) for asset_id in asset_ids}
        candidates = [
            item for item in inventory.items
            if item.unused and (wanted is None or item.id in wanted)
        ]
        unsafe = [item for item in candidates if not item.history_safe]
        if unsafe:
            labels = ', '.join(item.original_name or Path(item.file).name for item in unsafe[:3])
            raise MediaCleanupError(
                'Media opruimen is geblokkeerd: een historische versie verwijst naar een afbeelding '
                f'zonder eigen herstelkopie ({labels}).'
            )
        candidates = [item for item in candidates if item.history_safe]
        if not candidates:
            return MediaCleanupResult((), (), (), '')

        # A complete pre-cleanup snapshot makes the cleanup itself reversible in
        # History. This is intentionally one checkpoint for the whole batch.
        checkpoint = self.library.create_version(book, kind='media_cleanup')
        # Copying a complete checkpoint can take noticeably longer on books with
        # many images. Re-check immediately before the manifest commit so a sync
        # that landed during the copy cannot be overwritten by cleanup.
        self.library.verify_book_unchanged(book)

        manifest = self.store.load_manifest(book)
        removed_ids: list[str] = []
        removed_files: list[str] = []
        for item in candidates:
            if item.id in manifest['images']:
                manifest['images'].pop(item.id, None)
                removed_ids.append(item.id)
                removed_files.append(item.file)

        if not removed_ids:
            return MediaCleanupResult((), (), (), checkpoint.get('id', ''))

        # Commit metadata first. Failure here leaves every binary untouched.
        self.store._save_manifest_unchecked(book, manifest)
        leftovers: list[str] = []
        for relative in removed_files:
            path = Path(book.path) / relative
            if not path.exists():
                continue
            try:
                path.unlink()
            except OSError:
                # An untracked leftover is harmless and remains visible in the
                # manager so the user never gets a false "fully cleaned" state.
                leftovers.append(relative)
        self.library.refresh_book_revision(book)
        return MediaCleanupResult(
            tuple(removed_ids), tuple(removed_files), tuple(leftovers), str(checkpoint.get('id') or '')
        )
