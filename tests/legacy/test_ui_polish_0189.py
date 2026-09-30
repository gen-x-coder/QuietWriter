from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _source(relative):
    return (ROOT / relative).read_text(encoding='utf-8')


def test_drag_paint_uses_single_viewport_painter_and_plain_drop_geometry():
    source = _source('quietwriter/ui/manuscript_tree.py')
    paint = source[source.index('    def paintEvent'): ]
    assert paint.count('QPainter(self.viewport())') == 1
    assert 'if not painter.isActive():' in paint
    assert 'painter.end()' in paint
    assert 'self._drop_line_y' in paint
    assert 'self._drop_item' not in source


def test_native_drag_does_not_retain_tree_item_wrappers():
    source = _source('quietwriter/ui/manuscript_tree.py')
    start_drag = source[source.index('    def startDrag'):source.index('    def dragEnterEvent')]
    move = source[source.index('    def dragMoveEvent'):source.index('    def dragLeaveEvent')]
    drop = source[source.index('    def dropEvent'):source.index('    def paintEvent')]
    assert 'source_title = self._drag_item.text(0)' in start_drag
    assert start_drag.index('self._drag_item = None') < start_drag.index('drag.exec(Qt.MoveAction)')
    assert 'self._drop_target = (str(tdata[0]), str(tdata[1]))' in move
    assert 'self._drop_line_y = int(' in move
    assert 'target_data = self._drop_target' in drop


def test_selection_overlay_is_not_custom_painted_during_native_drag():
    source = _source('quietwriter/ui/manuscript_tree.py')
    paint = source[source.index('    def paintEvent'): ]
    assert 'if not self._dragging:' in paint
    assert 'drop_y = self._drop_line_y' in paint
