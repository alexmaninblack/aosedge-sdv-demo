# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One-time PKCE connection; credentials never appear in arguments or output."""
import argparse
import base64
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import stat
import time
from urllib.parse import parse_qsl, urlencode, urlsplit
from urllib.request import ProxyHandler, build_opener

from release_automation import CampaignError, atomic, code, read, require, safe
from .dropbox_delivery import APIError, Client, NoRedirect, SCOPES, folder_path, token_request

CALLBACK = 'http://127.0.0.1:53687/dropbox/callback'


def authorization(app_key, state, verifier):
    require(isinstance(app_key, str) and re.fullmatch('[A-Za-z0-9_-]{5,100}', app_key),
            'DROPBOX_APP_KEY_INVALID')
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    return 'https://www.dropbox.com/oauth2/authorize?' + urlencode(dict(
        client_id=app_key, response_type='code', token_access_type='offline',
        redirect_uri=CALLBACK, state=state, code_challenge=challenge,
        code_challenge_method='S256', scope=' '.join(sorted(SCOPES))))


def in_git_tree(path):
    return any((parent / '.git').exists() for parent in path.parents)


def credential_target(path):
    path = safe(path)
    require(not path.exists(), 'DROPBOX_CREDENTIALS_ALREADY_CONFIGURED')
    require(not in_git_tree(path), 'DROPBOX_CREDENTIALS_MUST_BE_OUTSIDE_GIT')
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.parent.stat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and
            stat.S_IMODE(info.st_mode) == 0o700, 'DROPBOX_PRIVATE_CREDENTIAL_DIRECTORY_REQUIRED')
    return path


def callback_values(target, state):
    parsed = urlsplit(target)
    require(parsed.path == '/dropbox/callback' and not parsed.fragment,
            'DROPBOX_OAUTH_CALLBACK_INVALID')
    rows = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
    values = dict(rows)
    require(len(rows) == len(values) and set(values) <= {'state', 'code', 'error', 'error_description'} and
            hmac.compare_digest(values.get('state', ''), state), 'DROPBOX_OAUTH_STATE_INVALID')
    require('error' not in values and isinstance(values.get('code'), str) and
            0 < len(values['code']) <= 4096, 'DROPBOX_OAUTH_DENIED')
    return values['code']


def initialize_folder(client, folder):
    folder_path(folder)
    meta = client.metadata(folder)
    if meta is None:
        try:
            client.call('files/create_folder_v2', {'path': folder, 'autorename': False})
        except APIError as error:
            if not (error.status == 409 and 'conflict' in error.tags): raise
        meta = client.metadata(folder)
    require(meta and meta.get('.tag') == 'folder' and meta.get('path_lower') == folder.lower(),
            'DROPBOX_RELEASE_FOLDER_UNAVAILABLE')
    client.preflight(folder, 0)


def connect(app_key, destination, folder, *, emit=print, timeout=600):
    destination = credential_target(destination)
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(64)
    accepted = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass  # Request URLs contain a one-time code.
        def do_GET(self):
            try:
                value = callback_values(self.path, state)
            except CampaignError:
                self.send_response(400); self.end_headers(); self.wfile.write(b'Authorization was not accepted.')
                return
            accepted.append(value)
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.end_headers(); self.wfile.write(b'Dropbox authorization received. You can close this tab.')
    with HTTPServer(('127.0.0.1', 53687), Handler) as server:
        server.timeout = 1
        emit(authorization(app_key, state, verifier), flush=True)
        deadline = time.monotonic() + timeout
        while not accepted and time.monotonic() < deadline:
            server.handle_request()
        require(len(accepted) == 1, 'DROPBOX_OAUTH_TIMED_OUT')
    result = token_request(build_opener(ProxyHandler({}), NoRedirect()), dict(
        grant_type='authorization_code', code=accepted[0], client_id=app_key,
        code_verifier=verifier, redirect_uri=CALLBACK))
    require(isinstance(result.get('refresh_token'), str) and
            0 < len(result['refresh_token']) <= 4096 and
            isinstance(result.get('account_id'), str) and
            re.fullmatch(r'dbid:[A-Za-z0-9_-]{10,100}', result['account_id']) and
            set(result.get('scope', '').split()) == SCOPES,
            'DROPBOX_OFFLINE_AUTHORIZATION_INCOMPLETE')
    atomic(destination, dict(schemaVersion=1, appKey=app_key, refreshToken=result['refresh_token'],
                             accountId=result['account_id'], scopes=sorted(SCOPES)))
    initialize_folder(Client(destination, result['account_id']), folder)
    emit('DROPBOX_CONNECTED: private credentials saved; release folder verified.', flush=True)


def main(argv=None):
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('connect', 'status', 'prepare-folder', 'selection'))
    parser.add_argument('--credentials', type=Path, required=True)
    parser.add_argument('--folder-path', default='/releases')
    parser.add_argument('--app-key')
    args = parser.parse_args(argv)
    try:
        if args.action == 'connect':
            connect(args.app_key, args.credentials.absolute(), args.folder_path)
        else:
            require(args.app_key is None, 'DROPBOX_STATUS_APP_KEY_NOT_REQUIRED')
            selected = read(args.credentials.absolute())
            client=Client(args.credentials.absolute(), selected['accountId'])
            if args.action=='prepare-folder':
                initialize_folder(client,args.folder_path)
            else:
                client.preflight(args.folder_path, 0)
            if args.action=='selection':
                print(json.dumps(dict(provider='dropbox',credentialFile=str(args.credentials.absolute()),
                                      accountId=selected['accountId'],folderPath=args.folder_path),indent=2))
            else:
                print('DROPBOX_CONNECTED: account and release folder verified; no file uploaded.')
        return 0
    except (Exception, KeyboardInterrupt) as error:
        print('STOP: ' + code(error), file=__import__('sys').stderr)
        return 2
