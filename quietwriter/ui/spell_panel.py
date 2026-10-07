
from PySide6.QtCore import Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from ..i18n import tr
from ..document_view import text_for_language_tools
from .panel_help import PanelHelp

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
        self._rows_rev = -1
        lay = QVBoxLayout(self); lay.setContentsMargins(18,18,18,18); lay.setSpacing(10)
        self.panel_help = PanelHelp(editor_page.main.settings, 'spell', tr('spell.title','Spellingscontrole'), tr('panel_help.spell', 'Loop de onbekende woorden in dit hoofdstuk één voor één langs. Negeren slaat alleen deze plek over; Alles negeren geldt tot je QuietWriter sluit. Altijd negeren en Toevoegen aan woordenboek onthouden het woord blijvend.'))
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
        lay.addWidget(self.panel_help); lay.addWidget(self.status); lay.addWidget(self.word); lay.addWidget(self.suggestions)
        lay.addSpacing(8); lay.addStretch(1); lay.addLayout(buttons)
        self.refresh()

    def refresh(self, *, select_in_editor: bool = True):
        self._rows_rev = self.editor_page.editor.document().revision()
        d = self.editor_page.dictionary
        if not d.words:
            self.rows=[]; self.index=0; self.status.setText(tr('spell.no_dictionary','Er is nog geen woordenboek ingesteld.')); self.word.clear(); self.suggestions.clear(); self._configure_tab_order(); return
        title_rows = [('title', w, a, b) for (w,a,b) in d.misspellings(self.editor_page.chapter_title.text())]
        body_text = text_for_language_tools(self.editor_page.editor.toPlainText())
        body_rows = [('body', w, a, b) for (w,a,b) in d.misspellings(body_text)]
        self.rows = title_rows + body_rows
        if not self.rows:
            self.index=0; self.status.setText(tr('spell.no_errors','Geen spelfouten gevonden in dit hoofdstuk.')); self.word.clear(); self.suggestions.clear(); self._configure_tab_order(); return
        self.index=min(max(self.index,0),len(self.rows)-1); self.show_current(select_in_editor=select_in_editor)

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

    def show_current(self, *, select_in_editor: bool = True):
        if not self.rows: return
        source,word,start,end=self.rows[self.index]
        where = tr('spell.chapter_title', 'Hoofdstuktitel') if source == 'title' else tr('spell.chapter_text', 'Hoofdstuktekst')
        self.status.setText(tr('spell.position', '{index} van {total} · {where}', index=self.index+1, total=len(self.rows), where=where))
        self.word.setText(word)
        self.suggestions.set_suggestions(self.editor_page.dictionary.suggest(word))
        self._configure_tab_order()
        if not select_in_editor:
            return
        if source == 'title':
            self.editor_page.chapter_title.setFocus()
            self.editor_page.chapter_title.setSelection(start, end-start)
        else:
            cur=self.editor_page.editor.textCursor(); cur.setPosition(start); cur.setPosition(end,QTextCursor.KeepAnchor); self.editor_page.editor.setTextCursor(cur); self.editor_page.editor.ensureCursorVisible()


    def follow_editor_cursor(self):
        """Focus the misspelling under the caret without moving/selecting editor text."""
        revision = self.editor_page.editor.document().revision()
        if not self.rows or revision != self._rows_rev:
            self.refresh(select_in_editor=False)
        pos = self.editor_page.editor.textCursor().position()
        for index, row in enumerate(self.rows):
            source, _word, start, end = row
            if source == 'body' and start <= pos <= end:
                self.index = index
                self.show_current(select_in_editor=False)
                return True
        return False

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

    def _source_text(self, source: str) -> str:
        if source == 'title':
            return self.editor_page.chapter_title.text()
        return self.editor_page.editor.toPlainText()

    def _reanchor_stale_row(self, source: str, word: str, start: int) -> tuple[str, str, int, int] | None:
        """Refresh stale spell offsets and find the nearest same misspelling.

        The spell panel may stay open while the user keeps typing. Rows therefore
        cannot be trusted as mutable offsets after any editor change. A refresh
        rebuilds offsets from the live title/body; choosing the nearest equal word
        preserves the user's intended occurrence when text was inserted before it.
        """
        self.refresh()
        candidates = [
            (index, row) for index, row in enumerate(self.rows)
            if row[0] == source and row[1] == word
        ]
        if not candidates:
            if self.rows:
                self.status.setText(tr(
                    'spell.text_changed',
                    'De tekst is intussen gewijzigd. De spellingscontrole is ververst; controleer de huidige treffer.'
                ))
            return None
        index, row = min(candidates, key=lambda item: (abs(item[1][2] - start), item[1][2]))
        self.index = index
        self.show_current()
        return row

    def change(self):
        if self.editor_page.preview_live_book:
            self.editor_page.main.status.showMessage(tr('history.read_only', 'Historische versie is alleen-lezen.'), 3000)
            return
        if not self.rows or not self.suggestions.selected: return
        source, word, start, end = self.rows[self.index]
        replacement = self.suggestions.selected

        # Rows contain offsets from the most recent refresh. If the writer typed
        # in the meantime, never apply those stale coordinates blindly.
        text = self._source_text(source)
        if text[start:end] != word:
            row = self._reanchor_stale_row(source, word, start)
            if row is None:
                return
            source, live_word, start, end = row
            text = self._source_text(source)
            if live_word != word or text[start:end] != word:
                return

        if source == 'title':
            self.editor_page.chapter_title.setText(text[:start] + replacement + text[end:])
            self.editor_page.rename_current()
        else:
            cur=self.editor_page.editor.textCursor(); cur.setPosition(start); cur.setPosition(end,QTextCursor.KeepAnchor); cur.insertText(replacement)
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
