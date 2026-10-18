# Third-party licenses

QuietWriter depends on third-party software and assets. This inventory is intended for the Windows 1.0 release and must be checked again when the portable build is assembled.

## Runtime software

- **Python** — Python Software Foundation License. Source: https://www.python.org/psf/license/
- **PySide6 / Qt for Python** — distributed by The Qt Company under applicable Qt for Python licensing terms, including LGPL/GPL options for the Community Edition. Source and license information: https://doc.qt.io/qtforpython-6/licenses.html
- **Requests** — Apache License 2.0. Source: https://github.com/psf/requests
- **spylls** — MIT License. Source: https://github.com/zverok/spylls
- **python-docx** — MIT License. Source: https://github.com/python-openxml/python-docx
- **lxml** — BSD 3-Clause License. Source: https://github.com/lxml/lxml
- **keyring** (OpenRouter browser login via Windows Credential Manager) — MIT License. Source: https://github.com/jaraco/keyring
  - **jaraco.classes**, **jaraco.functools**, **jaraco.context**, **more-itertools** — MIT License.
  - **pywin32-ctypes** — BSD 3-Clause License. Source: https://github.com/enthought/pywin32-ctypes
- **Velopack** (Python package and the `Update.exe` it adds to the portable build) — MIT License. Source: https://github.com/velopack/velopack

## Bundled writing fonts

The following fonts are licensed under the **SIL Open Font License 1.1**. Their complete OFL text is shipped in each font folder under `resources/fonts/<font>/OFL.txt`.

- Merriweather — The Merriweather Project Authors
- Literata — The Literata Project Authors
- Source Serif 4 — Adobe / Source Serif project
- EB Garamond — The EB Garamond Project Authors

## Hunspell dictionaries

QuietWriter can use Hunspell-compatible dictionaries for spelling. Since 1.7 **no dictionary is bundled**, neither in the source package nor in the Windows build.

- QuietWriter finds dictionaries that come with ONLYOFFICE, LibreOffice or OpenOffice on the computer and uses them read-only.
- On request, QuietWriter downloads a dictionary from a fixed list pinned to one commit of https://github.com/LibreOffice/dictionaries (see `quietwriter/dictionary_download.py`). Every file is checked against a SHA-256 checksum stored in QuietWriter.
- Each downloaded dictionary keeps its own license next to it as `LICENSE-<locale>.txt` in the workspace, and its author and license are shown before downloading. Example: Dutch (nl_NL) is OpenTaal (https://opentaal.org), Revised BSD License (3-clause) or CC BY 3.0. Since 1.7.0-dev14 the list has 35 dictionaries; the author and license of each one are in `CATALOG` in `quietwriter/dictionary_download.py` and in the downloaded `LICENSE-<locale>.txt`.

## Libraries bundled via Requests

- **urllib3** — MIT License. https://github.com/urllib3/urllib3
- **idna** — BSD 3-Clause License. https://github.com/kjd/idna
- **charset-normalizer** — MIT License. https://github.com/jawah/charset_normalizer
- **certifi** — Mozilla Public License 2.0. https://github.com/certifi/python-certifi

## Packaging

- **PyInstaller** bootloader — GPL 2.0 with an exception that allows distributing the built executable under any license. https://pyinstaller.org/en/stable/license.html

## Development/test-only dependencies

Some tools used by CI and tests (for example pytest and PyYAML) are not necessarily redistributed with the application. Their licenses still apply to those tools themselves, but they only need to be included in the end-user third-party notice if they are actually bundled in the release.
