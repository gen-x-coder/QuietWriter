
from pathlib import Path
from datetime import datetime
import copy
import json
import re

from PySide6.QtCore import Qt, QSettings, QTimer, QSize, QPoint
from PySide6.QtGui import QColor, QFont, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QInputDialog,
    QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QSplitter,
    QTreeWidgetItem, QVBoxLayout, QWidget
)

from .current_page_stack import CurrentPageStack
from ..ai.ui import AIPanel
from ..chapter_order import DropTarget, move_chapter as reorder_chapter
from ..dictionary_catalog import DictionaryCatalog
from ..i18n import tr
from ..icon_theme import icon
from ..markdown_io import insert_scene_break as build_scene_break_text
from ..revisions import ExternalModificationError, RevisionVerificationError
from ..publication_models import FRONT_MATTER, BACK_MATTER, item_definition
from ..publication_storage import PublicationStore
from ..spell_engine import WordDictionary
from ..storage import Chapter, Section
from ..themes import THEMES
from ..typography import WritingTypography
from .dialogs import confirm
from .history_panel import HistoryPanel
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
        self.book = None; self.chapter = None; self.dirty = False
        self._chapter_word_counts = {}
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
        self.highlighter = self.editor.presentation_highlighter
        self.highlighter.set_dictionary(self.dictionary)
        self.load_dictionary_from_settings()
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
        previous = self.book
        if self.save() is False:
            return False
        if previous is not None and previous.id != book.id:
            self.main.library.untrack_book(previous)
        self.book = book; self.chapter = None
        self.main.library.track_book(book)
        self.publication_editor.set_book(book)
        self.book_title_label.setText(book.title); self.populate_tree()
        self._rebuild_word_count_cache()
        first = next((c for s in book.sections for c in s.chapters), None)
        if first: self.open_chapter(first)
        self.main.search_index.rebuild_book(book)
        if hasattr(self, 'history'): self.history.set_book(book)
        if hasattr(self, 'ai'): self.ai.set_book(book)
        return True

    def populate_tree(self):
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
            item = QTreeWidgetItem([label, 'wijzig' if editable else ''])
            item.setData(0, Qt.UserRole, ('manuscript_group', kind))
            item.setFlags(item.flags() & ~Qt.ItemIsDragEnabled)
            font = QFont(QApplication.font()); font.setWeight(QFont.Weight.DemiBold); item.setFont(0, font)
            item.setBackground(0, QColor(theme['panel2'])); item.setBackground(1, QColor(theme['panel2']))
            item.setForeground(0, QColor(theme['text']))
            if editable:
                item.setForeground(1, QColor(theme['accent']))
                item.setTextAlignment(1, Qt.AlignCenter)
                item.setToolTip(1, 'Publicatiestructuur wijzigen')
            # Keep the disclosure arrow visible even when Voorwerk/Achterwerk
            # currently contain no enabled items. These three zones are a stable
            # part of the manuscript structure, not something that appears only
            # after publication options have been selected.
            item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
            self.tree.addTopLevelItem(item)
            item.setExpanded(True)
            return item

        front_group = make_group('Voorwerk', 'front', editable=True)
        for key, text, _kind in FRONT_MATTER:
            if key in enabled:
                item = QTreeWidgetItem([text, ''])
                item.setData(0, Qt.UserRole, ('publication', key))
                item.setFlags(item.flags() & ~Qt.ItemIsDragEnabled)
                front_group.addChild(item)

        body_group = make_group('Boek', 'body')
        add_body(body_group)

        back_group = make_group('Achterwerk', 'back', editable=True)
        for key, text, _kind in BACK_MATTER:
            if key in enabled:
                item = QTreeWidgetItem([text, ''])
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
        try:
            writer(self.book)
            return 'mine'
        except RevisionVerificationError:
            QMessageBox.warning(self, 'Opslaan tijdelijk niet mogelijk', 'QuietWriter kan de actuele bestanden tijdelijk niet betrouwbaar controleren. Er is niets overschreven. Probeer het zo opnieuw.')
            return 'failed'
        except ExternalModificationError as exc:
            changed='\n'.join('• '+name for name in exc.changed_files[:6])
            box=QMessageBox(self); box.setIcon(QMessageBox.Warning); box.setWindowTitle('Boek extern gewijzigd'); box.setText('Dit boek is buiten QuietWriter gewijzigd.')
            box.setInformativeText('QuietWriter heeft het publicatieonderdeel niet overschreven.\n\nGewijzigd:\n'+changed+'\n\nWelke versie wil je gebruiken? Beide keuzes maken eerst automatisch een herstelversie.')
            mine=box.addButton('Mijn versie gebruiken',QMessageBox.AcceptRole); disk=box.addButton('Versie op schijf gebruiken',QMessageBox.DestructiveRole); box.setDefaultButton(disk); box.exec()
            if box.clickedButton() not in (mine,disk):
                return 'failed'
            old_book=self.book
            try:
                if box.clickedButton() is mine:
                    self.main.library.create_version(old_book,kind='conflict_external')
                    latest=self.main.library.load_book(old_book.path); self.main.library.track_book(latest); self.book=latest
                    writer(latest)
                    result='mine'
                else:
                    self.main.library.create_version_with_file_overrides(old_book,{relative_path:local_text},kind='conflict_local')
                    latest=self.main.library.load_book(old_book.path); self.main.library.track_book(latest); self.book=latest
                    result='disk'
                self.publication_editor.book=self.book
                self.publication_editor.data=self.publication_store.load(self.book)
                self.populate_tree()
                self.history.set_book(self.book); self.ai.set_book(self.book)
                return result
            except Exception as error:
                QMessageBox.critical(self,'Conflict niet opgelost',f'Er is niets bewust overschreven.\n\n{error}')
                return 'failed'
        except Exception as exc:
            QMessageBox.critical(self,'Publicatieonderdeel opslaan',f'Opslaan is mislukt.\n\n{exc}')
            return 'failed'

    def _set_publication_context(self):
        self.chapter = None
        self.autosave_timer.stop()
        self.right.hide()
        if hasattr(self.main, 'toolrail'):
            self.main.toolrail.hide()
        self.autosave_status.setText('')
        self.main.status.clearMessage()

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
        except (ExternalModificationError, RevisionVerificationError) as exc:
            self._handle_concurrency_issue(exc)
            self.populate_tree(); self.select_tree_chapter(chapter_id); return
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
            _, chapter = self.find_chapter_in_book(chapter_id)
            if not chapter:
                return
            rename_action = menu.addAction('Hernoemen…')
            duplicate_action = menu.addAction('Dupliceren')
            chosen = menu.exec(self.tree.viewport().mapToGlobal(pos))

            if chosen is rename_action:
                title, ok = QInputDialog.getText(self, 'Hoofdstuk hernoemen', 'Titel:', text=chapter.title)
                if ok and title.strip():
                    try:
                        self.main.library.rename_chapter(self.book, chapter_id, title)
                    except (ExternalModificationError, RevisionVerificationError) as exc:
                        self._handle_concurrency_issue(exc); return
                    if self.chapter and self.chapter.id == chapter_id:
                        self.chapter_title.setText(title.strip())
                    self.populate_tree(); self.select_tree_chapter(chapter_id)
            elif chosen is duplicate_action:
                if self.save() is False:
                    return
                try:
                    copied = self.main.library.duplicate_chapter(self.book, chapter_id)
                except (ExternalModificationError, RevisionVerificationError) as exc:
                    self._handle_concurrency_issue(exc); return
                self.populate_tree()
                if copied:
                    self._chapter_word_counts[copied.id] = self._chapter_word_counts.get(chapter_id, len(self.main.library.read_chapter(self.book, copied).split()))
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
                    try:
                        self.main.library.rename_section(self.book, section_id, title)
                    except (ExternalModificationError, RevisionVerificationError) as exc:
                        self._handle_concurrency_issue(exc); return
                    self.populate_tree()
            elif chosen is delete_action:
                if sec.chapters:
                    QMessageBox.information(self, 'Sectie verwijderen', 'Verplaats eerst de hoofdstukken uit deze sectie. Een niet-lege sectie wordt niet verwijderd.')
                    return
                if confirm(self, 'Sectie verwijderen', f'Wil je de sectie “{sec.title}” verwijderen?'):
                    previous_sections = self.book.sections
                    self.book.sections = [x for x in self.book.sections if x.id != sec.id]
                    if not self.book.sections:
                        self.book.sections = [Section(id='root', title='Manuscript')]
                    try:
                        self.main.library.save_manifest(self.book)
                    except (ExternalModificationError, RevisionVerificationError) as exc:
                        self.book.sections = previous_sections
                        self._handle_concurrency_issue(exc); return
                    self.populate_tree()

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
        if self.save() is False:
            return
        try:
            self.main.library.create_version(self.book, kind='chapter_delete')
            removed = self.main.library.delete_chapter(self.book, chapter.id)
        except (ExternalModificationError, RevisionVerificationError) as exc:
            self._handle_concurrency_issue(exc); return
        except Exception as exc:
            QMessageBox.critical(self, 'Hoofdstuk verwijderen', f'Verwijderen is mislukt.\n\n{exc}')
            return
        if not removed:
            QMessageBox.warning(self, 'Hoofdstuk verwijderen', 'Het hoofdstuk kon niet worden verwijderd.')
            return
        self._chapter_word_counts.pop(chapter.id, None)
        self.chapter = None; self.dirty = False
        self.populate_tree()
        if next_chapter:
            _, existing = self.find_chapter_in_book(next_chapter.id)
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

    def open_chapter_id(self, cid):
        _, c = self.find_chapter_in_book(cid)
        if c: self.open_chapter(c)

    def _set_editor_chapter(self, chapter):
        self.content_stack.setCurrentWidget(self.manuscript_content)
        self.chapter = chapter
        self.chapter_title.setText(chapter.title)
        self.editor.blockSignals(True)
        self.editor.setPlainText(self.main.library.read_chapter(self.book, chapter))
        self.editor.blockSignals(False)
        self.editor.apply_typography(WritingTypography.from_settings(self.main.settings))
        self.editor.apply_scene_break_formatting()
        self.dirty = False
        self.autosave_status.setText('● Opgeslagen')
        self.update_counts()
        if hasattr(self.main, 'toolrail') and self.main.stack.currentWidget() is self:
            self.main.toolrail.show()
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

    def on_text_changed(self):
        if self.preview_live_book:
            return
        self.dirty = True; self.autosave_status.setText('Niet opgeslagen')
        self.editor.schedule_formatting(); self.update_counts()
        if self.main.settings.value('autosave', True, bool): self.autosave_timer.start()

    def _adopt_disk_book(self, preferred_chapter_id: str | None = None):
        latest = self.main.library.load_book(self.book.path)
        self.main.library.track_book(latest)
        self.book = latest
        self.book_title_label.setText(latest.title)
        self.populate_tree()
        self._rebuild_word_count_cache()
        chapter = None
        if preferred_chapter_id:
            _, chapter = self.find_chapter_in_book(preferred_chapter_id)
        if chapter is None:
            chapter = next((c for section in latest.sections for c in section.chapters), None)
        if chapter:
            self._set_editor_chapter(chapter)
            self.select_tree_chapter(chapter.id)
        else:
            self.chapter = None
            self.editor.clear(); self.chapter_title.clear(); self.dirty = False
        self.history.set_book(latest)
        self.ai.set_book(latest)
        self.main.search_index.rebuild_book(latest)
        return latest, chapter

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
        self.autosave_timer.stop()
        if not self.book or not self.chapter:
            return False
        old_book = self.book
        old_chapter = self.chapter
        chapter_id = old_chapter.id
        local_text = self.editor.toPlainText()
        changed = '\n'.join(f'• {name}' for name in exc.changed_files[:6])
        if len(exc.changed_files) > 6:
            changed += f'\n• … en {len(exc.changed_files) - 6} meer'

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle('Boek extern gewijzigd')
        box.setText('Dit boek is buiten QuietWriter gewijzigd.')
        box.setInformativeText(
            'QuietWriter heeft niet opgeslagen om te voorkomen dat een andere versie wordt overschreven.\n\n'
            f'Gewijzigd:\n{changed}\n\n'
            'Welke versie wil je als uitgangspunt gebruiken? Beide keuzes maken eerst automatisch een herstelversie.'
        )
        use_mine = box.addButton('Mijn versie gebruiken', QMessageBox.AcceptRole)
        use_disk = box.addButton('Versie op schijf gebruiken', QMessageBox.DestructiveRole)
        box.setDefaultButton(use_disk)
        box.exec()
        clicked = box.clickedButton()
        if clicked not in (use_mine, use_disk):
            self.autosave_status.setText('⚠ Extern gewijzigd · niet opgeslagen')
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
                self.autosave_status.setText('● Eigen versie bewaard')
            else:
                # Preserve the in-memory manuscript structure and current editor
                # text in History before discarding them in favour of disk.
                self.main.library.create_version_from_state(
                    old_book, {old_chapter.file: local_text}, kind='conflict_local'
                )
                self._adopt_disk_book(chapter_id)
                self.autosave_status.setText('● Versie op schijf geladen')
            return True
        except ExternalModificationError:
            # The disk changed again while the user was deciding. Never bypass
            # the guard; leave local text in the editor and let the user retry.
            self.book = old_book; self.chapter = old_chapter
            self.editor.blockSignals(True); self.editor.setPlainText(local_text); self.editor.blockSignals(False)
            self.dirty = True
            self.autosave_status.setText('⚠ Opnieuw extern gewijzigd')
            QMessageBox.warning(self, 'Boek opnieuw gewijzigd', 'Het boek veranderde opnieuw tijdens het oplossen van het conflict. Er is niets overschreven. Probeer opnieuw nadat de synchronisatie klaar is.')
            return False
        except Exception as error:
            self.book = old_book; self.chapter = old_chapter
            self.editor.blockSignals(True); self.editor.setPlainText(local_text); self.editor.blockSignals(False)
            self.dirty = True
            self.autosave_status.setText('⚠ Conflict niet opgelost')
            QMessageBox.critical(self, 'Conflict niet opgelost', f'De herstelactie is mislukt. Er is niet verder opgeslagen.\n\n{error}')
            return False

    def _handle_verification_error(self, exc: RevisionVerificationError) -> bool:
        self.autosave_status.setText('Opslaan tijdelijk niet mogelijk')
        self.dirty = True
        # Sync software can briefly lock/on-demand hydrate a file. This is not a
        # content conflict. Keep the text in memory and quietly retry autosave.
        if self.main.settings.value('autosave', True, bool):
            self.autosave_timer.start(1800)
        return False

    def save(self):
        if self.preview_live_book:
            return True
        if self.content_stack.currentWidget() is self.publication_editor:
            return self.publication_editor.save_pending()
        if self.content_stack.currentWidget() is self.publication_setup:
            return True
        if not (self.book and self.chapter and self.dirty):
            return True
        try:
            self.main.library.save_chapter(self.book, self.chapter, self.editor.toPlainText())
        except ExternalModificationError as exc:
            return self._resolve_external_change(exc)
        except RevisionVerificationError as exc:
            return self._handle_verification_error(exc)
        self.dirty = False
        self.main.search_index.rebuild_book(self.book)
        self.autosave_status.setText('● Opgeslagen · zojuist')
        self.update_counts(saved=True)
        return True

    def _handle_concurrency_issue(self, exc) -> bool:
        if isinstance(exc, ExternalModificationError):
            return self._resolve_external_change(exc)
        if isinstance(exc, RevisionVerificationError):
            return self._handle_verification_error(exc)
        raise exc

    def rename_current(self):
        if self.preview_live_book:
            return
        if self.chapter:
            old_title = self.chapter.title
            self.chapter.title = self.chapter_title.text().strip() or 'Nieuw hoofdstuk'
            try:
                self.main.library.save_manifest(self.book)
            except (ExternalModificationError, RevisionVerificationError) as exc:
                self.chapter.title = old_title
                self._handle_concurrency_issue(exc)
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
                    self._chapter_word_counts[chapter.id] = len(text.split())
                except Exception:
                    self._chapter_word_counts[chapter.id] = 0

    def _ensure_word_count_cache(self):
        ids = self._book_chapter_ids()
        if ids != set(self._chapter_word_counts):
            self._rebuild_word_count_cache()

    def update_counts(self, saved=False):
        txt = self.editor.toPlainText()
        words = len(txt.split())
        self._ensure_word_count_cache()
        if self.chapter:
            self._chapter_word_counts[self.chapter.id] = words
        total = sum(self._chapter_word_counts.values()) if self.book else 0
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
        publication_btn = QPushButton('Publicatiestructuur'); publication_btn.setObjectName('flyoutButton')
        lay.addWidget(chapter_btn); lay.addWidget(section_btn); lay.addWidget(publication_btn)
        shadow = QGraphicsDropShadowEffect(popup); shadow.setBlurRadius(24); shadow.setOffset(0, 7); shadow.setColor(QColor(0,0,0,70)); popup.setGraphicsEffect(shadow)
        chapter_btn.clicked.connect(lambda: (popup.close(), self._create_chapter()))
        section_btn.clicked.connect(lambda: (popup.close(), self._create_section()))
        publication_btn.clicked.connect(lambda: (popup.close(), self.show_publication_setup()))
        popup.adjustSize()
        pos = self.add_content_button.mapToGlobal(QPoint(self.add_content_button.width() - popup.sizeHint().width(), self.add_content_button.height() + 6))
        popup.move(pos); popup.show(); popup.raise_()

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
                sec, _ = self.find_chapter_in_book(data[1]); insert_after = sec.id if sec else None
        try:
            self.main.library.add_section(self.book, title or tr('editor.new_section', 'Nieuwe sectie'), after_section_id=insert_after)
        except (ExternalModificationError, RevisionVerificationError) as exc:
            self._handle_concurrency_issue(exc); return
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
        title, ok = QInputDialog.getText(self, tr('editor.new_chapter', 'Nieuw hoofdstuk'), tr('editor.title', 'Titel:'))
        if not ok:
            return
        try:
            c = self.main.library.add_chapter(self.book, section, title or tr('editor.new_chapter', 'Nieuw hoofdstuk'))
        except (ExternalModificationError, RevisionVerificationError) as exc:
            self._handle_concurrency_issue(exc); return
        self._chapter_word_counts[c.id] = 0
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
        if self.save() is False:
            return
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
            if self.save() is False:
                return
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
        self._rebuild_word_count_cache()
        self.chapter = None; self.dirty = False
        self.book_title_label.setText(snapshot.title)
        self.editor.setReadOnly(True); self.chapter_title.setReadOnly(True); self.tree.setDragEnabled(False)
        self.history_banner_label.setText('Historische versie · ' + self._history_label(row or {'created_at': ''}))
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

    def exit_history_preview(self):
        if not self.preview_live_book:
            return
        live = self.preview_live_book
        wanted = self.preview_return_chapter_id
        self.preview_live_book = None; self.preview_version_id = None; self.preview_return_chapter_id = None
        self.book = live; self._rebuild_word_count_cache(); self.chapter = None; self.dirty = False
        self.editor.setReadOnly(False); self.chapter_title.setReadOnly(False); self.tree.setDragEnabled(True)
        self.history_banner.hide(); self.book_title_label.setText(live.title); self.populate_tree()
        chapter = None
        if wanted:
            _, chapter = self.find_chapter_in_book(wanted)
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
        except (ExternalModificationError, RevisionVerificationError) as exc:
            self._handle_concurrency_issue(exc); return
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
        live = self.book
        if self.save() is False:
            return False
        if live is not None:
            self.main.library.untrack_book(live)
        self.book = None
        self.chapter = None
        self.publication_editor.set_book(None)
        self.content_stack.setCurrentWidget(self.manuscript_content)
        self._chapter_word_counts = {}
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
        return True

    def _chapters_in_scope(self):
        if not self.book or not self.chapter: return []
        scope=self.search.scope.currentText()
        if scope=='Huidig hoofdstuk': return [self.chapter]
        if scope=='Huidige sectie':
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
        if self.save() is False:
            return
        chapters=self._chapters_in_scope()
        for ch in chapters:
            text=self.editor.toPlainText() if self.chapter and ch.id==self.chapter.id else self.main.library.read_chapter(self.book,ch)
            changed=rx.sub(lambda m: replacement,text)
            if changed!=text:
                if self.chapter and ch.id==self.chapter.id:
                    self.editor.blockSignals(True); self.editor.setPlainText(changed); self.editor.blockSignals(False); self.dirty=True
                else:
                    try:
                        self.main.library.save_chapter(self.book, ch, changed)
                    except (ExternalModificationError, RevisionVerificationError) as exc:
                        self._handle_concurrency_issue(exc); return
                self._chapter_word_counts[ch.id] = len(changed.split())
        if self.save() is False:
            return
        self.main.search_index.rebuild_book(self.book); self.do_search(); self.update_counts(saved=True)


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
