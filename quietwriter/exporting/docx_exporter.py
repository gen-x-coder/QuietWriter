from __future__ import annotations
from pathlib import Path
from ..docx_io import export_docx as _export_docx


def export_docx(document, destination: Path, settings: dict | None = None) -> Path:
    return _export_docx(document, destination, settings)
