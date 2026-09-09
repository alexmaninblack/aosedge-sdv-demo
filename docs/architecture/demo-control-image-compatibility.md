<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Control: image-bound component support

Status: P1 catalog reader and producer metadata increment, 10 September 2026.
Scope: the [accepted catalog compatibility change](../planning/active/demo-studio-delivery-plan.md#p1-fix-shared-operations-once),
not SOTA execution, service permissions or a new image qualification.

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

The existing .31 artifact's declaration was registered through
`democtl image build 6.1.1-maninblack.31 --metadata-only`. It derives the 23
accepted v1/v2/v3 read paths from the exact clean pinned Platform source and
checks the existing image's producer source, identity, read-only file and size.
It preserves the recorded image SHA and every unrelated manifest field.
It does not silently modify legacy manifests during status or publication.
No rebuild, image replacement or qualification promotion has occurred.

The existing pinned Factory build producer now includes this declaration in
its output manifest, deriving paths from that source's packaged VSS composition
and preserving `BUILT_NOT_LIVE_QUALIFIED`. Eight producer/migration tests cover
the exact source, schema, CLI/API parity, metadata conflicts, unsafe files,
immutable image preservation and idempotent repeat. Metadata-only mode cannot
fall through into a build when an artifact is missing. Actual registration and
one explicit repeat passed; the second returned `noOp=true`. Builder was not run.

Isolated regression tests cover a version-independent declared image, missing
declaration, wrong image SHA/type/source, unsupported paths and conflicting
producer metadata. They do not substitute for the declaration or live proof.
