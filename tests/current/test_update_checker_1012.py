from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from quietwriter.update_checker import is_newer_version


def test_update_version_comparison_is_numeric():
    assert is_newer_version("1.0.13", "1.0.12") is True
    assert is_newer_version("v1.1.0", "1.0.99") is True
    assert is_newer_version("1.0.12", "1.0.12") is False
    assert is_newer_version("1.0.11", "1.0.12") is False


def test_invalid_release_tag_is_not_treated_as_newer():
    assert is_newer_version("latest", "1.0.12") is False
