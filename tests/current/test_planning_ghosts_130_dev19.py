from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ghost_location_and_characters_are_built_as_separate_lines():
    editor = (ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py').read_text(encoding='utf-8')
    section = editor[editor.index('def _ghost_detail_lines'):editor.index('def _paint_planning_ghosts')]
    assert "lines.append(tr('planning.ghost.location'" in section
    assert "lines.append(tr('planning.ghost.characters'" in section
    assert "lines.append(' · '.join(meta))" not in section


def test_ghost_painter_reserves_footer_for_unshown_scenes():
    editor = (ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py').read_text(encoding='utf-8')
    section = editor[editor.index('def _paint_planning_ghosts'):editor.index('def resizeEvent')]
    assert 'scene_bottom = bottom - 24' in section
    assert 'remaining = len(scenes) - shown' in section
    assert "planning.ghost.more_scenes" in section
    assert 'in Planning' in section
