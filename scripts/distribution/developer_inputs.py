# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Build-only sealed results, never a runtime trust or public checkpoint format."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import stat

from installation_inputs import parse
from native_bundle import BundleError


@dataclass(frozen=True)
class DeveloperInputs:
    raw: bytes
    key: str

    @classmethod
    def load(cls, path, expected):
        path = Path(path)
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise BundleError('Linked developer result seal')
        info = path.stat()
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_mode & 0o7022
                or not 0 < info.st_size <= 2**20):
            raise BundleError('Unsafe developer result seal')
        raw = path.read_bytes()
        if not re.fullmatch('[a-f0-9]{64}', expected) or hashlib.sha256(raw).hexdigest() != expected:
            raise BundleError('Developer result seal digest differs')
        result = cls(raw, expected)
        result.value()  # Validate before exposing even the checkpoint subset.
        return result

    def value(self):
        if hashlib.sha256(self.raw).hexdigest() != self.key:
            raise BundleError('Developer result seal changed')
        value = parse(self.raw)
        if (not isinstance(value, dict) or set(value) != {
                'schemaVersion', 'kind', 'checkpoint', 'release', 'sources', 'upstreamBuilds'}
                or type(value['schemaVersion']) is not int or value['schemaVersion'] != 1
                or value['kind'] != 'developer-build-results'
                or not isinstance(value['sources'], dict) or not value['sources']
                or not isinstance(value['upstreamBuilds'], dict) or not value['upstreamBuilds']
                or not all(isinstance(k, str) and re.fullmatch('[a-z][a-z0-9-]*', k)
                           and isinstance(v, str) and re.fullmatch('[a-f0-9]{64}', v)
                           for k, v in value['upstreamBuilds'].items())):
            raise BundleError('Invalid developer result seal')
        return value

    def release_bytes(self):
        return (json.dumps(self.value()['release'], sort_keys=True, indent=2)+'\n').encode()
