"""Een vertaling van een gebruiker (Instellingen → Vertalingen → Exporteren)
opnemen in QuietWriter.

    python tools/merge_translation.py quietwriter-it.json

- Bestaande taal (nl, en, de, fr, es): de teksten uit het bestand gaan vóór.
- Nieuwe taal: er komt een nieuw bestand ``quietwriter/locales/<code>.json``.
  Daarna nog met de hand: de code in ``i18n.BUILTIN_CODES``, in
  ``tools/check_locales.py`` (CODES) en in de taallijst van Instellingen.
- Teksten waarvan de ``{plekken}`` niet kloppen met het Nederlands worden
  overgeslagen en gemeld; er gaat nooit stil iets kapot.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ROOT / 'quietwriter' / 'locales'
PLACEHOLDER_RE = re.compile(r'\{[^{}]+\}')


def _places(text: str) -> list[str]:
    return sorted(PLACEHOLDER_RE.findall(text or ''))


def merge(source: Path) -> tuple[Path, int, list[str]]:
    data = json.loads(source.read_text(encoding='utf-8'))
    meta = data.get('_meta') or {}
    code = str(meta.get('code') or '').lower()
    if not re.fullmatch(r'[a-z]{2,3}', code):
        raise SystemExit('Geen geldige taalcode in _meta.code')
    reference = json.loads((LOCALES / 'nl.json').read_text(encoding='utf-8'))
    target_path = LOCALES / f'{code}.json'
    target = json.loads(target_path.read_text(encoding='utf-8')) if target_path.exists() else {}
    skipped, taken = [], 0
    for key, value in data.items():
        if key.startswith('_') or key not in reference or not isinstance(value, str) or not value.strip():
            continue
        if _places(value) != _places(reference[key]):
            skipped.append(key)
            continue
        target[key] = value
        taken += 1
    target_path.write_text(json.dumps(dict(sorted(target.items())), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return target_path, taken, skipped


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    path, taken, skipped = merge(Path(argv[1]))
    print(f'{path.name}: {taken} teksten overgenomen')
    for key in skipped:
        print(f'  overgeslagen (plekken kloppen niet): {key}')
    if path.stem not in ('nl', 'en', 'de', 'fr', 'es'):
        print('Nieuwe taal: voeg de code toe aan i18n.BUILTIN_CODES, tools/check_locales.py en de taallijst in Instellingen.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
