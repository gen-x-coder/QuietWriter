from __future__ import annotations
import os
import re
import sys
from pathlib import Path
from datetime import datetime, date
import copy

from PySide6.QtCore import Qt, QSettings, QTimer, QSize, Signal, QMimeData, QUrl, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QPoint
from PySide6.QtGui import QAction, QColor, QFont, QFontDatabase, QIcon, QImageReader, QPainter, QPixmap, QTextCursor, QPen, QDrag, QDesktopServices, QPalette, QTextBlockFormat, QTextCharFormat
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QFrame, QGridLayout, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QSplitter, QStackedWidget, QStatusBar,
    QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QAbstractItemView, QHeaderView, QMenu, QTabWidget, QGraphicsDropShadowEffect, QSpinBox
)

from . import APP_NAME
from .storage import Library, slugify
from .themes import THEMES, stylesheet
from .typography import WritingTypography, available_families, typography_from_values
from .ollama import OllamaClient
from .ai.ui import AIPanel
from .ai.providers import ProviderFactory
from .search import BookSearchIndex
from .spellcheck import WordDictionary, SpellHighlighter
from .dictionary_catalog import DictionaryCatalog
from .chapter_order import DropTarget, move_chapter as reorder_chapter
from .i18n import tr
from .markdown_io import insert_scene_break as build_scene_break_text
from .icon_theme import icon, set_icon_theme


def confirm(parent, title: str, text: str, default_no: bool = True) -> bool:
    """Centrale Ja/Nee-dialoog; knopteksten komen uit het taalbestand."""
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Warning)
    box.setWindowTitle(title)
    box.setText(text)
    yes = box.addButton(tr('common.yes', 'Ja'), QMessageBox.YesRole)
    no = box.addButton(tr('common.no', 'Nee'), QMessageBox.NoRole)
    box.setDefaultButton(no if default_no else yes)
    box.exec()
    return box.clickedButton() is yes


class ManuscriptEditor(QTextEdit):
    """Rustige schrijfruimte met begrensde tekstkolom en lichte scene-break styling."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.max_text_width = 850
        self.setAcceptRichText(False)
        self._formatting_scene_breaks = False
        settings = QSettings('QuietWriter', 'QuietWriter')
        self.apply_typography(WritingTypography.from_settings(settings))
        self._update_margins()

    def apply_typography(self, typography: WritingTypography):
        """Apply writing typography without coupling family, size or theme.

        The editor stores plain text. Font family/size therefore live entirely in
        the QTextDocument default font instead of being written into every
        character format. This makes switching fonts immediate and repeatable.
        """
        font = typography.body_font()
        self.setFont(font)
        self.document().setDefaultFont(font)
        self.document().markContentsDirty(0, self.document().characterCount())
        self.apply_scene_break_formatting()
        self.viewport().update()

    def set_editor_font(self, preferred: str, point_size: int | None = None):
        # Backwards-compatible wrapper used by a few call sites.
        if point_size is None:
            point_size = QSettings('QuietWriter', 'QuietWriter').value('editor_font_size', 15, int)
        self.apply_typography(typography_from_values(preferred, point_size))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_margins()

    def _update_margins(self):
        side = max(42, (max(0, self.width()) - self.max_text_width) // 2)
        self.setViewportMargins(side, 30, side, 42)

    def apply_scene_break_formatting(self):
        """Render regels die exact *** bevatten als rustige gecentreerde scene break.

        De bron blijft platte Markdown; alleen de QTextDocument-opmaak verandert.
        """
        if self._formatting_scene_breaks:
            return
        self._formatting_scene_breaks = True
        signals_were_blocked = self.signalsBlocked()
        self.blockSignals(True)
        old_cursor = self.textCursor()
        old_pos, old_anchor = old_cursor.position(), old_cursor.anchor()
        try:
            block = self.document().begin()
            theme = THEMES.get(str(QSettings('QuietWriter','QuietWriter').value('theme','Helder')), THEMES['Helder'])
            muted = QColor(theme['muted'])
            while block.isValid():
                cur = QTextCursor(block)
                fmt = block.blockFormat()
                is_break = block.text().strip() == '***'
                was_centered = fmt.alignment() == Qt.AlignCenter
                if is_break:
                    if not was_centered or fmt.topMargin() != 14 or fmt.bottomMargin() != 14:
                        fmt.setAlignment(Qt.AlignCenter)
                        fmt.setTopMargin(14)
                        fmt.setBottomMargin(14)
                        cur.setBlockFormat(fmt)
                    cur.select(QTextCursor.BlockUnderCursor)
                    charfmt = QTextCharFormat()
                    charfmt.setForeground(muted)
                    charfmt.setFontLetterSpacing(160)
                    charfmt.setFontWeight(QFont.Weight.DemiBold)
                    cur.mergeCharFormat(charfmt)
                elif was_centered:
                    # Een voormalige scene break is gewone tekst geworden.
                    fmt.setAlignment(Qt.AlignLeft)
                    fmt.setTopMargin(0); fmt.setBottomMargin(0)
                    cur.setBlockFormat(fmt)
                    cur.select(QTextCursor.BlockUnderCursor)
                    charfmt = QTextCharFormat()
                    charfmt.clearForeground()
                    charfmt.setFontLetterSpacing(0)
                    charfmt.setFontWeight(QFont.Weight.Light)
                    cur.mergeCharFormat(charfmt)
                block = block.next()
        finally:
            restore = self.textCursor()
            restore.setPosition(min(old_anchor, max(0, self.document().characterCount()-1)))
            restore.setPosition(min(old_pos, max(0, self.document().characterCount()-1)), QTextCursor.KeepAnchor)
            self.setTextCursor(restore)
            self.blockSignals(signals_were_blocked)
            self._formatting_scene_breaks = False


class Splash(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(440, 240)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(34, 34, 34, 34)
        title = QLabel(APP_NAME)
        title.setObjectName('title')
        self.status = QLabel('Starten…')
        self.status.setObjectName('muted')
        lay.addStretch()
        lay.addWidget(title)
        lay.addSpacing(12)
        lay.addWidget(self.status)
        lay.addStretch()

    def set_status(self, text):
        self.status.setText(text)
        QApplication.processEvents()


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
                x = max(0, (scaled.width() - target.width()) // 2)
                y = max(0, (scaled.height() - target.height()) // 2)
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
    opened = __import__('PySide6.QtCore').QtCore.Signal(object)

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
    open_book = __import__('PySide6.QtCore').QtCore.Signal(object)
    new_book = __import__('PySide6.QtCore').QtCore.Signal()
    import_book = __import__('PySide6.QtCore').QtCore.Signal()

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


class BookDetailsPage(QWidget):
    saved = Signal(object)
    deleted = Signal(object)

    def __init__(self, library, settings, book, parent=None):
        super().__init__(parent)
        self.library = library
        self.settings = settings
        self.book = book
        self.old_slug = book.slug
        self.pending_cover = None
        root = QVBoxLayout(self); root.setContentsMargins(42, 34, 42, 34); root.setSpacing(12)
        title = QLabel('Boekdetails'); title.setObjectName('title')
        intro = QLabel('Deze gegevens horen bij het boek en kunnen later bij export naar Markdown als metadata worden gebruikt.')
        intro.setObjectName('muted'); intro.setWordWrap(True)
        root.addWidget(title); root.addWidget(intro); root.addSpacing(8)

        form = QFormLayout()
        self.title_edit = QLineEdit(book.title)
        self.slug_edit = QLineEdit(book.slug)
        slug_box = QWidget(); sh = QHBoxLayout(slug_box); sh.setContentsMargins(0,0,0,0)
        make_slug = QPushButton('Van titel')
        make_slug.clicked.connect(lambda: self.slug_edit.setText(slugify(self.title_edit.text())))
        sh.addWidget(self.slug_edit); sh.addWidget(make_slug)
        md = book.metadata or {}
        self.date_edit = QLineEdit(md.get('date',''))
        self.description = QTextEdit(md.get('description','')); self.description.setMaximumHeight(82)
        self.intro_text = QTextEdit(md.get('intro','')); self.intro_text.setMaximumHeight(100)
        self.meta = QTextEdit(md.get('meta','')); self.meta.setMaximumHeight(82)
        self.image_alt = QTextEdit(md.get('image_alt','')); self.image_alt.setMaximumHeight(82)
        self.author = QLineEdit(md.get('author',''))
        self.tags = QLineEdit(md.get('tags',''))
        self.published = QComboBox(); self.published.addItems(['No', 'Yes'])
        self.published.setCurrentText(str(md.get('published','No') or 'No'))
        self.synopsis = QTextEdit(md.get('synopsis','')); self.synopsis.setMaximumHeight(82)
        form.addRow('Titel', self.title_edit)
        form.addRow('Datum', self.date_edit)
        form.addRow('Slug', slug_box)
        form.addRow('Korte beschrijving', self.description)
        form.addRow('Intro boven het verhaal', self.intro_text)
        form.addRow('Meta / SEO-beschrijving', self.meta)
        form.addRow('Beschrijving afbeelding', self.image_alt)
        form.addRow('Auteur', self.author)
        form.addRow('Tags', self.tags)
        form.addRow('Gepubliceerd', self.published)
        form.addRow('Synopsis', self.synopsis)

        cover_box = QFrame(); cover_box.setObjectName('panel')
        cb = QHBoxLayout(cover_box); cb.setContentsMargins(12,12,12,12)
        self.cover_preview = QLabel(); self.cover_preview.setFixedSize(100,160); self.cover_preview.setAlignment(Qt.AlignCenter)
        cover_right = QVBoxLayout()
        self.cover_name = QLabel(''); self.cover_name.setObjectName('muted'); self.cover_name.setWordWrap(True)
        choose = QPushButton('Omslag kiezen…'); choose.clicked.connect(self.choose_cover)
        remove_cover = QPushButton('Omslag verwijderen'); remove_cover.clicked.connect(self.remove_cover)
        self.header_path = QLabel(''); self.header_path.setObjectName('muted'); self.header_path.setWordWrap(True)
        cover_right.addWidget(QLabel('Boekomslag · verhouding 1:1,6 · lange zijde minimaal 1024 px'))
        cover_buttons = QHBoxLayout(); cover_buttons.addWidget(choose); cover_buttons.addWidget(remove_cover); cover_buttons.addStretch()
        cover_right.addWidget(self.cover_name); cover_right.addLayout(cover_buttons); cover_right.addWidget(self.header_path); cover_right.addStretch()
        cb.addWidget(self.cover_preview); cb.addLayout(cover_right,1)

        # Metadata groeit mee met toekomstige frontmattervelden; houd de acties
        # onderaan altijd bereikbaar door het inhoudsdeel scrollbaar te maken.
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget); details_layout.setContentsMargins(0,0,0,0)
        details_layout.addLayout(form); details_layout.addWidget(cover_box); details_layout.addStretch()
        details_scroll = QScrollArea(); details_scroll.setWidgetResizable(True); details_scroll.setFrameShape(QFrame.NoFrame)
        details_scroll.setWidget(details_widget)
        root.addWidget(details_scroll, 1)
        self.slug_edit.textChanged.connect(self._update_header_path)
        self._refresh_cover_preview()
        self._update_header_path()

        actions = QHBoxLayout()
        export_btn = QPushButton('Exporteren…'); export_btn.setObjectName('secondaryButton'); export_btn.clicked.connect(self.export_markdown)
        delete = QPushButton('Naar prullenbak'); delete.setObjectName('dangerButton'); delete.clicked.connect(self.delete_book)
        actions.addWidget(export_btn); actions.addWidget(delete); actions.addStretch()
        save_btn = QPushButton(tr('common.save', 'Opslaan')); save_btn.setObjectName('primaryButton'); save_btn.clicked.connect(self.save)
        actions.addWidget(save_btn); root.addLayout(actions)

    def _cover_candidate(self):
        if self.pending_cover == '__REMOVE__':
            return self.library.default_cover_path()
        return self.pending_cover or self.library.cover_path(self.book) or self.library.default_cover_path()

    def _refresh_cover_preview(self):
        path = self._cover_candidate()
        self.cover_name.setText(str(path) if path else 'Geen omslag gevonden; QuietWriter gebruikt de ingebouwde rustige standaardweergave.')
        if path and Path(path).exists():
            pix = QPixmap(str(path))
            self.cover_preview.setPixmap(pix.scaled(self.cover_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.cover_preview.clear(); self.cover_preview.setText('Geen\nomslag')

    def _update_header_path(self):
        has_cover = self.pending_cover not in (None, '__REMOVE__') or (self.pending_cover is None and self.library.cover_path(self.book))
        if not has_cover:
            self.header_path.setText('Afbeeldingspad in metadata: leeg (geen omslag)')
            return
        template = self.settings.value('cover_header_template', '/{slug}.jpg')
        slug = self.slug_edit.text().strip() or 'boek'
        ext = 'jpg'
        cover = self.pending_cover if isinstance(self.pending_cover, Path) else self.library.cover_path(self.book)
        if cover:
            ext = Path(cover).suffix.lstrip('.') or 'jpg'
        try:
            path = str(template).format(slug=slug, ext=ext)
        except Exception:
            path = f'/{slug}.{ext}'
        self.header_path.setText(f'Afbeeldingspad in metadata: {path}')

    def choose_cover(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Kies boekomslag', str(self.library.covers_dir), 'Afbeeldingen (*.jpg *.jpeg *.png *.webp)')
        if not path: return
        reader = QImageReader(path)
        size = reader.size()
        if not size.isValid():
            QMessageBox.warning(self, 'Boekomslag', 'Deze afbeelding kon niet worden gelezen.'); return
        w, h = size.width(), size.height()
        ratio = w / h if h else 0
        if h < 1024:
            QMessageBox.warning(self, 'Boekomslag', f'De lange zijde is {h}px. Gebruik minimaal 1024px.'); return
        if abs(ratio - (1/1.6)) > 0.035:
            QMessageBox.warning(self, 'Boekomslag', f'De verhouding is {w}:{h}. Gebruik ongeveer 1:1,6 (bijvoorbeeld 1024×1638).'); return
        self.pending_cover = Path(path)
        self._refresh_cover_preview(); self._update_header_path()

    def remove_cover(self):
        # De wijziging is meteen zichtbaar, maar wordt pas definitief bij Opslaan.
        self.pending_cover = '__REMOVE__'
        self.cover_name.setText('Geen eigen omslag. De standaardomslag wordt gebruikt.')
        default = self.library.default_cover_path()
        if default and Path(default).exists():
            pix = QPixmap(str(default))
            self.cover_preview.setPixmap(pix.scaled(self.cover_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.cover_preview.clear(); self.cover_preview.setText('Standaard\nomslag')
        self._update_header_path()

    def save(self):
        title = self.title_edit.text().strip()
        slug = self.slug_edit.text().strip()
        if not title:
            QMessageBox.warning(self, 'Boekdetails', 'Geef het boek een titel.'); return
        if not slug:
            slug = slugify(title)
        # slug normaliseren zodat bestandsnamen en metadata voorspelbaar blijven.
        slug = slugify(slug)
        self.slug_edit.setText(slug)
        self.book.title = title
        template = self.settings.value('cover_header_template', '/{slug}.jpg')
        try:
            image_ref = str(template).format(slug=slug, ext='jpg')
        except Exception:
            image_ref = f'/{slug}.jpg'
        self.book.metadata.update({
            'slug': slug,
            'date': self.date_edit.text().strip(),
            'description': self.description.toPlainText().strip(),
            'intro': self.intro_text.toPlainText().strip(),
            'meta': self.meta.toPlainText().strip(),
            'image': image_ref if self.pending_cover != '__REMOVE__' and (self.pending_cover or self.library.cover_path(self.book)) else '',
            'image_alt': self.image_alt.toPlainText().strip(),
            'author': self.author.text().strip(),
            'tags': self.tags.text().strip(),
            'published': self.published.currentText().strip() or 'No',
            'synopsis': self.synopsis.toPlainText().strip(),
        })
        try:
            self.library.rename_cover_for_slug(self.book, self.old_slug, slug)
            if self.pending_cover == '__REMOVE__':
                self.library.remove_cover(self.book)
            elif self.pending_cover:
                self.library.set_cover(self.book, self.pending_cover)
            self.library.save_manifest(self.book)
        except Exception as e:
            QMessageBox.warning(self, 'Boekdetails', f'Opslaan mislukt:\n{e}'); return
        self.old_slug = slug
        self.pending_cover = None
        self.saved.emit(self.book)

    def export_markdown(self):
        # Sla eerst de velden in deze dialoog op in het in-memory boek, zonder de dialoog te sluiten.
        title = self.title_edit.text().strip() or self.book.title
        slug = slugify(self.slug_edit.text().strip() or title)
        self.book.title = title
        self.book.metadata.update({
            'slug': slug,
            'date': self.date_edit.text().strip(),
            'description': self.description.toPlainText().strip(),
            'intro': self.intro_text.toPlainText().strip(),
            'meta': self.meta.toPlainText().strip(),
            'image_alt': self.image_alt.toPlainText().strip(),
            'author': self.author.text().strip(),
            'tags': self.tags.text().strip(),
            'published': self.published.currentText().strip() or 'No',
            'synopsis': self.synopsis.toPlainText().strip(),
        })
        default_name = f'{slug}.md'
        path, _ = QFileDialog.getSaveFileName(self, 'Boek exporteren naar Markdown', str(Path.home() / default_name), 'Markdown (*.md)')
        if not path:
            return
        destination = Path(path)
        if destination.suffix.lower() != '.md':
            destination = destination.with_suffix('.md')
        if destination.exists() and not confirm(self, 'Bestand overschrijven', f'“{destination.name}” bestaat al. Wil je dit bestand overschrijven?'):
            return
        template = self.settings.value('cover_header_template', '/{slug}.jpg')
        image_ref = ''
        cover = self.library.cover_path(self.book)
        if cover:
            try:
                image_ref = str(template).format(slug=slug, ext=cover.suffix.lstrip('.'))
            except Exception:
                image_ref = f'/{slug}.jpg'
        # Zonder lokale omslag blijft image bewust leeg in de export.
        self.book.metadata['image'] = image_ref
        try:
            self.library.export_markdown_book(self.book, destination, image_ref=image_ref, include_frontmatter=True, include_section_markers=True)
        except Exception as exc:
            QMessageBox.critical(self, 'Boek exporteren', f'Exporteren mislukt:\n\n{exc}')
            return
        QMessageBox.information(self, 'Boek exporteren', f'Het boek is geëxporteerd naar:\n{destination}')

    def delete_book(self):
        if not confirm(
            self, 'Boek naar prullenbak',
            f'Wil je “{self.book.title}” naar de prullenbak verplaatsen?\n\nJe kunt het boek later herstellen of definitief verwijderen vanaf de prullenbakpagina.'
        ):
            return
        try:
            self.library.delete_book(self.book)
        except Exception as e:
            QMessageBox.critical(self, 'Boek verwijderen', str(e)); return
        self.deleted.emit(self.book)


class TrashPage(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        root = QVBoxLayout(self); root.setContentsMargins(42, 34, 42, 34)
        top = QHBoxLayout()
        title = QLabel('Prullenbak'); title.setObjectName('title')
        self.restore_btn = QPushButton('Herstellen'); self.restore_btn.setObjectName('primaryButton'); self.restore_btn.clicked.connect(self.restore_selected)
        self.delete_btn = QPushButton('Selectie definitief verwijderen'); self.delete_btn.setObjectName('dangerButton'); self.delete_btn.clicked.connect(self.delete_selected)
        self.empty_btn = QPushButton('Prullenbak legen'); self.empty_btn.setObjectName('dangerButton'); self.empty_btn.clicked.connect(self.empty_trash)
        top.addWidget(title); top.addStretch(); top.addWidget(self.restore_btn); top.addWidget(self.delete_btn); top.addWidget(self.empty_btn)
        info = QLabel('Selecteer één of meer boeken. Definitief verwijderen kan niet ongedaan worden gemaakt.')
        info.setObjectName('muted')
        self.list = QListWidget(); self.list.setSelectionMode(QListWidget.ExtendedSelection)
        self.empty = QLabel('De prullenbak is leeg.'); self.empty.setObjectName('muted'); self.empty.setAlignment(Qt.AlignCenter)
        root.addLayout(top); root.addWidget(info); root.addSpacing(10); root.addWidget(self.empty); root.addWidget(self.list, 1)
        self.refresh()

    def refresh(self):
        rows = self.main.library.list_trashed_books()
        self.list.clear()
        for row in rows:
            dt = datetime.fromtimestamp(row['deleted']).strftime('%d-%m-%Y %H:%M')
            item = QListWidgetItem(f"{row['title']}   ·   verwijderd {dt}")
            item.setData(Qt.UserRole, str(row['path']))
            self.list.addItem(item)
        self.empty.setVisible(not rows); self.list.setVisible(bool(rows))
        self.restore_btn.setEnabled(bool(rows)); self.delete_btn.setEnabled(bool(rows)); self.empty_btn.setEnabled(bool(rows))

    def selected_paths(self):
        return [Path(i.data(Qt.UserRole)) for i in self.list.selectedItems()]

    def restore_selected(self):
        paths = self.selected_paths()
        if not paths:
            QMessageBox.information(self, 'Prullenbak', 'Selecteer eerst één of meer boeken.')
            return
        for p in paths:
            try: self.main.library.restore_trashed_book(p)
            except Exception as e: QMessageBox.warning(self, 'Herstellen', str(e))
        self.main.start.refresh(); self.refresh()

    def delete_selected(self):
        paths = self.selected_paths()
        if not paths:
            QMessageBox.information(self, 'Prullenbak', 'Selecteer eerst één of meer boeken.')
            return
        if not confirm(self, 'Definitief verwijderen', f'Wil je {len(paths)} geselecteerde item(s) definitief verwijderen?'):
            return
        for p in paths:
            self.main.library.permanently_delete_trashed_book(p)
        self.refresh()

    def empty_trash(self):
        if not confirm(self, 'Prullenbak legen', 'Wil je alle boeken in de prullenbak definitief verwijderen?'):
            return
        self.main.library.empty_trash(); self.refresh()


class PersonaPage(QWidget):
    def __init__(self, library):
        super().__init__()
        self.library = library
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 30, 36, 30)
        top = QHBoxLayout()
        title = QLabel('Schrijverspersona')
        title.setObjectName('title')
        load_default = QPushButton('Meegeleverde schrijfwijzer laden')
        load_default.clicked.connect(self.load_default)
        top.addWidget(title); top.addStretch(); top.addWidget(load_default)
        info = QLabel('Deze persona wordt automatisch aan iedere AI-opdracht toegevoegd. QuietWriter wijzigt hem nooit automatisch.')
        info.setObjectName('muted')
        self.edit = QTextEdit()
        self.edit.setPlainText(library.read_persona())
        save = QPushButton('Opslaan'); save.setObjectName('primaryButton')
        save.clicked.connect(self.save)
        lay.addLayout(top)
        lay.addWidget(info)
        lay.addSpacing(12)
        lay.addWidget(self.edit)
        lay.addWidget(save, 0, Qt.AlignRight)

    def load_default(self):
        path = Path(__file__).resolve().parents[1] / 'schrijver.md'
        if not path.exists():
            QMessageBox.warning(self, 'Schrijfwijzer', 'De meegeleverde schrijfwijzer is niet gevonden.')
            return
        if confirm(self, 'Schrijfwijzer laden', 'De huidige tekst in de editor vervangen door de meegeleverde, geoptimaliseerde schrijfwijzer?'):
            self.edit.setPlainText(path.read_text(encoding='utf-8'))

    def save(self):
        self.library.save_persona(self.edit.toPlainText())


class SettingsPage(QWidget):
    DICTIONARY_DOWNLOAD_URL = 'https://extensions.openoffice.org/'

    def __init__(self, settings: QSettings, parent=None, models=None):
        super().__init__(parent)
        self.settings = settings
        self.original_theme = settings.value('theme', 'Helder')
        self._preview_theme = str(self.original_theme or 'Helder')
        self.original_typography = WritingTypography.from_settings(settings)
        self.original_editor_font = self.original_typography.family
        self.original_editor_size = self.original_typography.point_size
        self.available_models = list(models or [])

        root = QVBoxLayout(self); root.setContentsMargins(42, 34, 42, 34); root.setSpacing(14)
        page_title = QLabel(tr('settings.title', 'Instellingen')); page_title.setObjectName('title'); root.addWidget(page_title)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        # Algemeen
        general = QWidget(); gf = QFormLayout(general)
        self.language = QComboBox(); self.language.addItem('Nederlands', 'nl')
        self.autosave = QCheckBox(); self.autosave.setChecked(settings.value('autosave', True, bool))
        gf.addRow('Programmataal', self.language)
        gf.addRow('Automatisch opslaan', self.autosave)
        self.tabs.addTab(general, 'Algemeen')

        # Uiterlijk
        appearance = QWidget(); af = QFormLayout(appearance)
        self.theme = QComboBox(); self.theme.addItems(THEMES.keys()); self.theme.setCurrentText(settings.value('theme', 'Helder'))
        self.editor_font = QComboBox(); self.editor_font.addItems(available_families()); self.editor_font.setCurrentText(self.original_typography.family)
        self.editor_font_size = QSpinBox(); self.editor_font_size.setRange(11, 24); self.editor_font_size.setSuffix(' pt'); self.editor_font_size.setValue(self.original_typography.point_size)
        af.addRow('Kleurenschema', self.theme)
        af.addRow('Schrijflettertype', self.editor_font)
        af.addRow('Tekstgrootte', self.editor_font_size)
        appearance_note = QLabel('Lettertype en tekstgrootte zijn onafhankelijke instellingen. QuietWriter toont alle op deze computer beschikbare lettertypen. Merriweather is de standaard; ontbreekt een opgeslagen font, dan valt QuietWriter terug op Merriweather of Georgia. Wijzigingen worden direct in de editor getoond; Annuleren herstelt de vorige instellingen.')
        appearance_note.setObjectName('muted'); appearance_note.setWordWrap(True); af.addRow('', appearance_note)
        self.tabs.addTab(appearance, 'Uiterlijk')

        # Opslag
        storage = QWidget(); sf = QFormLayout(storage)
        self.root = QLineEdit(settings.value('workspace', str(Path.home() / 'QuietWriter')))
        choose = QPushButton('Map kiezen…'); choose.clicked.connect(self.choose_root)
        box = QWidget(); h = QHBoxLayout(box); h.setContentsMargins(0,0,0,0); h.addWidget(self.root); h.addWidget(choose)
        self.cover_template = QLineEdit(settings.value('cover_header_template', '/{slug}.jpg')); self.cover_template.setPlaceholderText('/{slug}.jpg')
        sf.addRow('Werkmap', box)
        self.sync_warning = QLabel('')
        self.sync_warning.setObjectName('syncWarning'); self.sync_warning.setWordWrap(True)
        sf.addRow('', self.sync_warning)
        self.root.textChanged.connect(self.update_sync_warning)
        sf.addRow('Afbeeldingspad in metadata', self.cover_template)
        storage_note = QLabel('Voor afbeeldingspaden kun je {slug} gebruiken, bijvoorbeeld /{slug}.jpg of /images/{slug}.jpg. QuietWriter bewaart alleen het relatieve pad en kent geen websiteadres.')
        storage_note.setObjectName('muted'); storage_note.setWordWrap(True); sf.addRow('', storage_note)
        self.tabs.addTab(storage, 'Opslag')

        # AI — provider en functies zijn bewust van elkaar losgekoppeld.
        ai = QWidget(); aif = QFormLayout(ai)
        self.ai_provider = QComboBox(); self.ai_provider.addItem('Ollama (lokaal)', 'ollama'); self.ai_provider.addItem('OpenRouter', 'openrouter')
        provider_value = str(settings.value('ai_provider', 'ollama') or 'ollama')
        idx = self.ai_provider.findData(provider_value); self.ai_provider.setCurrentIndex(max(0, idx))
        self.ollama = QLineEdit(settings.value('ollama_url', 'http://127.0.0.1:11434'))
        self.openrouter_key = QLineEdit(settings.value('openrouter_api_key', '')); self.openrouter_key.setEchoMode(QLineEdit.Password); self.openrouter_key.setPlaceholderText('API-key')
        self.model = QComboBox(); self.model.setEditable(True)
        refresh = QPushButton('Modellen ophalen'); refresh.clicked.connect(self.refresh_models)
        modelbox = QWidget(); mh = QHBoxLayout(modelbox); mh.setContentsMargins(0,0,0,0); mh.addWidget(self.model); mh.addWidget(refresh)
        aif.addRow('AI-provider', self.ai_provider)
        aif.addRow('Ollama-adres', self.ollama)
        aif.addRow('OpenRouter API-key', self.openrouter_key)
        aif.addRow('Schrijf- en analysemodel', modelbox)
        ai_note = QLabel('QuietWriter gebruikt je schrijverspersona en de gekozen context: selectie, huidig hoofdstuk, huidige sectie of hele boek. De AI-provider staat los van deze functies; Ollama en OpenRouter gebruiken dezelfde schrijfworkflow.')
        ai_note.setObjectName('muted'); ai_note.setWordWrap(True); aif.addRow('', ai_note)
        self.tabs.addTab(ai, 'AI')

        # Spelling
        spelling = QWidget(); sl = QVBoxLayout(spelling); sl.setContentsMargins(16,16,16,16); sl.setSpacing(12)
        self.spell_enabled = QCheckBox('Spellingscontrole inschakelen'); self.spell_enabled.setChecked(settings.value('spell_enabled', True, bool))
        sl.addWidget(self.spell_enabled)
        explanation = QLabel(
            'QuietWriter zoekt automatisch naar Hunspell-woordenboeken in de werkmap en in geïnstalleerde versies van ONLYOFFICE, LibreOffice en OpenOffice. '
            'Alle gevonden talen verschijnen hieronder. Heb je geen van deze programma’s, dan kun je zelf een .dic/.aff-woordenboek toevoegen of via de downloadknop naar een algemene woordenboeksite gaan.'
        )
        explanation.setObjectName('muted'); explanation.setWordWrap(True); sl.addWidget(explanation)

        self.dictionary_catalog = DictionaryCatalog(Path(settings.value('workspace', str(Path.home() / 'QuietWriter'))) / 'dictionaries')
        row = QHBoxLayout(); row.addWidget(QLabel('Taal'))
        self.spell_language = QComboBox(); self.spell_language.currentIndexChanged.connect(self.update_dictionary_info); row.addWidget(self.spell_language, 1)
        sl.addLayout(row)
        self.dictionary_info = QLabel(''); self.dictionary_info.setObjectName('muted'); self.dictionary_info.setWordWrap(True); sl.addWidget(self.dictionary_info)

        actions = QHBoxLayout()
        self.scan_dict_btn = QPushButton('Opnieuw zoeken'); self.scan_dict_btn.clicked.connect(self.refresh_dictionaries)
        self.add_dict_btn = QPushButton('Woordenboek toevoegen…'); self.add_dict_btn.clicked.connect(self.choose_dictionary)
        self.remove_dict_btn = QPushButton('Eigen woordenboek verwijderen'); self.remove_dict_btn.clicked.connect(self.remove_dictionary)
        self.download_dict_btn = QPushButton('Woordenboeken downloaden'); self.download_dict_btn.clicked.connect(self.open_dictionary_download)
        actions.addWidget(self.scan_dict_btn); actions.addWidget(self.add_dict_btn); actions.addWidget(self.remove_dict_btn); actions.addWidget(self.download_dict_btn)
        sl.addLayout(actions)
        sl.addStretch(1)
        self.tabs.addTab(spelling, 'Spelling')

        self._populate_models(self.available_models)
        self.update_sync_warning()
        self.refresh_dictionaries(preserve_locale=str(settings.value('spell_language', 'nl_NL') or 'nl_NL'))

        buttons = QHBoxLayout(); buttons.addStretch()
        cancel_btn = QPushButton(tr('common.cancel', 'Annuleren')); cancel_btn.setObjectName('secondaryButton'); cancel_btn.clicked.connect(self.cancel)
        save_btn = QPushButton(tr('common.save', 'Opslaan')); save_btn.setObjectName('primaryButton'); save_btn.clicked.connect(self.save_settings)
        buttons.addWidget(cancel_btn); buttons.addWidget(save_btn); root.addLayout(buttons)
        self.theme.currentTextChanged.connect(self._preview_appearance)
        self.editor_font.currentTextChanged.connect(self._preview_appearance)
        self.editor_font_size.valueChanged.connect(self._preview_appearance)

    def _preview_appearance(self, *_):
        theme = self.theme.currentText() or 'Helder'
        font = self.editor_font.currentText() or 'Merriweather'
        size = int(self.editor_font_size.value())
        # Re-polishing the complete QApplication for every font-family change is
        # unnecessary and on some Windows/Qt builds triggers
        # QFont::setPointSize(-1). Only a theme change needs a global QSS pass.
        if theme != self._preview_theme:
            win = self.parent()
            if win and hasattr(win, 'apply_theme'):
                win.apply_theme(theme)
            else:
                QApplication.instance().setStyleSheet(stylesheet(theme))
            self._preview_theme = theme
        win = self.parent()
        if win and hasattr(win, 'apply_writing_font'):
            win.apply_writing_font(font, size)

    def restore_preview(self):
        if self._preview_theme != str(self.original_theme or 'Helder'):
            win = self.parent()
            if win and hasattr(win, 'apply_theme'):
                win.apply_theme(str(self.original_theme or 'Helder'))
            else:
                QApplication.instance().setStyleSheet(stylesheet(self.original_theme))
            self._preview_theme = str(self.original_theme or 'Helder')
        win = self.parent()
        if win and hasattr(win, 'apply_writing_font'):
            win.apply_writing_font(self.original_editor_font, self.original_editor_size)

    def cancel(self):
        self.restore_preview()
        if self.parent() and hasattr(self.parent(), 'return_from_settings'):
            self.parent().return_from_settings()

    def update_sync_warning(self):
        path = self.root.text().strip()
        provider = None
        lowered = path.casefold().replace('\\', '/')
        checks = [
            ('Dropbox', 'dropbox'),
            ('OneDrive', 'onedrive'),
            ('Google Drive', 'google drive'),
            ('Google Drive', 'googledrive'),
            ('iCloud Drive', 'icloud'),
        ]
        for label, token in checks:
            if token in lowered:
                provider = label
                break
        if provider:
            self.sync_warning.setText(
                f'Let op: deze werkmap lijkt in {provider} te staan. Gesynchroniseerde mappen kunnen bestanden heel kort vergrendelen tijdens synchronisatie. '
                'QuietWriter vangt dit zo veel mogelijk op, maar sluit bij onverwachte opslagfouten eerst andere programma’s die dezelfde bestanden gebruiken.'
            )
            self.sync_warning.show()
        else:
            self.sync_warning.clear(); self.sync_warning.hide()

    def choose_root(self):
        p = QFileDialog.getExistingDirectory(self, 'Kies werkmap', self.root.text())
        if p:
            self.root.setText(p)

    def _dictionary_workspace(self) -> Path:
        return Path(self.root.text().strip() or str(Path.home() / 'QuietWriter')) / 'dictionaries'

    def refresh_dictionaries(self, checked=False, preserve_locale=None):
        current = preserve_locale or self.spell_language.currentData() or str(self.settings.value('spell_language', 'nl_NL') or 'nl_NL')
        self.dictionary_catalog = DictionaryCatalog(self._dictionary_workspace())
        self.spell_language.blockSignals(True)
        self.spell_language.clear()
        entries = self.dictionary_catalog.entries()
        for entry in entries:
            self.spell_language.addItem(entry.label, entry.locale)
        idx = self.spell_language.findData(current)
        if idx >= 0:
            self.spell_language.setCurrentIndex(idx)
        elif entries:
            self.spell_language.setCurrentIndex(0)
        self.spell_language.blockSignals(False)
        self.update_dictionary_info()

    def update_dictionary_info(self):
        locale = self.spell_language.currentData()
        entry = self.dictionary_catalog.get(locale) if locale else None
        if not entry:
            self.dictionary_info.setText('Geen woordenboeken gevonden. Installeer bijvoorbeeld ONLYOFFICE, LibreOffice of OpenOffice, of voeg zelf een Hunspell-woordenboek toe.')
            self.remove_dict_btn.setEnabled(False)
            return
        aff = 'met .aff-regels' if entry.aff else 'alleen .dic'
        self.dictionary_info.setText(f'Bron: {entry.source} · {entry.locale} · {aff}\n{entry.dic}')
        self.remove_dict_btn.setEnabled(entry.source == 'Werkmap')

    def choose_dictionary(self):
        p, _ = QFileDialog.getOpenFileName(self, 'Kies Hunspell-woordenboek', str(Path.home()), 'Hunspell woordenboek (*.dic);;Alle bestanden (*)')
        if not p:
            return
        self.dictionary_catalog = DictionaryCatalog(self._dictionary_workspace())
        entry = self.dictionary_catalog.add_custom(Path(p))
        self.refresh_dictionaries(preserve_locale=entry.locale)

    def remove_dictionary(self):
        locale = self.spell_language.currentData()
        entry = self.dictionary_catalog.get(locale) if locale else None
        if not entry or entry.source != 'Werkmap':
            QMessageBox.information(self, 'Woordenboek verwijderen', 'Alleen woordenboeken die je zelf aan QuietWriter hebt toegevoegd kunnen hier worden verwijderd. Woordenboeken van Office-programma’s blijven onaangeroerd.')
            return
        if not confirm(self, 'Woordenboek verwijderen', f'Wil je “{entry.label}” uit de QuietWriter-werkmap verwijderen?'):
            return
        if not self.dictionary_catalog.remove_custom(locale):
            QMessageBox.warning(self, 'Woordenboek verwijderen', 'Het woordenboek kon niet worden verwijderd.')
        self.refresh_dictionaries()

    def open_dictionary_download(self):
        QDesktopServices.openUrl(QUrl(self.DICTIONARY_DOWNLOAD_URL))

    def _populate_models(self, models):
        provider_name = str(self.settings.value('ai_provider', 'ollama') or 'ollama')
        current = self.settings.value('ollama_model', '') if provider_name == 'ollama' else self.settings.value('openrouter_model', '')
        self.model.clear()
        if provider_name == 'ollama':
            self.model.addItems(list(models or []))
        elif current:
            self.model.addItem(str(current))
        if current:
            self.model.setCurrentText(str(current))
        elif self.model.count():
            self.model.setCurrentIndex(0)

    def refresh_models(self):
        self.settings.setValue('ai_provider', self.ai_provider.currentData() or 'ollama')
        self.settings.setValue('ollama_url', self.ollama.text())
        self.settings.setValue('openrouter_api_key', self.openrouter_key.text())
        try:
            provider = ProviderFactory.from_settings(self.settings)
            infos = provider.list_models()
            models = [m['name'] for m in infos]
            current = self.model.currentText()
            self.model.clear(); self.model.addItems(models)
            if current in models:
                self.model.setCurrentText(current)
            elif models:
                self.model.setCurrentIndex(0)
            if self.parent() and hasattr(self.parent(), 'models'):
                self.parent().models = models
        except Exception as exc:
            QMessageBox.warning(self, 'AI', f'Modellen ophalen mislukt:\n\n{exc}')

    def save_settings(self):
        old_root = self.settings.value('workspace', str(Path.home()/APP_NAME))
        self.settings.setValue('theme', self.theme.currentText())
        self.settings.setValue('editor_font', typography_from_values(self.editor_font.currentText(), self.editor_font_size.value()).family)
        self.settings.setValue('editor_font_size', int(self.editor_font_size.value()))
        self.settings.setValue('autosave', self.autosave.isChecked())
        self.settings.setValue('workspace', self.root.text())
        provider = self.ai_provider.currentData() or 'ollama'
        self.settings.setValue('ai_provider', provider)
        self.settings.setValue('ollama_url', self.ollama.text())
        self.settings.setValue('openrouter_api_key', self.openrouter_key.text())
        if provider == 'openrouter': self.settings.setValue('openrouter_model', self.model.currentText())
        else: self.settings.setValue('ollama_model', self.model.currentText())
        self.settings.setValue('cover_header_template', self.cover_template.text().strip() or '/{slug}.jpg')
        self.settings.setValue('spell_enabled', self.spell_enabled.isChecked())
        self.settings.setValue('spell_language', self.spell_language.currentData() or '')
        self.original_theme = self.theme.currentText()
        self.original_editor_font = self.editor_font.currentText()
        self.original_editor_size = int(self.editor_font_size.value())
        self._preview_theme = self.original_theme
        if self.parent() and hasattr(self.parent(), 'settings_saved'):
            self.parent().settings_saved(old_root)

    def begin_session(self):
        self.original_theme = self.settings.value('theme', 'Helder')
        self.original_editor_font = str(self.settings.value('editor_font', 'Merriweather') or 'Merriweather')
        self.original_editor_size = int(self.settings.value('editor_font_size', 15, int) or 15)
        self._preview_theme = str(self.original_theme or 'Helder')
        for widget in (self.theme, self.editor_font, self.editor_font_size): widget.blockSignals(True)
        self.theme.setCurrentText(str(self.original_theme or 'Helder'))
        self.editor_font.setCurrentText(self.original_editor_font)
        self.editor_font_size.setValue(self.original_editor_size)
        for widget in (self.theme, self.editor_font, self.editor_font_size): widget.blockSignals(False)
        self.autosave.setChecked(self.settings.value('autosave', True, bool))
        self.root.setText(self.settings.value('workspace', str(Path.home()/APP_NAME)))
        self.cover_template.setText(self.settings.value('cover_header_template', '/{slug}.jpg'))
        provider = str(self.settings.value('ai_provider', 'ollama') or 'ollama')
        idx = self.ai_provider.findData(provider); self.ai_provider.setCurrentIndex(max(0, idx))
        self.ollama.setText(self.settings.value('ollama_url', 'http://127.0.0.1:11434'))
        self.openrouter_key.setText(self.settings.value('openrouter_api_key', ''))
        self._populate_models(self.available_models)
        self.spell_enabled.setChecked(self.settings.value('spell_enabled', True, bool))
        self.refresh_dictionaries(preserve_locale=str(self.settings.value('spell_language', 'nl_NL') or 'nl_NL'))
        self.update_sync_warning()


class SearchPanel(QWidget):
    open_match = __import__('PySide6.QtCore').QtCore.Signal(object)
    request_next = __import__('PySide6.QtCore').QtCore.Signal()
    request_replace = __import__('PySide6.QtCore').QtCore.Signal()
    request_replace_all = __import__('PySide6.QtCore').QtCore.Signal()

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(18,18,18,18)
        lab = QLabel(tr('search.title', 'Zoeken en vervangen')); lab.setObjectName('sectionTitle')
        self.scope = QComboBox(); self.scope.addItems(['Huidig hoofdstuk', 'Huidige sectie', 'Hele boek'])
        self.query = QLineEdit(); self.query.setPlaceholderText('Zoeken…'); self.query.setClearButtonEnabled(True)
        self.replace = QLineEdit(); self.replace.setPlaceholderText('Vervangen door…'); self.replace.setClearButtonEnabled(True)
        options = QHBoxLayout()
        self.case_sensitive = QCheckBox('Hoofdlettergevoelig')
        self.whole_word = QCheckBox('Heel woord')
        options.addWidget(self.case_sensitive); options.addWidget(self.whole_word); options.addStretch()
        self.summary = QLabel(''); self.summary.setObjectName('muted')
        self.empty = QLabel(tr('search.no_results', 'Geen resultaten gevonden.')); self.empty.setObjectName('muted'); self.empty.setAlignment(Qt.AlignCenter); self.empty.hide()
        self.results = QListWidget()
        self.results.itemActivated.connect(lambda i: self.open_match.emit(i.data(Qt.UserRole)))
        buttons = QHBoxLayout()
        self.next_btn = QPushButton(tr('search.next','Volgende')); self.next_btn.clicked.connect(self.request_next.emit)
        self.replace_btn = QPushButton(tr('search.replace','Vervangen')); self.replace_btn.clicked.connect(self.request_replace.emit)
        self.replace_all_btn = QPushButton(tr('search.replace_all','Alles vervangen')); self.replace_all_btn.clicked.connect(self.request_replace_all.emit)
        buttons.addWidget(self.next_btn); buttons.addWidget(self.replace_btn); buttons.addWidget(self.replace_all_btn)
        lay.addWidget(lab); lay.addWidget(self.scope); lay.addWidget(self.query); lay.addLayout(options)
        lay.addWidget(self.summary); lay.addWidget(self.empty); lay.addWidget(self.results, 1)
        lay.addWidget(QLabel('Vervangen door')); lay.addWidget(self.replace); lay.addLayout(buttons)

    def show_results(self, rows):
        self.results.clear()
        active = bool(self.query.text().strip())
        self.empty.setVisible(active and not rows)
        self.results.setVisible(bool(rows) or not active)
        self.summary.setText((f'{len(rows)} resultaat' if len(rows) == 1 else f'{len(rows)} resultaten') if active else '')
        for row in rows:
            cid, title, snippet, start, length = row
            item = QListWidgetItem(f'{title}\n{snippet}')
            item.setData(Qt.UserRole, (cid, start, length))
            self.results.addItem(item)


class ManuscriptTree(QTreeWidget):
    chapterDropped = Signal(str, str, str, bool)

    MIME_TYPE = 'application/x-quietwriter-chapter'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHeaderHidden(True)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.Fixed)
        self.header().setMinimumSectionSize(0)
        self.setColumnWidth(1, 38)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(False)
        # Crucial: do NOT use InternalMove. QTreeWidget would then mutate its own
        # item model during a drag, independently of book.json. QuietWriter uses
        # a custom QDrag and only changes the book model after a validated drop.
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setRootIsDecorated(False)
        self.setItemsExpandable(False)
        self.setIndentation(14)
        self.setUniformRowHeights(True)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self._drag_allowed = False
        self._drag_item = None
        self._drop_item = None
        self._drop_before = True


    def mouseMoveEvent(self, event):
        idx = self.indexAt(event.position().toPoint())
        item = self.itemAt(event.position().toPoint())
        data = item.data(0, Qt.UserRole) if item else None
        over_handle = bool(idx.isValid() and idx.column() == 1 and data and data[0] == 'chapter')
        self.viewport().setCursor(Qt.OpenHandCursor if over_handle else Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        idx = self.indexAt(event.position().toPoint())
        data = item.data(0, Qt.UserRole) if item else None
        # Only the six-dot handle in column 1 can start a drag.
        self._drag_allowed = bool(item and idx.isValid() and idx.column() == 1 and data and data[0] == 'chapter')
        self._drag_item = item if self._drag_allowed else None
        if self._drag_allowed:
            self.viewport().setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def startDrag(self, supportedActions):
        if not self._drag_allowed or not self._drag_item:
            return
        data = self._drag_item.data(0, Qt.UserRole)
        if not data or data[0] != 'chapter':
            return
        mime = QMimeData()
        mime.setData(self.MIME_TYPE, data[1].encode('utf-8'))
        drag = QDrag(self)
        drag.setMimeData(mime)
        # Small neutral drag image; this does not detach/move the tree item.
        pix = QPixmap(max(180, self.visualItemRect(self._drag_item).width()), max(28, self.visualItemRect(self._drag_item).height()))
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setPen(QColor(THEMES.get(str(QSettings('QuietWriter','QuietWriter').value('theme','Helder')), THEMES['Helder'])['muted']))
        painter.drawText(pix.rect().adjusted(8, 0, -8, 0), Qt.AlignVCenter | Qt.AlignLeft, self._drag_item.text(0))
        painter.end()
        drag.setPixmap(pix)
        drag.exec(Qt.MoveAction)
        self.viewport().setCursor(Qt.ArrowCursor)
        self._drag_allowed = False
        self._drag_item = None
        self._drop_item = None
        self.viewport().update()

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if not event.mimeData().hasFormat(self.MIME_TYPE):
            event.ignore(); return
        target = self.itemAt(event.position().toPoint())
        if not target:
            self._drop_item = None; self.viewport().update(); event.ignore(); return
        tdata = target.data(0, Qt.UserRole)
        source_id = bytes(event.mimeData().data(self.MIME_TYPE)).decode('utf-8', errors='ignore')
        if not tdata or tdata[0] not in ('chapter', 'section') or (tdata[0] == 'chapter' and tdata[1] == source_id):
            self._drop_item = None; self.viewport().update(); event.ignore(); return
        rect = self.visualItemRect(target)
        self._drop_item = target
        self._drop_before = event.position().y() < rect.center().y()
        self.viewport().update()
        event.setDropAction(Qt.MoveAction)
        event.accept()

    def dragLeaveEvent(self, event):
        self._drop_item = None
        self.viewport().update()
        event.accept()

    def dropEvent(self, event):
        try:
            if not event.mimeData().hasFormat(self.MIME_TYPE):
                event.ignore(); return
            source_id = bytes(event.mimeData().data(self.MIME_TYPE)).decode('utf-8', errors='ignore')
            target = self._drop_item or self.itemAt(event.position().toPoint())
            if not source_id or not target:
                event.ignore(); return
            tdata = target.data(0, Qt.UserRole)
            if not tdata or tdata[0] not in ('chapter', 'section'):
                event.ignore(); return
            self.chapterDropped.emit(source_id, tdata[0], tdata[1], self._drop_before)
            event.setDropAction(Qt.MoveAction)
            event.accept()
        finally:
            self._drag_item = None
            self._drop_item = None
            self._drag_allowed = False
            self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._drop_item:
            r = self.visualItemRect(self._drop_item)
            y = r.top() if self._drop_before else r.bottom()
            p = QPainter(self.viewport())
            p.setPen(QPen(self.palette().color(QPalette.Highlight), 3))
            p.drawLine(8, y, max(8, self.viewport().width() - 8), y)


class SuggestionButtons(QWidget):
    """Compact suggestion list: one real row per word, no scroll area."""
    chosen = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)
        self._buttons = []
        self.selected = ''

    def clear(self):
        self.selected = ''
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._buttons = []
        self.setFixedHeight(0)

    def set_suggestions(self, words):
        self.clear()
        for index, word in enumerate(list(words)[:8]):
            button = QPushButton(word)
            button.setObjectName('suggestionButton')
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setFixedHeight(30)
            button.clicked.connect(lambda checked=False, w=word: self._select(w))
            self._layout.addWidget(button)
            self._buttons.append(button)
            if index == 0:
                button.setChecked(True)
                self.selected = word
        self.setFixedHeight(len(self._buttons) * 32)

    def _select(self, word):
        self.selected = word
        self.chosen.emit(word)



class SpellPanel(QWidget):
    def __init__(self, editor_page):
        super().__init__()
        self.editor_page = editor_page
        self.rows = []
        self.index = 0
        lay = QVBoxLayout(self); lay.setContentsMargins(18,18,18,18); lay.setSpacing(10)
        title = QLabel(tr('spell.title','Spellingscontrole')); title.setObjectName('sectionTitle')
        self.status = QLabel(''); self.status.setObjectName('muted'); self.status.setWordWrap(True)
        self.word = QLabel(''); self.word.setObjectName('title')
        self.suggestions = SuggestionButtons()
        buttons = QVBoxLayout(); buttons.setSpacing(6)
        self.change_btn = QPushButton(tr('spell.change','Wijzigen')); self.change_btn.clicked.connect(self.change)
        self.ignore_btn = QPushButton(tr('spell.ignore','Negeren')); self.ignore_btn.clicked.connect(self.ignore)
        self.ignore_all_btn = QPushButton(tr('spell.ignore_all','Alles negeren')); self.ignore_all_btn.clicked.connect(self.ignore_all)
        self.ignore_always_btn = QPushButton(tr('spell.ignore_always','Altijd negeren')); self.ignore_always_btn.clicked.connect(self.ignore_always)
        self.add_btn = QPushButton(tr('spell.add','Toevoegen aan woordenboek')); self.add_btn.clicked.connect(self.add_personal)
        for b in (self.change_btn, self.ignore_btn, self.ignore_all_btn, self.ignore_always_btn, self.add_btn):
            buttons.addWidget(b)
        lay.addWidget(title); lay.addWidget(self.status); lay.addWidget(self.word); lay.addWidget(self.suggestions)
        lay.addSpacing(8); lay.addStretch(1); lay.addLayout(buttons)
        self.refresh()

    def refresh(self):
        d = self.editor_page.dictionary
        if not d.words:
            self.rows=[]; self.index=0; self.status.setText(tr('spell.no_dictionary','Er is nog geen woordenboek ingesteld.')); self.word.clear(); self.suggestions.clear(); return
        title_rows = [('title', w, a, b) for (w,a,b) in d.misspellings(self.editor_page.chapter_title.text())]
        body_rows = [('body', w, a, b) for (w,a,b) in d.misspellings(self.editor_page.editor.toPlainText())]
        self.rows = title_rows + body_rows
        if not self.rows:
            self.index=0; self.status.setText(tr('spell.no_errors','Geen spelfouten gevonden in dit hoofdstuk.')); self.word.clear(); self.suggestions.clear(); return
        self.index=min(max(self.index,0),len(self.rows)-1); self.show_current()

    def show_current(self):
        if not self.rows: return
        source,word,start,end=self.rows[self.index]
        where = 'Hoofdstuktitel' if source == 'title' else 'Hoofdstuktekst'
        self.status.setText(f'{self.index+1} van {len(self.rows)} · {where}')
        self.word.setText(word)
        self.suggestions.set_suggestions(self.editor_page.dictionary.suggest(word))
        if source == 'title':
            self.editor_page.chapter_title.setFocus()
            self.editor_page.chapter_title.setSelection(start, end-start)
        else:
            cur=self.editor_page.editor.textCursor(); cur.setPosition(start); cur.setPosition(end,QTextCursor.KeepAnchor); self.editor_page.editor.setTextCursor(cur); self.editor_page.editor.ensureCursorVisible()

    def _advance(self):
        self.refresh()
        if self.rows:
            self.index=min(self.index,len(self.rows)-1); self.show_current()

    def change(self):
        if not self.rows or not self.suggestions.selected: return
        source,_,start,end=self.rows[self.index]
        if source == 'title':
            text = self.editor_page.chapter_title.text()
            self.editor_page.chapter_title.setText(text[:start] + self.suggestions.selected + text[end:])
            self.editor_page.rename_current()
        else:
            cur=self.editor_page.editor.textCursor(); cur.setPosition(start); cur.setPosition(end,QTextCursor.KeepAnchor); cur.insertText(self.suggestions.selected)
        self.editor_page.highlighter.rehighlight(); self._advance()

    def ignore(self):
        """Sla alleen deze ene vindplaats over; niets wordt aan lijsten toegevoegd."""
        if not self.rows: return
        self.index += 1
        if self.index >= len(self.rows): self.index=0
        self.show_current()

    def ignore_all(self):
        """Negeer dit woord alleen zolang QuietWriter draait."""
        if not self.rows: return
        self.editor_page.dictionary.ignore(self.rows[self.index][1]); self.editor_page.highlighter.rehighlight(); self._advance()

    def ignore_always(self):
        """Persistente aparte negeerlijst; het woord wordt geen persoonlijk woordenboekwoord."""
        if not self.rows: return
        self.editor_page.dictionary.ignore_always(self.rows[self.index][1]); self.editor_page.highlighter.rehighlight(); self._advance()

    def add_personal(self):
        if not self.rows: return
        self.editor_page.dictionary.add_personal(self.rows[self.index][1]); self.editor_page.highlighter.rehighlight(); self._advance()


class HistoryPanel(QWidget):
    versionSelected = Signal(str)
    currentSelected = Signal()
    createRequested = Signal()
    starChanged = Signal(str, bool)

    def __init__(self, editor_page):
        super().__init__()
        self.editor_page = editor_page
        self.book = None
        self.rows = []
        lay = QVBoxLayout(self); lay.setContentsMargins(18,18,18,18); lay.setSpacing(10)
        title = QLabel('Versiegeschiedenis'); title.setObjectName('sectionTitle')
        self.starred_only = QCheckBox('Alleen versies met ster')
        self.starred_only.stateChanged.connect(self.refresh)
        self.create_btn = QPushButton('+ Nieuwe versie maken'); self.create_btn.setObjectName('primaryButton')
        self.create_btn.clicked.connect(self.createRequested.emit)
        self.list = QListWidget()
        self.list.itemClicked.connect(self._clicked)
        self.list.currentItemChanged.connect(self._selection_changed)
        self.star_btn = QPushButton('☆ Ster toevoegen')
        self.star_btn.clicked.connect(self._toggle_star)
        self.star_btn.setEnabled(False)
        self.empty = QLabel('Nog geen oudere versies beschikbaar.')
        self.empty.setObjectName('muted'); self.empty.setAlignment(Qt.AlignCenter); self.empty.setWordWrap(True)
        lay.addWidget(title); lay.addWidget(self.starred_only); lay.addWidget(self.create_btn)
        lay.addWidget(self.empty); lay.addWidget(self.list, 1); lay.addWidget(self.star_btn)

    def set_book(self, book):
        self.book = book
        self.refresh()

    @staticmethod
    def _format_stamp(value: str) -> tuple[str, str]:
        try:
            dt = datetime.fromisoformat(value)
        except Exception:
            dt = datetime.now()
        months = ['januari','februari','maart','april','mei','juni','juli','augustus','september','oktober','november','december']
        date_label = f'{dt.day} {months[dt.month-1]} {dt.year}'
        return date_label, dt.strftime('%H:%M')

    def refresh(self, *_):
        self.list.clear(); self.rows = []
        if not self.book:
            self.empty.show(); self.star_btn.setEnabled(False); return
        try:
            rows = self.editor_page.main.library.list_versions(self.book)
        except Exception:
            rows = []
        if self.starred_only.isChecked():
            rows = [r for r in rows if r.get('starred')]
        self.rows = rows
        self.empty.setVisible(not rows)
        # The live manuscript is always available as a first item.
        current = QListWidgetItem('Huidige versie')
        current.setData(Qt.UserRole, None)
        current.setToolTip('Terug naar de huidige, bewerkbare versie')
        self.list.addItem(current)
        last_group = None
        for row in rows:
            date_label, time_label = self._format_stamp(row['created_at'])
            group = 'Vandaag' if date_label == self._format_stamp(datetime.now().isoformat())[0] else date_label
            if group != last_group:
                header = QListWidgetItem(group.upper())
                header.setFlags(Qt.NoItemFlags)
                header.setData(Qt.UserRole, '__header__')
                self.list.addItem(header); last_group = group
            star = '★' if row.get('starred') else '☆'
            kind = {'daily':'Dagarchief', 'manual':'Handmatig', 'pre_restore':'Voor herstel', 'chapter_delete':'Voor verwijderen hoofdstuk'}.get(row.get('kind'), 'Versie')
            text = f'{star}  {time_label}  ·  {kind}\n{row.get("chapters",0)} hoofdstukken · {row.get("words",0):,} woorden'.replace(',', '.')
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, row['id'])
            item.setData(Qt.UserRole + 1, bool(row.get('starred')))
            self.list.addItem(item)
        self.star_btn.setEnabled(False)

    def select_version(self, version_id: str | None):
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item.data(Qt.UserRole) == version_id:
                self.list.setCurrentItem(item); return

    def _clicked(self, item):
        data = item.data(Qt.UserRole)
        if data == '__header__': return
        if data is None:
            self.currentSelected.emit()
        elif data:
            self.versionSelected.emit(str(data))

    def _selection_changed(self, current, previous):
        if not current:
            self.star_btn.setEnabled(False); return
        data = current.data(Qt.UserRole)
        if not data or data == '__header__':
            self.star_btn.setEnabled(False); return
        starred = bool(current.data(Qt.UserRole + 1))
        self.star_btn.setEnabled(True)
        self.star_btn.setText('★ Ster verwijderen' if starred else '☆ Ster toevoegen')

    def _toggle_star(self):
        item = self.list.currentItem()
        if not item: return
        version_id = item.data(Qt.UserRole)
        if not version_id or version_id == '__header__': return
        starred = not bool(item.data(Qt.UserRole + 1))
        self.starChanged.emit(str(version_id), starred)



class EditorPage(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.book = None; self.chapter = None; self.dirty = False
        self.preview_live_book = None; self.preview_version_id = None; self.preview_return_chapter_id = None
        self.autosave_timer = QTimer(self); self.autosave_timer.setSingleShot(True); self.autosave_timer.setInterval(3000); self.autosave_timer.timeout.connect(self.save)

        root = QHBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.left_split = QSplitter(Qt.Horizontal)
        self.manuscript = QWidget(); self.manuscript.setObjectName('panel'); self.manuscript.setMinimumWidth(250); ml = QVBoxLayout(self.manuscript); ml.setContentsMargins(14,14,14,14)
        head = QHBoxLayout(); title = QLabel(tr('editor.contents', 'Inhoud')); title.setObjectName('sectionTitle')
        self.add_content_button = QPushButton(tr('editor.add', '+ Toevoegen')); self.add_content_button.setObjectName('secondaryButton'); self.add_content_button.clicked.connect(self.add_menu)
        head.addWidget(title); head.addStretch(); head.addWidget(self.add_content_button)
        self.tree = ManuscriptTree(); self.tree.setObjectName('manuscriptTree'); self.tree.itemClicked.connect(self.tree_clicked); self.tree.chapterDropped.connect(self.move_chapter); self.tree.setContextMenuPolicy(Qt.CustomContextMenu); self.tree.customContextMenuRequested.connect(self.tree_context_menu)
        self.book_words = QLabel('0 woorden'); self.book_words.setObjectName('muted')
        ml.addLayout(head); ml.addWidget(self.tree); ml.addWidget(self.book_words)

        self.center = QWidget(); cl = QVBoxLayout(self.center); cl.setContentsMargins(0,0,0,0); cl.setSpacing(0)
        self.history_banner = QFrame(); self.history_banner.setObjectName('historyBanner'); hb = QHBoxLayout(self.history_banner); hb.setContentsMargins(14,8,14,8)
        self.history_banner_label = QLabel(''); self.history_banner_label.setObjectName('historyBannerLabel')
        self.history_restore_btn = QPushButton('Deze versie herstellen'); self.history_restore_btn.setObjectName('restoreButton'); self.history_restore_btn.clicked.connect(self.restore_preview_version)
        self.history_exit_btn = QPushButton('Afsluiten'); self.history_exit_btn.setObjectName('historyExitButton'); self.history_exit_btn.clicked.connect(self.exit_history_preview)
        hb.addWidget(self.history_banner_label); hb.addStretch(); hb.addWidget(self.history_restore_btn); hb.addWidget(self.history_exit_btn)
        self.history_banner.hide()
        topbar = QFrame(); topbar.setObjectName('editorTopbar'); tl = QHBoxLayout(topbar); tl.setContentsMargins(14,8,18,8)
        undo = QPushButton(); self.undo_button = undo; undo.setProperty('iconName','undo'); undo.setObjectName('compactButton'); undo.setIcon(icon('undo')); undo.setIconSize(QSize(22,22)); undo.setToolTip('Ongedaan maken')
        redo = QPushButton(); self.redo_button = redo; redo.setProperty('iconName','redo'); redo.setObjectName('compactButton'); redo.setIcon(icon('redo')); redo.setIconSize(QSize(22,22)); redo.setToolTip('Opnieuw')
        self.book_title_label = QLabel(''); self.book_title_label.setObjectName('bookTitleLabel')
        self.autosave_status = QLabel(''); self.autosave_status.setObjectName('autosaveStatus')
        tl.addWidget(undo); tl.addWidget(redo); tl.addSpacing(8); tl.addWidget(self.book_title_label); tl.addStretch(); tl.addWidget(self.autosave_status)
        self.chapter_title = QLineEdit(); self.chapter_title.setPlaceholderText('Hoofdstuktitel'); self.chapter_title.setAlignment(Qt.AlignCenter); self.chapter_title.setObjectName('chapterTitle')
        _writing_typography = WritingTypography.from_settings(QSettings('QuietWriter','QuietWriter'))
        self.chapter_title.setFont(_writing_typography.title_font())
        self.chapter_title.editingFinished.connect(self.rename_current)
        self.editor = ManuscriptEditor(); self.editor.setObjectName('editor'); self.editor.textChanged.connect(self.on_text_changed)
        undo.clicked.connect(self.editor.undo); redo.clicked.connect(self.editor.redo)
        self.dictionary = WordDictionary()
        self.dictionary.load_personal(self.main.library.dict_dir / 'persoonlijk.txt')
        self.dictionary.load_persistent_ignored(self.main.library.dict_dir / 'altijd_negeren.txt')
        self.highlighter = SpellHighlighter(self.editor.document(), self.dictionary)
        self.load_dictionary_from_settings()
        cl.addWidget(self.history_banner); cl.addWidget(topbar); cl.addWidget(self.chapter_title); cl.addWidget(self.editor)

        self.right = QStackedWidget(); self.right.setObjectName('panel'); self.right.setMinimumWidth(300)
        self.search = SearchPanel(); self.ai = AIPanel(main); self.spell = SpellPanel(self); self.history = HistoryPanel(self)
        self.right.addWidget(self.search); self.right.addWidget(self.ai); self.right.addWidget(self.spell); self.right.addWidget(self.history)
        self.history.versionSelected.connect(self.enter_history_preview)
        self.history.currentSelected.connect(self.exit_history_preview)
        self.history.createRequested.connect(self.create_manual_version)
        self.history.starChanged.connect(self.set_version_starred)
        self.search.query.textChanged.connect(lambda _: self.do_search()); self.search.scope.currentTextChanged.connect(lambda _: self.do_search())
        self.search.case_sensitive.stateChanged.connect(lambda _: self.do_search()); self.search.whole_word.stateChanged.connect(lambda _: self.do_search())
        self.search.open_match.connect(self.open_search_match); self.search.request_next.connect(self.search_next); self.search.request_replace.connect(self.replace_current_match); self.search.request_replace_all.connect(self.replace_all_matches)

        self.left_split.addWidget(self.manuscript); self.left_split.addWidget(self.center); self.left_split.addWidget(self.right)
        self.left_split.setStretchFactor(0,0); self.left_split.setStretchFactor(1,1); self.left_split.setStretchFactor(2,0)
        # Visible side panels may never collapse to a 1-2 px sliver. They are
        # collapsed explicitly by hiding the widget, not by shrinking it in QSplitter.
        self.left_split.setCollapsible(0, False); self.left_split.setCollapsible(1, False); self.left_split.setCollapsible(2, False)
        self._manuscript_width = 280
        self._right_width = 360
        self.left_split.setSizes([self._manuscript_width, 800, self._right_width])
        self.left_split.splitterMoved.connect(self._remember_panel_widths)
        self.left_split.splitterMoved.connect(lambda *_: self._position_contents_edge_button())
        root.addWidget(self.left_split)

        # Het Inhoud-tabje wordt bewust pas NA de splitter aangemaakt. Het is een
        # overlay-child van EditorPage en ligt daardoor in de stacking order boven
        # het volledige splitteroppervlak (dus ook boven de hoofdstukkenboom).
        # Bij een ingeklapt Inhoud-paneel zit de vlakke linkerzijde naadloos tegen
        # de linker navigatie-/editorgrens aan.
        self.contents_edge_button = QPushButton(self)
        self.contents_edge_button.setObjectName('contentsEdgeButton')
        self.contents_edge_button.setProperty('iconName','panel-left'); self.contents_edge_button.setIcon(icon('panel-left'))
        self.contents_edge_button.setIconSize(QSize(20,20))
        self.contents_edge_button.setFixedSize(30, 46)
        self.contents_edge_button.clicked.connect(self.toggle_manuscript)
        self.contents_edge_button.setToolTip(tr('tool.hide_contents', 'Inhoud verbergen'))
        self.contents_edge_button.show()
        self.contents_edge_button.raise_()
        QTimer.singleShot(0, self._position_contents_edge_button)

    def load_book(self, book):
        self.save(); self.book = book; self.chapter = None; self.book_title_label.setText(book.title); self.populate_tree()
        first = next((c for s in book.sections for c in s.chapters), None)
        if first: self.open_chapter(first)
        self.main.search_index.rebuild_book(book)
        if hasattr(self, 'history'): self.history.set_book(book)
        if hasattr(self, 'ai'): self.ai.set_book(book)

    def populate_tree(self):
        self.tree.clear()
        if not self.book: return
        for section in self.book.sections:
            if section.id == 'root' and len(self.book.sections)==1:
                for chapter in section.chapters:
                    it = QTreeWidgetItem([chapter.title, '']); it.setData(0, Qt.UserRole, ('chapter', chapter.id)); it.setIcon(1, icon('drag_handle')); it.setTextAlignment(1, Qt.AlignCenter); it.setToolTip(1, tr('editor.drag_chapter', 'Sleep om hoofdstuk te verplaatsen')); self.tree.addTopLevelItem(it)
            else:
                sit = QTreeWidgetItem([section.title, '']); sit.setData(0, Qt.UserRole, ('section', section.id)); sit.setFlags(sit.flags() & ~Qt.ItemIsDragEnabled)
                section_font = QFont(QApplication.font()); section_font.setWeight(QFont.Weight.DemiBold); sit.setFont(0, section_font)
                sit.setForeground(0, QColor(THEMES.get(str(self.main.settings.value('theme','Helder')), THEMES['Helder'])['muted']))
                self.tree.addTopLevelItem(sit)
                for chapter in section.chapters:
                    cit = QTreeWidgetItem([chapter.title, '']); cit.setData(0, Qt.UserRole, ('chapter', chapter.id)); cit.setIcon(1, icon('drag_handle')); cit.setTextAlignment(1, Qt.AlignCenter); cit.setToolTip(1, tr('editor.drag_chapter', 'Sleep om hoofdstuk te verplaatsen')); sit.addChild(cit)
                sit.setExpanded(True)

    def move_chapter(self, chapter_id: str, target_type: str, target_id: str, before: bool):
        if not self.book or self.preview_live_book:
            return
        # Reorder a deep copy first. Only commit it to the live in-memory model after
        # book.json has been persisted successfully. This prevents Dropbox/file-lock
        # failures from making the tree diverge from disk.
        proposed = copy.deepcopy(self.book.sections)
        try:
            changed = reorder_chapter(proposed, chapter_id, DropTarget(target_type, target_id, before))
            if changed:
                shadow = copy.copy(self.book)
                shadow.sections = proposed
                self.main.library.save_manifest(shadow)
                self.book.sections = proposed
        except Exception as exc:
            QMessageBox.critical(self, 'Verplaatsen mislukt',
                                 'Het hoofdstuk is niet verplaatst en de bestaande volgorde is behouden.\n\n' + str(exc))
            self.populate_tree(); self.select_tree_chapter(chapter_id); return
        self.populate_tree(); self.select_tree_chapter(chapter_id)

    def tree_context_menu(self, pos):
        if self.preview_live_book:
            return
        item = self.tree.itemAt(pos)
        if not item or not self.book:
            return
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        menu = QMenu(self)

        if data[0] == 'chapter':
            chapter_id = data[1]
            _, chapter = self.find_chapter(chapter_id)
            if not chapter:
                return
            rename_action = menu.addAction('Hernoemen…')
            duplicate_action = menu.addAction('Dupliceren')
            chosen = menu.exec(self.tree.viewport().mapToGlobal(pos))

            if chosen is rename_action:
                title, ok = QInputDialog.getText(self, 'Hoofdstuk hernoemen', 'Titel:', text=chapter.title)
                if ok and title.strip():
                    self.main.library.rename_chapter(self.book, chapter_id, title)
                    if self.chapter and self.chapter.id == chapter_id:
                        self.chapter_title.setText(title.strip())
                    self.populate_tree(); self.select_tree_chapter(chapter_id)
            elif chosen is duplicate_action:
                self.save()
                copied = self.main.library.duplicate_chapter(self.book, chapter_id)
                self.populate_tree()
                if copied:
                    self.open_chapter(copied); self.select_tree_chapter(copied.id)

        elif data[0] == 'section':
            section_id = data[1]
            sec = next((x for x in self.book.sections if x.id == section_id), None)
            if not sec:
                return
            rename_action = menu.addAction('Sectie hernoemen…')
            delete_action = menu.addAction('Sectie verwijderen…')
            chosen = menu.exec(self.tree.viewport().mapToGlobal(pos))
            if chosen is rename_action:
                title, ok = QInputDialog.getText(self, 'Sectie hernoemen', 'Titel:', text=sec.title)
                if ok and title.strip():
                    self.main.library.rename_section(self.book, section_id, title)
                    self.populate_tree()
            elif chosen is delete_action:
                if sec.chapters:
                    QMessageBox.information(self, 'Sectie verwijderen', 'Verplaats eerst de hoofdstukken uit deze sectie. Een niet-lege sectie wordt niet verwijderd.')
                    return
                if confirm(self, 'Sectie verwijderen', f'Wil je de sectie “{sec.title}” verwijderen?'):
                    self.book.sections = [x for x in self.book.sections if x.id != sec.id]
                    if not self.book.sections:
                        from .storage import Section
                        self.book.sections = [Section(id='root', title='Manuscript')]
                    self.main.library.save_manifest(self.book); self.populate_tree()

    def delete_current_chapter(self):
        if not self.book or not self.chapter or self.preview_live_book:
            return
        total = sum(len(sec.chapters) for sec in self.book.sections)
        if total <= 1:
            QMessageBox.information(self, 'Hoofdstuk verwijderen', 'Het laatste hoofdstuk van een boek kan niet worden verwijderd.')
            return
        chapter = self.chapter
        next_chapter = self.main.library.adjacent_chapter_for_delete(self.book, chapter.id)
        message = (
            f'Weet je zeker dat je “{chapter.title}” wilt verwijderen?\n\n'
            'Er wordt eerst een versie in de versiegeschiedenis gemaakt, zodat je de inhoud later kunt herstellen.'
        )
        if not confirm(self, 'Hoofdstuk verwijderen', message):
            return
        self.save()
        try:
            self.main.library.create_version(self.book, kind='chapter_delete')
            removed = self.main.library.delete_chapter(self.book, chapter.id)
        except Exception as exc:
            QMessageBox.critical(self, 'Hoofdstuk verwijderen', f'Verwijderen is mislukt.\n\n{exc}')
            return
        if not removed:
            QMessageBox.warning(self, 'Hoofdstuk verwijderen', 'Het hoofdstuk kon niet worden verwijderd.')
            return
        self.chapter = None; self.dirty = False
        self.populate_tree()
        if next_chapter:
            _, existing = self.find_chapter(next_chapter.id)
            if existing:
                self.open_chapter(existing); self.select_tree_chapter(existing.id)
        self.main.search_index.rebuild_book(self.book)
        self.history.set_book(self.book)
        self.update_counts()
        self.main.sync_tool_buttons()

    def select_tree_chapter(self, cid):
        root=self.tree.invisibleRootItem()
        stack=[root]
        while stack:
            parent=stack.pop()
            for i in range(parent.childCount()):
                item=parent.child(i); data=item.data(0,Qt.UserRole)
                if data and data[0]=='chapter' and data[1]==cid:
                    self.tree.setCurrentItem(item); return
                stack.append(item)

    def load_dictionary_from_settings(self):
        self.dictionary.clear()
        enabled = self.main.settings.value('spell_enabled', True, bool)
        if enabled:
            catalog = DictionaryCatalog(self.main.library.dict_dir)
            locale = str(self.main.settings.value('spell_language', 'nl_NL') or 'nl_NL')
            entry = catalog.get(locale)
            path = entry.dic if entry else None
            legacy = str(self.main.settings.value('spell_dictionary','') or '').strip()
            if not path and legacy and Path(legacy).exists():
                path = Path(legacy)
            if path and Path(path).exists():
                try: self.dictionary.load_dic(Path(path))
                except Exception: pass
        # Inline red underlining is passive feedback and remains available even
        # while the spelling panel is closed. Opening the panel is what starts
        # the guided walk-through and text selection.
        self.highlighter.set_active(bool(enabled and self.dictionary.words))

    def find_chapter(self, cid):
        for s in self.book.sections:
            for c in s.chapters:
                if c.id == cid: return s, c
        return None, None

    def tree_clicked(self, item, col):
        data = item.data(0, Qt.UserRole)
        if data and data[0]=='chapter': self.open_chapter_id(data[1])

    def open_chapter_id(self, cid):
        _, c = self.find_chapter(cid)
        if c: self.open_chapter(c)

    def open_chapter(self, chapter):
        self.save(); self.chapter = chapter; self.chapter_title.setText(chapter.title)
        self.editor.blockSignals(True); self.editor.setPlainText(self.main.library.read_chapter(self.book, chapter)); self.editor.blockSignals(False)
        # setPlainText() creates a fresh QTextDocument character stream. Reapply
        # the saved writing typography so the selected font is correct immediately
        # after startup/opening a book, not only after visiting Settings.
        self.editor.apply_typography(WritingTypography.from_settings(self.main.settings))
        self.editor.apply_scene_break_formatting()
        self.dirty = False; self.autosave_status.setText('● Opgeslagen'); self.update_counts(); self.main.sync_tool_buttons()
        if self.right.isVisible() and self.right.currentWidget() is self.spell:
            self.spell.refresh()

    def on_text_changed(self):
        if self.preview_live_book:
            return
        self.dirty = True; self.autosave_status.setText('Niet opgeslagen')
        self.editor.apply_scene_break_formatting(); self.update_counts()
        if self.main.settings.value('autosave', True, bool): self.autosave_timer.start()

    def save(self):
        if self.preview_live_book:
            return
        if self.book and self.chapter and self.dirty:
            self.main.library.save_chapter(self.book, self.chapter, self.editor.toPlainText()); self.dirty = False
            self.main.search_index.rebuild_book(self.book); self.autosave_status.setText('● Opgeslagen · zojuist'); self.update_counts(saved=True)

    def rename_current(self):
        if self.preview_live_book:
            return
        if self.chapter:
            self.chapter.title = self.chapter_title.text().strip() or 'Nieuw hoofdstuk'; self.main.library.save_manifest(self.book); self.populate_tree()

    def update_counts(self, saved=False):
        txt = self.editor.toPlainText(); words = len(txt.split())
        total = 0
        if self.book:
            for section in self.book.sections:
                for chapter in section.chapters:
                    if self.chapter and chapter.id == self.chapter.id:
                        total += words
                    else:
                        try: total += len(self.main.library.read_chapter(self.book, chapter).split())
                        except Exception: pass
        self.book_words.setText(f'{total:,}'.replace(',', '.') + ' woorden')
        chapter_index = 0; chapter_total = 0
        if self.book:
            flat = [c for sec in self.book.sections for c in sec.chapters]
            chapter_total = len(flat)
            if self.chapter:
                chapter_index = next((i+1 for i,c in enumerate(flat) if c.id == self.chapter.id), 0)
        prefix = f'Hoofdstuk {chapter_index} van {chapter_total} · ' if chapter_total else ''
        self.main.status.showMessage(prefix + f'{words:,}'.replace(',', '.') + ' woorden')

    def add_menu(self):
        """Toon een rustige flyout voor Hoofdstuk of Sectie.

        Qt.Popup sluit automatisch wanneer de gebruiker ergens buiten de flyout klikt.
        Daarmee is een aparte Annuleren-knop niet nodig.
        """
        if not self.book or self.preview_live_book:
            return
        if hasattr(self, '_add_flyout') and self._add_flyout:
            self._add_flyout.close()
        popup = QFrame(None, Qt.Popup | Qt.FramelessWindowHint)
        popup.setObjectName('flyout')
        popup.setAttribute(Qt.WA_DeleteOnClose, True)
        lay = QVBoxLayout(popup); lay.setContentsMargins(8,8,8,8); lay.setSpacing(4)
        title = QLabel(tr('editor.add_what', 'Toevoegen')); title.setObjectName('sectionTitle'); lay.addWidget(title)
        chapter_btn = QPushButton(tr('editor.new_chapter', 'Hoofdstuk')); chapter_btn.setObjectName('flyoutButton')
        section_btn = QPushButton(tr('editor.new_section', 'Sectie')); section_btn.setObjectName('flyoutButton')
        lay.addWidget(chapter_btn); lay.addWidget(section_btn)
        shadow = QGraphicsDropShadowEffect(popup); shadow.setBlurRadius(24); shadow.setOffset(0, 7); shadow.setColor(QColor(0,0,0,70)); popup.setGraphicsEffect(shadow)
        chapter_btn.clicked.connect(lambda: (popup.close(), self._create_chapter()))
        section_btn.clicked.connect(lambda: (popup.close(), self._create_section()))
        popup.adjustSize()
        pos = self.add_content_button.mapToGlobal(QPoint(self.add_content_button.width() - popup.sizeHint().width(), self.add_content_button.height() + 6))
        popup.move(pos); popup.show(); popup.raise_()
        self._add_flyout = popup

    def _create_section(self):
        if not self.book or self.preview_live_book:
            return
        title, ok = QInputDialog.getText(self, tr('editor.new_section', 'Nieuwe sectie'), tr('editor.name', 'Naam:'))
        if not ok:
            return
        insert_after = None
        item = self.tree.currentItem()
        if item:
            data = item.data(0, Qt.UserRole)
            if data and data[0] == 'section':
                insert_after = data[1]
            elif data and data[0] == 'chapter':
                sec, _ = self.find_chapter(data[1]); insert_after = sec.id if sec else None
        self.main.library.add_section(self.book, title or tr('editor.new_section', 'Nieuwe sectie'), after_section_id=insert_after)
        self.populate_tree()

    def _create_chapter(self):
        if not self.book or self.preview_live_book:
            return
        section = self.book.sections[-1]
        item = self.tree.currentItem()
        if item:
            data = item.data(0, Qt.UserRole)
            if data and data[0] == 'section':
                section = next((s for s in self.book.sections if s.id == data[1]), section)
            elif data and data[0] == 'chapter':
                found, _ = self.find_chapter(data[1])
                if found:
                    section = found
        title, ok = QInputDialog.getText(self, tr('editor.new_chapter', 'Nieuw hoofdstuk'), tr('editor.title', 'Titel:'))
        if not ok:
            return
        c = self.main.library.add_chapter(self.book, section, title or tr('editor.new_chapter', 'Nieuw hoofdstuk'))
        self.populate_tree(); self.open_chapter(c)

    def insert_scene_break(self):
        if not self.book or not self.chapter or self.preview_live_book:
            return
        cursor = self.editor.textCursor()
        text = self.editor.toPlainText()
        new_text, new_pos = build_scene_break_text(text, cursor.position())
        if new_text == text:
            return
        cursor.beginEditBlock()
        cursor.select(QTextCursor.Document)
        cursor.insertText(new_text)
        cursor.setPosition(min(new_pos, len(new_text)))
        cursor.endEditBlock()
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def show_insert_menu(self):
        if not self.book or self.preview_live_book:
            return
        menu = QMenu(self.main)
        scene = menu.addAction('Scènebreuk')
        scene.setToolTip('Voeg *** toe tussen twee tekstblokken')
        chosen = menu.exec(self.main.insert_button.mapToGlobal(self.main.insert_button.rect().bottomLeft()))
        if chosen is scene:
            self.insert_scene_break()

    def create_manual_version(self):
        live = self.preview_live_book or self.book
        if not live:
            return
        if self.preview_live_book:
            self.exit_history_preview()
            live = self.book
        self.save()
        try:
            row = self.main.library.create_version(live, kind='manual')
            self.history.set_book(live)
            self.history.select_version(row['id'])
            self.main.status.showMessage('Nieuwe versie opgeslagen.', 3500)
        except Exception as exc:
            QMessageBox.critical(self, 'Versie maken', f'De versie kon niet worden gemaakt.\n\n{exc}')

    def set_version_starred(self, version_id: str, starred: bool):
        live = self.preview_live_book or self.book
        if not live:
            return
        try:
            self.main.library.set_version_starred(live, version_id, starred)
            self.history.set_book(live)
            self.history.select_version(version_id)
        except Exception as exc:
            QMessageBox.critical(self, 'Versiegeschiedenis', f'De ster kon niet worden opgeslagen.\n\n{exc}')

    def _history_label(self, row: dict) -> str:
        try:
            dt = datetime.fromisoformat(row['created_at'])
            months = ['januari','februari','maart','april','mei','juni','juli','augustus','september','oktober','november','december']
            return f'{dt:%H:%M}, {dt.day} {months[dt.month-1]} {dt.year}'
        except Exception:
            return row.get('created_at', 'Oudere versie')

    def enter_history_preview(self, version_id: str):
        live = self.preview_live_book or self.book
        if not live:
            return
        # Switching from one historical version to another does not touch disk.
        if not self.preview_live_book:
            self.save()
            self.preview_live_book = live
            self.preview_return_chapter_id = self.chapter.id if self.chapter else None
        try:
            snapshot = self.main.library.load_version(self.preview_live_book, version_id)
            row = next((r for r in self.main.library.list_versions(self.preview_live_book) if r['id'] == version_id), None)
        except Exception as exc:
            QMessageBox.critical(self, 'Versiegeschiedenis', f'De gekozen versie kon niet worden geopend.\n\n{exc}')
            if self.preview_live_book:
                self.exit_history_preview()
            return
        self.preview_version_id = version_id
        self.book = snapshot
        self.chapter = None; self.dirty = False
        self.book_title_label.setText(snapshot.title)
        self.editor.setReadOnly(True); self.chapter_title.setReadOnly(True); self.tree.setDragEnabled(False)
        self.history_banner_label.setText('Historische versie · ' + self._history_label(row or {'created_at': ''}))
        self.history_banner.show()
        self.populate_tree()
        wanted = self.preview_return_chapter_id
        chapter = None
        if wanted:
            _, chapter = self.find_chapter(wanted)
        if chapter is None:
            chapter = next((c for sec in snapshot.sections for c in sec.chapters), None)
        if chapter:
            self.open_chapter(chapter); self.select_tree_chapter(chapter.id)
        self.history.set_book(self.preview_live_book)
        self.history.select_version(version_id)
        self.main.sync_tool_buttons()

    def exit_history_preview(self):
        if not self.preview_live_book:
            return
        live = self.preview_live_book
        wanted = self.preview_return_chapter_id
        self.preview_live_book = None; self.preview_version_id = None; self.preview_return_chapter_id = None
        self.book = live; self.chapter = None; self.dirty = False
        self.editor.setReadOnly(False); self.chapter_title.setReadOnly(False); self.tree.setDragEnabled(True)
        self.history_banner.hide(); self.book_title_label.setText(live.title); self.populate_tree()
        chapter = None
        if wanted:
            _, chapter = self.find_chapter(wanted)
        if chapter is None:
            chapter = next((c for sec in live.sections for c in sec.chapters), None)
        if chapter:
            self.open_chapter(chapter); self.select_tree_chapter(chapter.id)
        self.history.set_book(live); self.history.select_version(None)
        self.main.sync_tool_buttons()

    def restore_preview_version(self):
        if not self.preview_live_book or not self.preview_version_id:
            return
        live = self.preview_live_book
        version_id = self.preview_version_id
        if not confirm(self, 'Versie herstellen',
                       'Wil je deze versie herstellen?\n\nDe huidige versie wordt eerst automatisch veiliggesteld, zodat je ook deze herstelactie later kunt terugdraaien.'):
            return
        try:
            restored = self.main.library.restore_version(live, version_id)
        except Exception as exc:
            QMessageBox.critical(self, 'Versie herstellen', f'Herstellen is mislukt. De huidige versie is niet bewust overschreven.\n\n{exc}')
            return
        self.preview_live_book = None; self.preview_version_id = None; self.preview_return_chapter_id = None
        self.editor.setReadOnly(False); self.chapter_title.setReadOnly(False); self.tree.setDragEnabled(True); self.history_banner.hide()
        self.load_book(restored)
        self.history.set_book(restored)
        self.main.start.refresh()
        self.main.status.showMessage('De gekozen versie is hersteld.', 4500)

    def show_history(self):
        live = self.preview_live_book or self.book
        if live:
            self.history.set_book(live)
            self.history.select_version(self.preview_version_id if self.preview_live_book else None)
        self._toggle_right_widget(self.history, self.history.list)

    def close_book(self):
        if self.preview_live_book:
            self.exit_history_preview()
        self.save()
        self.book = None
        self.chapter = None
        self.dirty = False
        self.tree.clear()
        self.chapter_title.clear()
        self.book_title_label.clear()
        self.editor.blockSignals(True); self.editor.clear(); self.editor.blockSignals(False)
        self.book_words.setText('0 woorden')
        self.right.hide()
        if hasattr(self, 'ai'): self.ai.set_book(None)
        self._set_spell_active(False)
        self.main.status.clearMessage()

    def _chapters_in_scope(self):
        if not self.book or not self.chapter: return []
        scope=self.search.scope.currentText()
        if scope=='Huidig hoofdstuk': return [self.chapter]
        if scope=='Huidige sectie':
            section,_=self.find_chapter(self.chapter.id); return list(section.chapters) if section else [self.chapter]
        return [c for sec in self.book.sections for c in sec.chapters]

    def _search_regex(self):
        q=self.search.query.text()
        if not q: return None
        pattern=re.escape(q)
        if self.search.whole_word.isChecked(): pattern=r'\b'+pattern+r'\b'
        flags=0 if self.search.case_sensitive.isChecked() else re.IGNORECASE
        return re.compile(pattern,flags)

    def collect_search_matches(self):
        rx=self._search_regex()
        if not rx: return []
        rows=[]
        for ch in self._chapters_in_scope():
            text=self.editor.toPlainText() if self.chapter and ch.id==self.chapter.id else self.main.library.read_chapter(self.book,ch)
            for m in rx.finditer(text):
                a=max(0,m.start()-40); b=min(len(text),m.end()+60); snippet=text[a:b].replace('\n',' ')
                rows.append((ch.id,ch.title,snippet,m.start(),m.end()-m.start()))
        return rows

    def do_search(self):
        self.search.show_results(self.collect_search_matches())

    def open_search_match(self, match):
        cid,start,length=match
        if not self.chapter or self.chapter.id!=cid: self.open_chapter_id(cid)
        cur=self.editor.textCursor(); cur.setPosition(start); cur.setPosition(start+length,QTextCursor.KeepAnchor); self.editor.setTextCursor(cur); self.editor.ensureCursorVisible()

    def search_next(self):
        rows=self.collect_search_matches()
        if not rows: return
        cid=self.chapter.id if self.chapter else None; pos=self.editor.textCursor().selectionEnd()
        target=None
        for row in rows:
            if row[0]==cid and row[3]>=pos: target=row; break
        if target is None: target=rows[0]
        self.open_search_match((target[0],target[3],target[4]))

    def replace_current_match(self):
        q=self.search.query.text()
        if not q: return
        cur=self.editor.textCursor()
        selected=cur.selectedText()
        good = selected == q if self.search.case_sensitive.isChecked() else selected.casefold()==q.casefold()
        if not good:
            self.search_next(); return
        cur.insertText(self.search.replace.text()); self.do_search()

    def replace_all_matches(self):
        rows=self.collect_search_matches()
        if not rows: return
        if not confirm(self,'Alles vervangen',f'Wil je {len(rows)} voorkomens vervangen?'): return
        replacement=self.search.replace.text(); rx=self._search_regex()
        self.save()
        chapters=self._chapters_in_scope()
        for ch in chapters:
            text=self.editor.toPlainText() if self.chapter and ch.id==self.chapter.id else self.main.library.read_chapter(self.book,ch)
            changed=rx.sub(lambda m: replacement,text)
            if changed!=text:
                if self.chapter and ch.id==self.chapter.id:
                    self.editor.blockSignals(True); self.editor.setPlainText(changed); self.editor.blockSignals(False); self.dirty=True
                else:
                    self.main.library.save_chapter(self.book,ch,changed)
        self.save(); self.main.search_index.rebuild_book(self.book); self.do_search(); self.update_counts(saved=True)


    def _remember_panel_widths(self, *_):
        sizes = self.left_split.sizes()
        if self.manuscript.isVisible() and sizes[0] >= 200:
            self._manuscript_width = sizes[0]
        if self.right.isVisible() and sizes[2] >= 260:
            self._right_width = sizes[2]

    def _position_contents_edge_button(self):
        """Keep the contents tab attached to the boundary of the left pane.

        The tab deliberately lives above the splitter as a child of EditorPage,
        not inside the center widget.  That avoids it being clipped/covered by
        splitter children and makes the control remain visible when the contents
        pane is hidden.
        """
        if not hasattr(self, 'contents_edge_button') or not hasattr(self, 'center'):
            return
        try:
            center_pos = self.center.mapTo(self, QPoint(0, 0))
            # When the contents pane is visible, straddle its right boundary.
            # When hidden, keep the tab just inside the editor edge.
            x = max(0, center_pos.x() - (self.contents_edge_button.width() // 2))
            y = 58
            self.contents_edge_button.move(x, y)
            self.contents_edge_button.raise_()
        except RuntimeError:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self._position_contents_edge_button)

    def _restore_splitter_widths(self):
        """Give every visible pane a sane width after show/restore.

        QSplitter remembers a hidden widget as width 0. Restoring that state and
        later calling show() can otherwise leave a 1-2 px strip.
        """
        total = max(self.left_split.width(), sum(self.left_split.sizes()), 900)
        left = self._manuscript_width if self.manuscript.isVisible() else 0
        right = self._right_width if self.right.isVisible() else 0
        center = max(320, total - left - right)
        self.left_split.setSizes([left, center, right])

    def _show_manuscript_panel(self):
        self.manuscript.show()
        QTimer.singleShot(0, self._restore_splitter_widths)
        QTimer.singleShot(0, self._position_contents_edge_button)

    def _show_right_panel(self):
        self.right.show()
        QTimer.singleShot(0, self._restore_splitter_widths)

    def toggle_manuscript(self):
        if self.manuscript.isVisible():
            self._remember_panel_widths()
            self.manuscript.hide()
        else:
            self._show_manuscript_panel()
        if hasattr(self, 'contents_edge_button'):
            self.contents_edge_button.setToolTip(
                tr('tool.hide_contents', 'Inhoud verbergen') if self.manuscript.isVisible()
                else tr('tool.show_contents', 'Inhoud tonen')
            )
            self.contents_edge_button.raise_()
            QTimer.singleShot(0, self._position_contents_edge_button)
        self.main.sync_tool_buttons()

    def _set_spell_active(self, active: bool):
        # The passive red underline stays enabled whenever spelling is enabled.
        # Closing the guided panel only removes its current text selection.
        if not active:
            cur = self.editor.textCursor()
            cur.clearSelection()
            self.editor.setTextCursor(cur)

    def toggle_right(self):
        will_hide = self.right.isVisible()
        if will_hide:
            self._remember_panel_widths()
            self.right.hide()
            self._set_spell_active(False)
        else:
            self._show_right_panel()
            if self.right.currentWidget() is self.spell:
                self.spell.refresh()
        self.main.sync_tool_buttons()

    def _toggle_right_widget(self, widget, focus_widget):
        closing_same = self.right.isVisible() and self.right.currentWidget() is widget
        if closing_same:
            self._remember_panel_widths()
            self.right.hide()
            if widget is self.spell:
                self._set_spell_active(False)
        else:
            if widget is not self.spell:
                self._set_spell_active(False)
            self.right.setCurrentWidget(widget)
            self._show_right_panel()
            focus_widget.setFocus()
        self.main.sync_tool_buttons()

    def show_search(self):
        self._toggle_right_widget(self.search, self.search.query)

    def show_ai(self):
        self._toggle_right_widget(self.ai, self.ai.input)

    def show_spell(self):
        opening = not (self.right.isVisible() and self.right.currentWidget() is self.spell)
        if opening:
            self.spell.refresh()
        self._toggle_right_widget(self.spell, self.spell.suggestions)


class MainWindow(QMainWindow):
    def __init__(self, settings, library, models):
        super().__init__(); self.settings=settings; self.library=library; self.models=models
        self._active_theme = str(self.settings.value('theme','Helder') or 'Helder')
        set_icon_theme(self._active_theme)
        self.search_index = BookSearchIndex(library.cache_dir / 'book_search.db')
        self.status = QStatusBar(); self.setStatusBar(self.status)
        self.setWindowTitle(APP_NAME); self.setWindowIcon(icon('books')); self.resize(1480, 900)
        self.rail_expanded = self.settings.value('nav_expanded', False, bool)

        wrap = QWidget(); self.setCentralWidget(wrap); root = QHBoxLayout(wrap); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.rail = QFrame(); self.rail.setObjectName('toolrail')
        self.rail_layout = QVBoxLayout(self.rail); self.rail_layout.setContentsMargins(7,10,7,10); self.rail_layout.setSpacing(6)

        self.stack = QStackedWidget()
        self.start = StartPage(library)
        self.editor_page = EditorPage(self)
        self.persona = PersonaPage(library)
        self.settings_page = SettingsPage(settings, self, models)
        self.trash = TrashPage(self)
        self.book_details_page = None
        for page in (self.start, self.editor_page, self.persona, self.settings_page, self.trash): self.stack.addWidget(page)
        root.addWidget(self.rail); root.addWidget(self.stack, 1)

        self.nav_buttons = []
        self.menu_button = self._nav_button('menu', tr('nav.menu', 'Menu'), self.toggle_nav, checkable=False)
        self.rail_layout.addSpacing(8)
        self.bookshelf_button = self._nav_button('shelf', tr('nav.bookshelf', 'Boekenplank'), self.go_home)
        self.write_button = self._nav_button('books', tr('nav.contents', 'Inhoud'), self.show_editor)
        self.book_details_button = self._nav_button('edit', tr('nav.book_details', 'Boekdetails'), self.open_current_book_details)
        self.rail_layout.addStretch()
        self.persona_button = self._nav_button('persona', tr('nav.persona', 'Schrijverspersona'), self.show_persona)
        self.settings_button = self._nav_button('settings', tr('nav.settings', 'Instellingen'), self.open_settings)
        self.trash_button = self._nav_button('trash', tr('nav.trash', 'Prullenbak'), self.show_trash)

        # Rechter gereedschapsrail. De functie-iconen openen/sluiten hun eigen paneel.
        # Een aparte 'rechterpaneel tonen/verbergen'-knop is daardoor overbodig.
        self.toolrail_expanded = self.settings.value('toolrail_expanded', False, bool)
        self.toolrail = QFrame(); self.toolrail.setObjectName('toolrail')
        self.tool_layout = QVBoxLayout(self.toolrail); self.tool_layout.setContentsMargins(8,10,8,10); self.tool_layout.setSpacing(7)
        self.tool_buttons = []
        def trb(icon_name, tip, fn, checkable=True):
            b=QPushButton(); b.setObjectName('railButton'); b.setProperty('iconName', icon_name); b.setIcon(icon(icon_name)); b.setIconSize(QSize(24,24)); b.setFixedHeight(48); b.setToolTip(tip); b.setCheckable(checkable); b.clicked.connect(fn); b.setProperty('toolLabel', tip); self.tool_layout.addWidget(b); self.tool_buttons.append(b); return b
        self.tool_menu_button = trb('menu', tr('nav.menu', 'Menu'), self.toggle_toolrail, checkable=False)
        self.search_button = trb('search', tr('tool.search', 'Zoeken'), self.editor_page.show_search)
        self.ai_button = trb('spark', tr('tool.ai', 'AI-assistent'), self.editor_page.show_ai)
        self.spell_button = trb('spell', tr('tool.spell', 'Spellingscontrole'), self.editor_page.show_spell)
        self.insert_button = trb('insert', tr('tool.insert', 'Toevoegen'), self.editor_page.show_insert_menu, checkable=False)
        self.history_button = trb('history', tr('tool.history', 'Versiegeschiedenis'), self.editor_page.show_history)
        self.delete_chapter_button = trb('trash', tr('tool.delete_chapter', 'Huidig hoofdstuk verwijderen'), self.editor_page.delete_current_chapter, checkable=False)
        self.tool_layout.addStretch(); root.addWidget(self.toolrail)

        self.start.open_book.connect(self.open_book); self.start.new_book.connect(self.new_book); self.start.import_book.connect(self.import_book)
        self.restore_state(); self._apply_nav_width(); self._apply_toolrail_width(); QTimer.singleShot(0, self.editor_page._position_contents_edge_button)
        self.stack.currentChanged.connect(self._mode_changed); self._mode_changed(0)

        save = QAction('Opslaan', self); save.setShortcut('Ctrl+S'); save.triggered.connect(self.editor_page.save); self.addAction(save)
        focus_left = QAction(self); focus_left.setShortcut('Ctrl+Shift+L'); focus_left.triggered.connect(self.editor_page.toggle_manuscript); self.addAction(focus_left)
        focus_right = QAction(self); focus_right.setShortcut('Ctrl+Shift+R'); focus_right.triggered.connect(self.editor_page.toggle_right); self.addAction(focus_right)
        scene_break = QAction(self); scene_break.setShortcut('Ctrl+Shift+Return'); scene_break.triggered.connect(self.editor_page.insert_scene_break); self.addAction(scene_break)

        # Apply the persisted writing profile once all writer-facing widgets exist.
        # This makes startup deterministic even when Qt/QSS supplies a different
        # inherited font before the first chapter is loaded.
        self.apply_writing_font(
            str(self.settings.value('editor_font', 'Merriweather') or 'Merriweather'),
            int(self.settings.value('editor_font_size', 15, int) or 15),
        )
        self._refresh_theme_icons(self._active_theme)
        self.editor_page.ai.apply_theme(self._active_theme)

    def _nav_button(self, icon_name, label, fn, checkable=True):
        b = QPushButton()
        b.setObjectName('navButton')
        b.setProperty('iconName', icon_name); b.setIcon(icon(icon_name)); b.setIconSize(QSize(22,22))
        b.setToolTip(label); b.setCheckable(checkable)
        # De hoofdrail gedraagt zich als navigatie, niet als een set toggles.
        # Een reeds actieve bestemming kan daarom niet door een tweede klik
        # visueel worden uitgezet. Actieknoppen (Instellingen/Boekdetails/Menu)
        # blijven niet-checkable.
        if checkable:
            b.setAutoExclusive(True)
        b.clicked.connect(fn)
        b.setProperty('navLabel', label)
        self.rail_layout.addWidget(b); self.nav_buttons.append(b)
        return b

    def _apply_nav_width(self, animate=False):
        target = 218 if self.rail_expanded else 64
        for b in self.nav_buttons:
            label = b.property('navLabel') or ''
            b.setText(('  ' + label) if self.rail_expanded else '')
            b.setFixedHeight(48)
            if self.rail_expanded:
                b.setMinimumWidth(198); b.setMaximumWidth(198)
            else:
                b.setFixedWidth(48)
        self.menu_button.setToolTip(tr('nav.collapse', 'Menu inklappen') if self.rail_expanded else tr('nav.expand', 'Menu uitklappen'))
        if not animate:
            self.rail.setMinimumWidth(target); self.rail.setMaximumWidth(target)
            return
        start_width = self.rail.width()
        self._nav_animation = QParallelAnimationGroup(self)
        for prop in (b'minimumWidth', b'maximumWidth'):
            anim = QPropertyAnimation(self.rail, prop, self._nav_animation)
            anim.setDuration(150); anim.setStartValue(start_width); anim.setEndValue(target)
            anim.setEasingCurve(QEasingCurve.InOutCubic)
            self._nav_animation.addAnimation(anim)
        self._nav_animation.start()

    def toggle_nav(self):
        self.rail_expanded = not self.rail_expanded
        self.settings.setValue('nav_expanded', self.rail_expanded)
        self._apply_nav_width(animate=True)

    def _apply_toolrail_width(self, animate=False):
        target = 208 if self.toolrail_expanded else 64
        for b in self.tool_buttons:
            label = b.property('toolLabel') or ''
            b.setText(('  ' + label) if self.toolrail_expanded else '')
            b.setFixedHeight(48)
            b.setMinimumWidth(192 if self.toolrail_expanded else 48)
            b.setMaximumWidth(192 if self.toolrail_expanded else 48)
        self.tool_menu_button.setToolTip(
            tr('tool.menu_collapse', 'Gereedschapsmenu inklappen') if self.toolrail_expanded
            else tr('tool.menu_expand', 'Gereedschapsmenu uitklappen')
        )
        if not animate:
            self.toolrail.setMinimumWidth(target); self.toolrail.setMaximumWidth(target)
            return
        start_width = self.toolrail.width()
        self._tool_animation = QParallelAnimationGroup(self)
        for prop in (b'minimumWidth', b'maximumWidth'):
            anim = QPropertyAnimation(self.toolrail, prop, self._tool_animation)
            anim.setDuration(150); anim.setStartValue(start_width); anim.setEndValue(target)
            anim.setEasingCurve(QEasingCurve.InOutCubic); self._tool_animation.addAnimation(anim)
        self._tool_animation.start()

    def toggle_toolrail(self):
        self.toolrail_expanded = not self.toolrail_expanded
        self.settings.setValue('toolrail_expanded', self.toolrail_expanded)
        self._apply_toolrail_width(animate=True)

    def _mode_changed(self, idx):
        in_editor = self.stack.currentWidget() is self.editor_page
        self.toolrail.setVisible(in_editor)
        self.write_button.setVisible(self.editor_page.book is not None)
        self.book_details_button.setVisible(self.editor_page.book is not None)
        self._sync_nav_selection()
        self.sync_tool_buttons()

    def _leave_settings_preview(self):
        if self.stack.currentWidget() is self.settings_page:
            self.settings_page.restore_preview()

    def _sync_nav_selection(self):
        current = self.stack.currentWidget()
        for b in (self.bookshelf_button, self.write_button, self.book_details_button, self.persona_button, self.settings_button, self.trash_button): b.setChecked(False)
        if current is self.start: self.bookshelf_button.setChecked(True)
        elif current is self.editor_page: self.write_button.setChecked(True)
        elif self.book_details_page is not None and current is self.book_details_page: self.book_details_button.setChecked(True)
        elif current is self.persona: self.persona_button.setChecked(True)
        elif current is self.settings_page: self.settings_button.setChecked(True)
        elif current is self.trash: self.trash_button.setChecked(True)

    def show_editor(self):
        self._leave_settings_preview()
        if self.stack.currentWidget() is self.editor_page:
            self._sync_nav_selection()
            return
        if self.editor_page.book:
            self.stack.setCurrentWidget(self.editor_page)
        else:
            self.go_home()

    def show_persona(self):
        self._leave_settings_preview()
        if self.stack.currentWidget() is self.persona:
            self._sync_nav_selection()
            return
        self.persona.edit.setPlainText(self.library.read_persona())
        self.stack.setCurrentWidget(self.persona)

    def show_trash(self):
        self._leave_settings_preview()
        if self.stack.currentWidget() is self.trash:
            self._sync_nav_selection()
            return
        self.trash.refresh()
        self.stack.setCurrentWidget(self.trash)

    def go_home(self):
        self._leave_settings_preview()
        if self.stack.currentWidget() is self.start and self.editor_page.book is None:
            self._sync_nav_selection()
            return
        self.editor_page.close_book()
        if self.book_details_page is not None:
            self.stack.removeWidget(self.book_details_page); self.book_details_page.deleteLater(); self.book_details_page = None
        self.start.refresh()
        self.stack.setCurrentWidget(self.start)
        self.write_button.setVisible(False)
        self.book_details_button.setVisible(False)
        self._sync_nav_selection()

    def new_book(self):
        title, ok = QInputDialog.getText(self, 'Nieuw boek', 'Titel van het boek:')
        if ok:
            book = self.library.create_book(title or 'Naamloos boek'); self.start.refresh(); self.open_book(book)

    def import_book(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Boek importeren', str(Path.home()), 'Markdown (*.md);;Alle bestanden (*)')
        if not path:
            return
        try:
            book = self.library.import_markdown_book(Path(path))
        except Exception as e:
            QMessageBox.critical(self, 'Boek importeren', f'Importeren mislukt:\n{e}')
            return
        self.start.refresh()
        self.open_book(book)

    def open_book(self, book):
        self.library.touch_book(book)
        self.editor_page.load_book(book)
        self._replace_book_details_page(book)
        self.write_button.setVisible(True)
        self.book_details_button.setVisible(True)
        self.stack.setCurrentWidget(self.editor_page)
        self._sync_nav_selection()

    def _replace_book_details_page(self, book):
        if self.book_details_page is not None:
            self.stack.removeWidget(self.book_details_page)
            self.book_details_page.deleteLater()
        self.book_details_page = BookDetailsPage(self.library, self.settings, book, self)
        self.book_details_page.saved.connect(self._book_details_saved)
        self.book_details_page.deleted.connect(self._book_details_deleted)
        self.stack.addWidget(self.book_details_page)

    def open_current_book_details(self):
        self._leave_settings_preview()
        if not self.editor_page.book:
            self.go_home(); return
        if self.book_details_page is None or self.book_details_page.book.id != self.editor_page.book.id:
            self._replace_book_details_page(self.editor_page.book)
        self.stack.setCurrentWidget(self.book_details_page)

    def _book_details_saved(self, book):
        self.start.refresh()
        if self.editor_page.book and self.editor_page.book.id == book.id:
            self.editor_page.book_title_label.setText(book.title)
        self.status.showMessage('Boekdetails opgeslagen', 2500)

    def _book_details_deleted(self, book):
        if self.editor_page.book and self.editor_page.book.id == book.id:
            self.editor_page.close_book()
        self.start.refresh()
        self.write_button.setVisible(False); self.book_details_button.setVisible(False)
        page = self.book_details_page
        self.book_details_page = None
        if page is not None:
            self.stack.removeWidget(page); page.deleteLater()
        self.stack.setCurrentWidget(self.start)

    def apply_theme(self, theme_name: str):
        """Apply one theme to QSS, icons and rich-content widgets.

        SVG files do not reliably inherit QPushButton ``color`` on Windows, and
        QTextBrowser HTML keeps its last rendered colours until it is rebuilt.
        Keeping these updates in one place prevents partial theme switches.
        """
        theme_name = theme_name if theme_name in THEMES else 'Helder'
        self._active_theme = theme_name
        set_icon_theme(theme_name)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(stylesheet(theme_name))
        self._refresh_theme_icons(theme_name)
        if hasattr(self, 'editor_page') and hasattr(self.editor_page, 'ai'):
            self.editor_page.ai.apply_theme(theme_name)

    def _refresh_theme_icons(self, theme_name: str | None = None):
        theme_name = theme_name or self._active_theme
        # Main navigation and right tool rail.
        for button in list(getattr(self, 'nav_buttons', [])) + list(getattr(self, 'tool_buttons', [])):
            name = button.property('iconName')
            if name:
                button.setIcon(icon(str(name), theme_name=theme_name))
        # Editor-local controls.
        ep = getattr(self, 'editor_page', None)
        if ep is not None:
            for button in (getattr(ep, 'undo_button', None), getattr(ep, 'redo_button', None), getattr(ep, 'contents_edge_button', None)):
                if button is None:
                    continue
                name = button.property('iconName')
                if name:
                    button.setIcon(icon(str(name), theme_name=theme_name))
            # Tree drag handles are item icons, not QPushButtons. Reapply them.
            tree = getattr(ep, 'tree', None)
            if tree is not None:
                drag_icon = icon('drag_handle', theme_name=theme_name)
                root = tree.invisibleRootItem()
                stack = [root.child(i) for i in range(root.childCount())]
                while stack:
                    item = stack.pop()
                    if item is None:
                        continue
                    data = item.data(0, Qt.UserRole)
                    if data and data[0] == 'chapter':
                        item.setIcon(1, drag_icon)
                    stack.extend(item.child(i) for i in range(item.childCount()))

    def apply_writing_font(self, preferred: str, point_size: int | None = None):
        """Apply independent writing typography to every writing surface.

        No theme/QSS change is performed here. The family and size are resolved
        once and then applied as widget/document defaults, so either setting can
        change without affecting the other.
        """
        if point_size is None:
            point_size = self.settings.value('editor_font_size', 15, int)
        typography = typography_from_values(preferred, point_size)
        self.editor_page.editor.apply_typography(typography)
        self.editor_page.chapter_title.setFont(typography.title_font())

    def open_settings(self):
        if self.stack.currentWidget() is self.settings_page:
            self._sync_nav_selection(); return
        self._settings_return_page = self.stack.currentWidget()
        self.settings_page.begin_session()
        self.stack.setCurrentWidget(self.settings_page)

    def return_from_settings(self):
        target = getattr(self, '_settings_return_page', None)
        if target is None or self.stack.indexOf(target) < 0:
            target = self.editor_page if self.editor_page.book else self.start
        self.stack.setCurrentWidget(target)

    def settings_saved(self, old_root):
        editor_font = str(self.settings.value('editor_font','Merriweather') or 'Merriweather')
        editor_size = int(self.settings.value('editor_font_size',15,int) or 15)
        self.apply_writing_font(editor_font, editor_size)
        self.editor_page.load_dictionary_from_settings()
        if self.settings.value('workspace') != old_root:
            QMessageBox.information(self,'Werkmap gewijzigd','De nieuwe werkmap wordt gebruikt nadat de applicatie opnieuw is gestart.')
        self.status.showMessage('Instellingen opgeslagen', 2500)

    def sync_tool_buttons(self):
        if not hasattr(self, 'search_button'): return
        in_editor = self.stack.currentWidget() is self.editor_page
        right_visible = self.editor_page.right.isVisible() and in_editor
        self.search_button.setChecked(right_visible and self.editor_page.right.currentWidget() is self.editor_page.search)
        self.ai_button.setChecked(right_visible and self.editor_page.right.currentWidget() is self.editor_page.ai)
        self.spell_button.setChecked(right_visible and self.editor_page.right.currentWidget() is self.editor_page.spell)
        self.history_button.setChecked(right_visible and self.editor_page.right.currentWidget() is self.editor_page.history)
        if hasattr(self, 'delete_chapter_button'):
            total = sum(len(sec.chapters) for sec in self.editor_page.book.sections) if self.editor_page.book else 0
            self.delete_chapter_button.setEnabled(bool(in_editor and self.editor_page.chapter and not self.editor_page.preview_live_book and total > 1))

    def build_ai_context(self, mode: str, prompt: str):
        ep=self.editor_page; book=ep.book; chapter=ep.chapter
        if not book or not chapter: return '', 'geen manuscript geopend'
        selected = ep.editor.textCursor().selectedText().replace('\u2029','\n')
        if selected: return selected, 'geselecteerde tekst'
        if mode=='Huidig hoofdstuk': return ep.editor.toPlainText(), f'hoofdstuk: {chapter.title}'
        if mode=='Huidige sectie':
            section,_=ep.find_chapter(chapter.id); parts=[]
            for c in section.chapters:
                txt = ep.editor.toPlainText() if c.id==chapter.id else self.library.read_chapter(book,c)
                parts.append(f'# {c.title}\n{txt}')
            return '\n\n'.join(parts), f'sectie: {section.title}'
        if mode=='Hele boek':
            parts=[]
            for s in book.sections:
                if s.id != 'root': parts.append(f'## {s.title}')
                for c in s.chapters:
                    txt=ep.editor.toPlainText() if c.id==chapter.id else self.library.read_chapter(book,c)
                    parts.append(f'# {c.title}\n{txt}')
            return '\n\n'.join(parts), f'boek: {book.title}'
        return ep.editor.toPlainText(), f'hoofdstuk: {chapter.title}'

    def closeEvent(self, event):
        # AI-workers moeten echt gestopt zijn voordat Qt widgets/QThreads vernietigt.
        # Anders kan Qt afsluiten met: QThread: Destroyed while thread is still running.
        if hasattr(self.editor_page, 'ai') and not self.editor_page.ai.shutdown(4500):
            QMessageBox.warning(self, 'AI is nog bezig', 'QuietWriter kon het lopende AI-verzoek nog niet veilig stoppen. Klik op “Stop AI” en probeer daarna opnieuw af te sluiten.')
            event.ignore()
            return
        self.editor_page.save()
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())
        self.settings.setValue('splitter', self.editor_page.left_split.saveState())
        self.settings.setValue('manuscript_visible', self.editor_page.manuscript.isVisible())
        self.settings.setValue('right_visible', self.editor_page.right.isVisible())
        self.settings.setValue('nav_expanded', self.rail_expanded)
        super().closeEvent(event)

    def restore_state(self):
        g=self.settings.value('geometry'); s=self.settings.value('windowState'); sp=self.settings.value('splitter')
        if g: self.restoreGeometry(g)
        if s: self.restoreState(s)
        if sp:
            self.editor_page.left_split.restoreState(sp)
            sizes = self.editor_page.left_split.sizes()
            if len(sizes) >= 3:
                if sizes[0] >= 200: self.editor_page._manuscript_width = sizes[0]
                if sizes[2] >= 260: self.editor_page._right_width = sizes[2]
        self.editor_page.manuscript.setVisible(self.settings.value('manuscript_visible', True, bool))
        self.editor_page.right.setVisible(self.settings.value('right_visible', False, bool))
        # Sanitize old splitter states that may contain a collapsed 0-2 px pane.
        QTimer.singleShot(0, self.editor_page._restore_splitter_widths)


def run():
    app=QApplication(sys.argv); app.setApplicationName(APP_NAME); app.setOrganizationName('QuietWriter')
    # Use a fresh font with an explicit valid point size. On some Windows/Qt
    # combinations QFontDatabase.systemFont() can carry pointSize=-1; copying
    # that font into widgets later produces the Qt warning
    # 'QFont::setPointSize: Point size <= 0 (-1)'.
    app_font = QFont('Segoe UI', 10)
    app.setFont(app_font)
    settings=QSettings('QuietWriter','QuietWriter')
    set_icon_theme(str(settings.value('theme','Helder') or 'Helder'))
    app.setWindowIcon(icon('books'))
    app.setStyleSheet(stylesheet(settings.value('theme','Helder')))
    splash=Splash(); splash.show(); splash.set_status('Instellingen laden…')
    root=Path(settings.value('workspace', str(Path.home()/APP_NAME)))
    splash.set_status('Werkmap controleren…'); library=Library(root)
    splash.set_status('Ollama controleren…')
    client=OllamaClient(settings.value('ollama_url','http://127.0.0.1:11434'))
    try:
        infos=client.model_info(timeout=1.8); models=[m['name'] for m in infos]; splash.set_status(f'Ollama gevonden · {len(models)} modellen')
        if models and not settings.value('ollama_model',''):
            settings.setValue('ollama_model', models[0])
    except Exception:
        models=[]; splash.set_status('Ollama niet bereikbaar · editor blijft beschikbaar')
    QTimer.singleShot(450, splash.accept); splash.exec()
    win=MainWindow(settings,library,models); win.show(); return app.exec()
