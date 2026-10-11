"""Safe, streaming .qwbook backups. Verifies archives before they become visible."""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

from .revisions import ExternalModificationError
from .storage import BookBlockedError

from .qwbook_io import (
    BOOK_PREFIX, HISTORY_PREFIX, MANIFEST_NAME, PACKAGE_FORMAT, PACKAGE_VERSION,
    MAX_FILE_COUNT, MAX_FILE_SIZE, MAX_TOTAL_SIZE, QwBookError, _check_entry_before_extract,
    _iter_tree_files, _load_package, _safe_member_name, _sanitize_book_json,
)


class BackupError(ValueError):
    """A backup cannot be safely created or verified."""


def validate_backup_root(workspace: Path, requested: Path) -> Path:
    try:
        work = Path(workspace).expanduser().resolve(strict=True)
        target = Path(requested).expanduser()
        if not target.is_absolute():
            raise BackupError('Kies een volledige locatie voor je back-ups.')
        if any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction())
               for p in (target, *target.parents)):
            raise BackupError('Een back-upmap via een koppeling wordt niet ondersteund.')
        target = target.resolve(strict=False)
        if target == work or target in work.parents or work in target.parents:
            raise BackupError('Kies een back-upmap buiten de werkmap.')
        return target
    except OSError as exc:
        raise BackupError('De back-uplocatie is niet bereikbaar.') from exc


def validate_archive(path: Path, expected_book_id: str) -> dict:
    """Check package members and their digest using bounded memory."""
    try:
        with zipfile.ZipFile(path, 'r') as archive:
            package = _load_package(archive)
            if package.get('book_id') != expected_book_id:
                raise BackupError('De back-up hoort bij een ander boek.')
            files = {}
            for prefix, entries in ((BOOK_PREFIX, package['files']),
                                    (HISTORY_PREFIX, package['history_files'])):
                for relative, record in entries.items():
                    _safe_member_name(relative)
                    files[prefix + relative] = record
            members = archive.namelist()
            if len(members) != len(set(members)) or set(members) != set(files) | {MANIFEST_NAME}:
                raise BackupError('De back-up bevat ontbrekende of onverwachte bestanden.')
            total = 0
            for name, record in files.items():
                entry = archive.getinfo(name)
                total = _check_entry_before_extract(entry, record, name, total)
                digest = hashlib.sha256()
                with archive.open(entry) as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                        digest.update(chunk)
                if digest.hexdigest() != record['sha256']:
                    raise BackupError('De back-up is niet volledig leesbaar.')
            return package
    except BackupError:
        raise
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile, KeyError, TypeError,
            ValueError, QwBookError, OverflowError) as exc:
        raise BackupError('De back-up kon niet veilig worden gecontroleerd.') from exc


def _stat(path):
    value = path.stat()
    return (value.st_size, value.st_mtime_ns)


def _stream_member(archive, member, path, *, sanitize=False):
    before = _stat(path)
    if before[0] > MAX_FILE_SIZE:
        raise BackupError('Een bestand is te groot voor een back-up: ' + path.name)
    digest = hashlib.sha256()
    count = 0
    if sanitize:
        # book.json is intentionally small; sanitize only this metadata, not media.
        if before[0] > 10 * 1024 * 1024:
            raise BackupError('De boekinformatie is onredelijk groot.')
        data = _sanitize_book_json(path.read_bytes())
        if _stat(path) != before:
            raise BackupError('Het boek veranderde tijdens de back-up.')
        with archive.open(member, 'w') as dest:
            dest.write(data)
        digest.update(data)
        count = len(data)
    else:
        # Already-compressed media need not consume CPU for a second DEFLATE.
        compressed_media = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif',
                            '.mp3', '.ogg', '.mp4', '.m4a', '.flac', '.zip', '.pdf'}
        if path.suffix.lower() in compressed_media:
            member_info = zipfile.ZipInfo(member)
            member_info.compress_type = zipfile.ZIP_STORED
        else:
            member_info = member
        with path.open('rb') as source, archive.open(member_info, 'w') as dest:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                dest.write(chunk)
                digest.update(chunk)
                count += len(chunk)
    if before != _stat(path) or (not sanitize and count != before[0]):
        raise BackupError('Een bestand veranderde tijdens de back-up: ' + path.name)
    return {'size': count, 'sha256': digest.hexdigest()}


def _legacy_folders(library, book, registered):
    """Include stable legacy snapshots without trusting an in-progress copytree."""
    root = library.archive_dir / book.id
    result = {}
    if not root.exists():
        return result
    now = time.time()
    for folder in root.iterdir():
        if not folder.is_dir() or folder.name.startswith('.') or folder.name in registered.values():
            continue
        # Files from an incomplete current copy are unsafe, even with book.json.
        if folder.is_symlink() or not (folder / 'book.json').is_file():
            continue
        _safe_member_name(folder.name)
        files = list(_iter_tree_files(folder))
        if not files or any(now - path.stat().st_mtime < 600 for _, path in files):
            continue  # An uncommitted copy is not safe to include.
        try:
            snapshot = library.load_book(folder)
            chapter_paths = [folder / chapter.file for section in snapshot.sections for chapter in section.chapters]
            if not all(path.is_file() and not path.is_symlink() for path in chapter_paths):
                continue  # Incomplete legacy copy; never include it in a verified backup.
        except BackupError:
            raise
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise BackupError('Een oudere boekversie kan niet worden gelezen.') from exc
        result[folder.name] = tuple(sorted((rel, *_stat(path)) for rel, path in files))
    return result


def _history_state(library, book):
    index = library._load_history_index(book)
    versions = index.get('versions', {})
    if not isinstance(versions, dict):
        raise BackupError('De versiegeschiedenis is niet leesbaar.')
    registered = {key: str(row.get('folder') or key) for key, row in versions.items()
                  if isinstance(row, dict)}
    legacy = _legacy_folders(library, book, registered)
    return (json.dumps(index, sort_keys=True, ensure_ascii=False), legacy), {
        **registered, **{name: name for name in legacy}
    }


def _export_streaming(library, book, path, registered):
    # An unopened book has no baseline; the before/after snapshots still
    # detect mutation while exporting. Never re-track an open book here.
    if library.tracked_revision(book) is not None or library.is_book_blocked(book):
        library.verify_book_unchanged(book)
    book_root = Path(book.path)
    history_root = library.archive_dir / book.id
    files, history_files = {}, {}
    count = total = 0
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6,
                         allowZip64=True) as archive:
        for rel, src in _iter_tree_files(book_root):
            count += 1
            if count > MAX_FILE_COUNT:
                raise BackupError('Dit boek bevat te veel bestanden voor een back-up.')
            record = _stream_member(archive, BOOK_PREFIX + rel, src, sanitize=(rel == 'book.json'))
            files[rel] = record
            total += record['size']
            if total > MAX_TOTAL_SIZE:
                raise BackupError('Dit boek met zijn versies is te groot voor een .qwbook-back-up.')
        if 'book.json' not in files:
            raise BackupError('Het boek mist zijn boekinformatie.')
        # Copy only committed versions: in-progress copytree directories are not registered.
        # Keep history.json unchanged, so restored version listings match the archived folders.
        if history_root.exists():
            index_path = history_root / 'history.json'
            if index_path.is_file():
                record = _stream_member(archive, HISTORY_PREFIX + 'history.json', index_path)
                history_files['history.json'] = record
                count += 1
                total += record['size']
            for version_folder in sorted(set(registered.values())):
                _safe_member_name(version_folder)
                folder = history_root / version_folder
                if not folder.is_dir() or folder.is_symlink():
                    raise BackupError('Een geregistreerde boekversie ontbreekt.')
                for rel, src in _iter_tree_files(folder):
                    name = version_folder + '/' + rel
                    count += 1
                    if count > MAX_FILE_COUNT:
                        raise BackupError('Dit boek bevat te veel bestanden voor een back-up.')
                    record = _stream_member(archive, HISTORY_PREFIX + name, src,
                                            sanitize=(rel == 'book.json'))
                    history_files[name] = record
                    total += record['size']
                    if total > MAX_TOTAL_SIZE:
                        raise BackupError('Dit boek met zijn versies is te groot voor een .qwbook-back-up.')
        package = {
            'format': PACKAGE_FORMAT, 'version': PACKAGE_VERSION,
            'book_id': book.id, 'title': book.title,
            'files': files, 'history_files': history_files,
            'privacy': {'source_file_removed': True},
            'history_included': True, 'ai_chat_included': True,
        }
        archive.writestr(MANIFEST_NAME, json.dumps(package, ensure_ascii=False, indent=2))
    return package


def _publish(source, target):
    for attempt in range(8):
        try:
            if target.exists():
                raise BackupError('Een back-up met deze naam bestaat al.')
            os.replace(source, target)
            return
        except PermissionError as exc:
            if attempt == 7:
                raise BackupError('De back-upmap is tijdelijk in gebruik.') from exc
            time.sleep(0.04 * (attempt + 1))


def _cleanup_old_partials(folder, *, now=None):
    now = time.time() if now is None else now
    for p in folder.glob('.*.partial'):
        try:
            if p.is_file() and not p.is_symlink() and now - p.stat().st_mtime > 86400:
                p.unlink()
        except OSError:
            pass


def create_backup(library, book, root: Path, *, now: datetime | None = None, automatic: bool = False) -> Path:
    """Publish only a fully written, flushed, validated and unchanged snapshot."""
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,128}', book.id):
        raise BackupError('Dit boek heeft geen geldige identiteit voor een back-up.')
    destination_root = validate_backup_root(library.root, root)
    folder = destination_root / 'QuietWriter' / book.id
    try:
        if any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction())
               for p in (folder, folder.parent)):
            raise BackupError('Deze back-upmap bevat een koppeling.')
        folder.mkdir(parents=True, exist_ok=True)
        _cleanup_old_partials(folder)
        stamp = (now or datetime.now()).strftime('%Y-%m-%d_%H%M%S')
        result = folder / f'{"auto_" if automatic else ""}{stamp}_{uuid.uuid4().hex}.qwbook'
        partial = folder / ('.' + result.name + '.partial')
        before = library.capture_revision(book)
        history_before, registered = _history_state(library, book)
        try:
            _export_streaming(library, book, partial, registered)
            with partial.open('r+b') as stream:
                os.fsync(stream.fileno())
            validate_archive(partial, book.id)
            after = library.capture_revision(book)
            history_after, _ = _history_state(library, book)
            if before.changed_files(after) or history_before != history_after:
                raise BackupError('Het boek veranderde tijdens de back-up. Probeer het opnieuw.')
            _publish(partial, result)
            if os.name != 'nt':
                try:
                    fd = os.open(folder, os.O_RDONLY)
                    try:
                        os.fsync(fd)
                    finally:
                        os.close(fd)
                except OSError:
                    # Directory durability is platform/filesystem dependent.
                    pass
            return result
        finally:
            try:
                partial.unlink(missing_ok=True)
            except OSError:
                pass
    except BackupError:
        raise
    except ExternalModificationError as exc:
        raise BackupError('Het boek is buiten QuietWriter gewijzigd. Open het opnieuw en probeer het nog eens.') from exc
    except BookBlockedError as exc:
        raise BackupError('Dit boek is geblokkeerd. Los de melding bij het boek eerst op.') from exc
    except QwBookError as exc:
        raise BackupError('Een bestand in dit boek kan niet veilig worden meegenomen: ' + str(exc)) from exc
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        raise BackupError('De back-up kon niet worden opgeslagen. Controleer de locatie en vrije ruimte.') from exc
