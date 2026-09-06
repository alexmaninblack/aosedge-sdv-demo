# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Discover immutable image artifacts; no registration database or image hashing."""

import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path

from .status import project_root, read_json

NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,95}")
SHA = re.compile(r"[0-9a-f]{64}")


class ImageError(ValueError):
    """An explicit selector could not be resolved without guessing."""


@dataclass(frozen=True)
class ImageRecord:
    selector: str
    version: str
    architecture: str
    path: Path
    size: int
    sha256: object
    image_format: object
    metadata_sources: tuple
    problems: tuple

    def public(self, artifact_root):
        return {
            "selector": self.selector, "version": self.version,
            "architecture": self.architecture,
            "path": "$DEMO_ARTIFACT_ROOT/" + self.path.relative_to(artifact_root).as_posix(),
            "sizeBytes": self.size, "expectedSha256": self.sha256, "format": self.image_format,
            "metadataSources": list(self.metadata_sources),
            "problems": list(self.problems),
            "state": "METADATA_AVAILABLE" if not self.problems else "UNAVAILABLE_FOR_CREATE",
            "digestChecked": False,
        }


class ImageCatalog:
    def __init__(self, root=None, workspace=None):
        self.workspace = Path(workspace) if workspace else project_root().parent
        configured = root if root is not None else os.environ.get("DEMO_ARTIFACT_ROOT")
        self.root = Path(configured).expanduser().resolve() if configured else self.workspace / "demo-artifacts"
        self.project = self.root / "aosedge-sdv-demo"

    def _image_reference(self, value, manifest):
        if not isinstance(value, str):
            raise ImageError("IMAGE_REFERENCE_INVALID")
        substitutions = {"$DEMO_ARTIFACT_ROOT": self.root, "$WORKSPACE_ROOT": self.workspace}
        for prefix, replacement in substitutions.items():
            if value.startswith(prefix + "/"):
                return replacement / value[len(prefix) + 1:]
        if "$" in value:
            raise ImageError("IMAGE_REFERENCE_INVALID")
        candidate = Path(value)
        return candidate if candidate.is_absolute() else manifest.parent / candidate

    def _metadata(self):
        records = {}
        issues = []
        # Only known manifest locations; do not traverse bundles or runtime state.
        paths = list((self.project / "manifest").glob("*.json"))
        paths.extend((self.project / "factory-images").glob("*/*.json"))
        for path in sorted(paths):
            if not path.resolve().is_relative_to(self.project.resolve()):
                issues.append({"source": path.name, "reason": "MANIFEST_OUTSIDE_CATALOG"})
                continue
            try:
                data = read_json(path, limit=262144)
                if not isinstance(data, dict):
                    raise ImageError("MANIFEST_INVALID")
                image = data.get("factoryImage") or data.get("image")
                if image is None:
                    continue
                if not isinstance(image, dict):
                    raise ImageError("MANIFEST_INVALID")
                target = self._image_reference(image["path"], path).resolve()
                sha = image.get("sha256")
                size = image.get("byteLength", image.get("sizeBytes"))
                version = image.get("version")
                if not isinstance(sha, str) or not SHA.fullmatch(sha) or type(size) is not int or size <= 0:
                    raise ImageError("MANIFEST_INVALID")
                if not isinstance(version, str) or not NAME.fullmatch(version):
                    raise ImageError("MANIFEST_INVALID")
                fmt = image.get("format")
                if fmt is None and target.suffix == ".img":
                    # The retained .27 inventory records a raw .img, not a qcow2.
                    # Creation must independently verify actual qemu-img metadata.
                    fmt = "raw"
                if fmt not in ("raw", "qcow2"):
                    raise ImageError("MANIFEST_FORMAT_UNKNOWN")
                source = path.relative_to(self.root).as_posix()
                records.setdefault(target, []).append((sha, size, version, fmt, source))
            except (OSError, ValueError, TypeError, KeyError):
                issues.append({"source": path.name, "reason": "MANIFEST_INVALID"})
        return records, issues

    def records(self):
        manifests, issues = self._metadata()
        result = []
        for path in sorted((self.project / "factory-images").glob("*/*")):
            if path.suffix not in (".img", ".qcow2") or not path.is_file():
                continue
            version, arch = path.parent.name, path.stem
            if not NAME.fullmatch(version) or not NAME.fullmatch(arch):
                continue
            problems = []
            info = path.stat()
            canonical = path.resolve()
            if path.is_symlink() or not canonical.is_relative_to(self.project.resolve()):
                problems.append("IMAGE_PATH_NOT_OWNED")
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                problems.append("IMAGE_NOT_INDEPENDENT_REGULAR_FILE")
            if stat.S_IMODE(info.st_mode) & 0o222:
                problems.append("IMAGE_NOT_READ_ONLY")
            entries = manifests.get(canonical, [])
            if not entries:
                problems.append("MANIFEST_MISSING")
                sha, fmt, sources = None, None, ()
            else:
                bindings = {(s, n, v, f) for s, n, v, f, _ in entries}
                sha, size, recorded_version, fmt = entries[0][:4]
                sources = tuple(sorted({entry[4] for entry in entries}))
                if len(bindings) != 1:
                    problems.append("MANIFEST_CONFLICT")
                if size != info.st_size or recorded_version != version:
                    problems.append("MANIFEST_BINDING_MISMATCH")
            result.append(ImageRecord(version + "/" + arch, version, arch, path, info.st_size,
                                      sha, fmt, sources, tuple(problems)))
        return result, issues

    def list(self):
        try:
            records, issues = self.records()
            return {
                "catalog": "$DEMO_ARTIFACT_ROOT/aosedge-sdv-demo/factory-images",
                "catalogExists": (self.project / "factory-images").is_dir(),
                "images": [record.public(self.root) for record in records],
                "issues": issues, "digestChecked": False,
                "claim": "Artifact and metadata inventory, not qualification or a digest verification.",
            }
        except (OSError, ValueError):
            return {"images": [], "issues": [{"reason": "CATALOG_UNREADABLE"}], "digestChecked": False}

    def resolve(self, selector=None, image_path=None):
        if bool(selector) == bool(image_path):
            raise ImageError("EXACTLY_ONE_IMAGE_SELECTOR_REQUIRED")
        records, _ = self.records()
        if selector is not None:
            matches = [r for r in records if r.selector == selector]
        else:
            candidate = Path(image_path).expanduser()
            if candidate.is_symlink():
                raise ImageError("IMAGE_PATH_NOT_OWNED")
            matches = [r for r in records if r.path.resolve() == candidate.resolve()]
        if len(matches) != 1:
            raise ImageError("IMAGE_NOT_FOUND" if not matches else "IMAGE_AMBIGUOUS")
        if matches[0].problems:
            raise ImageError(matches[0].problems[0])
        return matches[0]
