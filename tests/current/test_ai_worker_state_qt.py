import os
import threading
import tempfile
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

    def stream_chat(self, model, messages, **options):
        self.release.wait(5)
        yield StreamChunk(content='laat antwoord')

    def cancel_active(self):
        # Deliberately does not release the simulated network request. This
        # recreates the provider that does not honour cancellation immediately.
        pass


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _run_events(ms=120):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def test_late_cancel_from_book_a_cannot_mutate_book_b(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        book_a = SimpleNamespace(id='a', path=root / 'a')
        book_b = SimpleNamespace(id='b', path=root / 'b')
        book_a.path.mkdir(); book_b.path.mkdir()
        b_store = ConversationStore(book_b)
        b_rows = [ConversationStore.entry('user', 'Bericht van boek B.')]
        b_store.save(b_rows)

        main = SimpleNamespace(
            settings=FakeSettings(),
            library=SimpleNamespace(
                read_persona=lambda: 'persona',
                read_book_profile=lambda _book: '',
                read_book_memory=lambda _book: '',
            ),
        )
        _active = {'book': None}
        main.active_book = lambda: _active['book']
        panel = AIPanel(main)
        _active['book'] = book_a
        panel.set_book(book_a)
        provider = BlockingProvider()
        context = SimpleNamespace(label='test', pieces=['Testcontext'], text='context')
        panel._continue_send(provider, 'model', 'Vraag uit boek A', context)

        _active['book'] = book_b
        panel.set_book(book_b)
        assert [m['content'] for m in panel.messages] == ['Bericht van boek B.']

        provider.release.set()
        _run_events()

        assert [m['content'] for m in panel.messages] == ['Bericht van boek B.']
        assert [m['content'] for m in b_store.load()] == ['Bericht van boek B.']
        panel.close()
