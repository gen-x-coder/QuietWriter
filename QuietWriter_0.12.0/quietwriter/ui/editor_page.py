
from pathlib import Path
from datetime import datetime
import copy
import re

from PySide6.QtCore import Qt, QSettings, QTimer, QSize, QPoint
from PySide6.QtGui import QColor, QFont, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QInputDialog,
    QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QSplitter,
    QStackedWidget, QTreeWidgetItem, QVBoxLayout, QWidget
)

from ..ai.ui import AIPanel
from ..chapter_order import DropTarget, move_chapter as reorder_chapter
from ..dictionary_catalog import DictionaryCatalog
from ..i18n import tr
from ..icon_theme import icon
from ..markdown_io import insert_scene_break as build_scene_break_text
from ..spellcheck import WordDictionary, SpellHighlighter
from ..themes import THEMES
from ..typography import WritingTypography
from .dialogs import confirm
from .history_panel import HistoryPanel
from .manuscript_editor import ManuscriptEditor
from .manuscript_tree import ManuscriptTree
from .search_panel import SearchPanel
from .spell_panel import SpellPanel

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
                    it = QTreeWidgetItem([chapter.title, '']); it.setData(0, Qt.UserRole, ('chapter', chapter.id)); it.setIcon(1, icon('drag_handle')); it.setTextAlignment(1, Qt.AlignCenter); it.setToolTip(1, tr('editor.drag_chapter', 'Sleep om hoofdstuk te verplaatsen')); self.tree.addTopLevelItem(it)
            else:
                sit = QTreeWidgetItem([section.title, '']); sit.setData(0, Qt.UserRole, ('section', section.id)); sit.setFlags(sit.flags() & ~Qt.ItemIsDragEnabled)
                section_font = QFont(QApplication.font()); section_font.setWeight(QFont.Weight.DemiBold); sit.setFont(0, section_font)
                sit.setForeground(0, QColor(THEMES.get(str(self.main.settings.value('theme','Helder')), THEMES['Helder'])['muted']))
                self.tree.addTopLevelItem(sit)
                for chapter in section.chapters:
                    cit = QTreeWidgetItem([chapter.title, '']); cit.setData(0, Qt.UserRole, ('chapter', chapter.id)); cit.setIcon(1, icon('drag_handle')); cit.setTextAlignment(1, Qt.AlignCenter); cit.setToolTip(1, tr('editor.drag_chapter', 'Sleep om hoofdstuk te verplaatsen')); sit.addChild(cit)
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
                        from ..storage import Section
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
        # setPlainText() creates a fresh QTextDocument character stream. Reapply
        # the saved writing typography so the selected font is correct immediately
        # after startup/opening a book, not only after visiting Settings.
        self.editor.apply_typography(WritingTypography.from_settings(self.main.settings))
        self.editor.apply_scene_break_formatting()
        self.dirty = False; self.autosave_status.setText('● Opgeslagen'); self.update_counts(); self.main.sync_tool_buttons()
        if self.right.isVisible() and self.right.currentWidget() is self.spell:
            self.spell.refresh()

    def on_text_changed(self):
        if self.preview_live_book:
            return
        self.dirty = True; self.autosave_status.setText('Niet opgeslagen')
        self.editor.apply_scene_break_formatting(); self.update_counts()
        if self.main.settings.value('autosave', True, bool): self.autosave_timer.start()

    def save(self):
        if self.preview_live_book:
            return
        if self.book and self.chapter and self.dirty:
            self.main.library.save_chapter(self.book, self.chapter, self.editor.toPlainText()); self.dirty = False
            self.main.search_index.rebuild_book(self.book); self.autosave_status.setText('● Opgeslagen · zojuist'); self.update_counts(saved=True)

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
        chapter_index = 0; chapter_total = 0
        if self.book:
            flat = [c for sec in self.book.sections for c in sec.chapters]
            chapter_total = len(flat)
            if self.chapter:
                chapter_index = next((i+1 for i,c in enumerate(flat) if c.id == self.chapter.id), 0)
        prefix = f'Hoofdstuk {chapter_index} van {chapter_total} · ' if chapter_total else ''
        self.main.status.showMessage(prefix + f'{words:,}'.replace(',', '.') + ' woorden')

    def add_menu(self):
        """Toon een rustige flyout voor Hoofdstuk of Sectie.

        Qt.Popup sluit automatisch wanneer de gebruiker ergens buiten de flyout klikt.
        Daarmee is een aparte Annuleren-knop niet nodig.
        """
        if not self.book or self.preview_live_book:
            return
        if hasattr(self, '_add_flyout') and self._add_flyout:
            self._add_flyout.close()
        popup = QFrame(None, Qt.Popup | Qt.FramelessWindowHint)
        popup.setObjectName('flyout')
        popup.setAttribute(Qt.WA_DeleteOnClose, True)
        lay = QVBoxLayout(popup); lay.setContentsMargins(8,8,8,8); lay.setSpacing(4)
        title = QLabel(tr('editor.add_what', 'Toevoegen')); title.setObjectName('sectionTitle'); lay.addWidget(title)
        chapter_btn = QPushButton(tr('editor.new_chapter', 'Hoofdstuk')); chapter_btn.setObjectName('flyoutButton')
        section_btn = QPushButton(tr('editor.new_section', 'Sectie')); section_btn.setObjectName('flyoutButton')
        lay.addWidget(chapter_btn); lay.addWidget(section_btn)
        shadow = QGraphicsDropShadowEffect(popup); shadow.setBlurRadius(24); shadow.setOffset(0, 7); shadow.setColor(QColor(0,0,0,70)); popup.setGraphicsEffect(shadow)
        chapter_btn.clicked.connect(lambda: (popup.close(), self._create_chapter()))
        section_btn.clicked.connect(lambda: (popup.close(), self._create_section()))
        popup.adjustSize()
        pos = self.add_content_button.mapToGlobal(QPoint(self.add_content_button.width() - popup.sizeHint().width(), self.add_content_button.height() + 6))
        popup.move(pos); popup.show(); popup.raise_()
        self._add_flyout = popup

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
                sec, _ = self.find_chapter(data[1]); insert_after = sec.id if sec else None
        self.main.library.add_section(self.book, title or tr('editor.new_section', 'Nieuwe sectie'), after_section_id=insert_after)
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
                found, _ = self.find_chapter(data[1])
                if found:
                    section = found
        title, ok = QInputDialog.getText(self, tr('editor.new_chapter', 'Nieuw hoofdstuk'), tr('editor.title', 'Titel:'))
        if not ok:
            return
        c = self.main.library.add_chapter(self.book, section, title or tr('editor.new_chapter', 'Nieuw hoofdstuk'))
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
