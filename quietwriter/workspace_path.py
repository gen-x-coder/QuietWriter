from __future__ import annotations

from pathlib import Path
import sys
import tempfile

from .i18n import tr


class UnsafeWorkspacePath(ValueError):
    """A user data directory would be inside the replaceable installation."""


def portable_install_root() -> Path | None:
    """Only frozen portable executables have a replaceable installation root."""
    if not getattr(sys, "frozen", False):
        return None
    exe_dir = Path(sys.executable).resolve(strict=False).parent
    # Velopack (portable zip of Setup): het programma staat in ``current/``
    # naast ``Update.exe``. De hele Velopack-map is van het programma.
    if exe_dir.name.lower() == 'current' and (exe_dir.parent / 'Update.exe').is_file():
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


class WorkspaceNotWritable(UnsafeWorkspacePath):
    """QuietWriter mag niet schrijven in de gekozen map."""


def require_writable_directory(path: str | Path) -> Path:
    """Controleer met een echt tijdelijk bestand of QuietWriter hier mag schrijven.

    Op Windows blokkeert *Beveiligde mapcontrole* (Controlled Folder Access)
    onbekende programma's in Documenten en Bureaublad. Zonder deze controle
    merkt de schrijver dat pas bij de eerste mislukte opslag. Er wordt geen map
    aangemaakt: bestaat de map nog niet, dan wordt de dichtstbijzijnde bestaande
    bovenliggende map getest.
    """
    target = Path(path).expanduser()
    probe_dir = target
    while not probe_dir.exists() and probe_dir.parent != probe_dir:
        probe_dir = probe_dir.parent
    try:
        with tempfile.NamedTemporaryFile(prefix='.quietwriter-schrijftest-', dir=str(probe_dir), delete=True) as handle:
            handle.write(b'ok')
            handle.flush()
    except OSError as exc:
        raise WorkspaceNotWritable(tr(
            'workspace.not_writable',
            'QuietWriter kan niet schrijven in deze map:\n{path}\n\nMisschien blokkeert Windows-beveiliging (Beveiligde mapcontrole) dit, of heb je hier geen schrijfrechten. Kies een andere map, of sta QuietWriter toe via Windows-beveiliging > Bescherming tegen ransomware.',
            path=str(target),
        )) from exc
    return target


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
