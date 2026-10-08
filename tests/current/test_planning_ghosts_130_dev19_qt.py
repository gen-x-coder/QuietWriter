import pytest

pytest.importorskip('PySide6')

from PySide6.QtWidgets import QApplication

from quietwriter.chapter_context import ChapterSceneContext
from quietwriter.ui.manuscript_editor import ManuscriptEditor


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def test_ghost_detail_lines_keep_location_and_characters_separate(app):
    scene = ChapterSceneContext(
        id='s1', title='Scène', synopsis='Synopsis', status='idee',
        location='Delft', character_names=('Arie', 'Eveline'),
        goal='Doel', conflict='Conflict', outcome='Uitkomst', notes='',
    )
    lines = ManuscriptEditor._ghost_detail_lines(scene)
    assert lines[:3] == ['Status: ○ Idee', 'Locatie: Delft', 'Personages: Arie, Eveline']
