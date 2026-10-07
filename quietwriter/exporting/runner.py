from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .docx_exporter import export_docx
from .epub_exporter import export_epub
from .markdown_exporter import export_markdown
from .pdf_exporter import export_pdf

FORMAT_SUFFIXES = {'epub': '.epub', 'pdf': '.pdf', 'markdown': '.md', 'docx': '.docx', 'qwbook': '.qwbook'}


@dataclass(frozen=True)
class ExportResult:
    path: Path
    format: str
    bytes: int
    validated: bool


def destination_for(output_dir: Path, document, format_name: str) -> Path:
    return Path(output_dir) / f'{document.slug}{FORMAT_SUFFIXES[format_name]}'


def run_export(library, book, document, format_name: str, settings: dict, destination: Path) -> ExportResult:
    """The single export route shared by guided and manual export.

    UI code prepares the snapshot, preflight and overwrite confirmation; this
    function only renders/writes the requested format.
    """
    destination = Path(destination)
    validated = False
    if format_name == 'epub':
        export_epub(document, destination, settings)
        validated = True
    elif format_name == 'pdf':
        export_pdf(document, destination, settings)
    elif format_name == 'docx':
        export_docx(document, destination, settings)
    elif format_name == 'qwbook':
        from ..qwbook_io import export_qwbook
        options = settings.get('qwbook') or {}
        export_qwbook(
            library, book, destination,
            include_history=bool(options.get('include_history', True)),
            include_ai_chat=bool(options.get('include_ai_chat', True)),
        )
    elif format_name == 'markdown':
        export_markdown(document, destination, settings)
    else:
        raise ValueError(f'Onbekend exportformaat: {format_name}')
    size = destination.stat().st_size if destination.exists() else 0
    return ExportResult(path=destination, format=format_name, bytes=size, validated=validated)
