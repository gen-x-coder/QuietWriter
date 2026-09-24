
from PySide6.QtCore import Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from ..i18n import tr
from ..media.markup import mask_image_paths

class SuggestionButtons(QWidget):
    """Compact suggestion list: one real row per word, no scroll area."""
    chosen = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)
        self._buttons = []
        self.selected = ''

    def clear(self):
        self.selected = ''
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._buttons = []
        self.setFixedHeight(0)

    def set_suggestions(self, words):
        self.clear()
        for index, word in enumerate(list(words)[:8]):
            button = QPushButton(word)
            button.setObjectName('suggestionButton')
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setFixedHeight(30)
            button.clicked.connect(lambda checked=False, w=word: self._select(w))
            self._layout.addWidget(button)
            self._buttons.append(button)
            if index == 0:
                button.setChecked(True)
                self.selected = word
        self.setFixedHeight(len(self._buttons) * 32)

    def _select(self, word):
        self.selected = word
        self.chosen.emit(word)

class SpellPanel(QWidget):
    def __init__(self, editor_page):
        super().__init__()
        self.editor_page = editor_page
        self.rows = []
        self.index = 0
        lay = QVBoxLayout(self); lay.setContentsMargins(18,18,18,18); lay.setSpacing(10)
        title = QLabel(tr('spell.title','Spellingscontrole')); title.setObjectName('sectionTitle')
        self.status = QLabel(''); self.status.setObjectName('muted'); self.status.setWordWrap(True)
        self.word = QLabel(''); self.word.setObjectName('title')
        self.suggestions = SuggestionButtons()
        buttons = QVBoxLayout(); buttons.setSpacing(6)
        self.change_btn = QPushButton(tr('spell.change','Wijzigen')); self.change_btn.clicked.connect(self.change)
        self.ignore_btn = QPushButton(tr('spell.ignore','Negeren')); self.ignore_btn.clicked.connect(self.ignore)
        self.ignore_all_btn = QPushButton(tr('spell.ignore_all','Alles negeren')); self.ignore_all_btn.clicked.connect(self.ignore_all)
        self.ignore_always_btn = QPushButton(tr('spell.ignore_always','Altijd negeren')); self.ignore_always_btn.clicked.connect(self.ignore_always)
        self.add_btn = QPushButton(tr('spell.add','Toevoegen aan woordenboek')); self.add_btn.clicked.connect(self.add_personal)
        for b in (self.change_btn, self.ignore_btn, self.ignore_all_btn, self.ignore_always_btn, self.add_btn):
            buttons.addWidget(b)
        lay.addWidget(title); lay.addWidget(self.status); lay.addWidget(self.word); lay.addWidget(self.suggestions)
        lay.addSpacing(8); lay.addStretch(1); lay.addLayout(buttons)
        self.refresh()

    def refresh(self):
        d = self.editor_page.dictionary
        if not d.words:
            self.rows=[]; self.index=0; self.status.setText(tr('spell.no_dictionary','Er is nog geen woordenboek ingesteld.')); self.word.clear(); self.suggestions.clear(); self._configure_tab_order(); return
        title_rows = [('title', w, a, b) for (w,a,b) in d.misspellings(self.editor_page.chapter_title.text())]
        body_text = mask_image_paths(self.editor_page.editor.toPlainText())
        body_rows = [('body', w, a, b) for (w,a,b) in d.misspellings(body_text)]
        self.rows = title_rows + body_rows
        if not self.rows:
            self.index=0; self.status.setText(tr('spell.no_errors','Geen spelfouten gevonden in dit hoofdstuk.')); self.word.clear(); self.suggestions.clear(); self._configure_tab_order(); return
        self.index=min(max(self.index,0),len(self.rows)-1); self.show_current()

    def focus_first_control(self):
        """Put keyboard focus on the first useful action in the guided panel."""
        if self.suggestions._buttons:
            self.suggestions._buttons[0].setFocus()
        else:
            self.change_btn.setFocus()

    def _configure_tab_order(self):
        controls = list(self.suggestions._buttons) + [
            self.change_btn, self.ignore_btn, self.ignore_all_btn,
            self.ignore_always_btn, self.add_btn,
        ]
        for first, second in zip(controls, controls[1:], strict=False):
            QWidget.setTabOrder(first, second)

    def show_current(self):
        if not self.rows: return
        source,word,start,end=self.rows[self.index]
        where = 'Hoofdstuktitel' if source == 'title' else 'Hoofdstuktekst'
        self.status.setText(f'{self.index+1} van {len(self.rows)} · {where}')
        self.word.setText(word)
        self.suggestions.set_suggestions(self.editor_page.dictionary.suggest(word))
        self._configure_tab_order()
        if source == 'title':
            self.editor_page.chapter_title.setFocus()
            self.editor_page.chapter_title.setSelection(start, end-start)
        else:
            cur=self.editor_page.editor.textCursor(); cur.setPosition(start); cur.setPosition(end,QTextCursor.KeepAnchor); self.editor_page.editor.setTextCursor(cur); self.editor_page.editor.ensureCursorVisible()

    @staticmethod
    def _row_key(row):
        source, _word, start, _end = row
        return (0 if source == 'title' else 1, start)

    def _advance(self):
        self.refresh()
        if self.rows:
            self.index=min(self.index,len(self.rows)-1); self.show_current()

    def _advance_after_global_change(self, source: str, start: int):
        """Continue at the first remaining error at/after the previous text position.

        Global ignore/dictionary actions can remove multiple earlier rows at once. Keeping
        the old numeric index would then skip the error that shifted into that slot.
        """
        anchor = (0 if source == 'title' else 1, start)
        self.refresh()
        if not self.rows:
            return
        for index, row in enumerate(self.rows):
            if self._row_key(row) >= anchor:
                self.index = index
                self.show_current()
                return
        self.index = 0
        self.show_current()

    def change(self):
        if self.editor_page.preview_live_book:
            self.editor_page.main.status.showMessage(tr('history.read_only', 'Historische versie is alleen-lezen.'), 3000)
            return
        if not self.rows or not self.suggestions.selected: return
        source,_,start,end=self.rows[self.index]
        if source == 'title':
            text = self.editor_page.chapter_title.text()
            self.editor_page.chapter_title.setText(text[:start] + self.suggestions.selected + text[end:])
            self.editor_page.rename_current()
        else:
            cur=self.editor_page.editor.textCursor(); cur.setPosition(start); cur.setPosition(end,QTextCursor.KeepAnchor); cur.insertText(self.suggestions.selected)
        self.editor_page.highlighter.rehighlight(); self._advance()

    def ignore(self):
        """Sla alleen deze ene vindplaats over; niets wordt aan lijsten toegevoegd."""
        if not self.rows: return
        self.index += 1
        if self.index >= len(self.rows): self.index=0
        self.show_current()

    def ignore_all(self):
        """Negeer dit woord alleen zolang QuietWriter draait."""
        if not self.rows: return
        source, word, start, _end = self.rows[self.index]
        self.editor_page.dictionary.ignore(word)
        self.editor_page.highlighter.rehighlight()
        self._advance_after_global_change(source, start)

    def ignore_always(self):
        """Persistente aparte negeerlijst; het woord wordt geen persoonlijk woordenboekwoord."""
        if not self.rows: return
        source, word, start, _end = self.rows[self.index]
        self.editor_page.dictionary.ignore_always(word)
        self.editor_page.highlighter.rehighlight()
        self._advance_after_global_change(source, start)

    def add_personal(self):
        if not self.rows: return
        source, word, start, _end = self.rows[self.index]
        self.editor_page.dictionary.add_personal(word)
        self.editor_page.highlighter.rehighlight()
        self._advance_after_global_change(source, start)
