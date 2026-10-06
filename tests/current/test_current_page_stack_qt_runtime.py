import os

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

PySide6 = pytest.importorskip('PySide6')
from PySide6.QtWidgets import QApplication, QWidget
from quietwriter.ui.current_page_stack import CurrentPageStack


@pytest.fixture(scope='module')
def app():
    instance = QApplication.instance() or QApplication([])
    return instance


def test_hidden_large_page_does_not_raise_stack_minimum_height(app):
    stack = CurrentPageStack()
    small = QWidget()
    small.setMinimumSize(120, 80)
    huge = QWidget()
    huge.setMinimumSize(300, 1050)
    stack.addWidget(small)
    stack.addWidget(huge)

    stack.setCurrentWidget(small)
    assert stack.minimumSizeHint().height() <= 80

    stack.setCurrentWidget(huge)
    assert stack.minimumSizeHint().height() >= 1050

    stack.setCurrentWidget(small)
    assert stack.minimumSizeHint().height() <= 80
