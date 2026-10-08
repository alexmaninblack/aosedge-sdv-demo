# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Explicit maintainer Drive transport; never called by a build or installer."""
import argparse
import http.client
import json
from pathlib import Path
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

from . import artifacts
from .core import ROOT, LabError, Release, Storage, atomic_json, digest, read_json, require

ORIGIN = 'https://www.googleapis.com'
API = ORIGIN + '/drive/v3/'
FIELDS = 'id,name,size,sha256Checksum,version,parents,trashed,shared,webViewLink,capabilities(canDownload)'
UPLOAD_CHUNK = 32 * 2**20


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_-]{10,200}', value), 'Invalid Drive identifier')
    return value


def descriptor(path):
    value = read_json(path)
    require(set(value) == {'schemaVersion', 'productVersion', 'status', 'file', 'bytes', 'sha256',
                          'buildKey', 'producerRevision', 'manifestSha256', 'signing', 'notarized'},
            'Unexpected delivery descriptor fields')
    require(value['schemaVersion'] == 1 and value['status'] == 'ENGINEERING_CANDIDATE_NOT_QUALIFIED'
            and value['signing'] == 'apple-development-local-only' and value['notarized'] is False,
            'Unsupported candidate delivery state')
    require(re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+-rc\.[0-9]+', value['productVersion'])
            and value['file'] == 'AosEdge-SDV-Lab-' + value['productVersion'] + '.dmg'
            and type(value['bytes']) is int and value['bytes'] > 0, 'Invalid candidate identity')
    for field in ('sha256', 'buildKey', 'manifestSha256', 'producerRevision'):
        require(re.fullmatch('[a-f0-9]{' + ('40' if field == 'producerRevision' else '64') + '}', value[field]),
                'Invalid candidate provenance digest')
    return value


class Client:
    def __init__(self, gcloud, account):
        self.gcloud, self.account = gcloud, account
        self.token, self.expires = '', 0
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), artifacts.NoRedirect())

    def access_token(self):
        if time.monotonic() >= self.expires:
            result = subprocess.run([self.gcloud, 'auth', 'print-access-token', '--account=' + self.account],
                                    capture_output=True, timeout=60)
            require(result.returncode == 0, 'Google CLI authorization unavailable; complete the approved login')
            token = result.stdout.decode().strip()
            require(0 < len(token) <= 4096 and not any(c.isspace() for c in token), 'Invalid authorization')
            self.token, self.expires = token, time.monotonic() + 1800
        return self.token

    def request(self, method, url, data=None, headers=None):
        parsed = urllib.parse.urlsplit(url)
        require(parsed.scheme == 'https' and parsed.netloc == 'www.googleapis.com'
                and not parsed.fragment and parsed.path.startswith(('/drive/v3/', '/upload/drive/v3/')),
                'Refusing untrusted Drive endpoint')
        request = urllib.request.Request(url, data=data, method=method, headers={
            'Authorization': 'Bearer ' + self.access_token(), 'Accept-Encoding': 'identity', **(headers or {})})
        try:
            return self.opener.open(request, timeout=120)
        except urllib.error.HTTPError as exc:
            if exc.code in (308, 404, 409, 429, 500, 502, 503, 504):
                return exc
            raise LabError(f'Drive HTTP {exc.code}; response body omitted') from None
        except (OSError, urllib.error.URLError, http.client.HTTPException):
            raise LabError('Drive connection interrupted; reconcile the recorded file ID before retry') from None

    def json(self, method, url, value=None):
        with self.request(method, url, None if value is None else json.dumps(value).encode(),
                          {'Content-Type': 'application/json'}) as response:
            if response.status == 404:
                return None
            require(response.status in (200, 201), f'Drive HTTP {response.status}; response body omitted')
            raw = response.read(65537)
            require(len(raw) <= 65536, 'Oversized Drive metadata')
            return json.loads(raw)

    def metadata(self, file_id):
        return self.json('GET', API + 'files/' + identifier(file_id) + '?fields=' + FIELDS)

    def content(self, file_id, start):
        return self.request('GET', API + 'files/' + identifier(file_id) + '?alt=media',
                            headers={'Range': f'bytes={start}-'})

    def named_files(self, folder, name):
        require(re.fullmatch(r'[A-Za-z0-9_.-]+', name), 'Unsafe release file name')
        query = f"'{identifier(folder)}' in parents and name = '{name}' and trashed = false"
        result = self.json('GET', API + 'files?' + urllib.parse.urlencode({
            'q': query, 'pageSize': 2, 'fields': 'nextPageToken,files(' + FIELDS + ')'}))
        require(not result.get('nextPageToken') and len(result['files']) <= 1,
                'Duplicate release file names require explicit reconciliation')
        return result['files']

    def preflight(self, folder, expected):
        about = self.json('GET', API + 'about?fields=user(emailAddress),storageQuota,maxUploadSize')
        require(about['user']['emailAddress'] == self.account, 'Google account differs from explicit selection')
        quota = about['storageQuota']
        require(int(about['maxUploadSize']) >= expected['bytes'], 'Drive upload limit too small')
        if 'limit' in quota:
            require(int(quota['limit']) - int(quota['usage']) >= expected['bytes'], 'Insufficient Drive capacity')
        metadata = self.json('GET', API + 'files/' + identifier(folder)
                             + '?fields=id,mimeType,trashed,shared,capabilities(canAddChildren)')
        require(metadata and metadata.get('mimeType') == 'application/vnd.google-apps.folder'
                and metadata.get('trashed') is False and metadata.get('shared') is False
                and metadata.get('capabilities', {}).get('canAddChildren') is True,
                'Expected a private writable release folder; sharing is never changed automatically')


def check_remote(meta, file_id, folder, expected):
    require(meta and meta.get('id') == file_id and meta.get('name') == expected['file']
            and meta.get('parents') == [folder] and meta.get('trashed') is False
            and meta.get('shared') is False and meta.get('capabilities', {}).get('canDownload') is True
            and meta.get('sha256Checksum') == expected['sha256']
            and str(meta.get('size')) == str(expected['bytes']) and meta.get('version'),
            'Remote file differs from reviewed candidate; no overwrite or duplicate permitted')


def acknowledged(response, total):
    require(response.status == 308, 'Unexpected resumable upload status')
    value = response.headers.get('Range')
    if value is None:
        return 0
    match = re.fullmatch(r'bytes=0-(\d+)', value)
    require(match and int(match[1]) < total, 'Invalid acknowledged upload range')
    return int(match[1]) + 1


def upload(client, source, expected, folder, state_path, check=lambda: None, progress=lambda *x: None):
    """Persist only a non-secret ID/intent. Session capabilities remain in memory."""
    before = artifacts.identity(source)
    require(before[2] == expected['bytes'], 'Source size differs from reviewed descriptor')
    binding = {'descriptorDigest': digest(expected), 'folderId': identifier(folder)}
    if state_path.exists():
        intent = read_json(state_path)
        require(set(intent) == {'descriptorDigest', 'folderId', 'fileId'}
                and all(intent[k] == v for k, v in binding.items()), 'Delivery intent binding differs')
        file_id = identifier(intent['fileId'])
        meta = client.metadata(file_id)
        if meta:
            check_remote(meta, file_id, folder, expected)
            progress('UPLOAD_REUSED', expected['bytes'])
            return meta
    else:
        existing = client.named_files(folder, expected['file'])
        if existing:
            meta = existing[0]
            file_id = identifier(meta['id'])
            check_remote(meta, file_id, folder, expected)
            atomic_json(state_path, {**binding, 'fileId': file_id})
            progress('UPLOAD_REUSED', expected['bytes'])
            return meta
        file_id = identifier(client.json('GET', API + 'files/generateIds?count=1&space=drive&type=files')['ids'][0])
        atomic_json(state_path, {**binding, 'fileId': file_id})
    require(artifacts.sha256(source, check) == expected['sha256'], 'Source digest differs from reviewed descriptor')
    progress('SOURCE_VERIFIED', expected['bytes'])
    url = ORIGIN + '/upload/drive/v3/files?uploadType=resumable&fields=' + FIELDS
    body = json.dumps({'id': file_id, 'name': expected['file'], 'parents': [folder],
                       'mimeType': 'application/x-apple-diskimage'}).encode()
    with client.request('POST', url, body, {'Content-Type': 'application/json',
                        'X-Upload-Content-Type': 'application/x-apple-diskimage',
                        'X-Upload-Content-Length': str(expected['bytes'])}) as response:
        require(response.status in (200, 201), f'Upload initiation HTTP {response.status}; intent preserved')
        session = response.headers.get('Location')
        require(isinstance(session, str), 'Missing upload session')
    offset, recoveries = 0, 0
    with source.open('rb') as stream:
        while offset < expected['bytes']:
            check()
            require(artifacts.identity(source) == before, 'Source changed during upload')
            stream.seek(offset)
            data = stream.read(min(UPLOAD_CHUNK, expected['bytes'] - offset))
            try:
                response = client.request('PUT', session, data, {
                    'Content-Type': 'application/x-apple-diskimage',
                    'Content-Range': f'bytes {offset}-{offset + len(data)-1}/{expected["bytes"]}'})
            except LabError:
                response = None
            if response is None or response.status in (429, 500, 502, 503, 504):
                if response is not None:
                    response.close()
                recoveries += 1
                require(recoveries <= 3, 'Upload interrupted repeatedly; file intent preserved')
                # Observe server acknowledgement before any retransmission.
                time.sleep(2)
                response = client.request('PUT', session, b'', {'Content-Range': f'bytes */{expected["bytes"]}'})
            with response:
                if response.status in (200, 201):
                    offset = expected['bytes']
                else:
                    next_offset = acknowledged(response, expected['bytes'])
                    require(offset <= next_offset <= offset + len(data), 'Upload acknowledgement outside sent range')
                    if next_offset == offset:
                        recoveries += 1
                        require(recoveries <= 3, 'Upload made no progress; intent preserved')
                    offset = next_offset
            progress('UPLOAD_BYTES', offset)
    require(artifacts.identity(source) == before, 'Source changed during upload')
    meta = client.metadata(file_id)
    check_remote(meta, file_id, folder, expected)
    return meta


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('upload', 'download'))
    parser.add_argument('--descriptor', type=Path, required=True)
    parser.add_argument('--storage', type=Path, required=True)
    parser.add_argument('--folder-id', required=True)
    parser.add_argument('--account', required=True)
    parser.add_argument('--gcloud', default='gcloud')
    parser.add_argument('--source', type=Path)
    parser.add_argument('--file-id')
    args = parser.parse_args(argv)
    try:
        expected = descriptor(args.descriptor)
        storage = Storage(args.storage, Release(), 'operator')
        client = Client(args.gcloud, args.account)
        last = [0]
        def progress(stage, value):
            now = time.monotonic()
            if now - last[0] >= 15 or 'BYTES' not in stage or value == expected['bytes']:
                print(json.dumps({'stage': stage, 'value': value}), flush=True)
                last[0] = now
        with storage.locked():
            if args.action == 'upload':
                require(args.source is not None and args.file_id is None, 'Upload requires source, not file ID')
                source = artifacts.regular(args.source)
                require(source.stat().st_dev == storage.volume['device'], 'Source must be on the selected external volume')
                client.preflight(args.folder_id, expected)
                meta = upload(client, source, expected, args.folder_id, storage.path('upload-intent.json'),
                              lambda: storage.check(reserve=0), progress)
                atomic_json(storage.path('upload-receipt.json'), {
                    'schemaVersion': 1, 'status': 'PRIVATE_DELIVERY_NOT_QUALIFICATION',
                    'descriptorDigest': digest(expected), 'artifact': expected,
                    'folderId': args.folder_id, 'fileId': meta['id'], 'driveVersion': meta['version'],
                    'webViewLink': meta.get('webViewLink')})
                print(json.dumps({'status': 'UPLOADED_VERIFIED', 'fileId': meta['id'], 'url': meta.get('webViewLink')}))
            else:
                require(args.file_id and args.source is None, 'Download requires file ID, not local source')
                reused = artifacts.cached(storage, expected) is not None
                path = artifacts.download(storage, client, identifier(args.file_id), identifier(args.folder_id), expected, progress)
                atomic_json(storage.path('download-receipt.json'), {
                    'schemaVersion': 1, 'status': 'CACHE_REUSED' if reused else 'TRANSFER_VERIFIED',
                    'descriptorDigest': digest(expected), 'fileId': args.file_id, 'folderId': args.folder_id,
                    'sha256': expected['sha256'], 'bytes': expected['bytes'],
                    'qualificationClaimed': False})
                print(json.dumps({'status': 'DOWNLOADED_VERIFIED', 'path': str(path)}))
        return 0
    except (LabError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        # Exception details may include a session capability or credential response.
        print(json.dumps({'status': 'DELIVERY_FAILED', 'reason': str(exc) if isinstance(exc, LabError)
                          else type(exc).__name__ + '; details omitted'}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
