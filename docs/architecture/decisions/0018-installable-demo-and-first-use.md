<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0018: Installable Demo and First-use Boundary

- Status: Accepted and implemented for the engineering preview; remaining distribution/qualification gates explicit
- Version: 1.3
- Prepared: 2026-09-27
- Implementation review: 2026-10-22
- Owner: Demo Solution Team
- Change class: C for installed-state/first-use integration; the first delivery
  slice is an offline, non-activating installation tool
- Architecture input: [High-Level Architecture 1.8](../high-level-architecture.md)
- Authority: the user approved implementation after reviewing the installation
  proposal and explicitly retaining one OEM and one SP for Brake and Tire.
- Parent: [Distribution plan](../../planning/roadmap.md)

## Decision

Use the [integrated Setup scenario](../../../contracts/distribution-installation/native-setup.md#integrated-user-journey): automatic default
installation, one authenticated OEM/SP Connect action, bounded missing-SP
repair without Test deletion, paired token enrollment with official registration
handoff, and a signed per-user persistent launcher. Reuse all existing owners;
no new lifecycle/readiness store. The [native contract](../../../contracts/distribution-installation/native-setup.md)
defines the exact paths and operations. Integrated installation/access/open
is implemented. Current native issuance/connection for existing accounts and
separate runtime API/UI profiles passed; broader gates follow the current
baseline. This decision alone does not close a qualification or distribution gate.

Deliver a macOS DMG with an application and first-use wizard, supported by
versioned components. Setup consumes the complete matching local kit; the
launcher now obtains the reviewed public DMG from its selected delivery locator. The
operator does not build Unreal, CARLA, Python, the host UI or vehicle services.
Docker Desktop is an explicit separately installed prerequisite with its own
operator acceptance and licensing; do not silently install or reconfigure it.

The backend-preparation engine is composed inside ordinary Install; it is not
another required screen. The trusted wrapper imports the pinned untagged image
set into the already
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

The accepted direct beta channel uses Developer ID
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

## Single DMG delivery

Ship the trusted native Setup and its matching complete runtime kit in one DMG.
Setup discovers only the fixed sibling payload internally; the independently pinned
validation still authenticates it. Discovery is not installation or readiness.
No folder picker is needed on the ordinary mounted-media path. No arbitrary
payload code is executed and no Cloud, dependency installation or runtime start
is added to the offline transaction.

Build from the current verified kit without rebuilding Factory or CARLA. Verify
the mounted media and install on M1 without a separately staged kit fallback.
The candidate remains local engineering media until signing, notarization and
redistribution gates close. The persistent launcher and integrated onboarding
are implemented through the engines below. A complete guided scenario and
full native return journey remain separate from opening the existing lab.

<a id="current-implementation--7-october-2026"></a>

<a id="current-implementation--15-october-2026"></a>
## Current implementation

The selected preview implements complete DMG delivery, private state,
integrated Setup, backend-image preparation, Cloud connection/enrollment/recovery
and Presenter launch through existing owners. The current Presenter also
provides Stop demo and keep data / Start controller for a retained Test.
The [current baseline](../../qualification/current-baseline.md) separates
exact-candidate retained-Test API/UI, native Setup issuance, public consumer and remaining
installation/recovery/distribution gates. The ownership allocation below is
effective architecture, not a chronological missing-feature list.

<a id="staged-allocation-and-non-claims"></a>
## Installed engines and non-claims

The [installation engine](../../../contracts/distribution-installation/README.md)
validates and installs immutable bytes offline; it never creates Cloud state
or a vehicle run. The [installed-state boundary](../../../contracts/distribution-installation/installed-state.md)
separates selected programs and read-only inputs from private credentials,
mutable outputs and run state. Setup composes these engines without giving
the transaction readiness authority.

The [version-selection/recovery detail](../../../contracts/distribution-installation/version-selection.md)
implements explicit compatible manifest selection,
runtime-use leases, stale-action rejection and program-only recovery with the
original bytes retained. Ordinary selection requires no retained current run.
The separately guarded retained-Test `upgrade` operation permits a compatible
package change around one stopped Test, preserving its journal, VM, credentials,
backend bindings and history. It changes only the atomic package selection and
retains the predecessor; it does not migrate schemas or operate Cloud. See the
exact [update proof](../../../contracts/distribution-installation/version-selection.md#retained-test-package-update).
Native activation, the exact candidate's live update proof, retained-run rollback
and destructive removal remain separate gates.

The [native Setup](../../../contracts/distribution-installation/native-setup.md)
wraps the engines with bounded progress, explicit local preparation and launch.
Open demo restores the selected instance through existing Demo Control
ownership, leases and workspace layout. Opening Presenter alone does not
manufacture a controller or simulator.

The [first-use engine](../../../contracts/distribution-installation/cloud-first-use.md)
owns one-shot SDK enrollment, durable private attempt/key recovery and exact
unbound Subject references. The assignment owner rechecks a saved reference
before use; installation cannot bind it to a Unit. Native secure input and
the writer/leases preserve the same ownership boundary. Existing-account
certificate issuance has scoped native M1 evidence; new-account signup,
state migration, public notarization and the full native return journey are
not implied by that result.

Installing bytes reports `INSTALLED_NOT_ACTIVATED`, never demo readiness.
Backend import, Cloud access, controller/simulator startup and functional
delivery retain independent checks and the current baseline's verdicts.

## Impact and preservation

Demo Control initializes a separate
private local Gateway server identity during explicit first simulator start,
as defined in the [local-trust contract](../../../contracts/distribution-installation/local-gateway-trust.md).
This is local lab authority, not an Aos Cloud/OEM certificate or system trust
enrollment. It supplies the server-TLS prerequisite;
client mTLS and selected-Unit authorization remain unchanged.

Owner: integration distribution tooling and the existing Demo Control. No
vehicle service, Gateway, Factory, model threshold or AosCore change is needed.
Preserve existing source work, unrelated Test/Production data, credentials,
the video repository, package pins and warm build caches. Source tags remain
immutable; installation candidate identity is the manifest digest, not a
reused application version label.

Evidence is selected by the current baseline. A source
test, local installation and clean-system/live proof remain distinct verdicts.
