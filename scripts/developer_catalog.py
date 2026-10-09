# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Bounded developer catalog reader; embedded verbatim in prepare-macos.sh.

Standard library only. The public pin authenticates one immutable catalog record,
not a mutable filename, owner-supplied checksum or Google account name.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

PIN = {
    'releaseId': '1.2.0-rc.1-source-factory-r1',
    'recordSha256': 'c4c5639edc09ddc363784b8fcf3c97fb5b5ff99b4815e8421bb2858b657d0da5',
    'lockDigests': {
        'buildInputs': 'f69665e4218111c3f13f35a8ecd6fe2ecdbc7dd3c6c36c46f650f31c479a77b0',
        'simulation': '18769de4641b3b7e2955123094ba7ac983a6af1a734a8fe25c8fd100f3d24e5e'},
    'sourceFiles': {
        'workspace/dependencies/carla-macos-arm64-r1.lock.json': '37311be6f3c1a18893bd61a112e42eddb7c457041168845e39a98c7b67ce151f',
        'workspace/dependencies/developer-factory41-r1.lock.json': '734927ac6c1f8efaf464884773fca37f117ef8ec96f5107ff17a254e6251fe0f',
        'workspace/releases/1.2.0-rc.1-source-factory-build-chain.json': '8ef497219dcbd11d06201330b6f429e07cdb6d672c66bbaad6ede8731334cfd6',
        'workspace/releases/1.2.0-rc.1-source-factory-delivery.json': '33cc8b296bfe76be301b33a170789539a3154dec7a8ad62a3333fff8e9a3ebdc',
        'workspace/releases/kit028-setup042.json': '5951852da7158a63802c1045fe0f37719f90d549b2e70f5f7ab63c5c9841ad13'},
}
ROLES = {'buildInputs': {'vehicle-bases', 'factory-image'},
         'simulation': {'carla-runtime', 'host-support', 'gateway-sdk'}}
LIMIT = 1024 * 1024
FOLDER = 'AosEdge SDV Lab Artifacts'
NAME = 'release-index.json'
FIELDS = 'id,name,mimeType,size,sha256Checksum,version,trashed,parents,capabilities(canDownload)'


class CatalogError(Exception):
    def __init__(self, message, code=12):
        super().__init__(message)
        self.code = code


def require(condition, message):
    if not condition:
        raise CatalogError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def json_bytes(raw):
    require(len(raw) <= LIMIT, 'Catalog metadata exceeds the supported size.')
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'Duplicate JSON fields are not supported.')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def identifier(value):
    require(isinstance(value, str) and re.fullmatch('[A-Za-z0-9_-]{10,200}', value), 'Invalid catalog object identity.')
    return value


def safe_path(value):
    path = Path(value)
    require(path.is_absolute() and '..' not in path.parts
            and not any(p.is_symlink() for p in (path, *path.parents)), 'Unsafe preparation file location.')
    return path


def read_local(value):
    path = safe_path(value)
    require(path.is_file() and path.stat().st_size <= LIMIT, 'Prepared release metadata is missing. Run the preparation wizard first.')
    return json_bytes(path.read_bytes())


def validate_binding(value, group):
    require(isinstance(value, dict) and set(value) == {'schemaVersion', 'lockDigest', 'folderId', 'files'}
            and type(value['schemaVersion']) is int and value['schemaVersion'] == 1
            and value['lockDigest'] == PIN['lockDigests'][group]
            and isinstance(value['files'], dict) and set(value['files']) == ROLES[group],
            'Input selection is incompatible with this preparation script. Obtain the matching release inputs.')
    identifier(value['folderId'])
    for file_id in value['files'].values():
        identifier(file_id)
    return value


def validate_record(entry):
    require(isinstance(entry, dict) and entry.get('id') == PIN['releaseId']
            and digest(entry) == PIN['recordSha256'],
            'The selected release record differs from the trusted source pin. No input selection was saved.')
    require(entry['sourceFiles'] == PIN['sourceFiles'] and set(entry['dependencyGroups']) == set(ROLES),
            'Release source requirements differ.')
    for group, row in entry['dependencyGroups'].items():
        validate_binding(row['binding'], group)
        require(set(row['packages']) == ROLES[group], 'Release input list is incomplete.')
    return entry


def select_record(catalog):
    require(isinstance(catalog, dict) and set(catalog) == {'schemaVersion', 'product', 'catalogRevision', 'releases'}
            and type(catalog['schemaVersion']) is int and catalog['schemaVersion'] == 1,
            'Unsupported release catalog format. Download the current preparation script from README B1.')
    require(catalog['product'] == 'aosedge-sdv-lab'
            and type(catalog['catalogRevision']) is int and catalog['catalogRevision'] >= 1
            and isinstance(catalog['releases'], list) and 0 < len(catalog['releases']) <= 1000,
            'Invalid release catalog.')
    ids = []
    for entry in catalog['releases']:
        require(isinstance(entry, dict) and isinstance(entry.get('id'), str), 'Invalid release record.')
        ids.append(entry['id'])
    require(len(set(ids)) == len(ids), 'Duplicate release IDs require release-owner reconciliation.')
    require(PIN['releaseId'] in ids,
            'No compatible release is available for this preparation script. Contact the release owner; no newer release was substituted.')
    return validate_record(catalog['releases'][ids.index(PIN['releaseId'])])


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Client:
    def __init__(self, gcloud, account):
        require(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', account or ''), 'Google account is missing or invalid.')
        try:
            result = subprocess.run([gcloud, 'auth', 'print-access-token', '--account=' + account],
                                    capture_output=True, text=True, timeout=60,
                                    env={**os.environ, 'CLOUDSDK_CORE_DISABLE_FILE_LOGGING': 'true'})
        except (OSError, subprocess.TimeoutExpired):
            raise CatalogError('Google CLI did not respond. Check connectivity; no new login was started.') from None
        if result.returncode:
            if any(word in result.stderr.lower() for word in ('auth login', 'invalid_grant', 'reauthentication', 'credentials have been revoked')):
                raise CatalogError('Google authorization is missing or expired.', 10)
            raise CatalogError('Google token refresh failed. Check connectivity/CLI; existing authorization was preserved.')
        self.token = result.stdout.strip()
        require(0 < len(self.token) <= 4096 and not any(c.isspace() for c in self.token), 'Google CLI returned an invalid authorization response.')
        self.opener = urllib.request.build_opener(NoRedirect())
        require(self.get('about?fields=user(emailAddress)')['user']['emailAddress'].lower() == account.lower(),
                'Google account differs from the selected account.')

    def raw(self, relative, limit=65536):
        # All paths are assembled here from fixed strings and validated IDs.
        request = urllib.request.Request('https://www.googleapis.com/drive/v3/' + relative,
            headers={'Authorization': 'Bearer ' + self.token, 'Accept-Encoding': 'identity'})
        try:
            with self.opener.open(request, timeout=20) as response:
                raw = response.read(limit + 1)
            require(len(raw) <= limit, 'Drive metadata exceeds the supported size.')
            return raw
        except urllib.error.HTTPError as error:
            if error.code == 401:
                raise CatalogError('Google authorization needs renewal.', 10) from None
            reason = ''
            try:
                reason = json_bytes(error.read(65536))['error']['errors'][0]['reason']
            except (ValueError, KeyError, TypeError, IndexError, CatalogError):
                pass
            if error.code == 403 and reason == 'insufficientPermissions':
                raise CatalogError('Existing Google authorization does not include Drive access.', 11) from None
            raise CatalogError('Drive access check failed (HTTP %s). Ask the release owner to grant this Google account access to the SDV Lab catalog and inputs. No archive was downloaded.' % error.code) from None
        except (OSError, urllib.error.URLError):
            raise CatalogError('Drive could not be reached. Check connectivity and rerun; existing authorization was preserved.') from None

    def get(self, relative):
        return json_bytes(self.raw(relative))

    def metadata(self, file_id):
        return self.get('files/' + identifier(file_id) + '?supportsAllDrives=true&fields=' + FIELDS)

    def unique(self, query, label):
        result = self.get('files?' + urllib.parse.urlencode({
            'q': query, 'pageSize': 2, 'includeItemsFromAllDrives': 'true', 'supportsAllDrives': 'true',
            'fields': 'nextPageToken,incompleteSearch,files(' + FIELDS + ')'}))
        require(not result.get('nextPageToken') and not result.get('incompleteSearch')
                and len(result['files']) <= 1, 'Ambiguous ' + label + '. Ask the release owner to reconcile duplicates; none was selected.')
        require(len(result['files']) == 1, 'The SDV Lab ' + label + ' is not available to this account. Ask the release owner for access; no JSON file is required from you.')
        row = result['files'][0]
        identifier(row['id'])
        return row

    def discover(self):
        folder = self.unique("name = '" + FOLDER + "' and mimeType = 'application/vnd.google-apps.folder' and trashed = false", 'artifact folder')
        row = self.unique("'" + folder['id'] + "' in parents and name = '" + NAME + "' and trashed = false", 'release catalog')
        require(row['name'] == NAME and row['mimeType'] == 'application/json'
                and not row.get('trashed', True) and folder['id'] in row.get('parents', [])
                and row.get('capabilities', {}).get('canDownload') is True
                and 0 < int(row['size']) <= LIMIT and re.fullmatch('[a-f0-9]{64}', row['sha256Checksum']),
                'The release catalog is not a readable bounded JSON file.')
        raw = self.raw('files/' + identifier(row['id']) + '?alt=media&supportsAllDrives=true', LIMIT)
        require(len(raw) == int(row['size']) and hashlib.sha256(raw).hexdigest() == row['sha256Checksum'], 'Release catalog transfer checksum differs.')
        after = self.metadata(row['id'])
        require(all(after.get(k) == row.get(k) for k in ('id', 'name', 'mimeType', 'size', 'sha256Checksum', 'version', 'parents', 'trashed')),
                'Release catalog changed during discovery. Rerun the wizard; no selection was saved.')
        return select_record(json_bytes(raw))

    def check_inputs(self, bindings, record=None):
        for group, binding in bindings.items():
            folder = self.metadata(binding['folderId'])
            require(folder['mimeType'] == 'application/vnd.google-apps.folder' and not folder.get('trashed', True), 'Input folder is unavailable.')
            for role, file_id in binding['files'].items():
                row = self.metadata(file_id)
                require(row['id'] == file_id and not row.get('trashed', True)
                        and binding['folderId'] in row.get('parents', [])
                        and row.get('capabilities', {}).get('canDownload') is True, 'An input is not downloadable from its declared folder. Ask the release owner for access.')
                if record:
                    expected = record['dependencyGroups'][group]['packages'][role]
                    require(row['name'] == expected['file'] and int(row['size']) == expected['bytes']
                            and row['sha256Checksum'] == expected['sha256'], 'An input no longer matches its release. Contact the release owner; no archive was downloaded.')


def private_directory(path, create=False):
    path = safe_path(path)
    if create:
        path.mkdir(mode=0o700, exist_ok=True)
    info = path.stat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700, 'Unsafe catalog state directory.')
    return path


def save_generation(state, record):
    parent = private_directory(state)
    for part in ('catalog', PIN['recordSha256']):
        parent = private_directory(parent / part, create=True)
    target = safe_path(parent / ('automatic' if record else 'manual'))
    files = {'source-requirements.json': PIN}
    if record:
        files.update({'release.json': record,
                      'developer-inputs.drive.json': record['dependencyGroups']['buildInputs']['binding'],
                      'simulation-inputs.drive.json': record['dependencyGroups']['simulation']['binding']})
    if target.exists():
        private_directory(target)
        require({p.name for p in target.iterdir()} == set(files), 'Prepared catalog files are incomplete or unexpected; preserved for inspection.')
        for name, value in files.items():
            path = safe_path(target/name)
            info = path.stat()
            require(info.st_uid == os.getuid() and info.st_nlink == 1 and stat.S_IMODE(info.st_mode) == 0o600
                    and read_local(path) == value, 'Prepared catalog files changed; preserved for inspection.')
        return
    temporary = Path(tempfile.mkdtemp(prefix='.pending-', dir=parent))
    try:
        for name, value in files.items():
            fd = os.open(temporary/name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(canonical(value) + b'\n')
        os.rename(temporary, target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)  # This invocation's small generated directory only.


def source_check(receipt, root):
    require(read_local(receipt) == PIN, 'Prepared source selection differs. Rerun the current preparation script before building.')
    for name, expected in PIN['sourceFiles'].items():
        path = safe_path(Path(root)/name)
        require(path.is_file() and path.stat().st_size <= LIMIT and hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                'Cloned source requirements differ from the prepared release. Stop here and rerun preparation for matching sources; do not download or build inputs.')
    print('Source compatibility: PASS — cloned dependency records and producer plan match the prepared release.')


def main(args):
    if len(args) == 2 and args[0] == '--check-source':
        source_check(args[1], Path(__file__).resolve().parents[1])
        return 0
    if args == ['--requirements']:
        print(json.dumps(PIN, sort_keys=True))
        return 0
    require(len(args) == 7, 'Invalid catalog helper invocation.')
    gcloud, account, build, simulation, mode, state, advanced = args
    require(mode in ('local', 'remote') and advanced in ('yes', 'no'), 'Invalid catalog check mode.')
    record = None
    if advanced == 'yes':
        bindings = {g: validate_binding(read_local(p), g) for g, p in (('buildInputs', build), ('simulation', simulation))}
    elif mode == 'local':
        generation = safe_path(Path(state)/'catalog'/PIN['recordSha256']/'automatic')
        record = validate_record(read_local(generation/'release.json'))
        bindings = {g: validate_binding(read_local(p), g) for g, p in (('buildInputs', build), ('simulation', simulation))}
        require(all(v == record['dependencyGroups'][g]['binding'] for g, v in bindings.items()), 'Prepared bindings differ from the trusted release.')
    if mode == 'local':
        print('Input file structure checked; Drive access is not checked in --check mode.')
        return 0
    client = Client(gcloud, account)
    if advanced == 'no':
        print('Finding compatible SDV Lab release…')
        record = client.discover()
        bindings = {g: row['binding'] for g, row in record['dependencyGroups'].items()}
    client.check_inputs(bindings, record)
    save_generation(state, record)
    if record:
        print('Selected release: ' + record['productVersion'] + ' — source-Factory engineering candidate (not qualified).')
        print('CARLA, controller base and supporting inputs: available. Input files prepared automatically.')
    print('Drive account and access to all five inputs checked (metadata only; no archives downloaded).')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except CatalogError as error:
        print(str(error))
        sys.exit(error.code)
    except (ValueError, KeyError, TypeError, IndexError, OSError, RecursionError):
        print('Catalog preparation failed: malformed metadata or unavailable local state. No archive was downloaded; existing files were preserved.')
        sys.exit(12)
