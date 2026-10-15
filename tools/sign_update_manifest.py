"""Offline-only detached Ed25519 signature tool for release manifest JSON.

Do not pass private signing keys to CI, GitHub, or this project's source tree.
Never automatically generate a production signing key.
"""
from __future__ import annotations
import argparse
from pathlib import Path

def sign(manifest: Path, keyfile: Path, signature: Path) -> None:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    data = manifest.read_bytes()
    key = keyfile.read_bytes()
    if len(key) != 32:
        raise ValueError('Expected raw 32-byte Ed25519 private seed')
    if signature.exists():
        raise FileExistsError('Refusing to overwrite existing signature')
    signature.write_bytes(Ed25519PrivateKey.from_private_bytes(key).sign(data))

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--manifest',required=True,type=Path)
    a.add_argument('--private-key',required=True,type=Path)
    a.add_argument('--signature',required=True,type=Path)
    x=a.parse_args();sign(x.manifest,x.private_key,x.signature)
if __name__=='__main__': main()
