"""Gedeelde paginavorm (1.7): marges, sectiekoppen en veldlabels.

Eén visuele grammatica voor detail- en formulierpagina's, gelijk aan
Instellingen: links een vetgedrukte naam (met eventueel uitleg), rechts de
bediening; sectiekoppen klein in hoofdletters; subnavigatie op de
paginakleur met de keuze als accentvlak (``contextSectionList``).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

PAGE_MARGINS = (34, 28, 34, 26)
FIELD_LABEL_WIDTH = 210
SHORT_FIELD_WIDTH = 320
FORM_MAX_WIDTH = 1040


def set_page_margins(layout, *, bottom: int | None = None) -> None:
    left, top, right, default_bottom = PAGE_MARGINS
    layout.setContentsMargins(left, top, right, default_bottom if bottom is None else bottom)


def field_label(text: str, min_width: int = FIELD_LABEL_WIDTH) -> QLabel:
    label = QLabel(text)
    label.setObjectName('settingsFieldLabel')
    label.setMinimumWidth(min_width)
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
    return label


def section_heading(title: str, help_text: str | None = None, *, first: bool = False) -> QWidget:
    """Sectiekop zoals in Instellingen: klein, hoofdletters, gedempt; optioneel uitleg eronder."""
    box = QWidget()
    box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 0 if first else 20, 0, 6)
    layout.setSpacing(4)
    label = QLabel(title.upper())
    label.setObjectName('settingsSectionTitle')
    layout.addWidget(label, 0, Qt.AlignLeft)
    if help_text:
        detail = QLabel(help_text)
        detail.setObjectName('settingsFieldHelp')
        detail.setWordWrap(True)
        layout.addWidget(detail)
    return box
