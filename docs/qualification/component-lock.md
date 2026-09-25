<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Exact Component Lock

## Current scope — 13 September 2026

Historical heading retained for links. Current audit: 24 September 2026.

The AOS-2/R6.1 locks below are immutable historical inputs, not effective
Factory39 core overrides. Current source is pinned by
[workspace/repositories.json](../../workspace/repositories.json) and hosted CI.
The [v1.1 checkpoint](../../workspace/checkpoints/demo-v1.1.json) and
[return point](demo-v1.1-return-point.md) record Factory39 provenance.
Reconciliation is complete for that published checkpoint. Do not rewrite old
release digests to manufacture agreement with newer source.

## Purpose

`components/baseline.lock.json` identifies the exact accepted AOS-2 source and
artifact inputs without Git submodules. It is public, non-secret, and contains
no developer checkout path. The later R6.1 Yocto/runtime source baseline is
separately pinned by `components/r6-1-source.lock.json`. These older candidates
must not be confused with the current .39 manufacturing input.

The initial candidate pins:

- the AosVM 6.1.0 ARM64 release archive and selected member digests;
- embedded KUKSA Databroker 0.5.0 and VSS 5.0 against the exact AosVM archive;
- the VSS 6.0 source revision used by the CARLA projection;
- the exact `carla-ego-runtime`, platform, and service commits;
- the platform contract, reproducible AOS-2 ARM64 provider bundle, and unsigned
  service-package template file digests.

The lock status is `accepted` because R-5 passed clean-clone qualification and
the independent GitHub Actions boundary gate, and R6/AOS-2 passed the live
CARLA-to-KUKSA, failure-state, restart, and cloud-continuity gates. It does not
yet claim AOS-3 service behavior.

## Static Validation

Run from any integration checkout:

```text
./scripts/validate-component-lock
```

The validator rejects missing components, floating branches and versions,
short commit identifiers, missing architecture qualification, unsafe local
paths, malformed digests, and embedded-component digest mismatches.

## Sibling Checkout Validation

To verify project-owned source commits and locked repository files, pass the
directory containing sibling clones:

```text
./scripts/validate-component-lock --workspace-root ..
```

The path is a command argument and is never recorded. If a developer tool
needs persistent checkout hints, it may use the ignored
`config/component-paths.local.json` file. Shared scripts must not require that
file.

## External Artifact Validation

To re-hash downloaded release artifacts, pass a directory containing the
locked archive filename:

```text
./scripts/validate-component-lock \
  --artifact-root .cache/aosvm/v6.1.0/qemuarm64
```

External source tags remain paired with full commit revisions. A tag alone is
not considered an exact source lock.
