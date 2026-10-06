from __future__ import annotations

from pathlib import Path


def normalize_workspace_path(value: str | Path | None, default: str | Path) -> Path:
    """Return a safe absolute workspace path.

    Relative input is interpreted below the user's home directory instead of
    the current/program directory. This prevents portable updates from taking
    user books with them when an old application folder is replaced.
    """
    default_path = Path(default).expanduser()
    raw = str(value or '').strip()
    path = Path(raw).expanduser() if raw else default_path
    if not path.is_absolute():
        path = Path.home() / path
    return path.resolve(strict=False)
