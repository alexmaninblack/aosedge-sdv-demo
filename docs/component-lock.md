<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Exact Component Lock

## Purpose

`components/baseline.lock.json` identifies the exact source and artifact inputs
for one tested or candidate integration baseline without Git submodules. It is
public, non-secret, and contains no developer checkout path.

The initial candidate pins:

- the AosVM 6.1.0 ARM64 release archive and selected member digests;
- embedded KUKSA Databroker 0.5.0 and VSS 5.0 against the exact AosVM archive;
- the VSS 6.0 source revision used by the CARLA projection;
- the exact `carla-ego-runtime`, platform, and service commits;
- the platform contract and unsigned service-package template file digests.

The lock status remains `candidate` until R-5 clean-clone qualification passes.
It does not claim AOS-2 or AOS-3 telemetry behavior.

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
