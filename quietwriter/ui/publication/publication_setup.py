from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from ...publication_models import BACK_MATTER, FRONT_MATTER, PublicationData
from ...i18n import tr


class PublicationSetup(QWidget):
    saved = Signal(object)
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = PublicationData()
        root = QVBoxLayout(self); root.setContentsMargins(34, 28, 34, 28); root.setSpacing(14)
        title = QLabel(tr('publication.setup.title', 'Publicatiestructuur')); title.setObjectName('title')
        intro = QLabel(tr('publication.setup.intro', 'Kies welke onderdelen vóór en na het manuscript in het uiteindelijke boek horen. Je kunt deze keuze later altijd wijzigen.'))
        intro.setObjectName('muted'); intro.setWordWrap(True)
        root.addWidget(title); root.addWidget(intro)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget(); lay = QVBoxLayout(body); lay.setContentsMargins(0, 8, 12, 8); lay.setSpacing(8)
        self.checks = {}
        self._add_group(lay, tr('publication.setup.front', 'VOORWERK'), FRONT_MATTER)
        lay.addSpacing(18)
        self._add_group(lay, tr('publication.setup.back', 'ACHTERWERK'), BACK_MATTER)
        lay.addStretch()
        scroll.setWidget(body); root.addWidget(scroll, 1)

        buttons = QHBoxLayout(); buttons.addStretch()
        cancel = QPushButton(tr('common.cancel', 'Annuleren')); cancel.setObjectName('secondaryButton'); cancel.clicked.connect(self.cancelled.emit)
        done = QPushButton(tr('publication.setup.done', 'Gereed')); done.setObjectName('primaryButton'); done.clicked.connect(self._save)
        buttons.addWidget(cancel); buttons.addWidget(done); root.addLayout(buttons)

    def _add_group(self, layout, heading, definitions):
        label = QLabel(heading); label.setObjectName('microLabel'); layout.addWidget(label)
        for key, text, _kind in definitions:
            cb = QCheckBox(tr(f'publication.item.{key}', text)); cb.setObjectName('publicationToggle'); self.checks[key] = cb; layout.addWidget(cb)

    def set_data(self, data: PublicationData):
        self._data = data
        enabled = set(data.enabled)
        for key, cb in self.checks.items(): cb.setChecked(key in enabled)

    def _save(self):
        self._data.enabled = [key for key in self.checks if self.checks[key].isChecked()]
        self.saved.emit(self._data)
