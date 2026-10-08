
import copy
from pathlib import Path
from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QImageReader, QPixmap
from PySide6.QtWidgets import (
    QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QSizePolicy, QTextEdit, QVBoxLayout, QWidget
)
from ..storage import slugify
from ..migrations import FutureBookFormatError
from ..i18n import tr
from ..field_merge import merge_scalar_fields
from ..revisions import ExternalModificationError
from .dialogs import confirm
from .form_controls import QuietComboBox, QuietDateEdit, QuietSpinBox

class BookDetailsPage(QWidget):
    saved = Signal(object)
    deleted = Signal(object)

    def __init__(self, library, settings, book, parent=None, before_delete=None):
        super().__init__(parent)
        self.library = library
        self.main = parent
        self.before_delete = before_delete
        self.settings = settings
        self.book = book
        self.old_slug = book.slug
        self.pending_cover = None
        self._baseline_title = book.title
        self._baseline_metadata = copy.deepcopy(book.metadata or {})
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
        self.language = QuietComboBox(); self.language.addItem(tr('book_details.language.nl', 'Nederlands'), 'nl'); self.language.addItem(tr('book_details.language.en', 'Engels'), 'en'); self.language.addItem(tr('book_details.language.de', 'Duits'), 'de'); self.language.addItem(tr('book_details.language.fr', 'Frans'), 'fr'); self.language.addItem(tr('book_details.language.es', 'Spaans'), 'es')
        lang_index = self.language.findData(str(md.get('language', 'nl') or 'nl')); self.language.setCurrentIndex(max(0, lang_index))
        self.tags = QLineEdit(md.get('tags',''))
        self.published = QuietComboBox(); self.published.addItem(tr('common.no', 'Nee'), 'No'); self.published.addItem(tr('common.yes', 'Ja'), 'Yes')
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

        # Schrijfdoel en Boekomslag gebruiken hetzelfde formulierpatroon als de rest
        # van Boekdetails: rustige sectiekop + uitleg, daarna labels links en bediening rechts.
        self.word_goal = QuietSpinBox(); self.word_goal.setRange(0, 10_000_000); self.word_goal.setSingleStep(1000); self.word_goal.setSpecialValueText(tr('writing_goal.none', 'Geen doel'))
        self.word_goal.setValue(max(0, int(md.get('writing_goal_words', 0) or 0)))
        self.goal_date = QuietDateEdit(); self.goal_date.setObjectName('quietDateEdit'); self.goal_date.setCalendarPopup(True); self.goal_date.setDisplayFormat('dd-MM-yyyy')
        self.goal_date.setDate(QDate.currentDate()); self.goal_date.setMinimumWidth(150); self.goal_date.setMaximumWidth(180)
        target_date = QDate.fromString(str(md.get('writing_goal_date', '') or ''), 'yyyy-MM-dd')
        self.goal_date_mode = QuietComboBox()
        self.goal_date_mode.addItem(tr('writing_goal.date_mode_none', 'Geen einddatum'), False)
        self.goal_date_mode.addItem(tr('writing_goal.date_mode_use', 'Einddatum gebruiken'), True)
        self.goal_date_mode.setMaximumWidth(210)
        self.goal_date_mode.setCurrentIndex(1 if target_date.isValid() else 0)
        if target_date.isValid(): self.goal_date.setDate(target_date)
        date_control = QWidget(); date_line = QHBoxLayout(date_control); date_line.setContentsMargins(0,0,0,0); date_line.setSpacing(8)
        date_line.addWidget(self.goal_date_mode); date_line.addWidget(self.goal_date); date_line.addStretch()
        self.goal_summary = QLabel(''); self.goal_summary.setObjectName('muted'); self.goal_summary.setWordWrap(True)

        goal_heading = self._details_section_heading(
            tr('writing_goal.title', 'Schrijfdoel'),
            tr('writing_goal.intro', 'Stel een woorddoel in en kies eventueel een gewenste einddatum.'),
        )
        form.addRow(goal_heading)
        form.addRow(tr('writing_goal.words', 'Woorddoel'), self.word_goal)
        form.addRow(tr('writing_goal.date', 'Gewenst klaar op'), date_control)
        form.addRow(tr('writing_goal.progress', 'Voortgang'), self.goal_summary)
        self.word_goal.valueChanged.connect(self._update_goal_state)
        self.goal_date.dateChanged.connect(self._update_goal_state)
        self.goal_date_mode.currentIndexChanged.connect(self._update_goal_state)
        self._update_goal_state()

        cover_heading = self._details_section_heading(
            tr('book_details.cover.title', 'Boekomslag'),
            tr('book_details.cover.requirements', 'Verhouding 1:1,6 · lange zijde minimaal 1024 px.'),
        )
        form.addRow(cover_heading)
        cover_control = QWidget(); cb = QHBoxLayout(cover_control); cb.setContentsMargins(0,0,0,0); cb.setSpacing(14)
        self.cover_preview = QLabel(); self.cover_preview.setObjectName('coverPlaceholder'); self.cover_preview.setFixedSize(100,160); self.cover_preview.setAlignment(Qt.AlignCenter)
        cover_right = QVBoxLayout(); cover_right.setContentsMargins(0,0,0,0); cover_right.setSpacing(8)
        self.cover_name = QLabel(''); self.cover_name.setObjectName('muted'); self.cover_name.setWordWrap(True)
        choose = QPushButton(tr('book_details.cover.choose', 'Omslag kiezen…')); choose.setObjectName('secondaryButton'); choose.clicked.connect(self.choose_cover)
        self.remove_cover_button = QPushButton(tr('book_details.cover.remove', 'Omslag verwijderen')); self.remove_cover_button.setObjectName('secondaryButton'); self.remove_cover_button.clicked.connect(self.remove_cover)
        self.header_path = QLabel(''); self.header_path.setObjectName('muted'); self.header_path.setWordWrap(True)
        cover_buttons = QHBoxLayout(); cover_buttons.setContentsMargins(0,0,0,0); cover_buttons.addWidget(choose); cover_buttons.addWidget(self.remove_cover_button); cover_buttons.addStretch()
        cover_right.addWidget(self.cover_name); cover_right.addLayout(cover_buttons); cover_right.addWidget(self.header_path); cover_right.addStretch()
        cb.addWidget(self.cover_preview); cb.addLayout(cover_right,1)
        form.addRow(tr('book_details.cover.field', 'Omslag'), cover_control)

        # Metadata groeit mee met toekomstige frontmattervelden; houd de acties
        # onderaan altijd bereikbaar door het inhoudsdeel scrollbaar te maken.
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget); details_layout.setContentsMargins(0,0,0,0)
        details_layout.addLayout(form); details_layout.addStretch()
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

    @staticmethod
    def _details_section_heading(title: str, help_text: str) -> QWidget:
        box = QWidget(); box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout = QVBoxLayout(box); layout.setContentsMargins(0, 18, 0, 6); layout.setSpacing(4)
        label = QLabel(title); label.setObjectName('settingsFieldLabel'); layout.addWidget(label)
        detail = QLabel(help_text); detail.setObjectName('muted'); detail.setWordWrap(True); layout.addWidget(detail)
        return box

    def _goal_date_iso(self) -> str:
        if self.word_goal.value() <= 0 or not bool(self.goal_date_mode.currentData()):
            return ''
        return self.goal_date.date().toString('yyyy-MM-dd')

    def _current_book_words(self) -> int:
        editor = getattr(self.main, 'editor_page', None)
        if editor is not None and getattr(editor, 'book', None) is not None and editor.book.id == self.book.id:
            try:
                editor._ensure_word_count_cache()
                return sum(editor._chapter_word_counts.values())
            except Exception:
                pass
        total = 0
        for section in self.book.sections:
            for chapter in section.chapters:
                try:
                    from ..manuscript_text import count_words
                    total += count_words(self.library.read_chapter(self.book, chapter))
                except Exception:
                    pass
        return total

    def _update_goal_state(self, *_):
        enabled = self.word_goal.value() > 0
        self.goal_date_mode.setEnabled(enabled)
        self.goal_date.setEnabled(enabled and bool(self.goal_date_mode.currentData()))
        if not enabled:
            self.goal_summary.setText(tr('writing_goal.summary_none', 'Geen woorddoel ingesteld.'))
            return
        current = self._current_book_words()
        target = int(self.word_goal.value())
        remaining = max(0, target - current)
        if remaining == 0:
            self.goal_summary.setText(tr('writing_goal.summary_complete', '{count} van {goal} woorden.', count=f'{current:,}'.replace(',', '.'), goal=f'{target:,}'.replace(',', '.')))
            return
        target_date = self.goal_date.date()
        if not bool(self.goal_date_mode.currentData()):
            self.goal_summary.setText(tr('writing_goal.summary_remaining', 'Nog {count} woorden.', count=f'{remaining:,}'.replace(',', '.')))
            return
        today = QDate.currentDate()
        if target_date < today:
            self.goal_summary.setText(tr('writing_goal.summary_expired', 'Nog {count} woorden · gewenste datum {date} is verstreken.', count=f'{remaining:,}'.replace(',', '.'), date=target_date.toString('dd-MM-yyyy')))
            return
        days = max(1, today.daysTo(target_date) + 1)
        raw = remaining / days if remaining else 0
        pace = max(1, int(round(raw)) if raw < 10 else int(round(raw / 10.0) * 10))
        self.goal_summary.setText(tr('writing_goal.summary_pace', 'Nog {count} woorden · ongeveer {pace} per dag tot {date}.', count=f'{remaining:,}'.replace(',', '.'), pace=f'{pace:,}'.replace(',', '.'), date=target_date.toString('dd-MM-yyyy')))

    @staticmethod
    def _canonical_published(value) -> str:
        return 'Yes' if str(value or '').strip().casefold() in {'yes', 'ja', 'true', '1'} else 'No'

    def _form_values(self) -> dict:
        return {
            'title': self.title_edit.text().strip(),
            'slug': self.slug_edit.text().strip(),
            'date': self.date_edit.text().strip(),
            'description': self.description.toPlainText().strip(),
            'intro': self.intro_text.toPlainText().strip(),
            'meta': self.meta.toPlainText().strip(),
            'image_alt': self.image_alt.toPlainText().strip(),
            'author': self.author.text().strip(),
            'language': self.language.currentData() or 'nl',
            'tags': self.tags.text().strip(),
            'published': self.published.currentData() or 'No',
            'synopsis': self.synopsis.toPlainText().strip(),
            'writing_goal_words': int(self.word_goal.value()),
            'writing_goal_date': self._goal_date_iso(),
        }

    def _book_values(self, book=None) -> dict:
        book = book or self.book
        md = book.metadata or {}
        return {
            'title': book.title,
            'slug': str(md.get('slug', '') or ''),
            'date': str(md.get('date', '') or ''),
            'description': str(md.get('description', '') or ''),
            'intro': str(md.get('intro', '') or ''),
            'meta': str(md.get('meta', '') or ''),
            'image_alt': str(md.get('image_alt', '') or ''),
            'author': str(md.get('author', '') or ''),
            'language': str(md.get('language', 'nl') or 'nl'),
            'tags': str(md.get('tags', '') or ''),
            'published': self._canonical_published(md.get('published', 'No')),
            'synopsis': str(md.get('synopsis', '') or ''),
            'writing_goal_words': max(0, int(md.get('writing_goal_words', 0) or 0)),
            'writing_goal_date': str(md.get('writing_goal_date', '') or ''),
        }

    def _baseline_values(self) -> dict:
        class _Baseline:
            pass
        baseline = _Baseline()
        baseline.title = self._baseline_title
        baseline.metadata = self._baseline_metadata
        return self._book_values(baseline)

    def has_pending_changes(self) -> bool:
        return self.pending_cover is not None or self._form_values() != self._baseline_values()

    def _candidate_with_form_values(self, base_book, values: dict):
        """Build a recovery-only Book carrying the current local form values."""
        candidate = copy.deepcopy(base_book)
        candidate.title = str(values.get('title', '') or '').strip() or base_book.title
        raw_slug = str(values.get('slug', '') or '').strip()
        candidate.metadata.update({
            'slug': slugify(raw_slug or candidate.title),
            'date': str(values.get('date', '') or ''),
            'description': str(values.get('description', '') or ''),
            'intro': str(values.get('intro', '') or ''),
            'meta': str(values.get('meta', '') or ''),
            'image_alt': str(values.get('image_alt', '') or ''),
            'author': str(values.get('author', '') or ''),
            'language': str(values.get('language', 'nl') or 'nl'),
            'tags': str(values.get('tags', '') or ''),
            'published': self._canonical_published(values.get('published', 'No')),
            'synopsis': str(values.get('synopsis', '') or ''),
            'writing_goal_words': max(0, int(values.get('writing_goal_words', 0) or 0)),
            'writing_goal_date': str(values.get('writing_goal_date', '') or ''),
        })
        return candidate

    def _apply_form_values(self, values: dict):
        self.title_edit.setText(str(values.get('title', '') or ''))
        self.slug_edit.setText(str(values.get('slug', '') or ''))
        self.date_edit.setText(str(values.get('date', '') or ''))
        self.description.setPlainText(str(values.get('description', '') or ''))
        self.intro_text.setPlainText(str(values.get('intro', '') or ''))
        self.meta.setPlainText(str(values.get('meta', '') or ''))
        self.image_alt.setPlainText(str(values.get('image_alt', '') or ''))
        self.author.setText(str(values.get('author', '') or ''))
        idx = self.language.findData(values.get('language', 'nl')); self.language.setCurrentIndex(max(0, idx))
        self.tags.setText(str(values.get('tags', '') or ''))
        idx = self.published.findData(self._canonical_published(values.get('published', 'No'))); self.published.setCurrentIndex(max(0, idx))
        self.synopsis.setPlainText(str(values.get('synopsis', '') or ''))
        self.word_goal.setValue(max(0, int(values.get('writing_goal_words', 0) or 0)))
        parsed_goal_date = QDate.fromString(str(values.get('writing_goal_date', '') or ''), 'yyyy-MM-dd')
        self.goal_date_mode.setCurrentIndex(1 if parsed_goal_date.isValid() else 0)
        self.goal_date.setDate(parsed_goal_date if parsed_goal_date.isValid() else QDate.currentDate())
        self._update_goal_state()

    def prepare_adoption(self, book):
        """Calculate the metadata merge and preserve conflicts before commit."""
        current = self._form_values()
        previous = self._baseline_values()
        incoming = self._book_values(book)
        keys = tuple(current.keys())
        merged, conflicts = merge_scalar_fields(current, previous, incoming, keys)

        if conflicts:
            local_candidate = self._candidate_with_form_values(book, current)
            self.library.create_version_with_file_overrides(
                book, {'book.json': self.library.manifest_text(local_candidate)}, kind='conflict_local'
            )
        return {'merged': merged, 'conflicts': bool(conflicts)}

    def adopt_book_preserving_form(self, book, *, prepared=None, show_message: bool = True):
        """Rebind live state with a three-way merge for dirty metadata fields.

        Local-only edits stay in the form. Disk-only edits are adopted. If the
        same field changed differently on both sides, the disk value stays live.
        Conflict preservation itself happens during MainWindow preflight.
        """
        plan = prepared if prepared is not None else self.prepare_adoption(book)
        merged = plan['merged']
        conflicts = bool(plan.get('conflicts'))

        self.book = book
        self._baseline_title = book.title
        self._baseline_metadata = copy.deepcopy(book.metadata or {})
        self.old_slug = book.slug
        self._apply_form_values(merged)

        if self.pending_cover is None:
            self._refresh_cover_preview()
        self._update_header_path()

        if conflicts and show_message:
            QMessageBox.information(
                self,
                tr('book_details.merge_conflict_title', 'Lokale invoer veilig bewaard'),
                tr(
                    'book_details.merge_conflict_text',
                    'Dezelfde boekgegevens zijn lokaal en extern gewijzigd. '
                    'De versie op schijf is voor die velden geladen; je lokale invoer staat apart in Versiegeschiedenis.'
                ),
            )
        return conflicts

    def show_adoption_message(self, prepared):
        if prepared and prepared.get('conflicts'):
            QMessageBox.information(
                self,
                tr('book_details.merge_conflict_title', 'Lokale invoer veilig bewaard'),
                tr(
                    'book_details.merge_conflict_text',
                    'Dezelfde boekgegevens zijn lokaal en extern gewijzigd. '
                    'De versie op schijf is voor die velden geladen; je lokale invoer staat apart in Versiegeschiedenis.'
                ),
            )

    def _cover_candidate(self):
        if self.pending_cover == '__REMOVE__':
            return None
        return self.pending_cover or self.library.cover_path(self.book)

    def _refresh_cover_preview(self):
        path = self._cover_candidate()
        has_own_cover = bool(path and Path(path).exists())
        self.remove_cover_button.setEnabled(has_own_cover)
        self.cover_name.setText(str(path) if has_own_cover else tr('book_details.cover.none_found', 'Geen eigen omslag gekozen.'))
        if has_own_cover:
            pix = QPixmap(str(path))
            self.cover_preview.setPixmap(pix.scaled(self.cover_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.cover_preview.setText('')
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
        self._refresh_cover_preview()
        self._update_header_path()

    def save(self):
        title = self.title_edit.text().strip()
        slug = self.slug_edit.text().strip()
        if not title:
            QMessageBox.warning(self, tr('book_details.title', 'Boekdetails'), tr('book_details.title_required', 'Geef het boek een titel.')); return False
        if not slug:
            slug = slugify(title)
        # slug normaliseren zodat bestandsnamen en metadata voorspelbaar blijven.
        slug = slugify(slug)
        self.slug_edit.setText(slug)

        # BookDetails shares the live Book object with Editor/Planning/Export.
        # Never mutate that shared object before validation/persistence succeeds:
        # a failed save must leave later editor autosaves unable to commit these
        # rejected metadata changes accidentally.
        candidate = copy.deepcopy(self.book)
        candidate.title = title
        image_ref = self._image_ref_for(slug)
        candidate.metadata.update({
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
            'writing_goal_words': int(self.word_goal.value()),
            'writing_goal_date': self._goal_date_iso(),
        })
        try:
            self.library.save_book_details(self.book, candidate, self.pending_cover)
        except FutureBookFormatError:
            recovery = self._candidate_with_form_values(self.book, self._form_values())
            return self.main.preserve_local_and_close_future_book(
                self.book, state_book=recovery, context='book_details'
            ) if self.main else False
        except ExternalModificationError:
            # A normal Dropbox/external change must not turn the save guard into
            # a dead end. Reload first; adopt_active_book performs the existing
            # three-way form merge and preserves same-field conflicts in History.
            try:
                latest = self.library.load_book(self.book.path)
            except FutureBookFormatError:
                recovery = self._candidate_with_form_values(self.book, self._form_values())
                return self.main.preserve_local_and_close_future_book(
                    self.book, state_book=recovery, context='book_details'
                ) if self.main else False
            except Exception as e:
                QMessageBox.warning(
                    self, tr('book_details.title', 'Boekdetails'),
                    tr('book_details.reload_failed', 'Het boek is extern gewijzigd, maar de nieuwste versie kon niet veilig worden geladen. Je invoer blijft staan.\n\n{error}', error=e)
                )
                return False
            try:
                self.main.adopt_active_book(latest)
            except Exception as e:
                QMessageBox.warning(
                    self, tr('book_details.title', 'Boekdetails'),
                    tr('book_details.merge_failed', 'Het boek is extern gewijzigd. Je invoer blijft staan, maar samenvoegen is mislukt.\n\n{error}', error=e)
                )
                return False
            QMessageBox.information(
                self, tr('book_details.external_title', 'Boek extern gewijzigd'),
                tr('book_details.external_retry', 'De nieuwste versie is geladen en je lokale boekgegevens zijn behouden. Controleer de gegevens en sla daarna opnieuw op.')
            )
            return False
        except Exception as e:
            QMessageBox.warning(self, tr('book_details.title', 'Boekdetails'), tr('book_details.save_failed', 'Opslaan mislukt:\n{error}', error=e)); return False

        # Commit to the shared in-memory identity only after the guarded disk
        # transaction has succeeded. Sections/chapters are intentionally kept on
        # the existing object graph; BookDetails edits metadata only.
        self.book.title = candidate.title
        self.book.metadata = copy.deepcopy(candidate.metadata)
        self.old_slug = slug
        self.pending_cover = None
        self._baseline_title = self.book.title
        self._baseline_metadata = copy.deepcopy(self.book.metadata or {})
        self.settings.sync()
        self.saved.emit(self.book)
        return True

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
