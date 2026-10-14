"""OpenRouter browser authorization, stored in the native Windows credential vault."""
from __future__ import annotations
import base64
import hashlib
import json
import secrets
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SERVICE = 'QuietWriter-OpenRouter'
ACCOUNT = 'api-key'
API = 'https://openrouter.ai/api/v1'


def _vault():
    if sys.platform != 'win32':
        raise RuntimeError('Browserlogin met veilige opslag is momenteel alleen beschikbaar op Windows.')
    try:
        import keyring
        from keyring.backends.Windows import WinVaultKeyring
    except ImportError as exc:
        raise RuntimeError('Windows-sleutelopslag ontbreekt. Installeer de vereiste pakketten opnieuw.') from exc
    if not isinstance(keyring.get_keyring(), WinVaultKeyring):
        raise RuntimeError('Windows Credential Manager is niet beschikbaar.')
    return keyring


def stored_key() -> str:
    return _vault().get_password(SERVICE, ACCOUNT) or ''


def remove_key() -> bool:
    vault = _vault()
    if not vault.get_password(SERVICE, ACCOUNT):
        return False
    vault.delete_password(SERVICE, ACCOUNT)
    return True


def _api(method, path, *, key='', payload=None):
    headers = {'Accept': 'application/json', 'User-Agent': 'QuietWriter/1.5'}
    if key:
        headers['Authorization'] = 'Bearer ' + key
    data = None
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'OpenRouter HTTP {exc.code}: {exc.reason}') from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f'OpenRouter is niet bereikbaar: {exc.reason}') from exc


def verify_key(key: str) -> dict:
    return _api('GET', '/key', key=key).get('data', {})


def authorize(timeout_seconds=180) -> dict:
    """Requires explicit user click. Starts local callback and saves only after validation."""
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode('ascii')).digest()).decode('ascii').rstrip('=')
    nonce = secrets.token_urlsafe(24)
    result = {'code': None, 'error': None}
    complete = threading.Event()

    class Callback(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlsplit(self.path)
            parameters = urllib.parse.parse_qs(parsed.query)
            if parsed.path != '/callback' or not secrets.compare_digest(parameters.get('state', [''])[0], nonce):
                self.send_error(400, 'Invalid callback')
                return
            result['code'] = parameters.get('code', [None])[0]
            result['error'] = parameters.get('error', [None])[0]
            self.send_response(200 if result['code'] else 400)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            message = 'Autorisatie ontvangen. Je kunt dit tabblad sluiten.' if result['code'] else 'Autorisatie afgebroken.'
            self.wfile.write(f'<html><meta charset="utf-8"><body><h2>{message}</h2></body></html>'.encode('utf-8'))
            complete.set()

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Callback)
    server.timeout = 1
    port = server.server_address[1]
    callback = f'http://localhost:{port}/callback?state={urllib.parse.quote(nonce)}'
    query = urllib.parse.urlencode({'callback_url': callback, 'code_challenge': challenge, 'code_challenge_method': 'S256'})
    try:
        if not webbrowser.open('https://openrouter.ai/auth?' + query):
            raise RuntimeError('De browser kon niet worden geopend.')
        for _ in range(timeout_seconds):
            if complete.is_set():
                break
            server.handle_request()
        if not complete.is_set():
            raise RuntimeError('Geen autorisatie ontvangen binnen drie minuten.')
    finally:
        server.server_close()
    if not result['code']:
        raise RuntimeError('Autorisatie niet voltooid: ' + str(result['error'] or 'geen code'))
    token = _api('POST', '/auth/keys', payload={'code': result['code'], 'code_verifier': verifier, 'code_challenge_method': 'S256'}).get('key')
    if not isinstance(token, str) or not token.startswith('sk-or-'):
        raise RuntimeError('OpenRouter gaf geen geldige sleutel terug.')
    detail = verify_key(token)
    _vault().set_password(SERVICE, ACCOUNT, token)
    return detail
