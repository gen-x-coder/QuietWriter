"""1.7.0: leesbare zoekresultaten (stukje rond de treffer, treffer vet, hoofdstuk
alleen bij een nieuw hoofdstuk, nooit horizontaal scrollen)."""
from __future__ import annotations

import os

import pytest

from quietwriter.ui.search_panel import search_snippet


def test_snippet_stays_in_paragraph_and_starts_on_a_word():
    text = 'Eerste alinea.\n' + 'Het regende al de hele dag en de wind blies hard toen Anna eindelijk naar huis liep en niemand haar zag of hoorde onderweg naar de oude brug over de rivier die al jaren half ingestort lag in de mist.' + '\nVolgende.'
    start = text.index('Anna'); end = start + 4
    snippet, a, b = search_snippet(text, start, end)
    assert snippet[a:b] == 'Anna'
    assert 'Eerste' not in snippet and 'Volgende' not in snippet
    assert snippet.startswith('…') and not snippet.startswith('… ')
    assert snippet.endswith('…')


def test_short_paragraph_is_shown_whole():
    text = 'Bram wachtte. Anna kwam niet.'
    snippet, a, b = search_snippet(text, text.index('Anna'), text.index('Anna') + 4)
    assert snippet == text and snippet[a:b] == 'Anna'


@pytest.mark.qt
def test_panel_shows_title_only_for_a_new_chapter():
    pytest.importorskip('PySide6')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    from quietwriter.ui.search_panel import HIGHLIGHT_ROLE, SNIPPET_ROLE, TITLE_ROLE, SearchPanel
    app = QApplication.instance() or QApplication([])
    panel = SearchPanel()
    panel.query.setText('Anna')
    panel.show_results([('c1', 'Een', 'Anna a', 0, 4, (0, 4)), ('c1', 'Een', 'b Anna', 9, 4, (2, 6)),
                        ('c2', 'Twee', 'Anna c', 0, 4)])
    items = [panel.results.item(i) for i in range(panel.results.count())]
    assert [i.data(TITLE_ROLE) for i in items] == ['Een', '', 'Twee']
    assert items[1].data(HIGHLIGHT_ROLE) == (2, 6) and items[2].data(HIGHLIGHT_ROLE) == (0, 0)
    assert items[0].data(Qt.UserRole) == ('c1', 0, 4) and items[0].data(SNIPPET_ROLE) == 'Anna a'
    assert panel.results.horizontalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
    panel.results.resize(300, 300); panel.results.grab()   # tekenen mag niet falen
    assert app is not None
