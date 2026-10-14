import hashlib
import json
from pathlib import Path

import pytest

from quietwriter.update_download import (UpdateDownloadError, download_verified_asset,
                                          verify_signed_manifest)

crypto = pytest.importorskip('cryptography.hazmat.primitives.asymmetric.ed25519')
serialization = pytest.importorskip('cryptography.hazmat.primitives.serialization')


def signed(data=b'dummy'):
    key = crypto.Ed25519PrivateKey.generate()
    pub = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    payload = json.dumps(dict(schema=1, version='1.5.0',
                              filename='QuietWriter-windows-portable.zip',
                              url='https://github.com/gen-x-coder/QuietWriter/releases/download/1.5.0/QuietWriter-windows-portable.zip',
                              size=len(data), sha256=hashlib.sha256(data).hexdigest())).encode()
    return payload, key.sign(payload), pub


def test_signed_manifest_and_tampering():
    doc, sig, pub = signed()
    asset = verify_signed_manifest(doc, sig, pub)
    assert asset.version == '1.5.0'
    with pytest.raises(UpdateDownloadError):
        verify_signed_manifest(doc + b' ', sig, pub)
    with pytest.raises(UpdateDownloadError):
        verify_signed_manifest(doc, sig, b'\0' * 32)


def test_signed_unofficial_url_rejected():
    key = crypto.Ed25519PrivateKey.generate()
    pub = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    doc, _, _ = signed()
    bad = doc.replace(b'github.com/gen-x-coder/QuietWriter', b'github.com/someone/Other')
    with pytest.raises(UpdateDownloadError):
        verify_signed_manifest(bad, key.sign(bad), pub)


class Response:
    def __init__(self, url, chunks):
        self.url, self.chunks = url, chunks
        self.status_code = 200
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def raise_for_status(self): pass
    def iter_content(self, chunk_size): return iter(self.chunks)


class Session:
    def __init__(self, url, chunks): self.url, self.chunks = url, chunks
    def get(self, url, **kwargs): return Response(self.url, self.chunks)


def test_download_verified_is_atomic_and_preserves_existing(tmp_path):
    doc, sig, pub = signed(b'dummy')
    asset = verify_signed_manifest(doc, sig, pub)
    staged = download_verified_asset(asset, tmp_path, session=Session(asset.url, [b'du', b'mmy']))
    assert staged.read_bytes() == b'dummy'
    # A verified identical download may be reused (supported since dev.19).
    repeated = download_verified_asset(asset, tmp_path, session=Session(asset.url, [b'dummy']))
    assert repeated == staged
    assert staged.read_bytes() == b'dummy'
    assert not list(tmp_path.glob('*.partial'))


@pytest.mark.parametrize('chunks', [[b'changed'], [b'dum'], [b'dummy-extra']])
def test_download_failure_removes_partial(tmp_path, chunks):
    doc, sig, pub = signed(b'dummy')
    asset = verify_signed_manifest(doc, sig, pub)
    with pytest.raises(UpdateDownloadError):
        download_verified_asset(asset, tmp_path, session=Session(asset.url, chunks))
    assert not list(tmp_path.iterdir())


def test_cancelled_and_redirect_blocked(tmp_path):
    doc, sig, pub = signed(b'dummy')
    asset = verify_signed_manifest(doc, sig, pub)
    with pytest.raises(UpdateDownloadError):
        download_verified_asset(asset, tmp_path, cancelled=lambda: True,
                                session=Session(asset.url, [b'dummy']))
    assert not list(tmp_path.iterdir())
    with pytest.raises(UpdateDownloadError):
        download_verified_asset(asset, tmp_path, session=Session('https://evil.example/download', [b'dummy']))
