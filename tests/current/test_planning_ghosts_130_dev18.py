from pathlib import Path

from quietwriter.chapter_context import build_chapter_context
from quietwriter.planning_models import Character, Scene


ROOT = Path(__file__).resolve().parents[2]


def test_ghost_context_keeps_saved_scene_order_and_skips_broken_characters():
    a = Character(name='Ada')
    b = Character(name='Bram')
    scenes = [
        Scene(chapter_id='c1', title='Eerste', synopsis='Begin', character_ids=[a.id, 'missing']),
        Scene(chapter_id='c1', title='Tweede', synopsis='Vervolg', character_ids=[b.id]),
        Scene(chapter_id='c2', title='Andere'),
    ]
    context = build_chapter_context('c1', scenes, [a, b])
    assert [s.title for s in context.scenes] == ['Eerste', 'Tweede']
    assert context.scenes[0].character_names == ('Ada',)
    assert context.character_names == ('Ada', 'Bram')


def test_ghost_implementation_is_presentation_only_by_construction():
    editor = (ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py').read_text(encoding='utf-8')
    page = (ROOT / 'quietwriter' / 'ui' / 'editor_page.py').read_text(encoding='utf-8')
    assert 'def _paint_planning_ghosts' in editor
    assert 'set_planning_ghosts' in editor
    assert 'painter.drawText' in editor
    assert 'context.scenes if context is not None else ()' in page
    # Planning hints are supplied separately; they are never appended to source.
    ghost_section = editor[editor.index('def set_planning_ghosts'):editor.index('def resizeEvent')]
    assert 'insertText(' not in ghost_section
    assert 'setPlainText(' not in ghost_section
