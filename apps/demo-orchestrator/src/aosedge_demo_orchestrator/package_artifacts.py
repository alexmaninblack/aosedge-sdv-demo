# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Local publication representations of immutable prepared package content."""

import hashlib
import json
import re
from .environment import EnvironmentError
from .status import read_json


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def context(identity, prepared_sha):
    from .cloud_connection import domain_name
    if (not isinstance(identity, dict) or identity.get("role") not in ("oem", "service provider")
            or not re.fullmatch(r"[0-9a-f]{64}", identity.get("signerId", ""))
            or not re.fullmatch(r"[0-9a-f]{64}", prepared_sha)):
        raise EnvironmentError("PACKAGE_SIGNING_CONTEXT_INVALID")
    return dict(schemaVersion=1, domain=domain_name(identity["domain"]), role=identity["role"],
                signerId=identity["signerId"], preparedSha256=prepared_sha)


def paths(directory, identity, *, create=False):
    parent = directory / ".signatures"
    target = parent / digest(identity)
    if directory.is_symlink() or parent.is_symlink() or target.is_symlink():
        raise EnvironmentError("PACKAGE_SIGNING_PATH_UNSAFE")
    if create:
        target.mkdir(mode=0o700, parents=True, exist_ok=True)
    bundle, receipt = target / "deployment-bundle.tar.gz", target / "signed.json"
    if bundle.is_symlink() or receipt.is_symlink():
        raise EnvironmentError("PACKAGE_SIGNING_PATH_UNSAFE")
    return bundle, receipt


def signed_receipt(directory, identity):
    bundle, path = paths(directory, identity)
    if not path.is_file() or not bundle.is_file():
        raise EnvironmentError("PACKAGE_SIGN_FOR_SELECTED_CLOUD_REQUIRED")
    value = read_json(path)
    if value.get("signingContext") != identity or value.get("signatureVerification") != "VERIFIED_RS256":
        raise EnvironmentError("PACKAGE_SIGNING_RECEIPT_MISMATCH")
    return bundle, value


def publication_path(directory, domain, role, *, create=False, owner_id=None):
    """An attempted publication survives signer rotation, unlike a signature."""
    from .cloud_connection import domain_name
    parent = directory / ".publications"
    scope = dict(domain=domain_name(domain), role=role)
    legacy = parent / digest(scope) / "publication.json"
    if owner_id:
        from .status import object_id
        scope["ownerId"] = object_id(owner_id)
    target = parent / digest(scope)
    path = target / "publication.json"
    if any(item.is_symlink() for item in (directory, parent, target, path)):
        raise EnvironmentError("PACKAGE_PUBLICATION_PATH_UNSAFE")
    if owner_id and not path.exists():
        if legacy.is_symlink() or legacy.parent.is_symlink():
            raise EnvironmentError("PACKAGE_PUBLICATION_PATH_UNSAFE")
        if legacy.is_file():
            old = read_json(legacy)
            if not old.get("ownerId"):
                raise EnvironmentError("PACKAGE_LEGACY_OWNER_RECONCILIATION_REQUIRED")
            if old.get("ownerId") == owner_id:
                if old.get("cloudDomain") != domain:
                    raise EnvironmentError("PACKAGE_PUBLICATION_CONTEXT_MISMATCH")
                # Retain the original exact receipt; do not copy/retry its POST.
                return legacy
    if create:
        target.mkdir(mode=0o700, parents=True, exist_ok=True)
    return path


def credential_stamp(path):
    """Cheap UI invalidation only; signing/upload always verify cryptographically."""
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o077:
            return None
        info = path.stat()
    except OSError:
        return None
    return digest([str(path), info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns])


def visible_signature(directory, domain, role, stamp):
    parent = directory / ".signatures"
    if parent.is_symlink():
        raise EnvironmentError("PACKAGE_SIGNING_PATH_UNSAFE")
    entries = list(parent.iterdir()) if parent.is_dir() else []
    if len(entries) > 256:
        raise EnvironmentError("PACKAGE_SIGNING_RECEIPT_LIMIT")
    for entry in entries:
        path = entry / "signed.json"
        if entry.is_symlink() or path.is_symlink():
            raise EnvironmentError("PACKAGE_SIGNING_PATH_UNSAFE")
        if not path.is_file():
            continue
        value = read_json(path)
        scope = value.get("signingContext", {})
        if (scope.get("domain") == domain and scope.get("role") == role and stamp
                and value.get("credentialStamp") == stamp
                and value.get("signatureVerification") == "VERIFIED_RS256"
                and not (entry / "deployment-bundle.tar.gz").is_symlink()
                and (entry / "deployment-bundle.tar.gz").is_file()):
            return value
    return {}
