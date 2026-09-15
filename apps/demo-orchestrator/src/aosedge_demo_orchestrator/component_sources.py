# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Pinned unsigned VDP sources; no historical signing credential."""

import os
import tempfile
from .environment import EnvironmentError, atomic_json
from .status import read_json

# Hashes of the exact inner archives in the separately pinned legacy bundles.
# A runtime-generated adjacent manifest cannot replace these reviewed pins.
UNSIGNED_SHA = {
    "1.0.16": "d6757035407968553f27fe7e93caae00bbab72bb13fc4f3527a37700e8f34fa1",
    "2.0.0": "8728a0779cb1665910f2953457a1140ccfcda07ee236f215836193ff0d6b1a90",
    "3.0.0": "746a38d76848f86ed6d4c4150893c95eb36cf044cf6f44c7a6f57506d72e7411",
}


def source(service, version, *, materialize=False):
    from .component_build import PROFILE_BASES
    from .components import MAX_ARCHIVE, archive_files, sha
    bases = {entry[0]: entry[1] for entry in PROFILE_BASES.values()}
    if version not in bases or version not in UNSIGNED_SHA:
        raise EnvironmentError("COMPONENT_SOURCE_NOT_PINNED")
    service._directory(version)  # Existing catalog boundary.
    parent = service.root / ".source-profiles"
    destination = parent / version
    expected = dict(schemaVersion=1, version=version, legacyArchiveSha256=bases[version],
        unsignedSha256=UNSIGNED_SHA[version], trust="REVIEWED_SOURCE_DIGESTS")

    def checked(path, digest):
        if (path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ARCHIVE):
            raise EnvironmentError("COMPONENT_SOURCE_PATH_UNSAFE")
        raw = path.read_bytes()
        if sha(raw) != digest:
            raise EnvironmentError("COMPONENT_SOURCE_DIGEST_MISMATCH")
        return raw

    if parent.is_symlink() or destination.is_symlink():
        raise EnvironmentError("COMPONENT_SOURCE_PATH_UNSAFE")
    if destination.exists():
        path = destination / "package.tar.gz"
        if read_json(destination / "source.json") != expected:
            raise EnvironmentError("COMPONENT_SOURCE_MANIFEST_MISMATCH")
        checked(path, expected["unsignedSha256"])
        info, payload = service._inspect(version, path=path)
    else:
        path = service._directory(version) / ("vdp-" + version + "-deployment-bundle.tar.gz")
        outer = archive_files(checked(path, bases[version]))
        if set(outer) != {"batch.tar.gz", "config.yaml", "package.sign"}:
            raise EnvironmentError("COMPONENT_SOURCE_ENVELOPE_INVALID")
        unsigned = outer["batch.tar.gz"]
        inner = archive_files(unsigned)
        if sha(unsigned) != expected["unsignedSha256"] or inner.get("config.yaml") != outer["config.yaml"]:
            raise EnvironmentError("COMPONENT_SOURCE_UNSIGNED_DIGEST_MISMATCH")
        info, payload = service._inspect(version, path=path)
        if materialize and not info["problems"]:
            parent.mkdir(mode=0o700, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=".source-", dir=parent) as temporary:
                from pathlib import Path
                candidate = Path(temporary) / "candidate"
                candidate.mkdir(mode=0o700)
                target = candidate / "package.tar.gz"
                target.write_bytes(unsigned)
                target.chmod(0o444)
                atomic_json(candidate / "source.json", expected)
                os.rename(candidate, destination)
    if info["problems"]:
        raise EnvironmentError("COMPONENT_SOURCE_STRUCTURE_INVALID")
    return dict(info, source=expected, signatureVerification="NOT_APPLICABLE",
                sourceIntegrity="VERIFIED_PINNED_DIGESTS"), payload
