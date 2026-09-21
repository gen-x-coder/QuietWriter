from __future__ import annotations
import os
import re
import sys
from pathlib import Path
from datetime import datetime, date
import copy

from PySide6.QtCore import Qt, QSettings, QTimer, QSize, Signal, QMimeData, QUrl
from PySide6.QtGui import QAction, QColor, QFont, QFontDatabase, QIcon, QImageReader, QPainter, QPixmap, QTextCursor, QPen, QDrag, QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QFrame, QGridLayout, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QSplitter, QStackedWidget, QStatusBar,
    QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QAbstractItemView, QHeaderView, QMenu, QTabWidget
)

from . import APP_NAME
from .storage import Library, slugify
from .themes import THEMES, stylesheet
from .ollama import OllamaClient
from .ai.ui import AIPanel
from .ai.providers import ProviderFactory
from .search import BookSearchIndex
from .story_index import StoryIndex
from .spellcheck import WordDictionary, SpellHighlighter
from .dictionary_catalog import DictionaryCatalog
from .chapter_order import DropTarget, move_chapter as reorder_chapter
from .i18n import tr
from .markdown_io import insert_scene_break as build_scene_break_text


ICON_DIR = Path(__file__).with_name('icons')


def icon(name: str) -> QIcon:
    return QIcon(str(ICON_DIR / f'{name}.svg'))


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
    """Rustige schrijfruimte met een begrensde tekstkolom zoals in boekeditors."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.max_text_width = 760
        self.setAcceptRichText(False)
        self.document().setDefaultFont(QFont('Georgia', 14))
        self._update_margins()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_margins()

    def _update_margins(self):
        side = max(42, (max(0, self.width()) - self.max_text_width) // 2)
        self.setViewportMargins(side, 28, side, 36)


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
        self.setFixedSize(180, 288)  # 1 : 1,6

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
                painter.fillRect(target, QColor('#dfe3e7'))
        else:
            painter.fillRect(target, QColor('#dfe3e7'))
            # Abstracte, rustige fallback. Geen titel in het beeldbestand zelf.
            painter.fillRect(0, 0, target.width(), target.height() // 3, QColor('#c9d2d8'))
            painter.fillRect(0, target.height() // 3, target.width(), target.height() // 3, QColor('#d6dadd'))

        # De titel blijft echte, dynamische tekst en maakt dus geen deel uit van de omslagafbeelding.
        band_h = 78
        painter.fillRect(0, target.height() - band_h, target.width(), band_h, QColor(0, 0, 0, 118))
        painter.setPen(QColor('white'))
        font = QFont('Georgia', 14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect().adjusted(12, target.height() - band_h + 10, -12, -10),
                         Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, self.book.title)


class BookCard(QFrame):
    opened = __import__('PySide6.QtCore').QtCore.Signal(object)
    details = __import__('PySide6.QtCore').QtCore.Signal(object)

    def __init__(self, library, book, parent=None):
        super().__init__(parent)
        self.library = library
        self.book = book
        self.setObjectName('bookCard')
        self.setFixedSize(198, 372)
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
        buttons = QHBoxLayout(); buttons.setSpacing(6)
        open_btn = QPushButton('Openen')
        details_btn = QPushButton('Details')
        open_btn.clicked.connect(lambda: self.opened.emit(self.book))
        details_btn.clicked.connect(lambda: self.details.emit(self.book))
        buttons.addWidget(open_btn); buttons.addWidget(details_btn)
        lay.addWidget(cover, 0, Qt.AlignHCenter)
        lay.addWidget(info)
        lay.addLayout(buttons)


class StartPage(QWidget):
    open_book = __import__('PySide6.QtCore').QtCore.Signal(object)
    new_book = __import__('PySide6.QtCore').QtCore.Signal()
    import_book = __import__('PySide6.QtCore').QtCore.Signal()
    manage_book = __import__('PySide6.QtCore').QtCore.Signal(object)

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
        self.grid.setContentsMargins(42, 22, 42, 42); self.grid.setHorizontalSpacing(22); self.grid.setVerticalSpacing(26)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        scroll.setWidget(self.cards_host); outer.addWidget(scroll, 1)
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

        create = QFrame(); create.setObjectName('newBookCard'); create.setFixedSize(198, 372)
        cl = QVBoxLayout(create); cl.setContentsMargins(18, 28, 18, 22)
        plus = QLabel('+'); plus.setObjectName('newBookPlus'); plus.setAlignment(Qt.AlignCenter)
        text = QLabel('Nieuw boek'); text.setObjectName('sectionTitle'); text.setAlignment(Qt.AlignCenter)
        btn = QPushButton('Aanmaken'); btn.clicked.connect(self.new_book.emit)
        imp = QPushButton('Importeren…'); imp.clicked.connect(self.import_book.emit)
        cl.addStretch(); cl.addWidget(plus); cl.addWidget(text); cl.addStretch(); cl.addWidget(btn); cl.addWidget(imp)
        self.grid.addWidget(create, 0, 0)
        for i, book in enumerate(books, 1):
            card = BookCard(self.library, book)
            card.opened.connect(self.open_book.emit)
            card.details.connect(self.manage_book.emit)
            self.grid.addWidget(card, i // 5, i % 5)


class StoryBrowser(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.current_story = None
        root = QHBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        left = QFrame(); left.setObjectName('panel'); left.setFixedWidth(330)
        ll = QVBoxLayout(left); ll.setContentsMargins(20,24,20,20)
        title = QLabel('Verhalen'); title.setObjectName('title')
        self.search = QLineEdit(); self.search.setPlaceholderText('Zoek titel, tag of tekst…'); self.search.setClearButtonEnabled(True)
        self.list = QListWidget(); self.list.itemClicked.connect(self._open_item)
        self.empty = QLabel('Geen verhalen gevonden.'); self.empty.setObjectName('muted'); self.empty.setAlignment(Qt.AlignCenter); self.empty.hide()
        self.search.textChanged.connect(self.filter_list)
        ll.addWidget(title); ll.addWidget(self.search); ll.addSpacing(8); ll.addWidget(self.empty); ll.addWidget(self.list)

        right = QWidget(); rl = QVBoxLayout(right); rl.setContentsMargins(42,30,42,30)
        self.story_title = QLabel('Kies een verhaal'); self.story_title.setObjectName('title')
        self.meta = QLabel(''); self.meta.setObjectName('muted'); self.meta.setWordWrap(True)
        self.chapter_picker = QComboBox(); self.chapter_picker.currentIndexChanged.connect(self._chapter_changed); self.chapter_picker.hide()
        self.reader = QTextEdit(); self.reader.setReadOnly(True); self.reader.setObjectName('storyReader')
        self.reader.document().setDefaultFont(QFont('Georgia', 13))
        rl.addWidget(self.story_title); rl.addWidget(self.meta); rl.addWidget(self.chapter_picker); rl.addSpacing(8); rl.addWidget(self.reader,1)
        root.addWidget(left); root.addWidget(right,1)
        self.refresh()

    def refresh(self):
        self.main.story_index.rebuild(self.main.library.stories_dir)
        self.filter_list()

    def filter_list(self):
        q = self.search.text().strip() if hasattr(self, 'search') else ''
        rows = self.main.story_index.search(q, limit=500) if q else self.main.story_index.list_all()
        self.list.clear()
        for row in rows:
            item = QListWidgetItem(row['title'])
            details = row.get('tags','')
            if details: item.setToolTip(details)
            item.setData(Qt.UserRole, row['path'])
            self.list.addItem(item)
        self.empty.setVisible(bool(q) and not rows)
        self.list.setVisible(bool(rows) or not q)

    def _open_item(self, item):
        try:
            self.current_story = self.main.story_index.get(item.data(Qt.UserRole))
        except Exception as e:
            QMessageBox.warning(self, 'Verhaal openen', str(e)); return
        d = self.current_story
        self.story_title.setText(d.get('title') or Path(d['path']).stem)
        bits = []
        if d.get('description'): bits.append(d['description'])
        if d.get('intro'): bits.append('Intro: ' + d['intro'])
        if d.get('tags'): bits.append('Tags: ' + d['tags'])
        self.meta.setText('\n\n'.join(bits))
        chapters = d.get('chapters', [])
        self.chapter_picker.blockSignals(True); self.chapter_picker.clear()
        for ch in chapters: self.chapter_picker.addItem(ch['title'])
        self.chapter_picker.blockSignals(False)
        self.chapter_picker.setVisible(len(chapters) > 1)
        self._show_chapter(0)

    def _chapter_changed(self, idx):
        self._show_chapter(idx)

    def _show_chapter(self, idx):
        if not self.current_story: return
        chapters = self.current_story.get('chapters', [])
        if not chapters: self.reader.clear(); return
        idx = max(0, min(idx, len(chapters)-1))
        self.reader.setPlainText(chapters[idx]['text'])


class BookDetailsDialog(QDialog):
    deleted = __import__('PySide6.QtCore').QtCore.Signal(object)

    def __init__(self, library, settings, book, parent=None):
        super().__init__(parent)
        self.library = library
        self.settings = settings
        self.book = book
        self.old_slug = book.slug
        self.pending_cover = None
        self.setWindowTitle('Boekdetails')
        self.resize(720, 690)
        root = QVBoxLayout(self)
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
        self.description = QTextEdit(md.get('description','')); self.description.setMaximumHeight(82)
        self.meta = QTextEdit(md.get('meta','')); self.meta.setMaximumHeight(82)
        self.intro_text = QTextEdit(md.get('intro','')); self.intro_text.setMaximumHeight(100)
        self.tags = QLineEdit(md.get('tags',''))
        self.author = QLineEdit(md.get('author',''))
        form.addRow('Titel', self.title_edit)
        form.addRow('Slug', slug_box)
        form.addRow('Korte beschrijving', self.description)
        form.addRow('Meta / SEO-beschrijving', self.meta)
        form.addRow('Intro boven het verhaal', self.intro_text)
        form.addRow('Tags', self.tags)
        form.addRow('Auteur', self.author)
        root.addLayout(form)

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
        root.addWidget(cover_box)
        self.slug_edit.textChanged.connect(self._update_header_path)
        self._refresh_cover_preview()
        self._update_header_path()

        actions = QHBoxLayout()
        export_btn = QPushButton('Exporteren…'); export_btn.clicked.connect(self.export_markdown)
        delete = QPushButton('Naar prullenbak'); delete.setObjectName('dangerButton'); delete.clicked.connect(self.delete_book)
        actions.addWidget(export_btn); actions.addWidget(delete); actions.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(tr('common.save', 'Opslaan'))
        buttons.button(QDialogButtonBox.Cancel).setText(tr('common.cancel', 'Annuleren'))
        buttons.accepted.connect(self.save); buttons.rejected.connect(self.reject)
        actions.addWidget(buttons); root.addLayout(actions)

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
        template = self.settings.value('cover_header_template', '/{slug}.jpg')
        slug = self.slug_edit.text().strip() or 'boek'
        try:
            path = str(template).format(slug=slug, ext='jpg')
        except Exception:
            path = f'/{slug}.jpg'
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
        self._refresh_cover_preview()

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
            'description': self.description.toPlainText().strip(),
            'meta': self.meta.toPlainText().strip(),
            'intro': self.intro_text.toPlainText().strip(),
            'tags': self.tags.text().strip(),
            'author': self.author.text().strip(),
            'image': image_ref,
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
        self.accept()

    def export_markdown(self):
        # Sla eerst de velden in deze dialoog op in het in-memory boek, zonder de dialoog te sluiten.
        title = self.title_edit.text().strip() or self.book.title
        slug = slugify(self.slug_edit.text().strip() or title)
        self.book.title = title
        self.book.metadata.update({
            'slug': slug,
            'description': self.description.toPlainText().strip(),
            'meta': self.meta.toPlainText().strip(),
            'intro': self.intro_text.toPlainText().strip(),
            'tags': self.tags.text().strip(),
            'author': self.author.text().strip(),
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
        if self.library.cover_path(self.book):
            try:
                image_ref = str(template).format(slug=slug, ext=self.library.cover_path(self.book).suffix.lstrip('.'))
            except Exception:
                image_ref = f'/{slug}.jpg'
        else:
            # Een bestaand geïmporteerd image-veld blijft behouden als er geen lokale omslag is gekozen.
            image_ref = str(self.book.metadata.get('image', '') or '')
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
        self.done(2)


class TrashPage(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        root = QVBoxLayout(self); root.setContentsMargins(42, 34, 42, 34)
        top = QHBoxLayout()
        title = QLabel('Prullenbak'); title.setObjectName('title')
        self.restore_btn = QPushButton('Herstellen'); self.restore_btn.clicked.connect(self.restore_selected)
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
        save = QPushButton('Opslaan')
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


class SettingsDialog(QDialog):
    DICTIONARY_DOWNLOAD_URL = 'https://extensions.openoffice.org/'

    def __init__(self, settings: QSettings, parent=None, models=None):
        super().__init__(parent)
        self.settings = settings
        self.original_theme = settings.value('theme', 'Helder')
        self.available_models = list(models or [])
        self.setWindowTitle(tr('settings.title', 'Instellingen'))
        self.resize(720, 560)

        root = QVBoxLayout(self)
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
        af.addRow('Kleurenschema', self.theme)
        appearance_note = QLabel('De gekozen stijl wordt direct als voorbeeld toegepast. Bij Annuleren wordt het vorige thema hersteld.')
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

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(tr('common.save', 'Opslaan'))
        buttons.button(QDialogButtonBox.Cancel).setText(tr('common.cancel', 'Annuleren'))
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        self.theme.currentTextChanged.connect(lambda n: QApplication.instance().setStyleSheet(stylesheet(n)))

    def reject(self):
        QApplication.instance().setStyleSheet(stylesheet(self.original_theme))
        super().reject()

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

    def accept(self):
        self.settings.setValue('theme', self.theme.currentText())
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
        super().accept()


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
        self._drag_allowed = False
        self._drag_item = None
        self._drop_item = None
        self._drop_before = True

    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        idx = self.indexAt(event.position().toPoint())
        data = item.data(0, Qt.UserRole) if item else None
        # Only the six-dot handle in column 1 can start a drag.
        self._drag_allowed = bool(item and idx.isValid() and idx.column() == 1 and data and data[0] == 'chapter')
        self._drag_item = item if self._drag_allowed else None
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
        painter.setPen(QColor('#6b7280'))
        painter.drawText(pix.rect().adjusted(8, 0, -8, 0), Qt.AlignVCenter | Qt.AlignLeft, self._drag_item.text(0))
        painter.end()
        drag.setPixmap(pix)
        drag.exec(Qt.MoveAction)
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
            p.setPen(QPen(QColor('#4d738f'), 3))
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
        self.create_btn = QPushButton('+ Nieuwe versie maken')
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
        head = QHBoxLayout(); title = QLabel('Manuscript'); title.setObjectName('sectionTitle'); add = QPushButton('+ Toevoegen'); add.clicked.connect(self.add_menu)
        head.addWidget(title); head.addStretch(); head.addWidget(add)
        self.tree = ManuscriptTree(); self.tree.itemClicked.connect(self.tree_clicked); self.tree.chapterDropped.connect(self.move_chapter); self.tree.setContextMenuPolicy(Qt.CustomContextMenu); self.tree.customContextMenuRequested.connect(self.tree_context_menu)
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
        undo = QPushButton(); undo.setObjectName('compactButton'); undo.setIcon(icon('undo')); undo.setIconSize(QSize(22,22)); undo.setToolTip('Ongedaan maken')
        redo = QPushButton(); redo.setObjectName('compactButton'); redo.setIcon(icon('redo')); redo.setIconSize(QSize(22,22)); redo.setToolTip('Opnieuw')
        self.book_title_label = QLabel(''); self.book_title_label.setObjectName('bookTitleLabel')
        tl.addWidget(undo); tl.addWidget(redo); tl.addSpacing(8); tl.addWidget(self.book_title_label); tl.addStretch()
        self.chapter_title = QLineEdit(); self.chapter_title.setPlaceholderText('Hoofdstuktitel'); self.chapter_title.setAlignment(Qt.AlignCenter); self.chapter_title.setObjectName('chapterTitle')
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
        root.addWidget(self.left_split)

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
                    it = QTreeWidgetItem([chapter.title, '']); it.setData(0, Qt.UserRole, ('chapter', chapter.id)); it.setIcon(1, icon('drag_handle')); it.setTextAlignment(1, Qt.AlignCenter); it.setToolTip(1, 'Sleep om hoofdstuk te verplaatsen'); self.tree.addTopLevelItem(it)
            else:
                sit = QTreeWidgetItem([section.title, '']); sit.setData(0, Qt.UserRole, ('section', section.id)); sit.setFlags(sit.flags() & ~Qt.ItemIsDragEnabled); self.tree.addTopLevelItem(sit)
                for chapter in section.chapters:
                    cit = QTreeWidgetItem([chapter.title, '']); cit.setData(0, Qt.UserRole, ('chapter', chapter.id)); cit.setIcon(1, icon('drag_handle')); cit.setTextAlignment(1, Qt.AlignCenter); cit.setToolTip(1, 'Sleep om hoofdstuk te verplaatsen'); sit.addChild(cit)
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
        self.dirty = False; self.update_counts(); self.main.sync_tool_buttons()
        if self.right.isVisible() and self.right.currentWidget() is self.spell:
            self.spell.refresh()

    def on_text_changed(self):
        if self.preview_live_book:
            return
        self.dirty = True; self.update_counts()
        if self.main.settings.value('autosave', True, bool): self.autosave_timer.start()

    def save(self):
        if self.preview_live_book:
            return
        if self.book and self.chapter and self.dirty:
            self.main.library.save_chapter(self.book, self.chapter, self.editor.toPlainText()); self.dirty = False
            self.main.search_index.rebuild_book(self.book); self.update_counts(saved=True)

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
        self.main.status.showMessage(f'{words:,}'.replace(',', '.') + ' woorden' + (f' · Opgeslagen {datetime.now():%H:%M}' if saved else ''))

    def add_menu(self):
        if not self.book or self.preview_live_book: return
        choices = ['Nieuw hoofdstuk', 'Nieuwe sectie']
        choice, ok = QInputDialog.getItem(self, 'Toevoegen', 'Wat wil je toevoegen?', choices, 0, False)
        if not ok: return
        if choice == 'Nieuwe sectie':
            title, ok = QInputDialog.getText(self, 'Nieuwe sectie', 'Naam:')
            if ok:
                insert_after = None
                item = self.tree.currentItem()
                if item:
                    data = item.data(0, Qt.UserRole)
                    if data and data[0] == 'section': insert_after = data[1]
                    elif data and data[0] == 'chapter':
                        sec, _ = self.find_chapter(data[1]); insert_after = sec.id if sec else None
                self.main.library.add_section(self.book, title or 'Nieuwe sectie', after_section_id=insert_after); self.populate_tree()
        else:
            # Voeg toe aan geselecteerde sectie, anders laatste sectie.
            section = self.book.sections[-1]
            item = self.tree.currentItem()
            if item:
                data = item.data(0, Qt.UserRole)
                if data and data[0]=='section':
                    section = next((s for s in self.book.sections if s.id==data[1]), section)
                elif data and data[0]=='chapter':
                    section, _ = self.find_chapter(data[1])
            title, ok = QInputDialog.getText(self, 'Nieuw hoofdstuk', 'Titel:')
            if ok:
                c = self.main.library.add_chapter(self.book, section, title or 'Nieuw hoofdstuk'); self.populate_tree(); self.open_chapter(c)

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

    def _show_right_panel(self):
        self.right.show()
        QTimer.singleShot(0, self._restore_splitter_widths)

    def toggle_manuscript(self):
        if self.manuscript.isVisible():
            self._remember_panel_widths()
            self.manuscript.hide()
        else:
            self._show_manuscript_panel()
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
        self.search_index = BookSearchIndex(library.cache_dir / 'book_search.db')
        self.story_index = StoryIndex(library.cache_dir / 'stories.db')
        self.status = QStatusBar(); self.setStatusBar(self.status)
        self.setWindowTitle(APP_NAME); self.resize(1480, 900)
        self.rail_expanded = self.settings.value('nav_expanded', False, bool)

        wrap = QWidget(); self.setCentralWidget(wrap); root = QHBoxLayout(wrap); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.rail = QFrame(); self.rail.setObjectName('toolrail')
        self.rail_layout = QVBoxLayout(self.rail); self.rail_layout.setContentsMargins(7,10,7,10); self.rail_layout.setSpacing(6)

        self.stack = QStackedWidget()
        self.start = StartPage(library)
        self.editor_page = EditorPage(self)
        self.stories = StoryBrowser(self)
        self.persona = PersonaPage(library)
        self.trash = TrashPage(self)
        for page in (self.start, self.editor_page, self.stories, self.persona, self.trash): self.stack.addWidget(page)
        root.addWidget(self.rail); root.addWidget(self.stack, 1)

        self.nav_buttons = []
        self.menu_button = self._nav_button('menu', 'Menu', self.toggle_nav, checkable=False)
        self.rail_layout.addSpacing(8)
        self.bookshelf_button = self._nav_button('shelf', 'Boekenplank', self.go_home)
        self.write_button = self._nav_button('books', 'Manuscript', self.show_editor)
        self.book_details_button = self._nav_button('edit', 'Boekdetails', self.open_current_book_details, checkable=False)
        self.stories_button = self._nav_button('stories', 'Verhalen', self.show_stories)
        self.persona_button = self._nav_button('persona', 'Schrijverspersona', self.show_persona)
        self.trash_button = self._nav_button('trash', 'Prullenbak', self.show_trash)
        self.rail_layout.addStretch()
        self.settings_button = self._nav_button('settings', 'Instellingen', self.open_settings, checkable=False)

        # Rechter gereedschapsrail: alleen actief in het manuscript.
        self.toolrail = QFrame(); self.toolrail.setObjectName('toolrail'); self.toolrail.setFixedWidth(64)
        tr=QVBoxLayout(self.toolrail); tr.setContentsMargins(8,10,8,10); tr.setSpacing(7)
        def trb(icon_name, tip, fn, checkable=True):
            b=QPushButton(); b.setObjectName('railButton'); b.setIcon(icon(icon_name)); b.setIconSize(QSize(28,28)); b.setFixedSize(48,48); b.setToolTip(tip); b.setCheckable(checkable); b.clicked.connect(fn); tr.addWidget(b); return b
        self.search_button = trb('search','Zoeken', self.editor_page.show_search)
        self.ai_button = trb('spark','AI-assistent', self.editor_page.show_ai)
        self.spell_button = trb('spell','Spellingscontrole', self.editor_page.show_spell)
        self.insert_button = trb('insert','Toevoegen', self.editor_page.show_insert_menu, checkable=False)
        self.history_button = trb('history','Versiegeschiedenis', self.editor_page.show_history)
        self.delete_chapter_button = trb('trash','Huidig hoofdstuk verwijderen', self.editor_page.delete_current_chapter, checkable=False)
        self.manuscript_button = trb('panel-left','Hoofdstukpaneel tonen/verbergen', self.editor_page.toggle_manuscript)
        self.right_button = trb('panel-right','Rechterpaneel tonen/verbergen', self.editor_page.toggle_right)
        tr.addStretch(); root.addWidget(self.toolrail)

        self.start.open_book.connect(self.open_book); self.start.new_book.connect(self.new_book); self.start.import_book.connect(self.import_book); self.start.manage_book.connect(self.manage_book)
        self.restore_state(); self._apply_nav_width()
        self.stack.currentChanged.connect(self._mode_changed); self._mode_changed(0)

        save = QAction('Opslaan', self); save.setShortcut('Ctrl+S'); save.triggered.connect(self.editor_page.save); self.addAction(save)
        focus_left = QAction(self); focus_left.setShortcut('Ctrl+Shift+L'); focus_left.triggered.connect(self.editor_page.toggle_manuscript); self.addAction(focus_left)
        focus_right = QAction(self); focus_right.setShortcut('Ctrl+Shift+R'); focus_right.triggered.connect(self.editor_page.toggle_right); self.addAction(focus_right)
        scene_break = QAction(self); scene_break.setShortcut('Ctrl+Shift+Return'); scene_break.triggered.connect(self.editor_page.insert_scene_break); self.addAction(scene_break)

    def _nav_button(self, icon_name, label, fn, checkable=True):
        b = QPushButton()
        b.setObjectName('navButton')
        b.setIcon(icon(icon_name)); b.setIconSize(QSize(28,28))
        b.setToolTip(label); b.setCheckable(checkable); b.clicked.connect(fn)
        b.setProperty('navLabel', label)
        self.rail_layout.addWidget(b); self.nav_buttons.append(b)
        return b

    def _apply_nav_width(self):
        self.rail.setFixedWidth(218 if self.rail_expanded else 64)
        for b in self.nav_buttons:
            label = b.property('navLabel') or ''
            b.setText(('  ' + label) if self.rail_expanded else '')
            b.setFixedHeight(48)
            if self.rail_expanded:
                b.setMinimumWidth(198); b.setMaximumWidth(198)
            else:
                b.setFixedWidth(48)
        self.menu_button.setToolTip('Menu inklappen' if self.rail_expanded else 'Menu uitklappen')

    def toggle_nav(self):
        self.rail_expanded = not self.rail_expanded
        self.settings.setValue('nav_expanded', self.rail_expanded)
        self._apply_nav_width()

    def _mode_changed(self, idx):
        in_editor = self.stack.currentWidget() is self.editor_page
        self.toolrail.setVisible(in_editor)
        self.write_button.setVisible(self.editor_page.book is not None)
        self.book_details_button.setVisible(self.editor_page.book is not None)
        self._sync_nav_selection()
        self.sync_tool_buttons()

    def _sync_nav_selection(self):
        current = self.stack.currentWidget()
        for b in (self.bookshelf_button, self.write_button, self.stories_button, self.persona_button, self.trash_button): b.setChecked(False)
        if current is self.start: self.bookshelf_button.setChecked(True)
        elif current is self.editor_page: self.write_button.setChecked(True)
        elif current is self.stories: self.stories_button.setChecked(True)
        elif current is self.persona: self.persona_button.setChecked(True)
        elif current is self.trash: self.trash_button.setChecked(True)

    def show_editor(self):
        if self.editor_page.book:
            self.stack.setCurrentWidget(self.editor_page)
        else:
            self.go_home()

    def show_stories(self):
        self.stories.refresh(); self.stack.setCurrentWidget(self.stories)

    def show_persona(self):
        self.persona.edit.setPlainText(self.library.read_persona())
        self.stack.setCurrentWidget(self.persona)

    def show_trash(self):
        self.trash.refresh()
        self.stack.setCurrentWidget(self.trash)

    def go_home(self):
        self.editor_page.close_book()
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
        path, _ = QFileDialog.getOpenFileName(self, 'Boek importeren', str(self.library.stories_dir), 'Markdown (*.md);;Alle bestanden (*)')
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
        self.write_button.setVisible(True)
        self.book_details_button.setVisible(True)
        self.stack.setCurrentWidget(self.editor_page)
        self._sync_nav_selection()

    def open_current_book_details(self):
        if self.editor_page.book:
            self.manage_book(self.editor_page.book)
        else:
            self.go_home()

    def manage_book(self, book):
        if self.editor_page.book and self.editor_page.book.id == book.id:
            self.editor_page.save()
        d = BookDetailsDialog(self.library, self.settings, book, self)
        result = d.exec()
        # Bij verwijderen is het boek mogelijk ook in de editor geladen.
        if result == 2 and self.editor_page.book and self.editor_page.book.id == book.id:
            self.editor_page.close_book()
            self.write_button.setVisible(False)
            self.book_details_button.setVisible(False)
        self.start.refresh()
        if result == QDialog.Accepted and self.editor_page.book and self.editor_page.book.id == book.id:
            # Houd titelwijzigingen ook direct zichtbaar wanneer hetzelfde boek nog open staat.
            self.editor_page.book_title_label.setText(book.title)

    def open_settings(self):
        old_root = self.settings.value('workspace', str(Path.home()/APP_NAME))
        d=SettingsDialog(self.settings,self,self.models)
        if d.exec():
            QApplication.instance().setStyleSheet(stylesheet(self.settings.value('theme','Helder')))
            self.editor_page.load_dictionary_from_settings()
            if self.settings.value('workspace') != old_root:
                QMessageBox.information(self,'Werkmap gewijzigd','De nieuwe werkmap wordt gebruikt nadat de applicatie opnieuw is gestart.')

    def sync_tool_buttons(self):
        if not hasattr(self, 'search_button'): return
        in_editor = self.stack.currentWidget() is self.editor_page
        right_visible = self.editor_page.right.isVisible() and in_editor
        self.search_button.setChecked(right_visible and self.editor_page.right.currentWidget() is self.editor_page.search)
        self.ai_button.setChecked(right_visible and self.editor_page.right.currentWidget() is self.editor_page.ai)
        self.spell_button.setChecked(right_visible and self.editor_page.right.currentWidget() is self.editor_page.spell)
        self.history_button.setChecked(right_visible and self.editor_page.right.currentWidget() is self.editor_page.history)
        self.manuscript_button.setChecked(self.editor_page.manuscript.isVisible() and in_editor)
        self.right_button.setChecked(right_visible)
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
    # Start from Qt's real system font and only repair it if Windows reports an
    # invalid point size. This avoids propagating a -1 point size into child fonts.
    app_font = QFontDatabase.systemFont(QFontDatabase.GeneralFont)
    if app_font.pointSizeF() <= 0:
        app_font.setPointSizeF(10.0)
    app_font.setFamily('Segoe UI')
    app.setFont(app_font)
    settings=QSettings('QuietWriter','QuietWriter')
    app.setStyleSheet(stylesheet(settings.value('theme','Helder')))
    splash=Splash(); splash.show(); splash.set_status('Instellingen laden…')
    root=Path(settings.value('workspace', str(Path.home()/APP_NAME)))
    splash.set_status('Werkmap controleren…'); library=Library(root)
    splash.set_status('Verhalenindex bijwerken…'); story_index=StoryIndex(library.cache_dir/'stories.db'); story_index.rebuild(library.stories_dir)
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
