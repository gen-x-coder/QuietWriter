from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from .storage import Book, Library, slugify

PACKAGE_FORMAT = 'quietwriter-book'
PACKAGE_VERSION = 2
MANIFEST_NAME = 'qwbook.json'
BOOK_PREFIX = 'book/'
HISTORY_PREFIX = 'history/'
MAX_MANIFEST_SIZE = 10 * 1024 * 1024
MAX_FILE_SIZE = 512 * 1024 * 1024
MAX_TOTAL_SIZE = 2 * 1024 * 1024 * 1024
MAX_FILE_COUNT = 20_000
MAX_COMPRESSION_RATIO = 1000
_WINDOWS_RESERVED = {
    'CON', 'PRN', 'AUX', 'NUL',
    *(f'COM{i}' for i in range(1, 10)),
    *(f'LPT{i}' for i in range(1, 10)),
}


class QwBookError(RuntimeError):
    pass


class QwBookFutureFormatError(QwBookError):
    pass


class QwBookConflictError(QwBookError):
    pass


def _safe_member_name(name: str) -> PurePosixPath:
    """Validate a portable archive-relative path for POSIX *and* Windows.

    .qwbook files are shareable.  Validation therefore follows the stricter
    Windows rules even when QuietWriter happens to run on Linux/macOS.
    """
    if not isinstance(name, str) or not name:
        raise QwBookError('Leeg pad in .qwbook geweigerd.')
    if '\x00' in name or '\\' in name or ':' in name:
        raise QwBookError(f'Ongeldig pad in .qwbook: {name}')
    if any(ord(ch) < 32 for ch in name):
        raise QwBookError(f'Ongeldig pad in .qwbook: {name}')
    if name.startswith('/') or '//' in name:
        raise QwBookError(f'Ongeldig pad in .qwbook: {name}')
    parts = name.split('/')
    if not parts or any(part in ('', '.', '..') for part in parts):
        raise QwBookError(f'Ongeldig pad in .qwbook: {name}')
    for part in parts:
        if part.endswith((' ', '.')):
            raise QwBookError(f'Ongeldig Windows-pad in .qwbook: {name}')
        stem = part.split('.', 1)[0].upper()
        if stem in _WINDOWS_RESERVED:
            raise QwBookError(f'Gereserveerde Windows-bestandsnaam in .qwbook: {name}')
    path = PurePosixPath(*parts)
    if path.is_absolute():
        raise QwBookError(f'Ongeldig pad in .qwbook: {name}')
    return path


def _safe_target(root: Path, relative: PurePosixPath) -> Path:
    root_resolved = Path(root).resolve()
    target = root_resolved.joinpath(*relative.parts)
    resolved = target.resolve(strict=False)
    try:
        inside = resolved.is_relative_to(root_resolved)
    except AttributeError:  # pragma: no cover - Python < 3.9 compatibility guard
        inside = root_resolved == resolved or root_resolved in resolved.parents
    if not inside:
        raise QwBookError(f'Pad buiten de tijdelijke importmap geweigerd: {relative.as_posix()}')
    return target


def _sanitize_book_json(data: bytes) -> bytes:
    """Remove machine-local provenance from a portable/shared package."""
    try:
        value = json.loads(data.decode('utf-8-sig'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return data
    if not isinstance(value, dict):
        return data
    metadata = value.get('metadata')
    if isinstance(metadata, dict):
        metadata = dict(metadata)
        metadata.pop('source_file', None)
        value = dict(value)
        value['metadata'] = metadata
    return json.dumps(value, ensure_ascii=False, indent=2).encode('utf-8')


def _read_stable_bytes(path: Path, relative: str = '') -> bytes:
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
        raise QwBookError(f'Bestand veranderde tijdens export: {path.name}')
    if PurePosixPath(relative).name == 'book.json':
        data = _sanitize_book_json(data)
    return data


def _iter_tree_files(root: Path):
    root = Path(root)
    if not root.exists():
        return
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise QwBookError(f'Symbolische koppeling wordt niet opgenomen: {path.name}')
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            _safe_member_name(relative)
            yield relative, path


def _collect_payloads(root: Path) -> tuple[dict[str, dict[str, object]], list[tuple[str, bytes]]]:
    files: dict[str, dict[str, object]] = {}
    payloads: list[tuple[str, bytes]] = []
    for relative, path in _iter_tree_files(root) or ():
        data = _read_stable_bytes(path, relative)
        if len(data) > MAX_FILE_SIZE:
            raise QwBookError(f'Bestand is te groot voor .qwbook: {relative}')
        files[relative] = {'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data)}
        payloads.append((relative, data))
    return files, payloads


def export_qwbook(library: Library, book: Book, destination: Path, *, include_history: bool = True) -> Path:
    """Create one portable, self-verifying QuietWriter book backup."""
    destination = Path(destination)
    library.verify_book_unchanged(book)
    files, book_payloads = _collect_payloads(Path(book.path))
    history_root = library.archive_dir / book.id
    if include_history:
        history_files, history_payloads = _collect_payloads(history_root)
    else:
        history_files, history_payloads = {}, []

    if 'book.json' not in files:
        raise QwBookError('Dit boek heeft geen book.json en kan niet worden verpakt.')
    total_size = sum(int(row['size']) for row in files.values()) + sum(int(row['size']) for row in history_files.values())
    if len(files) + len(history_files) > MAX_FILE_COUNT:
        raise QwBookError('Dit boek bevat te veel bestanden voor één .qwbook-pakket.')
    if total_size > MAX_TOTAL_SIZE:
        raise QwBookError('Dit boek is te groot voor één .qwbook-pakket.')

    package = {
        'format': PACKAGE_FORMAT,
        'version': PACKAGE_VERSION,
        'book_id': book.id,
        'title': book.title,
        'files': files,
        'history_files': history_files,
        'privacy': {'source_file_removed': True},
        'history_included': bool(include_history),
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=destination.name + '.', suffix='.tmp', dir=str(destination.parent))
    os.close(fd)
    temp = Path(temp_name)
    try:
        with zipfile.ZipFile(temp, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            archive.writestr(MANIFEST_NAME, json.dumps(package, ensure_ascii=False, indent=2))
            for relative, data in book_payloads:
                archive.writestr(BOOK_PREFIX + relative, data)
            for relative, data in history_payloads:
                archive.writestr(HISTORY_PREFIX + relative, data)
        os.replace(temp, destination)
    finally:
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass
    return destination


def _load_package(archive: zipfile.ZipFile) -> dict:
    names = archive.namelist()
    if MANIFEST_NAME not in names:
        raise QwBookError('Dit bestand bevat geen QuietWriter-pakketmanifest.')
    info = archive.getinfo(MANIFEST_NAME)
    if info.file_size > MAX_MANIFEST_SIZE:
        raise QwBookError('Het QuietWriter-pakketmanifest is onredelijk groot.')
    try:
        package = json.loads(archive.read(info).decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError) as exc:
        raise QwBookError('Het QuietWriter-pakketmanifest is beschadigd.') from exc
    if not isinstance(package, dict) or package.get('format') != PACKAGE_FORMAT:
        raise QwBookError('Dit is geen geldig QuietWriter-boekbestand.')
    version = int(package.get('version') or 0)
    if version > PACKAGE_VERSION:
        raise QwBookFutureFormatError('Dit .qwbook-bestand is gemaakt met een nieuwere QuietWriter-versie.')
    if version < 1:
        raise QwBookError('Onbekende .qwbook-versie.')
    files = package.get('files')
    if not isinstance(files, dict) or 'book.json' not in files:
        raise QwBookError('Het .qwbook-bestand bevat geen volledige boekenlijst.')
    history_files = package.get('history_files', {})
    if not isinstance(history_files, dict):
        raise QwBookError('Ongeldige versiegeschiedenislijst in .qwbook.')
    package['history_files'] = history_files
    return package


def inspect_qwbook(source: Path) -> dict:
    source = Path(source)
    try:
        with zipfile.ZipFile(source, 'r') as archive:
            return _load_package(archive)
    except zipfile.BadZipFile as exc:
        raise QwBookError('Dit .qwbook-bestand is beschadigd of geen ZIP-container.') from exc


def _check_entry_before_extract(info: zipfile.ZipInfo, metadata: object, relative: str, running_total: int) -> int:
    if not isinstance(metadata, dict):
        raise QwBookError(f'Ongeldige bestandsmetadata: {relative}')
    expected_size = int(metadata.get('size', -1))
    if expected_size < 0 or info.file_size != expected_size:
        raise QwBookError(f'Bestandsgrootte wijkt af van het manifest: {relative}')
    if info.file_size > MAX_FILE_SIZE:
        raise QwBookError(f'Bestand is te groot voor import: {relative}')
    new_total = running_total + info.file_size
    if new_total > MAX_TOTAL_SIZE:
        raise QwBookError('Het uitgepakte .qwbook-bestand is te groot.')
    if info.file_size > 10 * 1024 * 1024 and info.compress_size > 0:
        if info.file_size / max(1, info.compress_size) > MAX_COMPRESSION_RATIO:
            raise QwBookError(f'Onveilige compressieverhouding in .qwbook: {relative}')
    if ((info.external_attr >> 16) & 0o170000) == 0o120000:
        raise QwBookError(f'Symbolische koppeling in .qwbook geweigerd: {relative}')
    return new_total


def _extract_verified_entry(archive: zipfile.ZipFile, info: zipfile.ZipInfo, metadata: dict, target: Path, relative: str):
    expected_hash = str(metadata.get('sha256') or '')
    digest = hashlib.sha256()
    written = 0
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with archive.open(info, 'r') as src, target.open('xb') as dst:
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > info.file_size:
                    raise QwBookError(f'Bestand groeide tijdens uitpakken: {relative}')
                digest.update(chunk)
                dst.write(chunk)
        if written != info.file_size or digest.hexdigest() != expected_hash:
            raise QwBookError(f'Bestandscontrole mislukt voor {relative}.')
    except Exception:
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _book_id_in_trash(library: Library, book_id: str):
    for row in library.list_trashed_books():
        if str(row.get('book_id') or '') == book_id:
            return row
    return None


def _cleanup_stale_import_dirs(import_parent: Path):
    if not import_parent.exists():
        return
    for path in import_parent.glob('qwbook-import-*'):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)


def _sanitize_imported_book_json(path: Path) -> None:
    if not path.exists():
        return
    original = path.read_bytes()
    cleaned = _sanitize_book_json(original)
    if cleaned != original:
        path.write_bytes(cleaned)


def _move_orphan_history(library: Library, history_path: Path) -> Path | None:
    """Move history aside when no live/trashed book owns this identity."""
    if not history_path.exists():
        return None
    if not any(history_path.iterdir()):
        shutil.rmtree(history_path, ignore_errors=True)
        return None
    orphan_root = library.archive_dir / '.orphaned'
    orphan_root.mkdir(parents=True, exist_ok=True)
    base = history_path.name + '-orphan'
    target = orphan_root / base
    counter = 2
    while target.exists():
        target = orphan_root / f'{base}-{counter}'
        counter += 1
    os.replace(history_path, target)
    return target


def import_qwbook(library: Library, source: Path) -> Book:
    """Import a complete package without overwriting live, trashed, or historic identity."""
    source = Path(source)
    temp_root: Path | None = None
    final_path: Path | None = None
    final_history: Path | None = None
    history_moved = False
    orphan_history_path: Path | None = None
    try:
        with zipfile.ZipFile(source, 'r') as archive:
            package = _load_package(archive)
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise QwBookError('Het .qwbook-bestand bevat dubbele bestandsnamen.')
            folded = [name.casefold() for name in names]
            if len(folded) != len(set(folded)):
                raise QwBookError('Het .qwbook-bestand bevat bestandsnamen die op Windows met elkaar botsen.')
            if len(names) > MAX_FILE_COUNT + 1:
                raise QwBookError('Het .qwbook-bestand bevat onredelijk veel bestanden.')

            book_id = str(package.get('book_id') or '').strip()
            title = str(package.get('title') or source.stem).strip() or source.stem
            if not book_id:
                raise QwBookError('Het .qwbook-bestand bevat geen boek-id.')
            for existing in library.list_books():
                if existing.id == book_id:
                    raise QwBookConflictError(f'Boek “{existing.title}” met dezelfde identiteit bestaat al in deze werkmap.')
            trashed = _book_id_in_trash(library, book_id)
            if trashed:
                raise QwBookConflictError(
                    f'Boek “{trashed.get("title") or title}” met dezelfde identiteit staat in de prullenbak. '
                    'Herstel dat boek of verwijder het eerst definitief.'
                )

            folder_name = f'{slugify(title)}-{book_id[:8]}'
            final_path = library.books_dir / folder_name
            if final_path.exists():
                raise QwBookConflictError(f'Doelmap bestaat al: {final_path.name}')
            final_history = library.archive_dir / book_id
            history_files = package.get('history_files') or {}

            import_parent = library.cache_dir / 'qwbook-import'
            import_parent.mkdir(parents=True, exist_ok=True)
            _cleanup_stale_import_dirs(import_parent)
            temp_root = Path(tempfile.mkdtemp(prefix='qwbook-import-', dir=str(import_parent)))
            temp_book = temp_root / 'book'
            temp_history = temp_root / 'history'
            temp_book.mkdir()

            files = package['files']
            expected_entries = {BOOK_PREFIX + _safe_member_name(str(name)).as_posix() for name in files}
            expected_history = {HISTORY_PREFIX + _safe_member_name(str(name)).as_posix() for name in history_files}
            actual_book_entries = {name for name in names if name.startswith(BOOK_PREFIX) and not name.endswith('/')}
            actual_history_entries = {name for name in names if name.startswith(HISTORY_PREFIX) and not name.endswith('/')}
            if actual_book_entries != expected_entries or actual_history_entries != expected_history:
                raise QwBookError('De inhoud van het .qwbook-bestand wijkt af van het pakketmanifest.')
            allowed_entries = {MANIFEST_NAME} | expected_entries | expected_history
            extra_entries = {name for name in names if not name.endswith('/')} - allowed_entries
            if extra_entries:
                raise QwBookError('Het .qwbook-bestand bevat onverwachte bestanden.')

            total_size = 0
            for prefix, rows, root in ((BOOK_PREFIX, files, temp_book), (HISTORY_PREFIX, history_files, temp_history)):
                for relative, metadata in rows.items():
                    rel = _safe_member_name(str(relative))
                    entry = prefix + rel.as_posix()
                    info = archive.getinfo(entry)
                    total_size = _check_entry_before_extract(info, metadata, str(relative), total_size)
                    target = _safe_target(root, rel)
                    _extract_verified_entry(archive, info, metadata, target, str(relative))

        # Older v1 packages may still contain machine-local source_file paths.
        # Clean those during import as well, so legacy packages do not reintroduce
        # personal local paths into the workspace.
        _sanitize_imported_book_json(temp_book / 'book.json')
        if temp_history.exists():
            for history_book_json in temp_history.rglob('book.json'):
                _sanitize_imported_book_json(history_book_json)

        candidate = library.load_book(temp_book)
        if candidate.id != book_id:
            raise QwBookError('Boek-id in book.json komt niet overeen met het pakketmanifest.')
        if candidate.title != title:
            raise QwBookError('Boektitel in book.json komt niet overeen met het pakketmanifest.')
        for section in candidate.sections:
            for chapter in section.chapters:
                rel = _safe_member_name(chapter.file)
                if not _safe_target(temp_book, rel).is_file():
                    raise QwBookError(f'Hoofdstukbestand ontbreekt: {chapter.file}')

        if history_files:
            # Only replace orphaned history after the entire package has been
            # extracted and validated.  A failed import must not change the
            # visible history state.  Packages without history deliberately
            # keep an existing archive for this book id.
            if final_history.exists():
                orphan_history_path = _move_orphan_history(library, final_history)
            final_history.parent.mkdir(parents=True, exist_ok=True)
            os.replace(temp_history, final_history)
            history_moved = True
        os.replace(temp_book, final_path)
        imported = library.load_book(final_path)
        library.track_book(imported)
        shutil.rmtree(temp_root, ignore_errors=True)
        temp_root = None
        return imported
    except zipfile.BadZipFile as exc:
        raise QwBookError('Dit .qwbook-bestand is beschadigd of geen geldig archief.') from exc
    except Exception:
        if history_moved and final_history is not None and final_history.exists() and (final_path is None or not final_path.exists()):
            shutil.rmtree(final_history, ignore_errors=True)
        if (orphan_history_path is not None and orphan_history_path.exists()
                and final_history is not None and not final_history.exists()):
            final_history.parent.mkdir(parents=True, exist_ok=True)
            os.replace(orphan_history_path, final_history)
        raise
    finally:
        if temp_root is not None:
            shutil.rmtree(temp_root, ignore_errors=True)
