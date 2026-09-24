from __future__ import annotations

from datetime import datetime
import faulthandler
from pathlib import Path
import sys
import tempfile
import threading
import traceback


_LOG_HANDLE = None
_ORIGINAL_EXCEPTHOOK = sys.excepthook
_ORIGINAL_THREADING_EXCEPTHOOK = getattr(threading, 'excepthook', None)
_MAX_LOG_BYTES = 2 * 1024 * 1024


def _rotate_if_needed(log_path: Path, max_bytes: int = _MAX_LOG_BYTES) -> None:
    """Keep one bounded previous crash log; rotation itself must never abort startup."""
    try:
        if not log_path.exists() or log_path.stat().st_size < max_bytes:
            return
        backup = log_path.with_name(log_path.name + '.1')
        try:
            backup.unlink(missing_ok=True)
        except OSError:
            pass
        try:
            log_path.replace(backup)
        except OSError:
            # If rename is blocked by sync/AV software, truncate as the safer
            # fallback rather than allowing unbounded growth.
            try:
                log_path.write_text('', encoding='utf-8')
            except OSError:
                pass
    except OSError:
        pass


def _open_append_handle(log_path: Path):
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _rotate_if_needed(log_path)
    return log_path.open('a', encoding='utf-8', buffering=1), log_path


def _open_crash_log(preferred_path: Path):
    """Open the preferred log, falling back to the OS temp directory on failure."""
    preferred_path = Path(preferred_path)
    try:
        return _open_append_handle(preferred_path)
    except (OSError, PermissionError):
        fallback = Path(tempfile.gettempdir()) / 'QuietWriter' / 'crash.log'
        try:
            return _open_append_handle(fallback)
        except (OSError, PermissionError):
            return None, preferred_path


def enable_crash_logging(log_path: Path) -> Path:
    """Enable best-effort crash logging without ever making startup depend on it.

    The preferred workspace log is used when possible. If that location cannot
    be created/opened, QuietWriter falls back to the OS temporary directory. If
    even that fails, startup simply continues with the normal Python hooks.
    """
    global _LOG_HANDLE

    handle, actual_path = _open_crash_log(Path(log_path))
    if handle is None:
        return actual_path

    # This function normally runs once, but keeping it safe for repeated calls
    # makes tests and future workspace switching predictable.
    if _LOG_HANDLE is not None and _LOG_HANDLE is not handle:
        try:
            faulthandler.disable()
        except Exception:
            pass
        try:
            _LOG_HANDLE.close()
        except Exception:
            pass
    _LOG_HANDLE = handle

    try:
        _LOG_HANDLE.write(
            f'\n=== QuietWriter start {datetime.now().isoformat(timespec="seconds")} '
            f'Python {sys.version.split()[0]} ===\n'
        )
        _LOG_HANDLE.flush()
    except Exception:
        # A log destination can disappear between open() and the first write
        # (network drive/sync mount). Logging remains optional.
        try:
            _LOG_HANDLE.close()
        except Exception:
            pass
        _LOG_HANDLE = None
        return actual_path

    try:
        faulthandler.enable(_LOG_HANDLE, all_threads=True)
    except Exception as exc:
        try:
            _LOG_HANDLE.write(f'faulthandler kon niet worden geactiveerd: {exc!r}\n')
        except Exception:
            pass

    def exception_hook(exc_type, exc_value, exc_tb):
        try:
            if _LOG_HANDLE is not None:
                _LOG_HANDLE.write(f'\n--- Onverwerkte Python-exception {datetime.now().isoformat(timespec="seconds")} ---\n')
                traceback.print_exception(exc_type, exc_value, exc_tb, file=_LOG_HANDLE)
                _LOG_HANDLE.flush()
        except Exception:
            pass
        finally:
            _ORIGINAL_EXCEPTHOOK(exc_type, exc_value, exc_tb)

    sys.excepthook = exception_hook

    if _ORIGINAL_THREADING_EXCEPTHOOK is not None:
        def thread_exception_hook(args):
            try:
                if _LOG_HANDLE is not None:
                    _LOG_HANDLE.write(
                        f'\n--- Onverwerkte thread-exception {datetime.now().isoformat(timespec="seconds")} '
                        f'({getattr(args.thread, "name", "thread")}) ---\n'
                    )
                    traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback, file=_LOG_HANDLE)
                    _LOG_HANDLE.flush()
            except Exception:
                pass
            finally:
                _ORIGINAL_THREADING_EXCEPTHOOK(args)

        threading.excepthook = thread_exception_hook

    return actual_path
