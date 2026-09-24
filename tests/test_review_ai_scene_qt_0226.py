from __future__ import annotations

import os
import tempfile
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from quietwriter.ai.conversations import ConversationStore
from quietwriter.ai.providers import StreamChunk
from quietwriter.ai.ui import AIPanel


class FakeSettings:
    def value(self, key, default=None, *args):
        if key == 'theme':
            return 'Helder'
        return default


class BlockingProvider:
    def __init__(self):
        self.release = threading.Event()
        self.cancelled = False

    def stream_chat(self, model, messages, **options):
        self.release.wait(5)
        if self.cancelled:
            return
        yield StreamChunk(content='antwoord blijft behouden')

    def cancel_active(self):
        self.cancelled = True


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _run_events(ms=160):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def test_same_book_adopt_does_not_cancel_active_ai_request(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        path = root / 'book'
        path.mkdir()
        book_v1 = SimpleNamespace(id='same-book', path=path)
        book_v2 = SimpleNamespace(id='same-book', path=path)

        main = SimpleNamespace(
            settings=FakeSettings(),
            library=SimpleNamespace(read_persona=lambda: 'persona'),
        )
        panel = AIPanel(main)
        panel.set_book(book_v1)
        provider = BlockingProvider()
        context = SimpleNamespace(label='test', pieces=['Testcontext'], text='context')
        panel._continue_send(provider, 'model', 'Vraag blijft actief', context)

        generation = panel._book_generation
        worker = panel.worker
        panel.set_book(book_v2)

        assert panel._book_generation == generation
        assert panel.worker is worker
        assert provider.cancelled is False
        assert [m['content'] for m in panel.messages] == ['Vraag blijft actief']

        provider.release.set()
        _run_events()

        stored = ConversationStore(book_v2).load()
        assert [m['content'] for m in stored] == ['Vraag blijft actief', 'antwoord blijft behouden']
        panel.close()
