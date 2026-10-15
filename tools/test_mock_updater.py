"""Demonstrate a mock update against a disposable fixture.

Run alongside mock_update_server.py in a separate Python terminal.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from quietwriter.update_test_updater import create_fixture, apply_mock_update


def demo(base_url='http://127.0.0.1:8765', fault=False):
    if not base_url.startswith('http://127.0.0.1:'):
        raise ValueError('Only local test server allowed')
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    def fetch(path):
        with urllib.request.urlopen(base_url + path, timeout=5) as response:
            return response.read(1024 * 1024 + 1)
    manifest = fetch('/manifest.json')
    signature = fetch('/manifest.sig')
    key = bytes.fromhex(fetch('/test-public-key.hex').decode())
    Ed25519PublicKey.from_public_bytes(key).verify(signature, manifest)
    info = json.loads(manifest)
    if info['url'] != base_url + '/mock-update.zip':
        raise ValueError('Mock archive URL does not match local test server')
    body = fetch('/mock-update.zip')
    if len(body) != info['size'] or hashlib.sha256(body).hexdigest() != info['sha256']:
        raise ValueError('Mock archive failed verification')
    with tempfile.TemporaryDirectory(prefix='qw-updater-demo-') as temp:
        target = create_fixture(Path(temp))
        archive = Path(temp) / 'mock-update.zip'
        archive.write_bytes(body)
        print('Before:', (target / 'version.txt').read_text().strip())
        try:
            apply_mock_update(target, archive, expected_sha256=info['sha256'], fail_after=1 if fault else None)
        except ValueError as exc:
            print('Simulated failure:', exc)
            if not fault:
                raise
        result = (target / 'version.txt').read_text().strip()
        print('After:', result)
        if result != ('1.5.0' if fault else '1.5.1'):
            raise AssertionError('Unexpected fixture version')
        print('PASS: disposable fixture only; automatically cleaned up')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fault', action='store_true', help='Inject failure and verify rollback')
    args = parser.parse_args()
    demo(fault=args.fault)
