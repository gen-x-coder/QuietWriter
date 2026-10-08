import pytest

pytest.importorskip('PySide6')

from PySide6.QtWidgets import QApplication

from quietwriter.chapter_context import ChapterSceneContext
from quietwriter.ui.manuscript_editor import ManuscriptEditor


@pytest.fixture(scope='module')
def app():
    instance = QApplication.instance() or QApplication([])
    return instance


def _scene():
    return ChapterSceneContext(
        id='s1', title='Ontmoeting', synopsis='Ada vindt de sleutel.', status='idee',
        location='Station', character_names=('Ada',), goal='De sleutel vinden',
        conflict='De trein vertrekt', outcome='Ze stapt in', notes='Niet tonen',
    )


def test_ghost_text_never_enters_document_and_follows_empty_state(app):
    editor = ManuscriptEditor()
    editor.setPlainText('')
    editor.set_planning_ghosts([_scene()], enabled=True)
    assert editor.planning_ghosts_visible()
    assert editor.source_text() == ''
    assert editor.document().toPlainText() == ''
    assert not editor.find('Ontmoeting')

    editor.setPlainText('echte tekst')
    assert not editor.planning_ghosts_visible()
    assert editor.source_text() == 'echte tekst'

    editor.setPlainText('')
    assert editor.planning_ghosts_visible()


def test_ghosts_can_be_disabled_without_touching_source(app):
    editor = ManuscriptEditor()
    editor.setPlainText('')
    editor.set_planning_ghosts([_scene()], enabled=False)
    assert not editor.planning_ghosts_visible()
    assert editor.source_text() == ''
