from pathlib import Path

from PySide6.QtCore import Qt, QSettings, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget
)

from ..i18n import tr
from ..media.markup import count_words
from ..themes import THEMES
from ..typography import typography_from_values


CONTENT_MAX_WIDTH = 1440
CARD_WIDTH = 210
CARD_HEIGHT = 400
COVER_WIDTH = 192
COVER_HEIGHT = 307
CARD_GAP = 24


class _CenteredMaxWidthHost(QWidget):
    """Centreer inhoud tot een maximum breedte zonder hem tot een derde te krimpen."""

    def __init__(self, content: QWidget, max_width: int = CONTENT_MAX_WIDTH, parent=None):
        super().__init__(parent)
        self.setObjectName('centeredMaxWidthHost')
        self._content = content
        self._max_width = max_width
        self._side_margin = 28
        content.setSizePolicy(QSizePolicy.Expanding, content.sizePolicy().verticalPolicy())

        row = QHBoxLayout(self)
        row.setContentsMargins(self._side_margin, 0, self._side_margin, 0)
        row.setSpacing(0)
        row.addWidget(content, 0, Qt.AlignHCenter)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        available = max(0, self.width() - 2 * self._side_margin)
        self._content.setFixedWidth(min(self._max_width, available))


def _centered_host(widget: QWidget, max_width: int = CONTENT_MAX_WIDTH) -> QWidget:
    """Plaats een inhoudsblok in een rustige, gecentreerde contentkolom."""
    return _CenteredMaxWidthHost(widget, max_width)


class BookCover(QWidget):
    """Boekomslag met foto als achtergrond en dynamische titel als echte UI-tekst."""

    def __init__(self, library, book, parent=None):
        super().__init__(parent)
        self.library = library
        self.book = book
        self.setFixedSize(COVER_WIDTH, COVER_HEIGHT)  # circa 1 : 1,6

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        target = self.rect()
        path = self.library.cover_path(self.book) or self.library.default_cover_path()
        if path and Path(path).exists():
            pix = QPixmap(str(path))
            if not pix.isNull():
                scaled = pix.scaled(target.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                painter.drawPixmap((target.width() - scaled.width()) // 2, (target.height() - scaled.height()) // 2, scaled)
            else:
                theme = THEMES.get(str(QSettings('QuietWriter', 'QuietWriter').value('theme', 'Helder')), THEMES['Helder'])
                painter.fillRect(target, QColor(theme['cover1']))
        else:
            theme = THEMES.get(str(QSettings('QuietWriter', 'QuietWriter').value('theme', 'Helder')), THEMES['Helder'])
            painter.fillRect(target, QColor(theme['cover1']))
            painter.fillRect(0, 0, target.width(), target.height() // 3, QColor(theme['cover2']))
            painter.fillRect(0, target.height() // 3, target.width(), target.height() // 3, QColor(theme['cover3']))

        # De titel blijft echte, dynamische tekst en maakt dus geen deel uit van de omslagafbeelding.
        band_h = 78
        painter.fillRect(0, target.height() - band_h, target.width(), band_h, QColor(0, 0, 0, 118))
        painter.setPen(QColor('white'))
        font = typography_from_values(QSettings('QuietWriter', 'QuietWriter').value('editor_font', 'Merriweather'), 11).body_font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            self.rect().adjusted(12, target.height() - band_h + 10, -12, -10),
            Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
            self.book.title,
        )


class BookCard(QFrame):
    opened = Signal(object)

    def __init__(self, library, book, parent=None):
        super().__init__(parent)
        self.library = library
        self.book = book
        self.setObjectName('bookCard')
        self.setAttribute(Qt.WA_Hover, True)
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 24))
        self.setGraphicsEffect(shadow)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 10)
        lay.setSpacing(7)

        cover = BookCover(library, book)
        cover.setToolTip(book.title)

        words = 0
        for section in book.sections:
            for chapter in section.chapters:
                try:
                    words += count_words(library.read_chapter(book, chapter))
                except Exception:
                    pass

        info = QLabel(tr('bookshelf.words', '{count} woorden', count=f"{words:,}".replace(',', '.')))
        info.setObjectName('muted')
        info.setAlignment(Qt.AlignCenter)

        open_btn = QPushButton(tr('bookshelf.open', 'Openen'))
        open_btn.setObjectName('primaryButton')
        open_btn.clicked.connect(lambda: self.opened.emit(self.book))

        lay.addWidget(cover, 0, Qt.AlignHCenter)
        lay.addWidget(info)
        lay.addWidget(open_btn)


class StartPage(QWidget):
    open_book = Signal(object)
    new_book = Signal()
    import_book = Signal()

    def __init__(self, library):
        super().__init__()
        self.library = library

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # De donkere hero blijft schermbreed; de inhoud volgt dezelfde gecentreerde
        # contentas als de bediening en de boekenplank eronder.
        hero = QFrame()
        hero.setObjectName('bookshelfHero')
        hero_inner = QWidget()
        hero_inner.setObjectName('bookshelfHeroInner')
        hl = QVBoxLayout(hero_inner)
        hl.setContentsMargins(0, 34, 0, 30)
        title = QLabel(tr('bookshelf.title', 'Boekenplank'))
        title.setObjectName('heroTitle')
        subtitle = QLabel(tr('bookshelf.subtitle', 'Schrijf, bewerk en organiseer je boeken vanuit één rustige werkplek.'))
        subtitle.setObjectName('heroSubtitle')
        hl.addStretch()
        hl.addWidget(title)
        hl.addWidget(subtitle)
        hl.addStretch()
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(0, 0, 0, 0)
        hero_layout.setSpacing(0)
        hero_layout.addWidget(_centered_host(hero_inner))
        outer.addWidget(hero)

        controls_widget = QWidget()
        controls = QHBoxLayout(controls_widget)
        controls.setContentsMargins(0, 16, 0, 8)
        controls.setSpacing(12)

        self.count = QLabel(tr('bookshelf.count.zero', '0 boeken'))
        self.count.setObjectName('sectionTitle')

        self.sorting = QComboBox()
        for key in ('recent', 'title_az', 'title_za', 'words'):
            self.sorting.addItem(tr(f'bookshelf.sort.{key}', {
                'recent': 'Laatst gebruikt',
                'title_az': 'Titel A–Z',
                'title_za': 'Titel Z–A',
                'words': 'Aantal woorden',
            }[key]), key)
        self.sorting.setToolTip(tr('bookshelf.sort.tip', 'Sorteer de boekenplank'))
        self.sorting.currentIndexChanged.connect(self.refresh)

        self.search = QLineEdit()
        self.search.setPlaceholderText(tr('bookshelf.search.placeholder', 'Zoek op titel, tag of beschrijving…'))
        self.search.setMinimumWidth(280)
        self.search.setMaximumWidth(390)
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)

        controls.addWidget(self.count)
        controls.addStretch(1)
        controls.addWidget(self.sorting)
        controls.addWidget(self.search)
        outer.addWidget(_centered_host(controls_widget))

        self.no_results = QLabel(tr('bookshelf.no_results', 'Geen boeken gevonden.'))
        self.no_results.setObjectName('muted')
        self.no_results.setAlignment(Qt.AlignCenter)
        self.no_results.hide()
        outer.addWidget(self.no_results)

        scroll = QScrollArea()
        scroll.setObjectName('bookshelfScroll')
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.cards_host = QWidget()
        self.cards_host.setObjectName('bookshelfCardsHost')
        self.cards_host.setMaximumWidth(CONTENT_MAX_WIDTH)
        self.grid = QGridLayout(self.cards_host)
        self.grid.setContentsMargins(28, 22, 28, 42)
        self.grid.setHorizontalSpacing(CARD_GAP)
        self.grid.setVerticalSpacing(30)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        scroll.setWidget(self.cards_host)
        outer.addWidget(scroll, 1)

        self._cards = []
        self.refresh()

    def refresh(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        books = self.library.list_books()
        total = len(books)

        def word_count(book):
            total_words = 0
            for section in book.sections:
                for chapter in section.chapters:
                    try:
                        total_words += count_words(self.library.read_chapter(book, chapter))
                    except Exception:
                        pass
            return total_words

        order = self.sorting.currentData() if hasattr(self, 'sorting') else 'recent'
        if order == 'title_az':
            books.sort(key=lambda b: b.title.casefold())
        elif order == 'title_za':
            books.sort(key=lambda b: b.title.casefold(), reverse=True)
        elif order == 'words':
            books.sort(key=word_count, reverse=True)
        else:
            books.sort(key=self.library.book_activity, reverse=True)

        query = self.search.text().strip().casefold() if hasattr(self, 'search') else ''
        if query:
            def searchable(book):
                md = book.metadata or {}
                return ' '.join([
                    book.title,
                    str(md.get('slug', '')),
                    str(md.get('description', '')),
                    str(md.get('meta', '')),
                    str(md.get('intro', '')),
                    str(md.get('tags', '')),
                    str(md.get('author', '')),
                ]).casefold()
            books = [b for b in books if query in searchable(b)]

        if query:
            shown = len(books)
            if total == 1:
                self.count.setText(tr('bookshelf.count.filtered.one', '{shown} van {total} boek', shown=shown, total=total))
            else:
                self.count.setText(tr('bookshelf.count.filtered.many', '{shown} van {total} boeken', shown=shown, total=total))
        else:
            if total == 1:
                self.count.setText(tr('bookshelf.count.one', '{count} boek', count=total))
            else:
                self.count.setText(tr('bookshelf.count.many', '{count} boeken', count=total))
        self.no_results.setVisible(bool(query) and not books)

        create = QFrame()
        create.setObjectName('newBookCard')
        create.setAttribute(Qt.WA_Hover, True)
        create.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        create_shadow = QGraphicsDropShadowEffect(create)
        create_shadow.setBlurRadius(14)
        create_shadow.setOffset(0, 4)
        create_shadow.setColor(QColor(0, 0, 0, 20))
        create.setGraphicsEffect(create_shadow)

        cl = QVBoxLayout(create)
        cl.setContentsMargins(18, 28, 18, 22)
        cl.setSpacing(8)
        plus = QLabel('+')
        plus.setObjectName('newBookPlus')
        plus.setAlignment(Qt.AlignCenter)
        text = QLabel(tr('bookshelf.new_book', 'Nieuw boek'))
        text.setObjectName('sectionTitle')
        text.setAlignment(Qt.AlignCenter)
        btn = QPushButton(tr('bookshelf.create', 'Aanmaken'))
        btn.setObjectName('primaryButton')
        btn.clicked.connect(self.new_book.emit)
        imp = QPushButton(tr('bookshelf.import', 'Importeren…'))
        imp.setObjectName('secondaryButton')
        imp.clicked.connect(self.import_book.emit)
        cl.addStretch()
        cl.addWidget(plus)
        cl.addWidget(text)
        cl.addStretch()
        cl.addWidget(btn)
        cl.addWidget(imp)

        self._cards = [create]
        for book in books:
            card = BookCard(self.library, book)
            card.opened.connect(self.open_book.emit)
            self._cards.append(card)
        self._reflow_cards()

    def _reflow_cards(self):
        if not hasattr(self, '_cards'):
            return
        while self.grid.count():
            self.grid.takeAt(0)

        margins = self.grid.contentsMargins()
        available = max(220, self.cards_host.width() - margins.left() - margins.right())
        columns = max(1, int((available + CARD_GAP) // (CARD_WIDTH + CARD_GAP)))
        for i, card in enumerate(self._cards):
            self.grid.addWidget(card, i // columns, i % columns)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self._reflow_cards)
