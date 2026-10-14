"""Local-only update simulation server, never a production update source.

Run: python tools/mock_update_server.py --port 8765
Use a second Python terminal to execute tools/test_mock_updater.py.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from quietwriter.update_test_updater import create_mock_update


def serve(port: int) -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    with TemporaryDirectory(prefix='qw-mock-update-server-') as work:
        archive = create_mock_update(Path(work) / 'mock-update.zip')
        data = archive.read_bytes()
        # Ephemeral test key: discarded at shutdown. Never accepted by production verifier.
        key = Ed25519PrivateKey.generate()
        pub = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        manifest = json.dumps({'schema': 1, 'version': '1.5.1', 'url': f'http://127.0.0.1:{port}/mock-update.zip',
                               'filename': 'mock-update.zip', 'size': len(data),
                               'sha256': hashlib.sha256(data).hexdigest()}, sort_keys=True).encode()
        signature = key.sign(manifest)
        responses = {'/manifest.json': (manifest, 'application/json'), '/manifest.sig': (signature, 'application/octet-stream'),
                     '/mock-update.zip': (data, 'application/zip'), '/test-public-key.hex': (pub.hex().encode(), 'text/plain')}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path not in responses:
                    self.send_error(404)
                    return
                body, kind = responses[self.path]
                self.send_response(200)
                self.send_header('Content-Type', kind)
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(body)

        class LocalServer(ThreadingHTTPServer):
            def server_bind(self):
                if self.server_address[0] != '127.0.0.1':
                    raise ValueError('Only loopback binding allowed')
                super().server_bind()

        with LocalServer(('127.0.0.1', port), Handler) as httpd:
            print(f'Mock update server on http://127.0.0.1:{port}/manifest.json', flush=True)
            print('Temporary TEST signing key; real QuietWriter will never accept this key.', flush=True)
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Local-only disposable update server')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('Choose port 1024-65535')
    serve(args.port)
