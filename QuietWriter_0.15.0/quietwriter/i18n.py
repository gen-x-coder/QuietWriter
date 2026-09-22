from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path

_LOCALE_DIR = Path(__file__).with_name('locales')

@lru_cache(maxsize=8)
def load_locale(code: str = 'nl') -> dict:
    path = _LOCALE_DIR / f'{code}.json'
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def tr(key: str, default: str | None = None, code: str = 'nl', **values) -> str:
    text = load_locale(code).get(key, default if default is not None else key)
    try:
        return str(text).format(**values)
    except Exception:
        return str(text)
