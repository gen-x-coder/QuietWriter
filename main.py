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

def _health_request(argv):
    if '--update-health-check' not in argv:
        return None
    # Health checking is intentionally isolated from the user's normal profile:
    # the existing smoke-test builds temporary settings and workspace.
    i = argv.index('--update-health-check')
    if len(argv) != i + 3:
        return 2
    from pathlib import Path
    from quietwriter.update_health import run_health_check
    from quietwriter.app import run
    token, path = argv[i+1:i+3]
    sys.argv = [argv[0], '--smoke-test']
    try:
        return run_health_check(token, Path(path), run)
    except Exception as exc:
        print(f'Update health check failed: {type(exc).__name__}', file=sys.stderr)
        return 1

from quietwriter.app import run

if __name__ == '__main__':
    health = _health_request(sys.argv)
    raise SystemExit(run() if health is None else health)
