"""Read-only discovery of cloud conflict copies in a QuietWriter workspace.

The result is advisory. Never resolve, rename, delete or overwrite a conflict.
"""
from __future__ import annotations

import os
from pathlib import Path


def is_conflict_copy(name: str) -> bool:
    name = name.casefold()
    return ('conflicted copy' in name or 'conflictkopie' in name
            or 'conflict copy' in name)


def discover_conflict_copies(workspace: Path, *, max_files: int = 50,
                             max_visited: int = 20_000) -> list[Path]:
    """Bounded read-only scan below books/; do not follow directory links."""
    root = Path(workspace) / 'books'
    if not root.is_dir() or root.is_symlink():
        return []
    found: list[Path] = []
    seen = 0
    def no_error(_error):
        return None
    for directory, subdirs, files in os.walk(root, topdown=True, followlinks=False,
                                             onerror=no_error):
        parent = Path(directory)
        subdirs[:] = [d for d in subdirs if not (parent / d).is_symlink()]
        for name in files:
            seen += 1
            path = parent / name
            if is_conflict_copy(name) and not path.is_symlink():
                found.append(path)
                if len(found) >= max_files:
                    return found
            if seen >= max_visited:
                return found
    return found
