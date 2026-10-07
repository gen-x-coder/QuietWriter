"""Read-only summaries for guided export.

Nothing in this module may create, write or touch files: looking must never
mutate the workspace. In particular history is inspected through plain
filesystem reads, never through Library helpers that create archive folders.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from ..manuscript_text import count_words
from .models import ExportDocument

AI_CHAT_FILE = '.quietwriter/ai_chat.json'


@dataclass(frozen=True)
class SectionSummary:
    title: str
    chapters: int
    words: int


@dataclass(frozen=True)
class ContentSummary:
    words: int
    chapters: int
    sections: tuple[SectionSummary, ...]
    images: int
    has_cover: bool
    front_matter: tuple[str, ...]
    back_matter: tuple[str, ...]


@dataclass(frozen=True)
class PackageSummary:
    has_planning: bool
    has_profile: bool
    has_memory: bool
    has_ai_chat: bool
    history_versions: int
    history_bytes: int
    history_files: int
    history_ai_chat_bytes: int
    history_ai_chat_files: int
    book_bytes: int
    book_files: int
    ai_chat_bytes: int
    media_files: int

    def estimated_bytes(self, *, include_history: bool, include_ai_chat: bool) -> int:
        total = self.book_bytes
        if not include_ai_chat:
            total -= self.ai_chat_bytes
        if include_history:
            total += self.history_bytes
            if not include_ai_chat:
                total -= self.history_ai_chat_bytes
        return max(0, total)

    def estimated_files(self, *, include_history: bool, include_ai_chat: bool) -> int:
        total = self.book_files
        if not include_ai_chat and self.ai_chat_bytes:
            total -= 1
        if include_history:
            total += self.history_files
            if not include_ai_chat:
                total -= self.history_ai_chat_files
        return max(0, total)


def round_words(words: int) -> int:
    """Round to hundreds for display ('ongeveer 82.400 woorden'); small counts stay exact."""
    if words < 1000:
        return words
    return int(round(words / 100.0)) * 100


def build_content_summary(document: ExportDocument) -> ContentSummary:
    sections: list[SectionSummary] = []
    total = 0
    for section in document.sections:
        words = sum(count_words(chapter.markdown) for chapter in section.chapters)
        total += words
        sections.append(SectionSummary(title=section.title, chapters=len(section.chapters), words=words))
    return ContentSummary(
        words=total,
        chapters=document.chapter_count,
        sections=tuple(sections),
        images=document.inline_asset_count,
        has_cover=document.cover_asset is not None,
        front_matter=tuple(item.key for item in document.front_matter),
        back_matter=tuple(item.key for item in document.back_matter),
    )


def _tree_size(root: Path) -> tuple[int, int]:
    """(bytes, files) of a tree, read-only, without following symlinks."""
    total = 0
    count = 0
    if not root.is_dir():
        return 0, 0
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(Path(entry.path))
                        elif entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                            count += 1
                    except OSError:
                        continue
        except OSError:
            continue
    return total, count


def _history_ai_chat_stats(history_root: Path) -> tuple[int, int]:
    """Return (bytes, files) for Reader conversations inside history snapshots."""
    if not history_root.is_dir():
        return 0, 0
    total = 0
    count = 0
    try:
        candidates = history_root.rglob('ai_chat.json')
        for path in candidates:
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                relative = path.relative_to(history_root).as_posix()
                if relative == AI_CHAT_FILE or relative.endswith('/' + AI_CHAT_FILE):
                    total += path.stat().st_size
                    count += 1
            except (OSError, ValueError):
                continue
    except OSError:
        pass
    return total, count


def _history_version_count(history_root: Path) -> int:
    index = history_root / 'history.json'
    if index.is_file():
        try:
            data = json.loads(index.read_text(encoding='utf-8'))
            versions = data.get('versions') if isinstance(data, dict) else None
            if isinstance(versions, dict):
                return len(versions)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            pass
    if not history_root.is_dir():
        return 0
    try:
        return sum(1 for entry in history_root.iterdir() if entry.is_dir())
    except OSError:
        return 0


def build_package_summary(library, book) -> PackageSummary:
    book_root = Path(book.path)
    history_root = Path(library.archive_dir) / str(book.id)   # read-only: never via _history_root()
    book_bytes, book_files = _tree_size(book_root)
    history_bytes, history_files = _tree_size(history_root)
    history_ai_chat_bytes, history_ai_chat_files = _history_ai_chat_stats(history_root)
    chat = book_root / AI_CHAT_FILE
    try:
        chat_bytes = chat.stat().st_size if chat.is_file() else 0
    except OSError:
        chat_bytes = 0
    planning = book_root / 'planning'
    has_planning = any((planning / name).is_file() for name in ('outline.json', 'characters.json', 'notes.md'))
    _media_bytes, media_files = _tree_size(book_root / 'assets')
    return PackageSummary(
        has_planning=has_planning,
        has_profile=(book_root / 'ai' / 'boekprofiel.md').is_file(),
        has_memory=(book_root / 'ai' / 'memory.md').is_file(),
        has_ai_chat=chat_bytes > 0,
        history_versions=_history_version_count(history_root),
        history_bytes=history_bytes,
        history_files=history_files,
        history_ai_chat_bytes=history_ai_chat_bytes,
        history_ai_chat_files=history_ai_chat_files,
        book_bytes=book_bytes,
        book_files=book_files,
        ai_chat_bytes=chat_bytes,
        media_files=media_files,
    )
