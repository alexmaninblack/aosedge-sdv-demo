# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Minimal release-number continuity, independent of disposable run history."""

from .environment import EnvironmentError, atomic_json
from .status import read_json

LEDGER = ".local/release-continuity.json"
IDENTITIES = ("vdp", "brake", "tire")


def number(value):
    import re
    if not isinstance(value, str) or len(value) > 32 or not re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", value):
        raise EnvironmentError("RELEASE_VERSION_INVALID")
    return tuple(map(int, value.split(".")))


class ReleaseContinuity:
    def __init__(self, environment):
        self.environment = environment
        self.path = environment.root / LEDGER

    def read(self):
        if self.path.parent.is_symlink():
            raise EnvironmentError("RELEASE_CONTINUITY_UNSAFE")
        if self.path.is_symlink():
            raise EnvironmentError("RELEASE_CONTINUITY_UNSAFE")
        if not self.path.exists():
            return {"schemaVersion": 1, "versions": {}}
        value = read_json(self.path)
        if value.get("schemaVersion") != 1 or not isinstance(value.get("versions"), dict):
            raise EnvironmentError("RELEASE_CONTINUITY_INVALID")
        for identity, version in value["versions"].items():
            if identity not in IDENTITIES:
                raise EnvironmentError("RELEASE_IDENTITY_INVALID")
            number(version)
        return value

    def next(self, identity, observed=()):
        if identity not in IDENTITIES:
            raise EnvironmentError("RELEASE_IDENTITY_INVALID")
        floor = self.read()["versions"].get(identity, "3.0.0" if identity == "vdp" else "0.0.0")
        version = str(max(number(item) for item in [floor, *observed])[0] + 1) + ".0.0"
        number(version)
        return version

    def remember(self, identity, version):
        # Same existing single writer as lifecycle/artifact operations. No
        # credentials, Unit identities or old operational history are retained.
        if identity not in IDENTITIES:
            raise EnvironmentError("RELEASE_IDENTITY_INVALID")
        number(version)
        with self.environment._writer():
            value = self.read()
            previous = value["versions"].get(identity, "0.0.0")
            value["versions"][identity] = max((previous, version), key=number)
            self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            atomic_json(self.path, value)
        return version

    def reserve(self, identity, observed=()):
        with self.environment._writer():
            return self.remember(identity, self.next(identity, observed))
