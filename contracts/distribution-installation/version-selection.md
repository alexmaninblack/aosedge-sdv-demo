<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installed Version Selection and Recovery

- Status: Accepted implemented selection/lease contract; scoped proof in the current baseline
- Version: 1.2
- Updated: 2026-10-22
- Prepared: 2026-09-27
- Owner: Demo Solution Team
- Parent: [Installed state](installed-state.md) and [ADR 0018](../../docs/architecture/decisions/0018-installable-demo-and-first-use.md)

## Selection is not runtime readiness

An explicit local selection binds a private instance to a fully verified
installed manifest digest and a volume-bound store. It never starts/stops an
application, VM, container, simulator or Cloud operation. The existing Demo
Control remains the runtime owner. The native Setup and persistent application launcher consume this shared
selection/lease mechanism now. Their scoped proof is in the
[current baseline](../../docs/qualification/current-baseline.md); the complete
interruption/repair/update/removal matrix remains a separate gate.

The fixed compatibility identity is `aosedge-demo-installed-state/1`, carried
by the independently pinned application manifest as `installedStateContract`.
It covers the installed instance and existing retained Demo Control state
formats, not vehicle firmware or Cloud releases. Only exact supported identity
is accepted. Missing declarations, unknown
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
operation requires explicit `--store` and `--volume-uuid`. `status`, `select`, `upgrade`,
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
succeed completely; failure is not treated as idle. Ordinary select, rollback
and unselect still require no retained run. They never force Finish or erase a
journal to unblock an update.
Open-handle checks catch detached native consumers after a CLI has returned.
No process is killed and no motion control is exercised.

## Retained-Test package update

The operator authorized this bounded extension on 22 October 2026. Explicit
`upgrade` (or Install/Update followed by native Setup preparation) can select a
new compatible package around one stopped Test. It is not a general schema
migration and does not support a Production-role or dual-role journal.

Hold the existing store writer, exclusive instance lease, both verified package
leases and the existing journal writer lock across the atomic selection. Do not
create a missing journal lock, hide a journal, rewrite a receipt or adopt another
Test. Both packages must declare the same supported installed-state contract.
The Factory, VDP/runtime and service profiles, simulator identity, VM payloads
and Cloud runtime must match the bounded compatibility checks. Native host/UI
programs may change; unknown state or incompatible inputs fail closed.

Validate the existing journal through the ordinary Test lifecycle and status
readers. Require a stopped unassigned Test/VM/source/backend stack, terminal
operations, no pending journal write, no active native consumer, no QEMU owner
for the overlay and no running container owning/mounting the instance or store.
Docker must be observable and unchanged; unrelated containers are not stopped.
The update never activates a replacement backend image: existing backend image
bindings, volumes and model/history data remain the runtime owner's inputs.

The sole durable mutation is one atomic `installation.json` selection change,
recording the former current package as predecessor. Compare unchanged state
identities across this change, excluding that selection record. Preserve Test,
Unit/Node IDs, VM/backing files, credentials, release ledgers and history.
Repeat/restart revalidates the same proof and reuses the current selection.
An interrupted atomic write preserves the old selection or the committed new
selection; never silently retry an unknown result. Opening remains a separate
runtime action. Local fixtures and the exact M1 update/API/UI campaign are
separate acceptance gates; this contract alone claims no live pass.

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

The shared store permits a private `quarantine` directory; receipts may
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
to demonstrate this engine. Native Setup activation and installed live profiles
have scoped proof in the [current baseline](../../docs/qualification/current-baseline.md),
not blanket selection/recovery acceptance. Target-host interruption, repair,
rollback around a retained run, general migration, destructive pruning/uninstall
and the complete clean-macOS consent/recovery matrix remain separate gates.
