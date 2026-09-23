from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QDialog, QFrame, QHBoxLayout, QLabel, QProgressBar,
    QVBoxLayout,
)

from .. import APP_NAME, __version__
from ..i18n import tr


class Splash(QDialog):
    """Small startup window that stays visible until the main window is exposed.

    The splash deliberately has no fixed timeout.  Startup can be nearly instant
    or can take longer when a workspace/provider is slow; in both cases it only
    disappears once Qt/Windows has actually exposed the main window.
    """

    def __init__(self):
        super().__init__(None)
        self.setObjectName('startupSplash')
        self.setWindowFlags(
            Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setFixedSize(520, 300)
        self._main_window = None
        self._finish_attempts = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(1, 1, 1, 1)
        outer.setSpacing(0)

        card = QFrame()
        card.setObjectName('splashCard')
        outer.addWidget(card)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(38, 34, 38, 28)
        lay.setSpacing(0)

        title = QLabel(APP_NAME)
        title.setObjectName('splashTitle')
        lay.addWidget(title)

        tagline = QLabel(tr('splash.tagline', 'Rustig schrijven. Heldere boeken.'))
        tagline.setObjectName('splashTagline')
        lay.addWidget(tagline)

        lay.addStretch(1)

        self.status = QLabel(tr('splash.starting', 'QuietWriter voorbereiden…'))
        self.status.setObjectName('splashStatus')
        lay.addWidget(self.status)
        lay.addSpacing(10)

        self.progress = QProgressBar()
        self.progress.setObjectName('splashProgress')
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(5)
        lay.addWidget(self.progress)

        lay.addSpacing(22)
        footer = QHBoxLayout()
        footer.setSpacing(12)
        version = QLabel(tr('splash.version', 'Versie {version}', version=__version__))
        version.setObjectName('splashFooter')
        copyright_label = QLabel(tr('splash.copyright', '© 2026 Lucas Bonsel'))
        copyright_label.setObjectName('splashFooter')
        footer.addWidget(version)
        footer.addStretch(1)
        footer.addWidget(copyright_label)
        lay.addLayout(footer)

    def showEvent(self, event):
        super().showEvent(event)
        screen = self.screen() or QApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            self.move(area.center() - self.rect().center())

    def set_status(self, text: str):
        self.status.setText(text)
        # Startup still runs synchronously.  Processing pending paint events here
        # keeps the status useful without turning startup into a fake timed show.
        QApplication.processEvents()

    def finish_when_ready(self, main_window):
        self._main_window = main_window
        self._finish_attempts = 0
        QTimer.singleShot(0, self._wait_for_main_window)

    def _wait_for_main_window(self):
        window = self._main_window
        if window is None:
            self.close()
            return

        handle = window.windowHandle()
        exposed = bool(window.isVisible() and handle is not None and handle.isExposed())
        if exposed or self._finish_attempts >= 100:
            self.status.setText(tr('splash.ready', 'Klaar'))
            QTimer.singleShot(60, self._finish)
            return

        self._finish_attempts += 1
        QTimer.singleShot(20, self._wait_for_main_window)

    def _finish(self):
        window = self._main_window
        self.close()
        if window is not None:
            window.raise_()
            window.activateWindow()
