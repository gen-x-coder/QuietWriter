import hashlib
import os
import io
import json
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from quietwriter.update_download import verify_signed_manifest, UpdateDownloadError, download_verified_asset, VerifiedAsset
from tools.create_portable_zip import create_portable_zip


def test_production_zip_layout(tmp_path):
    source=tmp_path/'QuietWriter-1.6.0';source.mkdir()
    (source/'QuietWriter.exe').write_bytes(b'dummy')
    (source/'_internal').mkdir();(source/'_internal'/'lib.dll').write_bytes(b'lib')
    target=tmp_path/'release.zip';create_portable_zip(source,target)
    with zipfile.ZipFile(target) as z:
        assert sorted(z.namelist()) == ['QuietWriter.exe','_internal/lib.dll']


def test_packager_rejects_links(tmp_path):
    source=tmp_path/'bin';source.mkdir();(source/'QuietWriter.exe').write_bytes(b'dummy')
    try:
        (source/'a').symlink_to(source/'QuietWriter.exe')
    except OSError as exc:
        if os.name == 'nt' and getattr(exc, 'winerror', None) == 1314:
            pytest.skip('Windows symlink privilege is not available; link rejection is tested where supported')
        raise
    with pytest.raises(ValueError,match='Link'):create_portable_zip(source,tmp_path/'asset.zip')


def test_schema2_signed_manifest_expires_and_older_schema_kept():
    crypt=pytest.importorskip('cryptography')
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    key=Ed25519PrivateKey.generate()
    pub=key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    now=datetime.now(timezone.utc)
    base=dict(schema=2,version='1.6.0',url='https://github.com/gen-x-coder/QuietWriter/releases/download/1.6.0/QuietWriter-windows-portable.zip',filename='QuietWriter-windows-portable.zip',size=8,sha256='a'*64,released_at=(now-timedelta(days=1)).isoformat(),expires=(now+timedelta(days=30)).isoformat())
    b=json.dumps(base).encode();asset=verify_signed_manifest(b,key.sign(b),pub)
    assert asset.expires == base['expires']
    base['expires']=(now-timedelta(days=1)).isoformat();b=json.dumps(base).encode()
    with pytest.raises(UpdateDownloadError):verify_signed_manifest(b,key.sign(b),pub)
    base.pop('expires');base.pop('released_at');base['schema']=1;b=json.dumps(base).encode()
    assert verify_signed_manifest(b,key.sign(b),pub).expires is None


def test_no_unsigned_extra_manifest_fields():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    k=Ed25519PrivateKey.generate()
    p=k.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    obj=dict(schema=2,version='1.6.0',url='https://github.com/gen-x-coder/QuietWriter/releases/download/1.6.0/QuietWriter-windows-portable.zip',filename='QuietWriter-windows-portable.zip',size=8,sha256='a'*64,released_at='2026-10-01T00:00:00Z',expires='2026-12-01T00:00:00Z',unexpected=1)
    b=json.dumps(obj).encode()
    with pytest.raises(UpdateDownloadError):verify_signed_manifest(b,k.sign(b),p)
