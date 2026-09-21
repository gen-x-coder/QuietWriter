from __future__ import annotations
import difflib
import re
from pathlib import Path
from PySide6.QtGui import QColor, QTextCharFormat, QSyntaxHighlighter

WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿĀ-ž]+(?:['’-][A-Za-zÀ-ÖØ-öø-ÿĀ-ž]+)?")


class WordDictionary:
    def __init__(self):
        self.words = set()
        self.personal_words = set()
        self.ignored_words = set()
        self.path: Path | None = None
        self.personal_path: Path | None = None

    def clear(self):
        self.words.clear()
        self.path = None

    def load_dic(self, path: Path):
        path = Path(path)
        words = set()
        lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
        for line in lines[1:] if lines and lines[0].strip().isdigit() else lines:
            word = line.split('/', 1)[0].strip().lower()
            if word:
                words.add(word)
        self.words = words
        self.path = path

    def load_personal(self, path: Path):
        self.personal_path = Path(path)
        if self.personal_path.exists():
            self.personal_words = {
                line.strip().lower() for line in self.personal_path.read_text(encoding='utf-8', errors='ignore').splitlines()
                if line.strip()
            }

    def add_personal(self, word: str):
        word = word.strip().lower()
        if not word:
            return
        self.personal_words.add(word)
        if self.personal_path:
            self.personal_path.parent.mkdir(parents=True, exist_ok=True)
            self.personal_path.write_text('\n'.join(sorted(self.personal_words)) + '\n', encoding='utf-8')

    def ignore(self, word: str):
        if word:
            self.ignored_words.add(word.lower())

    def known(self, word: str) -> bool:
        if not self.words or len(word) <= 1:
            return True
        low = word.lower()
        if low in self.personal_words or low in self.ignored_words:
            return True
        # Namen en zinopeningen niet automatisch afkeuren. Dit voorkomt veel ruis in fictie.
        if word[0].isupper():
            return True
        return low in self.words

    def suggest(self, word: str):
        pool = self.words | self.personal_words
        if not pool:
            return []
        return difflib.get_close_matches(word.lower(), pool, n=6, cutoff=.72)

    def misspellings(self, text: str):
        if not self.words:
            return []
        rows = []
        for m in WORD_RE.finditer(text):
            word = m.group(0)
            if not self.known(word):
                rows.append((word, m.start(), m.end()))
        return rows


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
