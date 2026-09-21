from __future__ import annotations
import os
import sys
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QSettings, QTimer, QSize
from PySide6.QtGui import QAction, QFont, QIcon, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QFrame, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QSplitter, QStackedWidget, QStatusBar,
    QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
)

from . import APP_NAME
from .storage import Library
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


class StartPage(QWidget):
    open_book = __import__('PySide6.QtCore').QtCore.Signal(object)
    new_book = __import__('PySide6.QtCore').QtCore.Signal()

    def __init__(self, library):
        super().__init__()
        self.library = library
        outer = QVBoxLayout(self)
        outer.setContentsMargins(42, 36, 42, 36)
        row = QHBoxLayout()
        title = QLabel('Boeken')
        title.setObjectName('title')
        new = QPushButton('+ Nieuw boek')
        new.clicked.connect(self.new_book.emit)
        row.addWidget(title)
        row.addStretch()
        row.addWidget(new)
        outer.addLayout(row)
        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self._open)
        outer.addWidget(self.list)
        self.refresh()

    def refresh(self):
        self.list.clear()
        for book in self.library.list_books():
            item = QListWidgetItem(book.title)
            item.setData(Qt.UserRole, str(book.path))
            self.list.addItem(item)

    def _open(self, item):
        self.open_book.emit(self.library.load_book(Path(item.data(Qt.UserRole))))


class PersonaPage(QWidget):
    def __init__(self, library):
        super().__init__()
        self.library = library
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 30, 36, 30)
        title = QLabel('Schrijverspersona')
        title.setObjectName('title')
        info = QLabel('Deze persona wordt automatisch aan iedere AI-opdracht toegevoegd.')
        info.setObjectName('muted')
        self.edit = QTextEdit()
        self.edit.setPlainText(library.read_persona())
        save = QPushButton('Opslaan')
        save.clicked.connect(self.save)
        lay.addWidget(title)
        lay.addWidget(info)
        lay.addSpacing(12)
        lay.addWidget(self.edit)
        lay.addWidget(save, 0, Qt.AlignRight)

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
        form.addRow('Programmataal', self.language)
        form.addRow('Kleurenschema', self.theme)
        form.addRow('Automatisch opslaan', self.autosave)
        form.addRow('Werkmap / Dropbox-map', box)
        form.addRow('Ollama-adres', self.ollama)
        form.addRow('Schrijf- en analysemodel', modelbox)
        form.addRow('Snel achtergrondmodel', self.fast_model)
        root.addLayout(form)
        note = QLabel('OpenRouter is voorbereid in de architectuur, maar nog niet actief in deze versie.')
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
        super().accept()


class SearchPanel(QWidget):
    open_chapter = __import__('PySide6.QtCore').QtCore.Signal(str)
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(18,18,18,18)
        lab = QLabel('Zoeken'); lab.setObjectName('sectionTitle')
        self.query = QLineEdit(); self.query.setPlaceholderText('Zoek in dit boek…')
        self.only_chapter = QCheckBox('Alleen huidig hoofdstuk')
        self.results = QListWidget()
        self.results.itemActivated.connect(lambda i: self.open_chapter.emit(i.data(Qt.UserRole)))
        lay.addWidget(lab); lay.addWidget(self.query); lay.addWidget(self.only_chapter); lay.addWidget(self.results)

    def show_results(self, rows):
        self.results.clear()
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
        head = QHBoxLayout(); title = QLabel('Manuscript'); title.setObjectName('sectionTitle'); add = QPushButton('+ Add'); add.clicked.connect(self.add_menu)
        head.addWidget(title); head.addStretch(); head.addWidget(add)
        self.tree = QTreeWidget(); self.tree.setHeaderHidden(True); self.tree.itemClicked.connect(self.tree_clicked)
        ml.addLayout(head); ml.addWidget(self.tree)

        self.center = QWidget(); cl = QVBoxLayout(self.center); cl.setContentsMargins(0,0,0,0)
        self.chapter_title = QLineEdit(); self.chapter_title.setPlaceholderText('Hoofdstuktitel'); self.chapter_title.setAlignment(Qt.AlignCenter); self.chapter_title.setStyleSheet('font-size:24px; font-weight:600; border:0; padding:24px 44px 12px 44px;')
        self.chapter_title.editingFinished.connect(self.rename_current)
        self.editor = ManuscriptEditor(); self.editor.setObjectName('editor'); self.editor.textChanged.connect(self.on_text_changed)
        self.dictionary = WordDictionary(); self.highlighter = SpellHighlighter(self.editor.document(), self.dictionary)
        cl.addWidget(self.chapter_title); cl.addWidget(self.editor)

        self.right = QStackedWidget(); self.right.setObjectName('panel'); self.right.setMinimumWidth(280)
        self.search = SearchPanel(); self.ai = AIPanel(main)
        self.right.addWidget(self.search); self.right.addWidget(self.ai)
        self.search.query.textChanged.connect(self.do_search); self.search.only_chapter.stateChanged.connect(lambda _: self.do_search(self.search.query.text())); self.search.open_chapter.connect(self.open_chapter_id)

        self.left_split.addWidget(self.manuscript); self.left_split.addWidget(self.center); self.left_split.addWidget(self.right)
        self.left_split.setStretchFactor(0,0); self.left_split.setStretchFactor(1,1); self.left_split.setStretchFactor(2,0)
        self.left_split.setSizes([280, 800, 360])
        root.addWidget(self.left_split)

    def load_book(self, book):
        self.save(); self.book = book; self.chapter = None; self.populate_tree()
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
        self.main.status.showMessage(f'{words:,} woorden' + (f' · Opgeslagen {datetime.now():%H:%M}' if saved else ''))

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
        self.editor.blockSignals(True); self.editor.clear(); self.editor.blockSignals(False)
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

        wrap = QWidget(); self.setCentralWidget(wrap); root = QHBoxLayout(wrap); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.rail = QFrame(); self.rail.setObjectName('toolrail'); self.rail.setFixedWidth(58); rl=QVBoxLayout(self.rail); rl.setContentsMargins(7,10,7,10); rl.setSpacing(6)
        self.stack = QStackedWidget()
        self.start = StartPage(library); self.persona = PersonaPage(library); self.editor_page = EditorPage(self)
        self.stack.addWidget(self.start); self.stack.addWidget(self.editor_page); self.stack.addWidget(self.persona)
        root.addWidget(self.rail); root.addWidget(self.stack)

        def rb(icon_name, tip, fn):
            b=QPushButton(); b.setObjectName('railButton'); b.setIcon(icon(icon_name)); b.setIconSize(QSize(24,24)); b.setFixedSize(44,44); b.setToolTip(tip); b.clicked.connect(fn); rl.addWidget(b); return b
        self.home_button = rb('books','Boeken / boek sluiten', self.go_home)
        self.write_button = rb('edit','Schrijven', self.show_editor)
        self.persona_button = rb('persona','Persona', lambda: self.stack.setCurrentWidget(self.persona))
        rl.addStretch()
        self.settings_button = rb('settings','Instellingen', self.open_settings)
        self.start.open_book.connect(self.open_book); self.start.new_book.connect(self.new_book)

        # rechter gereedschapsrail wanneer editor actief
        self.toolrail = QFrame(); self.toolrail.setObjectName('toolrail'); self.toolrail.setFixedWidth(58); tr=QVBoxLayout(self.toolrail); tr.setContentsMargins(7,10,7,10); tr.setSpacing(6)
        def trb(icon_name, tip, fn):
            b=QPushButton(); b.setObjectName('railButton'); b.setIcon(icon(icon_name)); b.setIconSize(QSize(24,24)); b.setFixedSize(44,44); b.setToolTip(tip); b.setCheckable(True); b.clicked.connect(fn); tr.addWidget(b); return b
        self.search_button = trb('search','Zoeken', self.editor_page.show_search)
        self.ai_button = trb('spark','AI-assistent', self.editor_page.show_ai)
        self.manuscript_button = trb('panel-left','Hoofdstukpaneel tonen/verbergen', self.editor_page.toggle_manuscript)
        self.right_button = trb('panel-right','Rechterpaneel tonen/verbergen', self.editor_page.toggle_right)
        tr.addStretch()
        root.addWidget(self.toolrail)

        self.restore_state()
        self.stack.currentChanged.connect(self._mode_changed); self._mode_changed(0)
        save = QAction('Opslaan', self); save.setShortcut('Ctrl+S'); save.triggered.connect(self.editor_page.save); self.addAction(save)
        focus_left = QAction(self); focus_left.setShortcut('Ctrl+Shift+L'); focus_left.triggered.connect(self.editor_page.toggle_manuscript); self.addAction(focus_left)
        focus_right = QAction(self); focus_right.setShortcut('Ctrl+Shift+R'); focus_right.triggered.connect(self.editor_page.toggle_right); self.addAction(focus_right)

    def _mode_changed(self, idx):
        self.toolrail.setVisible(self.stack.currentWidget() is self.editor_page)
        self.sync_tool_buttons()

    def show_editor(self):
        if self.editor_page.book:
            self.stack.setCurrentWidget(self.editor_page)
        else:
            self.go_home()

    def go_home(self):
        self.editor_page.close_book()
        self.start.refresh()
        self.stack.setCurrentWidget(self.start)
    def new_book(self):
        title, ok = QInputDialog.getText(self, 'Nieuw boek', 'Titel van het boek:')
        if ok:
            book = self.library.create_book(title or 'Naamloos boek'); self.start.refresh(); self.open_book(book)
    def open_book(self, book): self.editor_page.load_book(book); self.stack.setCurrentWidget(self.editor_page)

    def open_settings(self):
        old_root = self.settings.value('workspace', str(Path.home()/APP_NAME))
        d=SettingsDialog(self.settings,self,self.models)
        if d.exec():
            QApplication.instance().setStyleSheet(stylesheet(self.settings.value('theme','Helder')))
            if self.settings.value('workspace') != old_root:
                QMessageBox.information(self,'Werkmap gewijzigd','De nieuwe werkmap wordt gebruikt nadat de applicatie opnieuw is gestart.')


    def sync_tool_buttons(self):
        if not hasattr(self, 'search_button'):
            return
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
                parts.append(f'## {s.title}')
                for c in s.chapters:
                    txt=ep.editor.toPlainText() if c.id==chapter.id else self.library.read_chapter(book,c)
                    parts.append(f'# {c.title}\n{txt}')
            return '\n\n'.join(parts), f'boek: {book.title}'
        # Verhalenbibliotheek: snelle FTS-selectie. Later kan hier embeddings + snel model tussen.
        hits=self.story_index.search(prompt, limit=5)
        parts=[]
        for h in hits:
            try: body=Path(h['path']).read_text(encoding='utf-8',errors='replace')
            except Exception: body=h['snippet']
            parts.append(f"# {h['title']}\nTags: {h['tags']}\nSynopsis: {h['synopsis']}\n\n{body}")
        return '\n\n'.join(parts) if parts else '(Geen relevante oude verhalen gevonden.)', 'relevante verhalen uit bibliotheek'

    def closeEvent(self, event):
        self.editor_page.save()
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())
        self.settings.setValue('splitter', self.editor_page.left_split.saveState())
        self.settings.setValue('manuscript_visible', self.editor_page.manuscript.isVisible())
        self.settings.setValue('right_visible', self.editor_page.right.isVisible())
        super().closeEvent(event)
    def restore_state(self):
        g=self.settings.value('geometry'); s=self.settings.value('windowState'); sp=self.settings.value('splitter')
        if g: self.restoreGeometry(g)
        if s: self.restoreState(s)
        if sp: self.editor_page.left_split.restoreState(sp)
        self.editor_page.manuscript.setVisible(self.settings.value('manuscript_visible', True, bool))
        self.editor_page.right.setVisible(self.settings.value('right_visible', True, bool))


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
