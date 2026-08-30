# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Pin the exact installed aos-prov 5.4.2 sources used by host wrappers."""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import stat


LOCK = Path(__file__).with_name("aos-prov-5.4.2-source-lock.json")


class SourceLockError(RuntimeError):
    pass


def _regular_nonsymlink(path: Path, label: str) -> None:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise SourceLockError(f"{label} is not a regular non-symlink file")
    if metadata.st_nlink != 1:
        raise SourceLockError(f"{label} must have exactly one hard link")


def verify() -> Path:
    _regular_nonsymlink(LOCK, "aos-prov source lock")
    payload = json.loads(LOCK.read_text(encoding="utf-8"))
    if set(payload) != {"schema", "distribution", "version", "files"}:
        raise SourceLockError("aos-prov source lock fields changed")
    if payload["schema"] != 1 or payload["distribution"] != "aos-prov":
        raise SourceLockError("aos-prov source lock identity changed")
    if payload["version"] != "5.4.2":
        raise SourceLockError("aos-prov source lock version changed")
    if importlib.metadata.version("aos-prov") != payload["version"]:
        raise SourceLockError("installed aos-prov version is not pinned 5.4.2")
    specification = importlib.util.find_spec("aos_prov")
    if specification is None or specification.origin is None:
        raise SourceLockError("installed aos_prov package is unavailable")
    package_root = Path(specification.origin).parent
    _regular_nonsymlink(Path(specification.origin), "aos_prov package initializer")
    expected_files = payload["files"]
    if not isinstance(expected_files, dict) or len(expected_files) != 5:
        raise SourceLockError("aos-prov pinned source set changed")
    for relative, expected_digest in sorted(expected_files.items()):
        if not isinstance(relative, str) or relative.startswith(("/", ".")):
            raise SourceLockError("aos-prov source lock path is unsafe")
        if not isinstance(expected_digest, str) or len(expected_digest) != 64:
            raise SourceLockError("aos-prov source lock digest is invalid")
        source = package_root / relative
        _regular_nonsymlink(source, f"pinned aos-prov source {relative}")
        actual_digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual_digest != expected_digest:
            raise SourceLockError(f"pinned aos-prov source changed: {relative}")
    return package_root
