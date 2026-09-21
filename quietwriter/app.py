from __future__ import annotations
import os
import sys
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QSettings, QTimer, QSize
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QImageReader, QPainter, QPixmap, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QFrame, QGridLayout, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QSplitter, QStackedWidget, QStatusBar,
    QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
)

from . import APP_NAME
from .storage import Library, slugify
from .themes import THEMES, stylesheet
from .ollama import OllamaClient, ChatWorker
from .search import BookSearchIndex
from .story_index import StoryIndex
from .spellcheck import WordDictionary, SpellHighlighter


ICON_DIR = Path(__file__).with_name('icons')


def icon(name: str) -> QIcon:
    return QIcon(str(ICON_DIR / f'{name}.svg'))


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
        self.search = QLineEdit(); self.search.setPlaceholderText('Zoek op titel, tag of beschrijving…'); self.search.setMaximumWidth(390)
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)
        controls.addWidget(self.count); controls.addStretch(); controls.addWidget(self.search)
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
        cl.addStretch(); cl.addWidget(plus); cl.addWidget(text); cl.addStretch(); cl.addWidget(btn)
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
        self.header_path = QLabel(''); self.header_path.setObjectName('muted'); self.header_path.setWordWrap(True)
        cover_right.addWidget(QLabel('Boekomslag · verhouding 1:1,6 · lange zijde minimaal 1024 px'))
        cover_right.addWidget(self.cover_name); cover_right.addWidget(choose,0,Qt.AlignLeft); cover_right.addWidget(self.header_path); cover_right.addStretch()
        cb.addWidget(self.cover_preview); cb.addLayout(cover_right,1)
        root.addWidget(cover_box)
        self.slug_edit.textChanged.connect(self._update_header_path)
        self._refresh_cover_preview()
        self._update_header_path()

        actions = QHBoxLayout()
        delete = QPushButton('Boek verwijderen'); delete.setObjectName('dangerButton'); delete.clicked.connect(self.delete_book)
        actions.addWidget(delete); actions.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText('Opslaan')
        buttons.button(QDialogButtonBox.Cancel).setText('Annuleren')
        buttons.accepted.connect(self.save); buttons.rejected.connect(self.reject)
        actions.addWidget(buttons); root.addLayout(actions)

    def _cover_candidate(self):
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
            if self.pending_cover:
                self.library.set_cover(self.book, self.pending_cover)
            self.library.save_manifest(self.book)
        except Exception as e:
            QMessageBox.warning(self, 'Boekdetails', f'Opslaan mislukt:\n{e}'); return
        self.accept()

    def delete_book(self):
        answer = QMessageBox.warning(
            self, 'Boek verwijderen',
            f'Wil je “{self.book.title}” echt verwijderen?\n\nDit verwijdert het boek en alle hoofdstukken uit de boekenmap. Deze actie kan niet ongedaan worden gemaakt.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        try:
            self.library.delete_book(self.book)
        except Exception as e:
            QMessageBox.critical(self, 'Boek verwijderen', str(e)); return
        self.deleted.emit(self.book)
        self.done(2)


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
        if QMessageBox.question(self, 'Schrijfwijzer laden', 'De huidige tekst in de editor vervangen door de meegeleverde, geoptimaliseerde schrijfwijzer?') == QMessageBox.Yes:
            self.edit.setPlainText(path.read_text(encoding='utf-8'))

    def save(self):
        self.library.save_persona(self.edit.toPlainText())


class SettingsDialog(QDialog):
    def __init__(self, settings: QSettings, parent=None, models=None):
        super().__init__(parent)
        self.settings = settings
        self.original_theme = settings.value('theme', 'Helder')
        self.available_models = list(models or [])
        self.setWindowTitle('Instellingen')
        self.resize(560, 420)
        root = QVBoxLayout(self)
        form = QFormLayout()
        self.language = QComboBox(); self.language.addItem('Nederlands', 'nl')
        self.theme = QComboBox(); self.theme.addItems(THEMES.keys()); self.theme.setCurrentText(settings.value('theme', 'Helder'))
        self.autosave = QCheckBox(); self.autosave.setChecked(settings.value('autosave', True, bool))
        self.root = QLineEdit(settings.value('workspace', str(Path.home() / 'QuietWriter')))
        choose = QPushButton('Map kiezen…')
        choose.clicked.connect(self.choose_root)
        box = QWidget(); h = QHBoxLayout(box); h.setContentsMargins(0,0,0,0); h.addWidget(self.root); h.addWidget(choose)
        self.ollama = QLineEdit(settings.value('ollama_url', 'http://127.0.0.1:11434'))
        self.model = QComboBox(); self.model.setEditable(True)
        refresh = QPushButton('Modellen ophalen')
        refresh.clicked.connect(self.refresh_models)
        modelbox = QWidget(); mh = QHBoxLayout(modelbox); mh.setContentsMargins(0,0,0,0); mh.addWidget(self.model); mh.addWidget(refresh)
        self.fast_model = QComboBox(); self.fast_model.setEditable(True)
        self.cover_template = QLineEdit(settings.value('cover_header_template', '/{slug}.jpg'))
        self.cover_template.setPlaceholderText('/{slug}.jpg')
        form.addRow('Programmataal', self.language)
        form.addRow('Kleurenschema', self.theme)
        form.addRow('Automatisch opslaan', self.autosave)
        form.addRow('Werkmap / Dropbox-map', box)
        form.addRow('Ollama-adres', self.ollama)
        form.addRow('Schrijf- en analysemodel', modelbox)
        form.addRow('Snel achtergrondmodel', self.fast_model)
        form.addRow('Afbeeldingspad in metadata', self.cover_template)
        root.addLayout(form)
        note = QLabel('Voor afbeeldingspaden kun je {slug} gebruiken, bijvoorbeeld /{slug}.jpg of /images/{slug}.jpg. QuietWriter kent geen websiteadres; alleen dit relatieve pad wordt bewaard.\n\nOpenRouter is voorbereid in de architectuur, maar nog niet actief in deze versie.')
        note.setObjectName('muted'); note.setWordWrap(True); root.addWidget(note)
        self._populate_models(self.available_models)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText('Opslaan')
        buttons.button(QDialogButtonBox.Cancel).setText('Annuleren')
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        root.addStretch(); root.addWidget(buttons)
        self.theme.currentTextChanged.connect(lambda n: QApplication.instance().setStyleSheet(stylesheet(n)))

    def reject(self):
        QApplication.instance().setStyleSheet(stylesheet(self.original_theme))
        super().reject()

    def choose_root(self):
        p = QFileDialog.getExistingDirectory(self, 'Kies werkmap', self.root.text())
        if p: self.root.setText(p)

    def _populate_models(self, models):
        main_current = self.settings.value('ollama_model', '')
        fast_current = self.settings.value('fast_model', '')
        self.model.clear(); self.fast_model.clear()
        self.model.addItems(models)
        self.fast_model.addItems(models)
        if main_current:
            self.model.setCurrentText(main_current)
        elif models:
            self.model.setCurrentIndex(0)
        if fast_current:
            self.fast_model.setCurrentText(fast_current)
        elif models:
            self.fast_model.setCurrentIndex(0)

    def refresh_models(self):
        try:
            infos = OllamaClient(self.ollama.text()).model_info()
            models = [m['name'] for m in infos]
            main_current = self.model.currentText()
            fast_current = self.fast_model.currentText()
            self.model.clear(); self.fast_model.clear()
            self.model.addItems(models); self.fast_model.addItems(models)
            if main_current in models:
                self.model.setCurrentText(main_current)
            elif models:
                self.model.setCurrentIndex(0)
            if fast_current in models:
                self.fast_model.setCurrentText(fast_current)
            elif infos:
                smallest = min(infos, key=lambda m: m.get('size', 0) or 0)['name']
                self.fast_model.setCurrentText(smallest)
            if self.parent() and hasattr(self.parent(), 'models'):
                self.parent().models = models
        except Exception as e:
            QMessageBox.warning(self, 'Ollama', f'Ollama is niet bereikbaar:\n{e}')

    def accept(self):
        self.settings.setValue('theme', self.theme.currentText())
        self.settings.setValue('autosave', self.autosave.isChecked())
        self.settings.setValue('workspace', self.root.text())
        self.settings.setValue('ollama_url', self.ollama.text())
        self.settings.setValue('ollama_model', self.model.currentText())
        self.settings.setValue('fast_model', self.fast_model.currentText())
        self.settings.setValue('cover_header_template', self.cover_template.text().strip() or '/{slug}.jpg')
        super().accept()


class SearchPanel(QWidget):
    open_chapter = __import__('PySide6.QtCore').QtCore.Signal(str)
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(18,18,18,18)
        lab = QLabel('Zoeken'); lab.setObjectName('sectionTitle')
        self.query = QLineEdit(); self.query.setPlaceholderText('Zoek in dit boek…'); self.query.setClearButtonEnabled(True)
        self.only_chapter = QCheckBox('Alleen huidig hoofdstuk')
        self.empty = QLabel('Geen resultaten gevonden.'); self.empty.setObjectName('muted'); self.empty.setAlignment(Qt.AlignCenter); self.empty.hide()
        self.results = QListWidget()
        self.results.itemActivated.connect(lambda i: self.open_chapter.emit(i.data(Qt.UserRole)))
        lay.addWidget(lab); lay.addWidget(self.query); lay.addWidget(self.only_chapter); lay.addWidget(self.empty); lay.addWidget(self.results)

    def show_results(self, rows):
        self.results.clear()
        active = bool(self.query.text().strip())
        self.empty.setVisible(active and not rows)
        self.results.setVisible(bool(rows) or not active)
        for cid, title, snippet in rows:
            item = QListWidgetItem(f'{title}\n{snippet}')
            item.setData(Qt.UserRole, cid)
            self.results.addItem(item)


class AIPanel(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.worker = None
        self.current_assistant = ''
        self._thinking_dots = 0
        self._final_started = False
        self.thinking_timer = QTimer(self)
        self.thinking_timer.setInterval(350)
        self.thinking_timer.timeout.connect(self._animate_thinking)

        lay = QVBoxLayout(self); lay.setContentsMargins(16,16,16,16)
        top = QHBoxLayout()
        lab = QLabel('AI-assistent'); lab.setObjectName('sectionTitle')
        self.context = QComboBox(); self.context.addItems(['Huidig hoofdstuk', 'Huidige sectie', 'Hele boek', 'Verhalenbibliotheek'])
        top.addWidget(lab); top.addStretch(); top.addWidget(self.context)

        self.thinking_button = QPushButton('Denken…')
        self.thinking_button.setObjectName('thinkingButton')
        self.thinking_button.clicked.connect(self._toggle_thinking_details)
        self.thinking_button.hide()
        self.thinking_details = QTextEdit()
        self.thinking_details.setReadOnly(True)
        self.thinking_details.setMaximumHeight(130)
        self.thinking_details.setObjectName('thinkingDetails')
        self.thinking_details.hide()

        self.chat = QTextEdit(); self.chat.setReadOnly(True)
        self.input = QTextEdit(); self.input.setMaximumHeight(120); self.input.setPlaceholderText('Typ een opdracht…')
        self.send_button = QPushButton('Versturen'); self.send_button.clicked.connect(self.send)
        lay.addLayout(top)
        lay.addWidget(self.thinking_button, 0, Qt.AlignLeft)
        lay.addWidget(self.thinking_details)
        lay.addWidget(self.chat); lay.addWidget(self.input); lay.addWidget(self.send_button, 0, Qt.AlignRight)

    def send(self):
        prompt = self.input.toPlainText().strip()
        if not prompt or self.worker: return
        model = self.main.settings.value('ollama_model', '')
        if not model:
            QMessageBox.information(self, 'AI', 'Kies eerst een Ollama-model in Instellingen.')
            return
        persona = self.main.library.read_persona()
        context_text, context_label = self.main.build_ai_context(self.context.currentText(), prompt)
        system = ('Je bent de schrijf- en redactieassistent van de gebruiker. Gebruik ALTIJD het onderstaande '
                  'schrijversprofiel als vaste persona. Pas nooit rechtstreeks manuscriptbestanden aan. '
                  'Geef wijzigingen, herschrijvingen en suggesties uitsluitend in je antwoord.\n\n'
                  f'SCHRIJVERSPROFIEL:\n{persona}\n\nCONTEXT ({context_label}):\n{context_text}')
        self.chat.append(f'<b>Jij</b><br>{prompt.replace(chr(10), "<br>")}<br>')
        self.chat.append('<b>AI</b><br>')
        self.input.clear(); self.current_assistant = ''; self._final_started = False
        self._start_thinking()
        self.worker = ChatWorker(self.main.settings.value('ollama_url','http://127.0.0.1:11434'), model,
                                 [{'role':'system','content':system},{'role':'user','content':prompt}])
        self.worker.token.connect(self._token)
        self.worker.thinking.connect(self._thinking)
        self.worker.failed.connect(self._fail)
        self.worker.finished_ok.connect(self._done)
        self.worker.start()

    def _start_thinking(self):
        self._thinking_dots = 0
        self.thinking_details.clear()
        self.thinking_details.hide()
        self.thinking_button.setText('Denken…')
        self.thinking_button.show()
        self.thinking_timer.start()

    def _animate_thinking(self):
        self._thinking_dots = (self._thinking_dots + 1) % 4
        self.thinking_button.setText('Denken' + '.' * (self._thinking_dots + 1))

    def _toggle_thinking_details(self):
        if self.thinking_details.toPlainText().strip():
            self.thinking_details.setVisible(not self.thinking_details.isVisible())

    def _thinking(self, text):
        cur = self.thinking_details.textCursor(); cur.movePosition(QTextCursor.End); cur.insertText(text); self.thinking_details.setTextCursor(cur)

    def _finish_thinking(self):
        self.thinking_timer.stop()
        self.thinking_details.clear()
        self.thinking_details.hide()
        self.thinking_button.hide()

    def _token(self, text):
        if not self._final_started:
            self._final_started = True
            self._finish_thinking()
        self.current_assistant += text
        cur = self.chat.textCursor(); cur.movePosition(QTextCursor.End); cur.insertText(text); self.chat.setTextCursor(cur)

    def _done(self):
        self._finish_thinking()
        self.chat.append('<br>')
        self.worker = None

    def _fail(self, err):
        self._finish_thinking()
        self.chat.append(f'<br><i>Fout: {err}</i><br>')
        self.worker = None


class EditorPage(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.book = None; self.chapter = None; self.dirty = False
        self.autosave_timer = QTimer(self); self.autosave_timer.setSingleShot(True); self.autosave_timer.setInterval(3000); self.autosave_timer.timeout.connect(self.save)

        root = QHBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.left_split = QSplitter(Qt.Horizontal)
        self.manuscript = QWidget(); self.manuscript.setObjectName('panel'); ml = QVBoxLayout(self.manuscript); ml.setContentsMargins(14,14,14,14)
        head = QHBoxLayout(); title = QLabel('Manuscript'); title.setObjectName('sectionTitle'); add = QPushButton('+ Toevoegen'); add.clicked.connect(self.add_menu)
        head.addWidget(title); head.addStretch(); head.addWidget(add)
        self.tree = QTreeWidget(); self.tree.setHeaderHidden(True); self.tree.itemClicked.connect(self.tree_clicked)
        self.book_words = QLabel('0 woorden'); self.book_words.setObjectName('muted')
        ml.addLayout(head); ml.addWidget(self.tree); ml.addWidget(self.book_words)

        self.center = QWidget(); cl = QVBoxLayout(self.center); cl.setContentsMargins(0,0,0,0); cl.setSpacing(0)
        topbar = QFrame(); topbar.setObjectName('editorTopbar'); tl = QHBoxLayout(topbar); tl.setContentsMargins(14,8,18,8)
        undo = QPushButton(); undo.setObjectName('compactButton'); undo.setIcon(icon('undo')); undo.setIconSize(QSize(22,22)); undo.setToolTip('Ongedaan maken')
        redo = QPushButton(); redo.setObjectName('compactButton'); redo.setIcon(icon('redo')); redo.setIconSize(QSize(22,22)); redo.setToolTip('Opnieuw')
        self.book_title_label = QLabel(''); self.book_title_label.setObjectName('bookTitleLabel')
        tl.addWidget(undo); tl.addWidget(redo); tl.addSpacing(8); tl.addWidget(self.book_title_label); tl.addStretch()
        self.chapter_title = QLineEdit(); self.chapter_title.setPlaceholderText('Hoofdstuktitel'); self.chapter_title.setAlignment(Qt.AlignCenter); self.chapter_title.setObjectName('chapterTitle')
        self.chapter_title.editingFinished.connect(self.rename_current)
        self.editor = ManuscriptEditor(); self.editor.setObjectName('editor'); self.editor.textChanged.connect(self.on_text_changed)
        undo.clicked.connect(self.editor.undo); redo.clicked.connect(self.editor.redo)
        self.dictionary = WordDictionary(); self.highlighter = SpellHighlighter(self.editor.document(), self.dictionary)
        cl.addWidget(topbar); cl.addWidget(self.chapter_title); cl.addWidget(self.editor)

        self.right = QStackedWidget(); self.right.setObjectName('panel'); self.right.setMinimumWidth(280)
        self.search = SearchPanel(); self.ai = AIPanel(main)
        self.right.addWidget(self.search); self.right.addWidget(self.ai)
        self.search.query.textChanged.connect(self.do_search); self.search.only_chapter.stateChanged.connect(lambda _: self.do_search(self.search.query.text())); self.search.open_chapter.connect(self.open_chapter_id)

        self.left_split.addWidget(self.manuscript); self.left_split.addWidget(self.center); self.left_split.addWidget(self.right)
        self.left_split.setStretchFactor(0,0); self.left_split.setStretchFactor(1,1); self.left_split.setStretchFactor(2,0)
        self.left_split.setSizes([280, 800, 360])
        root.addWidget(self.left_split)

    def load_book(self, book):
        self.save(); self.book = book; self.chapter = None; self.book_title_label.setText(book.title); self.populate_tree()
        first = next((c for s in book.sections for c in s.chapters), None)
        if first: self.open_chapter(first)
        self.main.search_index.rebuild_book(book)

    def populate_tree(self):
        self.tree.clear()
        if not self.book: return
        for section in self.book.sections:
            if section.id == 'root' and len(self.book.sections)==1:
                for chapter in section.chapters:
                    it = QTreeWidgetItem([chapter.title]); it.setData(0, Qt.UserRole, ('chapter', chapter.id)); self.tree.addTopLevelItem(it)
            else:
                sit = QTreeWidgetItem([section.title]); sit.setData(0, Qt.UserRole, ('section', section.id)); self.tree.addTopLevelItem(sit)
                for chapter in section.chapters:
                    cit = QTreeWidgetItem([chapter.title]); cit.setData(0, Qt.UserRole, ('chapter', chapter.id)); sit.addChild(cit)
                sit.setExpanded(True)

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
        self.dirty = False; self.update_counts()

    def on_text_changed(self):
        self.dirty = True; self.update_counts()
        if self.main.settings.value('autosave', True, bool): self.autosave_timer.start()

    def save(self):
        if self.book and self.chapter and self.dirty:
            self.main.library.save_chapter(self.book, self.chapter, self.editor.toPlainText()); self.dirty = False
            self.main.search_index.rebuild_book(self.book); self.update_counts(saved=True)

    def rename_current(self):
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
        if not self.book: return
        choices = ['Nieuw hoofdstuk', 'Nieuwe sectie']
        choice, ok = QInputDialog.getItem(self, 'Toevoegen', 'Wat wil je toevoegen?', choices, 0, False)
        if not ok: return
        if choice == 'Nieuwe sectie':
            title, ok = QInputDialog.getText(self, 'Nieuwe sectie', 'Naam:')
            if ok: self.main.library.add_section(self.book, title or 'Nieuwe sectie'); self.populate_tree()
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

    def close_book(self):
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
        self.main.status.clearMessage()

    def do_search(self, q):
        if not self.book:
            return
        rows = self.main.search_index.search(self.book.id, q)
        if self.search.only_chapter.isChecked() and self.chapter:
            rows = [row for row in rows if row[0] == self.chapter.id]
        self.search.show_results(rows)

    def toggle_manuscript(self):
        self.manuscript.setVisible(not self.manuscript.isVisible())
        self.main.sync_tool_buttons()

    def toggle_right(self):
        self.right.setVisible(not self.right.isVisible())
        self.main.sync_tool_buttons()

    def _toggle_right_widget(self, widget, focus_widget):
        if self.right.isVisible() and self.right.currentWidget() is widget:
            self.right.hide()
        else:
            self.right.setCurrentWidget(widget)
            self.right.show()
            focus_widget.setFocus()
        self.main.sync_tool_buttons()

    def show_search(self):
        self._toggle_right_widget(self.search, self.search.query)

    def show_ai(self):
        self._toggle_right_widget(self.ai, self.ai.input)


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
        for page in (self.start, self.editor_page, self.stories, self.persona): self.stack.addWidget(page)
        root.addWidget(self.rail); root.addWidget(self.stack, 1)

        self.nav_buttons = []
        self.menu_button = self._nav_button('menu', 'Menu', self.toggle_nav, checkable=False)
        self.rail_layout.addSpacing(8)
        self.bookshelf_button = self._nav_button('shelf', 'Boekenplank', self.go_home)
        self.write_button = self._nav_button('books', 'Manuscript', self.show_editor)
        self.book_details_button = self._nav_button('edit', 'Boekdetails', self.open_current_book_details, checkable=False)
        self.stories_button = self._nav_button('stories', 'Verhalen', self.show_stories)
        self.persona_button = self._nav_button('persona', 'Schrijverspersona', self.show_persona)
        self.rail_layout.addStretch()
        self.settings_button = self._nav_button('settings', 'Instellingen', self.open_settings, checkable=False)

        # Rechter gereedschapsrail: alleen actief in het manuscript.
        self.toolrail = QFrame(); self.toolrail.setObjectName('toolrail'); self.toolrail.setFixedWidth(64)
        tr=QVBoxLayout(self.toolrail); tr.setContentsMargins(8,10,8,10); tr.setSpacing(7)
        def trb(icon_name, tip, fn):
            b=QPushButton(); b.setObjectName('railButton'); b.setIcon(icon(icon_name)); b.setIconSize(QSize(28,28)); b.setFixedSize(48,48); b.setToolTip(tip); b.setCheckable(True); b.clicked.connect(fn); tr.addWidget(b); return b
        self.search_button = trb('search','Zoeken', self.editor_page.show_search)
        self.ai_button = trb('spark','AI-assistent', self.editor_page.show_ai)
        self.manuscript_button = trb('panel-left','Hoofdstukpaneel tonen/verbergen', self.editor_page.toggle_manuscript)
        self.right_button = trb('panel-right','Rechterpaneel tonen/verbergen', self.editor_page.toggle_right)
        tr.addStretch(); root.addWidget(self.toolrail)

        self.start.open_book.connect(self.open_book); self.start.new_book.connect(self.new_book); self.start.manage_book.connect(self.manage_book)
        self.restore_state(); self._apply_nav_width()
        self.stack.currentChanged.connect(self._mode_changed); self._mode_changed(0)

        save = QAction('Opslaan', self); save.setShortcut('Ctrl+S'); save.triggered.connect(self.editor_page.save); self.addAction(save)
        focus_left = QAction(self); focus_left.setShortcut('Ctrl+Shift+L'); focus_left.triggered.connect(self.editor_page.toggle_manuscript); self.addAction(focus_left)
        focus_right = QAction(self); focus_right.setShortcut('Ctrl+Shift+R'); focus_right.triggered.connect(self.editor_page.toggle_right); self.addAction(focus_right)

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
        for b in (self.bookshelf_button, self.write_button, self.stories_button, self.persona_button): b.setChecked(False)
        if current is self.start: self.bookshelf_button.setChecked(True)
        elif current is self.editor_page: self.write_button.setChecked(True)
        elif current is self.stories: self.stories_button.setChecked(True)
        elif current is self.persona: self.persona_button.setChecked(True)

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

    def open_book(self, book):
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
            if self.settings.value('workspace') != old_root:
                QMessageBox.information(self,'Werkmap gewijzigd','De nieuwe werkmap wordt gebruikt nadat de applicatie opnieuw is gestart.')

    def sync_tool_buttons(self):
        if not hasattr(self, 'search_button'): return
        in_editor = self.stack.currentWidget() is self.editor_page
        right_visible = self.editor_page.right.isVisible() and in_editor
        self.search_button.setChecked(right_visible and self.editor_page.right.currentWidget() is self.editor_page.search)
        self.ai_button.setChecked(right_visible and self.editor_page.right.currentWidget() is self.editor_page.ai)
        self.manuscript_button.setChecked(self.editor_page.manuscript.isVisible() and in_editor)
        self.right_button.setChecked(right_visible)

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
        hits=self.story_index.search(prompt, limit=5)
        parts=[]
        for h in hits:
            try:
                d=self.story_index.get(h['path']); body=d['body']
            except Exception:
                body=h.get('snippet','')
            parts.append(f"# {h['title']}\nTags: {h.get('tags','')}\nSynopsis: {h.get('synopsis','')}\n\n{body}")
        return '\n\n'.join(parts) if parts else '(Geen relevante oude verhalen gevonden.)', 'relevante verhalen uit bibliotheek'

    def closeEvent(self, event):
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
        if sp: self.editor_page.left_split.restoreState(sp)
        self.editor_page.manuscript.setVisible(self.settings.value('manuscript_visible', True, bool))
        self.editor_page.right.setVisible(self.settings.value('right_visible', False, bool))


def run():
    app=QApplication(sys.argv); app.setApplicationName(APP_NAME); app.setOrganizationName('QuietWriter')
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
        if infos and not settings.value('fast_model',''):
            smallest=min(infos, key=lambda m: m.get('size', 0) or 0)['name']
            settings.setValue('fast_model', smallest)
    except Exception:
        models=[]; splash.set_status('Ollama niet bereikbaar · editor blijft beschikbaar')
    QTimer.singleShot(450, splash.accept); splash.exec()
    win=MainWindow(settings,library,models); win.show(); return app.exec()
