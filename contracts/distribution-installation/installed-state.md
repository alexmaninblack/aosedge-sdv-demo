<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installed Runtime Path Separation

- Status: Accepted for the isolated Stage 3 implementation; live activation unqualified
- Version: 1.1
- Prepared: 2026-09-27
- Owner: Demo Solution Team
- Decision: [ADR 0018](../../docs/architecture/decisions/0018-installable-demo-and-first-use.md)

## Roots and authority

The existing Demo Control retains ownership of all operations. In the installed
mode, one explicitly selected private instance directory is its state root.
The running code and contract locks come from the installed immutable version;
the five packaged input groups and Factory catalogue come from that version's
input directory. Prepared releases, backend configuration/data and other
generated artifacts belong to the instance's `artifacts` directory, never the
immutable catalogue. Existing relative `.local` and `.run` journal references
retain their meaning under the instance root.

Developer mode without an instance selection retains the previous workspace
layout. Installed mode rejects developer artifact overrides and absent packaged
groups instead of falling back to sibling checkouts, Homebrew or user `.aos`.
It never reads another instance's state. Package repair/replacement cannot
reset the release ledger, provisioned identity, backend history or credentials.

Developer build/patch entry points are unavailable in installed mode. A kit
must already contain its public Cloud Unit template and all five locked input
groups; copying that template into mutable instance state is not required.

Docker Desktop remains the separately installed prerequisite in ADR 0018.
Installed backend commands resolve its executable inside the standard
`/Applications/Docker.app` bundle, independently of an interactive shell PATH.
They do not start/install Docker, inherit a developer PATH or fall back to
Homebrew. Missing executable and unavailable engine remain distinct blocking
results. Developer-mode executable discovery is unchanged.

## Instance creation and explicit selection

Creation is a separate, explicit local operation. The parent must exist. Create
only a new private directory or validate an already recognized instance; do not
adopt foreign content. A bounded owner-only regular `instance.json` contains
exactly `schemaVersion: 1`, `kind: aosedge-demo-instance` and a generated
`instanceId` UUID. The marker is version-independent: it is neither a Cloud
identity nor proof of runtime readiness. Unknown schema, wrong owner/mode,
links, overlapping package/state paths and unsupported native socket path
lengths block selection. No migration, downgrade or implicit data copy occurs.

This slice constrains private state to the home filesystem and bounded socket
paths. The native installation preflight must additionally verify the internal
storage policy; this is not qualification of an externally located home.
Package selection re-reads the mounted volume UUID/ownership independently of
its mount name and requires it to match the private installation receipt.

The engineering `--instance-root` option selects an existing instance for one
CLI invocation. Selection requires the executing application to reside in an
installed version with the matching manifest digest and installation receipt.
The original Kit 005 engineering entry does not write an active-version pointer.
Subsequent managed kits use the [version-selection contract](version-selection.md):
an explicit compatible selection and shared instance/package leases are required
before runtime entry. Neither mechanism stops another process or grants permission
to replace a running setup. Native operator activation remains a later gate.

Normal runtime status does not repeatedly hash large immutable payloads.
Existing bounded source-lock and consumed-file validation remains mandatory;
installation performs full-payload trust verification. A selected package must
never be used as a writable runtime working directory.

## Window metadata is not lifecycle state

Accepted 29 September amendment: the existing window owner stores its private
metadata at `.local/demo-control/workspace/state.json`, independently of the
vehicle-run journal. This is physical UI state, not a second lifecycle authority.
First/repeat/restarted Open Presenter must leave the vehicle journal absent
until Create Controller initializes it. Existing journals remain byte-for-byte
unchanged by layout operations; legacy workspace fields are read-only fallback
only when the new record is absent. Invalid journals are not repaired or accepted.
The exact schema, file checks and qualification are in
[native setup](native-setup.md#independent-window-metadata--accepted-29-september-2026).

## Credentials and transport defaults

Fresh installed instances default to private relative paths under
`.local/demo-control/credentials` for OEM/SP certificates and to
`.local/demo-control/tls` for operator transport trust. Missing files remain
missing prerequisites. Never auto-adopt developer certificates, trust files or
the developer VM password from a shared Keychain item. The installed Keychain
namespace includes the instance UUID. Native explicit credential selection
remains the only existing mechanism for choosing external certificate files.
This slice does not enroll users, generate trust or claim encrypted PKCS#12
support. One OEM and one associated SP own the two distinct demo services.

Accepted 28 September amendment: [local Gateway server trust](local-gateway-trust.md)
adds per-instance initialization during explicit first simulator start, not
during installation or read-only observation. It replaces only the missing
server-pair prerequisite for a fresh installed instance; unsafe/foreign material
still blocks, and Cloud credential selection and client mTLS authority do not change.

## Acceptance boundary

Tests cover legacy-path preservation; separate program/input/output/state roots;
fresh, repeated and invalid instance creation; missing/corrupt group rejection;
private credential and instance-scoped Keychain defaults; packaged command
identity; output/ledger preservation across program-version selection; and
read-only package execution with developer and credential inputs denied.
No UI/Cloud/provisioning/CARLA action is needed for those isolated gates.

This path-separation proof is not qualification of native first-use, update
activation, state-schema migration, removal, external working-data relocation
or live E2E. The separate version-selection contract scopes engineering
rollback/recovery evidence without making a native activation claim.
