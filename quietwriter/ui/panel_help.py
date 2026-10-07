from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from ..i18n import tr
from ..icon_theme import icon


def panel_help_key(panel_id: str) -> str:
    return f'help/{panel_id}/dismissed'


class _MemorySettings:
    def __init__(self):
        self._values = {}
    def value(self, key, default=None, value_type=None):
        value = self._values.get(key, default)
        return value_type(value) if value_type is not None else value
    def setValue(self, key, value):
        self._values[key] = value
    def sync(self):
        pass


class WrappedLabel(QLabel):
    """Word-wrapped label that reserves the height required by its current width."""

    def __init__(self, text: str = '', parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

    def reserve_wrapped_height(self) -> None:
        width = self.width()
        if width <= 0:
            return
        need = self.heightForWidth(width)
        if need > 0 and self.minimumHeight() != need:
            self.setMinimumHeight(need)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.reserve_wrapped_height()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.reserve_wrapped_height()

    def setText(self, text: str) -> None:
        super().setText(text)
        self.setMinimumHeight(0)
        self.reserve_wrapped_height()


class PanelHelp(QWidget):
    """Shared title row and collapsible first-use explanation for right panels."""

    expandedChanged = Signal(bool)

    def __init__(self, settings, panel_id: str, title: str, text: str | None, *, extra_title_widgets=(), parent=None):
        super().__init__(parent)
        self.settings = settings if settings is not None else _MemorySettings()
        self.panel_id = panel_id
        self._has_help = text is not None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        self.title = QLabel(title)
        self.title.setObjectName('sectionTitle')
        row.addWidget(self.title, 1)
        for widget in extra_title_widgets:
            row.addWidget(widget)

        self.toggle = QPushButton()
        self.toggle.setObjectName('panelHelpButton')
        self.toggle.setProperty('iconName', 'help')
        self.toggle.setIcon(icon('help'))
        self.toggle.setCheckable(True)
        self.toggle.setFixedSize(32, 32)
        name = tr('panel_help.toggle', 'Uitleg over {panel}', panel=title)
        self.toggle.setAccessibleName(name)
        self.toggle.setToolTip(name)
        self.toggle.toggled.connect(self._on_toggled)
        row.addWidget(self.toggle, 0, Qt.AlignTop)
        root.addLayout(row)

        self.block = QFrame()
        self.block.setObjectName('softPanel')
        self.block.setAccessibleName(tr('panel_help.region', 'Uitleg'))
        block_layout = QVBoxLayout(self.block)
        block_layout.setContentsMargins(14, 12, 14, 12)
        block_layout.setSpacing(10)
        self.text = WrappedLabel(text or '')
        self.text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        block_layout.addWidget(self.text)
        self.ok = QPushButton(tr('common.understood', 'Begrepen'))
        self.ok.setObjectName('secondaryButton')
        self.ok.clicked.connect(self.dismiss)
        ok_row = QHBoxLayout()
        ok_row.setContentsMargins(0, 0, 0, 0)
        ok_row.addWidget(self.ok)
        ok_row.addStretch(1)
        block_layout.addLayout(ok_row)
        root.addWidget(self.block)

        if not self._has_help:
            sp = self.toggle.sizePolicy()
            sp.setRetainSizeWhenHidden(True)
            self.toggle.setSizePolicy(sp)
            self.toggle.hide()
            self.block.hide()
        else:
            self.sync_from_settings()


    def _reserve_text_height(self) -> None:
        if not self._has_help or self.block.isHidden():
            return
        self.text.reserve_wrapped_height()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reserve_text_height()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._reserve_text_height()

    def is_dismissed(self) -> bool:
        if not self._has_help:
            return True
        return self.settings.value(panel_help_key(self.panel_id), False, bool)

    def sync_from_settings(self) -> None:
        if self._has_help:
            self.set_expanded(not self.is_dismissed(), remember=False)

    def set_expanded(self, expanded: bool, *, remember: bool) -> None:
        if not self._has_help:
            return
        self.toggle.blockSignals(True)
        self.toggle.setChecked(expanded)
        self.toggle.blockSignals(False)
        self.block.setVisible(expanded)
        if expanded:
            self._reserve_text_height()
        if remember:
            self.settings.setValue(panel_help_key(self.panel_id), not expanded)
            self.settings.sync()
        self.expandedChanged.emit(expanded)

    def collapse_temporarily(self) -> None:
        self.set_expanded(False, remember=False)

    def dismiss(self) -> None:
        self.set_expanded(False, remember=True)
        self.toggle.setFocus(Qt.OtherFocusReason)

    def _on_toggled(self, checked: bool) -> None:
        self.set_expanded(checked, remember=True)
        if checked:
            self.ok.setFocus(Qt.OtherFocusReason)

    def retranslate(self, title: str, text: str | None) -> None:
        self.title.setText(title)
        name = tr('panel_help.toggle', 'Uitleg over {panel}', panel=title)
        self.toggle.setAccessibleName(name)
        self.toggle.setToolTip(name)
        if text is not None:
            self.text.setText(text)
            self._reserve_text_height()
