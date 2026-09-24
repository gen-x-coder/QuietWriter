
from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImageReader, QPixmap
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QTextEdit, QVBoxLayout, QWidget
)
from ..storage import slugify
from ..i18n import tr
from .dialogs import confirm

class BookDetailsPage(QWidget):
    saved = Signal(object)
    deleted = Signal(object)

    def __init__(self, library, settings, book, parent=None, before_delete=None):
        super().__init__(parent)
        self.library = library
        self.before_delete = before_delete
        self.settings = settings
        self.book = book
        self.old_slug = book.slug
        self.pending_cover = None
        root = QVBoxLayout(self); root.setContentsMargins(42, 34, 42, 34); root.setSpacing(12)
        title = QLabel(tr('book_details.title', 'Boekdetails')); title.setObjectName('title')
        intro = QLabel(tr('book_details.intro', 'Deze gegevens horen bij het boek en worden gebruikt bij publicatie en export.'))
        intro.setObjectName('muted'); intro.setWordWrap(True)
        root.addWidget(title); root.addWidget(intro); root.addSpacing(8)

        form = QFormLayout()
        self.title_edit = QLineEdit(book.title)
        self.slug_edit = QLineEdit(book.slug)
        slug_box = QWidget(); sh = QHBoxLayout(slug_box); sh.setContentsMargins(0,0,0,0)
        make_slug = QPushButton(tr('book_details.from_title', 'Van titel'))
        make_slug.clicked.connect(lambda: self.slug_edit.setText(slugify(self.title_edit.text())))
        sh.addWidget(self.slug_edit); sh.addWidget(make_slug)
        md = book.metadata or {}
        self.date_edit = QLineEdit(md.get('date',''))
        self.description = QTextEdit(md.get('description','')); self.description.setMaximumHeight(82)
        self.intro_text = QTextEdit(md.get('intro','')); self.intro_text.setMaximumHeight(100)
        self.meta = QTextEdit(md.get('meta','')); self.meta.setMaximumHeight(82)
        self.image_alt = QTextEdit(md.get('image_alt','')); self.image_alt.setMaximumHeight(82)
        self.author = QLineEdit(md.get('author',''))
        self.language = QComboBox(); self.language.addItem(tr('book_details.language.nl', 'Nederlands'), 'nl'); self.language.addItem(tr('book_details.language.en', 'Engels'), 'en')
        lang_index = self.language.findData(str(md.get('language', 'nl') or 'nl')); self.language.setCurrentIndex(max(0, lang_index))
        self.tags = QLineEdit(md.get('tags',''))
        self.published = QComboBox(); self.published.addItem(tr('common.no', 'Nee'), 'No'); self.published.addItem(tr('common.yes', 'Ja'), 'Yes')
        published_value = str(md.get('published', 'No') or 'No').strip().casefold()
        published_canonical = 'Yes' if published_value in {'yes', 'ja', 'true', '1'} else 'No'
        self.published.setCurrentIndex(max(0, self.published.findData(published_canonical)))
        self.synopsis = QTextEdit(md.get('synopsis','')); self.synopsis.setMaximumHeight(82)
        form.addRow(tr('book_details.field.title', 'Titel'), self.title_edit)
        form.addRow(tr('book_details.field.date', 'Datum'), self.date_edit)
        form.addRow(tr('book_details.field.slug', 'Slug'), slug_box)
        form.addRow(tr('book_details.field.description', 'Korte beschrijving'), self.description)
        form.addRow(tr('book_details.field.intro', 'Intro boven het verhaal'), self.intro_text)
        form.addRow(tr('book_details.field.meta', 'Meta / SEO-beschrijving'), self.meta)
        form.addRow(tr('book_details.field.image_alt', 'Beschrijving afbeelding'), self.image_alt)
        form.addRow(tr('book_details.field.author', 'Auteur'), self.author)
        form.addRow(tr('book_details.field.language', 'Boektaal'), self.language)
        form.addRow(tr('book_details.field.tags', 'Tags'), self.tags)
        form.addRow(tr('book_details.field.published', 'Gepubliceerd'), self.published)
        form.addRow(tr('book_details.field.synopsis', 'Synopsis'), self.synopsis)

        cover_box = QFrame(); cover_box.setObjectName('panel')
        cb = QHBoxLayout(cover_box); cb.setContentsMargins(12,12,12,12)
        self.cover_preview = QLabel(); self.cover_preview.setFixedSize(100,160); self.cover_preview.setAlignment(Qt.AlignCenter)
        cover_right = QVBoxLayout()
        self.cover_name = QLabel(''); self.cover_name.setObjectName('muted'); self.cover_name.setWordWrap(True)
        choose = QPushButton(tr('book_details.cover.choose', 'Omslag kiezen…')); choose.clicked.connect(self.choose_cover)
        remove_cover = QPushButton(tr('book_details.cover.remove', 'Omslag verwijderen')); remove_cover.clicked.connect(self.remove_cover)
        self.header_path = QLabel(''); self.header_path.setObjectName('muted'); self.header_path.setWordWrap(True)
        cover_right.addWidget(QLabel(tr('book_details.cover.requirements', 'Boekomslag · verhouding 1:1,6 · lange zijde minimaal 1024 px')))
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
        delete = QPushButton(tr('book_details.trash', 'Naar prullenbak')); delete.setObjectName('dangerButton'); delete.clicked.connect(self.delete_book)
        actions.addWidget(delete); actions.addStretch()
        save_btn = QPushButton(tr('common.save', 'Opslaan')); save_btn.setObjectName('primaryButton'); save_btn.clicked.connect(self.save)
        actions.addWidget(save_btn); root.addLayout(actions)

    def _cover_candidate(self):
        if self.pending_cover == '__REMOVE__':
            return self.library.default_cover_path()
        return self.pending_cover or self.library.cover_path(self.book) or self.library.default_cover_path()

    def _refresh_cover_preview(self):
        path = self._cover_candidate()
        self.cover_name.setText(str(path) if path else tr('book_details.cover.none_found', 'Geen omslag gevonden; QuietWriter gebruikt de ingebouwde rustige standaardweergave.'))
        if path and Path(path).exists():
            pix = QPixmap(str(path))
            self.cover_preview.setPixmap(pix.scaled(self.cover_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.cover_preview.clear(); self.cover_preview.setText(tr('book_details.cover.none_short', 'Geen\nomslag'))

    def _current_cover_for_metadata(self):
        """Return the cover represented by the current UI state.

        A newly selected cover should already be reflected by Export even before
        the user presses Save.  Removing a cover likewise exports an empty image
        field.  This helper deliberately does not mutate/persist the cover.
        """
        if self.pending_cover == '__REMOVE__':
            return None
        if isinstance(self.pending_cover, Path):
            return self.pending_cover
        return self.library.cover_path(self.book)

    def _image_ref_for(self, slug: str) -> str:
        cover = self._current_cover_for_metadata()
        if not cover:
            return ''
        template = self.settings.value('cover_header_template', '/{slug}.jpg')
        ext = Path(cover).suffix.lstrip('.') or 'jpg'
        try:
            return str(template).format(slug=slug, ext=ext)
        except Exception:
            return f'/{slug}.{ext}'

    def _update_header_path(self):
        has_cover = self.pending_cover not in (None, '__REMOVE__') or (self.pending_cover is None and self.library.cover_path(self.book))
        if not has_cover:
            self.header_path.setText(tr('book_details.cover.metadata_empty', 'Afbeeldingspad in metadata: leeg (geen omslag)'))
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
        self.header_path.setText(tr('book_details.cover.metadata_path', 'Afbeeldingspad in metadata: {path}', path=path))

    def choose_cover(self):
        path, _ = QFileDialog.getOpenFileName(self, tr('book_details.cover.choose_title', 'Kies boekomslag'), str(self.library.covers_dir), tr('book_details.cover.filter', 'Afbeeldingen (*.jpg *.jpeg *.png *.webp)'))
        if not path: return
        reader = QImageReader(path)
        size = reader.size()
        if not size.isValid():
            QMessageBox.warning(self, tr('book_details.cover.title', 'Boekomslag'), tr('book_details.cover.unreadable', 'Deze afbeelding kon niet worden gelezen.')); return
        w, h = size.width(), size.height()
        ratio = w / h if h else 0
        if h < 1024:
            QMessageBox.warning(self, tr('book_details.cover.title', 'Boekomslag'), tr('book_details.cover.too_small', 'De lange zijde is {height}px. Gebruik minimaal 1024px.', height=h)); return
        if abs(ratio - (1/1.6)) > 0.035:
            QMessageBox.warning(self, tr('book_details.cover.title', 'Boekomslag'), tr('book_details.cover.bad_ratio', 'De verhouding is {width}:{height}. Gebruik ongeveer 1:1,6 (bijvoorbeeld 1024×1638).', width=w, height=h)); return
        self.pending_cover = Path(path)
        self._refresh_cover_preview(); self._update_header_path()

    def remove_cover(self):
        # De wijziging is meteen zichtbaar, maar wordt pas definitief bij Opslaan.
        self.pending_cover = '__REMOVE__'
        self.cover_name.setText(tr('book_details.cover.default_used', 'Geen eigen omslag. De standaardomslag wordt gebruikt.'))
        default = self.library.default_cover_path()
        if default and Path(default).exists():
            pix = QPixmap(str(default))
            self.cover_preview.setPixmap(pix.scaled(self.cover_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.cover_preview.clear(); self.cover_preview.setText(tr('book_details.cover.default_short', 'Standaard\nomslag'))
        self._update_header_path()

    def save(self):
        title = self.title_edit.text().strip()
        slug = self.slug_edit.text().strip()
        if not title:
            QMessageBox.warning(self, tr('book_details.title', 'Boekdetails'), tr('book_details.title_required', 'Geef het boek een titel.')); return
        if not slug:
            slug = slugify(title)
        # slug normaliseren zodat bestandsnamen en metadata voorspelbaar blijven.
        slug = slugify(slug)
        self.slug_edit.setText(slug)
        self.book.title = title
        image_ref = self._image_ref_for(slug)
        self.book.metadata.update({
            'slug': slug,
            'date': self.date_edit.text().strip(),
            'description': self.description.toPlainText().strip(),
            'intro': self.intro_text.toPlainText().strip(),
            'meta': self.meta.toPlainText().strip(),
            'image': image_ref,
            'image_alt': self.image_alt.toPlainText().strip(),
            'author': self.author.text().strip(),
            'language': self.language.currentData() or 'nl',
            'tags': self.tags.text().strip(),
            'published': self.published.currentData() or 'No',
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
            QMessageBox.warning(self, tr('book_details.title', 'Boekdetails'), tr('book_details.save_failed', 'Opslaan mislukt:\n{error}', error=e)); return
        self.old_slug = slug
        self.pending_cover = None
        self.saved.emit(self.book)

    def delete_book(self):
        if not confirm(
            self, tr('book_details.trash_title', 'Boek naar prullenbak'),
            tr('book_details.trash_confirm', 'Wil je “{title}” naar de prullenbak verplaatsen?\n\nJe kunt het boek later herstellen of definitief verwijderen vanaf de prullenbakpagina.', title=self.book.title)
        ):
            return
        if self.before_delete is not None and self.before_delete(self.book) is False:
            return
        try:
            self.library.delete_book(self.book)
        except Exception as e:
            QMessageBox.critical(self, tr('book_details.delete_title', 'Boek verwijderen'), str(e)); return
        self.deleted.emit(self.book)
