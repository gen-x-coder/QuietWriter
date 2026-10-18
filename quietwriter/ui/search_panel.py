
from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QFont, QFontMetrics, QPalette
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QStackedLayout, QStyle, QStyledItemDelegate, QVBoxLayout, QWidget
)
from ..i18n import tr
from .panel_help import PanelHelp

SNIPPET_BEFORE = 36
SNIPPET_AFTER = 90
HIGHLIGHT_ROLE = Qt.UserRole + 1
TITLE_ROLE = Qt.UserRole + 2
SNIPPET_ROLE = Qt.UserRole + 3


def search_snippet(text: str, start: int, end: int) -> tuple[str, int, int]:
    """Stukje tekst rond een treffer: (tekst, begin, eind van de treffer erin).

    Blijft binnen de alinea van de treffer, begint en eindigt op een
    woordgrens en zet '…' waar iets is weggelaten.
    """
    text = text or ''
    line_start = text.rfind('\n', 0, start) + 1
    line_end = text.find('\n', end)
    if line_end < 0:
        line_end = len(text)
    a = max(line_start, start - SNIPPET_BEFORE)
    if a > line_start:
        space = text.find(' ', a, start)
        a = space + 1 if space >= 0 else a
    b = min(line_end, end + SNIPPET_AFTER)
    if b < line_end:
        space = text.rfind(' ', end, b)
        b = space if space > end else b
    prefix = '…' if a > line_start else ''
    suffix = '…' if b < line_end else ''
    snippet = prefix + text[a:b] + suffix
    hl_start = len(prefix) + (start - a)
    return snippet, hl_start, hl_start + (end - start)


class SearchResultDelegate(QStyledItemDelegate):
    """Twee rustige regels: hoofdstuk (alleen bij een nieuw hoofdstuk) en het
    stukje tekst met de treffer vet. Nooit horizontaal scrollen."""

    PAD = 6

    def _fonts(self, option):
        base = QFont(option.font)
        title = QFont(base); title.setPointSizeF(max(7.5, base.pointSizeF() - 1.5))
        bold = QFont(base); bold.setBold(True)
        return base, title, bold

    def sizeHint(self, option, index):
        base, title, _ = self._fonts(option)
        height = QFontMetrics(base).height() + 2 * self.PAD
        if index.data(TITLE_ROLE):
            height += QFontMetrics(title).height() + 2
        return QSize(option.rect.width(), height)

    def paint(self, painter, option, index):
        painter.save()
        style = option.widget.style() if option.widget else QApplication.style()
        style.drawPrimitive(QStyle.PE_PanelItemViewItem, option, painter, option.widget)
        base, title_font, bold = self._fonts(option)
        selected = bool(option.state & QStyle.State_Selected)
        palette = option.palette
        text_color = palette.color(QPalette.HighlightedText if selected else QPalette.Text)
        muted = palette.color(QPalette.PlaceholderText)
        rect = option.rect.adjusted(self.PAD, self.PAD, -self.PAD, -self.PAD)
        y = rect.top()
        title = index.data(TITLE_ROLE)
        if title:
            painter.setFont(title_font)
            painter.setPen(text_color if selected else muted)
            metrics = QFontMetrics(title_font)
            painter.drawText(QRect(rect.left(), y, rect.width(), metrics.height()), Qt.AlignLeft | Qt.AlignVCenter,
                             metrics.elidedText(str(title), Qt.ElideRight, rect.width()))
            y += metrics.height() + 2
        snippet = str(index.data(SNIPPET_ROLE) or '')
        hl = index.data(HIGHLIGHT_ROLE) or (0, 0)
        start, end = max(0, int(hl[0])), max(0, int(hl[1]))
        parts = ((snippet[:start], base), (snippet[start:end], bold), (snippet[end:], base))
        x = rect.left()
        height = QFontMetrics(base).height()
        painter.setPen(text_color)
        for number, (part, font) in enumerate(parts):
            if not part:
                continue
            metrics = QFontMetrics(font)
            room = rect.right() - x
            if room <= 8:
                break
            shown = metrics.elidedText(part, Qt.ElideRight, room) if number == 2 else part
            width = metrics.horizontalAdvance(shown)
            if width > room:
                shown = metrics.elidedText(part, Qt.ElideRight, room)
                width = metrics.horizontalAdvance(shown)
            painter.setFont(font)
            painter.drawText(QRect(x, y, width + 1, height), Qt.AlignLeft | Qt.AlignVCenter, shown)
            x += width
        painter.restore()

class SearchPanel(QWidget):
    open_match = Signal(object)
    request_next = Signal()
    request_replace = Signal()
    request_replace_all = Signal()

    def __init__(self, settings=None):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(18,18,18,18); lay.setSpacing(10)
        self.panel_help = PanelHelp(settings, 'search', tr('search.title', 'Zoeken en vervangen'), tr('panel_help.search', 'Zoek in dit hoofdstuk, deze sectie of het hele boek. Vervang treffers één voor één, of allemaal tegelijk met Alles vervangen.'))
        self.scope = QComboBox(); self.scope.addItem(tr('search.scope.chapter', 'Huidig hoofdstuk'), 'chapter'); self.scope.addItem(tr('search.scope.section', 'Huidige sectie'), 'section'); self.scope.addItem(tr('search.scope.book', 'Hele boek'), 'book')
        self.query = QLineEdit(); self.query.setPlaceholderText(tr('search.placeholder', 'Zoeken…')); self.query.setClearButtonEnabled(True)
        self.replace = QLineEdit(); self.replace.setPlaceholderText(tr('search.replace_placeholder', 'Vervangen door…')); self.replace.setClearButtonEnabled(True)
        options = QHBoxLayout()
        self.case_sensitive = QCheckBox(tr('search.case_sensitive', 'Hoofdlettergevoelig'))
        self.whole_word = QCheckBox(tr('search.whole_word', 'Heel woord'))
        options.addWidget(self.case_sensitive); options.addWidget(self.whole_word); options.addStretch()
        self.summary = QLabel(''); self.summary.setObjectName('muted')
        self.empty = QLabel(tr('search.no_results', 'Geen resultaten gevonden.')); self.empty.setObjectName('searchEmptyResults'); self.empty.setAlignment(Qt.AlignCenter)
        self.results = QListWidget()
        self.results.setObjectName('searchResults')
        self.results.setItemDelegate(SearchResultDelegate(self.results))
        self.results.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.results.setUniformItemSizes(False)
        self.result_area = QWidget()
        self.result_area.setObjectName('searchResultArea')
        self.result_stack = QStackedLayout(self.result_area)
        self.result_stack.setContentsMargins(0, 0, 0, 0)
        self.result_stack.addWidget(self.results)
        self.result_stack.addWidget(self.empty)
        self.result_stack.setCurrentWidget(self.results)
        # Mouse navigation is intentionally single-click: result rows are
        # navigation targets, not objects that need a separate selection step.
        # itemActivated remains for Enter/Return keyboard activation.
        self.results.itemClicked.connect(self._open_result_item)
        self.results.itemActivated.connect(self._open_result_item)
        buttons = QHBoxLayout()
        self.next_btn = QPushButton(tr('search.next','Volgende')); self.next_btn.clicked.connect(self.request_next.emit)
        self.replace_btn = QPushButton(tr('search.replace','Vervangen')); self.replace_btn.clicked.connect(self.request_replace.emit)
        self.replace_all_btn = QPushButton(tr('search.replace_all','Alles vervangen')); self.replace_all_btn.clicked.connect(self.request_replace_all.emit)
        buttons.addWidget(self.next_btn); buttons.addWidget(self.replace_btn); buttons.addWidget(self.replace_all_btn)
        lay.addWidget(self.panel_help); lay.addWidget(self.scope); lay.addWidget(self.query); lay.addLayout(options)
        lay.addWidget(self.summary); lay.addWidget(self.result_area, 1)
        lay.addWidget(QLabel(tr('search.replace_label', 'Vervangen door'))); lay.addWidget(self.replace); lay.addLayout(buttons)
        # Creation order differs from visual order because the replacement field
        # is constructed before the option row. Keep Tab/Shift+Tab predictable.
        tab_order = (
            self.scope, self.query, self.case_sensitive, self.whole_word,
            self.results, self.replace, self.next_btn, self.replace_btn,
            self.replace_all_btn,
        )
        for first, second in zip(tab_order, tab_order[1:], strict=False):
            QWidget.setTabOrder(first, second)


    def _open_result_item(self, item):
        if item is not None:
            self.open_match.emit(item.data(Qt.UserRole))

    def show_results(self, rows):
        self.results.clear()
        active = bool(self.query.text().strip())
        self.result_stack.setCurrentWidget(self.empty if active and not rows else self.results)
        self.summary.setText((tr('search.result.one', '{count} resultaat', count=len(rows)) if len(rows) == 1 else tr('search.result.many', '{count} resultaten', count=len(rows))) if active and rows else '')
        previous = None
        for row in rows:
            cid, title, snippet, start, length = row[:5]
            highlight = row[5] if len(row) > 5 else (0, 0)
            item = QListWidgetItem(f'{title}: {snippet}')   # ook voor schermlezers en zoeken in de lijst
            item.setToolTip(f'{title}\n{snippet}')
            item.setData(Qt.UserRole, (cid, start, length))
            item.setData(TITLE_ROLE, title if cid != previous else '')
            item.setData(SNIPPET_ROLE, snippet)
            item.setData(HIGHLIGHT_ROLE, highlight)
            previous = cid
            self.results.addItem(item)
