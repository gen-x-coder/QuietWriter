# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller-spec voor de portable Windows-build van QuietWriter (onedir).

Bouwen (vanuit de projectmap):

    python tools/fetch_bundled_fonts.py
    python tools/fetch_dictionaries.py
    python packaging/make_version_info.py
    pyinstaller --noconfirm --clean packaging/quietwriter.spec

Resultaat: dist/QuietWriter/QuietWriter.exe plus de map _internal/.

Alle paden in QuietWriter zijn relatief aan __file__. In een onedir-build
staan de modules in _internal/, dus de datamappen moeten daar met dezelfde
relatieve structuur terechtkomen als in de broncode:

    _internal/quietwriter/icons/...        (icon_theme.py, ai/ui.py)
    _internal/quietwriter/locales/...      (i18n.py)
    _internal/quietwriter/resources/...    (icon_theme.app_icon_path)
    _internal/quietwriter/export_templates (exporting/templates.py)
    _internal/resources/fonts/...          (font_catalog.py)
    _internal/dictionaries/...             (dictionary_catalog.py, 'Meegeleverd')
    _internal/documents/licenses/LICENSE, THIRD_PARTY_LICENSES.md  (ui/about_page.py)
"""
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).resolve().parent  # noqa: F821  (SPECPATH komt van PyInstaller)
ICON = ROOT / 'quietwriter' / 'resources' / 'quietwriter.ico'
VERSION_FILE = ROOT / 'build' / 'version_info.txt'


def _dir(src: str, dest: str | None = None):
    path = ROOT / src
    if not path.exists():
        return []
    return [(str(path), dest or src)]


def _file(src: str, dest: str = '.'):
    path = ROOT / src
    return [(str(path), dest)] if path.exists() else []


fonts_dir = ROOT / 'resources' / 'fonts'
if not any(fonts_dir.rglob('*.ttf')):
    sys.exit('Geen lettertypen gevonden. Draai eerst: python tools/fetch_bundled_fonts.py')

datas = []
datas += _dir('quietwriter/icons')
datas += _dir('quietwriter/locales')
datas += _dir('quietwriter/export_templates')
datas += [(str(ICON), 'quietwriter/resources')]
datas += _dir('resources/fonts')
datas += _dir('dictionaries')  # optioneel: alleen als tools/fetch_dictionaries.py gedraaid is
datas += _file('documents/licenses/LICENSE', 'documents/licenses')
datas += _file('documents/licenses/THIRD_PARTY_LICENSES.md', 'documents/licenses')

hiddenimports = collect_submodules('spylls')

# Qt-modules die QuietWriter niet gebruikt. Scheelt tientallen MB en
# voorkomt dat PyInstaller ze via een omweg toch meeneemt.
excludes = [
    'tkinter', 'unittest', 'pydoc', 'pytest',
    'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineQuick',
    'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickWidgets', 'PySide6.QtQuick3D',
    'PySide6.Qt3DCore', 'PySide6.Qt3DRender', 'PySide6.QtCharts', 'PySide6.QtDataVisualization',
    'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets', 'PySide6.QtBluetooth',
    'PySide6.QtPositioning', 'PySide6.QtLocation', 'PySide6.QtSensors', 'PySide6.QtSerialPort',
    'PySide6.QtSql', 'PySide6.QtTest', 'PySide6.QtDesigner', 'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
]

a = Analysis(  # noqa: F821
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

# Qt-plugins (virtueel toetsenbord, PDF-afbeeldingsplugin) trekken QML/Quick
# en Qt Pdf mee, die QuietWriter niet gebruikt. Filter ze samen met hun
# plugins weg, zodat er geen plugin achterblijft die een ontbrekende DLL zoekt.
_DROP = ('qt6qml', 'qt6quick', 'virtualkeyboard', 'qt6pdf', 'qpdf')


def _keep(entry) -> bool:
    name = str(entry[0]).replace('\\', '/').lower().rsplit('/', 1)[-1]
    return not any(token in name for token in _DROP)


a.binaries = [b for b in a.binaries if _keep(b)]

pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QuietWriter',
    debug=False,
    strip=False,
    upx=False,          # UPX geeft vaker vals alarm bij virusscanners
    console=False,      # geen zwart consolevenster
    icon=str(ICON),
    version=str(VERSION_FILE) if VERSION_FILE.exists() else None,
)
coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='QuietWriter',
)
