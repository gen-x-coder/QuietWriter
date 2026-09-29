from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QRadioButton, QScrollArea, QVBoxLayout, QWidget
)

from ..exporting import (
    ExportSettingsStore, TEMPLATES, build_export_document, export_epub,
    export_markdown, export_pdf, run_preflight,
)
from ..i18n import current_locale, tr
from ..revisions import ExternalModificationError
from ..storage import BookBlockedError, CorruptSourceError, StorageWriteError
from .dialogs import confirm


class ExportPage(QWidget):
    """Single lightweight home for EPUB/PDF/Markdown export.

    The page owns UI preferences only. Publication content remains in the existing
    PublicationStore and rendering receives a read-only ExportDocument snapshot.
    """

    def __init__(self, main):
        super().__init__(main)
        self.main = main
        self.book = None
        self.store = ExportSettingsStore(main.library)
        self.export_settings: dict = {}
        self.document = None
        self._corrupt_source = False
        self._loading_settings = False
        self.last_output: Path | None = None

        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        host = QWidget(); body = QVBoxLayout(host); body.setContentsMargins(42, 32, 42, 32); body.setSpacing(14)
        scroll.setWidget(host); root.addWidget(scroll)

        heading = QLabel(tr('export.title', 'Exporteren')); heading.setObjectName('title')
        self.subtitle = QLabel(''); self.subtitle.setObjectName('muted'); self.subtitle.setWordWrap(True)
        body.addWidget(heading); body.addWidget(self.subtitle); body.addSpacing(6)

        section = QLabel(tr('export.format', 'Formaat')); section.setObjectName('sectionTitle'); body.addWidget(section)
        formats = QHBoxLayout(); formats.setSpacing(10)
        self.format_group = QButtonGroup(self); self.format_group.setExclusive(True)
        self.epub_button = self._format_button('EPUB', tr('export.epub.short', 'Voor e-readers en e-bookapps'), 'epub')
        self.pdf_button = self._format_button('PDF', tr('export.pdf.short', 'Vaste pagina-opmaak voor lezen en print'), 'pdf')
        self.markdown_button = self._format_button('Markdown', tr('export.markdown.short', 'Uitwisselen en back-up'), 'markdown')
        for button in (self.epub_button, self.pdf_button, self.markdown_button): formats.addWidget(button, 1)
        body.addLayout(formats)

        self.preflight_box = QFrame(); self.preflight_box.setObjectName('softPanel')
        pre = QVBoxLayout(self.preflight_box); pre.setContentsMargins(14, 12, 14, 12); pre.setSpacing(5)
        pretitle = QLabel(tr('export.preflight.title', 'Exportcontrole')); pretitle.setObjectName('sectionTitle'); pre.addWidget(pretitle)
        self.preflight_label = QLabel(''); self.preflight_label.setWordWrap(True); self.preflight_label.setTextInteractionFlags(Qt.TextSelectableByMouse); pre.addWidget(self.preflight_label)
        body.addWidget(self.preflight_box)

        content_box = QFrame(); content_box.setObjectName('softPanel')
        cl = QVBoxLayout(content_box); cl.setContentsMargins(14, 12, 14, 12); cl.setSpacing(6)
        ct = QLabel(tr('export.content.title', 'Inhoud')); ct.setObjectName('sectionTitle'); cl.addWidget(ct)
        self.content_summary = QLabel(''); self.content_summary.setWordWrap(True); cl.addWidget(self.content_summary)
        publication_btn = QPushButton(tr('export.content.adjust', 'Publicatiestructuur aanpassen'))
        publication_btn.setObjectName('secondaryButton'); publication_btn.clicked.connect(self._open_publication_setup); cl.addWidget(publication_btn, 0, Qt.AlignLeft)
        body.addWidget(content_box)

        self.epub_panel = QFrame(); self.epub_panel.setObjectName('panel')
        el = QVBoxLayout(self.epub_panel); el.setContentsMargins(0, 6, 0, 0); el.setSpacing(10)
        et = QLabel(tr('export.appearance', 'Vormgeving')); et.setObjectName('sectionTitle'); el.addWidget(et)
        template_row = QHBoxLayout(); template_row.addWidget(QLabel(tr('export.template', 'Template')))
        self.template_combo = QComboBox();
        for key, template in TEMPLATES.items():
            label = template.name_en if current_locale() == 'en' else template.name_nl
            self.template_combo.addItem(label, key)
        template_row.addWidget(self.template_combo, 1); el.addLayout(template_row)
        self.template_help = QLabel(''); self.template_help.setObjectName('muted'); self.template_help.setWordWrap(True); el.addWidget(self.template_help)

        self.include_cover = QCheckBox(tr('export.cover.include', 'Boekomslag opnemen')); self.include_cover.setObjectName('publicationToggle'); el.addWidget(self.include_cover)
        cover_box = QFrame(); cover_box.setObjectName('softPanel'); cbl = QVBoxLayout(cover_box); cbl.setContentsMargins(12, 10, 12, 10); cbl.setSpacing(5)
        cover_title = QLabel(tr('export.cover.title', 'Tekst op de omslag')); cover_title.setObjectName('sectionTitle'); cbl.addWidget(cover_title)
        self.cover_art_only = QRadioButton(tr('export.cover.artwork_only', 'Mijn omslag heeft geen tekst — QuietWriter voegt titel en auteur toe'))
        self.cover_has_text = QRadioButton(tr('export.cover.has_text', 'Mijn omslag bevat al tekst — afbeelding ongewijzigd gebruiken'))
        for rb in (self.cover_art_only, self.cover_has_text): rb.setObjectName('publicationRadio'); cbl.addWidget(rb)
        self.cover_box = cover_box; el.addWidget(cover_box)
        self.show_sections = QCheckBox(tr('export.sections.show', 'Sectietitels als eigen pagina opnemen')); self.show_sections.setObjectName('publicationToggle'); el.addWidget(self.show_sections)
        epub_validation_help = QLabel(tr(
            'export.epub.validation_help',
            'QuietWriter controleert na export de EPUB-structuur en interne verwijzingen voordat het bestand wordt geplaatst.'
        ))
        epub_validation_help.setObjectName('muted'); epub_validation_help.setWordWrap(True); el.addWidget(epub_validation_help)
        body.addWidget(self.epub_panel)

        self.pdf_panel = QFrame(); self.pdf_panel.setObjectName('panel')
        pl = QVBoxLayout(self.pdf_panel); pl.setContentsMargins(0, 6, 0, 0); pl.setSpacing(10)
        pt = QLabel(tr('export.pdf.appearance', 'PDF-opmaak')); pt.setObjectName('sectionTitle'); pl.addWidget(pt)

        pdf_template_row = QHBoxLayout(); pdf_template_row.addWidget(QLabel(tr('export.template', 'Template')))
        self.pdf_template_combo = QComboBox()
        for key, template in TEMPLATES.items():
            label = template.name_en if current_locale() == 'en' else template.name_nl
            self.pdf_template_combo.addItem(label, key)
        pdf_template_row.addWidget(self.pdf_template_combo, 1); pl.addLayout(pdf_template_row)

        paper_row = QHBoxLayout(); paper_row.addWidget(QLabel(tr('export.pdf.paper', 'Boekformaat')))
        self.pdf_paper_combo = QComboBox(); self.pdf_paper_combo.addItem('A5', 'A5'); self.pdf_paper_combo.addItem('A4', 'A4')
        paper_row.addWidget(self.pdf_paper_combo, 1); pl.addLayout(paper_row)

        margin_row = QHBoxLayout(); margin_row.addWidget(QLabel(tr('export.pdf.margins', 'Marges')))
        self.pdf_margin_combo = QComboBox()
        self.pdf_margin_combo.addItem(tr('export.pdf.margin.compact', 'Compact'), 'compact')
        self.pdf_margin_combo.addItem(tr('export.pdf.margin.standard', 'Standaard'), 'standard')
        self.pdf_margin_combo.addItem(tr('export.pdf.margin.wide', 'Ruim'), 'wide')
        margin_row.addWidget(self.pdf_margin_combo, 1); pl.addLayout(margin_row)

        self.pdf_page_numbers = QCheckBox(tr('export.pdf.page_numbers', 'Paginanummers opnemen')); self.pdf_page_numbers.setObjectName('publicationToggle'); pl.addWidget(self.pdf_page_numbers)
        self.pdf_running_header = QCheckBox(tr('export.pdf.running_header', 'Boektitel als rustige lopende kop')); self.pdf_running_header.setObjectName('publicationToggle'); pl.addWidget(self.pdf_running_header)
        self.pdf_show_sections = QCheckBox(tr('export.sections.show', 'Sectietitels als eigen pagina opnemen')); self.pdf_show_sections.setObjectName('publicationToggle'); pl.addWidget(self.pdf_show_sections)
        pdf_help = QLabel(tr('export.pdf.help', 'PDF gebruikt vaste pagina-opmaak. Een afbeelding met tekstomloop en een lang onderschrift valt veilig terug op een gewoon links/rechts afbeeldingsblok.'))
        pdf_help.setObjectName('muted'); pdf_help.setWordWrap(True); pl.addWidget(pdf_help)
        body.addWidget(self.pdf_panel)

        self.markdown_panel = QFrame(); self.markdown_panel.setObjectName('softPanel')
        ml = QVBoxLayout(self.markdown_panel); ml.setContentsMargins(14, 12, 14, 12); ml.setSpacing(6)
        mt = QLabel(tr('export.markdown.fixed_title', 'Vast Markdown-formaat')); mt.setObjectName('sectionTitle'); ml.addWidget(mt)
        markdown_help = QLabel(tr(
            'export.markdown.fixed_help',
            'QuietWriter gebruikt altijd je vaste publicatieheader: title, date, slug, description, meta, intro, author en tags. Bij één los verhaal wordt geen overbodige hoofdstukkop toegevoegd.'
        ))
        markdown_help.setObjectName('muted'); markdown_help.setWordWrap(True); ml.addWidget(markdown_help)
        body.addWidget(self.markdown_panel)

        output_box = QFrame(); output_box.setObjectName('softPanel')
        ol = QVBoxLayout(output_box); ol.setContentsMargins(14, 12, 14, 12); ol.setSpacing(7)
        ot = QLabel(tr('export.output.title', 'Uitvoer')); ot.setObjectName('sectionTitle'); ol.addWidget(ot)
        output_row = QHBoxLayout(); self.output_label = QLabel(''); self.output_label.setObjectName('muted'); self.output_label.setWordWrap(True)
        choose_output = QPushButton(tr('export.output.choose', 'Exportmap…')); choose_output.setObjectName('secondaryButton'); choose_output.clicked.connect(self._choose_output_dir)
        output_row.addWidget(self.output_label, 1); output_row.addWidget(choose_output); ol.addLayout(output_row)
        body.addWidget(output_box)

        self.success_box = QFrame(); self.success_box.setObjectName('softPanel'); self.success_box.hide()
        sl = QVBoxLayout(self.success_box); sl.setContentsMargins(14, 12, 14, 12); sl.setSpacing(7)
        self.success_label = QLabel(''); self.success_label.setWordWrap(True); self.success_label.setTextInteractionFlags(Qt.TextSelectableByMouse); sl.addWidget(self.success_label)
        success_buttons = QHBoxLayout(); self.open_file_button = QPushButton(tr('export.open_file', 'Bestand openen')); self.open_file_button.clicked.connect(self._open_file)
        self.open_folder_button = QPushButton(tr('export.open_folder', 'Map openen')); self.open_folder_button.clicked.connect(self._open_folder)
        success_buttons.addWidget(self.open_file_button); success_buttons.addWidget(self.open_folder_button); success_buttons.addStretch(); sl.addLayout(success_buttons)
        body.addWidget(self.success_box)

        actions = QHBoxLayout(); actions.addStretch(); self.export_button = QPushButton(tr('export.action.epub', 'EPUB exporteren')); self.export_button.setObjectName('primaryButton'); self.export_button.clicked.connect(self._export); actions.addWidget(self.export_button); body.addLayout(actions); body.addStretch()

        self.format_group.buttonClicked.connect(self._format_changed)
        self.template_combo.currentIndexChanged.connect(self._options_changed)
        self.include_cover.toggled.connect(self._options_changed)
        self.cover_art_only.toggled.connect(self._options_changed)
        self.cover_has_text.toggled.connect(self._options_changed)
        self.show_sections.toggled.connect(self._options_changed)
        self.pdf_template_combo.currentIndexChanged.connect(self._options_changed)
        self.pdf_paper_combo.currentIndexChanged.connect(self._options_changed)
        self.pdf_margin_combo.currentIndexChanged.connect(self._options_changed)
        self.pdf_page_numbers.toggled.connect(self._options_changed)
        self.pdf_running_header.toggled.connect(self._options_changed)
        self.pdf_show_sections.toggled.connect(self._options_changed)

    def _format_button(self, title: str, description: str, key: str) -> QPushButton:
        button = QPushButton(f'{title}\n{description}')
        button.setObjectName('exportFormatCard'); button.setCheckable(True); button.setMinimumHeight(76)
        button.setProperty('formatKey', key); self.format_group.addButton(button)
        return button

    @property
    def format_name(self) -> str:
        checked = self.format_group.checkedButton()
        return str(checked.property('formatKey')) if checked else 'epub'

    def set_book(self, book):
        self.book = book
        self.last_output = None; self.success_box.hide()
        self._corrupt_source = False
        if not book:
            self.setEnabled(False); return
        settings_path = self.store.path(book)
        if settings_path.exists():
            try:
                self.store.validate_source(book)
            except CorruptSourceError:
                self._corrupt_source = True
                self.setEnabled(False)
                self.subtitle.setText(tr('export.corrupt_settings', 'De exportinstellingen zijn beschadigd. Herstel ze eerst via Integriteit.'))
                return
        self.setEnabled(True)
        self._loading_settings = True
        self.export_settings = self.store.load(book)
        fmt = self.export_settings.get('format', 'epub')
        {'epub': self.epub_button, 'pdf': self.pdf_button, 'markdown': self.markdown_button}.get(fmt, self.epub_button).setChecked(True)
        epub = self.export_settings.get('epub', {})
        idx = self.template_combo.findData(epub.get('template', 'classic')); self.template_combo.setCurrentIndex(max(0, idx))
        self.include_cover.setChecked(bool(epub.get('include_cover', True)))
        if epub.get('cover_mode') == 'artwork_with_text': self.cover_has_text.setChecked(True)
        else: self.cover_art_only.setChecked(True)
        self.show_sections.setChecked(bool(epub.get('show_section_titles', True)))
        pdf = self.export_settings.get('pdf', {})
        idx = self.pdf_template_combo.findData(pdf.get('template', 'classic')); self.pdf_template_combo.setCurrentIndex(max(0, idx))
        idx = self.pdf_paper_combo.findData(str(pdf.get('paper_size', 'A5')).upper()); self.pdf_paper_combo.setCurrentIndex(max(0, idx))
        idx = self.pdf_margin_combo.findData(pdf.get('margin_preset', 'standard')); self.pdf_margin_combo.setCurrentIndex(max(0, idx))
        self.pdf_page_numbers.setChecked(bool(pdf.get('page_numbers', True)))
        self.pdf_running_header.setChecked(bool(pdf.get('running_header', True)))
        self.pdf_show_sections.setChecked(bool(pdf.get('show_section_titles', True)))
        self.subtitle.setText(tr('export.subtitle', 'Maak een publicatiebestand van “{title}”.', title=book.title))
        self._refresh_document()
        self._refresh_output_dir()
        self._format_changed()
        self._loading_settings = False

    def refresh(self):
        if self.book: self.set_book(self.book)

    def _settings_from_ui(self) -> dict:
        settings = dict(self.export_settings or {})
        settings['format'] = self.format_name
        settings['epub'] = dict(settings.get('epub') or {})
        settings['epub'].update({
            'template': self.template_combo.currentData() or 'classic',
            'include_cover': self.include_cover.isChecked(),
            'cover_mode': 'artwork_with_text' if self.cover_has_text.isChecked() else 'artwork_only',
            'show_section_titles': self.show_sections.isChecked(),
        })
        settings['pdf'] = dict(settings.get('pdf') or {})
        settings['pdf'].update({
            'template': self.pdf_template_combo.currentData() or 'classic',
            'paper_size': self.pdf_paper_combo.currentData() or 'A5',
            'margin_preset': self.pdf_margin_combo.currentData() or 'standard',
            'page_numbers': self.pdf_page_numbers.isChecked(),
            'running_header': self.pdf_running_header.isChecked(),
            'show_section_titles': self.pdf_show_sections.isChecked(),
        })
        settings['markdown'] = {}
        return settings

    def _refresh_document(self):
        if not self.book: return
        try:
            self.document = build_export_document(self.main.library, self.book)
        except Exception:
            self.document = None
        self._refresh_summary(); self._refresh_preflight()

    def _refresh_summary(self):
        if not self.document:
            self.content_summary.setText(tr('export.content.unavailable', 'De inhoud kan nu niet worden gelezen.'))
            return
        front = len(self.document.front_matter); back = len(self.document.back_matter)
        self.content_summary.setText(tr(
            'export.content.summary',
            'Voorwerk: {front} onderdeel/onderdelen\nManuscript: {sections} sectie(s) · {chapters} hoofdstuk(ken)\nAchterwerk: {back} onderdeel/onderdelen',
            front=front, sections=len(self.document.sections), chapters=self.document.chapter_count, back=back,
        ))

    def _preflight_text(self, item) -> str:
        prefix = {'ok': '✓', 'warning': '⚠', 'error': '✕', 'info': '•'}.get(item.level, '•')
        values = {
            'title': tr('export.check.title', 'Titel: {value}', value=item.value or tr('export.check.missing', 'ontbreekt')),
            'author': tr('export.check.author', 'Auteur: {value}', value=item.value or tr('export.check.missing', 'ontbreekt')),
            'language': tr('export.check.language', 'Boektaal: {value}', value=item.value or tr('export.check.missing', 'ontbreekt')),
            'chapters': tr('export.check.chapters', '{value} hoofdstuk(ken)', value=item.value or '0'),
            'images': tr('export.check.images', '{value} afbeelding(en) in het manuscript', value=item.value or '0'),
            'missing_assets': tr('export.check.missing_assets', 'Een of meer afbeeldingen ontbreken of zijn gewijzigd:\n{value}', value=item.value),
            'markdown_images_pending': tr('export.check.markdown_images_pending', 'Markdown-export met afbeeldingen volgt in de volgende mediastap.'),
            'cover': tr('export.check.cover', 'Omslag: {value}', value=item.value),
            'cover_missing': tr('export.check.cover_missing', 'Geen eigen boekomslag; EPUB wordt zonder omslag gemaakt.'),
            'cover_disabled': tr('export.check.cover_disabled', 'Omslag is uitgeschakeld voor deze export.'),
            'isbn': tr('export.check.isbn', 'EPUB-ISBN: {value}', value=item.value) if item.value else tr('export.check.no_isbn', 'Geen EPUB-ISBN; boek-ID wordt als identifier gebruikt.'),
            'pdf_wrap_fallback': tr('export.check.pdf_wrap_fallback', '{value} afbeelding(en) met lang onderschrift worden in PDF zonder tekstomloop geplaatst.', value=item.value),
        }
        return f'{prefix} {values.get(item.key, item.key)}'

    def _refresh_preflight(self):
        if not self.document:
            self.preflight_label.setText(tr('export.check.failed', 'Exportcontrole kon niet worden uitgevoerd.'))
            self.export_button.setEnabled(False); return
        report = run_preflight(self.document, self.format_name, self._settings_from_ui())
        self.preflight_label.setText('\n'.join(self._preflight_text(item) for item in report.items))
        self.export_button.setEnabled(report.can_export)

    def _resolve_external_change(self, exc: ExternalModificationError):
        """Reload through the established live-book conflict path before retrying settings."""
        editor = self.main.editor_page
        publication_pending = False
        try:
            current = editor.content_stack.currentWidget()
            publication_pending = (
                current is editor.publication_editor and editor.publication_editor.has_pending_changes()
            ) or (
                current is editor.publication_setup and editor.publication_setup.has_pending_changes()
            )
        except Exception:
            publication_pending = False

        if bool(getattr(editor, 'dirty', False)) or publication_pending:
            editor._resolve_external_change(exc)
            self.book = getattr(self.main, '_active_book', None) or self.book
            self.refresh()
            return

        try:
            latest = self.main.library.load_book(self.book.path)
            self.main.adopt_active_book(
                latest,
                preferred_chapter_id=getattr(getattr(editor, 'chapter', None), 'id', None),
                planning_changed_files=exc.changed_files,
            )
            self.book = latest
            self.refresh()
            QMessageBox.information(
                self,
                tr('export.external_title', 'Boek extern gewijzigd'),
                tr('export.external_reloaded', 'Het boek is op een andere computer gewijzigd. De nieuwste versie is geladen. Kies je exportinstelling opnieuw.'),
            )
        except Exception as reload_error:
            QMessageBox.warning(
                self,
                tr('export.external_title', 'Boek extern gewijzigd'),
                tr('export.external_reload_failed', 'De exportinstelling is niet opgeslagen en de nieuwste versie kon niet veilig worden geladen. Er is niets overschreven.\n\n{error}', error=reload_error),
            )
            self.refresh()

    def _persist_settings(self) -> bool:
        if not self.book or self._corrupt_source or self._loading_settings:
            return True
        self.export_settings = self._settings_from_ui()
        try:
            self.store.save(self.book, self.export_settings)
            return True
        except ExternalModificationError as exc:
            self._resolve_external_change(exc)
            return False
        except (CorruptSourceError, BookBlockedError, StorageWriteError) as exc:
            QMessageBox.warning(
                self,
                tr('export.settings_save_title', 'Exportinstellingen niet opgeslagen'),
                str(exc),
            )
            return False

    def _format_changed(self, *args):
        fmt = self.format_name
        self.epub_panel.setVisible(fmt == 'epub')
        self.pdf_panel.setVisible(fmt == 'pdf')
        self.markdown_panel.setVisible(fmt == 'markdown')
        if fmt == 'markdown':
            self.export_button.setText(tr('export.action.markdown', 'Markdown exporteren'))
        elif fmt == 'pdf':
            self.export_button.setText(tr('export.action.pdf', 'PDF exporteren'))
        else:
            self.export_button.setText(tr('export.action.epub', 'EPUB exporteren'))
        self.export_settings = self._settings_from_ui()
        if not self._persist_settings():
            return
        self._options_changed()

    def _options_changed(self, *args):
        key = self.template_combo.currentData() or 'classic'
        template = TEMPLATES.get(key, TEMPLATES['classic'])
        self.template_help.setText(template.description_en if current_locale() == 'en' else template.description_nl)
        self.cover_box.setEnabled(self.include_cover.isChecked() and bool(self.document and self.document.cover_asset))
        if not self._persist_settings():
            return
        self._refresh_preflight()

    def _output_dir(self) -> Path:
        raw = str(self.main.settings.value('export/output_dir', '') or '').strip()
        path = Path(raw) if raw else (Path.home() / 'Documents')
        if not path.exists(): path = Path.home()
        return path

    def _refresh_output_dir(self):
        self.output_label.setText(tr('export.output.current', 'Exportmap: {path}', path=self._output_dir()))

    def _choose_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, tr('export.output.choose_title', 'Kies exportmap'), str(self._output_dir()))
        if path:
            self.main.settings.setValue('export/output_dir', path); self._refresh_output_dir()

    def _open_publication_setup(self):
        if not self.book: return
        self.main.show_editor()
        self.main.editor_page.show_publication_setup()

    def _export(self):
        if not self.book: return
        # Save any active manuscript/publication editor before capturing the snapshot.
        if self.main.editor_page.save() is False: return
        if self.main.planning_page.save_pending() is False: return
        try:
            self.document = build_export_document(self.main.library, self.book)
        except Exception as exc:
            QMessageBox.critical(self, tr('export.error.title', 'Exporteren'), tr('export.error.snapshot', 'De boeksnapshot kon niet veilig worden gemaakt.\n\n{error}', error=exc)); return
        self.export_settings = self._settings_from_ui()
        if not self._persist_settings(): return
        report = run_preflight(self.document, self.format_name, self.export_settings)
        self._refresh_preflight()
        if not report.can_export: return

        suffix = {'epub': '.epub', 'pdf': '.pdf', 'markdown': '.md'}[self.format_name]
        destination = self._output_dir() / f'{self.document.slug}{suffix}'
        if destination.exists() and not confirm(self, tr('export.overwrite.title', 'Bestand overschrijven'), tr('export.overwrite.text', '“{name}” bestaat al. Wil je dit bestand overschrijven?', name=destination.name)):
            return
        try:
            if self.format_name == 'epub':
                export_epub(self.document, destination, self.export_settings)
            elif self.format_name == 'pdf':
                export_pdf(self.document, destination, self.export_settings)
            else:
                export_markdown(self.document, destination, self.export_settings)
        except Exception as exc:
            QMessageBox.critical(self, tr('export.error.title', 'Exporteren'), tr('export.error.failed', 'Exporteren is mislukt.\n\n{error}', error=exc)); return
        self.last_output = destination
        if self.format_name == 'epub':
            self.success_label.setText(tr(
                'export.success.epub_validated',
                'EPUB voltooid en intern gecontroleerd:\n{path}',
                path=destination,
            ))
            status_text = tr('export.success.epub_validated.short', 'EPUB voltooid en gecontroleerd')
        else:
            self.success_label.setText(tr('export.success', 'Export voltooid:\n{path}', path=destination))
            status_text = tr('export.success.short', 'Export voltooid')
        self.success_box.show()
        self.main.status.showMessage(status_text, 2500)

    def _open_file(self):
        if self.last_output and self.last_output.exists(): QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_output)))

    def _open_folder(self):
        if self.last_output: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_output.parent)))
