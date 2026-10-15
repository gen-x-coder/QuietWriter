import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest
from quietwriter import update_release_preflight as p


def make_zip(tmp_path, files=None, *, extra=None):
    files = files or {'QuietWriter.exe': b'MZ-test', '_internal/app.bin': b'abc'}
    manifest = {'schema': 1, 'files': {name: {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()} for name, data in files.items()}}
    target = tmp_path / 'release.zip'
    with zipfile.ZipFile(target, 'w') as z:
        for name, data in files.items():
            z.writestr(name, data)
        z.writestr('qw-release-files.json', json.dumps(manifest))
        if extra:
            z.writestr(*extra)
    return target


def verified(path):
    return p.verify_release_zip(path, expected_size=path.stat().st_size, expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def test_valid_release(tmp_path):
    assert verified(make_zip(tmp_path))['verified_files'] == 2


@pytest.mark.parametrize('extra', [('../book.json', b'X'), ('CON.txt', b'x'), ('quietwriter.EXE', b'x'), ('_internal/app.bin', b'x'), ('_internal/evil:ads', b'x')])
def test_unsafe_entries_rejected(tmp_path, extra):
    with pytest.raises(p.ReleasePreflightError):
        verified(make_zip(tmp_path, extra=extra))


def test_corrupt_signed_asset_rejected(tmp_path):
    z = make_zip(tmp_path)
    with pytest.raises(p.ReleasePreflightError, match='digest'):
        p.verify_release_zip(z, expected_sha256='0'*64, expected_size=z.stat().st_size)


def test_incomplete_manifest_rejected(tmp_path):
    z = make_zip(tmp_path, files={'QuietWriter.exe': b'MZ-test'})
    with zipfile.ZipFile(z, 'a') as f:
        f.writestr('_internal/not-in-manifest', b'unknown')
    with pytest.raises(p.ReleasePreflightError, match='cover'):
        verified(z)


def test_no_pinned_key_fails_closed(tmp_path):
    with pytest.raises(p.ReleasePreflightError, match='production signing key'):
        p.preflight_official_release(b'{}', b'0'*64, 'test-example', tmp_path/'some.zip', installed_root=tmp_path)


def test_zip_does_not_extract_to_disk(tmp_path):
    z = make_zip(tmp_path)
    verified(z)
    assert sorted(x.name for x in tmp_path.iterdir()) == ['release.zip']


def test_offline_packaging_roundtrip(tmp_path):
    from tools.prepare_verifiable_release import package
    src = tmp_path / 'build'
    src.mkdir()
    (src / 'QuietWriter.exe').write_bytes(b'MZ')
    (src / '_internal').mkdir()
    (src / '_internal' / 'code.bin').write_bytes(b'abc')
    dst = tmp_path / 'release.zip'
    assert package(src, dst) == dst
    assert verified(dst)['verified_files'] == 2
    with pytest.raises(p.ReleasePreflightError, match='overwrite'):
        package(src, dst)
