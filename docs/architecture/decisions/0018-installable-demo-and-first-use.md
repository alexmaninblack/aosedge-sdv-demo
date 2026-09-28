<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0018: Installable Demo and First-use Boundary

- Status: Accepted direction; staged implementation and qualification incomplete
- Version: 1.0
- Prepared: 2026-09-27
- Owner: Demo Solution Team
- Change class: C for installed-state/first-use integration; the first delivery
  slice is an offline, non-activating installation tool
- Architecture input: [High-Level Architecture 1.8](../high-level-architecture.md)
- Authority: the user approved implementation after reviewing the installation
  proposal and explicitly retaining one OEM and one SP for Brake and Tire.
- Parent: [Distribution plan](../../planning/active/installable-distribution-and-reproducibility.md)

## Decision

Deliver a macOS DMG with an application and first-use wizard, supported by
versioned components. The first implementation accepts a complete local kit;
download hosting and its authorization are not selected or purchased. The
operator does not build Unreal, CARLA, Python, the host UI or vehicle services.
Docker Desktop is an explicit separately installed prerequisite with its own
operator acceptance and licensing; do not silently install or reconfigure it.

Keep immutable program/component versions separate from durable user state,
credentials and disposable caches. Use a user-selected package store; ordinary
application use needs no administrator identity. Initially retain working
VM/backend data internally. External working-data relocation requires separate
functional/performance proof. Bind external storage by volume identity and
fail when absent rather than creating a replacement mount directory.

Installation and Cloud onboarding are independent. First use offers existing
access or official registration; registration/email steps remain with the
operator and platform. Use one OEM and one associated SP owning both distinct
services. Never require a second SP for this first release. Preserve separate
service identities, versions, histories, permissions and Reset operations;
this topology does not demonstrate cross-provider isolation.

Secrets are never shipped, logged or copied from the developer setup. Native
secure input and supported SDK operations own certificate enrollment; do not
execute a pasted email command. Preserve the selected-domain and authoritative
permission checks. The runtime remains the existing Demo Control, not a new
independent orchestrator. Cloud registration, publication and Finish retain
their separate exact-target authorization and reconciliation contracts.

Install/update into a new verified version before explicit activation. No
automatic replacement of running software. Repair affects program files only.
Retain one compatible predecessor, but do not delete a Factory still referenced
by a VM. An application rollback never decrements release numbers, rolls back
Cloud or restores old run data. Block incompatible state rollback. Removal
preserves user data by default and never performs Finish implicitly.

Before external delivery, close Developer ID/notarization, dependency notices
and redistribution review, and declare only the measured support envelope.
Do not disable OS security to make installation work.

## Staged allocation and non-claims

The [installation contract](../../../contracts/distribution-installation/README.md)
freezes the first offline transaction slice. It installs only immutable bytes,
has no runtime activation entry point and never opens operator state. Therefore
it does not yet change the existing runtime root, state owner or Cloud protocol.
The broader canonical architecture/flow/requirements cascade and installed
runtime path separation are gates before enabling activation, first-use SDK
enrollment, update switching or removal. Keep this work on its architecture
branch until that cascade and its tests are complete.

The subsequent [installed-state slice](../../../contracts/distribution-installation/installed-state.md)
has completed that canonical path-separation cascade and its isolated Kit 005
proof. It adds explicit engineering instance selection, not native activation
or onboarding. The [evidence and remaining gates](../../qualification/installed-state-2026-09-27.md)
distinguish these outcomes from the first transaction slice above.

The [version-selection/recovery detail](../../../contracts/distribution-installation/version-selection.md)
now refines the same ownership decision: explicit compatible manifest selection,
runtime-use leases, stale-action rejection and program-only recovery with the
original bytes retained. This engineering layer permits only quiescent instances
without a retained current run; it does not authorize deleting run data to allow
an update. Native activation, retained-run updates and destructive removal remain
separate gates, not consequences of a successful local selection.

The [native local-setup detail](../../../contracts/distribution-installation/native-setup.md)
wraps these same engines with bounded progress and explicit local preparation.
It remains an offline engineering preview, not enrollment or runtime activation.

The complete wizard/DMG, state migration, secure enrollment, fresh Docker import, signing,
clean-Mac installation and live E2E remain separate deliverables. Installing
bytes must report `INSTALLED_NOT_ACTIVATED`, never claim the demo is ready.

## Impact and preservation

Owner: integration distribution tooling and the existing Demo Control. No
vehicle service, Gateway, Factory, model threshold or AosCore change is needed.
Preserve the existing source work, current live Test/Production, credentials,
video repository, package pins and warm build caches. The source `demo-v1.1`
tag stays immutable; installation candidate identity is the manifest digest,
not a reused application version label.

Evidence is recorded per delivery slice in the distribution plan. A source
test, local installation and clean-system/live proof remain distinct verdicts.
