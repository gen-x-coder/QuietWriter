# -*- mode: python ; coding: utf-8 -*-
"""Experimental Linux x86_64 onedir build of QuietWriter."""
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).resolve().parent.parent

def folder(path):
    p = ROOT / path
    return [(str(p), path)] if p.is_dir() else []

datas = []
for path in ('quietwriter/icons', 'quietwriter/locales', 'quietwriter/export_templates', 'resources/fonts'):
    datas += folder(path)
for src, dest in (
    ('quietwriter/resources/quietwriter.ico', 'quietwriter/resources'),
    ('documents/licenses/LICENSE', 'documents/licenses'),
    ('documents/licenses/THIRD_PARTY_LICENSES.md', 'documents/licenses'),
):
    p = ROOT / src
    if p.is_file():
        datas.append((str(p), dest))

a = Analysis(
    [str(ROOT / 'main.py')], pathex=[str(ROOT)],
    binaries=[], datas=datas,
    hiddenimports=collect_submodules('spylls') + collect_submodules('docx') + collect_submodules('keyring.backends'),
    hookspath=[], runtime_hooks=[],
    excludes=['tkinter', 'pytest', 'unittest',
              'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineCore',
              'PySide6.QtQml', 'PySide6.QtQuick'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='QuietWriter',
          debug=False, strip=False, upx=False, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='QuietWriter')
