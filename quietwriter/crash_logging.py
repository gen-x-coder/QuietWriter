from __future__ import annotations

from datetime import datetime
import faulthandler
from pathlib import Path
import sys
import threading
import traceback


_LOG_HANDLE = None
_ORIGINAL_EXCEPTHOOK = sys.excepthook
_ORIGINAL_THREADING_EXCEPTHOOK = getattr(threading, 'excepthook', None)


def enable_crash_logging(log_path: Path) -> Path:
    """Write fatal/native and uncaught Python failures to a persistent log.

    The handle intentionally stays open for the lifetime of the process because
    faulthandler writes directly to its file descriptor when Python is no longer
    in a state where normal logging is reliable.
    """
    global _LOG_HANDLE
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _LOG_HANDLE = log_path.open('a', encoding='utf-8', buffering=1)
    _LOG_HANDLE.write(
        f'\n=== QuietWriter start {datetime.now().isoformat(timespec="seconds")} '
        f'Python {sys.version.split()[0]} ===\n'
    )
    _LOG_HANDLE.flush()

    try:
        faulthandler.enable(_LOG_HANDLE, all_threads=True)
    except Exception as exc:
        _LOG_HANDLE.write(f'faulthandler kon niet worden geactiveerd: {exc!r}\n')

    def exception_hook(exc_type, exc_value, exc_tb):
        try:
            _LOG_HANDLE.write(f'\n--- Onverwerkte Python-exception {datetime.now().isoformat(timespec="seconds")} ---\n')
            traceback.print_exception(exc_type, exc_value, exc_tb, file=_LOG_HANDLE)
            _LOG_HANDLE.flush()
        finally:
            _ORIGINAL_EXCEPTHOOK(exc_type, exc_value, exc_tb)

    sys.excepthook = exception_hook

    if _ORIGINAL_THREADING_EXCEPTHOOK is not None:
        def thread_exception_hook(args):
            try:
                _LOG_HANDLE.write(
                    f'\n--- Onverwerkte thread-exception {datetime.now().isoformat(timespec="seconds")} '
                    f'({getattr(args.thread, "name", "thread")}) ---\n'
                )
                traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback, file=_LOG_HANDLE)
                _LOG_HANDLE.flush()
            finally:
                _ORIGINAL_THREADING_EXCEPTHOOK(args)

        threading.excepthook = thread_exception_hook

    return log_path
