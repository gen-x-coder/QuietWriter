from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QDateEdit, QSpinBox


class _WheelNeedsFocus:
    """Ignore wheel changes until a form field has keyboard focus.

    The ignored wheel event can then continue to the containing scroll area,
    so scrolling a settings page never changes a value just because the mouse
    happens to be above a control.
    """

    def _init_wheel_focus(self):
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event):
        if not self.hasFocus():
            event.ignore()
            return
        super().wheelEvent(event)


class QuietComboBox(_WheelNeedsFocus, QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_wheel_focus()


class QuietSpinBox(_WheelNeedsFocus, QSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_wheel_focus()


class QuietDateEdit(_WheelNeedsFocus, QDateEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_wheel_focus()
