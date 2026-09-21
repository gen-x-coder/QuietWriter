from __future__ import annotations
import difflib
import re
from pathlib import Path
from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QColor, QTextCharFormat, QSyntaxHighlighter

WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿĀ-ž]+(?:['’-][A-Za-zÀ-ÖØ-öø-ÿĀ-ž]+)?")


class WordDictionary:
    def __init__(self):
        self.words = set()

    def load_dic(self, path: Path):
        words = set()
        lines = Path(path).read_text(encoding='utf-8', errors='ignore').splitlines()
        for line in lines[1:] if lines and lines[0].strip().isdigit() else lines:
            word = line.split('/', 1)[0].strip().lower()
            if word:
                words.add(word)
        self.words = words

    def known(self, word: str) -> bool:
        if not self.words or len(word) <= 1 or word[0].isupper():
            return True
        return word.lower() in self.words

    def suggest(self, word: str):
        if not self.words:
            return []
        return difflib.get_close_matches(word.lower(), self.words, n=5, cutoff=.72)


class SpellHighlighter(QSyntaxHighlighter):
    def __init__(self, document, dictionary: WordDictionary):
        super().__init__(document)
        self.dictionary = dictionary
        self.bad = QTextCharFormat()
        self.bad.setUnderlineColor(QColor('#c84b4b'))
        self.bad.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)

    def highlightBlock(self, text):
        if not self.dictionary.words:
            return
        for m in WORD_RE.finditer(text):
            word = m.group(0)
            if not self.dictionary.known(word):
                self.setFormat(m.start(), len(word), self.bad)
