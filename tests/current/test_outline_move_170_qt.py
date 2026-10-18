"""1.7.0-dev15: Planning bijschaven: scènes slepen en verplaatsen, groepen inklappen."""
import os

import pytest
pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QEvent, QCoreApplication, QMimeData, QPointF, Qt
from PySide6.QtGui import QDropEvent
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from quietwriter.planning_models import Scene
from quietwriter.planning_storage import PlanningStore
from quietwriter.storage import Library
from quietwriter.ui.planning.outline_page import SCENE_MIME, SceneCard, SceneGroup


def _settle(app):
    for _ in range(3):
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        app.processEvents()


@pytest.fixture
def env(tmp_path):
    app = QApplication.instance() or QApplication([])
    from quietwriter.ui.main_window import MainWindow
    lib = Library(tmp_path / 'ws')
    book = lib.create_book('Outline')
    lib.add_chapter(book, book.sections[0], 'Twee')
    book = lib.load_book(book.path)
    ch1, ch2 = [c for s in book.sections for c in s.chapters]
    scenes = [Scene(title='A', chapter_id=ch1.id), Scene(title='B', chapter_id=ch1.id),
              Scene(title='C', chapter_id=ch2.id), Scene(title='Los', chapter_id=None)]
    PlanningStore(lib).save_scenes(book, scenes)
    settings = QSettings(str(tmp_path / 's.ini'), QSettings.IniFormat)
    settings.setValue('workspace', str(lib.root))
    window = MainWindow(settings, lib, [])
    window.resize(1200, 900); window.show(); window.open_book(book); window.show_planning()
    outline = window.planning_page.outline_page
    window.planning_page.show_section(1); outline.load(); _settle(app)
    yield app, window, outline, lib, book, (ch1, ch2)
    window.close()


def _order(lib, book):
    return [(s.title, s.chapter_id) for s in PlanningStore(lib).load_scenes(book)]


def test_drop_reorders_within_and_between_chapters(env):
    app, _w, outline, lib, book, (ch1, ch2) = env
    ids = {s.title: s.id for s in outline.scenes}
    outline.drop_scene(ids['B'], ch1.id, ids['A'])            # B vóór A
    assert _order(lib, book)[:2] == [('B', ch1.id), ('A', ch1.id)]
    outline.drop_scene(ids['A'], ch2.id, ids['C'])            # A naar hoofdstuk 2, vóór C
    assert [t for t, cid in _order(lib, book) if cid == ch2.id] == ['A', 'C']
    outline.drop_scene(ids['Los'], ch1.id, None)              # los idee achteraan hoofdstuk 1
    assert [t for t, cid in _order(lib, book) if cid == ch1.id] == ['B', 'Los']
    outline.move_scene_to(ids['C'], None)                     # menu: naar Losse ideeën
    assert ('C', None) in _order(lib, book)


def test_drop_on_itself_or_orphan_group_changes_nothing(env):
    _app, _w, outline, lib, book, (ch1, _ch2) = env
    before = _order(lib, book)
    sid = outline.scenes[0].id
    outline.drop_scene(sid, ch1.id, sid)
    outline.drop_scene(sid, '__orphaned__', None)
    outline.drop_scene(sid, ch1.id, outline.scenes[1].id)     # al op die plek
    assert _order(lib, book) == before


def test_drag_and_drop_event_goes_through_the_group(env):
    app, _w, outline, lib, book, (_ch1, ch2) = env
    groups = [g for g in outline.findChildren(SceneGroup) if g.isVisible()]
    target = next(g for g in groups if g.chapter_id == ch2.id)
    card_c = next(c for c in target.findChildren(SceneCard))
    a_id = next(s.id for s in outline.scenes if s.title == 'A')
    mime = QMimeData(); mime.setData(SCENE_MIME, a_id.encode())
    point = QPointF(card_c.geometry().center().x(), card_c.geometry().top() + 2)
    event = QDropEvent(point, Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier)
    target.dropEvent(event)
    _settle(app)
    assert [t for t, cid in _order(lib, book) if cid == ch2.id] == ['A', 'C']


def test_collapsed_groups_are_remembered_per_book_and_toggle_all(env):
    app, window, outline, _lib, book, (ch1, _ch2) = env
    outline.toggle_group(str(ch1.id))
    assert str(ch1.id) in outline._stored_collapsed(book.id)
    outline._loaded_book_id = None                 # zoals bij opnieuw openen
    outline.load(); _settle(app)
    assert str(ch1.id) in outline._collapsed_groups
    outline.toggle_all(); _settle(app)
    assert outline.toggle_all_button.text() == 'Alles uitklappen'
    assert not [c for c in outline.findChildren(SceneCard) if c.isVisible()]
    outline.toggle_all(); _settle(app)
    assert outline.toggle_all_button.text() == 'Alles inklappen'
    assert outline._stored_collapsed(book.id) == set()
    assert window.settings.value(f'planning/outline_collapsed/{book.id}') == '[]'


def test_drop_into_collapsed_group_opens_it(env):
    app, _w, outline, lib, book, (_ch1, ch2) = env
    outline.toggle_group(str(ch2.id))
    a_id = next(s.id for s in outline.scenes if s.title == 'A')
    outline.drop_scene(a_id, ch2.id, None)
    assert str(ch2.id) not in outline._collapsed_groups
