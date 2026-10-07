<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0018: Installable Demo and First-use Boundary

- Status: Accepted direction; staged implementation and qualification incomplete
- Version: 1.1
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

On 1 October the user accepted the separate native **Prepare backends** step:
the trusted Setup wrapper imports the pinned untagged image set into the already
running local Docker Desktop engine. It uses existing instance/package leases
and the Demo Control writer; only a private attempt record is added for lost
response reconciliation. Docker remains image-readiness authority. No second
runtime lifecycle, auto-import during Create or new backend build is introduced.
The [native setup contract](../../../contracts/distribution-installation/native-setup.md#explicit-backend-preparation-accepted-on-1-october-2026)
defines the bounded operation and qualification gates.

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

On 29 September the user selected direct beta distribution: Developer ID
Application signing and Apple notarization, delivered through a DMG rather
than TestFlight. This refines the existing delivery channel, not vehicle/runtime
authority. Apple Development remains an explicitly local engineering signature.
The accepted channel does not establish that a distribution certificate/private
key, notarization credentials or permission to upload a particular archive is
available. Resolve those actual prerequisites without stopping independent
installation and lifecycle work. No certificate or account may be silently
created and no security warning may be bypassed.

Distribution signing covers the macOS executable closure, not only Setup's
outer bundle. Preserve the previous verified kit; sign only a new candidate,
then regenerate its integrity manifests and independent installer pin. Qualify
the required hardened-runtime/entitlement behavior and strict signatures before
submitting the exact archive to Apple. A successful local DMG build, developer
signature or checksum alone does not qualify distribution or notarization.

## Single DMG delivery accepted on 2 October 2026

The user accepted the operator-experience direction and requested complete media
as the first implementation milestone. Ship the trusted native Setup and its
matching complete runtime kit in one DMG. Setup may discover only the fixed
sibling payload and prefill its source field; the existing independently pinned
validation still authenticates it. Discovery is not installation or readiness.
No folder picker is needed on the ordinary mounted-media path. No arbitrary
payload code is executed and no Cloud, dependency installation or runtime start
is added to the offline transaction.

Build from the current verified kit without rebuilding Factory or CARLA. Verify
the mounted media and install on M1 without a separately staged kit fallback.
The candidate remains local engineering media until signing, notarization and
redistribution gates close. Persistent launcher installation, unified onboarding
and the guided scenario are accepted direction but later implementation slices;
do not claim that wrapping today's Setup completes those deliverables.

## Current implementation — 7 October 2026

Kit028 / Setup042 implements complete local DMG delivery, installed private
state, explicit backend preparation, Cloud access/enrollment/recovery and
Presenter launch using existing owners. The staged paragraphs below preserve
the order and non-claims of each original increment. They are not today's
“not implemented” list. The [current baseline](../../qualification/current-baseline.md)
records 98 installed scripted steps, incomplete native acceptance and the
still-unimplemented simplified wizard/returning-stopped-controller path.

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
Its original preparation actions remain offline. The separate explicit-launch
increment opens the selected instance using existing Demo Control ownership,
leases and workspace restoration, without version activation or VM/Cloud
mutations. Source/native/live qualification remain distinct; enrollment is open.

The accepted 29 September [first-use completion detail](../../../contracts/distribution-installation/cloud-first-use.md)
now has source implementation for one-shot SDK enrollment, durable private
attempt/key recovery and explicit exact unbound Subject references. The existing
assignment owner rechecks a saved reference before use; installation cannot bind
it to a Unit. Native secure input and the existing writer/leases preserve the
same ownership boundary. Source/fixture results do not qualify real token
issuance, ordinary installed first use, or clean-system acceptance.

The complete wizard, state migration, public signing/notarization and full native
E2E remain separate deliverables. DMG, backend import and installed scripted M1
evidence are recorded separately; they are not full wizard/native acceptance. Installing
bytes must report `INSTALLED_NOT_ACTIVATED`, never claim the demo is ready.

## Impact and preservation

Accepted 28 September first-use refinement: Demo Control initializes a separate
private local Gateway server identity during explicit first simulator start,
as defined in the [local-trust contract](../../../contracts/distribution-installation/local-gateway-trust.md).
This is local lab authority, not an Aos Cloud/OEM certificate or system trust
enrollment. It fills the previously explicit missing server-TLS prerequisite;
client mTLS and selected-Unit authorization remain unchanged.

Owner: integration distribution tooling and the existing Demo Control. No
vehicle service, Gateway, Factory, model threshold or AosCore change is needed.
Preserve the existing source work, current live Test/Production, credentials,
video repository, package pins and warm build caches. The source `demo-v1.1`
tag stays immutable; installation candidate identity is the manifest digest,
not a reused application version label.

Evidence is recorded per delivery slice in the distribution plan. A source
test, local installation and clean-system/live proof remain distinct verdicts.
