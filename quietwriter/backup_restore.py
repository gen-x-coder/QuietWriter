"""Deliberate, safeguarded replacement of an existing book from a .qwbook."""
from __future__ import annotations

import os
import shutil
import time
import tempfile
from pathlib import Path

from .automatic_backups import create_backup, BackupError
from .qwbook_io import QwBookError, import_qwbook, _load_package, AI_CHAT_RELATIVE
from .storage import Library
import zipfile


class RestoreError(RuntimeError):
    """The active book was not replaced; a backup or a recovery copy is kept."""


def backup_identity(source: Path) -> tuple[str, str]:
    try:
        with zipfile.ZipFile(source) as archive:
            info = _load_package(archive)
            return str(info['book_id']), str(info['title'])
    except (OSError, ValueError, KeyError, QwBookError, zipfile.BadZipFile) as exc:
        raise RestoreError('Deze back-up kan niet worden gelezen.') from exc


def _cleanup_old_restore_workspaces(stage_base: Path, *, older_than_seconds: int = 86400) -> None:
    """Retry cleanup only for abandoned restore workspaces, never active ones."""
    try:
        for folder in stage_base.glob('restore-*'):
            if folder.is_dir() and not folder.is_symlink() and not (folder / '.preserve-for-rescue').exists() and time.time() - folder.stat().st_mtime > older_than_seconds:
                shutil.rmtree(folder, ignore_errors=True)
    except OSError:
        pass


def replace_existing_book(library: Library, source: Path, backup_root: Path, *, expected_id: str | None = None):
    """Stage and verify through the normal import, preserve current book, then swap.

    The staging directory and swap backups are on the workspace filesystem.
    They are intentionally retained after an interrupted swap for manual rescue.
    This function must not be used while an editor has the target book open.
    """
    source = Path(source)
    book_id, _ = backup_identity(source)
    with zipfile.ZipFile(source) as archive:
        package_manifest = _load_package(archive)
    history_included = bool(package_manifest.get('history_included', True))
    ai_chat_included = bool(package_manifest.get('ai_chat_included', True))
    if expected_id is not None and book_id != expected_id:
        raise RestoreError('De gekozen back-up hoort bij een ander boek.')
    matches = [b for b in library.list_books() if b.id == book_id]
    if len(matches) != 1:
        raise RestoreError('Het bestaande boek kon niet eenduidig worden gevonden.')
    original = matches[0]
    if not source.is_file():
        raise RestoreError('De gekozen back-up bestaat niet meer.')

    # Create a full verified safety copy before attempting to change anything.
    try:
        safety = create_backup(library, original, Path(backup_root))
    except (BackupError, OSError) as exc:
        raise RestoreError('Het huidige boek kon niet veilig worden bewaard. Er is niets vervangen.') from exc

    stage_base = library.root / '.restore-staging'
    stage_base.mkdir(exist_ok=True)
    _cleanup_old_restore_workspaces(stage_base)
    # On Windows a scan or a transient open handle can block deletion after a
    # successful swap. Cleanup must never turn a completed restore into an error.
    workspace = Path(tempfile.mkdtemp(prefix='restore-', dir=stage_base))
    preserve_workspace = False
    try:
        stage = Library(workspace)
        try:
            staged = import_qwbook(stage, source)
        except Exception as exc:
            raise RestoreError('De back-up kon niet worden gecontroleerd. Het huidige boek is behouden.') from exc
        if staged.id != book_id:
            raise RestoreError('De teruggezette kopie hoort bij een ander boek.')

        live_path = original.path
        history_path = library.archive_dir / book_id
        staged_history = stage.archive_dir / book_id
        # Move old content aside (on the same filesystem) before replacing.
        # These filenames must not be treated as books by list_books().
        retired_book = Path(workspace) / 'previous-book'
        retired_history = Path(workspace) / 'previous-history'
        moved_book = moved_history = installed_book = installed_history = False
        try:
            os.replace(live_path, retired_book)
            moved_book = True
            if history_included and history_path.exists():
                os.replace(history_path, retired_history)
                moved_history = True
            # Preserve local AI conversation if this exported package deliberately
            # omitted it. It is unrelated to the manuscript being restored.
            if not ai_chat_included:
                # AI conversations are local to this installation, not the
                # book profile and book memory included in the backup.
                chat_source = retired_book / AI_CHAT_RELATIVE
                if chat_source.is_file():
                    chat_target = staged.path / AI_CHAT_RELATIVE
                    chat_target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(chat_source, chat_target)
            os.replace(staged.path, live_path)
            installed_book = True
            if history_included and staged_history.exists():
                os.replace(staged_history, history_path)
                installed_history = True
            restored = library.load_book(live_path)
            if restored.id != book_id:
                raise RestoreError('De boekidentiteit klopt niet na herstel.')
            library.track_book(restored)
            # Shelf metadata is deliberately untouched: same ID, same shelf.
            return restored, safety
        except Exception as exc:
            # Every rollback action is attempted, even if an earlier action is locked.
            rollback_errors = []
            for enabled, current, destination in (
                (installed_history, history_path, staged_history),
                (installed_book, live_path, staged.path),
                (moved_history, retired_history, history_path),
                (moved_book, retired_book, live_path),
            ):
                if enabled and current.exists():
                    try:
                        os.replace(current, destination)
                    except OSError as rollback_exc:
                        rollback_errors.append(rollback_exc)
            if rollback_errors:
                # Never destroy a workspace that may hold the only intact original.
                # Move intact originals to a durable rescue directory. A preexisting
                # rescue must not be overwritten by a later failed restore.
                preserve_workspace = True
                rescue_parent = library.root / '.restore-rescue' / book_id
                rescue_parent.mkdir(parents=True, exist_ok=True)
                # Older rescues are not overwritten. Move them into a uniquely
                # named archive before putting the CURRENT rescue at the stable
                # documented location.
                prior = [(rescue_parent / name) for name in ('book', 'history')
                         if (rescue_parent / name).exists()]
                if prior:
                    old_rescue = Path(tempfile.mkdtemp(prefix='previous-', dir=rescue_parent))
                    for old_path in prior:
                        try:
                            os.replace(old_path, old_rescue / old_path.name)
                        except OSError:
                            pass
                for name, original_path in (('book', retired_book), ('history', retired_history)):
                    if original_path.exists():
                        destination = rescue_parent / name
                        if not destination.exists():
                            try:
                                os.replace(original_path, destination)
                            except OSError:
                                pass  # original remains in the protected workspace
                try:
                    (workspace / '.preserve-for-rescue').write_text(
                        'Herstelwerkmap bewaren; niet automatisch verwijderen.\n', encoding='utf-8')
                except OSError:
                    pass  # Workspace is preserved regardless of marker write failures.
                raise RestoreError(
                    'Het terugzetten is niet gelukt. Je boek is veilig bewaard als back-up; '
                    'kies het in Instellingen > Herstellen.'
                ) from rollback_errors[0]
            raise RestoreError('Het terugzetten is afgebroken. Je oorspronkelijke boek is behouden.') from exc

    finally:
        # Keep any temporarily locked folder for a later safe cleanup attempt.
        # The separate .qwbook safety copy remains outside this workspace.
        if not preserve_workspace:
            try:
                shutil.rmtree(workspace)
            except OSError:
                pass  # transient Windows lock must not undo a successful restore
