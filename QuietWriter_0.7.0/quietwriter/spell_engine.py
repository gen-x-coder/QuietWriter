from __future__ import annotations
import difflib
import re
from pathlib import Path

WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿĀ-ž]+(?:['’-][A-Za-zÀ-ÖØ-öø-ÿĀ-ž]+)?")

try:
    from spylls.hunspell import Dictionary as HunspellDictionary
except Exception:  # pragma: no cover
    HunspellDictionary = None


class WordDictionary:
    def __init__(self):
        self.words = set()
        self.personal_words = set()
        self.ignored_words = set()
        self.persistent_ignored_words = set()
        self.path: Path | None = None
        self.personal_path: Path | None = None
        self.ignore_path: Path | None = None
        self.hunspell = None
        self._known_cache: dict[str, bool] = {}
        self._suggest_cache: dict[str, tuple[str, ...]] = {}

    def _clear_caches(self):
        self._known_cache.clear(); self._suggest_cache.clear()

    def clear(self):
        self.words.clear(); self.path = None; self.hunspell = None; self._clear_caches()

    def load_dic(self, path: Path):
        path = Path(path)
        lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
        source = lines[1:] if lines and lines[0].strip().isdigit() else lines
        self.words = {line.split('/', 1)[0].strip().lower() for line in source if line.split('/', 1)[0].strip()}
        self.path = path; self.hunspell = None
        aff = path.with_suffix('.aff')
        if HunspellDictionary is not None and aff.exists():
            try: self.hunspell = HunspellDictionary.from_files(str(path.with_suffix('')))
            except Exception: self.hunspell = None
        self._clear_caches()

    @staticmethod
    def _read_word_list(path: Path) -> set[str]:
        if not path.exists(): return set()
        return {line.strip().lower() for line in path.read_text(encoding='utf-8', errors='ignore').splitlines() if line.strip() and not line.lstrip().startswith('#')}

    @staticmethod
    def _write_word_list(path: Path, values: set[str]):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('\n'.join(sorted(values, key=str.casefold)) + ('\n' if values else ''), encoding='utf-8')

    def load_personal(self, path: Path):
        self.personal_path = Path(path); self.personal_words = self._read_word_list(self.personal_path); self._clear_caches()

    def load_persistent_ignored(self, path: Path):
        self.ignore_path = Path(path); self.persistent_ignored_words = self._read_word_list(self.ignore_path); self._clear_caches()

    def add_personal(self, word: str):
        word = word.strip().lower()
        if not word: return
        self.personal_words.add(word)
        if self.personal_path: self._write_word_list(self.personal_path, self.personal_words)
        self._clear_caches()

    def ignore(self, word: str):
        if word: self.ignored_words.add(word.lower()); self._clear_caches()

    def ignore_always(self, word: str):
        word = word.strip().lower()
        if not word: return
        self.persistent_ignored_words.add(word)
        if self.ignore_path: self._write_word_list(self.ignore_path, self.persistent_ignored_words)
        self._clear_caches()

    def known(self, word: str) -> bool:
        if not self.words or len(word) <= 1: return True
        if word[0].isupper(): return True
        low = word.lower()
        if low in self._known_cache: return self._known_cache[low]
        if low in self.personal_words or low in self.ignored_words or low in self.persistent_ignored_words:
            result = True
        elif self.hunspell is not None:
            try: result = bool(self.hunspell.lookup(word))
            except Exception: result = low in self.words
        else:
            result = low in self.words
        self._known_cache[low] = result
        return result

    def suggest(self, word: str):
        key = word.lower()
        if key in self._suggest_cache: return list(self._suggest_cache[key])
        out = []
        if self.hunspell is not None:
            try:
                for value in self.hunspell.suggest(word):
                    if value not in out: out.append(value)
                    if len(out) >= 8: break
            except Exception: out = []
        if not out:
            pool = self.words | self.personal_words
            if pool: out = difflib.get_close_matches(key, pool, n=8, cutoff=.72)
        self._suggest_cache[key] = tuple(out)
        return list(out)

    def misspellings(self, text: str):
        if not self.words: return []
        return [(m.group(0), m.start(), m.end()) for m in WORD_RE.finditer(text) if not self.known(m.group(0))]
