# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Explicit Dropbox publisher with immutable destinations and resumable sessions."""
import hashlib
import http.client
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from release_automation import CampaignError, atomic, digest, private_file, read, require, safe
from .artifacts import identity
from .dropbox_public import observe, public_link

BLOCK = 4 * 2**20
CHUNK = 32 * 2**20
SCOPES = frozenset(('account_info.read', 'files.metadata.read', 'files.content.write',
                    'sharing.read', 'sharing.write'))
RPC = frozenset(('users/get_current_account', 'users/get_space_usage', 'files/get_metadata',
                 'files/create_folder_v2', 'sharing/list_shared_links',
                 'sharing/create_shared_link_with_settings'))
CONTENT = frozenset(('files/upload_session/start', 'files/upload_session/append_v2',
                     'files/upload_session/finish'))


def folder_path(value):
    require(isinstance(value, str) and len(value) <= 500 and
            re.fullmatch(r'(?:/[A-Za-z0-9][A-Za-z0-9 _.-]{0,100}){1,8}', value) and
            all(part not in ('.', '..') and part == part.strip() for part in value.split('/')[1:]),
            'DROPBOX_FOLDER_PATH_INVALID')
    return value


def automatic(selected):
    return selected.get('provider') == 'dropbox' and 'credentialFile' in selected


def selection(selected):
    fields = {'provider', 'credentialFile', 'folderPath', 'accountId'}
    require(set(selected) in (fields, fields | {'attempt'}), 'DELIVERY_SELECTION_INVALID')
    require(type(selected.get('attempt', 1)) is int and 1 <= selected.get('attempt', 1) <= 9,
            'DELIVERY_ATTEMPT_INVALID')
    safe(selected['credentialFile']); folder_path(selected['folderPath'])
    require(isinstance(selected['accountId'], str) and
            re.fullmatch(r'dbid:[A-Za-z0-9_-]{10,100}', selected['accountId']),
            'DROPBOX_ACCOUNT_ID_INVALID')
    return selected


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise CampaignError('DROPBOX_AUTHENTICATED_REDIRECT_REFUSED')


class APIError(CampaignError):
    def __init__(self, status, error=None):
        super().__init__('DROPBOX_HTTP_' + str(status))
        self.status = status
        # Retain only documented discriminators/offsets, never raw messages or tokens.
        self.tags = set()
        self.correct_offset = None
        def visit(value):
            if isinstance(value, dict):
                tag = value.get('.tag')
                if isinstance(tag, str) and re.fullmatch('[a-z_]{1,60}', tag):
                    self.tags.add(tag)
                offset = value.get('correct_offset')
                if type(offset) is int and offset >= 0:
                    self.correct_offset = offset
                for item in value.values():
                    if isinstance(item, dict): visit(item)
        visit(error)


def response_json(opener, request):
    try:
        with opener.open(request, timeout=120) as response:
            require(response.status == 200, 'DROPBOX_RESPONSE_STATUS_INVALID')
            raw = response.read(2**20 + 1)
            require(len(raw) <= 2**20, 'DROPBOX_METADATA_TOO_LARGE')
            return json.loads(raw) if raw else None
    except HTTPError as error:
        try:
            raw = error.read(65537)
            body = json.loads(raw) if len(raw) <= 65536 else {}
        except (ValueError, OSError):
            body = {}
        finally:
            error.close()
        raise APIError(error.code, body.get('error') if isinstance(body, dict) else None) from None
    except (OSError, URLError, http.client.HTTPException):
        raise CampaignError('DROPBOX_CONNECTION_INTERRUPTED') from None
    except (ValueError, UnicodeError):
        raise CampaignError('DROPBOX_RESPONSE_INVALID') from None


def token_request(opener, fields):
    result = response_json(opener, Request('https://api.dropboxapi.com/oauth2/token',
        data=urlencode(fields).encode(), method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded'}))
    require(isinstance(result, dict), 'DROPBOX_TOKEN_RESPONSE_INVALID')
    return result


class Client:
    def __init__(self, credentials, account_id):
        self.credentials = read(credentials)
        required = {'schemaVersion', 'appKey', 'refreshToken', 'accountId', 'scopes'}
        require(set(self.credentials) == required and self.credentials['schemaVersion'] == 1 and
                self.credentials['accountId'] == account_id and
                set(self.credentials['scopes']) == SCOPES and
                re.fullmatch('[A-Za-z0-9_-]{5,100}', self.credentials['appKey']) and
                isinstance(self.credentials['refreshToken'], str) and
                0 < len(self.credentials['refreshToken']) <= 4096 and
                not any(c.isspace() for c in self.credentials['refreshToken']),
                'DROPBOX_CREDENTIAL_BINDING_INVALID')
        self.account_id = account_id
        self.opener = build_opener(ProxyHandler({}), NoRedirect())
        self.token, self.expires = '', 0

    def access_token(self):
        if time.monotonic() >= self.expires:
            result = token_request(self.opener, dict(grant_type='refresh_token',
                refresh_token=self.credentials['refreshToken'], client_id=self.credentials['appKey']))
            token, seconds = result.get('access_token'), result.get('expires_in')
            require(isinstance(token, str) and 0 < len(token) <= 4096 and
                    not any(c.isspace() for c in token) and type(seconds) is int and seconds > 120,
                    'DROPBOX_TOKEN_RESPONSE_INVALID')
            self.token, self.expires = token, time.monotonic() + seconds - 60
        return self.token

    def call(self, route, value=None, *, data=None):
        content = route in CONTENT
        require(content or route in RPC, 'DROPBOX_ENDPOINT_REFUSED')
        headers = {'Authorization': 'Bearer ' + self.access_token()}
        if content:
            require(isinstance(data, bytes) and len(data) <= CHUNK, 'DROPBOX_CHUNK_INVALID')
            headers.update({'Content-Type': 'application/octet-stream',
                            'Dropbox-API-Arg': json.dumps(value, ensure_ascii=True)})
            host, body = 'content.dropboxapi.com', data
        else:
            headers['Content-Type'] = 'application/json'
            host, body = 'api.dropboxapi.com', json.dumps(value).encode()
        # Never retry an authenticated mutation based on a transport/status error.
        return response_json(self.opener, Request('https://' + host + '/2/' + route,
                                                  data=body, method='POST', headers=headers))

    def metadata(self, path):
        try:
            return self.call('files/get_metadata', {'path': path})
        except APIError as error:
            if error.status == 409 and 'not_found' in error.tags: return None
            raise

    def preflight(self, folder, size):
        account = self.call('users/get_current_account')
        require(account.get('account_id') == self.account_id, 'DROPBOX_ACCOUNT_CHANGED')
        meta = self.metadata(folder_path(folder))
        require(meta and meta.get('.tag') == 'folder' and meta.get('id') and
                meta.get('path_lower') == folder.lower(), 'DROPBOX_RELEASE_FOLDER_UNAVAILABLE')
        space = self.call('users/get_space_usage')
        allocated = space.get('allocation', {}).get('allocated')
        require(type(allocated) is int and type(space.get('used')) is int and
                allocated - space['used'] >= size, 'DROPBOX_CAPACITY_UNAVAILABLE')
        return meta['id']

    def links(self, path):
        value, rows = {'path': path, 'direct_only': True}, []
        for _ in range(20):
            page = self.call('sharing/list_shared_links', value)
            require(isinstance(page, dict) and isinstance(page.get('links'), list),
                    'DROPBOX_LINK_RESPONSE_INVALID')
            rows.extend(page['links'])
            if page.get('has_more') is False: return rows
            require(isinstance(page.get('cursor'), str), 'DROPBOX_LINK_CURSOR_INVALID')
            value = {'cursor': page['cursor']}
        raise CampaignError('DROPBOX_LINK_PAGE_LIMIT')


def normalize_link(url):
    require(isinstance(url, str), 'DROPBOX_LINK_RESPONSE_INVALID')
    parsed = urlsplit(url)
    rows = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
    require(len(rows) == len(dict(rows)), 'DROPBOX_LINK_RESPONSE_INVALID')
    return public_link(urlunsplit((parsed.scheme, parsed.netloc, parsed.path,
        urlencode([(k, v) for k, v in rows if k != 'dl'] + [('dl', '1')]), parsed.fragment)))


def checked_link(meta, remote):
    require(meta.get('.tag') == 'file' and meta.get('id') == remote['id'] and
            meta.get('path_lower') == remote['path_lower'] and meta.get('size') == remote['size'] and
            meta.get('rev') == remote['rev'] and
            meta.get('link_permissions', {}).get('resolved_visibility', {}).get('.tag') == 'public' and
            meta.get('link_permissions', {}).get('allow_download') is True,
            'DROPBOX_PUBLIC_LINK_NOT_CONFIRMED')
    return normalize_link(meta.get('url'))


def public_url(client, remote):
    rows = client.links(remote['id'])
    require(len(rows) <= 1, 'DROPBOX_DUPLICATE_DIRECT_LINKS')
    if not rows:
        try:
            client.call('sharing/create_shared_link_with_settings', {
                'path': remote['id'], 'settings': {'requested_visibility': 'public',
                                                 'allow_download': True}})
        except APIError as error:
            if not (error.status == 409 and 'shared_link_already_exists' in error.tags): raise
        rows = client.links(remote['id'])
    require(len(rows) == 1, 'DROPBOX_PUBLIC_LINK_RECONCILIATION_REQUIRED')
    return checked_link(rows[0], remote)


def check_remote(meta, path, expected, content_hash, saved=None):
    require(isinstance(meta, dict) and meta.get('.tag') == 'file' and
            meta.get('path_lower') == path.lower() and meta.get('name') == expected['file'] and
            type(meta.get('size')) is int and meta['size'] == expected['bytes'] and
            meta.get('content_hash') == content_hash and
            isinstance(meta.get('id'), str) and meta['id'].startswith('id:') and
            isinstance(meta.get('rev'), str) and re.fullmatch('[a-f0-9]{9,64}', meta['rev']),
            'DROPBOX_IMMUTABLE_DESTINATION_CONFLICT')
    facts = {key: meta[key] for key in ('id', 'rev', 'path_lower', 'name', 'size', 'content_hash')}
    require(saved is None or facts == saved, 'DROPBOX_PUBLISHED_REVISION_CHANGED')
    return facts


def body_hash(data):
    # The API's upload content_hash covers this request body, not the complete
    # session. Verify the complete file separately through returned metadata.
    return hashlib.sha256(b''.join(hashlib.sha256(data[offset:offset + BLOCK]).digest()
                                  for offset in range(0, len(data), BLOCK))).hexdigest()


def source_hashes(source, expected, verified, check):
    before = identity(source)
    require(before[2] == expected['bytes'], 'DROPBOX_SOURCE_SIZE_CHANGED')
    if verified is not None:
        require(verified == {'identity': before, 'sha256': expected['sha256']},
                'DROPBOX_VERIFIED_SOURCE_CHANGED')
    whole, blocks = hashlib.sha256(), hashlib.sha256()
    check()
    with source.open('rb') as stream:
        while True:
            block = stream.read(BLOCK)
            if not block: break
            blocks.update(hashlib.sha256(block).digest())
            if verified is None: whole.update(block)
    require(identity(source) == before and (verified is not None or whole.hexdigest() == expected['sha256']),
            'DROPBOX_SOURCE_BYTES_CHANGED')
    check()
    return before, blocks.hexdigest()


def binding(selected, expected, folder_id):
    selection(selected)
    require(re.fullmatch(r'AosEdge-SDV-Lab-\d+\.\d+\.\d+-rc\.\d+\.dmg', expected['file']) and
            type(expected['bytes']) is int and expected['bytes'] > 0 and
            re.fullmatch('[a-f0-9]{64}', expected['sha256']), 'DROPBOX_ARTIFACT_INVALID')
    return dict(descriptorDigest=digest(expected), accountId=selected['accountId'],
                folderId=folder_id, path=selected['folderPath'] + '/' + expected['file'])


def upload(client, source, expected, selected, state_path, *, check=lambda: None,
           progress=lambda *args: None, verified_source=None):
    """Session IDs are private operational state, never included in release facts."""
    source, state_path = safe(source), safe(state_path)
    require(source.is_file() and source.stat().st_nlink == 1, 'DROPBOX_SOURCE_NOT_REGULAR')
    folder_id = client.preflight(selected['folderPath'], 0)
    bound = binding(selected, expected, folder_id)
    before = identity(source)
    if state_path.exists():
        state = read(state_path)
        require(state.get('binding') == bound and state.get('identity') == before and
                re.fullmatch('[a-f0-9]{64}', state.get('contentHash', '')),
                'DROPBOX_UPLOAD_BINDING_CHANGED')
        if verified_source is not None:
            require(verified_source == {'identity': before, 'sha256': expected['sha256']},
                    'DROPBOX_VERIFIED_SOURCE_CHANGED')
    else:
        before, content_hash = source_hashes(source, expected, verified_source, check)
        state = dict(binding=bound, identity=before, contentHash=content_hash,
                     phase='prepared', offset=0, inflight=0)
        atomic(state_path, state)
    def save(**values):
        state.update(values); atomic(state_path, state)
    meta = client.metadata(bound['path'])
    if meta is not None:
        facts = check_remote(meta, bound['path'], expected, state['contentHash'], state.get('remote'))
        save(phase='committed', remote=facts, offset=expected['bytes'], inflight=0)
        progress('UPLOAD_REUSED', expected['bytes'])
        return facts
    require('remote' not in state and state['phase'] != 'committed', 'DROPBOX_PUBLISHED_FILE_MISSING')
    client.preflight(selected['folderPath'], expected['bytes'])
    if 'sessionId' not in state:
        require(state['phase'] in ('prepared', 'starting'), 'DROPBOX_SESSION_STATE_INVALID')
        # Start carries no bytes: a lost response cannot create a published file.
        save(phase='starting')
        result = client.call('files/upload_session/start', {'close': False, 'content_hash': body_hash(b'')}, data=b'')
        session = result.get('session_id')
        require(isinstance(session, str) and 0 < len(session) <= 1024 and
                not any(c.isspace() for c in session), 'DROPBOX_SESSION_RESPONSE_INVALID')
        save(phase='uploading', sessionId=session, offset=0, inflight=0)
    offset, pending = state['offset'], state['inflight']
    require(type(offset) is int and type(pending) is int and
            0 <= offset <= expected['bytes'] and 0 <= pending <= CHUNK and
            offset + pending <= expected['bytes'], 'DROPBOX_SESSION_OFFSET_INVALID')
    # Probe the journaled cursor with zero bytes before resuming any lost append.
    try:
        client.call('files/upload_session/append_v2', {
            'cursor': {'session_id': state['sessionId'], 'offset': offset}, 'close': False,
            'content_hash': body_hash(b'')}, data=b'')
    except APIError as error:
        require(error.status == 409 and 'incorrect_offset' in error.tags and pending > 0 and
                error.correct_offset == offset + pending, 'DROPBOX_SESSION_RECONCILIATION_REQUIRED')
        offset = error.correct_offset
    save(phase='uploading', offset=offset, inflight=0)
    last_check = time.monotonic()
    with source.open('rb') as stream:
        stream.seek(offset)
        while offset < expected['bytes']:
            require(identity(source) == before, 'DROPBOX_SOURCE_CHANGED_DURING_UPLOAD')
            if time.monotonic() - last_check >= 30:
                check(); last_check = time.monotonic()
            data = stream.read(min(CHUNK, expected['bytes'] - offset))
            require(data, 'DROPBOX_SOURCE_TRUNCATED')
            save(inflight=len(data))
            client.call('files/upload_session/append_v2', {
                'cursor': {'session_id': state['sessionId'], 'offset': offset}, 'close': False,
                'content_hash': body_hash(data)}, data=data)
            offset += len(data)
            save(offset=offset, inflight=0)
            progress('UPLOAD_BYTES', offset)
    require(identity(source) == before, 'DROPBOX_SOURCE_CHANGED_DURING_UPLOAD')
    check(); save(phase='finishing')
    client.call('files/upload_session/finish', {
        'cursor': {'session_id': state['sessionId'], 'offset': offset},
        'commit': {'path': bound['path'], 'mode': 'add', 'autorename': False,
                   'strict_conflict': True, 'mute': True}, 'content_hash': body_hash(b'')}, data=b'')
    facts = check_remote(client.metadata(bound['path']), bound['path'], expected, state['contentHash'])
    save(phase='committed', remote=facts)
    return facts


def publish(client, source, expected, selected, state_path, **options):
    remote = upload(client, source, expected, selected, state_path, **options)
    url = public_url(client, remote)
    head = observe(url, expected['bytes'])
    check_remote(client.metadata(remote['id']), selected['folderPath'] + '/' + expected['file'],
                 expected, remote['content_hash'], remote)
    return dict(provider='dropbox', automaticUpload=True, downloadURL=url, remote=remote,
                accountId=selected['accountId'], folderPath=selected['folderPath'], metadata=head)


def verify(client, expected, selected, facts):
    require(facts.get('automaticUpload') is True and facts.get('accountId') == selected['accountId'] and
            facts.get('folderPath') == selected['folderPath'], 'DROPBOX_PUBLICATION_BINDING_CHANGED')
    remote = facts['remote']
    client.preflight(selected['folderPath'], 0)
    check_remote(client.metadata(remote['id']), selected['folderPath'] + '/' + expected['file'],
                 expected, remote['content_hash'], remote)
    require(public_url_readonly(client, remote) == facts['downloadURL'], 'DROPBOX_PUBLIC_LINK_CHANGED')
    require(observe(facts['downloadURL'], expected['bytes']) == facts['metadata'],
            'DROPBOX_PUBLIC_METADATA_CHANGED')


def public_url_readonly(client, remote):
    rows = client.links(remote['id'])
    require(len(rows) == 1, 'DROPBOX_PUBLIC_LINK_RECONCILIATION_REQUIRED')
    return checked_link(rows[0], remote)


def reconcile(client, source, expected, selected, state_path):
    folder_id = client.preflight(selected['folderPath'], 0)
    bound = binding(selected, expected, folder_id)
    meta = client.metadata(bound['path'])
    if not state_path.exists():
        require(meta is None, 'DROPBOX_UNRECORDED_DESTINATION_REQUIRES_REVIEW')
        return True  # No session or payload operation was attempted.
    state = read(state_path)
    require(state.get('binding') == bound and state.get('identity') == identity(source),
            'DROPBOX_UPLOAD_BINDING_CHANGED')
    if meta is not None:
        check_remote(meta, bound['path'], expected, state['contentHash'], state.get('remote'))
    else:
        require('remote' not in state and state.get('phase') != 'committed',
                'DROPBOX_PUBLISHED_FILE_MISSING')
    return True  # upload() reconciles a private cursor before transmitting bytes.
