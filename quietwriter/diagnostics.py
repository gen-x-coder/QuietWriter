"""Minimal, privacy-preserving support information. No user paths or book data."""
from __future__ import annotations

import platform
import sys

from . import __version__


def diagnostic_summary(*, qt_version: str, pyside_version: str) -> str:
    """Only fixed public runtime facts; never scan settings, files or environment."""
    return "\n".join((
        "QuietWriter diagnostics",
        f"QuietWriter: {__version__}",
        f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        f"PySide6: {pyside_version}",
        f"Qt: {qt_version}",
        f"Platform: {platform.system()}",
    ))
