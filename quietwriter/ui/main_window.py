
from pathlib import Path

from PySide6.QtCore import (
    Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve,
    QParallelAnimationGroup
)
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout, QInputDialog, QMainWindow,
    QLabel, QMessageBox, QPushButton, QStatusBar, QVBoxLayout, QWidget
)

from .current_page_stack import CurrentPageStack
from .. import APP_NAME
from ..icon_theme import icon, set_icon_theme
from ..i18n import tr
from ..search import BookSearchIndex
from ..themes import THEMES, stylesheet
from ..typography import typography_from_values
from ..manuscript_markup import ManuscriptStyle
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

class MainWindow(QMainWindow):
    def __init__(self, settings, library, models):
        super().__init__(); self.settings=settings; self.library=library
        self.models = [str(item.get('name')) if isinstance(item, dict) else str(item) for item in (models or [])]
        self._active_book = None
        self._active_theme = str(self.settings.value('theme','Helder') or 'Helder')
        set_icon_theme(self._active_theme)
        self.search_index = BookSearchIndex(library.cache_dir / 'book_search.db')
        self.status = QStatusBar(); self.setStatusBar(self.status)
        self.setWindowTitle(APP_NAME); self.setWindowIcon(icon('books')); self.resize(1280, 720)
        self.rail_expanded = self.settings.value('nav_expanded', False, bool)

        wrap = QWidget(); self.setCentralWidget(wrap); root = QHBoxLayout(wrap); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.rail = QFrame(); self.rail.setObjectName('toolrail')
        self.rail_layout = QVBoxLayout(self.rail); self.rail_layout.setContentsMargins(7,10,7,10); self.rail_layout.setSpacing(6)

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
        self.nav_group_labels = []
        self.menu_button = self._nav_button('menu', tr('nav.menu', 'Menu'), self.toggle_nav, checkable=False)
        self.rail_layout.addSpacing(4)
        self.library_group_label = self._nav_group(tr('nav.group.library', 'BIBLIOTHEEK'))
        self.bookshelf_button = self._nav_button('shelf', tr('nav.bookshelf', 'Boekenplank'), self.go_home)
        self.book_group_label = self._nav_group(tr('nav.group.current_book', 'HUIDIG BOEK'))
        self.write_button = self._nav_button('books', tr('nav.contents', 'Inhoud'), self.show_editor)
        self.planning_button = self._nav_button('planning', tr('nav.planning', 'Planning'), self.show_planning)
        self.book_details_button = self._nav_button('edit', tr('nav.book_details', 'Boekdetails'), self.open_current_book_details)
        self.book_profile_button = self._nav_button('persona', tr('nav.book_profile', 'Boekprofiel'), self.show_book_profile)
        self.book_memory_button = self._nav_button('history', tr('nav.book_memory', 'Boekgeheugen'), self.show_book_memory)
        self.media_button = self._nav_button('insert', tr('nav.media', 'Media'), self.show_media)
        self.integrity_button = self._nav_button('history', tr('nav.integrity', 'Integriteit'), self.show_integrity)
        self.export_button = self._nav_button('export', tr('nav.export', 'Exporteren'), self.show_export)
        self.rail_layout.addStretch()
        self.writing_group_label = self._nav_group(tr('nav.group.writing', 'SCHRIJVEN'))
        self.persona_button = self._nav_button('persona', tr('nav.persona', 'Schrijverspersona'), self.show_persona)
        self.program_group_label = self._nav_group(tr('nav.group.program', 'PROGRAMMA'))
        self.settings_button = self._nav_button('settings', tr('nav.settings', 'Instellingen'), self.open_settings)
        self.trash_button = self._nav_button('trash', tr('nav.trash', 'Prullenbak'), self.show_trash)

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
        self.ai_button = trb('spark', tr('tool.ai', 'AI-assistent'), self.editor_page.show_ai)
        self.spell_button = trb('spell', tr('tool.spell', 'Spellingscontrole'), self.editor_page.show_spell)
        self.insert_button = trb('insert', tr('tool.insert', 'Toevoegen'), self.editor_page.show_insert_menu)
        self.history_button = trb('history', tr('tool.history', 'Versiegeschiedenis'), self.editor_page.show_history)
        self._apply_ai_visibility()
        self.delete_chapter_button = trb('trash', tr('tool.delete_chapter', 'Huidig hoofdstuk verwijderen'), self.editor_page.delete_current_chapter, checkable=False)
        self.tool_layout.addStretch(); root.addWidget(self.toolrail)
        self._configure_rail_tab_order()

        self.start.open_book.connect(self.open_book); self.start.new_book.connect(self.new_book); self.start.import_book.connect(self.import_book)
        self.restore_state(); self._apply_ai_visibility(); self._apply_nav_width(); self._apply_toolrail_width(); QTimer.singleShot(0, self.editor_page._position_contents_edge_button)
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
        self._active_book = book
        if book is None:
            return None
        self.library.track_book(book)
        self.editor_page.adopt_live_book(book, preferred_chapter_id)
        self.planning_page.adopt_book(book, reload_kind=planning_reload_kind, changed_files=planning_changed_files)
        self.book_profile_page.adopt_book(book)
        self.book_memory_page.adopt_book(book)

        details = self.book_details_page
        same_details_book = bool(details and details.book and details.book.id == book.id)
        if same_details_book and details.has_pending_changes():
            # A same-book reload uses a three-way merge. Local-only form edits
            # stay live; same-field conflicts keep disk authoritative and first
            # preserve the full local form in Version History.
            detail_conflicts = details.adopt_book_preserving_form(book)
            if detail_conflicts:
                message = tr(
                    'book_details.external_conflict_preserved',
                    'Boek extern gewijzigd; conflicterende lokale boekgegevens zijn apart bewaard in Versiegeschiedenis.'
                )
            else:
                message = tr(
                    'book_details.external_preserved',
                    'Boek extern gewijzigd; je niet-opgeslagen boekgegevens zijn behouden.'
                )
            self.status.showMessage(message, 5000)
        else:
            self._replace_book_details_page(book)
        self.media_manager_page.adopt_book(book)
        self.integrity_page.adopt_book(book)
        self.export_page.set_book(book)
        return book


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

    def _nav_group(self, label):
        heading = QLabel(label)
        heading.setObjectName('navGroupLabel')
        heading.setProperty('navGroupText', label)
        heading.setContentsMargins(11, 6, 0, 0)
        self.rail_layout.addWidget(heading)
        self.nav_group_labels.append(heading)
        return heading

    def _nav_button(self, icon_name, label, fn, checkable=True):
        b = QPushButton()
        b.setObjectName('navButton')
        b.setProperty('iconName', icon_name); b.setIcon(icon(icon_name)); b.setIconSize(QSize(22,22))
        b.setToolTip(label); b.setAccessibleName(label); b.setCheckable(checkable)
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

    def _configure_rail_tab_order(self):
        for buttons in (self.nav_buttons, self.tool_buttons):
            for first, second in zip(buttons, buttons[1:], strict=False):
                QWidget.setTabOrder(first, second)

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
        for heading in self.nav_group_labels:
            heading.setVisible(self.rail_expanded and (heading is not self.book_group_label or self.active_book() is not None))
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
        # History preview is an editor-only, read-only view. As soon as the user
        # navigates to Planning, Book details, Export, Settings, etc. return the
        # editor to the live book so no other page can ever inherit an archive
        # snapshot by accident.
        if not in_editor and self.editor_page.preview_live_book:
            self.editor_page.exit_history_preview()
        self.toolrail.setVisible(in_editor)
        has_book = self.active_book() is not None
        if hasattr(self, 'book_group_label'):
            self.book_group_label.setVisible(self.rail_expanded and has_book)
        self.write_button.setVisible(has_book)
        self.planning_button.setVisible(has_book)
        self.book_details_button.setVisible(has_book)
        self.book_profile_button.setVisible(has_book)
        self.book_memory_button.setVisible(has_book)
        self.media_button.setVisible(has_book)
        self.integrity_button.setVisible(has_book)
        self.export_button.setVisible(has_book)
        self._sync_nav_selection()
        self.sync_tool_buttons()

    def _leave_settings_preview(self):
        if self.stack.currentWidget() is self.settings_page:
            self.settings_page.restore_preview()

    def _sync_nav_selection(self):
        current = self.stack.currentWidget()
        for b in (self.bookshelf_button, self.write_button, self.planning_button, self.book_details_button, self.book_profile_button, self.book_memory_button, self.media_button, self.integrity_button, self.export_button, self.persona_button, self.settings_button, self.trash_button): b.setChecked(False)
        if current is self.start: self.bookshelf_button.setChecked(True)
        elif current is self.editor_page: self.write_button.setChecked(True)
        elif current is self.planning_page: self.planning_button.setChecked(True)
        elif self.book_details_page is not None and current is self.book_details_page: self.book_details_button.setChecked(True)
        elif current is self.book_profile_page: self.book_profile_button.setChecked(True)
        elif current is self.book_memory_page: self.book_memory_button.setChecked(True)
        elif current is self.media_manager_page: self.media_button.setChecked(True)
        elif current is self.integrity_page: self.integrity_button.setChecked(True)
        elif current is self.export_page: self.export_button.setChecked(True)
        elif current is self.persona: self.persona_button.setChecked(True)
        elif current is self.settings_page: self.settings_button.setChecked(True)
        elif current is self.trash: self.trash_button.setChecked(True)

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
        for b in (self.write_button,self.planning_button,self.book_details_button,self.book_profile_button,self.book_memory_button,self.media_button,self.integrity_button,self.export_button): b.setVisible(False)
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
        self.write_button.setVisible(False)
        self.planning_button.setVisible(False)
        self.book_details_button.setVisible(False)
        self.book_profile_button.setVisible(False)
        self.book_memory_button.setVisible(False)
        self.media_button.setVisible(False)
        self.integrity_button.setVisible(False)
        self.export_button.setVisible(False)
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
        self.write_button.setVisible(True)
        self.planning_button.setVisible(True)
        self.book_details_button.setVisible(True)
        self.book_profile_button.setVisible(True)
        self.book_memory_button.setVisible(True)
        self.media_button.setVisible(True)
        self.integrity_button.setVisible(True)
        self.export_button.setVisible(True)
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
        self.write_button.setVisible(False); self.planning_button.setVisible(False); self.book_details_button.setVisible(False); self.book_profile_button.setVisible(False); self.book_memory_button.setVisible(False); self.media_button.setVisible(False); self.integrity_button.setVisible(False); self.export_button.setVisible(False)
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

    def _apply_ai_visibility(self):
        if not hasattr(self, 'ai_button'):
            return
        enabled = self.settings.value('ai_enabled', True, bool)
        self.ai_button.setVisible(enabled)
        if not enabled:
            self.ai_button.setChecked(False)
            if self.editor_page.right.currentWidget() is self.editor_page.ai:
                self.editor_page._remember_panel_widths()
                # Never leave a hidden AI page as the active right-panel page.
                self.editor_page.right.setCurrentWidget(self.editor_page.search)
                self.editor_page.right.hide()
        self.sync_tool_buttons()

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
        self._apply_ai_visibility()
        self.editor_page.ai.apply_settings()
        if self.settings.value('workspace') != old_root:
            QMessageBox.information(self,'Werkmap gewijzigd','De nieuwe werkmap wordt gebruikt nadat de applicatie opnieuw is gestart.')
        self.status.showMessage('Instellingen opgeslagen', 2500)

    def sync_tool_buttons(self):
        if not hasattr(self, 'search_button'): return
        in_editor = self.stack.currentWidget() is self.editor_page
        right_visible = self.editor_page.right.isVisible() and in_editor
        ai_enabled = self.settings.value('ai_enabled', True, bool)
        # Hiding AI is an editor invariant, not a one-off settings side effect.
        # This also protects against restored window/splitter state.
        self.ai_button.setVisible(ai_enabled)
        self.search_button.setChecked(right_visible and self.editor_page.right.currentWidget() is self.editor_page.search)
        self.ai_button.setChecked(bool(ai_enabled and right_visible and self.editor_page.right.currentWidget() is self.editor_page.ai))
        self.spell_button.setChecked(right_visible and self.editor_page.right.currentWidget() is self.editor_page.spell)
        self.insert_button.setChecked(right_visible and self.editor_page.right.currentWidget() is self.editor_page.insert)
        self.history_button.setChecked(right_visible and self.editor_page.right.currentWidget() is self.editor_page.history)
        corrupt_chapter = bool(in_editor and getattr(self.editor_page, '_chapter_corrupt', False))
        self.ai_button.setEnabled(bool(ai_enabled and not corrupt_chapter))
        self.spell_button.setEnabled(not corrupt_chapter)
        self.insert_button.setEnabled(not corrupt_chapter)
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
