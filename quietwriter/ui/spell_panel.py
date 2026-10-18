
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from ..i18n import tr
from ..document_view import text_for_language_tools
from .panel_help import PanelHelp

class _SuggestionSignals(QObject):
    ready = Signal(int, object, str, object)


class _SuggestionJob(QRunnable):
    """Calculate proposals without holding up Qt's interface thread."""

    def __init__(self, signals, request_id, dictionary, word):
        super().__init__()
        self.signals = signals
        self.request_id = request_id
        self.dictionary = dictionary
        self.word = word
        self.generation = getattr(dictionary, '_generation', 0)

    def run(self):
        try:
            proposals = self.dictionary.suggest(self.word)
        except Exception:
            proposals = []
        try:
            self.signals.ready.emit(self.request_id, self.dictionary, self.word,
                                    (self.generation, proposals))
        except RuntimeError:
            # The panel may have been destroyed while a suggestion was running.
            pass


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
        self._suggest_request = 0
        self._suggest_pool = QThreadPool(self)
        self._suggest_pool.setMaxThreadCount(1)
        self._suggest_signals = _SuggestionSignals()
        self._suggest_signals.ready.connect(self._suggestions_ready)
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

    def closeEvent(self, event):
        self._suggest_request += 1
        self._suggest_pool.clear()
        super().closeEvent(event)

    def refresh(self, *, select_in_editor: bool = True):
        self._suggest_request += 1
        self._rows_rev = self.editor_page.editor.document().revision()
        d = self.editor_page.dictionary
        if not d.words:
            self.rows=[]; self.index=0; self.status.setText(tr('spell.no_dictionary_171','Er is nog geen woordenboek voor deze taal. Kies of download er een bij Instellingen → Spelling.')); self.word.clear(); self.suggestions.clear(); self._set_actions_enabled(False); self._configure_tab_order(); return
        title_rows = [('title', w, a, b) for (w,a,b) in d.misspellings(self.editor_page.chapter_title.text())]
        body_text = text_for_language_tools(self.editor_page.editor.toPlainText())
        body_rows = [('body', w, a, b) for (w,a,b) in d.misspellings(body_text)]
        self.rows = title_rows + body_rows
        if not self.rows:
            self.index=0; self.status.setText(tr('spell.no_errors','Geen spelfouten gevonden in dit hoofdstuk.')); self.word.clear(); self.suggestions.clear(); self._set_actions_enabled(False); self._configure_tab_order(); return
        self._set_actions_enabled(True)
        self.index=min(max(self.index,0),len(self.rows)-1); self.show_current(select_in_editor=select_in_editor)

    def _set_actions_enabled(self, enabled: bool):
        """Zonder woord (geen woordenboek, geen fouten) zijn de knoppen niet te gebruiken (dev15)."""
        for button in (self.ignore_btn, self.ignore_all_btn, self.ignore_always_btn, self.add_btn):
            button.setEnabled(bool(enabled))
        if not enabled:
            self.change_btn.setEnabled(False)

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
        self._suggest_request += 1
        self.suggestions.clear()
        self.change_btn.setEnabled(False)
        dictionary = self.editor_page.dictionary
        job = _SuggestionJob(self._suggest_signals, self._suggest_request, dictionary, word)
        self._suggest_pool.clear()  # Discard requests that have not started yet.
        self._suggest_pool.start(job)
        self._configure_tab_order()
        if not select_in_editor:
            return
        if source == 'title':
            self.editor_page.chapter_title.setFocus()
            self.editor_page.chapter_title.setSelection(start, end-start)
        else:
            # Een fout in een voetnoot: die staat ingeklapt in de tekst, dus
            # selecteer hem in de notenstrook onder het blad (1.7).
            note = self._footnote_at(start, end)
            strip = getattr(self.editor_page, 'footnote_strip', None)
            if note is not None and strip is not None:
                index, content_start = note
                if strip.select_in_note(index, start - content_start, end - content_start):
                    return
            cur=self.editor_page.editor.textCursor(); cur.setPosition(start); cur.setPosition(end,QTextCursor.KeepAnchor); self.editor_page.editor.setTextCursor(cur); self.editor_page.editor.ensureCursorVisible()

    def _footnote_at(self, start: int, end: int):
        """(nootnummer vanaf 0, begin noottekst) als start–end in een voetnoot valt."""
        spans_of = getattr(self.editor_page.editor, 'footnote_spans', None)
        if spans_of is None:
            return None
        for index, (_open, content_start, content_end, _close) in enumerate(spans_of()):
            if content_start <= start and end <= content_end:
                return index, content_start
        return None


    def _suggestions_ready(self, request_id, dictionary, word, payload):
        # An older job may finish after the user moved to a different word,
        # changed books or selected a different dictionary.
        if request_id != self._suggest_request or dictionary is not self.editor_page.dictionary:
            return
        # The dictionary object is reused across source changes; object identity
        # alone is not enough to reject an older worker result.
        if isinstance(payload, tuple) and len(payload) == 2 and isinstance(payload[0], int):
            generation, proposals = payload
            if generation != getattr(dictionary, '_generation', 0):
                return
        else:
            proposals = payload  # Compatibility with existing direct Qt tests.
        if not self.rows or self.rows[self.index][1] != word:
            return
        self.suggestions.set_suggestions(proposals)
        self.change_btn.setEnabled(bool(proposals))
        self._configure_tab_order()

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
            note = self._footnote_at(start, end)
            strip = getattr(self.editor_page, 'footnote_strip', None)
            if note is not None and strip is not None and strip.select_in_note(note[0], start - note[1], end - note[1]):
                # Via het notenveld zelf: dat schrijft door naar het manuscript en
                # kan daarna nooit de oude tekst terugzetten.
                strip.rows[note[0]].edit.textCursor().insertText(replacement)
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
