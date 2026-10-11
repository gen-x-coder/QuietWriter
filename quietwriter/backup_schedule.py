"""Small, deliberately conservative automatic-backup scheduling and retention rules."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from .automatic_backups import BackupError, validate_archive


def backup_folder(root: Path, book_id: str) -> Path:
    return Path(root) / 'QuietWriter' / book_id


def latest_backup(root: Path, book_id: str) -> Path | None:
    folder = backup_folder(root, book_id)
    files = sorted(folder.glob('*.qwbook'), key=lambda p: p.stat().st_mtime, reverse=True) if folder.is_dir() else []
    return files[0] if files else None


def _source_last_change(book) -> float:
    """Content changes, not cache activity. Ignore hidden runtime folders."""
    root = Path(book.path)
    newest = 0.0
    for entry in root.rglob('*'):
        if any(part.startswith('.') for part in entry.relative_to(root).parts):
            continue
        if entry.is_symlink():
            raise BackupError('Een boekbestand verwijst naar een andere locatie.')
        if entry.is_file():
            newest = max(newest, entry.stat().st_mtime)
    return newest


def needs_daily_backup(book, root: Path, *, now: datetime | None = None) -> bool:
    """One backup per rolling day, only if the book changed since last backup."""
    current = (now or datetime.now()).timestamp()
    newest = latest_backup(root, book.id)
    if newest is None:
        return True
    completed = newest.stat().st_mtime
    if current - completed < 24 * 3600:
        return False
    return _source_last_change(book) > completed


def prune_automatic_backups(root: Path, book_id: str, *, newest_success: Path,
                            daily: int = 7, weekly: int = 4) -> list[Path]:
    """Keep recent daily and older weekly copies; never touch manual copies.

    Only call after an independently verified newly created archive. Validate
    the new file again before any deletion, and retain everything on errors.
    """
    validate_archive(newest_success, book_id)
    folder = backup_folder(root, book_id)
    if newest_success.parent.resolve() != folder.resolve():
        raise BackupError('De nieuwe back-up staat niet in de verwachte map.')
    files = sorted(folder.glob('auto_*.qwbook'), key=lambda p: p.stat().st_mtime, reverse=True)
    if newest_success not in files:
        raise BackupError('De nieuwste automatische back-up ontbreekt.')
    keep: set[Path] = {newest_success}
    days: set[str] = set()
    weeks: set[str] = set()
    for path in files:
        stamp = datetime.fromtimestamp(path.stat().st_mtime)
        day = stamp.strftime('%Y-%m-%d')
        week = f'{stamp.isocalendar().year}-{stamp.isocalendar().week:02d}'
        if day in days or week in weeks:
            continue
        if len(days) < daily:
            days.add(day)
            keep.add(path)
        elif len(weeks) < weekly:
            weeks.add(week)
            keep.add(path)
    deleted = []
    for path in files:
        if path not in keep:
            try:
                path.unlink()
            except OSError:
                continue  # Never cause a good backup to be reported as failed.
            deleted.append(path)
    return deleted
