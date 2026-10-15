from pathlib import Path

from quietwriter.update_pilot_gate import PILOT_MARKER, pilot_enabled


def test_off_by_default(tmp_path):
    assert not pilot_enabled(tmp_path)


def test_empty_marker_turns_on_and_removal_turns_off(tmp_path):
    marker = tmp_path / PILOT_MARKER
    marker.touch()
    assert pilot_enabled(tmp_path)
    marker.unlink()
    assert not pilot_enabled(tmp_path)


def test_rejects_nonempty_marker_and_directory(tmp_path):
    marker = tmp_path / PILOT_MARKER
    marker.write_text('true')
    assert not pilot_enabled(tmp_path)
    marker.unlink()
    marker.mkdir()
    assert not pilot_enabled(tmp_path)


def test_rejects_missing_workspace(tmp_path):
    assert not pilot_enabled(tmp_path / 'missing')


def test_gate_never_grants_signed_release_keys(tmp_path):
    (tmp_path / PILOT_MARKER).touch()
    assert pilot_enabled(tmp_path)
    from quietwriter.update_release_preflight import PINNED_RELEASE_KEYS
    assert PINNED_RELEASE_KEYS == {}
