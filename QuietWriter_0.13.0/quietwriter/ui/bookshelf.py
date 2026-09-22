
from pathlib import Path
from PySide6.QtCore import Qt, QSettings, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget
)
from ..themes import THEMES
from ..typography import typography_from_values

class BookCover(QWidget):
    """Boekomslag met foto als achtergrond en dynamische titel als echte UI-tekst."""
    def __init__(self, library, book, parent=None):
        super().__init__(parent)
        self.library = library
        self.book = book
        self.setFixedSize(184, 294)  # 1 : 1,6

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
                theme = THEMES.get(str(QSettings('QuietWriter','QuietWriter').value('theme','Helder')), THEMES['Helder']); painter.fillRect(target, QColor(theme['cover1']))
        else:
            theme = THEMES.get(str(QSettings('QuietWriter','QuietWriter').value('theme','Helder')), THEMES['Helder'])
            painter.fillRect(target, QColor(theme['cover1']))
            # Abstracte, rustige fallback. Kleuren volgen automatisch het actieve thema.
            painter.fillRect(0, 0, target.width(), target.height() // 3, QColor(theme['cover2']))
            painter.fillRect(0, target.height() // 3, target.width(), target.height() // 3, QColor(theme['cover3']))

        # De titel blijft echte, dynamische tekst en maakt dus geen deel uit van de omslagafbeelding.
        band_h = 78
        painter.fillRect(0, target.height() - band_h, target.width(), band_h, QColor(0, 0, 0, 118))
        painter.setPen(QColor('white'))
        font = typography_from_values(QSettings('QuietWriter','QuietWriter').value('editor_font','Merriweather'), 11).body_font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect().adjusted(12, target.height() - band_h + 10, -12, -10),
                         Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, self.book.title)

class BookCard(QFrame):
    opened = Signal(object)

    def __init__(self, library, book, parent=None):
        super().__init__(parent)
        self.library = library
        self.book = book
        self.setObjectName('bookCard')
        self.setAttribute(Qt.WA_Hover, True)
        self.setFixedSize(202, 390)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18); shadow.setOffset(0, 5); shadow.setColor(QColor(0, 0, 0, 28))
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
                    words += len(library.read_chapter(book, chapter).split())
                except Exception:
                    pass
        info = QLabel(f"{words:,}".replace(',', '.') + ' woorden')
        info.setObjectName('muted')
        info.setAlignment(Qt.AlignCenter)
        open_btn = QPushButton('Openen'); open_btn.setObjectName('primaryButton')
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

        hero = QFrame(); hero.setObjectName('bookshelfHero')
        hl = QVBoxLayout(hero); hl.setContentsMargins(42, 34, 42, 30)
        title = QLabel('Boekenplank'); title.setObjectName('heroTitle')
        subtitle = QLabel('Schrijf, bewerk en organiseer je boeken vanuit één rustige werkplek.')
        subtitle.setObjectName('heroSubtitle')
        hl.addStretch(); hl.addWidget(title); hl.addWidget(subtitle); hl.addStretch()
        outer.addWidget(hero)

        controls = QHBoxLayout(); controls.setContentsMargins(42, 16, 42, 8)
        self.count = QLabel('0 boeken'); self.count.setObjectName('sectionTitle')
        self.sorting = QComboBox(); self.sorting.addItems(['Laatst gebruikt', 'Titel A–Z', 'Titel Z–A', 'Aantal woorden'])
        self.sorting.setToolTip('Sorteer de boekenplank')
        self.sorting.currentTextChanged.connect(self.refresh)
        self.search = QLineEdit(); self.search.setPlaceholderText('Zoek op titel, tag of beschrijving…'); self.search.setMaximumWidth(390)
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)
        controls.addWidget(self.count); controls.addStretch(); controls.addWidget(self.sorting); controls.addWidget(self.search)
        outer.addLayout(controls)
        self.no_results = QLabel('Geen boeken gevonden.')
        self.no_results.setObjectName('muted')
        self.no_results.setAlignment(Qt.AlignCenter)
        self.no_results.hide()
        outer.addWidget(self.no_results)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        self.cards_host = QWidget(); self.grid = QGridLayout(self.cards_host)
        self.grid.setContentsMargins(28, 22, 28, 42); self.grid.setHorizontalSpacing(22); self.grid.setVerticalSpacing(26)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        scroll.setWidget(self.cards_host); outer.addWidget(scroll, 1)
        self._cards = []
        self.refresh()

    def refresh(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        books = self.library.list_books()
        total = len(books)
        def word_count(book):
            total_words = 0
            for section in book.sections:
                for chapter in section.chapters:
                    try:
                        total_words += len(self.library.read_chapter(book, chapter).split())
                    except Exception:
                        pass
            return total_words
        order = self.sorting.currentText() if hasattr(self, 'sorting') else 'Laatst gebruikt'
        if order == 'Titel A–Z':
            books.sort(key=lambda b: b.title.casefold())
        elif order == 'Titel Z–A':
            books.sort(key=lambda b: b.title.casefold(), reverse=True)
        elif order == 'Aantal woorden':
            books.sort(key=word_count, reverse=True)
        else:
            books.sort(key=self.library.book_activity, reverse=True)
        query = self.search.text().strip().casefold() if hasattr(self, 'search') else ''
        if query:
            def searchable(book):
                md = book.metadata or {}
                return ' '.join([
                    book.title,
                    str(md.get('slug','')),
                    str(md.get('description','')),
                    str(md.get('meta','')),
                    str(md.get('intro','')),
                    str(md.get('tags','')),
                    str(md.get('author','')),
                ]).casefold()
            books = [b for b in books if query in searchable(b)]
        if query:
            shown = len(books)
            self.count.setText(f'{shown} van {total} boek' if total == 1 else f'{shown} van {total} boeken')
        else:
            self.count.setText(f'{total} boek' if total == 1 else f'{total} boeken')
        self.no_results.setVisible(bool(query) and not books)

        create = QFrame(); create.setObjectName('newBookCard'); create.setAttribute(Qt.WA_Hover, True); create.setFixedSize(202, 390)
        create_shadow = QGraphicsDropShadowEffect(create); create_shadow.setBlurRadius(16); create_shadow.setOffset(0,4); create_shadow.setColor(QColor(0,0,0,22)); create.setGraphicsEffect(create_shadow)
        cl = QVBoxLayout(create); cl.setContentsMargins(18, 28, 18, 22)
        plus = QLabel('+'); plus.setObjectName('newBookPlus'); plus.setAlignment(Qt.AlignCenter)
        text = QLabel('Nieuw boek'); text.setObjectName('sectionTitle'); text.setAlignment(Qt.AlignCenter)
        btn = QPushButton('Aanmaken'); btn.setObjectName('primaryButton'); btn.clicked.connect(self.new_book.emit)
        imp = QPushButton('Importeren…'); imp.setObjectName('secondaryButton'); imp.clicked.connect(self.import_book.emit)
        cl.addStretch(); cl.addWidget(plus); cl.addWidget(text); cl.addStretch(); cl.addWidget(btn); cl.addWidget(imp)
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
        available = max(220, self.cards_host.width() - self.grid.contentsMargins().left() - self.grid.contentsMargins().right())
        card_w = 202
        spacing = self.grid.horizontalSpacing()
        columns = max(1, int((available + spacing) // (card_w + spacing)))
        for i, card in enumerate(self._cards):
            self.grid.addWidget(card, i // columns, i % columns)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self._reflow_cards)
