
from pathlib import Path

from PySide6.QtCore import (
    Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve,
    QParallelAnimationGroup
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QFileDialog, QFrame, QHBoxLayout, QInputDialog, QMainWindow,
    QLabel, QMessageBox, QPushButton, QScrollArea, QStatusBar, QVBoxLayout, QWidget
)

from .current_page_stack import CurrentPageStack
from .. import APP_NAME
from ..icon_theme import app_icon_path, icon, set_icon_theme
from ..i18n import tr
from ..search import BookSearchIndex
from ..themes import THEMES, stylesheet
from ..typography import typography_from_values
from ..manuscript_markup import ManuscriptStyle
from ..storage import CorruptSourceError
from ..planning_validation import FuturePlanningFormatError
from .book_details import BookDetailsPage
from .book_profile_page import BookProfilePage
from .book_memory_page import BookMemoryPage
from .bookshelf import StartPage
from .editor_page import EditorPage
from .export_page import ExportPage
from .media_manager_page import MediaManagerPage
from .integrity_page import IntegrityPage
from .persona_page import PersonaPage
from .planning import PlanningPage
from .settings_page import SettingsPage
from .trash_page import TrashPage
from .rail_model import RAIL_GROUPS, RailState, build_rail_view, fallback_destination

class MainWindow(QMainWindow):
    def __init__(self, settings, library, models):
        super().__init__(); self.settings=settings; self.library=library
        self.models = [str(item.get('name')) if isinstance(item, dict) else str(item) for item in (models or [])]
        self._active_book = None
        self._active_theme = str(self.settings.value('theme','Helder') or 'Helder')
        set_icon_theme(self._active_theme)
        self.search_index = BookSearchIndex(library.cache_dir / 'book_search.db')
        self.status = QStatusBar(); self.setStatusBar(self.status)
        self._document_status_text = ''
        self._restoring_document_status = False
        self.status.messageChanged.connect(self._status_message_changed)
        self.setWindowTitle(APP_NAME); self.setWindowIcon(QIcon(str(app_icon_path()))); self.resize(1280, 720)
        self.rail_expanded = self.settings.value('nav_expanded', False, bool)
        self._feature_visibility_preview = None

        wrap = QWidget(); self.setCentralWidget(wrap); root = QHBoxLayout(wrap); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.rail = QFrame(); self.rail.setObjectName('toolrail')
        self.rail_shell_layout = QVBoxLayout(self.rail)
        self.rail_shell_layout.setContentsMargins(5, 10, 5, 10)
        self.rail_shell_layout.setSpacing(4)
        self.rail_scroll = QScrollArea(); self.rail_scroll.setObjectName('navScroll')
        self.rail_scroll.setWidgetResizable(True); self.rail_scroll.setFrameShape(QFrame.NoFrame)
        self.rail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.rail_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.rail_content = QWidget(); self.rail_content.setObjectName('navScrollContent')
        self.rail_layout = QVBoxLayout(self.rail_content)
        self.rail_layout.setContentsMargins(0, 2, 0, 2); self.rail_layout.setSpacing(6)
        self.rail_scroll.setWidget(self.rail_content)
        self.program_host = QWidget(); self.program_host.setObjectName('navProgramHost')
        self.program_layout = QVBoxLayout(self.program_host)
        self.program_layout.setContentsMargins(0, 0, 0, 0); self.program_layout.setSpacing(6)
        self._rail_separator_widgets = {}

        self.stack = CurrentPageStack()
        self.start = StartPage(library)
        self.editor_page = EditorPage(self)
        self.persona = PersonaPage(library)
        self.book_profile_page = BookProfilePage(self)
        self.book_memory_page = BookMemoryPage(self)
        self.planning_page = PlanningPage(self)
        self.settings_page = SettingsPage(settings, self, models)
        self.trash = TrashPage(self)
        self.book_details_page = None
        self.export_page = ExportPage(self)
        self.media_manager_page = MediaManagerPage(self)
        self.integrity_page = IntegrityPage(self)
        for page in (self.start, self.editor_page, self.planning_page, self.book_profile_page, self.book_memory_page, self.media_manager_page, self.integrity_page, self.export_page, self.persona, self.settings_page, self.trash): self.stack.addWidget(page)
        root.addWidget(self.rail); root.addWidget(self.stack, 1)

        self.nav_buttons = []
        self.nav_selection_group = QButtonGroup(self)
        self.nav_selection_group.setExclusive(True)
        self.nav_group_labels = []
        self._rail_item_widgets = {}
        self._rail_group_widgets = {}
        self.menu_button = self._nav_button(
            'menu', tr('nav.menu', 'Menu'), self.toggle_nav, checkable=False,
            layout=self.rail_shell_layout,
        )
        self.rail_shell_layout.addWidget(self.rail_scroll, 1)

        self.library_group_label = self._register_nav_group('library', tr('nav.group.library', 'BIBLIOTHEEK'))
        self.bookshelf_button = self._register_nav_item('bookshelf', 'shelf', tr('nav.bookshelf', 'Boekenplank'), self.go_home)

        self._register_nav_separator('current_book')
        self.book_group_label = self._register_nav_group('current_book', tr('nav.group.current_book', 'HUIDIG BOEK'))
        self.write_button = self._register_nav_item('contents', 'books', tr('nav.contents', 'Inhoud'), self.show_editor)
        self.planning_button = self._register_nav_item('planning', 'planning', tr('nav.planning', 'Planning'), self.show_planning)
        self.media_button = self._register_nav_item('media', 'insert', tr('nav.media', 'Media'), self.show_media)
        self.book_details_button = self._register_nav_item('book_details', 'edit', tr('nav.book_details', 'Boekdetails'), self.open_current_book_details)
        self.export_button = self._register_nav_item('export', 'export', tr('nav.export', 'Exporteren'), self.show_export)
        self.integrity_button = self._register_nav_item('integrity', 'shield', tr('nav.integrity', 'Integriteit'), self.show_integrity)

        self._register_nav_separator('ai_context')
        self.ai_context_group_label = self._register_nav_group('ai_context', tr('nav.group.ai_context', 'AI-CONTEXT'))
        self.book_memory_button = self._register_nav_item('book_memory', 'memory', tr('nav.book_memory', 'Boekgeheugen'), self.show_book_memory)
        self.book_profile_button = self._register_nav_item('book_profile', 'book-profile', tr('nav.book_profile', 'Boekprofiel'), self.show_book_profile)

        self.rail_layout.addStretch()
        self._register_nav_separator('program', layout=self.program_layout)
        self.program_group_label = self._register_nav_group('program', tr('nav.group.program', 'PROGRAMMA'), layout=self.program_layout)
        self.persona_button = self._register_nav_item('persona', 'persona', tr('nav.persona', 'Schrijverspersona'), self.show_persona, layout=self.program_layout)
        self.settings_button = self._register_nav_item('settings', 'settings', tr('nav.settings', 'Instellingen'), self.open_settings, layout=self.program_layout)
        self.trash_button = self._register_nav_item('trash', 'trash', tr('nav.trash', 'Prullenbak'), self.show_trash, layout=self.program_layout)
        self.rail_shell_layout.addWidget(self.program_host, 0)
        self.rail_scroll.verticalScrollBar().rangeChanged.connect(
            lambda *_: self._refresh_program_separator_visibility()
        )

        # Rechter gereedschapsrail. De functie-iconen openen/sluiten hun eigen paneel.
        # Een aparte 'rechterpaneel tonen/verbergen'-knop is daardoor overbodig.
        self.toolrail_expanded = self.settings.value('toolrail_expanded', False, bool)
        self.toolrail = QFrame(); self.toolrail.setObjectName('toolrail')
        self.tool_layout = QVBoxLayout(self.toolrail); self.tool_layout.setContentsMargins(8,10,8,10); self.tool_layout.setSpacing(7)
        self.tool_buttons = []
        def trb(icon_name, tip, fn, checkable=True):
            b=QPushButton(); b.setObjectName('railButton'); b.setProperty('iconName', icon_name); b.setIcon(icon(icon_name)); b.setIconSize(QSize(24,24)); b.setFixedHeight(48); b.setToolTip(tip); b.setAccessibleName(tip); b.setCheckable(checkable); b.clicked.connect(fn); b.setProperty('toolLabel', tip); self.tool_layout.addWidget(b); self.tool_buttons.append(b); return b
        self.tool_menu_button = trb('menu', tr('nav.menu', 'Menu'), self.toggle_toolrail, checkable=False)
        self.search_button = trb('search', tr('tool.search', 'Zoeken'), self.editor_page.show_search)
        self.chapter_context_button = trb('planning', tr('tool.chapter_context', 'In dit hoofdstuk'), self.editor_page.show_chapter_context)
        self.ai_button = trb('spark', tr('tool.ai', 'AI-assistent'), self.editor_page.show_ai)
        self.spell_button = trb('spell', tr('tool.spell', 'Spellingscontrole'), self.editor_page.show_spell)
        self.insert_button = trb('insert', tr('tool.insert', 'Toevoegen'), self.editor_page.show_insert_menu)
        self.history_button = trb('history', tr('tool.history', 'Versiegeschiedenis'), self.editor_page.show_history)
        self._apply_feature_visibility()
        self.delete_chapter_button = trb('trash', tr('tool.delete_chapter', 'Huidig hoofdstuk verwijderen'), self.editor_page.delete_current_chapter, checkable=False)
        self.tool_layout.addStretch(); root.addWidget(self.toolrail)
        self._configure_rail_tab_order()

        self.start.open_book.connect(self.open_book); self.start.new_book.connect(self.new_book); self.start.import_book.connect(self.import_book)
        self.restore_state(); self._apply_feature_visibility(); self._apply_nav_width(); self._apply_toolrail_width(); QTimer.singleShot(0, self.editor_page._position_contents_edge_button)
        self.stack.currentChanged.connect(self._mode_changed); self._mode_changed(0)

        save = QAction('Opslaan', self); save.setShortcut('Ctrl+S'); save.triggered.connect(self.save_active); self.addAction(save)
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

    def active_book(self):
        """Return the single live Book object for the current workspace book."""
        return self._active_book

    def adopt_active_book(self, book, preferred_chapter_id: str | None = None, *, planning_reload_kind: str | None = None, planning_changed_files=None):
        """Adopt one freshly loaded live Book across all book-facing pages.

        Revision tracking is per book id, so allowing pages to keep older Book
        objects after a reload makes the guard ineffective. Every conflict/reload
        path therefore comes through here and reconnects all page references to
        the exact same object graph.
        """
        if book is None:
            self._active_book = None
            return None
        # Prepare first: exercise every disk-backed loader before any page is
        # rebound. Corrupt UTF-8 sources have tolerant/read-only loaders; other
        # structural failures abort here while the current workspace is intact.
        prepared = self._prepare_active_book_adoption(book, preferred_chapter_id)
        self.editor_page.adopt_live_book(book, preferred_chapter_id)
        planning_changed = set(planning_changed_files or [])
        if prepared.get('planning_notes_corrupt'):
            planning_changed.add('planning/notes.md')
        self.planning_page.adopt_book(
            book, reload_kind=planning_reload_kind, changed_files=sorted(planning_changed)
        )
        self.book_profile_page.adopt_book(book, prepared=prepared['profile'], show_message=False)
        self.book_memory_page.adopt_book(book, prepared=prepared['memory'], show_message=False)

        details = self.book_details_page
        same_details_book = bool(details and details.book and details.book.id == book.id)
        details_prepared = prepared['details'] is not None
        detail_status_message = None
        if same_details_book and details_prepared:
            # A same-book reload uses a three-way merge. Local-only form edits
            # stay live; same-field conflicts keep disk authoritative and first
            # preserve the full local form in Version History.
            detail_conflicts = details.adopt_book_preserving_form(
                book, prepared=prepared['details'], show_message=False
            )
            if detail_conflicts:
                detail_status_message = tr(
                    'book_details.external_conflict_preserved',
                    'Boek extern gewijzigd; conflicterende lokale boekgegevens zijn apart bewaard in Versiegeschiedenis.'
                )
            else:
                detail_status_message = tr(
                    'book_details.external_preserved',
                    'Boek extern gewijzigd; je niet-opgeslagen boekgegevens zijn behouden.'
                )
        else:
            self._replace_book_details_page(book)
        self.media_manager_page.adopt_book(book)
        self.integrity_page.adopt_book(book)
        self.export_page.set_book(book)
        # Commit the central identity/revision baseline last. Page adoption above
        # is deliberately side-effect free with respect to storage.
        self._active_book = book
        self.library.track_book(book)

        # User-facing conflict notices come last. At this point every page and
        # the central revision baseline already reference the same live Book.
        self.book_profile_page.show_adoption_message(prepared['profile'])
        self.book_memory_page.show_adoption_message(prepared['memory'])
        if prepared.get('planning_notes_corrupt_preserved'):
            self.planning_page.notes_page.show_corrupt_adoption_message()
        if same_details_book and details_prepared:
            if detail_status_message:
                self.status.showMessage(detail_status_message, 5000)
            details.show_adoption_message(prepared['details'])
        return book

    def _prepare_active_book_adoption(self, book, preferred_chapter_id=None):
        """Read all fallible book-backed sources before rebinding the live UI."""
        # Manuscript: unreadable chapter text is a supported corrupt/read-only state.
        chapter = None
        if preferred_chapter_id:
            for section in book.sections:
                chapter = next((c for c in section.chapters if c.id == preferred_chapter_id), None)
                if chapter:
                    break
        if chapter is None:
            chapter = next((c for section in book.sections for c in section.chapters), None)
        if chapter is not None:
            try:
                self.library.read_chapter(book, chapter)
            except UnicodeDecodeError:
                pass
        # Three-way merges and their recovery writes must happen before any page
        # is rebound. A snapshot failure therefore aborts adoption while the old
        # workspace is still completely intact.
        profile_plan = self.book_profile_page.prepare_adoption(book)
        memory_plan = self.book_memory_page.prepare_adoption(book)
        details_plan = None
        details = self.book_details_page
        if details and details.book and details.book.id == book.id and details.has_pending_changes():
            details_plan = details.prepare_adoption(book)
        # Planning/publication/export loaders are intentionally tolerant of corrupt
        # UTF-8 now; calling them here also catches unrelated preparation failures.
        # Structurally corrupt Planning JSON is a supported read-only state.
        # Do not block opening the whole book; the Planning page and chapter
        # context surface the error and Integriteit can restore the source.
        for loader in (self.planning_page.store.load_characters, self.planning_page.store.load_scenes):
            try:
                loader(book)
            except (CorruptSourceError, FuturePlanningFormatError):
                pass
        planning_notes_corrupt = False
        planning_notes_corrupt_preserved = False
        try:
            self.planning_page.store.load_notes(book)
        except UnicodeDecodeError:
            planning_notes_corrupt = True
            notes_page = self.planning_page.notes_page
            same_planning_book = bool(
                self.planning_page.book and book and self.planning_page.book.id == book.id
            )
            if same_planning_book and notes_page.dirty:
                self.library.create_version_with_file_overrides(
                    book, {'planning/notes.md': notes_page.editor.source_text()}, kind='conflict_local'
                )
                planning_notes_corrupt_preserved = True
        self.editor_page.publication_store.load(book)
        self.export_page.store.load(book)
        return {
            'profile': profile_plan,
            'memory': memory_plan,
            'details': details_plan,
            'planning_notes_corrupt': planning_notes_corrupt,
            'planning_notes_corrupt_preserved': planning_notes_corrupt_preserved,
        }


    def preserve_local_and_close_future_book(self, book, *, file_overrides=None, state_book=None, context='wijzigingen'):
        """Safely detach a book that became newer than this QuietWriter.

        Every caller must first preserve the local UI state in History.  The
        incompatible live manifest is never loaded or rewritten.  If creating
        the recovery snapshot fails, the workspace deliberately stays open.
        """
        try:
            if state_book is not None:
                self.library.create_version_from_state(state_book, kind='conflict_local')
            elif file_overrides:
                self.library.create_version_with_file_overrides(book, file_overrides, kind='conflict_local')
            else:
                self.library.create_version_from_state(book, kind='conflict_local')
        except Exception as exc:
            QMessageBox.critical(
                self, 'Lokale invoer niet veiliggesteld',
                f'Je lokale {context} konden niet in Versiegeschiedenis worden bewaard. '
                f'Het boek blijft open. Kopieer je invoer desnoods handmatig en probeer het opnieuw.\n\n{exc}'
            )
            return False
        QMessageBox.warning(
            self, 'Nieuwere QuietWriter nodig',
            f'Dit boek gebruikt inmiddels een nieuwere QuietWriter-versie. Je lokale {context} zijn '
            'bewaard in Versiegeschiedenis. Het boek wordt gesloten; werk QuietWriter bij voordat je verdergaat.'
        )
        self.force_return_to_bookshelf(book)
        return True

    def _save_book_details_if_pending(self):
        page = self.book_details_page
        if page is not None and page.has_pending_changes():
            return page.save() is not False
        return True

    def _nav_group(self, label, *, layout=None):
        heading = QLabel(label)
        heading.setObjectName('navGroupLabel')
        heading.setProperty('navGroupText', label)
        heading.setContentsMargins(11, 6, 0, 0)
        (layout or self.rail_layout).addWidget(heading)
        self.nav_group_labels.append(heading)
        return heading

    def _register_nav_group(self, key, label, *, layout=None):
        heading = self._nav_group(label, layout=layout)
        heading.setProperty('railGroupKey', key)
        self._rail_group_widgets[key] = heading
        return heading

    def _nav_button(self, icon_name, label, fn, checkable=True, *, layout=None):
        b = QPushButton()
        b.setObjectName('navButton')
        b.setProperty('iconName', icon_name); b.setIcon(icon(icon_name)); b.setIconSize(QSize(22,22))
        b.setToolTip(label); b.setAccessibleName(label); b.setCheckable(checkable)
        # Eén expliciete groep overbrugt ook widgets met verschillende parents
        # (scrollgebied versus vast PROGRAMMA-blok).
        if checkable:
            b.setAutoExclusive(False)
            self.nav_selection_group.addButton(b)
        b.clicked.connect(fn)
        b.setProperty('navLabel', label)
        (layout or self.rail_layout).addWidget(b); self.nav_buttons.append(b)
        return b

    def _register_nav_item(self, key, icon_name, label, fn, checkable=True, *, layout=None):
        button = self._nav_button(icon_name, label, fn, checkable=checkable, layout=layout)
        button.setProperty('railItemKey', key)
        self._rail_item_widgets[key] = button
        return button

    def _register_nav_separator(self, before_group, *, layout=None):
        separator = QFrame()
        separator.setObjectName('navGroupSeparator')
        separator.setFrameShape(QFrame.NoFrame)
        separator.setFixedHeight(2)
        (layout or self.rail_layout).addWidget(separator)
        self._rail_separator_widgets[before_group] = separator
        return separator

    def _configure_rail_tab_order(self):
        for buttons in (self.nav_buttons, self.tool_buttons):
            for first, second in zip(buttons, buttons[1:], strict=False):
                QWidget.setTabOrder(first, second)

    def _apply_nav_width(self, animate=False):
        target = 218 if self.rail_expanded else 64
        button_width = 194 if self.rail_expanded else 48
        for b in self.nav_buttons:
            label = b.property('navLabel') or ''
            b.setText(('  ' + label) if self.rail_expanded else '')
            b.setFixedHeight(48)
            b.setMinimumWidth(button_width); b.setMaximumWidth(button_width)
        for heading in self.nav_group_labels:
            # Group visibility itself is controlled only by _render_rail().
            heading.setProperty('railExpanded', self.rail_expanded)
        self.menu_button.setToolTip(tr('nav.collapse', 'Menu inklappen') if self.rail_expanded else tr('nav.expand', 'Menu uitklappen'))
        self._render_rail(self._effective_rail_state())
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

    def set_document_status(self, text: str):
        self._document_status_text = str(text or '')
        editor_page = getattr(self, 'editor_page', None)
        if self._document_status_text and hasattr(self, 'stack') and editor_page is not None and self.stack.currentWidget() is editor_page:
            self.status.showMessage(self._document_status_text)

    def clear_document_status(self):
        self._document_status_text = ''
        self.status.clearMessage()

    def _status_message_changed(self, message: str):
        if message or not self._document_status_text or self._restoring_document_status:
            return
        editor_page = getattr(self, 'editor_page', None)
        if not hasattr(self, 'stack') or editor_page is None or self.stack.currentWidget() is not editor_page:
            return
        QTimer.singleShot(0, self._restore_document_status)

    def _restore_document_status(self):
        if self._restoring_document_status or not self._document_status_text:
            return
        editor_page = getattr(self, 'editor_page', None)
        if editor_page is None or self.stack.currentWidget() is not editor_page or self.status.currentMessage():
            return
        self._restoring_document_status = True
        try:
            self.status.showMessage(self._document_status_text)
        finally:
            self._restoring_document_status = False

    def _mode_changed(self, idx):
        in_editor = self.stack.currentWidget() is self.editor_page
        # History preview is an editor-only, read-only view. As soon as the user
        # navigates to Planning, Book details, Export, Settings, etc. return the
        # editor to the live book so no other page can ever inherit an archive
        # snapshot by accident.
        if not in_editor and self.editor_page.preview_live_book:
            self.editor_page.exit_history_preview()
        self.toolrail.setVisible(in_editor)
        if in_editor and hasattr(self.editor_page, 'chapter_context'):
            self.editor_page.refresh_chapter_context()
            if self.editor_page.chapter is not None:
                self.editor_page.update_counts()
        elif not in_editor:
            self.clear_document_status()
        has_book = self.active_book() is not None
        self._apply_feature_visibility()
        self._sync_nav_selection()
        self.sync_tool_buttons()

    def _leave_settings_preview(self):
        if self.stack.currentWidget() is self.settings_page:
            self.settings_page.restore_preview()

    def _sync_nav_selection(self):
        current = self.stack.currentWidget()
        target = None
        if current is self.start: target = self.bookshelf_button
        elif current is self.editor_page: target = self.write_button
        elif current is self.planning_page: target = self.planning_button
        elif self.book_details_page is not None and current is self.book_details_page: target = self.book_details_button
        elif current is self.book_profile_page: target = self.book_profile_button
        elif current is self.book_memory_page: target = self.book_memory_button
        elif current is self.media_manager_page: target = self.media_button
        elif current is self.integrity_page: target = self.integrity_button
        elif current is self.export_page: target = self.export_button
        elif current is self.persona: target = self.persona_button
        elif current is self.settings_page: target = self.settings_button
        elif current is self.trash: target = self.trash_button

        if target is None:
            self.nav_selection_group.setExclusive(False)
            for button in self.nav_selection_group.buttons():
                button.setChecked(False)
            self.nav_selection_group.setExclusive(True)
            return
        target.setChecked(True)
        if target.parent() is self.rail_content and target.isVisible():
            self.rail_scroll.ensureWidgetVisible(target, 0, 8)

    def save_active(self):
        if self.stack.currentWidget() is self.planning_page:
            return self.planning_page.save_pending()
        if self.stack.currentWidget() is self.book_profile_page:
            return self.book_profile_page.save()
        if self.stack.currentWidget() is self.book_memory_page:
            return self.book_memory_page.save()
        if self.stack.currentWidget() is self.persona:
            return self.persona.save()
        return self.editor_page.save()

    def _save_planning_if_active(self):
        if self.stack.currentWidget() is self.planning_page:
            return self.planning_page.save_pending()
        if self.stack.currentWidget() is self.book_profile_page:
            return self.book_profile_page.save()
        if self.stack.currentWidget() is self.book_memory_page:
            return self.book_memory_page.save()
        if self.stack.currentWidget() is self.persona and self.persona.dirty:
            return self.persona.save()
        return True

    def show_editor(self):
        self._leave_settings_preview()
        if not self._save_book_details_if_pending(): return
        if not self._save_planning_if_active(): return
        if self.stack.currentWidget() is self.editor_page:
            self._sync_nav_selection()
            return
        if self.active_book():
            self.stack.setCurrentWidget(self.editor_page)
        else:
            self.go_home()

    def show_planning(self):
        self._leave_settings_preview()
        if not self._save_book_details_if_pending(): return
        if not self._save_planning_if_active(): return
        if not self.active_book():
            self.go_home(); return
        if self.editor_page.save() is False:
            return
        if self.stack.currentWidget() is self.planning_page:
            self._sync_nav_selection(); return
        self.planning_page.set_book(self.active_book())
        self.stack.setCurrentWidget(self.planning_page)

    def show_book_profile(self):
        if not self.settings.value('ai_enabled', True, bool):
            return
        self._leave_settings_preview()
        if not self._save_book_details_if_pending(): return
        if not self.active_book():
            self.go_home(); return
        if not self._save_planning_if_active(): return
        if self.editor_page.save() is False:
            return
        if self.stack.currentWidget() is self.book_profile_page:
            self._sync_nav_selection(); return
        if self.book_profile_page.set_book(self.active_book()) is False:
            return
        self.stack.setCurrentWidget(self.book_profile_page)

    def show_book_memory(self):
        if not self.settings.value('ai_enabled', True, bool):
            return
        self._leave_settings_preview()
        if not self._save_book_details_if_pending(): return
        if not self.active_book():
            self.go_home(); return
        if not self._save_planning_if_active(): return
        if self.editor_page.save() is False:
            return
        if self.stack.currentWidget() is self.book_memory_page:
            self._sync_nav_selection(); return
        if self.book_memory_page.set_book(self.active_book()) is False:
            return
        self.stack.setCurrentWidget(self.book_memory_page)

    def show_media(self):
        self._leave_settings_preview()
        if not self._save_book_details_if_pending(): return
        book = self.active_book()
        if not book:
            self.go_home(); return
        if not self._save_planning_if_active(): return
        if self.editor_page.save() is False: return
        self.media_manager_page.set_book(book)
        self.stack.setCurrentWidget(self.media_manager_page)

    def show_integrity(self):
        if not self.settings.value('advanced_options', True, bool):
            return
        self._leave_settings_preview()
        if not self._save_book_details_if_pending(): return
        book = self.active_book()
        if not book:
            self.go_home(); return
        if not self._save_planning_if_active(): return
        if self.editor_page.save() is False: return
        self.integrity_page.set_book(book)
        self.stack.setCurrentWidget(self.integrity_page)

    def show_persona(self):
        if not self.settings.value('ai_enabled', True, bool):
            return
        self._leave_settings_preview()
        if not self._save_book_details_if_pending(): return
        if not self._save_planning_if_active(): return
        if self.stack.currentWidget() is self.persona:
            self._sync_nav_selection()
            return
        self.persona.reload()
        self.stack.setCurrentWidget(self.persona)

    def show_trash(self):
        self._leave_settings_preview()
        if not self._save_book_details_if_pending(): return
        if not self._save_planning_if_active(): return
        if self.stack.currentWidget() is self.trash:
            self._sync_nav_selection()
            return
        self.trash.refresh()
        self.stack.setCurrentWidget(self.trash)

    def force_return_to_bookshelf(self, book=None):
        """Detach an incompatible book without invoking any save path."""
        live = book or self.active_book()
        if live is not None:
            # Do not weaken revision protection while detaching. A future-format
            # book is blocked against every later write until explicitly reopened.
            self.library.block_book(live)
        ep = self.editor_page
        ep.autosave_timer.stop(); ep.book=None; ep.chapter=None; ep.dirty=False
        ep.publication_editor.set_book(None); ep.content_stack.setCurrentWidget(ep.manuscript_content)
        ep._chapter_word_counts={}; ep.tree.clear(); ep.chapter_title.clear(); ep.book_title_label.clear()
        ep.editor.blockSignals(True); ep.editor.clear(); ep.editor.blockSignals(False); ep.right.hide()
        if hasattr(ep, 'ai'): ep.ai.set_book(None)
        self.planning_page.set_book(None, force=True)
        if self.book_details_page is not None:
            self.stack.removeWidget(self.book_details_page); self.book_details_page.deleteLater(); self.book_details_page=None
        self.media_manager_page.set_book(None); self.integrity_page.set_book(None); self.export_page.set_book(None)
        self.book_profile_page.set_book(None, force=True); self.book_memory_page.set_book(None, force=True)
        self._active_book=None; self.start.refresh(); self.stack.setCurrentWidget(self.start)
        self._apply_feature_visibility()
        self._sync_nav_selection()

    def go_home(self):
        self._leave_settings_preview()
        if self.stack.currentWidget() is self.start and self.active_book() is None:
            self._sync_nav_selection()
            return
        if not self._save_book_details_if_pending():
            return
        if self.planning_page.save_pending() is False:
            return
        if self.book_profile_page.dirty and self.book_profile_page.save() is False:
            return
        if self.book_memory_page.dirty and self.book_memory_page.save() is False:
            return
        if self.editor_page.close_book() is False:
            return
        self.planning_page.set_book(None)
        if self.book_details_page is not None:
            self.stack.removeWidget(self.book_details_page); self.book_details_page.deleteLater(); self.book_details_page = None
        self.media_manager_page.set_book(None)
        self.integrity_page.set_book(None)
        self.export_page.set_book(None)
        self.book_profile_page.set_book(None, force=True)
        self.book_memory_page.set_book(None, force=True)
        self._active_book = None
        self.start.refresh()
        self.stack.setCurrentWidget(self.start)
        self._apply_feature_visibility()
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
        if self.planning_page.book and self.planning_page.book.id != book.id:
            if self.planning_page.save_pending() is False:
                return
        try:
            # The bookshelf object may predate a Dropbox/OneDrive sync. touch_book
            # reloads book.json first and only updates last_used on that fresh graph.
            live = self.library.touch_book(book)
        except Exception as exc:
            QMessageBox.warning(self, tr('book.open_failed.title', 'Boek openen'), tr('book.open_failed.text', 'Het boek kon niet veilig worden geopend.\n\n{error}', error=exc))
            return
        if self.editor_page.load_book(live) is False:
            return
        self.book_profile_page.set_book(live, force=True)
        self.book_memory_page.set_book(live, force=True)
        self._apply_feature_visibility()
        self.stack.setCurrentWidget(self.editor_page)
        self._sync_nav_selection()

    def _replace_book_details_page(self, book):
        old_page = self.book_details_page
        was_current = old_page is not None and self.stack.currentWidget() is old_page
        if old_page is not None:
            self.stack.removeWidget(old_page)
            old_page.deleteLater()
        self.book_details_page = BookDetailsPage(self.library, self.settings, book, self, before_delete=self._prepare_book_delete)
        self.book_details_page.saved.connect(self._book_details_saved)
        self.book_details_page.deleted.connect(self._book_details_deleted)
        self.stack.addWidget(self.book_details_page)
        if was_current:
            self.stack.setCurrentWidget(self.book_details_page)

    def open_current_book_details(self):
        self._leave_settings_preview()
        if not self._save_planning_if_active(): return
        # Finish any editor/publication autosave before the form becomes
        # editable. This prevents a delayed same-book conflict from rebuilding
        # BookDetails underneath freshly typed form input.
        if self.editor_page.save() is False: return
        book = self.active_book()
        if not book:
            self.go_home(); return
        if self.book_details_page is None or self.book_details_page.book is not book:
            self._replace_book_details_page(book)
        self.stack.setCurrentWidget(self.book_details_page)

    def show_export(self):
        self._leave_settings_preview()
        if not self._save_book_details_if_pending(): return
        book = self.active_book()
        if not book:
            self.go_home(); return
        if not self._save_planning_if_active(): return
        if self.editor_page.save() is False: return
        self.export_page.set_book(book)
        self.stack.setCurrentWidget(self.export_page)

    def _prepare_book_delete(self, book):
        """Persist active book state before BookDetails moves it to trash."""
        active = self.active_book()
        if not active or active.id != book.id:
            return True
        if self.book_profile_page.dirty and self.book_profile_page.save() is False:
            return False
        if self.book_memory_page.dirty and self.book_memory_page.save() is False:
            return False
        if self.planning_page.save_pending() is False:
            QMessageBox.warning(
                self,
                tr('book_details.delete_blocked_title', 'Boek niet verwijderd'),
                tr('book_details.delete_blocked_planning', 'Niet alle planningswijzigingen konden worden opgeslagen. Het boek is niet verwijderd.'),
            )
            return False
        if self.editor_page.save() is False:
            QMessageBox.warning(
                self,
                tr('book_details.delete_blocked_title', 'Boek niet verwijderd'),
                tr('book_details.delete_blocked_manuscript', 'De actuele hoofdstuktekst kon niet worden opgeslagen. Het boek is niet verwijderd.'),
            )
            return False
        return True

    def _book_details_saved(self, book):
        self.start.refresh()
        active = self.active_book()
        if active and active.id == book.id:
            # BookDetails edits the shared live object. Keep the central pointer
            # explicit and refresh only consumers that do not own dirty text.
            self._active_book = book
            self.editor_page.book = book
            self.editor_page.book_title_label.setText(book.title)
            self.export_page.set_book(book)
        self.status.showMessage(tr('book_details.saved_status', 'Boekdetails opgeslagen'), 2500)

    def _book_details_deleted(self, book):
        # All pending editor/planning state was handled by _prepare_book_delete
        # before the book directory was moved to trash.
        self.planning_page.set_book(None)
        self.editor_page.close_book()
        self._active_book = None
        self.start.refresh()
        self._apply_feature_visibility()
        self._apply_nav_width(False)
        self.media_manager_page.set_book(None)
        self.integrity_page.set_book(None)
        self.export_page.set_book(None)
        self.book_profile_page.set_book(None, force=True)
        self.book_memory_page.set_book(None, force=True)
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
        if hasattr(self, 'editor_page') and hasattr(self.editor_page, 'editor'):
            self.editor_page.editor.schedule_formatting(immediate=True)
        about = getattr(getattr(self, 'settings_page', None), 'about_page', None)
        if about is not None and hasattr(about, 'refresh_branding'):
            about.refresh_branding(theme_name)

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
            for button in (getattr(ep, 'undo_button', None), getattr(ep, 'redo_button', None), getattr(ep, 'contents_edge_button', None), getattr(getattr(ep, 'editor', None), 'scene_delete_button', None)):
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
        self.planning_page.notes_page.editor.apply_typography(typography)

    def apply_manuscript_style(self, style: ManuscriptStyle | None = None):
        if style is None:
            style = ManuscriptStyle.from_settings(self.settings)
        self.editor_page.editor.apply_manuscript_style(style)
        self.planning_page.notes_page.editor.apply_manuscript_style(style)

    def open_settings(self):
        if not self._save_planning_if_active(): return
        if self.stack.currentWidget() is self.settings_page:
            self._sync_nav_selection(); return
        self._settings_return_page = self.stack.currentWidget()
        self.settings_page.begin_session()
        self.stack.setCurrentWidget(self.settings_page)

    def return_from_settings(self):
        target = getattr(self, '_settings_return_page', None)
        if target is None or self.stack.indexOf(target) < 0:
            target = self.editor_page if self.active_book() else self.start
        self.stack.setCurrentWidget(target)

    def _effective_rail_state(self, *, ai_enabled=None, advanced=None):
        """Return the effective state for rendering, including Settings preview."""
        preview = self._feature_visibility_preview or {}
        if ai_enabled is None:
            ai_enabled = preview.get('ai_enabled', self.settings.value('ai_enabled', True, bool))
        if advanced is None:
            advanced = preview.get('advanced', self.settings.value('advanced_options', True, bool))
        return RailState(
            has_book=self.active_book() is not None,
            ai_enabled=bool(ai_enabled),
            advanced_enabled=bool(advanced),
        )

    def _render_rail(self, state: RailState):
        """Pure left-rail renderer: visibility only, no navigation or side effects."""
        view = build_rail_view(state)
        for key, button in self._rail_item_widgets.items():
            button.setVisible(view.is_item_visible(key))
        for key, heading in self._rail_group_widgets.items():
            heading.setVisible(self.rail_expanded and view.is_group_visible(key))

        # In the collapsed rail the text headings disappear. Thin separators
        # retain the same grouping without adding visual noise. A separator is
        # only useful when its group and at least one preceding group are visible.
        group_order = [group.key for group in RAIL_GROUPS]
        visible_groups = set(view.visible_groups)
        for key, separator in self._rail_separator_widgets.items():
            index = group_order.index(key)
            has_visible_before = any(group in visible_groups for group in group_order[:index])
            visible = (not self.rail_expanded) and key in visible_groups and has_visible_before
            if key == 'program':
                # PROGRAMMA staat al vast onderaan. Op ruime schermen voegt een
                # extra lijn weinig toe; wanneer het middendeel moet scrollen
                # blijft de scheiding juist nuttig in de ingeklapte rail.
                visible = visible and self._program_separator_needed()
            separator.setVisible(visible)
        return view

    def _program_separator_needed(self):
        return self.rail_scroll.verticalScrollBar().maximum() > 0

    def _refresh_program_separator_visibility(self):
        separator = self._rail_separator_widgets.get('program')
        if separator is None:
            return
        view = build_rail_view(self._effective_rail_state())
        group_order = [group.key for group in RAIL_GROUPS]
        visible_groups = set(view.visible_groups)
        index = group_order.index('program')
        has_visible_before = any(group in visible_groups for group in group_order[:index])
        separator.setVisible(
            (not self.rail_expanded)
            and 'program' in visible_groups
            and has_visible_before
            and self._program_separator_needed()
        )

    def _render_feature_buttons(self, *, ai_enabled=None, spell_enabled=None):
        """Pure visibility renderer for editor feature buttons."""
        if not hasattr(self, 'ai_button'):
            return
        if ai_enabled is None:
            preview = self._feature_visibility_preview or {}
            ai_enabled = preview.get('ai_enabled', self.settings.value('ai_enabled', True, bool))
        if spell_enabled is None:
            spell_enabled = self.settings.value('spell_enabled', True, bool)
        self.ai_button.setVisible(bool(ai_enabled))
        self.spell_button.setVisible(bool(spell_enabled))

    def _page_key(self, page):
        mapping = {
            self.start: 'bookshelf',
            self.editor_page: 'contents',
            self.planning_page: 'planning',
            self.media_manager_page: 'media',
            self.export_page: 'export',
            self.integrity_page: 'integrity',
            self.book_memory_page: 'book_memory',
            self.book_profile_page: 'book_profile',
            self.persona: 'persona',
            self.settings_page: 'settings',
            self.trash: 'trash',
        }
        if self.book_details_page is not None:
            mapping[self.book_details_page] = 'book_details'
        return mapping.get(page)

    def _page_for_key(self, key):
        mapping = {
            'bookshelf': self.start,
            'contents': self.editor_page,
            'planning': self.planning_page,
            'media': self.media_manager_page,
            'export': self.export_page,
            'integrity': self.integrity_page,
            'book_memory': self.book_memory_page,
            'book_profile': self.book_profile_page,
            'persona': self.persona,
            'settings': self.settings_page,
            'trash': self.trash,
        }
        if self.book_details_page is not None:
            mapping['book_details'] = self.book_details_page
        return mapping.get(key)

    def _apply_committed_navigation_effects(self, state: RailState, *, spell_enabled=None):
        """Apply non-rendering effects only after a committed state transition.

        Preview never calls this method. It owns redirects and panel closing so
        the renderer remains a side-effect-free projection of effective state.
        """
        if spell_enabled is None:
            spell_enabled = self.settings.value('spell_enabled', True, bool)

        if hasattr(self.editor_page, 'right'):
            hidden_right = (
                (not state.ai_enabled and self.editor_page.right.currentWidget() is self.editor_page.ai)
                or (not bool(spell_enabled) and self.editor_page.right.currentWidget() is self.editor_page.spell)
            )
            if hidden_right:
                self.editor_page._remember_panel_widths()
                self.editor_page.right.setCurrentWidget(self.editor_page.search)
                self.editor_page.right.hide()

        return_page = getattr(self, '_settings_return_page', None)
        return_key = self._page_key(return_page)
        if return_key is not None:
            target_key = fallback_destination(return_key, state)
            if target_key != return_key:
                self._settings_return_page = self._page_for_key(target_key)

        current = self.stack.currentWidget()
        current_key = self._page_key(current)
        if current_key is not None and current is not self.settings_page:
            target_key = fallback_destination(current_key, state)
            if target_key != current_key:
                target = self._page_for_key(target_key)
                if target is not None:
                    self.stack.setCurrentWidget(target)

    def _set_feature_visibility(self, *, ai_enabled=None, spell_enabled=None, advanced=None, adjust_return=True):
        """Compatibility wrapper around the 0.33 state → model → render pipeline."""
        state = self._effective_rail_state(ai_enabled=ai_enabled, advanced=advanced)
        self._render_rail(state)
        self._render_feature_buttons(ai_enabled=state.ai_enabled, spell_enabled=spell_enabled)
        if adjust_return:
            self._apply_committed_navigation_effects(state, spell_enabled=spell_enabled)
        return state

    def _apply_feature_visibility(self):
        """Render committed feature switches without preview side effects."""
        self._feature_visibility_preview = None
        state = self._effective_rail_state()
        self._render_rail(state)
        self._render_feature_buttons(ai_enabled=state.ai_enabled)
        return state

    def preview_feature_visibility(self, *, ai_enabled=None, advanced=None):
        """Preview only the effective UI state; never redirect or close panels."""
        self._feature_visibility_preview = {
            'ai_enabled': bool(ai_enabled),
            'advanced': bool(advanced),
        }
        state = self._effective_rail_state(ai_enabled=ai_enabled, advanced=advanced)
        self._render_rail(state)
        self._render_feature_buttons(ai_enabled=state.ai_enabled)
        return state

    # Compatibility name retained for older tests/plugins.
    def _apply_ai_visibility(self):
        self._apply_feature_visibility()

    def settings_saved(self, old_root, writing_layout_changed: bool = False):
        editor_font = str(self.settings.value('editor_font','Merriweather') or 'Merriweather')
        editor_size = int(self.settings.value('editor_font_size',15,int) or 15)
        self.apply_writing_font(editor_font, editor_size)
        self.apply_manuscript_style()
        if writing_layout_changed:
            # Qt records QTextBlockFormat changes in the same Undo stack as text.
            # A committed appearance change is presentation state, not a manuscript
            # edit, so start a clean history after the formatting pass rather than
            # leave invisible font/indent steps above the writer's text edits.
            self.editor_page.editor.reset_undo_history()
            self.editor_page._sync_undo_redo()
            self.planning_page.notes_page.editor.reset_undo_history()
        self.editor_page.load_dictionary_from_settings()
        state = self._apply_feature_visibility()
        self._apply_committed_navigation_effects(
            state, spell_enabled=self.settings.value('spell_enabled', True, bool)
        )
        self.editor_page.ai.apply_settings()
        if self.settings.value('workspace') != old_root:
            QMessageBox.information(self,'Werkmap gewijzigd','De nieuwe werkmap wordt gebruikt nadat de applicatie opnieuw is gestart.')
        self.status.showMessage('Instellingen opgeslagen', 2500)

    def sync_tool_buttons(self):
        if not hasattr(self, 'search_button'): return
        in_editor = self.stack.currentWidget() is self.editor_page
        right_visible = self.editor_page.right.isVisible() and in_editor
        ai_enabled = self.settings.value('ai_enabled', True, bool)
        spell_enabled = self.settings.value('spell_enabled', True, bool)
        # Feature visibility is an editor invariant, not a one-off settings side effect.
        self.ai_button.setVisible(ai_enabled)
        self.spell_button.setVisible(spell_enabled)
        chapter_context_available = self.editor_page.chapter_context_available()
        self.chapter_context_button.setVisible(chapter_context_available)
        self.search_button.setChecked(right_visible and self.editor_page.right.currentWidget() is self.editor_page.search)
        self.chapter_context_button.setChecked(bool(chapter_context_available and right_visible and self.editor_page.right.currentWidget() is self.editor_page.chapter_context))
        self.ai_button.setChecked(bool(ai_enabled and right_visible and self.editor_page.right.currentWidget() is self.editor_page.ai))
        self.spell_button.setChecked(bool(spell_enabled and right_visible and self.editor_page.right.currentWidget() is self.editor_page.spell))
        self.insert_button.setChecked(right_visible and self.editor_page.right.currentWidget() is self.editor_page.insert)
        self.history_button.setChecked(right_visible and self.editor_page.right.currentWidget() is self.editor_page.history)
        corrupt_chapter = bool(in_editor and getattr(self.editor_page, '_chapter_corrupt', False))
        self.ai_button.setEnabled(bool(ai_enabled and not corrupt_chapter))
        self.spell_button.setEnabled(bool(spell_enabled and not corrupt_chapter))
        self.insert_button.setEnabled(not corrupt_chapter)
        self.chapter_context_button.setEnabled(chapter_context_available)
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
            section,_=ep.find_chapter_in_book(chapter.id); parts=[]
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
        try:
            if not self._save_book_details_if_pending():
                event.ignore(); return
            if self.persona.dirty and self.persona.save() is False:
                event.ignore(); return
            if self.book_memory_page.dirty and self.book_memory_page.save() is False:
                event.ignore(); return
            if self.book_profile_page.dirty and self.book_profile_page.save() is False:
                event.ignore(); return
            if self.planning_page.save_pending() is False:
                event.ignore(); return
        except Exception as exc:
            event.ignore()
            QMessageBox.critical(self, 'Afsluiten gestopt', f'QuietWriter kon niet alle wijzigingen veilig opslaan. Het venster blijft open.\n\n{exc}')
            return
        # AI-workers moeten echt gestopt zijn voordat Qt widgets/QThreads vernietigt.
        # Anders kan Qt afsluiten met: QThread: Destroyed while thread is still running.
        if hasattr(self.editor_page, 'ai') and not self.editor_page.ai.shutdown(4500):
            QMessageBox.warning(self, 'AI is nog bezig', 'QuietWriter kon het lopende AI-verzoek nog niet veilig stoppen. Klik op “Stop AI” en probeer daarna opnieuw af te sluiten.')
            event.ignore()
            return
        try:
            if self.editor_page.save() is False:
                event.ignore()
                return
        except Exception as exc:
            event.ignore()
            QMessageBox.critical(self, 'Afsluiten gestopt', f'QuietWriter kon je laatste wijzigingen niet veilig opslaan. Het venster blijft open.\n\n{exc}')
            return
        # Window geometry/state blijft volledig bij Qt. De layout zelf houdt
        # minimum-size hints nu binnen de beschikbare viewport; er is dus geen
        # Windows-specifieke clamp of handmatige setGeometry-workaround nodig.
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
