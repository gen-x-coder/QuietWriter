import hashlib
import json
from pathlib import Path

from PySide6.QtCore import Qt, QSettings, QStandardPaths, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QLineEdit,
    QGridLayout, QMenu, QMessageBox, QProgressBar, QPushButton, QScrollArea, QSizePolicy, QToolButton,
    QVBoxLayout, QWidget,
)

from ..i18n import tr
from ..manuscript_text import count_words
from ..themes import THEMES
from ..typography import typography_from_values


CONTENT_MAX_WIDTH = 1440
CARD_WIDTH = 210
CARD_HEIGHT = 452
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



class _WrappingCardHost(QWidget):
    """Plaats boekkaarten in rustige rijen zonder een horizontale scrollbar."""

    def __init__(self, cards, parent=None):
        super().__init__(parent)
        self._cards = list(cards)
        self._columns = 0
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(2, 2, 2, 8)
        self.grid.setHorizontalSpacing(CARD_GAP)
        self.grid.setVerticalSpacing(CARD_GAP)
        self.grid.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._reflow(force=True)

    def _column_count(self) -> int:
        usable = max(CARD_WIDTH, self.width() - 4)
        return max(1, (usable + CARD_GAP) // (CARD_WIDTH + CARD_GAP))

    def _reflow(self, *, force=False):
        columns = self._column_count()
        if not force and columns == self._columns:
            return
        self._columns = columns
        while self.grid.count():
            self.grid.takeAt(0)
        for index, card in enumerate(self._cards):
            row, column = divmod(index, columns)
            self.grid.addWidget(card, row, column, Qt.AlignLeft | Qt.AlignTop)
        rows = max(1, (len(self._cards) + columns - 1) // columns)
        margins = self.grid.contentsMargins()
        height = margins.top() + margins.bottom() + rows * CARD_HEIGHT + max(0, rows - 1) * CARD_GAP
        self.setFixedHeight(height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow()

def _centered_host(widget: QWidget, max_width: int = CONTENT_MAX_WIDTH) -> QWidget:
    return _CenteredMaxWidthHost(widget, max_width)


class _ClickableLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class EditableShelfTitle(QWidget):
    rename_requested = Signal(str)

    def __init__(self, name: str, *, private: bool = False, parent=None):
        super().__init__(parent)
        self._private = bool(private)
        self._name = name
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(7)

        self.label = _ClickableLabel()
        self.label.setObjectName('sectionTitle')
        self.label.setCursor(Qt.PointingHandCursor)
        self.label.setToolTip(tr('bookshelf.shelf.rename_tip', 'Klik om de planknaam te wijzigen'))
        self.label.clicked.connect(self.begin_edit)

        self.edit = QLineEdit(name)
        self.edit.setObjectName('shelfNameEdit')
        self.edit.hide()
        self.edit.returnPressed.connect(self.finish_edit)
        self.edit.editingFinished.connect(self.finish_edit)

        lay.addWidget(self.label)
        lay.addWidget(self.edit)
        lay.addStretch(1)
        self._update_label()

    def _update_label(self):
        suffix = '  🔒' if self._private else ''
        self.label.setText(f'{self._name}{suffix}')

    def begin_edit(self):
        self.edit.setText(self._name)
        self.label.hide()
        self.edit.show()
        self.edit.setFocus(Qt.MouseFocusReason)
        self.edit.selectAll()

    def finish_edit(self):
        if not self.edit.isVisible():
            return
        value = self.edit.text().strip()
        self.edit.hide()
        self.label.show()
        if value and value != self._name:
            self.rename_requested.emit(value)


class BookCover(QWidget):
    """Boekomslag met foto als achtergrond en dynamische titel als echte UI-tekst."""

    def __init__(self, library, book, settings=None, parent=None):
        super().__init__(parent)
        self.library = library
        self.book = book
        self.settings = settings or QSettings('QuietWriter', 'QuietWriter')
        self.setFixedSize(COVER_WIDTH, COVER_HEIGHT)

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
                theme = THEMES.get(str(self.settings.value('theme', 'Helder')), THEMES['Helder'])
                painter.fillRect(target, QColor(theme['cover1']))
        else:
            theme = THEMES.get(str(self.settings.value('theme', 'Helder')), THEMES['Helder'])
            painter.fillRect(target, QColor(theme['cover1']))
            painter.fillRect(0, 0, target.width(), target.height() // 3, QColor(theme['cover2']))
            painter.fillRect(0, target.height() // 3, target.width(), target.height() // 3, QColor(theme['cover3']))

        band_h = 78
        painter.fillRect(0, target.height() - band_h, target.width(), band_h, QColor(0, 0, 0, 118))
        painter.setPen(QColor('white'))
        font = typography_from_values(self.settings.value('editor_font', 'Merriweather'), 11).body_font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            self.rect().adjusted(12, target.height() - band_h + 10, -12, -10),
            Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
            self.book.title,
        )


class BookCard(QFrame):
    opened = Signal(object)
    move_requested = Signal(object, str)

    def __init__(self, library, book, shelves=(), current_shelf_id: str = '', words: int | None = None, settings=None, parent=None):
        super().__init__(parent)
        self.library = library
        self.book = book
        self.shelves = tuple(shelves)
        self.current_shelf_id = current_shelf_id
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

        cover = BookCover(library, book, settings=settings)
        cover.setToolTip(book.title)

        if words is None:
            words = 0
            for section in book.sections:
                for chapter in section.chapters:
                    try:
                        words += count_words(library.read_chapter(book, chapter))
                    except Exception:
                        pass

        goal = max(0, int((book.metadata or {}).get('writing_goal_words', 0) or 0))
        if goal > 0:
            info_text = tr(
                'bookshelf.words_goal', '{count} van {goal} woorden',
                count=f"{words:,}".replace(',', '.'), goal=f"{goal:,}".replace(',', '.')
            )
        else:
            info_text = tr('bookshelf.words', '{count} woorden', count=f"{words:,}".replace(',', '.'))
        info = QLabel(info_text)
        info.setObjectName('muted')
        info.setAlignment(Qt.AlignCenter)

        progress = None
        if goal > 0:
            progress = QProgressBar()
            progress.setObjectName('bookGoalProgress')
            progress.setRange(0, max(1, goal))
            progress.setValue(min(words, goal))
            progress.setTextVisible(False)
            progress.setFixedHeight(4)
            pct = min(100, round((words / goal) * 100)) if goal else 0
            progress.setToolTip(tr('bookshelf.goal_tip', '{percent}% · nog {remaining} woorden', percent=pct, remaining=f"{max(0, goal - words):,}".replace(',', '.')))

        open_btn = QPushButton(tr('bookshelf.open', 'Openen'))
        open_btn.setObjectName('primaryButton')
        open_btn.clicked.connect(lambda: self.opened.emit(self.book))

        actions_btn = QPushButton(tr('bookshelf.book.actions', 'Boekacties'))
        actions_btn.setObjectName('secondaryButton')
        actions_btn.setToolTip(tr('bookshelf.book.actions', 'Boekacties'))
        menu = QMenu(actions_btn)
        move_menu = menu.addMenu(tr('bookshelf.book.move_to', 'Verplaatsen naar'))
        for shelf in self.shelves:
            action = move_menu.addAction(shelf.name)
            action.setCheckable(True)
            action.setChecked(shelf.id == current_shelf_id)
            action.setEnabled(shelf.id != current_shelf_id)
            action.triggered.connect(lambda checked=False, sid=shelf.id: self.move_requested.emit(self.book, sid))
        actions_btn.setMenu(menu)

        lay.addWidget(cover, 0, Qt.AlignHCenter)
        if progress is not None:
            lay.addWidget(progress)
        lay.addWidget(info)
        lay.addWidget(open_btn)
        lay.addWidget(actions_btn)


class _NewBookCard(QFrame):
    new_book = Signal()
    import_book = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('newBookCard')
        self.setAttribute(Qt.WA_Hover, True)
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(14)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)

        cl = QVBoxLayout(self)
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


class ShelfSection(QFrame):
    rename_requested = Signal(str, str)
    privacy_requested = Signal(str, bool)
    delete_requested = Signal(str)
    book_opened = Signal(object)
    book_move_requested = Signal(object, str)
    new_book = Signal()
    import_book = Signal()

    def __init__(self, library, shelf, books, shelves, *, default_shelf_id: str, word_count, show_new_card=False, settings=None, parent=None):
        super().__init__(parent)
        self.shelf = shelf
        self.setObjectName('bookshelfShelf')
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 8, 0, 14)
        outer.setSpacing(10)

        header = QHBoxLayout()
        header.setContentsMargins(2, 0, 2, 0)
        title = EditableShelfTitle(shelf.name, private=shelf.private)
        title.rename_requested.connect(lambda name: self.rename_requested.emit(shelf.id, name))
        count_key = 'bookshelf.shelf.book_count_one' if len(books) == 1 else 'bookshelf.shelf.book_count'
        count_fallback = '{count} boek' if len(books) == 1 else '{count} boeken'
        count = QLabel(tr(count_key, count_fallback, count=len(books)))
        count.setObjectName('muted')
        menu_btn = QToolButton()
        menu_btn.setText(tr('bookshelf.actions.more', '⋯'))
        menu_btn.setToolTip(tr('bookshelf.shelf.actions', 'Plankacties'))
        menu_btn.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(menu_btn)
        private_action = menu.addAction(
            tr('bookshelf.shelf.make_public', 'Niet meer privé') if shelf.private
            else tr('bookshelf.shelf.make_private', 'Privé maken')
        )
        private_action.setEnabled(shelf.id != default_shelf_id)
        private_action.triggered.connect(lambda: self.privacy_requested.emit(shelf.id, not shelf.private))
        delete_action = menu.addAction(tr('bookshelf.shelf.delete', 'Plank verwijderen'))
        delete_action.setEnabled(shelf.id != default_shelf_id)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(shelf.id))
        menu_btn.setMenu(menu)
        header.addWidget(title, 1)
        header.addWidget(count)
        header.addWidget(menu_btn)
        outer.addLayout(header)

        cards = []
        if show_new_card:
            create = _NewBookCard()
            create.new_book.connect(self.new_book.emit)
            create.import_book.connect(self.import_book.emit)
            cards.append(create)
        for book in books:
            card = BookCard(library, book, shelves=shelves, current_shelf_id=shelf.id, words=word_count(book), settings=settings)
            card.opened.connect(self.book_opened.emit)
            card.move_requested.connect(self.book_move_requested.emit)
            cards.append(card)
        outer.addWidget(_WrappingCardHost(cards))


class StartPage(QWidget):
    open_book = Signal(object)
    new_book = Signal()
    import_book = Signal()
    demo_mode_changed = Signal(bool)

    def __init__(self, library, settings=None):
        super().__init__()
        self.library = library
        self._problem_signature = None
        self.settings = settings or QSettings('QuietWriter', 'QuietWriter')
        self._word_count_cache = self._load_word_count_cache()
        self._word_count_cache_dirty = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        hero = QFrame()
        hero.setObjectName('bookshelfHero')
        hero_inner = QWidget()
        hero_inner.setObjectName('bookshelfHeroInner')
        hl = QVBoxLayout(hero_inner)
        hl.setContentsMargins(0, 34, 0, 30)
        title = QLabel(tr('bookshelf.title', 'Boekenkast'))
        title.setObjectName('heroTitle')
        subtitle = QLabel(tr('bookshelf.subtitle', 'Schrijf, bewerk en organiseer je boeken vanuit één rustige werkplek.'))
        subtitle.setObjectName('heroSubtitle')
        hl.addStretch(); hl.addWidget(title); hl.addWidget(subtitle); hl.addStretch()
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(0, 0, 0, 0)
        hero_layout.addWidget(_centered_host(hero_inner))
        outer.addWidget(hero)

        controls_widget = QWidget()
        controls = QHBoxLayout(controls_widget)
        controls.setContentsMargins(0, 16, 0, 8)
        controls.setSpacing(12)
        self.count = QLabel(tr('bookshelf.count.zero', '0 boeken'))
        self.count.setObjectName('sectionTitle')
        add_shelf = QPushButton(tr('bookshelf.shelf.add', 'Nieuwe plank'))
        add_shelf.setObjectName('secondaryButton')
        add_shelf.clicked.connect(self._create_shelf)
        self.demo_toggle = QPushButton()
        self.demo_toggle.setObjectName('secondaryButton')
        self.demo_toggle.setCheckable(True)
        self.demo_toggle.setChecked(self.settings.value('bookshelf_demo_mode', False, bool))
        self.demo_toggle.setToolTip(tr('bookshelf.demo_mode_tip', 'Verbergt privéplanken en hun boeken in de Boekenkast, Bewaarplaats en Prullenbak. Geen beveiliging.'))
        self.demo_toggle.toggled.connect(self._set_demo_mode)
        self._update_demo_toggle()
        self.sorting = QComboBox()
        for key in ('recent', 'title_az', 'title_za', 'words'):
            self.sorting.addItem(tr(f'bookshelf.sort.{key}', {
                'recent': 'Laatst gebruikt', 'title_az': 'Titel A–Z',
                'title_za': 'Titel Z–A', 'words': 'Aantal woorden',
            }[key]), key)
        self.sorting.setToolTip(tr('bookshelf.sort.tip', 'Sorteer de boekenplank'))
        self.sorting.currentIndexChanged.connect(self.refresh)
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr('bookshelf.search.placeholder', 'Zoek op titel, tag of beschrijving…'))
        self.search.setMinimumWidth(280)
        self.search.setMaximumWidth(390)
        self.search.setClearButtonEnabled(True)
        self._search_refresh_timer = QTimer(self)
        self._search_refresh_timer.setSingleShot(True)
        self._search_refresh_timer.setInterval(200)
        self._search_refresh_timer.timeout.connect(self.refresh)
        self.search.textChanged.connect(self._schedule_search_refresh)
        controls.addWidget(self.count)
        controls.addWidget(add_shelf)
        controls.addWidget(self.demo_toggle)
        controls.addStretch(1)
        controls.addWidget(self.sorting)
        controls.addWidget(self.search)
        outer.addWidget(_centered_host(controls_widget))

        self.notice = QFrame()
        self.notice.setObjectName('bookshelfNotice')
        notice_lay = QHBoxLayout(self.notice)
        notice_lay.setContentsMargins(14, 8, 14, 8)
        self.notice_text = QLabel()
        self.notice_text.setWordWrap(True)
        self.notice_restore = QPushButton(tr('bookshelf.recovery.restore', 'Indeling herstellen'))
        self.notice_reset = QPushButton(tr('bookshelf.recovery.reset', 'Opnieuw beginnen'))
        self.notice_restore.clicked.connect(self._restore_shelves)
        self.notice_reset.clicked.connect(self._reset_shelves)
        notice_lay.addWidget(self.notice_text, 1)
        notice_lay.addWidget(self.notice_restore)
        notice_lay.addWidget(self.notice_reset)
        self.notice.hide()
        outer.addWidget(_centered_host(self.notice))

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
        self.shelves_host = QWidget()
        self.shelves_host.setObjectName('bookshelfCardsHost')
        self.shelves_host.setMaximumWidth(CONTENT_MAX_WIDTH)
        self.shelves_layout = QVBoxLayout(self.shelves_host)
        self.shelves_layout.setContentsMargins(28, 12, 28, 42)
        self.shelves_layout.setSpacing(18)
        self.shelves_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.shelves_host)
        outer.addWidget(scroll, 1)
        self.refresh()


    def _word_count_cache_path(self) -> Path:
        local_root = QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)
        base = Path(local_root) if local_root else (Path.home() / '.quietwriter')
        try:
            workspace = str(self.library.root.resolve())
        except OSError:
            workspace = str(self.library.root.absolute())
        workspace_hash = hashlib.sha256(workspace.encode('utf-8')).hexdigest()[:20]
        return base / 'cache' / f'bookshelf-word-counts-{workspace_hash}.json'

    def _load_word_count_cache(self) -> dict:
        path = self._word_count_cache_path()
        try:
            raw = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(raw, dict):
                return {}
            cache = {}
            for chapter_key, row in raw.items():
                valid_hash = (isinstance(chapter_key, str) and len(chapter_key) == 64
                              and all(char in '0123456789abcdef' for char in chapter_key))
                if (valid_hash and isinstance(row, list) and len(row) == 3
                        and all(isinstance(value, int) for value in row)):
                    cache[chapter_key] = tuple(row)
            return cache
        except (OSError, ValueError, TypeError):
            return {}

    def _save_word_count_cache(self) -> None:
        if not self._word_count_cache_dirty:
            return
        path = self._word_count_cache_path()
        tmp = path.with_suffix(path.suffix + '.tmp')
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = {key: list(value) for key, value in self._word_count_cache.items()}
            tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
            tmp.replace(path)
            self._word_count_cache_dirty = False
        except OSError:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass

    def demo_mode_enabled(self) -> bool:
        return bool(self.settings.value('bookshelf_demo_mode', False, bool))

    def _update_demo_toggle(self):
        enabled = bool(self.demo_toggle.isChecked())
        key = 'bookshelf.demo_mode.on' if enabled else 'bookshelf.demo_mode.off'
        fallback = 'Presentatiemodus: aan' if enabled else 'Presentatiemodus: uit'
        self.demo_toggle.setText(tr(key, fallback))
        self.demo_toggle.setAccessibleName(self.demo_toggle.text())

    def _set_demo_mode(self, enabled: bool):
        enabled = bool(enabled)
        self.settings.setValue('bookshelf_demo_mode', enabled)
        self._update_demo_toggle()
        self.refresh()
        self.demo_mode_changed.emit(enabled)


    def _schedule_search_refresh(self, _text=''):
        self._search_refresh_timer.start()

    def _chapter_word_count(self, book, chapter) -> int:
        path = Path(book.path) / chapter.file
        try:
            stat = path.stat()
            signature = (stat.st_mtime_ns, stat.st_size)
        except OSError:
            signature = None

        cache_key = hashlib.sha256(str(path).encode('utf-8')).hexdigest()
        cached = self._word_count_cache.get(cache_key)
        if signature is not None and cached is not None and cached[:2] == signature:
            return cached[2]

        try:
            words = count_words(self.library.read_chapter(book, chapter))
        except Exception:
            words = 0
        if signature is not None:
            self._word_count_cache[cache_key] = (signature[0], signature[1], words)
            self._word_count_cache_dirty = True
        return words

    def _show_error(self, message: str):
        QMessageBox.warning(self, tr('bookshelf.error.title', 'Boekenkast'), str(message))

    def _create_shelf(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, tr('bookshelf.shelf.add', 'Nieuwe plank'), tr('bookshelf.shelf.name', 'Naam van de plank'))
        if not ok or not name.strip():
            return
        try:
            self.library.shelves.create_shelf(name)
            self.refresh()
        except Exception as exc:
            self._show_error(exc)

    def _rename_shelf(self, shelf_id: str, name: str):
        try:
            self.library.shelves.rename_shelf(shelf_id, name)
            self.refresh()
        except Exception as exc:
            self._show_error(exc)

    def _set_private(self, shelf_id: str, private: bool):
        try:
            self.library.shelves.set_private(shelf_id, private)
            self.refresh()
        except Exception as exc:
            self._show_error(exc)

    def _confirm(self, title: str, text: str) -> bool:
        message = QMessageBox(self)
        message.setIcon(QMessageBox.Question)
        message.setWindowTitle(title)
        message.setText(text)
        message.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        message.setDefaultButton(QMessageBox.No)
        yes = message.button(QMessageBox.Yes)
        no = message.button(QMessageBox.No)
        if yes is not None:
            yes.setText(tr('common.yes', 'Ja'))
        if no is not None:
            no.setText(tr('common.no', 'Nee'))
        return message.exec() == QMessageBox.Yes

    def _delete_shelf(self, shelf_id: str):
        loaded = self.library.shelves.load()
        shelf = loaded.state.shelf(shelf_id)
        if shelf is None:
            return
        if not self._confirm(
            tr('bookshelf.shelf.delete', 'Plank verwijderen'),
            tr('bookshelf.shelf.delete_confirm', 'Plank “{name}” verwijderen? Boeken op deze plank gaan terug naar de standaardplank.', name=shelf.name),
        ):
            return
        try:
            self.library.shelves.delete_shelf(shelf_id)
            self.refresh()
        except Exception as exc:
            self._show_error(exc)

    def _move_book(self, book, shelf_id: str):
        try:
            self.library.shelves.move_book(book.id, shelf_id)
            self.refresh()
        except Exception as exc:
            self._show_error(exc)

    def _restore_shelves(self):
        try:
            self.library.shelves.restore_from_last_good()
            self.refresh()
        except Exception as exc:
            self._show_error(exc)

    def _reset_shelves(self):
        if not self._confirm(
            tr('bookshelf.recovery.reset', 'Opnieuw beginnen'),
            tr('bookshelf.recovery.reset_confirm', 'De plankindeling opnieuw maken? Alle boeken komen op de standaardplank. De boeken zelf worden niet gewijzigd.'),
        ):
            return
        try:
            self.library.shelves.reset_to_default()
            self.refresh()
        except Exception as exc:
            self._show_error(exc)

    def _update_notice(self, loaded):
        source = loaded.source
        if source in ('canonical', 'pending_migration'):
            self.notice.hide()
            return
        self.notice.show()
        self.notice_restore.setVisible(source == 'last_good')
        self.notice_reset.setVisible(source == 'emergency')
        if source == 'last_good':
            self.notice_text.setText(tr('bookshelf.recovery.last_good', 'De huidige plankindeling kon niet worden geladen. QuietWriter toont de laatste goede indeling.'))
        elif source == 'future':
            self.notice_text.setText(tr('bookshelf.recovery.future', 'Deze plankindeling is gemaakt door een nieuwere versie van QuietWriter en is hier alleen-lezen.'))
        else:
            self.notice_text.setText(tr('bookshelf.recovery.emergency', 'De plankindeling kon niet worden geladen. Je boeken zijn intact; de indeling kan opnieuw worden gemaakt.'))

    def _show_shelf_warnings(self):
        warnings = self.library.pop_shelf_metadata_warnings()
        if not warnings:
            return
        QMessageBox.warning(
            self,
            tr('bookshelf.warning.title', 'Boek opgeslagen'),
            '\n'.join(warnings),
        )

    def refresh(self):
        while self.shelves_layout.count():
            item = self.shelves_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        loaded = self.library.shelves.load()
        self._update_notice(loaded)
        books = self.library.list_books()
        demo_mode = self.demo_mode_enabled()
        visible_book_ids = self.library.shelves.visible_book_ids(
            [book.id for book in books], demo_mode=demo_mode, loaded=loaded
        )
        books = [book for book in books if book.id in visible_book_ids]
        visible_shelf_ids = set(self.library.shelves.visible_shelf_ids(demo_mode=demo_mode, loaded=loaded))
        load_errors = [] if demo_mode else list(getattr(self.library, 'last_list_errors', []) or [])
        total = len(books)
        word_counts = {}

        def word_count(book):
            key = getattr(book, 'id', None) or str(book.path)
            if key not in word_counts:
                word_counts[key] = sum(
                    self._chapter_word_count(book, chapter)
                    for section in book.sections
                    for chapter in section.chapters
                )
            return word_counts[key]

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
                    book.title, str(md.get('slug', '')), str(md.get('description', '')),
                    str(md.get('meta', '')), str(md.get('intro', '')), str(md.get('tags', '')),
                    str(md.get('author', '')),
                ]).casefold()
            books = [b for b in books if query in searchable(b)]

        shown = len(books)
        if query:
            key = 'bookshelf.count.filtered.one' if total == 1 else 'bookshelf.count.filtered.many'
            self.count.setText(tr(key, '{shown} van {total} boeken', shown=shown, total=total))
        else:
            key = 'bookshelf.count.one' if total == 1 else 'bookshelf.count.many'
            self.count.setText(tr(key, '{count} boeken', count=total))
        self.no_results.setVisible(bool(query) and not books)
        if load_errors:
            names = ', '.join(str(row.get('title') or '?') for row in load_errors[:3])
            count = len(load_errors)
            suffix = ' ' + (tr('bookshelf.load_errors.one', '• 1 boek niet geopend: {names}', names=names) if count == 1 else tr('bookshelf.load_errors.many', '• {count} boeken niet geopend: {names}', count=count, names=names))
            self.count.setText(self.count.text() + suffix)

        visible_shelves = tuple(s for s in loaded.state.shelves if s.id in visible_shelf_ids)
        by_shelf = {s.id: [] for s in visible_shelves}
        for book in books:
            shelf_id = self.library.shelves.effective_shelf_id(book.id, loaded=loaded)
            if shelf_id in by_shelf:
                by_shelf[shelf_id].append(book)

        for shelf in visible_shelves:
            shelf_books = by_shelf.get(shelf.id, [])
            if query and not shelf_books:
                continue
            section = ShelfSection(
                self.library, shelf, shelf_books, visible_shelves,
                default_shelf_id=loaded.state.default_shelf_id,
                word_count=word_count,
                show_new_card=(shelf.id == loaded.state.default_shelf_id and not query),
                settings=self.settings,
            )
            section.rename_requested.connect(self._rename_shelf)
            section.privacy_requested.connect(self._set_private)
            section.delete_requested.connect(self._delete_shelf)
            section.book_opened.connect(self.open_book.emit)
            section.book_move_requested.connect(self._move_book)
            section.new_book.connect(self.new_book.emit)
            section.import_book.connect(self.import_book.emit)
            self.shelves_layout.addWidget(section)
        self.shelves_layout.addStretch(1)
        self._save_word_count_cache()
        QTimer.singleShot(0, self._show_shelf_warnings)
