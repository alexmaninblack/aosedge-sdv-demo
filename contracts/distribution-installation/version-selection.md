<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installed Version Selection and Recovery

- Status: Accepted staged implementation detail of ADR 0018; native delivery unqualified
- Version: 1.0
- Prepared: 2026-09-27
- Owner: Demo Solution Team
- Parent: [Installed state](installed-state.md) and [ADR 0018](../../docs/architecture/decisions/0018-installable-demo-and-first-use.md)

## Selection is not runtime readiness

An explicit local selection binds a private instance to a fully verified
installed manifest digest and a volume-bound store. It never starts/stops an
application, VM, container, simulator or Cloud operation. The existing Demo
Control remains the runtime owner. This engineering slice supplies the shared
selection/lease mechanism; the native wizard and application launcher consume
it later, after their own qualification.

The fixed compatibility identity is `aosedge-demo-installed-state/1`, carried
by the independently pinned application manifest as `installedStateContract`.
It covers the installed instance and existing retained Demo Control state
formats, not vehicle firmware or Cloud releases. Only exact supported identity
is accepted. Missing declarations (including Kit 005 and earlier), unknown
versions or an instance bound to another contract block managed selection.
There is no schema migration or compatibility inference from application names.

One owner-private `installation.json` in the instance stores schemaVersion,
instanceId, storePath, volumeUUID, stateContract, revision, current and previous
manifest digests. An absent record has revision zero. Each change requires the
observed revision and commits one atomic replacement. A stale UI request cannot
overwrite a newer choice. Selecting the already current version is idempotent;
rollback selects only the recorded compatible predecessor. Unselect preserves
both package bytes and all user data and explicitly reports no disk space freed.
Unselect is not a complete application uninstall or package garbage collection.

Engineering entry: `scripts/distribution/version_management.py` from the trusted
integration source, not a script loaded from an unverified candidate. Every
operation requires explicit `--store` and `--volume-uuid`. `status`, `select`,
`rollback` and `unselect` additionally require an already initialized
`--instance-root`; changes require the revision returned by status through
`--revision`. Select requires the independent `--manifest-sha256`. Repair uses
`--source` and that same independent digest, without an instance or revision.
These tools are qualification interfaces, not the final first-use UX.

`SELECTED_NOT_STARTED` describes this operation's non-activating outcome, not an
observation that all runtime processes are stopped or that the demo is ready.
Readiness still belongs to the existing runtime's authoritative observations.

## Use and quiescence

Runtime entry holds shared, nonblocking owner-private locks on the instance
and package for the complete invocation. Selection holds the instance lock
exclusively. Repair holds the package lock exclusively. Lock files are never
replaced/unlinked; the same inode must remain bound to the name. Runtime entry
re-reads selection while leased and rejects a nonselected version. New managed
packages require explicit selection; legacy engineering probes remain separate.

Selection also blocks on current-run journals, working VM overlays and any
other owned process holding files under the instance or store. Inspection must
succeed completely; failure is not treated as idle. This intentionally permits
only quiescent instances without a retained current run in the first slice.
It does not force Finish or erase a journal to unblock an update. Supporting
an update around a retained provisioned run requires a later exact-owner proof.
Open-handle checks catch detached native consumers after a CLI has returned.
No process is killed and no motion control is exercised.

## Program-only repair

Repair uses an independently pinned complete source kit and the existing
verified installer. It never edits bytes in place or modifies instance data.
Under the store writer and exclusive package lease, stage and fully verify a
replacement in `quarantine/<digest>/replacement-store`, then rename the old
version to `quarantine/<digest>/original` and promote the replacement at the
original version path. A private transaction record blocks runtime entry until
reconciliation and receipt completion. A repeat reconciles interruption before
or after either rename rather than guessing or deleting uncertain state.

The existence of repair work without a committed first record also blocks
runtime entry. An explicit repair may recreate that first record only for the
recognized empty work directory (or its single fixed private pending record),
with the original version still present and the independent source reverified.
Unknown entries remain untouched and block recovery.

The old bytes remain recoverable; no recursive deletion occurs. An unresolved
transaction, unexpected quarantine content or second damaged generation blocks.
A healthy repeat verifies/reuses the installed version. A wrong source pin,
busy package, disk/volume failure or undeclared source leaves the selection and
user data unchanged. Preserve the 90 GiB engineering installation reserve.

The shared store now permits a private `quarantine` directory; receipts may
also contain `<digest>.use.lock`. Neither is runtime/model state. Keep one
compatible predecessor; do not prune additional versions or Factory references
until the separate all-instance retention/removal gate is implemented.

## Required evidence

Small fixture tests: first/repeat selection, restart reconstruction, stale
revision, compatible rollback, missing/incompatible manifest, wrong volume,
private/link checks, current-run/native-use exclusion, concurrent runtime lease,
atomic record failure, corrupt program repair, interrupted renames/recovery,
source rejection and byte-for-byte user-data preservation. No payload fixture
code may execute during install/select/repair.

Then test a complete new kit in an isolated store: explicit selection, fixed
read-only installed CLI, old-version rejection, quiescence block, repeat and
unselect. Real repair/rollback fault injection remains on tiny disposable
fixtures; do not corrupt large retained packages or the working demo merely
to demonstrate this engine. Native activation, installed live E2E, migration,
destructive pruning/uninstall and clean-Mac acceptance remain open gates.
