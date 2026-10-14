from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ROOT / 'quietwriter' / 'locales'
CODES = ('nl', 'en', 'de', 'fr', 'es')
PLACEHOLDER_RE = re.compile(r'\{[^{}]+\}')


def placeholders(value: str) -> list[str]:
    return sorted(PLACEHOLDER_RE.findall(value))


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    """Do not allow JSON duplicate keys to silently shadow translated text."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate translation key: {key}')
        result[key] = value
    return result


def main() -> int:
    errors: list[str] = []
    data = {}
    for code in CODES:
        try:
            data[code] = json.loads((LOCALES / f'{code}.json').read_text(encoding='utf-8'),
                                    object_pairs_hook=_unique_pairs)
        except (ValueError, OSError) as exc:
            errors.append(f'{code}: {exc}')
    if errors:
        print('\n'.join(errors))
        return 1
    reference = data['en']
    for code, locale in data.items():
        missing = sorted(set(reference) - set(locale))
        extra = sorted(set(locale) - set(reference))
        if missing:
            errors.append(f'{code}: missing keys: {missing}')
        if extra:
            errors.append(f'{code}: extra keys: {extra}')
        for key in set(reference) & set(locale):
            if placeholders(str(reference[key])) != placeholders(str(locale[key])):
                errors.append(f'{code}: placeholder mismatch: {key}')
            if r'\n' in str(locale[key]):
                errors.append(f'{code}: literal backslash-n: {key}')
    if errors:
        print('\n'.join(errors))
        return 1
    print(f'OK: {len(reference)} keys in {len(CODES)} locales')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
