from __future__ import annotations

from datetime import datetime
import faulthandler
from pathlib import Path
import sys
import tempfile
import threading
import traceback
from typing import Callable


_LOG_HANDLE = None
_LOG_PATH: Path | None = None
_ERROR_NOTIFIER: Callable[[str, str], None] | None = None
_ORIGINAL_EXCEPTHOOK = sys.excepthook
_ORIGINAL_THREADING_EXCEPTHOOK = getattr(threading, 'excepthook', None)
_ORIGINAL_QT_MESSAGE_HANDLER = None
_QT_HANDLER_INSTALLED = False
_MAX_LOG_BYTES = 2 * 1024 * 1024


def _rotate_if_needed(log_path: Path, max_bytes: int = _MAX_LOG_BYTES) -> None:
    """Keep one bounded previous log; rotation itself must never abort startup."""
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
        fallback = Path(tempfile.gettempdir()) / 'QuietWriter' / 'logs' / 'crash.log'
        try:
            return _open_append_handle(fallback)
        except (OSError, PermissionError):
            return None, preferred_path


def current_log_path() -> Path | None:
    return _LOG_PATH


def set_error_notifier(callback: Callable[[str, str], None] | None) -> None:
    """Set the UI notification callback used for uncaught Python errors.

    The callback receives ``(short_message, details)``. It may be called from a
    worker thread, so GUI clients should bridge this through a Qt signal.
    """
    global _ERROR_NOTIFIER
    _ERROR_NOTIFIER = callback


def _write(text: str) -> None:
    try:
        if _LOG_HANDLE is not None:
            _LOG_HANDLE.write(text)
            _LOG_HANDLE.flush()
    except Exception:
        pass


def _notify(short_message: str, details: str) -> None:
    callback = _ERROR_NOTIFIER
    if callback is None:
        return
    try:
        callback(short_message, details)
    except Exception:
        # The crash reporter must never cause a second crash.
        pass


def _install_qt_message_handler() -> None:
    """Mirror Qt's own warnings/errors into the same local log file."""
    global _ORIGINAL_QT_MESSAGE_HANDLER, _QT_HANDLER_INSTALLED
    if _QT_HANDLER_INSTALLED:
        return
    try:
        from PySide6.QtCore import QtMsgType, qInstallMessageHandler
    except Exception:
        return

    labels = {
        QtMsgType.QtDebugMsg: 'DEBUG',
        QtMsgType.QtInfoMsg: 'INFO',
        QtMsgType.QtWarningMsg: 'WARNING',
        QtMsgType.QtCriticalMsg: 'CRITICAL',
        QtMsgType.QtFatalMsg: 'FATAL',
    }

    def qt_message_handler(msg_type, context, message):
        label = labels.get(msg_type, 'QT')
        source = ''
        try:
            if context is not None and getattr(context, 'file', None):
                source = f" {context.file}:{getattr(context, 'line', 0)}"
        except Exception:
            source = ''
        _write(f'[{datetime.now().isoformat(timespec="seconds")}] Qt {label}{source}: {message}\n')
        previous = _ORIGINAL_QT_MESSAGE_HANDLER
        if previous is not None:
            try:
                previous(msg_type, context, message)
            except Exception:
                pass

    try:
        _ORIGINAL_QT_MESSAGE_HANDLER = qInstallMessageHandler(qt_message_handler)
        _QT_HANDLER_INSTALLED = True
    except Exception:
        _ORIGINAL_QT_MESSAGE_HANDLER = None
        _QT_HANDLER_INSTALLED = False
_QT_HANDLER_INSTALLED = False


def enable_crash_logging(log_path: Path) -> Path:
    """Enable best-effort local crash logging without making startup depend on it."""
    global _LOG_HANDLE, _LOG_PATH

    handle, actual_path = _open_crash_log(Path(log_path))
    _LOG_PATH = actual_path
    if handle is None:
        return actual_path

    # This function normally runs once, but keeping it safe for repeated calls
    # makes tests predictable.
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
        try:
            _LOG_HANDLE.close()
        except Exception:
            pass
        _LOG_HANDLE = None
        return actual_path

    try:
        faulthandler.enable(_LOG_HANDLE, all_threads=True)
    except Exception as exc:
        _write(f'faulthandler kon niet worden geactiveerd: {exc!r}\n')

    def exception_hook(exc_type, exc_value, exc_tb):
        stamp = datetime.now().isoformat(timespec='seconds')
        _write(f'\n--- Onverwerkte Python-exception {stamp} ---\n')
        try:
            if _LOG_HANDLE is not None:
                traceback.print_exception(exc_type, exc_value, exc_tb, file=_LOG_HANDLE)
                _LOG_HANDLE.flush()
        except Exception:
            pass
        details = ''.join(traceback.format_exception_only(exc_type, exc_value)).strip()
        _notify('Er ging iets mis in QuietWriter.', details)
        try:
            _ORIGINAL_EXCEPTHOOK(exc_type, exc_value, exc_tb)
        except Exception:
            pass

    sys.excepthook = exception_hook

    if _ORIGINAL_THREADING_EXCEPTHOOK is not None:
        def thread_exception_hook(args):
            stamp = datetime.now().isoformat(timespec='seconds')
            name = getattr(args.thread, 'name', 'thread')
            _write(f'\n--- Onverwerkte thread-exception {stamp} ({name}) ---\n')
            try:
                if _LOG_HANDLE is not None:
                    traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback, file=_LOG_HANDLE)
                    _LOG_HANDLE.flush()
            except Exception:
                pass
            details = ''.join(traceback.format_exception_only(args.exc_type, args.exc_value)).strip()
            _notify('Er ging iets mis in een achtergrondtaak.', details)
            try:
                _ORIGINAL_THREADING_EXCEPTHOOK(args)
            except Exception:
                pass

        threading.excepthook = thread_exception_hook

    _install_qt_message_handler()
    return actual_path
