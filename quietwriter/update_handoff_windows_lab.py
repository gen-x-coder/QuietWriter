"""Windows-only parent-process handoff proof for disposable updater laboratories.

A READY event is *not* permission to install; it only acknowledges that a
verified process handle has been opened before the parent is allowed to exit.
This module never accesses an installation, book, or updater transaction.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import uuid


class HandoffError(RuntimeError):
    pass


def _kernel():
    if os.name != 'nt':
        raise HandoffError('Windows handoff is unavailable on this platform')
    import ctypes
    from ctypes import wintypes
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    HANDLE = wintypes.HANDLE
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.OpenProcess.restype = HANDLE
    k.CloseHandle.argtypes = [HANDLE]
    k.CloseHandle.restype = wintypes.BOOL
    k.GetProcessTimes.argtypes = [HANDLE, ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME)]
    k.GetProcessTimes.restype = wintypes.BOOL
    k.QueryFullProcessImageNameW.argtypes = [HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    k.QueryFullProcessImageNameW.restype = wintypes.BOOL
    k.CreateEventW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
    k.CreateEventW.restype = HANDLE
    k.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    k.OpenEventW.restype = HANDLE
    k.SetEvent.argtypes = [HANDLE]
    k.SetEvent.restype = wintypes.BOOL
    k.WaitForSingleObject.argtypes = [HANDLE, wintypes.DWORD]
    k.WaitForSingleObject.restype = wintypes.DWORD
    return k, ctypes, wintypes


def _handle_identity(k, ctypes, wintypes, handle):
    created = wintypes.FILETIME(); exited = wintypes.FILETIME()
    kernel = wintypes.FILETIME(); user = wintypes.FILETIME()
    if not k.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(kernel), ctypes.byref(user)):
        raise HandoffError('Cannot read source process creation time')
    length = wintypes.DWORD(32768)
    buf = ctypes.create_unicode_buffer(length.value)
    if not k.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(length)):
        raise HandoffError('Cannot verify source process executable path')
    ticks = (created.dwHighDateTime << 32) | created.dwLowDateTime
    return ticks, Path(buf.value)


def process_identity(pid: int) -> tuple[int, str]:
    """Read stable identity from a live process; fail closed if it has exited."""
    k, ctypes, wintypes = _kernel()
    if pid <= 0:
        raise HandoffError('Invalid source PID')
    h = k.OpenProcess(0x00100000 | 0x1000, False, pid)
    if not h:
        raise HandoffError('Source process no longer available')
    try:
        t, path = _handle_identity(k, ctypes, wintypes, h)
        return t, str(path)
    finally:
        k.CloseHandle(h)


def new_event_name() -> str:
    return 'Local\\QuietWriterUpdateLab-' + uuid.uuid4().hex


def _validate_event_name(name: str) -> None:
    import re
    if not re.fullmatch(r'Local\\QuietWriterUpdateLab-[0-9a-f]{32}', name):
        raise HandoffError('Unsafe or invalid lab ready event')


@dataclass
class ReadyEvent:
    name: str
    handle: object

    @classmethod
    def create(cls):
        k, _, _ = _kernel()
        name = new_event_name()
        handle = k.CreateEventW(None, True, False, name)
        if not handle:
            raise HandoffError('Unable to create lab READY event')
        return cls(name, handle)

    def await_ready(self, timeout: float = 10.0) -> None:
        k, _, _ = _kernel()
        result = k.WaitForSingleObject(self.handle, max(0, int(timeout * 1000)))
        if result != 0:
            raise HandoffError('Lab updater did not acknowledge process handle before exit')

    def close(self) -> None:
        k, _, _ = _kernel()
        if self.handle:
            k.CloseHandle(self.handle)
            self.handle = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def wait_verified_parent(pid: int, created: int, image_path: str, ready_event: str, timeout: float = 30.0) -> None:
    """Acquire/verify HANDLE first, signal READY, then wait on the SAME HANDLE."""
    k, ctypes, wintypes = _kernel()
    _validate_event_name(ready_event)
    if pid <= 0 or created <= 0 or not Path(image_path).is_absolute() or timeout <= 0:
        raise HandoffError('Invalid source process identity')
    h = k.OpenProcess(0x00100000 | 0x1000, False, pid)
    if not h:
        raise HandoffError('Source process exited before handoff could begin')
    try:
        actual_created, actual_path = _handle_identity(k, ctypes, wintypes, h)
        if actual_created != created or os.path.normcase(os.path.normpath(str(actual_path))) != os.path.normcase(os.path.normpath(str(Path(image_path)))):
            raise HandoffError('Source process identity mismatch')
        # Do not acknowledge an already-terminated parent; it cannot promise a
        # clean, controlled close. The open HANDLE eliminates PID-reuse races.
        if k.WaitForSingleObject(h, 0) != 0x102:  # WAIT_TIMEOUT
            raise HandoffError('Source process terminated before READY')
        evt = k.OpenEventW(0x0002, False, ready_event)  # EVENT_MODIFY_STATE
        if not evt:
            raise HandoffError('Lab READY event not found')
        try:
            if not k.SetEvent(evt):
                raise HandoffError('Unable to acknowledge lab process handle')
        finally:
            k.CloseHandle(evt)
        result = k.WaitForSingleObject(h, min(int(timeout * 1000), 0xFFFFFFFE))
        if result != 0:
            raise HandoffError('Source process did not exit after READY')
    finally:
        k.CloseHandle(h)
