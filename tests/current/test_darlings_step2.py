from quietwriter.manuscript_markup import source_selection_as_markdown
from quietwriter.ui.rail_model import RailState, build_rail_view


def _selected(source, visible, occurrence=0):
    starts = []
    pos = -1
    for _ in range(occurrence + 1):
        pos = source.index(visible, pos + 1)
        starts.append(pos)
    start = starts[-1]
    end = start + len(visible)
    selected, _a, _b = source_selection_as_markdown(source, start, end)
    return selected


def test_copy_range_keeps_boundary_inline_markdown():
    assert _selected('Voor **vet** na', 'vet') == '**vet**'
    assert _selected('Voor *cursief* na', 'cursief') == '*cursief*'
    assert _selected('Voor ~~weg~~ na', 'weg') == '~~weg~~'
    assert _selected('Voor `code` na', 'code') == '`code`'
    assert _selected('Voor <u>onder</u> na', 'onder') == '<u>onder</u>'


def test_copy_range_keeps_nested_bold_italic_markdown():
    assert _selected('Voor ***beide*** na', 'beide') == '***beide***'


def test_partial_inline_selection_is_balanced_instead_of_dangling():
    source = 'Hier staat **vet woord** en *schuin woord* klaar.'

    # Wholly inside a formatted span: synthesize both markers.
    assert _selected(source, 'woord', 0) == '**woord**'
    assert _selected(source, 'woord', 1) == '*woord*'

    # Starts inside bold and crosses its original closing marker.
    start = source.index('woord')
    end = source.index(' en') + len(' en')
    selected, _a, _b = source_selection_as_markdown(source, start, end)
    assert selected == '**woord** en'

    # Starts before bold and ends inside it.
    start = source.index('staat')
    end = source.index('vet') + len('vet')
    selected, _a, _b = source_selection_as_markdown(source, start, end)
    assert selected == 'staat **vet**'


def test_internal_markup_is_already_preserved():
    source = 'begin normaal **vet** einde'
    start = source.index('normaal')
    end = source.index(' einde')
    selected, _a, _b = source_selection_as_markdown(source, start, end)
    assert selected == 'normaal **vet**'


def test_darlings_is_workspace_level_navigation():
    assert 'darlings' in build_rail_view(RailState(False, False, False)).visible_items
    assert 'darlings' in build_rail_view(RailState(True, True, True)).visible_items
