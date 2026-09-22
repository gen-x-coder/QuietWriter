from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from .. import APP_NAME, __version__
from ..font_catalog import bundled_fonts


class LicenseCard(QFrame):
    def __init__(self, title: str, subtitle: str, license_text: str, source_url: str = '', parent=None):
        super().__init__(parent)
        self.setObjectName('licenseCard')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(10)
        title_label = QLabel(title)
        title_label.setObjectName('licenseTitle')
        header.addWidget(title_label, 1)
        self.toggle = QPushButton('Licentietekst tonen')
        self.toggle.setObjectName('secondaryButton')
        self.toggle.setCheckable(True)
        self.toggle.clicked.connect(self._toggle_text)
        header.addWidget(self.toggle)
        layout.addLayout(header)

        info = QLabel(subtitle)
        info.setObjectName('muted')
        info.setWordWrap(True)
        layout.addWidget(info)

        if source_url:
            source = QPushButton('Bron bekijken')
            source.setObjectName('linkButton')
            source.setCursor(Qt.PointingHandCursor)
            source.clicked.connect(lambda checked=False, url=source_url: QDesktopServices.openUrl(QUrl(url)))
            layout.addWidget(source, 0, Qt.AlignLeft)

        self.text = QPlainTextEdit()
        self.text.setObjectName('licenseText')
        self.text.setReadOnly(True)
        self.text.setPlainText(license_text)
        self.text.setMaximumHeight(280)
        self.text.hide()
        layout.addWidget(self.text)

    def _toggle_text(self, checked: bool):
        self.text.setVisible(checked)
        self.toggle.setText('Licentietekst verbergen' if checked else 'Licentietekst tonen')


class AboutPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 0, 8, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName('aboutScroll')
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(scroll, 1)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 18, 24)
        layout.setSpacing(14)
        scroll.setWidget(content)

        heading = QLabel(f'Over {APP_NAME}')
        heading.setObjectName('settingsPageTitle')
        layout.addWidget(heading)

        intro = QLabel(
            'QuietWriter is een rustige lokale schrijversomgeving voor het schrijven, structureren en voorbereiden van boeken. '
            'De applicatie is ontworpen om de tekst centraal te houden en zo min mogelijk visuele ruis toe te voegen.'
        )
        intro.setObjectName('muted')
        intro.setWordWrap(True)
        intro.setMaximumWidth(760)
        layout.addWidget(intro)

        version = QLabel(f'Versie {__version__}')
        version.setObjectName('aboutVersion')
        layout.addWidget(version)

        layout.addSpacing(8)
        maker_title = QLabel('Maker')
        maker_title.setObjectName('settingsFieldLabel')
        layout.addWidget(maker_title)
        maker = QLabel(
            'QuietWriter wordt ontwikkeld door Lucas Bonsel. Het project is ontstaan vanuit de wens om een eenvoudige, '
            'lokale en prettige schrijfomgeving te hebben die niet probeert een tekstverwerker of projectmanagementtool te zijn.'
        )
        maker.setWordWrap(True)
        maker.setMaximumWidth(760)
        layout.addWidget(maker)

        copyright_label = QLabel('© 2026 Lucas Bonsel. Alle rechten voorbehouden.')
        copyright_label.setObjectName('muted')
        layout.addWidget(copyright_label)

        layout.addSpacing(12)
        license_heading = QLabel('Fontlicenties')
        license_heading.setObjectName('settingsFieldLabel')
        layout.addWidget(license_heading)
        license_intro = QLabel(
            'QuietWriter gebruikt onderstaande lettertypen als aanbevolen schrijftypografie. De licenties hieronder gelden '
            'voor de genoemde lettertypen en niet automatisch voor QuietWriter zelf.'
        )
        license_intro.setObjectName('muted')
        license_intro.setWordWrap(True)
        license_intro.setMaximumWidth(760)
        layout.addWidget(license_intro)

        for font in bundled_fonts():
            try:
                text = font.license_path.read_text(encoding='utf-8')
            except OSError:
                text = 'De licentietekst kon niet worden geladen.'
            card = LicenseCard(
                f'{font.family} — {font.license_name}',
                font.copyright,
                text,
                font.source,
            )
            card.setMaximumWidth(820)
            layout.addWidget(card)

        layout.addStretch(1)
