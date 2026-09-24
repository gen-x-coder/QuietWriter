from __future__ import annotations

import platform
import sys

from PySide6 import __version__ as pyside_version
from PySide6.QtCore import Qt, QUrl, qVersion
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from .. import APP_NAME, __version__
from ..font_catalog import bundled_fonts
from ..i18n import tr


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
        self.toggle = QPushButton(tr('about.license.show', 'Licentietekst tonen'))
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
            source = QPushButton(tr('about.source', 'Bron bekijken'))
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
        self.toggle.setText(tr('about.license.hide', 'Licentietekst verbergen') if checked else tr('about.license.show', 'Licentietekst tonen'))


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

        hero = QFrame()
        hero.setObjectName('aboutHero')
        hero.setMaximumWidth(820)
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 22, 24, 22)
        hero_layout.setSpacing(5)

        eyebrow = QLabel(APP_NAME.upper())
        eyebrow.setObjectName('aboutEyebrow')
        hero_layout.addWidget(eyebrow)
        title = QLabel(APP_NAME)
        title.setObjectName('aboutHeroTitle')
        hero_layout.addWidget(title)
        tagline = QLabel(tr('about.tagline', 'Rustig schrijven. Heldere boeken.'))
        tagline.setObjectName('aboutHeroTagline')
        hero_layout.addWidget(tagline)
        hero_layout.addSpacing(8)
        version = QLabel(tr('about.version', 'Versie {version}', version=__version__))
        version.setObjectName('aboutVersionChip')
        hero_layout.addWidget(version, 0, Qt.AlignLeft)
        layout.addWidget(hero)

        layout.addSpacing(4)
        about_title = QLabel(tr('about.product.title', 'Over QuietWriter'))
        about_title.setObjectName('settingsFieldLabel')
        layout.addWidget(about_title)
        intro = QLabel(tr('about.intro', 'QuietWriter is een rustige lokale schrijversomgeving voor het schrijven, structureren en voorbereiden van boeken. De applicatie is ontworpen om de tekst centraal te houden en zo min mogelijk visuele ruis toe te voegen.'))
        intro.setObjectName('muted')
        intro.setWordWrap(True)
        intro.setMaximumWidth(790)
        layout.addWidget(intro)

        privacy_title = QLabel(tr('about.privacy.title', 'Lokaal & privacy'))
        privacy_title.setObjectName('settingsFieldLabel')
        layout.addWidget(privacy_title)
        privacy = QLabel(tr(
            'about.privacy.text',
            'QuietWriter heeft geen eigen cloudopslag nodig voor je manuscripten. AI is optioneel: Ollama kan lokaal draaien. Gebruik je een externe AI-provider, dan kunnen de tekst en context die voor die AI-actie nodig zijn naar die provider worden verzonden.'
        ))
        privacy.setObjectName('muted')
        privacy.setWordWrap(True)
        privacy.setMaximumWidth(790)
        layout.addWidget(privacy)

        copyright_label = QLabel(tr('about.copyright', '© 2026 Lucas Bonsel. Alle rechten voorbehouden.'))
        copyright_label.setObjectName('muted')
        layout.addWidget(copyright_label)

        layout.addSpacing(8)
        technical_title = QLabel(tr('about.technical.title', 'Technische omgeving'))
        technical_title.setObjectName('settingsFieldLabel')
        layout.addWidget(technical_title)

        runtime = QLabel(tr(
            'about.runtime',
            'Python {python} · PySide6 {pyside} · Qt {qt} · {platform}',
            python=f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}',
            pyside=pyside_version,
            qt=qVersion(),
            platform=platform.system(),
        ))
        runtime.setObjectName('aboutRuntime')
        layout.addWidget(runtime)

        layout.addSpacing(10)
        license_heading = QLabel(tr('about.font_licenses', 'Fontlicenties'))
        license_heading.setObjectName('settingsFieldLabel')
        layout.addWidget(license_heading)
        license_intro = QLabel(tr('about.font_licenses_help', 'QuietWriter gebruikt onderstaande lettertypen als aanbevolen schrijftypografie. De licenties hieronder gelden voor de genoemde lettertypen en niet automatisch voor QuietWriter zelf.'))
        license_intro.setObjectName('muted')
        license_intro.setWordWrap(True)
        license_intro.setMaximumWidth(790)
        layout.addWidget(license_intro)

        for font in bundled_fonts():
            try:
                text = font.license_path.read_text(encoding='utf-8')
            except OSError:
                text = tr('about.license.load_error', 'De licentietekst kon niet worden geladen.')
            card = LicenseCard(
                f'{font.family} — {font.license_name}',
                font.copyright,
                text,
                font.source,
            )
            card.setMaximumWidth(820)
            layout.addWidget(card)

        layout.addStretch(1)
