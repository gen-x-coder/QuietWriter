from __future__ import annotations

import json
import re
from dataclasses import dataclass

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from . import __version__

LATEST_RELEASE_API = 'https://api.github.com/repos/gen-x-coder/QuietWriter/releases/latest'


@dataclass(frozen=True)
class UpdateResult:
    current_version: str
    latest_version: str
    release_url: str
    update_available: bool


def _version_tuple(value: str) -> tuple[int, ...]:
    """Return the numeric stable-version parts used by QuietWriter releases."""
    text = str(value or '').strip().lstrip('vV')
    match = re.match(r'^(\d+(?:\.\d+)*)', text)
    if not match:
        return ()
    return tuple(int(part) for part in match.group(1).split('.'))


def is_newer_version(candidate: str, current: str = __version__) -> bool:
    new = _version_tuple(candidate)
    old = _version_tuple(current)
    if not new or not old:
        return False
    size = max(len(new), len(old))
    return new + (0,) * (size - len(new)) > old + (0,) * (size - len(old))


class UpdateChecker(QObject):
    """Small asynchronous GitHub release check; never downloads an update."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = QNetworkAccessManager(self)
        self._reply = None

    def check(self) -> None:
        if self._reply is not None:
            return
        request = QNetworkRequest(QUrl(LATEST_RELEASE_API))
        request.setRawHeader(b'Accept', b'application/vnd.github+json')
        request.setRawHeader(b'User-Agent', f'QuietWriter/{__version__}'.encode('ascii', errors='ignore'))
        request.setTransferTimeout(5000)
        reply = self.manager.get(request)
        self._reply = reply
        reply.finished.connect(lambda r=reply: self._finished(r))

    def _finished(self, reply: QNetworkReply) -> None:
        self._reply = None
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self.failed.emit(reply.errorString() or 'network error')
                return
            payload = json.loads(bytes(reply.readAll()).decode('utf-8'))
            tag = str(payload.get('tag_name') or '').strip()
            url = str(payload.get('html_url') or '').strip()
            if not tag:
                raise ValueError('GitHub response has no tag_name')
            latest = tag[1:] if tag.lower().startswith('v') else tag
            self.finished.emit(UpdateResult(
                current_version=__version__,
                latest_version=latest,
                release_url=url,
                update_available=is_newer_version(latest),
            ))
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            reply.deleteLater()
