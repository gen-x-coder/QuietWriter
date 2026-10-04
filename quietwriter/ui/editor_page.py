
from pathlib import Path
from datetime import datetime
import copy
import json
import re

from PySide6.QtCore import QDate, QLocale, Qt, QSettings, QTimer, QSize, QPoint
from PySide6.QtGui import QColor, QFont, QKeySequence, QShortcut, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QSplitter, QComboBox,
    QTreeWidgetItem, QVBoxLayout, QWidget, QSizePolicy
)

from .current_page_stack import CurrentPageStack
from ..ai.ui import AIPanel
from ..chapter_order import DropTarget, move_chapter as reorder_chapter
from ..dictionary_catalog import DictionaryCatalog
from ..i18n import current_locale, tr
from ..icon_theme import icon
from ..markdown_io import insert_scene_break as build_scene_break_text
from ..media.markup import (
    build_image_markdown, count_words, image_reference_for_line, insert_image_block,
    is_searchable_range, mask_image_paths, replace_searchable_text, searchable_matches,
)
from ..media.store import MediaStore, MediaError
from ..revisions import ExternalModificationError, RevisionVerificationError
from ..migrations import FutureBookFormatError
from ..planning_validation import FuturePlanningFormatError
from ..publication_models import FRONT_MATTER, BACK_MATTER
from ..publication_storage import PublicationStore
from ..spell_engine import WordDictionary
from ..storage import Chapter, Section, StorageWriteError, CorruptSourceError
from ..themes import THEMES
from ..typography import WritingTypography
from ..editor_view import DEFAULT_TEXT_WIDTH, normalize_text_width
from .dialogs import confirm, prompt_text
from .history_panel import HistoryPanel
from .chapter_context_panel import ChapterContextPanel
from .insert_panel import InsertPanel
from .manuscript_editor import ManuscriptEditor
from .manuscript_tree import ManuscriptTree
from .search_panel import SearchPanel
from .spell_panel import SpellPanel
from .publication.publication_editor import PublicationEditor
from .publication.publication_setup import PublicationSetup

class EditorPage(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.media_store = MediaStore(main.library)
        self.book = None; self.chapter = None; self.dirty = False; self._chapter_corrupt = False
        self._clean_text = ''
        self._editing_image_block: int | None = None
        self._editing_image_reference_path: str | None = None
        self._chapter_word_counts = {}
        self.preview_live_book = None; self.preview_version_id = None; self.preview_return_chapter_id = None
        # Drag/drop is guarded as one transaction. A native QDrag runs a nested
        # Qt event loop, so timers and focus callbacks can fire while the OS still
        # owns model indexes. These flags make every tree rebuild coalesce until
        # the complete drag interaction has unwound.
        self._tree_refresh_pending = False
        self._tree_refresh_callbacks = []
        self._autosave_resume_after_drag = False
        self._publication_autosave_resume_after_drag = False
        self._save_pending_after_drag = False
        self._publication_save_pending_after_drag = False
        self._rename_pending_after_drag = False
        self.autosave_timer = QTimer(self); self.autosave_timer.setSingleShot(True); self.autosave_timer.setInterval(3000); self.autosave_timer.timeout.connect(self.save)
        self.undo_redo_sync_timer = QTimer(self); self.undo_redo_sync_timer.setSingleShot(True); self.undo_redo_sync_timer.setInterval(140); self.undo_redo_sync_timer.timeout.connect(self._sync_undo_redo)

        root = QHBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.left_split = QSplitter(Qt.Horizontal)
        self.manuscript = QWidget(); self.manuscript.setObjectName('panel'); self.manuscript.setMinimumWidth(250); ml = QVBoxLayout(self.manuscript); ml.setContentsMargins(14,14,14,14)
        head = QHBoxLayout(); title = QLabel(tr('editor.contents', 'Inhoud')); title.setObjectName('sectionTitle')
        self.add_content_button = QPushButton(tr('editor.add', '+ Toevoegen')); self.add_content_button.setObjectName('secondaryButton'); self.add_content_button.clicked.connect(self.add_menu)
        head.addWidget(title); head.addStretch(); head.addWidget(self.add_content_button)
        self.tree = ManuscriptTree(); self.tree.setObjectName('manuscriptTree'); self.tree.itemClicked.connect(self.tree_clicked); self.tree.keyboardActivated.connect(self.tree_keyboard_activated); self.tree.chapterDropped.connect(self.move_chapter); self.tree.dragStarted.connect(self._on_tree_drag_started); self.tree.dragFinished.connect(self._on_tree_drag_finished); self.tree.setContextMenuPolicy(Qt.CustomContextMenu); self.tree.customContextMenuRequested.connect(self.tree_context_menu)
        ml.addLayout(head); ml.addWidget(self.tree)

        self.center = QWidget(); cl = QVBoxLayout(self.center); cl.setContentsMargins(0,0,0,0); cl.setSpacing(0)
        self.history_banner = QFrame(); self.history_banner.setObjectName('historyBanner'); hb = QHBoxLayout(self.history_banner); hb.setContentsMargins(14,8,14,8)
        self.history_banner_label = QLabel(''); self.history_banner_label.setObjectName('historyBannerLabel')
        self.history_restore_btn = QPushButton(tr('history.restore_button', 'Deze versie herstellen')); self.history_restore_btn.setObjectName('restoreButton'); self.history_restore_btn.clicked.connect(self.restore_preview_version)
        self.history_exit_btn = QPushButton(tr('history.exit_button', 'Afsluiten')); self.history_exit_btn.setObjectName('historyExitButton'); self.history_exit_btn.clicked.connect(self.exit_history_preview)
        hb.addWidget(self.history_banner_label); hb.addStretch(); hb.addWidget(self.history_restore_btn); hb.addWidget(self.history_exit_btn)
        self.history_banner.hide()
        topbar = QFrame(); topbar.setObjectName('editorTopbar'); tl = QHBoxLayout(topbar); tl.setContentsMargins(14,8,18,8)
        undo = QPushButton(); self.undo_button = undo; undo.setProperty('iconName','undo'); undo.setObjectName('compactButton'); undo.setIcon(icon('undo')); undo.setIconSize(QSize(22,22)); undo.setToolTip(tr('editor.undo', 'Ongedaan maken'))
        redo = QPushButton(); self.redo_button = redo; redo.setProperty('iconName','redo'); redo.setObjectName('compactButton'); redo.setIcon(icon('redo')); redo.setIconSize(QSize(22,22)); redo.setToolTip(tr('editor.redo', 'Opnieuw'))
        self.book_title_label = QLabel(''); self.book_title_label.setObjectName('bookTitleLabel')
        self._book_title_full = ''
        self.book_title_label.setMinimumWidth(0)
        self.book_title_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.autosave_status = QLabel(''); self.autosave_status.setObjectName('autosaveStatus')
        self.text_width_combo = QComboBox()
        self.text_width_combo.setObjectName('editorTextWidth')
        self.text_width_combo.setToolTip(tr('editor.text_width.tip', 'Tekstbreedte verandert alleen de weergave, niet je manuscript of export.'))
        self.text_width_combo.setAccessibleName(tr('editor.text_width', 'Tekstbreedte'))
        self.text_width_combo.setFixedWidth(160)
        for key, label in (
            ('extra_narrow', tr('editor.text_width.extra_narrow', 'Extra smal')),
            ('narrow', tr('editor.text_width.narrow', 'Smal')),
            ('normal', tr('editor.text_width.normal', 'Normaal')),
            ('wide', tr('editor.text_width.wide', 'Breed')),
            ('extra_wide', tr('editor.text_width.extra_wide', 'Extra breed')),
        ):
            self.text_width_combo.addItem(label, key)
        current_width = normalize_text_width(self.main.settings.value('editor_text_width', DEFAULT_TEXT_WIDTH))
        width_index = self.text_width_combo.findData(current_width)
        self.text_width_combo.setCurrentIndex(width_index if width_index >= 0 else self.text_width_combo.findData(DEFAULT_TEXT_WIDTH))
        self.text_width_combo.currentIndexChanged.connect(self._editor_text_width_changed)
        tl.addWidget(undo); tl.addWidget(redo); tl.addSpacing(8); tl.addWidget(self.book_title_label, 1); tl.addStretch()
        tl.addWidget(self.text_width_combo)
        tl.addSpacing(8); tl.addWidget(self.autosave_status)
        self.chapter_title = QLineEdit(); self.chapter_title.setPlaceholderText(tr('editor.chapter_title_placeholder', 'Hoofdstuktitel')); self.chapter_title.setAlignment(Qt.AlignCenter); self.chapter_title.setObjectName('chapterTitle')
        _writing_typography = WritingTypography.from_settings(QSettings('QuietWriter','QuietWriter'))
        self.chapter_title.setFont(_writing_typography.title_font())
        self.chapter_title.editingFinished.connect(self.rename_current)
        self.editor = ManuscriptEditor(); self.editor.setObjectName('editor'); self.editor.textChanged.connect(self.on_text_changed); self.editor.cursorPositionChanged.connect(self._spell_follow_cursor); self.editor.document().contentsChange.connect(self._spell_contents_changed)
        self.editor.apply_text_width(current_width)
        self.editor.set_image_resolver(self._resolve_editor_image_path)
        self.editor.imageEditRequested.connect(self._open_image_editor)
        self.editor.imageDeleteRequested.connect(self._delete_image_block)
        undo.clicked.connect(self._undo_editor); redo.clicked.connect(self._redo_editor)
        undo.setAccessibleName(tr('editor.undo', 'Ongedaan maken'))
        redo.setAccessibleName(tr('editor.redo', 'Opnieuw'))
        undo.setEnabled(False); redo.setEnabled(False)
        # QTextEdit can suppress undoAvailable/redoAvailable while our visual
        # formatting pass temporarily blocks widget signals. Treat the document
        # state as the source of truth and use these signals only as prompts to
        # resynchronise. Real textChanged events schedule the same check.
        self.editor.undoAvailable.connect(self._schedule_undo_redo_sync)
        self.editor.redoAvailable.connect(self._schedule_undo_redo_sync)
        self._spell_cursor_from_edit = False
        self.dictionary = WordDictionary()
        self.dictionary.load_personal(self.main.library.dict_dir / 'persoonlijk.txt')
        self.dictionary.load_persistent_ignored(self.main.library.dict_dir / 'altijd_negeren.txt')
        self.highlighter = self.editor.presentation_highlighter
        self.highlighter.set_dictionary(self.dictionary)
        self.publication_store = PublicationStore(self.main.library)
        self.manuscript_content = QWidget(); manuscript_layout = QVBoxLayout(self.manuscript_content); manuscript_layout.setContentsMargins(0,0,0,0); manuscript_layout.setSpacing(0)
        manuscript_layout.addWidget(self.chapter_title); manuscript_layout.addWidget(self.editor)
        self.publication_editor = PublicationEditor(self)
        self.publication_setup = PublicationSetup(self)
        self.publication_setup.saved.connect(self._save_publication_setup)
        self.publication_setup.cancelled.connect(self._cancel_publication_setup)
        self.content_stack = CurrentPageStack(); self.content_stack.addWidget(self.manuscript_content); self.content_stack.addWidget(self.publication_editor); self.content_stack.addWidget(self.publication_setup)
        cl.addWidget(self.history_banner); cl.addWidget(topbar); cl.addWidget(self.content_stack)

        self.right = CurrentPageStack(); self.right.setObjectName('panel'); self.right.setMinimumWidth(300)
        self.search = SearchPanel(); self.chapter_context = ChapterContextPanel(main.library); self.ai = AIPanel(main); self.spell = SpellPanel(self); self.insert = InsertPanel(); self.history = HistoryPanel(self)
        self.load_dictionary_from_settings()
        self.editor.selectionChanged.connect(self.ai.refresh_quick_actions)
        self.right.addWidget(self.search); self.right.addWidget(self.chapter_context); self.right.addWidget(self.ai); self.right.addWidget(self.spell); self.right.addWidget(self.insert); self.right.addWidget(self.history)
        self.chapter_context.openPlanning.connect(self._open_planning_from_context)
        # Escape closes only the temporary right-side editor tool and returns
        # focus to the matching rail button.  The shortcut is scoped to the
        # panel and its children, so Escape in the manuscript itself remains
        # available to the editor/Qt.
        self._right_escape = QShortcut(QKeySequence(Qt.Key_Escape), self.right)
        self._right_escape.setContext(Qt.WidgetWithChildrenShortcut)
        self._right_escape.activated.connect(self._close_right_panel_from_keyboard)
        self.insert.sceneBreakRequested.connect(self._insert_scene_break_from_panel)
        self.insert.imageInsertRequested.connect(self._insert_image_from_panel)
        self.insert.imageEditRequested.connect(self._save_image_edit_from_panel)
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
        self.contents_edge_button.setAccessibleName(tr('tool.hide_contents', 'Inhoud verbergen'))
        self.contents_edge_button.show()
        self.contents_edge_button.raise_()
        self._configure_tab_order()
        QTimer.singleShot(0, self._position_contents_edge_button)

    def _editor_text_width_changed(self, *_args):
        preset = normalize_text_width(self.text_width_combo.currentData())
        self.editor.apply_text_width(preset)
        self.main.settings.setValue('editor_text_width', preset)
        self.main.settings.sync()

    def apply_text_width_setting(self, preset: str):
        preset = normalize_text_width(preset)
        self.editor.apply_text_width(preset)
        index = self.text_width_combo.findData(preset)
        if index >= 0 and index != self.text_width_combo.currentIndex():
            self.text_width_combo.blockSignals(True)
            self.text_width_combo.setCurrentIndex(index)
            self.text_width_combo.blockSignals(False)

    def _configure_tab_order(self):
        """Keep the editor chrome in the same order visually and by keyboard."""
        controls = (
            self.add_content_button,
            self.tree,
            self.contents_edge_button,
            self.undo_button,
            self.redo_button,
            self.chapter_title,
            self.editor,
        )
        for first, second in zip(controls, controls[1:], strict=False):
            QWidget.setTabOrder(first, second)

    def _sync_undo_redo(self):
        # Only manuscript text owns this undo stack. Publication/setup/history
        # contexts deliberately keep the topbar actions disabled.
        manuscript_active = (
            hasattr(self, 'content_stack')
            and self.content_stack.currentWidget() is self.manuscript_content
            and not self.preview_live_book
            and self.chapter is not None
        )
        document = self.editor.document()
        self.undo_button.setEnabled(bool(manuscript_active and document.isUndoAvailable()))
        self.redo_button.setEnabled(bool(manuscript_active and document.isRedoAvailable()))

    def _schedule_undo_redo_sync(self, *_args):
        # Query immediately for responsive buttons, and once more after the
        # 90 ms manuscript formatting pass has completed. This avoids depending
        # on Qt emitting undoAvailable while editor signals are blocked.
        self._sync_undo_redo()
        self.undo_redo_sync_timer.start()

    def _undo_editor(self):
        self.editor.undo()
        self._schedule_undo_redo_sync()

    def _redo_editor(self):
        self.editor.redo()
        self._schedule_undo_redo_sync()

    def load_book(self, book):
        previous = self.book
        if self.save() is False:
            return False
        if previous is not None and previous.id != book.id:
            self.main.library.untrack_book(previous)
        self.main.adopt_active_book(book)
        return True

    def adopt_live_book(self, book, preferred_chapter_id: str | None = None):
        """Adopt the one live Book object owned by MainWindow.

        This is deliberately a no-save operation. Callers use it only after the
        current state has already been persisted or after an explicit conflict
        choice. It reconnects every editor-side reference to the same fresh
        Book/Chapter graph so no stale Chapter object survives a reload.
        """
        preserve_publication_context = self.content_stack.currentWidget() in (self.publication_editor, self.publication_setup) and self.chapter is None
        self.book = book
        self.chapter = None
        self._set_book_title(book.title)
        self.publication_editor.adopt_book(book)
        self._rebuild_word_count_cache()

        chapter = None
        if preferred_chapter_id:
            _, chapter = self.find_chapter_in_book(preferred_chapter_id)
        if chapter is None and not preserve_publication_context:
            chapter = next((c for section in book.sections for c in section.chapters), None)

        if chapter is not None:
            self._set_editor_chapter(chapter)
            self.populate_tree(after=lambda cid=chapter.id: self.select_tree_chapter(cid))
        elif preserve_publication_context:
            self.chapter = None
            self.dirty = False
            if self.content_stack.currentWidget() is self.publication_setup:
                # No local setup draft may be discarded by callers that adopt a
                # fresh book. Refresh the checkbox model too, so an externally
                # changed publication.json cannot leave this preserved view stale.
                self.publication_setup.set_data(self.publication_store.load(book))
            self.populate_tree()
        else:
            self.chapter = None
            self.editor.blockSignals(True); self.editor.clear(); self.editor.blockSignals(False)
            self.chapter_title.clear(); self.dirty = False
            self.populate_tree()
            self._sync_undo_redo()

        self.main.search_index.rebuild_book(book)
        if hasattr(self, 'history'):
            self.history.set_book(book)
        if hasattr(self, 'ai'):
            self.ai.set_book(book)
        return book

    def _on_tree_drag_started(self):
        # Stop autosave before QTreeWidget processes the handle mouse-press. The
        # base class may change focus synchronously and QDrag.exec() later runs a
        # nested event loop in which ordinary QTimers keep firing.
        self._autosave_resume_after_drag = bool(
            self.autosave_timer.isActive()
            or self.dirty
        )
        self.autosave_timer.stop()
        if hasattr(self, 'publication_editor'):
            publication_timer = self.publication_editor.free_text.timer
            self._publication_autosave_resume_after_drag = bool(
                publication_timer.isActive() or self.publication_editor.free_text.dirty
            )
            publication_timer.stop()

    def _on_tree_drag_finished(self):
        # editingFinished on the chapter-title field can be caused by the very
        # mouse-press that begins a drag. Run that rename only after all native
        # drag state is gone, otherwise save_manifest()/populate_tree() can delete
        # the QTreeWidgetItem QAbstractItemView is still processing.
        try:
            if self._rename_pending_after_drag:
                self._rename_pending_after_drag = False
                self.rename_current()
            self._flush_deferred_tree_refresh()
        finally:
            should_resume = self._autosave_resume_after_drag or self._save_pending_after_drag
            publication_should_resume = self._publication_autosave_resume_after_drag or self._publication_save_pending_after_drag
            self._autosave_resume_after_drag = False
            self._publication_autosave_resume_after_drag = False
            self._save_pending_after_drag = False
            self._publication_save_pending_after_drag = False
            if should_resume and self.dirty:
                # A short fresh delay is intentional. It keeps conflict dialogs and
                # disk I/O outside the dragFinished signal stack as well.
                self.autosave_timer.start(250)
            if publication_should_resume and self.publication_editor.free_text.dirty:
                self.publication_editor.free_text.timer.start(250)

    def _flush_deferred_tree_refresh(self):
        if not self._tree_refresh_pending:
            return
        callbacks = self._tree_refresh_callbacks
        self._tree_refresh_callbacks = []
        self._tree_refresh_pending = False
        self._populate_tree_now()
        for callback in callbacks:
            callback()

    def populate_tree(self, after=None):
        """Rebuild the contents tree, atomically with an optional follow-up.

        During a drag this method never clears QTreeWidget. Instead it coalesces
        all refresh requests and, where needed, stores the operation that depends
        on the fresh tree (selection/opening) for dragFinished. This avoids both
        the native use-after-free and the stale-tree problem of a blind early
        return.
        """
        if self.tree.is_dragging:
            self._tree_refresh_pending = True
            if after is not None:
                self._tree_refresh_callbacks.append(after)
            return False
        self._populate_tree_now()
        if after is not None:
            after()
        return True

    def _populate_tree_now(self):
        self.tree.clear()
        if not self.book:
            return
        publication = self.publication_store.load(self.book)
        enabled = set(publication.enabled)
        theme = THEMES.get(str(self.main.settings.value('theme', 'Helder')), THEMES['Helder'])

        def add_chapter_item(parent, chapter):
            item = QTreeWidgetItem([chapter.title, ''])
            item.setData(0, Qt.UserRole, ('chapter', chapter.id))
            item.setIcon(1, icon('drag_handle'))
            item.setTextAlignment(1, Qt.AlignCenter)
            item.setToolTip(1, tr('editor.drag_chapter', 'Sleep om hoofdstuk te verplaatsen'))
            parent.addChild(item) if parent is not None else self.tree.addTopLevelItem(item)

        def add_body(parent=None):
            for section in self.book.sections:
                if section.id == 'root' and len(self.book.sections) == 1:
                    for chapter in section.chapters:
                        add_chapter_item(parent, chapter)
                else:
                    sit = QTreeWidgetItem([section.title, ''])
                    sit.setData(0, Qt.UserRole, ('section', section.id))
                    sit.setFlags(sit.flags() & ~Qt.ItemIsDragEnabled)
                    section_font = QFont(QApplication.font()); section_font.setWeight(QFont.Weight.DemiBold); sit.setFont(0, section_font)
                    sit.setForeground(0, QColor(theme['muted']))
                    parent.addChild(sit) if parent is not None else self.tree.addTopLevelItem(sit)
                    for chapter in section.chapters:
                        add_chapter_item(sit, chapter)
                    sit.setExpanded(True)

        def make_group(label, kind, editable=False):
            item = QTreeWidgetItem([label, tr('editor.tree.edit', 'wijzig') if editable else ''])
            item.setData(0, Qt.UserRole, ('manuscript_group', kind))
            item.setFlags(item.flags() & ~Qt.ItemIsDragEnabled)
            font = QFont(QApplication.font()); font.setWeight(QFont.Weight.DemiBold); item.setFont(0, font)
            item.setBackground(0, QColor(theme['panel2'])); item.setBackground(1, QColor(theme['panel2']))
            item.setForeground(0, QColor(theme['text']))
            if editable:
                item.setForeground(1, QColor(theme['accent']))
                item.setTextAlignment(1, Qt.AlignCenter)
                item.setToolTip(1, tr('editor.tree.publication_tip', 'Publicatiestructuur wijzigen'))
            # Keep the disclosure arrow visible even when Voorwerk/Achterwerk
            # currently contain no enabled items. These three zones are a stable
            # part of the manuscript structure, not something that appears only
            # after publication options have been selected.
            item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
            self.tree.addTopLevelItem(item)
            item.setExpanded(True)
            return item

        front_group = make_group(tr('editor.tree.front', 'Voorwerk'), 'front', editable=True)
        for key, text, _kind in FRONT_MATTER:
            if key in enabled:
                item = QTreeWidgetItem([tr(f'publication.item.{key}', text), ''])
                item.setData(0, Qt.UserRole, ('publication', key))
                item.setFlags(item.flags() & ~Qt.ItemIsDragEnabled)
                front_group.addChild(item)

        body_group = make_group(tr('editor.tree.book', 'Boek'), 'body')
        add_body(body_group)

        back_group = make_group(tr('editor.tree.back', 'Achterwerk'), 'back', editable=True)
        for key, text, _kind in BACK_MATTER:
            if key in enabled:
                item = QTreeWidgetItem([tr(f'publication.item.{key}', text), ''])
                item.setData(0, Qt.UserRole, ('publication', key))
                item.setFlags(item.flags() & ~Qt.ItemIsDragEnabled)
                back_group.addChild(item)

    def persist_publication_change(self, relative_path: str, local_text: str, writer) -> str:
        """Safely persist one publication file with the same conflict UX as planning.

        Returns ``mine`` when the local value was written, ``disk`` when the
        external value was accepted, and ``failed`` when no safe decision could
        be completed.
        """
        if not self.book:
            return 'failed'
        if self.tree.is_dragging:
            # Publication free-text has its own autosave timer. It is paused at
            # drag start, but this guard also protects direct/future callers from
            # opening a conflict dialog or rebuilding the tree during native drag.
            self._publication_save_pending_after_drag = True
            return 'failed'
        try:
            writer(self.book)
            return 'mine'
        except RevisionVerificationError:
            QMessageBox.warning(self, tr('publication.save_unavailable.title', 'Opslaan tijdelijk niet mogelijk'), tr('publication.save_unavailable.text', 'QuietWriter kan de actuele bestanden tijdelijk niet betrouwbaar controleren. Er is niets overschreven. Probeer het zo opnieuw.'))
            return 'failed'
        except ExternalModificationError as exc:
            changed='\n'.join('• '+name for name in exc.changed_files[:6])
            box=QMessageBox(self); box.setIcon(QMessageBox.Warning); box.setWindowTitle(tr('publication.conflict.title', 'Boek extern gewijzigd')); box.setText(tr('publication.conflict.text', 'Dit boek is buiten QuietWriter gewijzigd.'))
            box.setInformativeText(tr('publication.conflict.info', 'QuietWriter heeft het publicatieonderdeel niet overschreven.\n\nGewijzigd:\n{changed}\n\nWelke versie wil je gebruiken? Beide keuzes maken eerst automatisch een herstelversie.', changed=changed))
            mine=box.addButton(tr('publication.conflict.mine', 'Mijn versie gebruiken'),QMessageBox.AcceptRole); disk=box.addButton(tr('publication.conflict.disk', 'Versie op schijf gebruiken'),QMessageBox.DestructiveRole); box.setDefaultButton(disk); box.exec()
            if box.clickedButton() not in (mine,disk):
                return 'failed'
            old_book=self.book
            try:
                preferred_chapter_id = self.chapter.id if self.chapter else None
                if box.clickedButton() is mine:
                    self.main.library.create_version(old_book,kind='conflict_external')
                    latest=self.main.library.load_book(old_book.path)
                    self.main.library.track_book(latest)
                    writer(latest)
                    result='mine'
                else:
                    self.main.library.create_version_with_file_overrides(old_book,{relative_path:local_text},kind='conflict_local')
                    latest=self.main.library.load_book(old_book.path)
                    result='disk'
                self.main.adopt_active_book(latest, preferred_chapter_id)
                return result
            except FutureBookFormatError:
                snapshot_exists = box.clickedButton() is disk
                if not snapshot_exists:
                    try:
                        self.main.library.create_version_with_file_overrides(old_book, {relative_path: local_text}, kind='conflict_local')
                        snapshot_exists = True
                    except Exception as snapshot_error:
                        QMessageBox.critical(self, tr('publication.future.snapshot_failed_title', 'Lokale tekst niet veiliggesteld'), tr('publication.future.snapshot_failed_text', 'De publicatietekst kon niet in Versiegeschiedenis worden bewaard. Het boek blijft open.\n\n{error}', error=snapshot_error))
                        return 'failed'
                QMessageBox.warning(self, tr('publication.future.title', 'Nieuwere QuietWriter nodig'), tr('publication.future.text', 'Dit boek gebruikt inmiddels een nieuwere QuietWriter-versie. Je lokale publicatietekst is bewaard in Versiegeschiedenis. Het boek wordt gesloten; werk QuietWriter bij voordat je verdergaat.'))
                self.main.force_return_to_bookshelf(old_book)
                return 'failed'
            except Exception as error:
                QMessageBox.critical(self,tr('publication.conflict.failed_title', 'Conflict niet opgelost'),tr('publication.conflict.failed_text', 'Er is niets bewust overschreven.\n\n{error}', error=error))
                return 'failed'
        except Exception as exc:
            QMessageBox.critical(self,tr('publication.save_error.title', 'Publicatieonderdeel opslaan'),tr('publication.save_error.text', 'Opslaan is mislukt.\n\n{error}', error=exc))
            return 'failed'

    def _set_publication_context(self):
        # Corruption is a property of manuscript chapter text only.  Publication
        # editors have their own storage and must never inherit this guard.
        self.chapter = None
        self._chapter_corrupt = False
        self.autosave_timer.stop()
        self.undo_button.setEnabled(False)
        self.redo_button.setEnabled(False)
        self.right.hide()
        if hasattr(self, 'chapter_context'):
            self.chapter_context.clear()
        if hasattr(self.main, 'toolrail'):
            self.main.toolrail.hide()
        self.autosave_status.setText('')
        self.main.clear_document_status()

    def open_publication_item(self, key):
        if not self.book or self.preview_live_book:
            return
        if self.save() is False:
            return
        self._set_publication_context()
        self.publication_editor.set_book(self.book)
        if self.publication_editor.open_item(key):
            self.content_stack.setCurrentWidget(self.publication_editor)

    def show_publication_setup(self):
        if not self.book or self.preview_live_book:
            return
        if self.save() is False:
            return
        self._set_publication_context()
        self.publication_setup.set_data(self.publication_store.load(self.book))
        self.content_stack.setCurrentWidget(self.publication_setup)

    def _save_publication_setup(self, data):
        if not self.book:
            return
        payload = json.dumps(data.to_dict(), ensure_ascii=False, indent=2)
        selected = list(data.enabled)
        def write_enabled_only(book):
            latest_data = self.publication_store.load(book)
            latest_data.enabled = list(selected)
            self.publication_store.save(book, latest_data)
        result = self.persist_publication_change('publication/publication.json', payload, write_enabled_only)
        if result == 'failed':
            return
        if result == 'disk':
            data = self.publication_store.load(self.book)
        self.publication_editor.book = self.book
        self.publication_editor.data = data
        self.populate_tree()
        enabled = list(data.enabled)
        if enabled:
            self.select_tree_publication(enabled[0]); self.open_publication_item(enabled[0])
        elif self.chapter:
            self.content_stack.setCurrentWidget(self.manuscript_content)
        else:
            first = next((c for sec in self.book.sections for c in sec.chapters), None)
            if first: self.open_chapter(first); self.select_tree_chapter(first.id)

    def _cancel_publication_setup(self):
        first = next((c for sec in self.book.sections for c in sec.chapters), None) if self.book else None
        if first:
            self.open_chapter(first); self.select_tree_chapter(first.id)

    def select_tree_publication(self, key):
        root=self.tree.invisibleRootItem(); stack=[root]
        while stack:
            parent=stack.pop()
            for i in range(parent.childCount()):
                item=parent.child(i); data=item.data(0,Qt.UserRole)
                if data and data[0]=='publication' and data[1]==key:
                    self.tree.setCurrentItem(item); return
                stack.append(item)

    def move_chapter(self, chapter_id: str, target_type: str, target_id: str, before: bool):
        if not self.book or self.preview_live_book:
            return
        # Reordering is structural: it must never change which chapter the
        # editor is showing. Remember that navigation context before touching
        # the model and restore the same tree highlight after the rebuild.
        current_chapter_id = self.chapter.id if self.chapter else None
        target = DropTarget(target_type, target_id, before)

        def restore_active_tree_selection():
            if current_chapter_id:
                self.select_tree_chapter(current_chapter_id)
            else:
                self.tree.clearSelection()
                self.tree.setCurrentItem(None)

        def target_still_exists():
            source_exists = any(
                chapter.id == chapter_id
                for section in self.book.sections
                for chapter in section.chapters
            )
            if not source_exists:
                return False
            if target_type == 'chapter':
                return any(
                    chapter.id == target_id
                    for section in self.book.sections
                    for chapter in section.chapters
                )
            if target_type == 'section':
                return any(section.id == target_id for section in self.book.sections)
            return False

        # The first ExternalModificationError is resolved using the normal safe
        # conflict flow. If that succeeds, recompute the reorder against the
        # freshly loaded book and persist the user's drag intent once more. This
        # closes the old gap where the conflict was resolved but the move itself
        # was silently discarded.
        retried_after_conflict = False
        while True:
            proposed = copy.deepcopy(self.book.sections)
            try:
                changed = reorder_chapter(proposed, chapter_id, target)
                if not changed:
                    if retried_after_conflict and not target_still_exists():
                        QMessageBox.warning(
                            self, tr('editor.move.not_done_title', 'Verplaatsen niet uitgevoerd'),
                            tr('editor.move.source_missing', 'De boekstructuur is tijdens het synchroniseren gewijzigd. Het bronhoofdstuk of doel bestaat niet meer, daarom is de verplaatsing niet uitgevoerd.')
                        )
                    break
                shadow = copy.copy(self.book)
                shadow.sections = proposed
                self.main.library.save_manifest(shadow)
                self.book.sections = proposed
                if current_chapter_id:
                    _, rebound = self.find_chapter_in_book(current_chapter_id)
                    self.chapter = rebound
                break
            except ExternalModificationError as exc:
                if retried_after_conflict:
                    # Resolve the newly detected disk state, but do not loop
                    # indefinitely if sync software keeps changing the book.
                    self._handle_concurrency_issue(exc)
                    QMessageBox.warning(
                        self, tr('editor.move.not_done_title', 'Verplaatsen niet uitgevoerd'),
                        tr('editor.move.changed_again', 'Het boek veranderde opnieuw tijdens het opnieuw toepassen van de verplaatsing. De verplaatsing is niet uitgevoerd. Probeer het opnieuw zodra de synchronisatie klaar is.')
                    )
                    break
                if not self._handle_concurrency_issue(exc):
                    break
                retried_after_conflict = True
                continue
            except RevisionVerificationError as exc:
                self._handle_concurrency_issue(exc)
                break
            except Exception as exc:
                QMessageBox.critical(
                    self, tr('editor.move.failed_title', 'Verplaatsen mislukt'),
                    tr('editor.move.failed_text', 'Het hoofdstuk is niet verplaatst en de bestaande volgorde is behouden.\n\n{error}', error=exc)
                )
                break

        self.populate_tree(after=restore_active_tree_selection)

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
            _, chapter = self.find_chapter_in_book(chapter_id)
            if not chapter:
                return
            rename_action = menu.addAction(tr('common.rename', 'Hernoemen'))
            duplicate_action = menu.addAction(tr('common.duplicate', 'Dupliceren'))
            delete_action = menu.addAction(tr('common.delete', 'Verwijderen'))
            chosen = menu.exec(self.tree.viewport().mapToGlobal(pos))

            if chosen is rename_action:
                title, ok = prompt_text(self, tr('editor.rename_chapter.title', 'Hoofdstuk hernoemen'), tr('common.title_label', 'Titel:'), chapter.title)
                if ok and title.strip():
                    try:
                        self.main.library.rename_chapter(self.book, chapter_id, title)
                    except (ExternalModificationError, RevisionVerificationError) as exc:
                        self._handle_concurrency_issue(exc); return
                    except Exception as exc:
                        QMessageBox.critical(self, tr('editor.rename.failed_title', 'Hernoemen mislukt'), tr('editor.rename.chapter_failed', 'Het hoofdstuk is niet hernoemd.\n\n{error}', error=exc))
                        return
                    if self.chapter and self.chapter.id == chapter_id:
                        self.chapter_title.setText(title.strip())
                    self.populate_tree(after=lambda cid=chapter_id: self.select_tree_chapter(cid))
            elif chosen is duplicate_action:
                if self.save() is False:
                    return
                try:
                    copied = self.main.library.duplicate_chapter(self.book, chapter_id)
                except CorruptSourceError:
                    QMessageBox.warning(self, tr('editor.duplicate.corrupt_title', 'Hoofdstuk beschadigd'), tr('editor.duplicate.corrupt_text', 'Dit hoofdstuk is beschadigd en kan niet worden gedupliceerd. Herstel het eerst via Integriteit.'))
                    return
                except (ExternalModificationError, RevisionVerificationError) as exc:
                    self._handle_concurrency_issue(exc); return
                except Exception as exc:
                    QMessageBox.critical(self, tr('editor.duplicate.failed_title', 'Dupliceren mislukt'), tr('editor.duplicate.failed_text', 'Het hoofdstuk is niet gedupliceerd.\n\n{error}', error=exc))
                    return
                if copied:
                    self._chapter_word_counts[copied.id] = self._chapter_word_counts.get(chapter_id, count_words(self.main.library.read_chapter(self.book, copied)))
                    def open_copy(copied_id=copied.id):
                        _, current_copy = self.find_chapter_in_book(copied_id)
                        if current_copy:
                            self.open_chapter(current_copy)
                            self.select_tree_chapter(current_copy.id)
                    self.populate_tree(after=open_copy)
                else:
                    self.populate_tree()
            elif chosen is delete_action:
                self.delete_chapter(chapter_id)

        elif data[0] == 'section':
            section_id = data[1]
            sec = next((x for x in self.book.sections if x.id == section_id), None)
            if not sec:
                return
            rename_action = menu.addAction(tr('editor.section.rename_action', 'Sectie hernoemen…'))
            delete_action = menu.addAction(tr('editor.section.delete_action', 'Sectie verwijderen…'))
            chosen = menu.exec(self.tree.viewport().mapToGlobal(pos))
            if chosen is rename_action:
                title, ok = prompt_text(self, tr('editor.section.rename_title', 'Sectie hernoemen'), tr('common.title_label', 'Titel:'), sec.title)
                if ok and title.strip():
                    try:
                        self.main.library.rename_section(self.book, section_id, title)
                    except (ExternalModificationError, RevisionVerificationError) as exc:
                        self._handle_concurrency_issue(exc); return
                    except Exception as exc:
                        QMessageBox.critical(self, tr('editor.rename.failed_title', 'Hernoemen mislukt'), tr('editor.rename.section_failed', 'De sectie is niet hernoemd.\n\n{error}', error=exc))
                        return
                    self.populate_tree()
            elif chosen is delete_action:
                if sec.chapters:
                    QMessageBox.information(self, tr('editor.section.delete_title', 'Sectie verwijderen'), tr('editor.section.delete_nonempty', 'Verplaats eerst de hoofdstukken uit deze sectie. Een niet-lege sectie wordt niet verwijderd.'))
                    return
                if confirm(self, tr('editor.section.delete_title', 'Sectie verwijderen'), tr('editor.section.delete_confirm', 'Wil je de sectie “{title}” verwijderen?', title=sec.title)):
                    previous_sections = self.book.sections
                    self.book.sections = [x for x in self.book.sections if x.id != sec.id]
                    if not self.book.sections:
                        self.book.sections = [Section(id='root', title='Manuscript')]
                    try:
                        self.main.library.save_manifest(self.book)
                    except (ExternalModificationError, RevisionVerificationError) as exc:
                        self.book.sections = previous_sections
                        self._handle_concurrency_issue(exc); return
                    except Exception as exc:
                        self.book.sections = previous_sections
                        QMessageBox.critical(self, tr('editor.section.delete_failed_title', 'Sectie verwijderen mislukt'), tr('editor.section.delete_failed_text', 'De sectie is niet verwijderd.\n\n{error}', error=exc))
                        return
                    self.populate_tree()

    def delete_current_chapter(self):
        if not self.chapter:
            return
        self.delete_chapter(self.chapter.id)

    def delete_chapter(self, chapter_id: str):
        """Delete any manuscript chapter through the same guarded flow.

        Used both by the persistent delete tool and by the chapter context menu.
        Deleting a non-active chapter leaves the current editor chapter open.
        """
        if not self.book or self.preview_live_book:
            return
        _, chapter = self.find_chapter_in_book(chapter_id)
        if not chapter:
            return
        total = sum(len(sec.chapters) for sec in self.book.sections)
        if total <= 1:
            QMessageBox.information(self, tr('editor.chapter.delete_title', 'Hoofdstuk verwijderen'), tr('editor.chapter.delete_last', 'Het laatste hoofdstuk van een boek kan niet worden verwijderd.'))
            return

        deleting_active = bool(self.chapter and self.chapter.id == chapter_id)
        active_id = self.chapter.id if self.chapter else None
        next_chapter = self.main.library.adjacent_chapter_for_delete(self.book, chapter_id) if deleting_active else None
        message = (
            tr('editor.chapter.delete_confirm', 'Weet je zeker dat je “{title}” wilt verwijderen?\n\nHet hoofdstuk wordt naar de prullenbak verplaatst en kan later worden hersteld.', title=chapter.title)
        )
        if not confirm(self, tr('editor.chapter.delete_title', 'Hoofdstuk verwijderen'), message):
            return
        if self.save() is False:
            return
        try:
            self.main.library.create_version(self.book, kind='chapter_delete')
            removed = self.main.library.delete_chapter(self.book, chapter_id)
        except (ExternalModificationError, RevisionVerificationError) as exc:
            self._handle_concurrency_issue(exc); return
        except Exception as exc:
            QMessageBox.critical(self, tr('editor.chapter.delete_title', 'Hoofdstuk verwijderen'), tr('editor.chapter.delete_failed', 'Verwijderen is mislukt.\n\n{error}', error=exc))
            return
        if not removed:
            QMessageBox.warning(self, tr('editor.chapter.delete_title', 'Hoofdstuk verwijderen'), tr('editor.chapter.delete_failed_short', 'Het hoofdstuk kon niet worden verwijderd.'))
            return

        self._chapter_word_counts.pop(chapter_id, None)
        if deleting_active:
            self.chapter = None
            self.dirty = False

        def restore_selection():
            target_id = next_chapter.id if deleting_active and next_chapter else active_id
            if not target_id:
                return
            _, existing = self.find_chapter_in_book(target_id)
            if existing:
                if deleting_active:
                    self.open_chapter(existing)
                self.select_tree_chapter(existing.id)

        self.populate_tree(after=restore_selection)
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
        # while the spelling panel is closed. Disabling spelling must remove it
        # immediately; a restart may never be required for presentation state.
        active = bool(enabled and self.dictionary.words)
        self.highlighter.set_active(active)
        self.highlighter.rehighlight()
        document = self.editor.document()
        document.markContentsDirty(0, max(1, document.characterCount()))
        self.editor.viewport().update()
        if not enabled:
            self.spell.rows = []
            self.spell.index = 0
            self.spell.suggestions.clear()
            self.spell.word.clear()
            self.spell.status.setText(tr('spell.disabled', 'Spellingscontrole is uitgeschakeld.'))
            if self.right.currentWidget() is self.spell:
                self._remember_panel_widths()
                self.right.setCurrentWidget(self.search)
                self.right.hide()

    def find_chapter_in_book(self, cid):
        for s in self.book.sections:
            for c in s.chapters:
                if c.id == cid: return s, c
        return None, None

    def tree_clicked(self, item, col):
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        if data[0] == 'chapter':
            self.open_chapter_id(data[1])
        elif data[0] == 'publication':
            self.open_publication_item(data[1])
        elif data[0] == 'manuscript_group' and col == 1 and data[1] in ('front', 'back'):
            self.show_publication_setup()

    def tree_keyboard_activated(self, item):
        """Keyboard equivalent of the useful tree click actions.

        Chapter/publication rows can be reached with the arrow keys and opened
        with Enter/Return. Section/group rows retain the familiar tree behavior:
        Enter toggles expansion, while Voorwerk/Achterwerk can still be edited
        through the visible ``wijzig`` cell with the mouse.
        """
        if item is None:
            return
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        if data[0] in ('chapter', 'publication'):
            self.tree_clicked(item, 0)
        elif data[0] in ('section', 'manuscript_group'):
            item.setExpanded(not item.isExpanded())

    def open_chapter_id(self, cid):
        _, c = self.find_chapter_in_book(cid)
        if c: self.open_chapter(c)

    def _editor_source_text(self):
        """Compatibility wrapper for the shared persistent editor source."""
        return self.editor.source_text()

    def _set_editor_chapter(self, chapter):
        self.content_stack.setCurrentWidget(self.manuscript_content)
        self.chapter = chapter
        self.chapter_title.setText(chapter.title)
        self.editor.blockSignals(True)
        try:
            text = self.main.library.read_chapter(self.book, chapter)
        except UnicodeDecodeError:
            self._chapter_corrupt = True
            text = tr(
                'editor.corrupt_text',
                'Dit hoofdstukbestand is beschadigd en kan niet als UTF-8 worden gelezen.\n\n'
                'Het bestand is alleen-lezen om overschrijven te voorkomen. Open Integriteit om het te controleren en zo mogelijk te herstellen.'
            )
            self.editor.setPlainText(text)
            self._clean_text = self._editor_source_text()
            self.editor.setReadOnly(True)
            self.chapter_title.setReadOnly(True)
            self.editor.blockSignals(False)
            self.dirty = False
            self.autosave_timer.stop()
            self.autosave_status.setText(tr('editor.corrupt_readonly', 'Beschadigd · alleen-lezen'))
            self._sync_undo_redo()
            self.update_counts()
            self.refresh_chapter_context()
            self.main.sync_tool_buttons()
            return
        self._chapter_corrupt = False
        self.editor.setPlainText(text)
        self._clean_text = self._editor_source_text()
        if not self.preview_live_book:
            self.editor.setReadOnly(False)
            self.chapter_title.setReadOnly(False)
        self.editor.blockSignals(False)
        self._sync_undo_redo()
        self.editor.apply_typography(WritingTypography.from_settings(self.main.settings))
        self.editor.apply_scene_break_formatting()
        self.editor.reset_undo_history()
        self._sync_undo_redo()
        self.dirty = False
        self.autosave_status.setText(tr('editor.status.saved', '● Opgeslagen'))
        self.update_counts()
        if hasattr(self.main, 'toolrail') and self.main.stack.currentWidget() is self:
            self.main.toolrail.show()
        self.refresh_chapter_context()
        self.main.sync_tool_buttons()
        if self.right.isVisible() and self.right.currentWidget() is self.spell:
            self.spell.refresh()

    def open_chapter(self, chapter):
        chapter_id = chapter.id
        if self.save() is False:
            return
        # A conflict resolution may have reloaded the entire book. Resolve the
        # requested chapter against the current object instead of using a stale
        # Chapter instance from before that reload.
        _, current = self.find_chapter_in_book(chapter_id)
        if current:
            self._set_editor_chapter(current)

    def _spell_contents_changed(self, _position, removed, added):
        if removed + added <= 0:
            return
        self._spell_cursor_from_edit = True
        QTimer.singleShot(0, lambda: setattr(self, '_spell_cursor_from_edit', False))

    def on_text_changed(self):
        if self.preview_live_book or self._chapter_corrupt:
            return
        # QSyntaxHighlighter.rehighlight() and other presentation-only passes can
        # emit textChanged even though the manuscript source text is identical.
        # Dirty state must describe source changes only: otherwise Settings or a
        # spelling action can trigger an unnecessary autosave and even a false
        # two-computer conflict.
        current_text = self._editor_source_text()
        if current_text == self._clean_text:
            self.dirty = False
            self.autosave_timer.stop()
            self.autosave_status.setText(tr('editor.status.saved', '● Opgeslagen'))
            self._schedule_undo_redo_sync()
            self.update_counts()
            return
        self.dirty = True
        self.autosave_status.setText(tr('editor.status.unsaved', 'Niet opgeslagen'))
        self._schedule_undo_redo_sync()
        self.update_counts()
        self.autosave_timer.start()


    def _spell_follow_cursor(self):
        """Let the open spelling panel follow deliberate caret navigation, never typing."""
        if getattr(self, '_spell_cursor_from_edit', False):
            return
        if self.right.isVisible() and self.right.currentWidget() is self.spell:
            self.spell.follow_editor_cursor()

    def _adopt_disk_book(self, preferred_chapter_id: str | None = None):
        latest = self.main.library.load_book(self.book.path)
        self.main.adopt_active_book(latest, preferred_chapter_id)
        return latest, self.chapter

    def _ensure_current_chapter_in(self, latest, old_book, old_chapter):
        _, _, target = self.main.library.locate_chapter(latest, old_chapter.id)
        if target is not None:
            return target
        # The external version may have removed the chapter entirely. Choosing
        # "Mijn versie" means the current chapter must survive, so reattach it to
        # the corresponding section when possible (otherwise the first section).
        old_section = next((s for s in old_book.sections if any(c.id == old_chapter.id for c in s.chapters)), None)
        section = next((s for s in latest.sections if old_section and s.id == old_section.id), None)
        if section is None:
            if not latest.sections:
                latest.sections.append(Section(id='root', title='Manuscript'))
            section = latest.sections[0]
        target = Chapter(id=old_chapter.id, title=old_chapter.title, file=old_chapter.file)
        section.chapters.append(target)
        return target

    def _resolve_external_change(self, exc: ExternalModificationError) -> bool:
        # A history snapshot is read-only. Never run the normal live-book conflict
        # machinery while self.book points into archive/<book>/<version>; doing so
        # could track or write the snapshot as if it were the live book.
        if self.preview_live_book:
            self.exit_history_preview(reload_latest=True)
            QMessageBox.warning(
                self,
                tr('history.preview_conflict_title', 'Historische versie gesloten'),
                tr(
                    'history.preview_conflict_text',
                    'Het live boek is intussen extern gewijzigd. De historische weergave is gesloten; er is niets in het archief aangepast.'
                ),
            )
            return False
        if self.tree.is_dragging:
            self._save_pending_after_drag = True
            self.autosave_timer.stop()
            self.autosave_status.setText(tr('editor.status.external_after_move', 'Extern gewijzigd · na verplaatsen controleren'))
            return False
        self.autosave_timer.stop()
        if not self.book:
            return False
        changed = '\n'.join(f'• {name}' for name in exc.changed_files[:6])
        if len(exc.changed_files) > 6:
            changed += '\n• ' + tr('editor.conflict.more', '… en {count} meer', count=len(exc.changed_files) - 6)

        # Voorwerk/Achterwerk and publication setup deliberately have no active
        # manuscript chapter. Structural actions can still hit a book.json
        # conflict there, so never fail silently just because ``chapter`` is None.
        # If the current publication item itself is dirty, keep it in memory and
        # let its dedicated publication conflict flow resolve first; adopting the
        # disk book here would otherwise discard those unsaved fields/text.
        if not self.chapter:
            current_publication_widget = self.content_stack.currentWidget()
            publication_pending = (
                current_publication_widget is self.publication_editor
                and self.publication_editor.has_pending_changes()
            ) or (
                current_publication_widget is self.publication_setup
                and self.publication_setup.has_pending_changes()
            )
            if publication_pending:
                QMessageBox.warning(
                    self,
                    tr('structure_conflict.pending_title', 'Actie niet uitgevoerd'),
                    tr(
                        'structure_conflict.pending_text',
                        'Het boek is extern gewijzigd en deze publicatieweergave bevat nog niet-opgeslagen wijzigingen. '
                        'Sla de wijzigingen eerst op of annuleer ze en los het conflict daarna op. De structuuractie is niet uitgevoerd.'
                    ),
                )
                self.main.status.showMessage(
                    tr('structure_conflict.retry_after_save', 'Actie niet uitgevoerd · rond eerst de publicatiewijzigingen af'),
                    6000,
                )
                return False

            box = QMessageBox(self)
            box.setIcon(QMessageBox.Warning)
            box.setWindowTitle(tr('structure_conflict.title', 'Boek extern gewijzigd'))
            box.setText(tr('structure_conflict.text', 'Dit boek is buiten QuietWriter gewijzigd.'))
            box.setInformativeText(tr(
                'structure_conflict.info',
                'De structuuractie is niet uitgevoerd om te voorkomen dat een andere versie wordt overschreven.\n\n'
                'Gewijzigd:\n{changed}\n\n'
                'Wil je de nieuwste versie van het boek laden? Controleer daarna de structuur en voer de actie opnieuw uit.',
                changed=changed,
            ))
            load_latest = box.addButton(tr('structure_conflict.load_latest', 'Nieuwste versie laden'), QMessageBox.AcceptRole)
            box.addButton(tr('common.cancel', 'Annuleren'), QMessageBox.RejectRole)
            box.setDefaultButton(load_latest)
            box.exec()
            if box.clickedButton() is not load_latest:
                self.main.status.showMessage(
                    tr('structure_conflict.cancelled', 'Extern gewijzigd · structuuractie niet uitgevoerd'), 5000
                )
                return False
            old_book = self.book
            try:
                # Preserve the current external live state in History before
                # rebasing the whole UI on it. The failed structure mutation has
                # not changed the stale in-memory Book because storage verifies
                # before mutating.
                self.main.library.create_version(old_book, kind='conflict_external')
                self._adopt_disk_book(None)
                self.autosave_status.setText(tr('structure_conflict.loaded_short', '● Nieuwste versie geladen'))
                self.main.status.showMessage(
                    tr(
                        'structure_conflict.retry',
                        'De nieuwste versie is geladen. De structuuractie is niet uitgevoerd; controleer de boekstructuur en probeer opnieuw.'
                    ),
                    7000,
                )
            except Exception as error:
                QMessageBox.critical(
                    self,
                    tr('structure_conflict.failed_title', 'Conflict niet opgelost'),
                    tr('structure_conflict.failed_text', 'De nieuwste versie kon niet veilig worden geladen. Er is niets overschreven.\n\n{error}', error=error),
                )
            # False means the original structural write was not completed. This
            # also prevents move_chapter() from silently retrying against a tree
            # the user has not yet inspected.
            return False

        old_book = self.book
        old_chapter = self.chapter
        chapter_id = old_chapter.id
        local_text = self._editor_source_text()

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(tr('editor.external.title', 'Boek extern gewijzigd'))
        box.setText(tr('editor.external.text', 'Dit boek is buiten QuietWriter gewijzigd.'))
        box.setInformativeText(tr(
            'editor.external.info',
            'QuietWriter heeft niet opgeslagen om te voorkomen dat een andere versie wordt overschreven.\n\nGewijzigd:\n{changed}\n\nWelke versie wil je als uitgangspunt gebruiken? Beide keuzes maken eerst automatisch een herstelversie.',
            changed=changed,
        ))
        use_mine = box.addButton(tr('editor.external.use_mine', 'Mijn versie gebruiken'), QMessageBox.AcceptRole)
        use_disk = box.addButton(tr('editor.external.use_disk', 'Versie op schijf gebruiken'), QMessageBox.DestructiveRole)
        box.setDefaultButton(use_disk)
        box.exec()
        clicked = box.clickedButton()
        if clicked not in (use_mine, use_disk):
            self.autosave_status.setText(tr('editor.status.external_unsaved', '⚠ Extern gewijzigd · niet opgeslagen'))
            self.dirty = True
            return False

        try:
            if clicked is use_mine:
                # Preserve the complete external state first. Then reload it as
                # the new base and overlay only the chapter currently in memory.
                # Other external chapter/manifest changes therefore survive.
                self.main.library.create_version(old_book, kind='conflict_external')
                latest = self.main.library.load_book(old_book.path)
                self.main.library.track_book(latest)
                target = self._ensure_current_chapter_in(latest, old_book, old_chapter)
                self.main.library.save_chapter(latest, target, local_text)
                self.book = latest
                self._adopt_disk_book(chapter_id)
                self.autosave_status.setText(tr('editor.status.local_preserved', '● Eigen versie bewaard'))
            else:
                # Preserve the in-memory manuscript structure and current editor
                # text in History before discarding them in favour of disk.
                self.main.library.create_version_from_state(
                    old_book, {old_chapter.file: local_text}, kind='conflict_local'
                )
                self._adopt_disk_book(chapter_id)
                self.autosave_status.setText(tr('editor.status.disk_loaded', '● Versie op schijf geladen'))
            return True
        except FutureBookFormatError:
            self.book = old_book; self.chapter = old_chapter
            self.editor.blockSignals(True); self.editor.setPlainText(local_text); self.editor.blockSignals(False)
            self.dirty = True
            already = clicked is use_disk  # that branch created conflict_local before load_book()
            return self._leave_future_format_book(old_book, {old_chapter.file: local_text}, snapshot_exists=already)
        except ExternalModificationError:
            # The disk changed again while the user was deciding. Never bypass
            # the guard; leave local text in the editor and let the user retry.
            self.book = old_book; self.chapter = old_chapter
            self.editor.blockSignals(True); self.editor.setPlainText(local_text); self.editor.blockSignals(False)
            self.dirty = True
            self.autosave_status.setText(tr('editor.status.external_changed_again', '⚠ Opnieuw extern gewijzigd'))
            QMessageBox.warning(self, tr('editor.external.changed_again_title', 'Boek opnieuw gewijzigd'), tr('editor.external.changed_again_text', 'Het boek veranderde opnieuw tijdens het oplossen van het conflict. Er is niets overschreven. Probeer opnieuw nadat de synchronisatie klaar is.'))
            return False
        except Exception as error:
            self.book = old_book; self.chapter = old_chapter
            self.editor.blockSignals(True); self.editor.setPlainText(local_text); self.editor.blockSignals(False)
            self.dirty = True
            self.autosave_status.setText(tr('editor.status.conflict_unresolved', '⚠ Conflict niet opgelost'))
            QMessageBox.critical(self, tr('editor.external.resolve_failed_title', 'Conflict niet opgelost'), tr('editor.external.resolve_failed_text', 'De herstelactie is mislukt. Er is niet verder opgeslagen.\n\n{error}', error=error))
            return False

    def _handle_verification_error(self, exc: RevisionVerificationError) -> bool:
        self.autosave_status.setText(tr('editor.status.save_temporarily_unavailable', 'Opslaan tijdelijk niet mogelijk'))
        self.dirty = True
        # Sync software can briefly lock/on-demand hydrate a file. This is not a
        # content conflict. Keep the text in memory and quietly retry autosave.
        self.autosave_timer.start(1800)
        return False

    def _handle_storage_write_error(self, exc: StorageWriteError) -> bool:
        self.dirty = True
        self.autosave_status.setText(tr('editor.status.save_locked', '⚠ Opslaan mislukt · bestand vergrendeld'))
        self.autosave_timer.start(2500)
        return False

    def _leave_future_format_book(self, old_book, chapter_overrides=None, *, snapshot_exists=False):
        """Preserve local work, then detach from a book this version cannot safely edit."""
        try:
            if not snapshot_exists:
                self.main.library.create_version_from_state(old_book, chapter_overrides or {}, kind='conflict_local')
        except Exception as snapshot_error:
            QMessageBox.critical(self, tr('editor.future.snapshot_failed_title', 'Lokale tekst niet veiliggesteld'),
                tr('editor.future.snapshot_failed_text', 'Dit boek gebruikt inmiddels een nieuwere QuietWriter-versie, maar je lokale tekst kon niet in Versiegeschiedenis worden bewaard. Het boek blijft daarom open. Kopieer je tekst handmatig voordat je afsluit.\n\n{error}', error=snapshot_error))
            return False
        QMessageBox.warning(self, tr('editor.future.title', 'Nieuwere QuietWriter nodig'),
            tr('editor.future.text', 'Dit boek is op een andere computer met een nieuwere QuietWriter opgeslagen. Je laatste lokale tekst is bewaard in Versiegeschiedenis. QuietWriter sluit dit boek nu om te voorkomen dat het nieuwere formaat wordt beschadigd. Werk QuietWriter bij voordat je verdergaat.'))
        self.main.force_return_to_bookshelf(old_book)
        return False

    def save(self):
        # Never touch disk, show a conflict dialog or mutate the manuscript model
        # while a drag interaction owns QTreeWidget indexes. Autosave is resumed
        # after dragFinished; callers that require an immediate save receive False
        # and therefore abort their dependent action safely.
        if self.tree.is_dragging:
            if self.dirty:
                self._save_pending_after_drag = True
                self.autosave_status.setText(tr('editor.status.unsaved_after_move', 'Niet opgeslagen · na verplaatsen'))
            return False
        if self.preview_live_book:
            return True
        # Publication text is independent of the last manuscript chapter.
        # Handle those contexts before applying the chapter-corruption guard.
        if self.content_stack.currentWidget() is self.publication_editor:
            return self.publication_editor.save_pending()
        if self.content_stack.currentWidget() is self.publication_setup:
            return True
        if self._chapter_corrupt:
            self.dirty = False
            self.autosave_timer.stop()
            return True
        if not (self.book and self.chapter and self.dirty):
            return True
        try:
            source_text = self._editor_source_text()
            self.main.library.save_chapter(self.book, self.chapter, source_text)
        except ExternalModificationError as exc:
            return self._resolve_external_change(exc)
        except RevisionVerificationError as exc:
            return self._handle_verification_error(exc)
        except StorageWriteError as exc:
            return self._handle_storage_write_error(exc)
        self._clean_text = source_text
        self.dirty = False
        self.main.search_index.rebuild_book(self.book)
        self.autosave_status.setText(tr('editor.status.saved_just_now', '● Opgeslagen · zojuist'))
        self.update_counts(saved=True)
        return True

    def _handle_concurrency_issue(self, exc) -> bool:
        if isinstance(exc, ExternalModificationError):
            return self._resolve_external_change(exc)
        if isinstance(exc, RevisionVerificationError):
            return self._handle_verification_error(exc)
        raise exc

    def rename_current(self):
        if self.tree.is_dragging:
            self._rename_pending_after_drag = True
            return
        if self.preview_live_book:
            return
        if self.chapter:
            old_title = self.chapter.title
            self.chapter.title = self.chapter_title.text().strip() or tr('editor.chapter.untitled', 'Nieuw hoofdstuk')
            try:
                self.main.library.save_manifest(self.book)
            except (ExternalModificationError, RevisionVerificationError) as exc:
                self.chapter.title = old_title
                self._handle_concurrency_issue(exc)
                return
            except Exception as exc:
                self.chapter.title = old_title
                QMessageBox.critical(self, tr('editor.rename.failed_title', 'Hernoemen mislukt'), tr('editor.rename.chapter_failed', 'Het hoofdstuk is niet hernoemd.\n\n{error}', error=exc))
                return
            self.populate_tree()

    def _book_chapter_ids(self):
        if not self.book:
            return set()
        return {chapter.id for section in self.book.sections for chapter in section.chapters}

    def _rebuild_word_count_cache(self):
        """Read each chapter once and cache its word count.

        Typing must never cause disk reads of every other chapter.  The cache is
        rebuilt when a book/snapshot is loaded and refreshed incrementally after
        structural or bulk-edit operations.
        """
        self._chapter_word_counts = {}
        if not self.book:
            return
        for section in self.book.sections:
            for chapter in section.chapters:
                try:
                    text = self.main.library.read_chapter(self.book, chapter)
                    self._chapter_word_counts[chapter.id] = count_words(text)
                except Exception:
                    self._chapter_word_counts[chapter.id] = 0

    def _ensure_word_count_cache(self):
        ids = self._book_chapter_ids()
        if ids != set(self._chapter_word_counts):
            self._rebuild_word_count_cache()

    def update_counts(self, saved=False):
        txt = self.editor.toPlainText()
        words = count_words(txt)
        self._ensure_word_count_cache()
        if self.chapter:
            self._chapter_word_counts[self.chapter.id] = words
        total = sum(self._chapter_word_counts.values()) if self.book else 0
        chapter_index = 0; chapter_total = 0
        if self.book:
            flat = [c for sec in self.book.sections for c in sec.chapters]
            chapter_total = len(flat)
            if self.chapter:
                chapter_index = next((i+1 for i,c in enumerate(flat) if c.id == self.chapter.id), 0)
        locale = current_locale()
        def fmt_count(value):
            text = f'{value:,}'
            return text.replace(',', '.') if locale == 'nl' else text
        book_key = 'editor.status.book.one' if total == 1 else 'editor.status.book.many'
        book_text = tr(book_key, 'Boek: {count} woord' if total == 1 else 'Boek: {count} woorden', count=fmt_count(total))
        if chapter_total and self.chapter:
            chapter_key = 'editor.status.chapter.one' if words == 1 else 'editor.status.chapter.many'
            chapter_text = tr(
                chapter_key,
                'Hoofdstuk {index} van {total}: {count} woord' if words == 1 else 'Hoofdstuk {index} van {total}: {count} woorden',
                index=chapter_index, total=chapter_total, count=fmt_count(words),
            )
            self.main.set_document_status(book_text + ' · ' + chapter_text)
        else:
            self.main.set_document_status(book_text if self.book else '')

    def add_menu(self):
        """Toon een rustige flyout voor nieuwe manuscriptonderdelen.

        De popup is child van EditorPage en verwijdert zichzelf bij sluiten. Er
        wordt bewust geen blijvende Python-reference bewaard: Qt.Popup sluit
        automatisch bij een klik erbuiten en WA_DeleteOnClose vernietigt het
        object daarna. Zo kan een volgende klik nooit een al verwijderde
        Shiboken-wrapper proberen te gebruiken.
        """
        if not self.book or self.preview_live_book:
            return
        popup = QFrame(self, Qt.Popup | Qt.FramelessWindowHint)
        popup.setObjectName('flyout')
        popup.setAttribute(Qt.WA_DeleteOnClose, True)
        lay = QVBoxLayout(popup); lay.setContentsMargins(8,8,8,8); lay.setSpacing(4)
        title = QLabel(tr('editor.add_what', 'Toevoegen')); title.setObjectName('sectionTitle'); lay.addWidget(title)
        chapter_btn = QPushButton(tr('editor.new_chapter', 'Hoofdstuk')); chapter_btn.setObjectName('flyoutButton')
        section_btn = QPushButton(tr('editor.new_section', 'Sectie')); section_btn.setObjectName('flyoutButton')
        publication_btn = QPushButton(tr('editor.publication_structure', 'Publicatiestructuur')); publication_btn.setObjectName('flyoutButton')
        lay.addWidget(chapter_btn); lay.addWidget(section_btn); lay.addWidget(publication_btn)
        shadow = QGraphicsDropShadowEffect(popup); shadow.setBlurRadius(24); shadow.setOffset(0, 7); shadow.setColor(QColor(0,0,0,70)); popup.setGraphicsEffect(shadow)
        chapter_btn.clicked.connect(lambda: (popup.close(), self._create_chapter()))
        section_btn.clicked.connect(lambda: (popup.close(), self._create_section()))
        publication_btn.clicked.connect(lambda: (popup.close(), self.show_publication_setup()))
        escape = QShortcut(QKeySequence(Qt.Key_Escape), popup)
        escape.setContext(Qt.WidgetWithChildrenShortcut)
        popup._escape_shortcut = escape
        def close_from_keyboard():
            popup.close()
            self.add_content_button.setFocus()
        escape.activated.connect(close_from_keyboard)
        popup.adjustSize()
        pos = self.add_content_button.mapToGlobal(QPoint(self.add_content_button.width() - popup.sizeHint().width(), self.add_content_button.height() + 6))
        popup.move(pos); popup.show(); popup.raise_(); chapter_btn.setFocus()

    def _create_section(self):
        if not self.book or self.preview_live_book:
            return
        title, ok = prompt_text(self, tr('editor.new_section', 'Nieuwe sectie'), tr('editor.name', 'Naam:'))
        if not ok:
            return
        insert_after = None
        item = self.tree.currentItem()
        if item:
            data = item.data(0, Qt.UserRole)
            if data and data[0] == 'section':
                insert_after = data[1]
            elif data and data[0] == 'chapter':
                sec, _ = self.find_chapter_in_book(data[1]); insert_after = sec.id if sec else None
        try:
            self.main.library.add_section(self.book, title or tr('editor.new_section', 'Nieuwe sectie'), after_section_id=insert_after)
        except (ExternalModificationError, RevisionVerificationError) as exc:
            self._handle_concurrency_issue(exc); return
        except Exception as exc:
            QMessageBox.critical(self, tr('editor.new_section', 'Nieuwe sectie'), tr('editor.new_section.failed', 'De sectie is niet toegevoegd.\n\n{error}', error=exc))
            return
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
                found, _ = self.find_chapter_in_book(data[1])
                if found:
                    section = found
        title, ok = prompt_text(self, tr('editor.new_chapter', 'Nieuw hoofdstuk'), tr('editor.title', 'Titel:'))
        if not ok:
            return
        try:
            c = self.main.library.add_chapter(self.book, section, title or tr('editor.new_chapter', 'Nieuw hoofdstuk'))
        except (ExternalModificationError, RevisionVerificationError) as exc:
            self._handle_concurrency_issue(exc); return
        except Exception as exc:
            QMessageBox.critical(self, tr('editor.new_chapter', 'Nieuw hoofdstuk'), tr('editor.new_chapter.failed', 'Het hoofdstuk is niet toegevoegd.\n\n{error}', error=exc))
            return
        self._chapter_word_counts[c.id] = 0
        def open_new_chapter(chapter_id=c.id):
            _, current = self.find_chapter_in_book(chapter_id)
            if current:
                self.open_chapter(current)
                self.select_tree_chapter(current.id)
        self.populate_tree(after=open_new_chapter)

    def insert_scene_break(self):
        if not self.book or not self.chapter or self.preview_live_book or self._chapter_corrupt:
            return
        cursor = self.editor.textCursor()
        text = self._editor_source_text()
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
        """Toggle the regular right-side insert workflow.

        Insert is a first-class editor tool just like Search, AI and Spelling.
        The panel resets to its top-level choices whenever it is opened, so a
        future image/settings flow can live inside the same panel without
        leaving stale subpages behind.
        """
        if not self.book or self.preview_live_book or not self.chapter:
            return
        opening = not (self.right.isVisible() and self.right.currentWidget() is self.insert)
        if opening:
            self.insert.reset()
        self._toggle_right_widget(self.insert, self.insert.scene_break_button)

    def _insert_scene_break_from_panel(self):
        self.insert_scene_break()
        if self.right.isVisible() and self.right.currentWidget() is self.insert:
            self._remember_panel_widths()
            self.right.hide()
        self.main.sync_tool_buttons()

    def _resolve_editor_image_path(self, reference: str):
        if not self.book or not self.chapter:
            return None
        try:
            _asset, path = self.media_store.resolve_reference(self.book, self.chapter.file, reference)
            return path
        except MediaError:
            return None

    def _image_block_ref(self, number: int):
        block = self.editor.document().findBlockByNumber(number)
        if not block.isValid():
            return None, None
        return block, image_reference_for_line(block.text())

    def _find_editing_image_block(self):
        preferred = self._editing_image_block
        path = self._editing_image_reference_path
        if preferred is not None:
            block, ref = self._image_block_ref(preferred)
            if ref and (not path or ref.path == path):
                return block, ref
        if path:
            block = self.editor.document().begin()
            while block.isValid():
                ref = image_reference_for_line(block.text())
                if ref and ref.path == path:
                    return block, ref
                block = block.next()
        return None, None

    def _open_image_editor(self, block_number: int):
        if not self.book or not self.chapter or self.preview_live_book:
            return
        block, ref = self._image_block_ref(block_number)
        if not block or not ref:
            return
        asset_path = None
        display_name = Path(ref.path).name
        try:
            asset, asset_path = self.media_store.resolve_reference(self.book, self.chapter.file, ref.path)
            display_name = asset.original_name or display_name
        except MediaError:
            pass
        self._editing_image_block = block_number
        self._editing_image_reference_path = ref.path
        self.insert.show_image_edit_page(
            asset_path, ref.alt, ref.caption, display_name,
            width=ref.width, align=ref.align, wrap=ref.wrap,
        )
        self.right.setCurrentWidget(self.insert)
        self._show_right_panel()
        self.insert.image_page.alt_edit.setFocus()
        self.main.sync_tool_buttons()

    def _save_image_edit_from_panel(self, source_path: str, alt_text: str, caption: str,
                                    width: str, align: str, wrap: bool, replace_image: bool):
        if not self.book or not self.chapter or self.preview_live_book:
            return
        block, old_ref = self._find_editing_image_block()
        if not block or not old_ref:
            QMessageBox.warning(
                self,
                tr('insert.image.edit_title', 'Afbeelding bewerken'),
                tr('insert.image.edit_missing', 'Het afbeeldingsblok bestaat niet meer in het manuscript.'),
            )
            return
        new_reference = old_ref.path
        if replace_image:
            try:
                asset = self.media_store.import_image(self.book, Path(source_path))
                new_reference = self.media_store.reference_for_chapter(self.chapter, asset)
            except (ExternalModificationError, RevisionVerificationError) as exc:
                self._handle_concurrency_issue(exc)
                return
            except MediaError as exc:
                QMessageBox.warning(self, tr('insert.image.error_title', 'Afbeelding toevoegen'), str(exc))
                return
            except Exception as exc:
                QMessageBox.critical(
                    self,
                    tr('insert.image.edit_title', 'Afbeelding bewerken'),
                    tr('insert.image.edit_error', 'De afbeelding kon niet worden bijgewerkt.\n\n{error}', error=exc),
                )
                return

        markdown = build_image_markdown(
            new_reference, alt_text, caption, width=width, align=align, wrap=wrap
        )
        cursor = QTextCursor(block)
        cursor.beginEditBlock()
        cursor.setPosition(block.position())
        cursor.setPosition(block.position() + len(block.text()), QTextCursor.KeepAnchor)
        cursor.insertText(markdown)
        cursor.endEditBlock()
        self.editor.setTextCursor(cursor)
        self.editor.schedule_formatting(immediate=True, join_previous=True)
        self.editor.refresh_image_blocks()
        self._editing_image_block = None
        self._editing_image_reference_path = None
        if self.right.isVisible() and self.right.currentWidget() is self.insert:
            self._remember_panel_widths()
            self.right.hide()
        self.editor.setFocus()
        self.main.status.showMessage(tr('insert.image.updated', 'Afbeelding bijgewerkt'), 2500)
        self.main.sync_tool_buttons()

    def _delete_image_block(self, block_number: int):
        if not self.book or not self.chapter or self.preview_live_book:
            return
        block, ref = self._image_block_ref(block_number)
        if not block or not ref:
            return
        if not confirm(
            self,
            tr('image_block.delete_title', 'Afbeelding verwijderen'),
            tr(
                'image_block.delete_confirm',
                'Deze afbeelding uit het manuscript verwijderen?\n\nHet afbeeldingsbestand blijft bewaard voor versiegeschiedenis en herstel.'
            ),
        ):
            return

        text = self._editor_source_text()
        start = block.position()
        end = start + len(block.text())
        left = text[:start].rstrip('\n')
        right = text[end:].lstrip('\n')
        separator = '\n\n' if left and right else ''
        new_text = left + separator + right
        caret = len(left)

        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.Document)
        cursor.insertText(new_text)
        cursor.setPosition(min(caret, len(new_text)))
        cursor.endEditBlock()
        self.editor.setTextCursor(cursor)
        self.editor.schedule_formatting(immediate=True, join_previous=True)
        self.editor.refresh_image_blocks()
        self.editor.setFocus()
        self.main.status.showMessage(tr('image_block.deleted', 'Afbeelding uit het manuscript verwijderd'), 2500)

    def _insert_image_from_panel(self, source_path: str, alt_text: str, caption: str,
                                 width: str, align: str, wrap: bool):
        if not self.book or not self.chapter or self.preview_live_book or self._chapter_corrupt:
            return
        try:
            asset = self.media_store.import_image(self.book, Path(source_path))
        except (ExternalModificationError, RevisionVerificationError) as exc:
            self._handle_concurrency_issue(exc)
            return
        except MediaError as exc:
            QMessageBox.warning(
                self,
                tr('insert.image.error_title', 'Afbeelding toevoegen'),
                str(exc),
            )
            return
        except Exception as exc:
            QMessageBox.critical(
                self,
                tr('insert.image.error_title', 'Afbeelding toevoegen'),
                tr('insert.image.error', 'De afbeelding kon niet worden toegevoegd.\n\n{error}', error=exc),
            )
            return

        reference = self.media_store.reference_for_chapter(self.chapter, asset)
        block = build_image_markdown(
            reference, alt_text, caption, width=width, align=align, wrap=wrap
        )
        cursor = self.editor.textCursor()
        text = self._editor_source_text()
        new_text, new_pos = insert_image_block(text, cursor.position(), block)
        cursor.beginEditBlock()
        cursor.select(QTextCursor.Document)
        cursor.insertText(new_text)
        cursor.setPosition(min(new_pos, len(new_text)))
        cursor.endEditBlock()
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()
        self.editor.schedule_formatting(immediate=True, join_previous=True)
        if self.right.isVisible() and self.right.currentWidget() is self.insert:
            self._remember_panel_widths()
            self.right.hide()
        self.main.status.showMessage(tr('insert.image.added', 'Afbeelding toegevoegd aan het manuscript'), 2500)
        self.main.sync_tool_buttons()

    def create_manual_version(self):
        live = self.preview_live_book or self.book
        if not live:
            return
        if self.preview_live_book:
            self.exit_history_preview()
            live = self.book
        if self.save() is False:
            return
        try:
            row = self.main.library.create_version(live, kind='manual')
            self.history.set_book(live)
            self.history.select_version(row['id'])
            self.main.status.showMessage(tr('history.new_saved', 'Nieuwe versie opgeslagen.'), 3500)
        except Exception as exc:
            QMessageBox.critical(self, tr('history.create_error_title', 'Versie maken'), tr('history.create_error_text', 'De versie kon niet worden gemaakt.\n\n{error}', error=exc))

    def set_version_starred(self, version_id: str, starred: bool):
        live = self.preview_live_book or self.book
        if not live:
            return
        try:
            self.main.library.set_version_starred(live, version_id, starred)
            self.history.set_book(live)
            self.history.select_version(version_id)
        except Exception as exc:
            QMessageBox.critical(self, tr('history.star_error_title', 'Versiegeschiedenis'), tr('history.star_error_text', 'De ster kon niet worden opgeslagen.\n\n{error}', error=exc))

    def _history_label(self, row: dict) -> str:
        try:
            dt = datetime.fromisoformat(row['created_at'])
            locale = QLocale('en_US' if current_locale() == 'en' else 'nl_NL')
            date_label = locale.toString(QDate(dt.year, dt.month, dt.day), 'd MMMM yyyy')
            return f'{dt:%H:%M}, {date_label}'
        except Exception:
            return row.get('created_at', tr('history.older', 'Oudere versie'))

    def enter_history_preview(self, version_id: str):
        live = self.preview_live_book or self.book
        if not live:
            return
        # Switching from one historical version to another does not touch disk.
        if not self.preview_live_book:
            if self.save() is False:
                return
            self.preview_live_book = live
            self.preview_return_chapter_id = self.chapter.id if self.chapter else None
        try:
            snapshot = self.main.library.load_version(self.preview_live_book, version_id)
            row = next((r for r in self.main.library.list_versions(self.preview_live_book) if r['id'] == version_id), None)
        except Exception as exc:
            QMessageBox.critical(self, tr('history.open_error_title', 'Versiegeschiedenis'), tr('history.open_error_text', 'De gekozen versie kon niet worden geopend.\n\n{error}', error=exc))
            if self.preview_live_book:
                self.exit_history_preview()
            return
        self.preview_version_id = version_id
        self.book = snapshot
        self._rebuild_word_count_cache()
        self.chapter = None; self.dirty = False
        self._set_book_title(snapshot.title)
        self.editor.setReadOnly(True); self.chapter_title.setReadOnly(True); self.tree.setDragEnabled(False)
        self.history_banner_label.setText(tr('history.preview_banner', 'Historische versie · {label}', label=self._history_label(row or {'created_at': ''})))
        self.history_banner.show()
        self.populate_tree()
        wanted = self.preview_return_chapter_id
        chapter = None
        if wanted:
            _, chapter = self.find_chapter_in_book(wanted)
        if chapter is None:
            chapter = next((c for sec in snapshot.sections for c in sec.chapters), None)
        if chapter:
            self.open_chapter(chapter); self.select_tree_chapter(chapter.id)
        self.history.set_book(self.preview_live_book)
        self.history.select_version(version_id)
        self.main.sync_tool_buttons()

    def _rebind_live_editor_after_preview(self, book, preferred_chapter_id: str | None = None):
        """Reconnect only editor state to the existing live Book object.

        This intentionally does not track the book again, rebuild the live search
        index or reset the AI session. Ordinary preview exit is a read-only view
        transition and must not move any persistence/session baseline.
        """
        self.book = book
        self.chapter = None
        self.dirty = False
        self._set_book_title(book.title)
        self._rebuild_word_count_cache()
        chapter = None
        if preferred_chapter_id:
            _, chapter = self.find_chapter_in_book(preferred_chapter_id)
        if chapter is None:
            chapter = next((c for section in book.sections for c in section.chapters), None)
        if chapter is not None:
            self._set_editor_chapter(chapter)
            self.populate_tree(after=lambda cid=chapter.id: self.select_tree_chapter(cid))
        else:
            self.editor.blockSignals(True)
            self.editor.clear()
            self.editor.blockSignals(False)
            self.chapter_title.clear()
            self.populate_tree()
            self._sync_undo_redo()

    def exit_history_preview(self, *, reload_latest: bool = False):
        """Leave history preview without ever adopting the snapshot as live state.

        ``preview_live_book`` always points at the live book object captured when
        preview started; ``self.book`` may point into the archive. When requested
        (notably after a restore conflict), reload the current live manifest from
        disk before centrally adopting it so externally synced changes are shown
        immediately.
        """
        if not self.preview_live_book:
            return
        live = self.preview_live_book
        wanted = self.preview_return_chapter_id
        self.preview_live_book = None
        self.preview_version_id = None
        self.preview_return_chapter_id = None
        self.editor.setReadOnly(False)
        self.chapter_title.setReadOnly(False)
        self.tree.setDragEnabled(True)
        self.history_banner.hide()

        adopted = live
        reloaded = False
        if reload_latest:
            try:
                adopted = self.main.library.load_book(live.path)
                reloaded = True
            except Exception:
                # Never re-track a stale in-memory Book against a newer disk
                # revision: that would make the next write look safe. Keep the
                # old tracked baseline so a later save still detects the change.
                adopted = live

        if reloaded:
            self.main.adopt_active_book(adopted, wanted)
        else:
            # MainWindow already owns ``live`` as the active object. Reconnect
            # only the editor; do not move the revision baseline on ordinary
            # preview exit.
            self._rebind_live_editor_after_preview(adopted, wanted)
        self.history.set_book(adopted)
        self.history.select_version(None)
        self.main.sync_tool_buttons()

    def restore_preview_version(self):
        if not self.preview_live_book or not self.preview_version_id:
            return
        live = self.preview_live_book
        version_id = self.preview_version_id
        if not confirm(self, tr('history.restore_title', 'Versie herstellen'),
                       tr('history.restore_confirm', 'Wil je deze versie herstellen?\n\nDe huidige versie wordt eerst automatisch veiliggesteld, zodat je ook deze herstelactie later kunt terugdraaien.')):
            return
        try:
            restored = self.main.library.restore_version(live, version_id)
        except ExternalModificationError:
            # The live book changed while the user was previewing. The normal
            # editor conflict resolver must never receive this while self.book is
            # the archive snapshot. Close preview, adopt the newest live disk
            # state, and let the user explicitly retry the restore.
            self.exit_history_preview(reload_latest=True)
            QMessageBox.warning(
                self,
                tr('history.restore_changed_title', 'Versie niet hersteld'),
                tr(
                    'history.restore_changed_text',
                    'Het boek is intussen extern gewijzigd. Herstel is niet uitgevoerd en de historische versie is niet aangepast. Controleer de actuele versie en probeer daarna opnieuw.'
                ),
            )
            return
        except FuturePlanningFormatError as exc:
            self.exit_history_preview(reload_latest=False)
            QMessageBox.warning(
                self,
                tr('history.restore_future_planning_title', 'Versie niet hersteld'),
                tr(
                    'history.restore_future_planning_text',
                    'Planning is gemaakt met een nieuwere QuietWriter en is niet teruggezet. Werk QuietWriter bij voordat je deze versie herstelt.\n\n{error}',
                    error=exc,
                ),
            )
            return
        except RevisionVerificationError as exc:
            self.exit_history_preview(reload_latest=False)
            QMessageBox.warning(
                self,
                tr('history.restore_verify_title', 'Versie niet hersteld'),
                tr(
                    'history.restore_verify_text',
                    'QuietWriter kon de actuele live versie niet betrouwbaar controleren. Herstel is niet uitgevoerd. Probeer het opnieuw zodra de synchronisatie gereed is.\n\n{error}',
                    error=exc,
                ),
            )
            return
        except Exception as exc:
            QMessageBox.critical(self, tr('history.restore_title', 'Versie herstellen'), tr('history.restore_error_text', 'Herstellen is mislukt. De huidige versie is niet bewust overschreven.\n\n{error}', error=exc))
            return
        wanted = self.preview_return_chapter_id
        self.preview_live_book = None
        self.preview_version_id = None
        self.preview_return_chapter_id = None
        self.editor.setReadOnly(False)
        self.chapter_title.setReadOnly(False)
        self.tree.setDragEnabled(True)
        self.history_banner.hide()
        self.main.adopt_active_book(restored, wanted)
        self.history.set_book(restored)
        self.main.start.refresh()
        self.main.status.showMessage(tr('history.restore_success', 'De gekozen versie is hersteld.'), 4500)

    def show_history(self):
        live = self.preview_live_book or self.book
        if live:
            self.history.set_book(live)
            self.history.select_version(self.preview_version_id if self.preview_live_book else None)
        self._toggle_right_widget(self.history, self.history.list)

    def close_book(self):
        if self.preview_live_book:
            self.exit_history_preview()
        live = self.book
        if self.save() is False:
            return False
        if live is not None:
            self.main.library.untrack_book(live)
        self.book = None
        self.chapter = None
        self._chapter_corrupt = False
        self.publication_editor.set_book(None)
        self.content_stack.setCurrentWidget(self.manuscript_content)
        self._chapter_word_counts = {}
        self.dirty = False
        self._clean_text = ''
        self.tree.clear()
        self.chapter_title.clear()
        self._set_book_title('')
        self.editor.blockSignals(True); self.editor.clear(); self.editor.blockSignals(False)
        self._sync_undo_redo()
        self.right.hide()
        if hasattr(self, 'ai'): self.ai.set_book(None)
        self._set_spell_active(False)
        self.main.clear_document_status()
        return True

    def _chapters_in_scope(self):
        if not self.book or not self.chapter: return []
        scope=str(self.search.scope.currentData() or 'chapter')
        if scope=='chapter': return [self.chapter]
        if scope=='section':
            section,_=self.find_chapter_in_book(self.chapter.id); return list(section.chapters) if section else [self.chapter]
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
        if not rx:
            self._search_corrupt_skipped = []
            return []
        rows=[]
        skipped=[]
        for ch in self._chapters_in_scope():
            try:
                text=self._editor_source_text() if self.chapter and ch.id==self.chapter.id else self.main.library.read_chapter(self.book,ch)
            except UnicodeDecodeError:
                skipped.append(ch.title)
                continue
            searchable = mask_image_paths(text)
            for m in searchable_matches(text, rx):
                a=max(0,m.start()-40); b=min(len(text),m.end()+60); snippet=searchable[a:b].replace('\n',' ')
                rows.append((ch.id,ch.title,snippet,m.start(),m.end()-m.start()))
        self._search_corrupt_skipped = skipped
        return rows

    def _report_search_skips(self):
        skipped = getattr(self, '_search_corrupt_skipped', [])
        if skipped:
            count = len(skipped)
            self.main.status.showMessage(tr('editor.corrupt.skipped.one', '1 beschadigd hoofdstuk is overgeslagen. Herstel via Integriteit.') if count == 1 else tr('editor.corrupt.skipped.many', '{count} beschadigde hoofdstukken zijn overgeslagen. Herstel via Integriteit.', count=count), 5000)

    def do_search(self):
        self.search.show_results(self.collect_search_matches())
        self._report_search_skips()

    def open_search_match(self, match):
        cid,start,length=match
        if not self.chapter or self.chapter.id != cid:
            self.open_chapter_id(cid)
        # Saving/conflict handling can abort chapter navigation. Only position
        # the cursor when the requested chapter really became active.
        if not self.chapter or self.chapter.id != cid:
            return
        self.select_tree_chapter(cid)
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
        if self._chapter_corrupt:
            self.main.status.showMessage(tr('editor.corrupt_readonly', 'Beschadigd · alleen-lezen'), 3000)
            return
        if self.preview_live_book:
            self.main.status.showMessage(tr('history.read_only', 'Historische versie is alleen-lezen.'), 3000)
            return
        q=self.search.query.text()
        if not q: return
        cur=self.editor.textCursor()
        selected=cur.selectedText()
        good = selected == q if self.search.case_sensitive.isChecked() else selected.casefold()==q.casefold()
        source = self._editor_source_text()
        safe_range = is_searchable_range(source, cur.selectionStart(), cur.selectionEnd())
        if not good or not safe_range:
            self.search_next(); return
        cur.insertText(self.search.replace.text()); self.do_search()

    def replace_all_matches(self):
        if self._chapter_corrupt:
            self.main.status.showMessage(tr('editor.corrupt_readonly', 'Beschadigd · alleen-lezen'), 3000)
            return
        if self.preview_live_book:
            self.main.status.showMessage(tr('history.read_only', 'Historische versie is alleen-lezen.'), 3000)
            return
        rows=self.collect_search_matches()
        if not rows: return
        if not confirm(self, tr('editor.replace_all.title', 'Alles vervangen'), tr('editor.replace_all.confirm', 'Wil je {count} voorkomens vervangen?', count=len(rows))): return
        replacement=self.search.replace.text(); rx=self._search_regex()
        if self.save() is False:
            return
        chapters=self._chapters_in_scope()
        skipped=[]
        for ch in chapters:
            try:
                text=self._editor_source_text() if self.chapter and ch.id==self.chapter.id else self.main.library.read_chapter(self.book,ch)
            except UnicodeDecodeError:
                skipped.append(ch.title)
                continue
            changed=replace_searchable_text(text, rx, replacement)
            if changed!=text:
                if self.chapter and ch.id==self.chapter.id:
                    self.editor.blockSignals(True); self.editor.setPlainText(changed); self.editor.blockSignals(False); self.dirty=True
                else:
                    try:
                        self.main.library.save_chapter(self.book, ch, changed)
                    except (ExternalModificationError, RevisionVerificationError) as exc:
                        self._handle_concurrency_issue(exc); return
                self._chapter_word_counts[ch.id] = count_words(changed)
        if self.save() is False:
            return
        self.main.search_index.rebuild_book(self.book); self.do_search(); self.update_counts(saved=True)
        if skipped:
            count=len(skipped)
            self.main.status.showMessage(tr('editor.corrupt.replace_skipped.one', '1 beschadigd hoofdstuk is overgeslagen bij vervangen. Herstel via Integriteit.') if count == 1 else tr('editor.corrupt.replace_skipped.many', '{count} beschadigde hoofdstukken zijn overgeslagen bij vervangen. Herstel via Integriteit.', count=count), 5000)


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

    def _set_book_title(self, title: str):
        self._book_title_full = str(title or '')
        self.book_title_label.setToolTip(self._book_title_full)
        self._update_book_title_elision()

    def _update_book_title_elision(self):
        if not hasattr(self, 'book_title_label'):
            return
        # The title is presentation only and may never determine the minimum
        # window width. Keep enough room for the editor controls/right panel.
        available = max(80, min(360, self.width() // 4))
        self.book_title_label.setMaximumWidth(available)
        self.book_title_label.setText(
            self.book_title_label.fontMetrics().elidedText(
                self._book_title_full, Qt.ElideRight, available
            )
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_book_title_elision()
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
            self.contents_edge_button.setAccessibleName(self.contents_edge_button.toolTip())
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

    def _close_right_panel_from_keyboard(self):
        if not self.right.isVisible():
            return
        widget = self.right.currentWidget()
        self._remember_panel_widths()
        self.right.hide()
        if widget is self.spell:
            self._set_spell_active(False)
        self.main.sync_tool_buttons()
        button_name = {
            self.search: 'search_button',
            self.chapter_context: 'chapter_context_button',
            self.ai: 'ai_button',
            self.spell: 'spell_button',
            self.insert: 'insert_button',
            self.history: 'history_button',
        }.get(widget)
        button = getattr(self.main, button_name, None) if button_name else None
        if button is not None and button.isVisible():
            button.setFocus()

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
            if widget is self.spell:
                self.spell.focus_first_control()
            else:
                focus_widget.setFocus()
        self.main.sync_tool_buttons()

    def chapter_context_available(self):
        return bool(
            self.book is not None
            and self.chapter is not None
            and not self.preview_live_book
            and not self._chapter_corrupt
            and self.content_stack.currentWidget() is self.manuscript_content
        )

    def refresh_chapter_context(self):
        available = self.chapter_context_available()
        self.chapter_context.refresh(
            self.book if available else None,
            self.chapter.id if available and self.chapter else None,
            available=available,
        )
        if not available and self.right.isVisible() and self.right.currentWidget() is self.chapter_context:
            self._remember_panel_widths()
            self.right.hide()
        if hasattr(self.ai, 'refresh_context_summary'):
            self.ai.refresh_context_summary()
        if hasattr(self.main, 'sync_tool_buttons'):
            self.main.sync_tool_buttons()

    def _open_planning_from_context(self):
        self.main.show_planning()

    def show_chapter_context(self):
        if not self.chapter_context_available():
            return
        self.refresh_chapter_context()
        self._toggle_right_widget(self.chapter_context, self.chapter_context.open_button)

    def show_search(self):
        self._toggle_right_widget(self.search, self.search.query)

    def show_ai(self):
        if not self.main.settings.value('ai_enabled', True, bool):
            return
        self.ai.refresh_quick_actions()
        self._toggle_right_widget(self.ai, self.ai.input)
        self.ai.ensure_warmup()

    def show_spell(self):
        opening = not (self.right.isVisible() and self.right.currentWidget() is self.spell)
        if opening:
            self.spell.refresh()
        self._toggle_right_widget(self.spell, self.spell.suggestions)
