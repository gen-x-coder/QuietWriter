"""Begeleid exporteren: a calm step-by-step mode of the Exporteren page.

Design rules (see documents/QUIETWRITER_ONTWERP_EXPORTWIZARD.md):
- The wizard is a mode of ExportPage, not a modal dialog, so the Controle step
  can send the writer to Boekdetails/Media and return to the same step.
- Choices are a draft. Nothing is written to export/settings.json until a
  successful export; switching to "Zelf instellen" discards the draft.
- Controle and Inhoud are read-only. They never repair anything themselves.
- Rendering uses the same route as the manual page (ExportPage.run_export_flow).
"""
from __future__ import annotations

from PySide6.QtCore import QEvent, QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QScrollArea, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from ..exporting import build_export_document, run_preflight
from ..exporting.purposes import (
    PURPOSES, STEP_APPEARANCE, STEP_CHECK, STEP_CONTENT, STEP_EXPORT, STEP_PURPOSE,
    apply_purpose, get_purpose, steps_for,
)
from ..exporting.runner import destination_for
from ..exporting.summary import build_content_summary, build_package_summary, round_words
from ..exporting.templates import TEMPLATES
from ..i18n import current_locale, tr
from ..publication_models import PUBLICATION_ITEMS

STEP_DONE = 'done'
COMPACT_WIDTH = 640


# ----------------------------------------------------------------------------
# Small formatting helpers (locale aware, no Qt locale dependency)
def _fmt_int(value: int) -> str:
    text = f'{int(value):,}'
    return text.replace(',', '.') if current_locale() != 'en' else text


def _fmt_size(num_bytes: int) -> str:
    mb = max(0, int(num_bytes)) / (1024 * 1024)
    if mb < 0.1:
        text = f'{max(1, int(num_bytes) // 1024)} kB'
    elif mb < 10:
        text = f'{mb:.1f} MB'
    else:
        text = f'{mb:.0f} MB'
    return text.replace('.', ',') if current_locale() != 'en' else text


def _safe_int(value) -> int:
    try:
        return int(str(value or '0'))
    except ValueError:
        return 0


def _clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
        elif item.layout() is not None:
            _clear_layout(item.layout())


def _label(text: str = '', name: str | None = None, wrap: bool = True) -> QLabel:
    label = QLabel(text)
    if name:
        label.setObjectName(name)
    label.setWordWrap(wrap)
    return label


def _purpose_texts(purpose_id: str) -> tuple[str, str, str]:
    """(title, description, format badge) for a purpose card."""
    return {
        'ereader': (
            tr('export.wizard.purpose.ereader', 'Lezen op een e-reader of telefoon'),
            tr('export.wizard.purpose.ereader_help', 'Voor Kobo, Kindle-app, Apple Boeken en telefoon. De tekst past zich aan het scherm aan.'),
            'EPUB',
        ),
        'print': (
            tr('export.wizard.purpose.print', 'Afdrukken of als PDF delen'),
            tr('export.wizard.purpose.print_help', "Vaste pagina's, zoals een echt boek. Voor proeflezers op papier of een drukker."),
            'PDF',
        ),
        'word': (
            tr('export.wizard.purpose.word', 'Laten redigeren in Word'),
            tr('export.wizard.purpose.word_help', 'Voor een redacteur of meelezer die opmerkingen en wijzigingen in Word zet.'),
            'DOCX',
        ),
        'share': (
            tr('export.wizard.purpose.share', 'Delen met een andere QuietWriter-gebruiker'),
            tr('export.wizard.purpose.share_help', 'Je hele boek in één bestand: tekst, afbeeldingen en Planning. Zonder je oude versies.'),
            'QWBOOK',
        ),
        'backup': (
            tr('export.wizard.purpose.backup', 'Een back-up voor mezelf'),
            tr('export.wizard.purpose.backup_help', 'Alles in één bestand, ook je versiegeschiedenis. QuietWriter kan het later volledig terugzetten.'),
            'QWBOOK',
        ),
        'website': (
            tr('export.wizard.purpose.website', 'Op een website of blog plaatsen'),
            tr('export.wizard.purpose.website_help', 'Platte tekst met een vaste kop, klaar om te plakken in je site.'),
            'Markdown',
        ),
    }[purpose_id]


def _kind_noun(purpose_id: str) -> str:
    """Short noun used in step headings: 'je e-book', 'je PDF' …"""
    return {
        'ereader': tr('export.wizard.kind.ereader', 'e-book'),
        'print': tr('export.wizard.kind.print', 'PDF'),
        'word': tr('export.wizard.kind.word', 'Word-bestand'),
        'share': tr('export.wizard.kind.share', 'bestand om te delen'),
        'backup': tr('export.wizard.kind.backup', 'back-up'),
        'website': tr('export.wizard.kind.website', 'websitebestand'),
    }.get(purpose_id, tr('export.wizard.kind.default', 'bestand'))


def _make_verb(purpose_id: str) -> str:
    return {
        'ereader': tr('export.wizard.make.ereader', 'E-book maken'),
        'print': tr('export.wizard.make.print', 'PDF maken'),
        'word': tr('export.wizard.make.word', 'Word-bestand maken'),
        'share': tr('export.wizard.make.share', 'Bestand om te delen maken'),
        'backup': tr('export.wizard.make.backup', 'Back-up maken'),
        'website': tr('export.wizard.make.website', 'Websitebestand maken'),
    }.get(purpose_id, tr('export.wizard.make.default', 'Exporteren'))


def _step_name(step: str) -> str:
    return {
        STEP_PURPOSE: tr('export.wizard.step.purpose', 'Doel'),
        STEP_CHECK: tr('export.wizard.step.check', 'Controle'),
        STEP_CONTENT: tr('export.wizard.step.content', 'Inhoud'),
        STEP_APPEARANCE: tr('export.wizard.step.appearance', 'Vormgeving'),
        STEP_EXPORT: tr('export.wizard.step.export', 'Exporteren'),
    }[step]


class _ChoiceCard(QPushButton):
    """Checkable card with a title, an optional badge and a one-line explanation."""

    def __init__(self, title: str, description: str, badge: str = '', preview: QWidget | None = None):
        super().__init__()
        self.setObjectName('exportPurposeCard')
        self.setCheckable(True)
        self.setAccessibleName(title)
        self.setAccessibleDescription(description)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout = QVBoxLayout(self); layout.setContentsMargins(14, 12, 14, 12); layout.setSpacing(5)
        if preview is not None:
            preview.setAttribute(Qt.WA_TransparentForMouseEvents)
            layout.addWidget(preview)
        top = QHBoxLayout(); top.setSpacing(8)
        self.title_label = _label(title, 'exportPurposeTitle')
        top.addWidget(self.title_label, 1)
        if badge:
            badge_label = _label(badge, 'formatBadge', wrap=False)
            badge_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            top.addWidget(badge_label, 0, Qt.AlignTop)
        layout.addLayout(top)
        self.description_label = _label(description, 'muted')
        layout.addWidget(self.description_label)
        layout.addStretch(1)
        for label in (self.title_label, self.description_label):
            label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._height_padding = 8 if preview is None else 0
        self.setMinimumHeight(layout.sizeHint().height() + self._height_padding)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        layout = self.layout()
        if layout is None or self.width() <= 0:
            return
        wanted = layout.heightForWidth(self.width())
        if wanted < 0:
            wanted = layout.sizeHint().height()
        wanted += self._height_padding
        if wanted != self.minimumHeight():
            self.setMinimumHeight(wanted)


class ExportWizard(QWidget):
    def __init__(self, page):
        super().__init__(page)
        self.page = page
        self.book = None
        self.purpose_id: str | None = None
        self.draft: dict = {}
        self.steps: tuple[str, ...] = steps_for(None)
        self.step: str = STEP_PURPOSE
        self.document = None
        self.report = None
        self.content = None
        self.package = None
        self.result = None
        self.snapshot_error: str = ''
        self._changed_notice = False
        self._compact = False
        self._first_issue_button = None

        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        # Step bar (not clickable; Terug/Volgende are the only navigation).
        bar_host = QWidget(); bar_host.setObjectName('wizardStepBar')
        bar_host.setMaximumWidth(820 + 84)
        bar = QVBoxLayout(bar_host); bar.setContentsMargins(42, 10, 42, 0); bar.setSpacing(0)
        self.step_row = QHBoxLayout(); self.step_row.setSpacing(22)
        self.step_labels: list[QLabel] = []
        bar.addLayout(self.step_row)
        self.step_compact = _label('', 'wizardStepCurrent', wrap=False)
        bar.addWidget(self.step_compact)
        line = QFrame(); line.setObjectName('wizardStepLine'); line.setFixedHeight(1)
        bar.addWidget(line)
        root.addWidget(bar_host)

        # Navigation deliberately sits directly below the step indicator instead of
        # at the bottom of the scrolling content. Writers can make a choice and
        # immediately see how to continue, while selection remains separate from
        # navigation (a card click never advances the wizard automatically).
        self.action_bar = QFrame(); self.action_bar.setObjectName('wizardActionBar')
        self.action_bar.setMaximumWidth(820 + 84)
        self.action_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        fl = QHBoxLayout(self.action_bar); fl.setContentsMargins(42, 10, 42, 10); fl.setSpacing(10)
        self.back_button = QPushButton(tr('export.wizard.back', 'Terug')); self.back_button.setObjectName('secondaryButton')
        self.hint_label = _label('', 'muted', wrap=False)
        self.extra_button = QPushButton(''); self.extra_button.setObjectName('secondaryButton')
        self.next_button = QPushButton(tr('export.wizard.next', 'Volgende')); self.next_button.setObjectName('primaryButton')
        fl.addWidget(self.back_button); fl.addStretch(1); fl.addWidget(self.hint_label, 0, Qt.AlignVCenter)
        fl.addWidget(self.extra_button); fl.addWidget(self.next_button)
        root.addWidget(self.action_bar)

        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setObjectName('wizardScroll')
        self.scroll.setMinimumHeight(0)
        self.scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        host = QWidget(); host_layout = QVBoxLayout(host); host_layout.setContentsMargins(42, 18, 42, 24); host_layout.setSpacing(0)
        self.pages = QStackedWidget()
        self.pages.currentChanged.connect(self._fit_pages)
        host_layout.addWidget(self.pages); host_layout.addStretch(1)
        host.setMaximumWidth(820 + 84)
        self.scroll.setWidget(host)
        root.addWidget(self.scroll, 1)
        self.back_button.clicked.connect(self.go_back)
        self.next_button.clicked.connect(self.go_next)
        self.extra_button.clicked.connect(self._extra_clicked)

        self._build_purpose_page()
        self._build_check_page()
        self._build_content_page()
        self._build_appearance_page()
        self._build_export_page()
        self._build_done_page()
        self._show_step(STEP_PURPOSE, focus=False)

    # ------------------------------------------------------------------ pages
    def _page(self) -> tuple[QWidget, QVBoxLayout]:
        widget = QWidget(); outer = QVBoxLayout(widget); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        layout = QVBoxLayout(); layout.setSpacing(14)
        outer.addLayout(layout); outer.addStretch(1)
        widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Ignored)
        self.pages.addWidget(widget)
        return widget, layout

    def _heading(self, layout: QVBoxLayout) -> tuple[QLabel, QLabel]:
        heading = _label('', 'wizardHeading'); intro = _label('', 'muted')
        box = QVBoxLayout(); box.setSpacing(4); box.addWidget(heading); box.addWidget(intro)
        layout.addLayout(box)
        return heading, intro

    def _build_purpose_page(self):
        self.purpose_page, layout = self._page()
        heading, intro = self._heading(layout)
        heading.setText(tr('export.wizard.purpose.heading', 'Wat wil je met je boek doen?'))
        intro.setText(tr('export.wizard.purpose.intro', 'Kies wat het dichtst in de buurt komt. QuietWriter kiest daarna het juiste formaat en goede standaardinstellingen.'))
        self.purpose_grid = QGridLayout(); self.purpose_grid.setHorizontalSpacing(10); self.purpose_grid.setVerticalSpacing(10)
        self.purpose_group = QButtonGroup(self); self.purpose_group.setExclusive(True)
        self.purpose_cards: dict[str, _ChoiceCard] = {}
        for purpose in PURPOSES:
            title, description, badge = _purpose_texts(purpose.id)
            card = _ChoiceCard(title, description, badge)
            card.setProperty('purposeId', purpose.id)
            card.installEventFilter(self)
            self.purpose_group.addButton(card)
            self.purpose_cards[purpose.id] = card
        self.purpose_group.buttonClicked.connect(self._purpose_clicked)
        self._layout_purpose_cards()
        layout.addLayout(self.purpose_grid)
        layout.addWidget(_label(tr('export.wizard.purpose.manual_hint', 'Weet je al precies welk formaat en welke instellingen je wilt? Kies rechtsboven Zelf instellen. QuietWriter onthoudt je keuze.'), 'muted'))

    def _layout_purpose_cards(self):
        while self.purpose_grid.count():
            self.purpose_grid.takeAt(0)
        columns = 1 if self._compact else 2
        for index, purpose in enumerate(PURPOSES):
            self.purpose_grid.addWidget(self.purpose_cards[purpose.id], index // columns, index % columns)

    def _build_check_page(self):
        self.check_page, layout = self._page()
        self.check_heading, self.check_intro = self._heading(layout)
        self.check_status = QFrame(); self.check_status.setObjectName('wizardStatusOk')
        sl = QVBoxLayout(self.check_status); sl.setContentsMargins(18, 14, 18, 14); sl.setSpacing(2)
        self.check_status_title = _label('', 'wizardStatusTitle'); self.check_status_text = _label('', None)
        sl.addWidget(self.check_status_title); sl.addWidget(self.check_status_text)
        layout.addWidget(self.check_status)
        self.changed_label = _label(tr('export.wizard.check.changed', 'Er is iets veranderd in je boek. Controleer opnieuw voordat je verdergaat.'), 'muted')
        layout.addWidget(self.changed_label)
        self.issue_box = QVBoxLayout(); self.issue_box.setSpacing(10)
        layout.addLayout(self.issue_box)
        self.ok_toggle = QPushButton(''); self.ok_toggle.setObjectName('linkButton'); self.ok_toggle.setCheckable(True)
        self.ok_toggle.toggled.connect(self._toggle_ok_rows)
        layout.addWidget(self.ok_toggle, 0, Qt.AlignLeft)
        self.ok_rows = QFrame(); self.ok_rows.setObjectName('wizardCard')
        self.ok_rows_layout = QVBoxLayout(self.ok_rows); self.ok_rows_layout.setContentsMargins(18, 8, 18, 8); self.ok_rows_layout.setSpacing(6)
        layout.addWidget(self.ok_rows)

    def _build_content_page(self):
        self.content_page, layout = self._page()
        self.content_heading, self.content_intro = self._heading(layout)
        self.content_body = QVBoxLayout(); self.content_body.setSpacing(14)
        layout.addLayout(self.content_body)

    def _build_appearance_page(self):
        self.appearance_page, layout = self._page()
        self.appearance_heading, self.appearance_intro = self._heading(layout)
        self.template_row = QHBoxLayout(); self.template_row.setSpacing(10)
        self.template_group = QButtonGroup(self); self.template_group.setExclusive(True)
        self.template_cards: dict[str, _ChoiceCard] = {}
        for key, template in TEMPLATES.items():
            name = template.name_en if current_locale() == 'en' else template.name_nl
            description = template.description_en if current_locale() == 'en' else template.description_nl
            card = _ChoiceCard(name, description, preview=self._template_preview(key))
            card.setProperty('templateKey', key)
            card.installEventFilter(self)
            self.template_group.addButton(card); self.template_cards[key] = card
            self.template_row.addWidget(card, 1)
        self.template_group.buttonClicked.connect(self._template_clicked)
        layout.addLayout(self.template_row)

        # EPUB: cover text mode.
        self.cover_card = QFrame(); self.cover_card.setObjectName('wizardCard')
        cl = QVBoxLayout(self.cover_card); cl.setContentsMargins(18, 14, 18, 14); cl.setSpacing(8)
        cl.addWidget(_label(tr('export.wizard.cover.question', 'Staat er al tekst op je omslag?'), 'sectionTitle'))
        self.cover_art_only = QRadioButton(tr('export.wizard.cover.art_only', 'Nee, alleen een afbeelding. QuietWriter zet titel en auteur erop.'))
        self.cover_has_text = QRadioButton(tr('export.wizard.cover.has_text', 'Ja, mijn omslag is al compleet. Gebruik hem zoals hij is.'))
        cover_group = QButtonGroup(self); cover_group.addButton(self.cover_art_only); cover_group.addButton(self.cover_has_text)
        for radio in (self.cover_art_only, self.cover_has_text):
            radio.setObjectName('publicationRadio'); radio.toggled.connect(self._appearance_changed); cl.addWidget(radio)
        layout.addWidget(self.cover_card)
        self.no_cover_label = _label(tr('export.wizard.cover.none', 'Je boek heeft nog geen omslag. Die kun je toevoegen in Boekdetails.'), 'muted')
        layout.addWidget(self.no_cover_label)

        # PDF: paper size.
        self.paper_card = QFrame(); self.paper_card.setObjectName('wizardCard')
        pl = QVBoxLayout(self.paper_card); pl.setContentsMargins(18, 14, 18, 14); pl.setSpacing(8)
        pl.addWidget(_label(tr('export.wizard.paper.question', 'Boekformaat'), 'sectionTitle'))
        self.paper_a5 = QRadioButton(tr('export.wizard.paper.a5', 'A5, zoals een paperback'))
        self.paper_a4 = QRadioButton(tr('export.wizard.paper.a4', 'A4, gewoon printpapier'))
        paper_group = QButtonGroup(self); paper_group.addButton(self.paper_a5); paper_group.addButton(self.paper_a4)
        for radio in (self.paper_a5, self.paper_a4):
            radio.setObjectName('publicationRadio'); radio.toggled.connect(self._appearance_changed); pl.addWidget(radio)
        self.page_numbers = QCheckBox(tr('export.wizard.paper.page_numbers', 'Paginanummers'))
        self.running_header = QCheckBox(tr('export.wizard.paper.running_header', 'Boektitel bovenaan de pagina'))
        for box in (self.page_numbers, self.running_header):
            box.setObjectName('publicationToggle'); box.toggled.connect(self._appearance_changed); pl.addWidget(box)
        layout.addWidget(self.paper_card)

        self.section_pages = QCheckBox(tr('export.wizard.sections', 'Elk deel begint met een eigen titelpagina'))
        self.section_pages.setObjectName('publicationToggle'); self.section_pages.toggled.connect(self._appearance_changed)
        layout.addWidget(self.section_pages)

    def _template_preview(self, key: str) -> QLabel:
        sample_title = tr('export.wizard.sample.title', 'Hoofdstuk 1')
        sample_1 = tr('export.wizard.sample.p1', 'De mist hing nog over het water toen Ilse de kade op liep.')
        sample_2 = tr('export.wizard.sample.p2', 'Niemand had de boot zien aankomen.')
        if key == 'modern':
            html = (f'<div style="font-family:sans-serif"><p style="font-weight:600;font-size:13px;margin:0 0 6px 0">{sample_title}</p>'
                    f'<p style="margin:0 0 6px 0">{sample_1}</p><p style="margin:0">{sample_2}</p></div>')
        elif key == 'literary':
            html = (f'<div style="font-family:Literata,Georgia,serif"><p align="center" style="letter-spacing:2px;font-size:10px;margin:0 0 2px 0">{sample_title.upper()}</p>'
                    f'<p align="center" style="margin:0 0 6px 0">—</p><p style="margin:0">{sample_1}</p>'
                    f'<p style="margin:0;text-indent:14px">{sample_2}</p></div>')
        else:
            html = (f'<div style="font-family:Literata,Georgia,serif"><p align="center" style="font-weight:600;font-size:13px;margin:0 0 6px 0">{sample_title}</p>'
                    f'<p style="margin:0">{sample_1}</p><p style="margin:0;text-indent:14px">{sample_2}</p></div>')
        label = QLabel(html); label.setObjectName('templatePreview'); label.setWordWrap(True)
        label.setTextFormat(Qt.RichText); label.setFixedHeight(132); label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        return label

    def _build_export_page(self):
        self.export_page, layout = self._page()
        heading, intro = self._heading(layout)
        heading.setText(tr('export.wizard.review.heading', 'Klaar om te maken'))
        intro.setText(tr('export.wizard.review.intro', 'Kijk nog één keer. Met Terug kun je elke keuze nog veranderen.'))
        card = QFrame(); card.setObjectName('wizardCard')
        cl = QVBoxLayout(card); cl.setContentsMargins(20, 16, 20, 16); cl.setSpacing(12)
        self.review_file = _label('', 'wizardFileName', wrap=False)
        self.review_kind = _label('', 'muted')
        cl.addWidget(self.review_file); cl.addWidget(self.review_kind)
        line = QFrame(); line.setObjectName('wizardStepLine'); line.setFixedHeight(1); cl.addWidget(line)
        self.review_grid = QGridLayout(); self.review_grid.setHorizontalSpacing(16); self.review_grid.setVerticalSpacing(10)
        self.review_grid.setColumnMinimumWidth(0, 120); self.review_grid.setColumnStretch(1, 1)
        cl.addLayout(self.review_grid)
        layout.addWidget(card)
        self.review_note = _label('', 'muted')
        layout.addWidget(self.review_note)

    def _build_done_page(self):
        self.done_page, layout = self._page()
        panel = QFrame(); panel.setObjectName('wizardStatusOk')
        pl = QVBoxLayout(panel); pl.setContentsMargins(22, 18, 22, 18); pl.setSpacing(12)
        self.done_title = _label('', 'wizardStatusTitle'); self.done_detail = _label('', None)
        self.done_detail.setTextInteractionFlags(Qt.TextSelectableByMouse)
        pl.addWidget(self.done_title); pl.addWidget(self.done_detail)
        buttons = QHBoxLayout(); buttons.setSpacing(10)
        self.done_open_file = QPushButton(tr('export.open_file', 'Bestand openen')); self.done_open_file.setObjectName('primaryButton')
        self.done_open_folder = QPushButton(tr('export.open_folder', 'Map openen')); self.done_open_folder.setObjectName('secondaryButton')
        self.done_open_file.clicked.connect(self._open_file); self.done_open_folder.clicked.connect(self._open_folder)
        buttons.addWidget(self.done_open_file); buttons.addWidget(self.done_open_folder); buttons.addStretch(1)
        pl.addLayout(buttons)
        layout.addWidget(panel)
        self.done_tip_title = _label('', 'sectionTitle'); self.done_tip = _label('', 'muted')
        tip_box = QVBoxLayout(); tip_box.setSpacing(4)
        tip_box.addWidget(self.done_tip_title); tip_box.addWidget(self.done_tip)
        layout.addLayout(tip_box)

    # ------------------------------------------------------------------ state
    def set_book(self, book, *, reset: bool):
        self.book = book
        if book is None or reset:
            self._reset_state()
            return
        if self.page.mode_stack.currentWidget() is not self:
            # Manual mode: no background snapshots; the wizard starts fresh later.
            return
        # Same book shown again (e.g. after fixing something in Boekdetails/Media).
        if self.step in (STEP_PURPOSE, STEP_DONE):
            return
        self.recheck(save_first=False)

    def restart(self):
        self._reset_state()

    def discard_draft(self):
        self.draft = {}
        self.purpose_id = None

    def _saved_settings(self) -> dict:
        if not self.book:
            return {}
        try:
            return self.page.store.load(self.book)
        except Exception:
            return {}

    def _reset_state(self):
        self.document = self.report = self.content = self.package = self.result = None
        self.snapshot_error = ''
        self._changed_notice = False
        saved = self._saved_settings()
        remembered = saved.get('purpose')
        self.purpose_group.setExclusive(False)
        for card in self.purpose_cards.values():
            card.setChecked(False)
        self.purpose_group.setExclusive(True)
        if get_purpose(remembered):
            self.purpose_cards[remembered].setChecked(True)
            self._set_purpose(remembered)
        else:
            self.purpose_id = None; self.draft = {}
            self.steps = steps_for(None)
        self._show_step(STEP_PURPOSE, focus=False)

    def _set_purpose(self, purpose_id: str):
        self.purpose_id = purpose_id
        self.draft = apply_purpose(self._saved_settings(), purpose_id)
        self.steps = steps_for(purpose_id)

    @property
    def format_name(self) -> str:
        purpose = get_purpose(self.purpose_id)
        return purpose.format if purpose else 'epub'

    # ------------------------------------------------------------------ navigation
    def _index(self) -> int:
        return self.steps.index(self.step) if self.step in self.steps else len(self.steps)

    def go_next(self):
        if not self.next_button.isEnabled():
            return
        if self.step == STEP_PURPOSE:
            if not self.purpose_id:
                return
            self.recheck(save_first=True, navigate=False)
            self._show_step(STEP_CHECK)
        elif self.step == STEP_EXPORT:
            self._run_export()
        elif self.step in self.steps:
            index = self._index()
            if index + 1 < len(self.steps):
                if self.steps[index + 1] == STEP_EXPORT:
                    self._refresh_review()
                self._show_step(self.steps[index + 1])

    def go_back(self):
        if self.step == STEP_DONE or self._index() == 0:
            return
        self._show_step(self.steps[self._index() - 1])

    def _extra_clicked(self):
        if self.step == STEP_CHECK:
            self.recheck(save_first=True)
        elif self.step == STEP_DONE:
            self._reset_state()
            self._focus_first()

    def _show_step(self, step: str, *, focus: bool = True):
        self.step = step
        page = {
            STEP_PURPOSE: self.purpose_page, STEP_CHECK: self.check_page, STEP_CONTENT: self.content_page,
            STEP_APPEARANCE: self.appearance_page, STEP_EXPORT: self.export_page, STEP_DONE: self.done_page,
        }[step]
        if step == STEP_CHECK:
            self._render_check()
        elif step == STEP_CONTENT:
            self._render_content()
        elif step == STEP_APPEARANCE:
            self._render_appearance()
        elif step == STEP_EXPORT:
            self._refresh_review()
        self.pages.setCurrentWidget(page)
        self.scroll.verticalScrollBar().setValue(0)
        self._render_step_bar()
        self._update_footer()
        if focus:
            self._focus_first()

    def _fit_pages(self, *_):
        # Hidden pages must never determine the minimum size of the window.
        current = self.pages.currentWidget()
        for index in range(self.pages.count()):
            widget = self.pages.widget(index)
            widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred if widget is current else QSizePolicy.Ignored)
        self.pages.adjustSize()

    def _focus_first(self):
        if self.step == STEP_PURPOSE:
            target = self.purpose_group.checkedButton() or self.purpose_cards[PURPOSES[0].id]
        elif self.step == STEP_CHECK:
            target = self._first_issue_button or self.next_button
        elif self.step == STEP_APPEARANCE:
            target = self.template_group.checkedButton() or self.next_button
        elif self.step == STEP_DONE:
            target = self.done_open_file if self.done_open_file.isVisible() else self.done_open_folder
        else:
            target = self.next_button if self.next_button.isEnabled() else self.back_button
        if target is not None:
            target.setFocus(Qt.TabFocusReason)

    def _render_step_bar(self):
        _clear_layout(self.step_row)
        self.step_labels = []
        current_index = self._index()
        for index, step in enumerate(self.steps):
            done = self.step == STEP_DONE or index < current_index
            text = f'✓ {_step_name(step)}' if done else f'{index + 1} {_step_name(step)}'
            label = _label(text, 'wizardStepCurrent' if step == self.step else 'wizardStep', wrap=False)
            if step == self.step:
                label.setAccessibleDescription(tr('export.wizard.step.current', 'Huidige stap'))
            self.step_row.addWidget(label)
            self.step_labels.append(label)
        self.step_row.addStretch(1)
        shown = min(current_index, len(self.steps) - 1)
        self.step_compact.setText(tr(
            'export.wizard.step.compact', 'Stap {n} van {total} · {name}',
            n=shown + 1, total=len(self.steps), name=_step_name(self.steps[shown]),
        ))
        for label in self.step_labels:
            label.setVisible(not self._compact)
        self.step_compact.setVisible(self._compact)

    def _update_footer(self):
        step = self.step
        self.back_button.setVisible(step != STEP_DONE)
        self.back_button.setEnabled(self._index() > 0)
        self.next_button.setVisible(step != STEP_DONE)
        self.extra_button.setVisible(step in (STEP_CHECK, STEP_DONE))
        self.hint_label.setText('')
        self.next_button.setText(tr('export.wizard.next', 'Volgende'))
        enabled = True
        if step == STEP_PURPOSE:
            enabled = bool(self.purpose_id)
        elif step == STEP_CHECK:
            self.extra_button.setText(tr('export.wizard.check.again', 'Opnieuw controleren'))
            blocked = self.report is None or not self.report.can_export
            enabled = not blocked
            if blocked:
                self.hint_label.setText(tr('export.wizard.check.blocked_hint', 'Los eerst “Moet opgelost” op.'))
        elif step == STEP_CONTENT:
            self.next_button.setText(tr('export.wizard.content.next', 'Klopt, volgende'))
        elif step == STEP_EXPORT:
            self.next_button.setText(_make_verb(self.purpose_id or ''))
        elif step == STEP_DONE:
            self.extra_button.setText(tr('export.wizard.done.again', 'Nog een export maken'))
        self.next_button.setEnabled(enabled and self.book is not None)

    # ------------------------------------------------------------------ events
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and isinstance(obj, _ChoiceCard):
            group = self.purpose_group if obj in self.purpose_cards.values() else self.template_group
            buttons = group.buttons()
            key = event.key()
            if key in (Qt.Key_Right, Qt.Key_Down, Qt.Key_Left, Qt.Key_Up):
                step = 1 if key in (Qt.Key_Right, Qt.Key_Down) else -1
                index = (buttons.index(obj) + step) % len(buttons)
                buttons[index].click(); buttons[index].setFocus(Qt.TabFocusReason)
                return True
            if key in (Qt.Key_Return, Qt.Key_Enter):
                if not obj.isChecked():
                    obj.click()
                self.go_next()
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.next_button.isVisible() and self.next_button.isEnabled():
            self.go_next(); return
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        compact = self.width() - 84 < COMPACT_WIDTH
        if compact != self._compact:
            self._compact = compact
            self._layout_purpose_cards()
            self._render_step_bar()
        self.hint_label.setVisible(not compact)

    def _purpose_clicked(self, button):
        purpose_id = str(button.property('purposeId'))
        if purpose_id != self.purpose_id:
            self._set_purpose(purpose_id)
            self.report = None
        self._render_step_bar(); self._update_footer()

    # ------------------------------------------------------------------ check
    def recheck(self, *, save_first: bool, navigate: bool = True) -> bool:
        """Snapshot + preflight for the current draft. Read-only."""
        if not self.book or not self.purpose_id:
            return False
        self.snapshot_error = ''
        if save_first and not self.page.save_pending_work():
            self.snapshot_error = tr('export.wizard.check.unsaved', 'Niet-opgeslagen wijzigingen konden niet worden bewaard.')
        try:
            self.document = build_export_document(self.page.main.library, self.book)
        except Exception as exc:
            self.document = None
            self.snapshot_error = self.snapshot_error or str(exc)
        self.package = None
        if self.format_name == 'qwbook':
            try:
                self.package = build_package_summary(self.page.main.library, self.book)
            except Exception:
                self.package = None
        if self.document is not None and not self.snapshot_error:
            self.report = run_preflight(self.document, self.format_name, self.draft, self.package)
            self.content = build_content_summary(self.document)
        else:
            self.report = None
            self.content = None
        ok = self.report is not None and self.report.can_export
        if navigate:
            if self.step == STEP_CHECK:
                self._render_check(); self._update_footer()
            elif self.step not in (STEP_PURPOSE, STEP_DONE) and not ok:
                self._changed_notice = True
                self._show_step(STEP_CHECK, focus=False)
            elif self.step in (STEP_CONTENT, STEP_APPEARANCE, STEP_EXPORT):
                self._show_step(self.step, focus=False)
        return ok

    def _issue_texts(self, item) -> tuple[str, str, str, object]:
        """(title, consequence, action label, action callable) for a preflight item."""
        main = self.page.main
        details = (tr('export.wizard.action.details', 'Boekdetails openen'), main.open_current_book_details)
        no_action = ('', None)
        rows = {
            'title': (tr('export.wizard.issue.title', 'Je boek heeft geen titel'), tr('export.wizard.issue.title_help', 'Zonder titel kan QuietWriter geen bestand maken.'), *details),
            'author': (tr('export.wizard.issue.author', 'Geen auteur ingevuld'), tr('export.wizard.issue.author_help', 'E-readers en lezers zien dan geen naam bij je boek.'), *details),
            'language': (tr('export.wizard.issue.language', 'Geen taal ingesteld'), tr('export.wizard.issue.language_help', 'E-readers gebruiken de taal voor afbreking en voorlezen.'), *details),
            'chapters': (tr('export.wizard.issue.chapters', 'Je boek heeft nog geen hoofdstukken'), tr('export.wizard.issue.chapters_help', 'Er is nog niets om te exporteren.'), tr('export.wizard.action.contents', 'Naar Inhoud'), main.show_editor),
            'open_points': (tr('export.wizard.issue.open_points', '{n} open punt(en) staan nog in je boek', n=item.value), tr('export.wizard.issue.open_points_help', 'De technische markeringen komen niet in de export. Controleer wel of je deze plekken bewust onafgewerkt wilt laten.'), tr('export.wizard.action.open_points', 'Open punten bekijken'), main.show_open_points),
            'missing_assets': (tr('export.wizard.issue.missing_assets', 'Een afbeelding ontbreekt of is gewijzigd'), self._missing_asset_text(item.value), tr('export.wizard.action.media', 'Media openen'), main.show_media),
            'markdown_images_pending': (tr('export.wizard.issue.markdown_images', 'Afbeeldingen passen niet in een websitebestand'), tr('export.wizard.issue.markdown_images_help', 'Markdown-export ondersteunt nog geen afbeeldingen. Kies een ander doel.'), tr('export.wizard.action.other_purpose', 'Ander doel kiezen'), lambda: self._show_step(STEP_PURPOSE)),
            'cover_missing': (tr('export.wizard.issue.cover_missing', 'Geen omslag'), tr('export.wizard.issue.cover_missing_help', 'Je e-book krijgt dan geen voorkant in de boekenkast van de lezer.'), *details),
            'pdf_wrap_fallback': (tr('export.wizard.issue.pdf_wrap', '{n} afbeelding(en) zonder tekstomloop', n=item.value), tr('export.wizard.issue.pdf_wrap_help', 'Een lang onderschrift past niet naast de afbeelding. De tekst loopt er in de PDF onderdoor.'), *no_action),
            'qwbook_large': (tr('export.wizard.issue.qwbook_large', 'Groot bestand: ongeveer {size}', size=_fmt_size(_safe_int(item.value))), tr('export.wizard.issue.qwbook_large_help', 'Zet de versiegeschiedenis uit voor een kleiner bestand.'), tr('export.wizard.action.content_step', 'Naar Inhoud-stap'), lambda: self._show_step(STEP_CONTENT)),
            'qwbook_over_limit': (tr('export.wizard.issue.qwbook_over', 'Te groot voor één pakket'), tr('export.wizard.issue.qwbook_over_help', 'Zet de versiegeschiedenis uit, of maak het boek kleiner.'), tr('export.wizard.action.content_step', 'Naar Inhoud-stap'), lambda: self._show_step(STEP_CONTENT)),
        }
        return rows.get(item.key, (item.key, item.value, *no_action))

    @staticmethod
    def _missing_asset_text(value: str) -> str:
        # Preflight lines are "<alt or file>: <technical error>". Writers see only
        # the image name, never internal asset paths.
        names = []
        for line in str(value or '').splitlines():
            name = line.split(': ', 1)[0].strip()
            if name and name not in names:
                names.append(name)
        shown = ', '.join(f'“{name}”' for name in names[:3])
        if len(names) > 3:
            shown += ' …'
        return tr('export.wizard.issue.missing_assets_help', '{names} verwijst naar een bestand dat ontbreekt of is veranderd. Een export zonder deze afbeelding zou stil een gat bevatten.', names=shown)

    @staticmethod
    def _language_name(code: str) -> str:
        base = str(code or '').split('-', 1)[0].lower()
        names = {
            'nl': tr('book_details.language.nl', 'Nederlands'),
            'en': tr('book_details.language.en', 'Engels'),
            'de': tr('book_details.language.de', 'Duits'),
            'fr': tr('book_details.language.fr', 'Frans'),
            'es': tr('book_details.language.es', 'Spaans'),
        }
        return names.get(base, str(code or ''))

    def _ok_text(self, item) -> tuple[str, str]:
        missing = tr('export.check.missing', 'ontbreekt')
        rows = {
            'title': (tr('export.wizard.ok.title', 'Titel'), item.value or missing),
            'author': (tr('export.wizard.ok.author', 'Auteur'), item.value or missing),
            'language': (tr('export.wizard.ok.language', 'Taal'), self._language_name(item.value) or missing),
            'chapters': (tr('export.wizard.ok.chapters', 'Hoofdstukken'), item.value),
            'images': (tr('export.wizard.ok.images', 'Afbeeldingen'), tr('export.wizard.ok.images_value', '{n}, allemaal gevonden', n=item.value)),
            'cover': (tr('export.wizard.ok.cover', 'Omslag'), item.value),
            'cover_disabled': (tr('export.wizard.ok.cover', 'Omslag'), tr('export.wizard.ok.cover_disabled', 'niet opnemen')),
            'isbn': (tr('export.wizard.ok.isbn', 'ISBN'), item.value or tr('export.wizard.ok.no_isbn', 'Niet ingevuld. Alleen nodig als je via een winkel verkoopt.')),
            'qwbook_history': (tr('export.wizard.ok.history', 'Versiegeschiedenis'), tr('export.wizard.ok.history_value', '{n} versies gaan mee', n=item.value)),
        }
        return rows.get(item.key, (item.key, item.value))

    def _render_check(self):
        self.check_heading.setText(tr('export.wizard.check.heading', 'Is je boek klaar voor een {kind}?', kind=_kind_noun(self.purpose_id or '')))
        self.check_intro.setText(tr('export.wizard.check.intro', 'QuietWriter kijkt alleen. Er wordt niets aan je boek veranderd.'))
        if self.report is None and not self.snapshot_error:
            self.recheck(save_first=False, navigate=False)
        _clear_layout(self.issue_box)
        _clear_layout(self.ok_rows_layout)
        self._first_issue_button = None
        self.changed_label.setVisible(self._changed_notice)
        self._changed_notice = False
        if self.report is None:
            self._set_status('wizardStatusWarn', tr('export.wizard.check.failed', 'Controle niet gelukt'),
                             self.snapshot_error or tr('export.check.failed', 'Exportcontrole kon niet worden uitgevoerd.'))
            self.ok_toggle.hide(); self.ok_rows.hide()
            return
        issues = [item for item in self.report.items if item.level in ('error', 'warning')]
        oks = [item for item in self.report.items if item.level in ('ok', 'info')]
        for item in sorted(issues, key=lambda row: 0 if row.level == 'error' else 1):
            title, consequence, action_label, action = self._issue_texts(item)
            card = QFrame(); card.setObjectName('wizardCard')
            row = QHBoxLayout(card); row.setContentsMargins(18, 12, 18, 12); row.setSpacing(14)
            badge = _label(tr('export.wizard.badge.error', 'Moet opgelost') if item.level == 'error' else tr('export.wizard.badge.warning', 'Mag je overslaan'),
                           'wizardBadgeError' if item.level == 'error' else 'wizardBadgeWarning', wrap=False)
            row.addWidget(badge, 0, Qt.AlignVCenter)
            texts = QVBoxLayout(); texts.setSpacing(2)
            texts.addWidget(_label(title, 'wizardIssueTitle'))
            if consequence:
                texts.addWidget(_label(str(consequence), 'muted'))
            row.addLayout(texts, 1)
            if action is not None:
                button = QPushButton(action_label); button.setObjectName('secondaryButton')
                button.clicked.connect(lambda _checked=False, fn=action: fn())
                row.addWidget(button, 0, Qt.AlignVCenter)
                if self._first_issue_button is None:
                    self._first_issue_button = button
            self.issue_box.addWidget(card)
        for item in oks:
            name, value = self._ok_text(item)
            line = QHBoxLayout(); line.setSpacing(12)
            mark = _label('✓' if item.level == 'ok' else 'i', 'wizardOkMark' if item.level == 'ok' else 'muted', wrap=False)
            mark.setFixedWidth(16)
            key_label = _label(name, 'muted', wrap=False); key_label.setFixedWidth(150)
            line.addWidget(mark); line.addWidget(key_label); line.addWidget(_label(str(value), None), 1)
            self.ok_rows_layout.addLayout(line)
        errors = sum(1 for item in issues if item.level == 'error')
        if not issues:
            self._set_status('wizardStatusOk', tr('export.wizard.check.ok', 'Alles is in orde'),
                             tr('export.wizard.check.ok_help', 'Je kunt verder. Hieronder zie je wat QuietWriter heeft gecontroleerd.'))
            self.ok_toggle.hide(); self.ok_rows.setVisible(bool(oks))
        else:
            if errors:
                text = tr('export.wizard.check.some_errors', 'Los eerst de punten met “Moet opgelost” op. Punten met “Mag je overslaan” mag je laten staan.')
            else:
                text = tr('export.wizard.check.only_warnings', 'Je kunt verder, maar kijk even of je dit zo wilt.')
            self._set_status('wizardStatusWarn', tr('export.wizard.check.points', 'Nog {n} punt(en)', n=len(issues)), text)
            self.ok_toggle.setVisible(bool(oks))
            self.ok_toggle.setChecked(False)
            self._toggle_ok_rows(False)
            self.ok_toggle.setText(tr('export.wizard.check.ok_more', '▸ {n} andere controles in orde', n=len(oks)))

    def _toggle_ok_rows(self, shown: bool):
        self.ok_rows.setVisible(bool(shown))
        count = self.ok_rows_layout.count()
        self.ok_toggle.setText(tr('export.wizard.check.ok_less', '▾ {n} andere controles in orde', n=count) if shown
                               else tr('export.wizard.check.ok_more', '▸ {n} andere controles in orde', n=count))

    def _set_status(self, name: str, title: str, text: str):
        self.check_status.setObjectName(name)
        self.check_status.style().unpolish(self.check_status); self.check_status.style().polish(self.check_status)
        self.check_status_title.setText(title); self.check_status_text.setText(text)

    # ------------------------------------------------------------------ content
    def _render_content(self):
        _clear_layout(self.content_body)
        if self.format_name == 'qwbook':
            self._render_package()
            return
        kind = _kind_noun(self.purpose_id or '')
        self.content_heading.setText(tr('export.wizard.content.heading', 'Dit komt in je {kind}', kind=kind))
        self.content_intro.setText(tr('export.wizard.content.intro', 'Klopt dit? Zo niet, pas de publicatiestructuur aan. Daarna kom je hier terug.'))
        summary = self.content
        if summary is None:
            self.content_body.addWidget(_label(tr('export.content.unavailable', 'De inhoud kan nu niet worden gelezen.'), 'muted'))
            return
        extras = []
        if summary.images:
            extras.append(tr('export.wizard.content.extra_images', '<b>{n} afbeelding(en)</b>', n=summary.images))
        if summary.has_cover:
            extras.append(tr('export.wizard.content.extra_cover', 'een omslag'))
        sections = tr('export.wizard.content.extra_sections', ', verdeeld over {n} delen', n=len(summary.sections)) if len(summary.sections) > 1 else ''
        with_text = tr('export.wizard.content.extra_with', ', met {items}', items=tr('export.wizard.content.extra_and', ' en ').join(extras)) if extras else ''
        sentence = tr(
            'export.wizard.content.sentence',
            'Ongeveer <b>{words} woorden</b> in <b>{chapters} hoofdstuk(ken)</b>{sections}{extras}.',
            words=_fmt_int(round_words(summary.words)), chapters=summary.chapters, sections=sections, extras=with_text,
        )
        lead = _label(sentence, 'wizardLead'); lead.setTextFormat(Qt.RichText)
        self.content_body.addWidget(lead)

        card = QFrame(); card.setObjectName('wizardCard')
        grid = QGridLayout(card); grid.setContentsMargins(18, 14, 18, 14); grid.setHorizontalSpacing(16); grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 110); grid.setColumnStretch(1, 1)
        row = 0

        def item_names(keys):
            return ' · '.join(tr(f'publication.item.{key}', PUBLICATION_ITEMS.get(key, {}).get('label', key)) for key in keys)

        if summary.front_matter:
            grid.addWidget(_label(tr('export.wizard.content.front', 'Voorwerk'), 'muted'), row, 0, Qt.AlignTop)
            grid.addWidget(_label(item_names(summary.front_matter)), row, 1); row += 1
        grid.addWidget(_label(tr('export.wizard.content.book', 'Boek'), 'muted'), row, 0, Qt.AlignTop)
        sections = QVBoxLayout(); sections.setSpacing(6)
        for section in summary.sections:
            line = QHBoxLayout()
            line.addWidget(_label(section.title or tr('export.wizard.content.untitled', 'Zonder titel')), 1)
            line.addWidget(_label(tr('export.wizard.content.section_stats', '{chapters} hoofdstuk(ken) · {words} woorden',
                                     chapters=section.chapters, words=_fmt_int(round_words(section.words))), 'muted', wrap=False))
            sections.addLayout(line)
        grid.addLayout(sections, row, 1); row += 1
        if summary.back_matter:
            grid.addWidget(_label(tr('export.wizard.content.back', 'Achterwerk'), 'muted'), row, 0, Qt.AlignTop)
            grid.addWidget(_label(item_names(summary.back_matter)), row, 1); row += 1
        self.content_body.addWidget(card)

        note = QFrame(); note.setObjectName('softPanel')
        nl = QVBoxLayout(note); nl.setContentsMargins(16, 12, 16, 12)
        nl.addWidget(_label(tr('export.wizard.content.stays', 'Blijft alleen in QuietWriter: Planning, Boekprofiel, Boekgeheugen, het Meelezer-gesprek, de Bewaarplaats en je versiegeschiedenis.'), 'muted'))
        self.content_body.addWidget(note)
        adjust = QPushButton(tr('export.content.adjust', 'Publicatiestructuur aanpassen')); adjust.setObjectName('secondaryButton')
        adjust.clicked.connect(self.page._open_publication_setup)
        self.content_body.addWidget(adjust, 0, Qt.AlignLeft)

    def _render_package(self):
        sharing = self.purpose_id == 'share'
        self.content_heading.setText(tr('export.wizard.package.heading_share', 'Dit krijgt de ander van je') if sharing
                                     else tr('export.wizard.package.heading_backup', 'Dit zit in je back-up'))
        self.content_intro.setText(tr('export.wizard.package.intro', 'Een QuietWriter-boek is je boek in één bestand. Wie het opent, kan alles lezen wat hieronder meegaat.'))
        package = self.package
        content = self.content
        card = QFrame(); card.setObjectName('wizardCard')
        cl = QVBoxLayout(card); cl.setContentsMargins(18, 10, 18, 10); cl.setSpacing(8)

        def fixed(text: str):
            line = QHBoxLayout(); line.setSpacing(12)
            mark = _label('✓', 'wizardOkMark', wrap=False); mark.setFixedWidth(16)
            line.addWidget(mark); line.addWidget(_label(text), 1); line.addWidget(_label(tr('export.wizard.package.always', 'altijd'), 'muted', wrap=False))
            cl.addLayout(line)

        if content is not None:
            fixed(tr('export.wizard.package.manuscript', 'Manuscript: {chapters} hoofdstuk(ken), ongeveer {words} woorden',
                     chapters=content.chapters, words=_fmt_int(round_words(content.words))))
        else:
            fixed(tr('export.wizard.package.manuscript_plain', 'Manuscript'))
        fixed(tr('export.wizard.package.media', 'Afbeeldingen en omslag'))
        fixed(tr('export.wizard.package.planning', 'Planning, publicatiestructuur en boekgegevens'))
        fixed(tr('export.wizard.package.ai', 'Boekprofiel en Boekgeheugen'))

        options = self.draft.setdefault('qwbook', {})
        self.chat_box = QCheckBox(tr('export.wizard.package.chat', 'Meelezer-gesprek meesturen'))
        self.chat_box.setObjectName('publicationToggle')
        self.chat_box.setChecked(bool(options.get('include_ai_chat', True)))
        if package is not None and not package.has_ai_chat:
            self.chat_box.setEnabled(False)
            self.chat_box.setText(tr('export.wizard.package.chat_none', 'Meelezer-gesprek meesturen (er is nog geen gesprek)'))
        self.history_box = QCheckBox(tr('export.wizard.package.history', 'Versiegeschiedenis meesturen'))
        self.history_box.setObjectName('publicationToggle')
        self.history_box.setChecked(bool(options.get('include_history', True)))
        cl.addWidget(self.chat_box); cl.addWidget(self.history_box)
        if package is not None:
            versions = tr('export.wizard.package.history_stats', '{n} versie(s) · ongeveer {size} extra', n=package.history_versions, size=_fmt_size(package.history_bytes))
            history_hint = _label(versions, 'muted'); history_hint.setContentsMargins(26, 0, 0, 0)
            cl.addWidget(history_hint)
            if not package.history_versions:
                self.history_box.setEnabled(False)
        self.content_body.addWidget(card)

        self.package_note = _label('', 'muted')
        note = QFrame(); note.setObjectName('softPanel')
        nl = QVBoxLayout(note); nl.setContentsMargins(16, 12, 16, 12); nl.addWidget(self.package_note)
        self.package_note.setTextFormat(Qt.RichText)
        self.content_body.addWidget(note)
        self.chat_box.toggled.connect(self._package_options_changed)
        self.history_box.toggled.connect(self._package_options_changed)
        self._package_options_changed()

    def _package_options_changed(self, *_):
        options = self.draft.setdefault('qwbook', {})
        options['include_ai_chat'] = bool(self.chat_box.isChecked() and self.chat_box.isEnabled())
        options['include_history'] = bool(self.history_box.isChecked() and self.history_box.isEnabled())
        size = ''
        if self.package is not None:
            estimate = self.package.estimated_bytes(include_history=options['include_history'], include_ai_chat=options['include_ai_chat'])
            size = tr('export.wizard.package.size', 'Het bestand wordt ongeveer <b>{size}</b>.', size=_fmt_size(estimate))
        if self.purpose_id == 'share':
            text = tr('export.wizard.package.note_share', 'Oude versies kunnen tekst bevatten die je bewust hebt geschrapt. Daarom gaan ze bij delen standaard niet mee.')
        else:
            text = tr('export.wizard.package.note_backup', 'Bewaar dit bestand buiten deze computer, bijvoorbeeld op een USB-stick of in de cloud.')
        self.package_note.setText(f'{text} {size}'.strip())
        # Size-dependent checks follow the new options.
        if self.document is not None:
            self.report = run_preflight(self.document, self.format_name, self.draft, self.package)

    # ------------------------------------------------------------------ appearance
    def _render_appearance(self):
        fmt = self.format_name
        group = 'pdf' if fmt == 'pdf' else 'epub'
        options = self.draft.setdefault(group, {})
        if fmt == 'pdf':
            self.appearance_heading.setText(tr('export.wizard.appearance.heading_pdf', 'Hoe moet je PDF eruitzien?'))
            self.appearance_intro.setText(tr('export.wizard.appearance.intro_pdf', 'Kies een stijl en een boekformaat. De marges kiest QuietWriter zelf.'))
        else:
            self.appearance_heading.setText(tr('export.wizard.appearance.heading_epub', 'Hoe moet je e-book eruitzien?'))
            self.appearance_intro.setText(tr('export.wizard.appearance.intro_epub', 'Kies een stijl. Lettergrootte en lettertype bepaalt de lezer later zelf op zijn e-reader.'))
        key = options.get('template', 'classic')
        card = self.template_cards.get(key) or self.template_cards['classic']
        card.setChecked(True)
        has_cover = bool(self.content and self.content.has_cover)
        self.cover_card.setVisible(fmt == 'epub' and has_cover)
        self.no_cover_label.setVisible(fmt == 'epub' and not has_cover)
        self.paper_card.setVisible(fmt == 'pdf')
        many_sections = bool(self.content and len(self.content.sections) > 1)
        self.section_pages.setVisible(many_sections)
        for widget in (self.cover_art_only, self.cover_has_text, self.paper_a5, self.paper_a4, self.page_numbers, self.running_header, self.section_pages):
            widget.blockSignals(True)
        if options.get('cover_mode') == 'artwork_with_text':
            self.cover_has_text.setChecked(True)
        else:
            self.cover_art_only.setChecked(True)
        if str(options.get('paper_size', 'A5')).upper() == 'A4':
            self.paper_a4.setChecked(True)
        else:
            self.paper_a5.setChecked(True)
        self.page_numbers.setChecked(bool(options.get('page_numbers', True)))
        self.running_header.setChecked(bool(options.get('running_header', True)))
        self.section_pages.setChecked(bool(options.get('show_section_titles', True)))
        for widget in (self.cover_art_only, self.cover_has_text, self.paper_a5, self.paper_a4, self.page_numbers, self.running_header, self.section_pages):
            widget.blockSignals(False)

    def _template_clicked(self, button):
        group = 'pdf' if self.format_name == 'pdf' else 'epub'
        self.draft.setdefault(group, {})['template'] = str(button.property('templateKey'))

    def _appearance_changed(self, *_):
        if self.step != STEP_APPEARANCE:
            return
        if self.format_name == 'pdf':
            pdf = self.draft.setdefault('pdf', {})
            pdf['paper_size'] = 'A4' if self.paper_a4.isChecked() else 'A5'
            pdf['page_numbers'] = self.page_numbers.isChecked()
            pdf['running_header'] = self.running_header.isChecked()
            if self.section_pages.isVisible():
                pdf['show_section_titles'] = self.section_pages.isChecked()
        else:
            epub = self.draft.setdefault('epub', {})
            epub['cover_mode'] = 'artwork_with_text' if self.cover_has_text.isChecked() else 'artwork_only'
            if self.section_pages.isVisible():
                epub['show_section_titles'] = self.section_pages.isChecked()

    # ------------------------------------------------------------------ review + export
    def _refresh_review(self):
        _clear_layout(self.review_grid)
        fmt = self.format_name
        if self.document is not None:
            self.review_file.setText(destination_for(self.page._output_dir(), self.document, fmt).name)
        else:
            self.review_file.setText('')
        title, _description, _badge = _purpose_texts(self.purpose_id) if self.purpose_id else ('', '', '')
        self.review_kind.setText(title)
        rows: list[tuple[str, str]] = []
        if self.content is not None:
            value = tr('export.wizard.review.content_value', '{chapters} hoofdstuk(ken) · ongeveer {words} woorden',
                       chapters=self.content.chapters, words=_fmt_int(round_words(self.content.words)))
            if self.content.images:
                value += ' · ' + tr('export.wizard.review.content_images', '{n} afbeelding(en)', n=self.content.images)
            rows.append((tr('export.wizard.review.content', 'Inhoud'), value))
        if fmt in ('epub', 'pdf'):
            options = self.draft.get(fmt) or {}
            template = TEMPLATES.get(options.get('template', 'classic'), TEMPLATES['classic'])
            parts = [template.name_en if current_locale() == 'en' else template.name_nl]
            if fmt == 'pdf':
                parts.append(str(options.get('paper_size', 'A5')).upper())
            elif self.content and self.content.has_cover:
                parts.append(tr('export.wizard.review.cover_text', 'omslag met titel en auteur') if options.get('cover_mode') != 'artwork_with_text'
                             else tr('export.wizard.review.cover_plain', 'omslag zoals hij is'))
            rows.append((tr('export.wizard.review.style', 'Stijl'), ' · '.join(parts)))
        if fmt == 'qwbook':
            options = self.draft.get('qwbook') or {}
            extra = []
            extra.append(tr('export.wizard.review.with_history', 'met versiegeschiedenis') if options.get('include_history') else tr('export.wizard.review.without_history', 'zonder versiegeschiedenis'))
            extra.append(tr('export.wizard.review.with_chat', 'met Meelezer-gesprek') if options.get('include_ai_chat') else tr('export.wizard.review.without_chat', 'zonder Meelezer-gesprek'))
            rows.append((tr('export.wizard.review.included', 'Meegestuurd'), ' · '.join(extra)))
        for index, (name, value) in enumerate(rows):
            self.review_grid.addWidget(_label(name, 'muted', wrap=False), index, 0, Qt.AlignTop)
            self.review_grid.addWidget(_label(value), index, 1, 1, 2)
        row = len(rows)
        self.review_grid.addWidget(_label(tr('export.wizard.review.folder', 'Opslaan in'), 'muted', wrap=False), row, 0)
        folder = _label(str(self.page._output_dir()), None, wrap=True)
        self.review_grid.addWidget(folder, row, 1)
        change = QPushButton(tr('export.wizard.review.change_folder', 'Wijzigen…')); change.setObjectName('secondaryButton')
        change.clicked.connect(self._choose_folder)
        self.review_grid.addWidget(change, row, 2)
        if fmt == 'epub':
            note = tr('export.wizard.review.note_epub', 'QuietWriter controleert het e-book na het maken nog een keer. Pas als alles klopt, wordt het bestand opgeslagen.')
        elif fmt == 'qwbook':
            note = tr('export.wizard.review.note_qwbook', 'QuietWriter controleert elk bestand met een vingerafdruk, zodat een beschadigd pakket later wordt herkend.')
        else:
            note = ''
        remember = tr('export.wizard.review.remember', 'Je keuzes worden voor dit boek onthouden.')
        self.review_note.setText(f'{note} {remember}'.strip())

    def _choose_folder(self):
        self.page._choose_output_dir()
        self._refresh_review()

    def _run_export(self):
        if not self.book or not self.purpose_id:
            return
        draft = dict(self.draft)
        draft['format'] = self.format_name
        draft['purpose'] = self.purpose_id
        result = self.page.run_export_flow(self.format_name, draft)
        if result is None:
            # Cancelled overwrite, failed snapshot or a new blocking check.
            ok = self.recheck(save_first=False, navigate=False)
            if not ok:
                self._changed_notice = True
                self._show_step(STEP_CHECK, focus=False)
            return
        self.result = result
        # Commit the draft only after a successful export. The export remains
        # valid even if the guarded settings write loses a race; make that
        # distinction explicit on the done page instead of claiming the
        # choices were remembered.
        settings_saved = self.page.persist_settings_dict(draft)
        self._show_done(settings_saved=settings_saved)

    def _show_done(self, *, settings_saved: bool = True):
        result = self.result
        kind = _kind_noun(self.purpose_id or '')
        self.done_title.setText(tr('export.wizard.done.title', 'Je {kind} is klaar', kind=kind))
        detail = tr('export.wizard.done.detail', '{name} · {size} · opgeslagen in {folder}',
                    name=result.path.name, size=_fmt_size(result.bytes), folder=result.path.parent)
        if not settings_saved:
            detail += '\n' + tr(
                'export.wizard.done.settings_not_saved',
                'De export is gelukt, maar deze keuzes konden niet voor het boek worden onthouden.'
            )
        self.done_detail.setText(detail)
        self.done_open_file.setVisible(result.format != 'qwbook')
        self.done_open_folder.setObjectName('primaryButton' if result.format == 'qwbook' else 'secondaryButton')
        self.done_open_folder.style().unpolish(self.done_open_folder); self.done_open_folder.style().polish(self.done_open_folder)
        tips = {
            'ereader': (tr('export.wizard.tip.ereader_title', 'Hoe zet ik het op mijn e-reader?'),
                        tr('export.wizard.tip.ereader', 'Kobo en de meeste andere e-readers: sluit ze aan met een kabel en sleep het bestand erheen. Telefoon of tablet: open het bestand in Apple Boeken, Google Play Boeken of een andere e-bookapp.')),
            'print': (tr('export.wizard.tip.print_title', 'Afdrukken'),
                      tr('export.wizard.tip.print', 'Open de PDF en kies Afdrukken. Gebruik bij A5 de instelling “Werkelijke grootte”, anders wordt de pagina vergroot.')),
            'word': (tr('export.wizard.tip.word_title', 'Wijzigingen terugkrijgen'),
                     tr('export.wizard.tip.word', 'Krijg je het bestand met wijzigingen terug? Kies op de Boekenkast Boek importeren. Dan komt het als nieuw boek binnen; je huidige boek blijft onaangeroerd.')),
            'share': (tr('export.wizard.tip.share_title', 'Hoe opent de ander het?'),
                      tr('export.wizard.tip.share', 'Stuur het bestand naar de andere QuietWriter-gebruiker. Die kiest op de Boekenkast Boek importeren.')),
            'backup': (tr('export.wizard.tip.backup_title', 'Terugzetten'),
                       tr('export.wizard.tip.backup', 'Kies op de Boekenkast Boek importeren en selecteer dit bestand. QuietWriter zet het boek terug met alles wat erin zit.')),
            'website': (tr('export.wizard.tip.website_title', 'Op je site zetten'),
                        tr('export.wizard.tip.website', 'Open het bestand in een teksteditor en plak de inhoud in je site, of upload het als Markdown-bestand.')),
        }
        tip_title, tip = tips.get(self.purpose_id or '', ('', ''))
        self.done_tip_title.setText(tip_title); self.done_tip.setText(tip)
        self.done_tip_title.setVisible(bool(tip_title)); self.done_tip.setVisible(bool(tip))
        status = tr('export.success.epub_validated.short', 'EPUB voltooid en gecontroleerd') if result.validated else tr('export.success.short', 'Export voltooid')
        self.page.main.status.showMessage(status, 2500)
        self._show_step(STEP_DONE)

    def _open_file(self):
        if self.result and self.result.format != 'qwbook' and self.result.path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.result.path)))

    def _open_folder(self):
        if self.result:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.result.path.parent)))
