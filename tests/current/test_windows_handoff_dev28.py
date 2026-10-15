"""Safety contracts for Windows handle-based lab handoff."""
from __future__ import annotations
import os
import re
import pytest
from quietwriter import update_handoff_windows_lab as h


def test_event_name_unpredictable_and_scoped():
    a, b = h.new_event_name(), h.new_event_name()
    assert a != b
    assert re.fullmatch(r'Local\\QuietWriterUpdateLab-[0-9a-f]{32}', a)
    h._validate_event_name(a)


@pytest.mark.parametrize('name', ['Global\\QuietWriter', 'Local\\QuietWriterUpdateLab-foo', '../QuietWriter', '', 'Local\\QuietWriterUpdateLab-' + 'z'*32])
def test_invalid_event_names_rejected(name):
    with pytest.raises(h.HandoffError):
        h._validate_event_name(name)


def test_platform_is_windows_only():
    if os.name != 'nt':
        with pytest.raises(h.HandoffError, match='Windows'):
            h.process_identity(os.getpid())


@pytest.mark.skipif(os.name != 'nt', reason='Windows required')
def test_identity_current_process():
    created, image = h.process_identity(os.getpid())
    assert created > 0 and os.path.isabs(image)
