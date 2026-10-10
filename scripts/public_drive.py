# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Anonymous, bounded Drive downloads; no OAuth, API keys, cookies or publication.

The caller authenticates catalog records against a source pin and archive bytes
against a lock. A public URL is a locator, never an integrity authority.
"""
from html.parser import HTMLParser
import http.client
import re
import urllib.error
import urllib.parse
import urllib.request

HOSTS = {'drive.google.com', 'drive.usercontent.google.com'}
HTML_LIMIT = 65536


class PublicDriveError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise PublicDriveError(message)


def bounded_read(response, limit):
    try:
        return response.read(limit)
    except (OSError, urllib.error.URLError, http.client.HTTPException):
        raise PublicDriveError('Public download response was interrupted; no new selection was accepted.') from None


def link(url, confirmation=False):
    """Only persistent download links (including Google's resource key)."""
    require(isinstance(url, str) and len(url) <= 4096 and not any(c.isspace() for c in url),
            'Invalid public download link.')
    p = urllib.parse.urlsplit(url)
    require(p.scheme == 'https' and p.netloc in HOSTS and not p.fragment
            and ((p.netloc == 'drive.google.com' and p.path == '/uc')
                 or (p.netloc == 'drive.usercontent.google.com' and p.path == '/download')),
            'Unsupported public download endpoint; no request was sent.')
    try:
        pairs = urllib.parse.parse_qsl(p.query, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        raise PublicDriveError('Invalid public download query.') from None
    fields = dict(pairs)
    allowed = {'id', 'export', 'resourcekey'} | ({'confirm', 'uuid', 'at'} if confirmation else set())
    require(len(fields) == len(pairs) and set(fields) <= allowed
            and fields.get('export') == 'download'
            and re.fullmatch(r'[A-Za-z0-9_-]{10,200}', fields.get('id', ''))
            and all(re.fullmatch(r'[A-Za-z0-9_.:-]{1,2048}', v) for v in fields.values()),
            'Invalid public download parameters.')
    return fields


def binding(value, lock_digest, roles):
    require(isinstance(value, dict) and set(value) == {'schemaVersion', 'transport', 'lockDigest', 'files'}
            and type(value['schemaVersion']) is int and value['schemaVersion'] == 2
            and value['transport'] == 'google-drive-public' and value['lockDigest'] == lock_digest
            and isinstance(value['files'], dict) and set(value['files']) == set(roles),
            'Public input selection differs from the source lock.')
    for url in value['files'].values():
        link(url)
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class DownloadForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.forms = []
        self.fields = {}
        self.duplicate = False
        self.text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'form':
            self.active = a.get('id') == 'download-form'
            if self.active:
                self.forms.append(a)
        if tag == 'input' and self.active:
            name = a.get('name')
            if name:
                self.duplicate |= name in self.fields or a.get('type') != 'hidden'
                self.fields[name] = a.get('value', '')

    def handle_endtag(self, tag):
        if tag == 'form':
            self.active = False

    def handle_data(self, data):
        self.text.append(data)


def confirmation_url(raw, original):
    form = DownloadForm()
    try:
        form.feed(raw.decode('utf-8'))
    except UnicodeError:
        raise PublicDriveError('Unexpected download page; no file was saved.') from None
    text = ' '.join(form.text).lower()
    if 'too many users' in text or 'download quota' in text:
        raise PublicDriveError('Google Drive temporarily limited downloads. Retry later; no login or duplicate copy is needed.')
    require("can't scan this file for viruses" in text
            and not any(word in text for word in ('infected', 'malware', 'violates', 'abusive'))
            and len(form.forms) == 1 and not form.duplicate,
            'The public file is unavailable or needs sign-in, or Google returned an unsupported warning. Contact the release owner; no file was saved.')
    a = form.forms[0]
    require(a.get('action') == 'https://drive.usercontent.google.com/download'
            and a.get('method', 'get').lower() == 'get', 'Unsupported download confirmation form.')
    fields = form.fields
    require(fields.get('id') == original['id'] and fields.get('export') == 'download'
            and fields.get('confirm') == 't', 'Download confirmation does not match the requested file.')
    if original.get('resourcekey'):
        require(fields.get('resourcekey', original['resourcekey']) == original['resourcekey'], 'Download resource key changed.')
        fields['resourcekey'] = original['resourcekey']
    url = a['action'] + '?' + urllib.parse.urlencode(fields)
    link(url, confirmation=True)
    return url


class Client:
    def __init__(self):
        # No ambient proxy authentication, browser cookie jar, .netrc or CLI.
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def open(self, url, start=None, end=None):
        original = link(url)
        confirmed = False
        for _ in range(5):
            fields = link(url, confirmation=confirmed)
            require(fields['id'] == original['id'], 'Public redirect changed the requested file.')
            require(fields.get('resourcekey') == original.get('resourcekey'), 'Public redirect changed the resource key.')
            headers = {'Accept-Encoding': 'identity', 'Accept-Language': 'en', 'User-Agent': 'AosEdge-SDV-Lab/3'}
            if start is not None:
                require(type(start) is int and start >= 0 and (end is None or type(end) is int and end >= start), 'Invalid download range.')
                headers['Range'] = f'bytes={start}-' + (str(end) if end is not None else '')
            req = urllib.request.Request(url, headers=headers)
            try:
                response = self.opener.open(req, timeout=30)
            except urllib.error.HTTPError as error:
                response = error
            except (OSError, urllib.error.URLError, http.client.HTTPException):
                raise PublicDriveError('Public Drive connection interrupted; rerun to resume verified input acquisition.') from None
            if response.status in (301, 302, 303, 307, 308):
                with response:
                    next_url = urllib.parse.urljoin(url, response.headers.get('Location', ''))
                if urllib.parse.urlsplit(next_url).hostname == 'accounts.google.com':
                    raise PublicDriveError('This release is not publicly downloadable. Contact the release owner; Google login is not required by this workflow.')
                link(next_url, confirmation=confirmed)
                url = next_url
                continue
            if response.status not in (200, 206):
                with response:
                    code = response.status
                raise PublicDriveError(f'Public Drive download failed (HTTP {code}). Check access/connectivity or retry later for a quota limit; no login was started.')
            if response.headers.get('Content-Encoding', 'identity') != 'identity':
                response.close()
                raise PublicDriveError('Unexpected download content encoding.')
            content_type = response.headers.get('Content-Type', '').split(';')[0].strip().lower()
            if content_type in ('text/html', 'application/xhtml+xml'):
                with response:
                    raw = bounded_read(response, HTML_LIMIT + 1)
                require(len(raw) <= HTML_LIMIT and not confirmed, 'Unexpected or repeated download page; no file was saved.')
                url = confirmation_url(raw, original)
                confirmed = True
                continue
            if content_type not in ('application/octet-stream', 'application/json', 'application/gzip',
                                     'application/x-gzip', 'application/x-apple-diskimage', 'application/zip'):
                response.close()
                raise PublicDriveError('Unexpected public file type; no file was saved.')
            return response
        raise PublicDriveError('Too many public download redirects; no file was saved.')

    def catalog(self, url, limit=1024 * 1024):
        with self.open(url) as response:
            require(response.status == 200, 'Unexpected catalog range response.')
            raw = bounded_read(response, limit + 1)
        require(0 < len(raw) <= limit, 'Public catalog is empty or exceeds its size limit.')
        return raw

    def probe(self, url, expected):
        # Availability/length only. Full integrity belongs to the later consumer.
        with self.open(url, 0, 0) as response:
            require(response.status == 206 and response.headers.get('Content-Range') == f'bytes 0-0/{expected["bytes"]}',
                    'Public input size/range differs; no archive was downloaded.')
            require(len(bounded_read(response, 2)) == 1, 'Public input availability check failed.')
