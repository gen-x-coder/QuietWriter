# Third-party licenses

QuietWriter depends on third-party software and assets. This inventory is intended for the Windows 1.0 release and must be checked again when the portable build is assembled.

## Runtime software

- **Python** — Python Software Foundation License. Source: https://www.python.org/psf/license/
- **PySide6 / Qt for Python** — distributed by The Qt Company under applicable Qt for Python licensing terms, including LGPL/GPL options for the Community Edition. Source and license information: https://doc.qt.io/qtforpython-6/licenses.html
- **Requests** — Apache License 2.0. Source: https://github.com/psf/requests
- **spylls** — MIT License. Source: https://github.com/zverok/spylls

## Bundled writing fonts

The following fonts are licensed under the **SIL Open Font License 1.1**. Their complete OFL text is shipped in each font folder under `resources/fonts/<font>/OFL.txt`.

- Merriweather — The Merriweather Project Authors
- Literata — The Literata Project Authors
- Source Serif 4 — Adobe / Source Serif project
- EB Garamond — The EB Garamond Project Authors

## Hunspell dictionaries

QuietWriter can use Hunspell-compatible dictionaries for spelling. No dictionary data is stored in the source package. The Windows portable build bundles one dictionary, fetched at build time by `tools/fetch_dictionaries.py`:

- **Dutch (nl_NL)** — OpenTaal, https://opentaal.org (source: https://github.com/OpenTaal/opentaal-hunspell, distributed via https://github.com/LibreOffice/dictionaries). © 2020 OpenTaal (Simon Brouwer, Sander van Geloven); © 2006–2010 OpenTaal (Ruud Baars, Simon Brouwer); © 2001–2005 Simon Brouwer and others; © 1996 Nederlandstalige TeX Gebruikersgroep. Used under the **Revised BSD License (3-clause)**; OpenTaal also offers CC BY 3.0. The full license header is kept in `dictionaries/nl_NL.aff` and summarised in `dictionaries/LICENSE_nl_NL.txt`.

## Libraries bundled via Requests

- **urllib3** — MIT License. https://github.com/urllib3/urllib3
- **idna** — BSD 3-Clause License. https://github.com/kjd/idna
- **charset-normalizer** — MIT License. https://github.com/jawah/charset_normalizer
- **certifi** — Mozilla Public License 2.0. https://github.com/certifi/python-certifi

## Packaging

- **PyInstaller** bootloader — GPL 2.0 with an exception that allows distributing the built executable under any license. https://pyinstaller.org/en/stable/license.html

## Development/test-only dependencies

Some tools used by CI and tests (for example pytest and PyYAML) are not necessarily redistributed with the application. Their licenses still apply to those tools themselves, but they only need to be included in the end-user third-party notice if they are actually bundled in the release.
