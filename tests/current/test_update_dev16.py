"""Signed fixture integration, health decision, and recovery protocol."""
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
from quietwriter.update_integration_lab import run_fixture_update
from quietwriter.side_by_side_update import _paths, recover_test_update
from quietwriter.windows_portable_updater import make_test_install, make_test_archive, PortableUpdateError


def fixture(tmp_path):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    root = make_test_install(tmp_path)
    archive, _ = make_test_archive(tmp_path / 'QuietWriter-windows-portable.zip')
    signing = Ed25519PrivateKey.generate()
    pub = signing.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    now = datetime.now(timezone.utc)
    manifest = dict(schema=2, version='1.5.1',
        url='https://github.com/gen-x-coder/QuietWriter/releases/download/1.5.1/QuietWriter-windows-portable.zip',
        filename='QuietWriter-windows-portable.zip', size=archive.stat().st_size,
        sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        released_at=(now-timedelta(hours=1)).isoformat(),
        expires=(now+timedelta(days=10)).isoformat())
    b = json.dumps(manifest).encode()
    return root, archive, b, signing.sign(b), pub, signing


def test_signed_success_and_retained_previous(tmp_path):
    root, archive, b, sig, pub, key = fixture(tmp_path)
    assert run_fixture_update(root, archive, b, sig, pub) == '1.5.1'
    assert (root/'version.txt').read_text().strip() == '1.5.1'
    assert (_paths(root)[1]/'version.txt').read_text().strip() == '1.5.0'
    assert not _paths(root)[2].exists()


def test_failed_health_restores_old(tmp_path):
    root, archive, b, sig, pub, key = fixture(tmp_path)
    with pytest.raises(PortableUpdateError,match='Health check failed'):
        run_fixture_update(root, archive, b, sig, pub, health_should_fail=True)
    assert (root/'version.txt').read_text().strip() == '1.5.0'
    assert not _paths(root)[2].exists()


def test_invalid_signature_does_not_touch_install(tmp_path):
    root, archive, b, sig, pub, key = fixture(tmp_path)
    with pytest.raises(ValueError):run_fixture_update(root, archive, b, bytes(64), pub)
    assert (root/'version.txt').read_text().strip() == '1.5.0'
    assert not _paths(root)[2].exists()


def test_downgrade_policy_before_swap(tmp_path):
    root, archive, b, sig, pub, key = fixture(tmp_path)
    with pytest.raises(ValueError):run_fixture_update(root, archive, b, sig, pub, highest_seen='1.8.0')
    assert (root/'version.txt').read_text().strip() == '1.5.0'


def test_corrupt_archive_rejected_before_swap(tmp_path):
    root, archive, b, sig, pub, key = fixture(tmp_path)
    archive.write_bytes(archive.read_bytes()+b'corruption')
    with pytest.raises(PortableUpdateError,match='size mismatch'):
        run_fixture_update(root, archive, b, sig, pub)
    assert (root/'version.txt').read_text().strip() == '1.5.0'


def test_health_probe_detects_wrong_version(tmp_path):
    root, archive, b, sig, pub, key = fixture(tmp_path)
    data=json.loads(b);data['version']='1.5.2';new=json.dumps(data).encode()
    with pytest.raises(PortableUpdateError,match='Health check failed'):
        run_fixture_update(root, archive, new, key.sign(new), pub)
    assert (root/'version.txt').read_text().strip() == '1.5.0'
