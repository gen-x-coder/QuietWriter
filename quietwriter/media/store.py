from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
import tempfile
import time
import uuid
from pathlib import Path

from ..storage import _safe_atomic_write_text
from .models import MediaAsset
from .markup import relative_asset_reference


class MediaError(RuntimeError):
    pass


class UnsupportedImageError(MediaError):
    pass


class MissingMediaError(MediaError):
    pass


class CorruptMediaError(MediaError):
    pass


_MEDIA_BY_EXT = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png'}


def _atomic_copy(source: Path, target: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=target.name + '.', suffix='.tmp', dir=str(target.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        shutil.copyfile(source, tmp)
        delay = 0.04
        last = None
        for _ in range(8):
            try:
                os.replace(tmp, target)
                return
            except PermissionError as exc:
                last = exc
                time.sleep(delay)
                delay = min(delay * 1.8, 0.45)
        raise last or PermissionError(f'Kan {target} niet schrijven.')
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass


def _png_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) >= 24 and data.startswith(b'\x89PNG\r\n\x1a\n') and data[12:16] == b'IHDR':
        return struct.unpack('>II', data[16:24])
    return 0, 0


def _jpeg_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 4 or not data.startswith(b'\xff\xd8'):
        return 0, 0
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        while i < len(data) and data[i] == 0xFF:
            i += 1
        if i >= len(data):
            break
        marker = data[i]
        i += 1
        if marker in {0xD8, 0xD9}:
            continue
        if i + 2 > len(data):
            break
        length = int.from_bytes(data[i:i+2], 'big')
        if length < 2 or i + length > len(data):
            break
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF} and length >= 7:
            height = int.from_bytes(data[i+3:i+5], 'big')
            width = int.from_bytes(data[i+5:i+7], 'big')
            return width, height
        i += length
    return 0, 0


def _image_info(path: Path, data: bytes) -> tuple[str, int, int]:
    ext = path.suffix.lower()
    media_type = _MEDIA_BY_EXT.get(ext)
    if not media_type:
        raise UnsupportedImageError('Ondersteunde afbeeldingsformaten zijn JPG, JPEG en PNG.')
    if media_type == 'image/png':
        width, height = _png_dimensions(data)
        if not width:
            raise UnsupportedImageError('Het gekozen PNG-bestand is niet geldig.')
    else:
        width, height = _jpeg_dimensions(data)
        if not width:
            raise UnsupportedImageError('Het gekozen JPEG-bestand is niet geldig.')
    return media_type, width, height


class MediaStore:
    """Book-local immutable media store.

    Binaries are UUID named and never overwritten. ``manifest.json`` is the
    small revision-guarded source of truth; heavy image files are integrity
    checked when an export snapshot actually needs them.
    """

    def __init__(self, library):
        self.library = library

    def root(self, book) -> Path:
        return Path(book.path) / 'assets'

    def images_dir(self, book) -> Path:
        return self.root(book) / 'images'

    def cover_dir(self, book) -> Path:
        return self.root(book) / 'cover'

    def manifest_path(self, book) -> Path:
        return self.root(book) / 'manifest.json'

    def ensure_structure(self, book, *, create_manifest: bool = True):
        self.images_dir(book).mkdir(parents=True, exist_ok=True)
        self.cover_dir(book).mkdir(parents=True, exist_ok=True)
        if create_manifest and not self.manifest_path(book).exists():
            _safe_atomic_write_text(self.manifest_path(book), json.dumps({'version': 1, 'images': {}}, ensure_ascii=False, indent=2))

    def load_manifest(self, book) -> dict:
        path = self.manifest_path(book)
        if not path.exists():
            return {'version': 1, 'images': {}}
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as exc:
            raise MediaError(f'Mediamanifest kan niet worden gelezen: {exc}') from exc
        if not isinstance(data, dict):
            raise MediaError('Mediamanifest heeft een ongeldig formaat.')
        images = data.get('images')
        if not isinstance(images, dict):
            images = {}
        return {'version': int(data.get('version') or 1), 'images': images}

    def _save_manifest_unchecked(self, book, data: dict):
        self.root(book).mkdir(parents=True, exist_ok=True)
        _safe_atomic_write_text(self.manifest_path(book), json.dumps(data, ensure_ascii=False, indent=2))

    def assets(self, book) -> tuple[MediaAsset, ...]:
        data = self.load_manifest(book)
        return tuple(MediaAsset.from_dict(asset_id, row) for asset_id, row in data['images'].items())

    def import_image_bytes(self, book, data_bytes: bytes, original_name: str, *, verify_revision: bool = True) -> MediaAsset:
        """Import immutable PNG/JPEG bytes into a book-local media store.

        ``verify_revision=False`` is reserved for unpublished staging books,
        where no live revision can conflict yet. Normal editor imports keep the
        existing optimistic-concurrency guard.
        """
        name = Path(str(original_name or 'image'))
        if verify_revision:
            self.library.verify_book_unchanged(book)
        media_type, width, height = _image_info(name, data_bytes)
        digest = hashlib.sha256(data_bytes).hexdigest()
        manifest = self.load_manifest(book)

        for asset_id, row in manifest['images'].items():
            existing = MediaAsset.from_dict(asset_id, row)
            candidate = Path(book.path) / existing.file
            if existing.sha256 == digest and candidate.is_file():
                return existing

        asset_id = str(uuid.uuid4())
        ext = '.jpg' if media_type == 'image/jpeg' else '.png'
        relative = f'assets/images/{asset_id}{ext}'
        target = Path(book.path) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=target.name + '.', suffix='.tmp', dir=str(target.parent))
        os.close(fd)
        tmp = Path(tmp_name)
        try:
            tmp.write_bytes(data_bytes)
            os.replace(tmp, target)
        finally:
            if tmp.exists():
                tmp.unlink(missing_ok=True)

        asset = MediaAsset(
            id=asset_id, file=relative, media_type=media_type,
            original_name=name.name, width=width, height=height,
            sha256=digest, size=len(data_bytes),
        )
        manifest['images'][asset_id] = asset.to_dict()
        self._save_manifest_unchecked(book, manifest)
        if verify_revision:
            self.library.refresh_book_revision(book)
        return asset

    def import_image(self, book, source: Path) -> MediaAsset:
        source = Path(source)
        if not source.is_file():
            raise MissingMediaError(f'Afbeelding bestaat niet: {source}')
        return self.import_image_bytes(book, source.read_bytes(), source.name, verify_revision=True)

    def reference_for_chapter(self, chapter, asset: MediaAsset) -> str:
        return relative_asset_reference(chapter.file, asset.file)

    def _record_by_file(self, book, relative_file: str) -> MediaAsset | None:
        normalized = Path(relative_file).as_posix()
        for asset in self.assets(book):
            if Path(asset.file).as_posix() == normalized:
                return asset
        return None

    def resolve_reference(self, book, source_file: str, reference: str) -> tuple[MediaAsset, Path]:
        base = (Path(book.path) / Path(source_file).parent).resolve()
        target = (base / Path(reference)).resolve()
        book_root = Path(book.path).resolve()
        try:
            relative = target.relative_to(book_root).as_posix()
        except ValueError as exc:
            raise MissingMediaError(f'Afbeeldingspad ligt buiten het boek: {reference}') from exc
        if not relative.startswith('assets/images/'):
            raise MissingMediaError(f'Afbeelding is geen beheerd boekasset: {reference}')
        asset = self._record_by_file(book, relative)
        if asset is None:
            raise MissingMediaError(f'Afbeelding ontbreekt in assets/manifest.json: {reference}')
        if not target.is_file():
            raise MissingMediaError(f'Afbeeldingsbestand ontbreekt: {reference}')
        return asset, target

    def read_verified_reference(self, book, source_file: str, reference: str) -> tuple[MediaAsset, bytes]:
        asset, path = self.resolve_reference(book, source_file, reference)
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != asset.sha256:
            raise CorruptMediaError(f'Afbeelding wijkt af van het mediamanifest: {reference}')
        return asset, data
