from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path

_LOCALE_DIR = Path(__file__).with_name('locales')
_current_locale = 'nl'


@lru_cache(maxsize=8)
def load_locale(code: str = 'nl') -> dict:
    path = _LOCALE_DIR / f'{code}.json'
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def set_locale(code: str | None) -> str:
    """Set the process-wide UI locale and return the effective locale code."""
    global _current_locale
    requested = str(code or 'nl').strip().lower().replace('-', '_')
    # UI locales currently use language-only filenames (nl.json, en.json).
    requested = requested.split('_', 1)[0]
    if not (_LOCALE_DIR / f'{requested}.json').exists():
        requested = 'nl'
    _current_locale = requested
    return _current_locale


def current_locale() -> str:
    return _current_locale


def tr(key: str, default: str | None = None, code: str | None = None, **values) -> str:
    locale = code or _current_locale
    text = load_locale(locale).get(key, default if default is not None else key)
    try:
        return str(text).format(**values)
    except Exception:
        return str(text)
