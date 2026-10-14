"""Per-workspace opt-in for the experimental updater, disabled by default.

This is a visibility switch, NEVER a security bypass or install authorization.
"""
from __future__ import annotations

from pathlib import Path

PILOT_MARKER = '.quietwriter-update-pilot'


def pilot_enabled(workspace: Path) -> bool:
    """Require a regular marker file directly inside the active book workspace.

    Missing/inaccessible directories, symlinks and directories never grant access.
    This function performs no I/O beyond filesystem metadata reads.
    """
    try:
        workspace = Path(workspace)
        if not workspace.is_dir() or workspace.is_symlink():
            return False
        marker = workspace / PILOT_MARKER
        return marker.is_file() and not marker.is_symlink() and marker.stat().st_size == 0
    except (OSError, ValueError, TypeError):
        return False
