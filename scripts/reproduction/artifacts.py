# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Digest cache and bounded private/public Drive downloads; no publication."""
import hashlib
import http.client
import json
import os
import re
import stat
import urllib.error
import urllib.request
from urllib.parse import urlsplit
import public_drive
from .core import LabError, require, regular, read_json, atomic_json

CHUNK = 4 * 2**20

def identity(path):
    info = regular(path).stat()
    return [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns]

def sha256(path, check=lambda: None):
    before = identity(path)
    value = hashlib.sha256()
    with path.open('rb') as stream:
        while data := stream.read(CHUNK):
            check()
            value.update(data)
    require(identity(path) == before, 'Artifact changed while hashing')
    return value.hexdigest()

def cached(storage, expected):
    path = storage.path('cache/sha256/' + expected['sha256'])
    receipt = path.with_suffix('.json')
    if not path.exists():
        return None
    current = identity(path)
    require(current[2] == expected['bytes'], 'Cached artifact size differs')
    if receipt.exists():
        row = read_json(receipt)
        if row == {'sha256': expected['sha256'], 'identity': current}:
            return path
    require(sha256(path, lambda: storage.check(reserve=0)) == expected['sha256'], 'Cached artifact digest differs')
    atomic_json(receipt, {'sha256': expected['sha256'], 'identity': identity(path)})
    return path

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise LabError('Drive redirect refused; credentials were not forwarded')

class Drive:
    def __init__(self, token):
        require(isinstance(token, str) and 0 < len(token) <= 4096 and not any(c.isspace() for c in token),
                'Invalid short-lived Drive authorization')
        self._token = token
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, file_id, suffix, start=None):
        require(re.fullmatch(r'[A-Za-z0-9_-]{10,200}', file_id), 'Invalid Drive file identifier')
        headers = {'Authorization': 'Bearer ' + self._token, 'Accept-Encoding': 'identity'}
        if start is not None:
            headers['Range'] = f'bytes={start}-'
        request = urllib.request.Request('https://www.googleapis.com/drive/v3/files/' + file_id + suffix, headers=headers)
        try:
            return self._opener.open(request, timeout=30)
        except urllib.error.HTTPError as exc:
            raise LabError(f'Drive request rejected (HTTP {exc.code}); no response body recorded') from None
        except (urllib.error.URLError, OSError) as exc:
            raise LabError('Drive connection interrupted; partial data retained for resume') from None

    def metadata(self, file_id):
        fields = 'id,size,sha256Checksum,version,parents,trashed,capabilities(canDownload)'
        with self.request(file_id, '?supportsAllDrives=true&fields=' + fields) as response:
            raw = response.read(16385)
        require(len(raw) <= 16384, 'Drive metadata too large')
        try:
            return json.loads(raw)
        except (ValueError, UnicodeError):
            raise LabError('Invalid Drive metadata') from None

    def content(self, file_id, start):
        return self.request(file_id, '?alt=media&supportsAllDrives=true', start)

def binding_entry(binding, release, name):
    require(set(binding) == {'schemaVersion', 'releaseDigest', 'folderId', 'files'} and binding['schemaVersion'] == 1,
            'Unsupported Drive binding')
    require(binding['releaseDigest'] == release.key, 'Drive binding belongs to another definition')
    require(re.fullmatch(r'[A-Za-z0-9_-]{10,200}', binding['folderId']), 'Invalid release folder identifier')
    require(name in binding['files'], 'No Drive file bound for this artifact')
    entry = binding['files'][name]
    require(set(entry) == {'fileId'}, 'Drive binding must not override artifact identity or carry credentials')
    require(re.fullmatch(r'[A-Za-z0-9_-]{10,200}', entry['fileId']), 'Invalid artifact file identifier')
    expected = release.value['artifacts'].get(name)
    require(expected and 'bytes' in expected and 'sha256' in expected, 'Artifact has no pinned byte identity')
    return entry['fileId'], binding['folderId'], expected

def download(storage, drive, file_id, folder_id, expected, progress=lambda *args: None):
    hit = cached(storage, expected)
    if hit:
        progress('ARTIFACT_REUSED', expected['sha256'][:12])
        return hit
    meta = drive.metadata(file_id)
    require(type(meta) is dict, 'Invalid Drive artifact metadata')
    require(meta.get('parents') == [folder_id], 'Drive file is not in the bound release folder')
    require(meta.get('id') == file_id and meta.get('trashed') is False and
            meta.get('capabilities', {}).get('canDownload') is True, 'Drive download not permitted')
    require(str(meta.get('size')) == str(expected['bytes']) and
            meta.get('sha256Checksum') == expected['sha256'] and meta.get('version'), 'Drive artifact metadata differs from release')
    def unchanged():
        require(drive.metadata(file_id) == meta, 'Drive artifact changed during download; not promoted')
    return receive(storage, expected, lambda offset: drive.content(file_id, offset), progress, unchanged)


def public_binding(value, lock_digest, roles):
    try:
        return public_drive.binding(value, lock_digest, roles)
    except public_drive.PublicDriveError as error:
        raise LabError(str(error)) from None


def download_public(storage, url, expected, progress=lambda *args: None):
    """Source lock authenticates bytes; never invent private API metadata."""
    try:
        public_drive.link(url)
        hit = cached(storage, expected)
        if hit:
            progress('ARTIFACT_REUSED', expected['sha256'][:12])
            return hit
        client = public_drive.Client()
        return receive(storage, expected, lambda offset: client.open(url, offset), progress)
    except public_drive.PublicDriveError as error:
        raise LabError(str(error)) from None

def receive(storage, expected, open_content, progress, before_promote=lambda: None):
    """Shared bounded/resumable transport; callers establish input authority."""
    path = storage.path('cache/sha256/' + expected['sha256'])
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    partial = path.with_suffix('.part')
    offset = regular(partial).stat().st_size if partial.exists() else 0
    require(offset <= expected['bytes'], 'Partial artifact exceeds expected size')
    storage.check(additional=expected['bytes'] - offset)
    if offset < expected['bytes']:
        with open_content(offset) as response:
            require(response.status in (200, 206), 'Unexpected download status')
            if response.status == 206:
                require(response.headers.get('Content-Range') == f'bytes {offset}-{expected["bytes"]-1}/{expected["bytes"]}',
                        'Download byte range differs; partial data preserved')
            else:
                require(offset == 0, 'Download ignored resume range; partial data preserved')
            require(response.headers.get('Content-Encoding', 'identity') == 'identity', 'Unexpected content encoding')
            declared = response.headers.get('Content-Length')
            require(declared is None or declared == str(expected['bytes']-offset), 'Download length differs')
            descriptor = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
            try:
                with os.fdopen(descriptor, 'ab') as stream:
                    info = os.fstat(stream.fileno())
                    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == offset,
                            'Partial artifact changed before append')
                    while data := response.read(CHUNK):
                        storage.check(additional=len(data))
                        require(offset + len(data) <= expected['bytes'], 'Download exceeds expected size')
                        stream.write(data)
                        offset += len(data)
                        progress('DOWNLOAD_BYTES', offset)
                    stream.flush()
                    os.fsync(stream.fileno())
            except (OSError, urllib.error.URLError, http.client.HTTPException):
                raise LabError('Download interrupted; partial data retained') from None
    require(offset == expected['bytes'], 'Download incomplete; partial data retained')
    require(sha256(partial, lambda: storage.check(reserve=0)) == expected['sha256'], 'Downloaded artifact digest differs; not promoted')
    before_promote()
    storage.check(reserve=0)
    os.rename(partial, path)
    atomic_json(path.with_suffix('.json'), {'sha256': expected['sha256'], 'identity': identity(path)})
    progress('ARTIFACT_VERIFIED', expected['sha256'][:12])
    return path

def public_wheel(storage, expected, progress=lambda *args: None):
    """Only public hash-locked PyPI wheels, with no ambient proxy/auth use."""
    url = urlsplit(expected['url'])
    require(url.scheme == 'https' and url.netloc == 'files.pythonhosted.org'
            and url.path.startswith('/packages/') and not url.query and not url.fragment
            and url.path.rsplit('/', 1)[-1] == expected['file']
            and re.fullmatch(r'[A-Za-z0-9_.+-]+\.whl', expected['file'])
            and re.fullmatch(r'[a-f0-9]{64}', expected['sha256'])
            and type(expected['bytes']) is int and 0 < expected['bytes'] < 512*2**20,
            'Invalid pinned public wheel')
    hit = cached(storage, expected)
    if hit:
        progress('ARTIFACT_REUSED', expected['sha256'][:12])
        return hit
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    def content(offset):
        request = urllib.request.Request(expected['url'], headers={
            'Accept-Encoding': 'identity', 'Range': f'bytes={offset}-'})
        try:
            return opener.open(request, timeout=30)
        except urllib.error.HTTPError as exc:
            raise LabError(f'Public wheel request rejected (HTTP {exc.code}); no response body recorded') from None
        except (urllib.error.URLError, OSError):
            raise LabError('Public wheel download interrupted; partial data retained') from None
    return receive(storage, expected, content, progress)
