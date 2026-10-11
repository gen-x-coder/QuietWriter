"""Catch import-time Qt failures (notably incorrect PySide6 module imports).

Runs in a separate process so a Qt teardown crash cannot affect pytest itself.
When PySide6 isn't installed the test is explicitly skipped, never silently green.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def test_all_ui_modules_import_offscreen():
    pytest.importorskip('PySide6', reason='PySide6 is required for the Qt startup gate')
    script = '''
import importlib, pkgutil
import quietwriter.ui
modules = sorted(m.name for m in pkgutil.walk_packages(quietwriter.ui.__path__, quietwriter.ui.__name__ + '.'))
for name in modules:
    importlib.import_module(name)
print('QT_IMPORT_GATE_OK', len(modules))
'''
    environment = dict(os.environ, QT_QPA_PLATFORM='offscreen')
    outcome = subprocess.run(
        [sys.executable, '-c', script], cwd=ROOT, env=environment,
        capture_output=True, text=True, timeout=45,
    )
    assert outcome.returncode == 0, outcome.stdout + '\n' + outcome.stderr
    assert 'QT_IMPORT_GATE_OK' in outcome.stdout


def test_application_offscreen_smoke_startup():
    pytest.importorskip('PySide6', reason='PySide6 is required for the Qt startup gate')
    environment = dict(os.environ, QT_QPA_PLATFORM='offscreen')
    outcome = subprocess.run(
        [sys.executable, '-m', 'quietwriter.app', '--smoke-test'],
        cwd=ROOT, env=environment, capture_output=True, text=True, timeout=60,
    )
    assert outcome.returncode == 0, outcome.stdout + '\n' + outcome.stderr
