from __future__ import annotations
from PySide6.QtGui import QColor, QTextCharFormat, QSyntaxHighlighter
from .spell_engine import WORD_RE, WordDictionary

class SpellHighlighter(QSyntaxHighlighter):
    """Alleen rode onderstreping. Suggesties worden uitsluitend in het paneel berekend."""
    def __init__(self, document, dictionary: WordDictionary):
        super().__init__(document)
        self.dictionary = dictionary
        self.active = False
        self.bad = QTextCharFormat()
        self.bad.setUnderlineColor(QColor('#c84b4b'))
        self.bad.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)

    def set_active(self, active: bool):
        self.active = bool(active)
        self.rehighlight()

    def highlightBlock(self, text):
        if not self.active or not self.dictionary.words: return
        for m in WORD_RE.finditer(text):
            if not self.dictionary.known(m.group(0)):
                self.setFormat(m.start(), len(m.group(0)), self.bad)
