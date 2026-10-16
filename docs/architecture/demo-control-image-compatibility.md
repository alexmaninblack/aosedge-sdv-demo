<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Control: image-bound component support

This contract describes the current image compatibility reader and producer
metadata, not a dated Factory migration. The image is selected by the
[controller input lock](../../workspace/inputs/controller-images.lock.json);
the [baseline](../qualification/current-baseline.md) owns actual runtime proof.

Image presence, architecture and firmware version alone do not establish VDP
compatibility. `ImageCatalog.component_support` reads the selected immutable
image's bounded producer metadata and compares the exact recorded image SHA.
It does not hash image bytes or inspect a guest. Publication uses the owned
factory-copy receipt to select the catalog image; that receipt's identity must
match the current run.

The optional `demoCompatibility` object in the existing producer manifest has
exactly these fields:

| Field | Meaning |
| --- | --- |
| `schemaVersion` | Integer 1 |
| `runtimeProfile` | Implemented runtime profile, currently `aos-main-qemuarm64-v1` |
| `componentType` | Exact manufacturing component codename |
| `supportedReadPaths` | Nonempty unique VSS paths supplied by this firmware's packaged schema |
| `sourceRevision` | Full Platform commit, identical to the manifest's `source.revision`; repository must be `aos-vehicle-platform` |

Missing declarations, unsupported paths, mismatching SHA/source/type and
conflicting declarations are explicit blockers. Unknown images are not admitted
through a `.31` fallback. The declaration is a producer compatibility claim,
not live install/runtime evidence, and must not assert advisory support from
the telemetry-only VDP profiles.

## Producer and validation responsibilities

The producer derives the declaration from its exact clean Platform source and
packaged VSS composition, checking source identity, read-only image, size and
recorded digest. Metadata-only registration preserves image bytes and unrelated
manifest fields; it must not fall through to a build if input is missing.
Status/publication never silently migrates a legacy manifest.

Verify version-independent declarations, exact image/source/type binding,
unsupported paths, missing/conflicting metadata, unsafe files, immutable-image
preservation and idempotent repeat. A declaration is producer compatibility,
not proof of live installation, service permission or a healthy VDP process.
The former `.31` registration and its test diary remain in Git history, not the
current image selector.
