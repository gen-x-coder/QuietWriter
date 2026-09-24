from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExportTemplate:
    key: str
    name_nl: str
    name_en: str
    description_nl: str
    description_en: str
    css_file: str


TEMPLATES = {
    'classic': ExportTemplate('classic', 'Klassiek', 'Classic', 'Traditionele romanopmaak met inspringing.', 'Traditional novel layout with indented paragraphs.', 'classic.css'),
    'modern': ExportTemplate('modern', 'Modern', 'Modern', 'Rustig en eigentijds met ruimere alinea-afstand.', 'Calm contemporary layout with more paragraph spacing.', 'modern.css'),
    'literary': ExportTemplate('literary', 'Literair', 'Literary', 'Ruimere, typografische opmaak met klassieke accenten.', 'Airier typographic layout with classic accents.', 'literary.css'),
}


def template_css(key: str) -> str:
    template = TEMPLATES.get(key, TEMPLATES['classic'])
    path = Path(__file__).resolve().parent.parent / 'export_templates' / template.css_file
    return path.read_text(encoding='utf-8')
