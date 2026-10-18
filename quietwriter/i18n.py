from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path

_LOCALE_DIR = Path(__file__).with_name('locales')
_current_locale = 'nl'
# Vertalingen van gebruikers (1.7): <werkmap>/translations/<code>.json.
# Een bestand voor een meegeleverde taal past die aan; een nieuwe code voegt
# een taal toe. Sleutels die beginnen met "_" (zoals "_meta") zijn geen tekst.
_user_dir: Path | None = None
BUILTIN_CODES = ('nl', 'en', 'de', 'fr', 'es')
META_KEY = '_meta'


def set_user_translation_dir(path: Path | str | None) -> None:
    global _user_dir
    _user_dir = Path(path) if path else None
    load_locale.cache_clear()


def user_translation_dir() -> Path | None:
    return _user_dir


def user_translation_path(code: str) -> Path | None:
    return (_user_dir / f'{code}.json') if _user_dir else None


def _read_json(path: Path | None) -> dict:
    if path is None or not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def builtin_locale(code: str) -> dict:
    return _read_json(_LOCALE_DIR / f'{code}.json')


def user_locale(code: str) -> dict:
    """Alleen de teksten uit het gebruikersbestand (zonder _meta)."""
    data = _read_json(user_translation_path(code))
    return {k: v for k, v in data.items() if not k.startswith('_') and isinstance(v, str) and v != ''}


def user_locale_meta(code: str) -> dict:
    meta = _read_json(user_translation_path(code)).get(META_KEY)
    return meta if isinstance(meta, dict) else {}


@lru_cache(maxsize=16)
def load_locale(code: str = 'nl') -> dict:
    data = dict(builtin_locale(code))
    data.update(user_locale(code))
    return data


def available_languages() -> list[tuple[str, str]]:
    """(code, naam) van meegeleverde talen en vertalingen van gebruikers."""
    names = {'nl': 'Nederlands', 'en': 'English', 'de': 'Deutsch', 'fr': 'Français', 'es': 'Español'}
    rows = [(code, names[code]) for code in BUILTIN_CODES]
    if _user_dir and _user_dir.is_dir():
        for path in sorted(_user_dir.glob('*.json')):
            code = path.stem.lower()
            if code in BUILTIN_CODES or not code.isalpha() or len(code) > 3:
                continue
            name = str(user_locale_meta(code).get('name') or code)
            rows.append((code, name))
    return rows


def _known(code: str) -> bool:
    if (_LOCALE_DIR / f'{code}.json').exists():
        return True
    path = user_translation_path(code)
    return bool(path and path.is_file())


def set_locale(code: str | None) -> str:
    """Set the process-wide UI locale and return the effective locale code."""
    global _current_locale
    requested = str(code or 'nl').strip().lower().replace('-', '_')
    # UI locales use language-only filenames (nl.json, en.json, de.json, fr.json, es.json).
    requested = requested.split('_', 1)[0]
    if not _known(requested):
        requested = 'nl'
    _current_locale = requested
    return _current_locale


def current_locale() -> str:
    return _current_locale


def tr(key: str, default: str | None = None, code: str | None = None, **values) -> str:
    locale = code or _current_locale
    data = load_locale(locale)
    if key in data:
        text = data[key]
    elif locale not in {'nl', 'en'} and key in load_locale('en'):
        # English is the product fallback for incomplete translated locales.
        # Dutch code defaults remain the native fallback for Dutch itself.
        text = load_locale('en')[key]
    else:
        text = default if default is not None else key
    try:
        return str(text).format(**values)
    except Exception:
        return str(text)
