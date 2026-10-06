"""Haalt de Nederlandse Hunspell-woordenlijst van OpenTaal op voor de portable build.

De bestanden komen in ./dictionaries/, waar dictionary_catalog.py ze als
'Meegeleverd' vindt. OpenTaal is vrij te gebruiken onder de Revised BSD
License (3-clause) en/of CC BY 3.0; de licentiekop staat in nl_NL.aff zelf en
wordt hier ook als apart bestand meegeleverd (zie documents/licenses/THIRD_PARTY_LICENSES.md).
"""
from __future__ import annotations

from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'dictionaries'
BASE = 'https://raw.githubusercontent.com/LibreOffice/dictionaries/master/nl_NL/'
FILES = {'nl_NL.aff': 20_000, 'nl_NL.dic': 1_000_000}

LICENSE_TEXT = """Nederlandse woordenlijst (nl_NL.aff / nl_NL.dic)
Bron: OpenTaal — https://opentaal.org — https://github.com/OpenTaal/opentaal-hunspell
Gedistribueerd via https://github.com/LibreOffice/dictionaries (nl_NL)

© 2020 OpenTaal (Simon Brouwer, Sander van Geloven)
© 2006 - 2010 OpenTaal (Ruud Baars, Simon Brouwer)
© 2001 - 2005 Simon Brouwer and others
© 1996 Nederlandstalige TeX Gebruikersgroep

QuietWriter gebruikt deze bestanden onder de Revised BSD License (3-clause):
https://opensource.org/licenses/BSD-3-Clause
De volledige licentiekop staat bovenaan nl_NL.aff.
"""


def fetch(name: str, minimum: int) -> None:
    request = Request(BASE + name, headers={'User-Agent': 'QuietWriter packager'})
    with urlopen(request, timeout=60) as response:
        data = response.read()
    if len(data) < minimum:
        raise RuntimeError(f'{name}: onverwacht klein ({len(data)} bytes)')
    (TARGET / name).write_bytes(data)
    print(f'dictionaries/{name} ({len(data):,} bytes)')


def main() -> int:
    TARGET.mkdir(parents=True, exist_ok=True)
    for name, minimum in FILES.items():
        fetch(name, minimum)
    (TARGET / 'LICENSE_nl_NL.txt').write_text(LICENSE_TEXT, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
