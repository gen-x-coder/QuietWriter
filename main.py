from __future__ import annotations

import sys


def _require_supported_python() -> None:
    if sys.version_info >= (3, 12):
        return
    message = (
        "QuietWriter vereist Python 3.12 of nieuwer.\n"
        f"Gevonden: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}."
    )
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, "QuietWriter", 0x10)
        except Exception:
            print(message, file=sys.stderr)
    else:
        print(message, file=sys.stderr)
    raise SystemExit(2)


_require_supported_python()


def _velopack_startup() -> None:
    """Velopack moet als eerste draaien: bij installeren/bijwerken kan het
    dit proces afhandelen en beëindigen. In een bronversie of een oude
    portable zip doet dit niets."""
    try:
        import velopack
    except ImportError:
        return
    try:
        velopack.App().run()
    except Exception:
        # Een kapotte of ontbrekende Velopack-installatie mag het schrijven
        # nooit blokkeren; QuietWriter valt dan terug op alleen melden.
        pass


_velopack_startup()

from quietwriter.app import run  # noqa: E402  (pas na de Velopack-hook)

if __name__ == '__main__':
    raise SystemExit(run())
