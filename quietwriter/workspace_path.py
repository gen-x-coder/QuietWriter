from __future__ import annotations

from pathlib import Path
import sys


class UnsafeWorkspacePath(ValueError):
    """A user data directory would be inside the replaceable installation."""


def portable_install_root() -> Path | None:
    """Only frozen portable executables have a replaceable installation root."""
    if not getattr(sys, "frozen", False):
        return None
    exe_dir = Path(sys.executable).resolve(strict=False).parent
    # Versioned install: the replaceable app-* folder and *all* sibling
    # versions live inside a shared non-replaceable installation root.
    if exe_dir.name.startswith('app-') and any(
        (exe_dir.parent / filename).is_file()
        for filename in ('current.json', 'current.a.json', 'current.b.json')
    ):
        return exe_dir.parent
    return exe_dir


def require_external_user_directory(path: str | Path, *, install_root: Path | None = None) -> Path:
    """Refuse book/backup folders inside or equal to the replaceable app tree.

    Resolve existing symlinks, including symlinked parent paths. On Windows
    Path.resolve also resolves junctions. Nothing is created or modified.
    """
    candidate = Path(path).expanduser().resolve(strict=False)
    root = install_root if install_root is not None else portable_install_root()
    if root is not None:
        installation = Path(root).resolve(strict=False)
        if candidate == installation or installation in candidate.parents:
            raise UnsafeWorkspacePath(
                "Boeken en back-ups mogen niet in de programmamap staan. "
                "Kies een map buiten de QuietWriter-installatie."
            )
    return candidate


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
