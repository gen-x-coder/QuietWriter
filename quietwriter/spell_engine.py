from __future__ import annotations
import codecs
import difflib
import re
from pathlib import Path

from .storage import _safe_atomic_write_text

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

    @staticmethod
    def _declared_dic_encoding(path: Path) -> str | None:
        """Read Hunspell's ASCII-compatible ``SET`` declaration from the .aff file."""
        aff = Path(path).with_suffix('.aff')
        if not aff.exists():
            return None
        try:
            raw = aff.read_bytes()
        except OSError:
            return None
        for raw_line in raw.splitlines():
            line = raw_line.strip()
            if not line.upper().startswith(b'SET '):
                continue
            name = line.split(None, 1)[1].decode('ascii', errors='replace').strip()
            aliases = {
                'UTF8': 'utf-8',
                'MICROSOFT-CP1252': 'cp1252',
                'WINDOWS-1252': 'cp1252',
            }
            candidate = aliases.get(name.upper(), name)
            try:
                codecs.lookup(candidate)
            except LookupError:
                return None
            return candidate
        return None

    @classmethod
    def _read_dic_lines(cls, path: Path) -> list[str]:
        raw = Path(path).read_bytes()
        declared = cls._declared_dic_encoding(path)
        candidates = []
        for encoding in (declared, 'utf-8', 'latin-1'):
            if encoding and encoding.casefold() not in {value.casefold() for value in candidates}:
                candidates.append(encoding)
        for encoding in candidates:
            try:
                return raw.decode(encoding).splitlines()
            except (LookupError, UnicodeDecodeError):
                continue
        # latin-1 maps every byte and is therefore a deterministic last resort.
        return raw.decode('latin-1').splitlines()

    def load_dic(self, path: Path):
        path = Path(path)
        lines = self._read_dic_lines(path)
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

    @classmethod
    def _write_word_list(cls, path: Path, values: set[str]) -> set[str]:
        path = Path(path)
        merged = cls._read_word_list(path) | {value.strip().lower() for value in values if value.strip()}
        payload = '\n'.join(sorted(merged, key=str.casefold)) + ('\n' if merged else '')
        _safe_atomic_write_text(path, payload)
        return merged

    def load_personal(self, path: Path):
        self.personal_path = Path(path); self.personal_words = self._read_word_list(self.personal_path); self._clear_caches()

    def load_persistent_ignored(self, path: Path):
        self.ignore_path = Path(path); self.persistent_ignored_words = self._read_word_list(self.ignore_path); self._clear_caches()

    def add_personal(self, word: str):
        word = word.strip().lower()
        if not word: return
        self.personal_words.add(word)
        if self.personal_path:
            self.personal_words = self._write_word_list(self.personal_path, self.personal_words)
        self._clear_caches()

    def ignore(self, word: str):
        if word: self.ignored_words.add(word.lower()); self._clear_caches()

    def ignore_always(self, word: str):
        word = word.strip().lower()
        if not word: return
        self.persistent_ignored_words.add(word)
        if self.ignore_path:
            self.persistent_ignored_words = self._write_word_list(self.ignore_path, self.persistent_ignored_words)
        self._clear_caches()

    def known(self, word: str) -> bool:
        if not self.words or len(word) <= 1: return True
        low = word.lower()
        cache_key = word if self.hunspell is not None else low
        if cache_key in self._known_cache: return self._known_cache[cache_key]
        if low in self.personal_words or low in self.ignored_words or low in self.persistent_ignored_words:
            result = True
        elif self.hunspell is not None:
            try: result = bool(self.hunspell.lookup(word))
            except Exception: result = low in self.words
        else:
            result = low in self.words
        self._known_cache[cache_key] = result
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
