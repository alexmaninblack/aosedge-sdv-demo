<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Control

- Status: Draft
- Version: 0.19
- Prepared: 2026-09-07
- Owner: Demo Solution Team
- Architecture input: [High-Level Architecture 1.6](high-level-architecture.md)
- Scenario input: [Demo Scenarios 2.0](../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Architecture Flows 2.1](demo-scenario-architecture-flows.md)
- Requirements input: [Demo Orchestration Component Requirements 1.2](../requirements/components/demo-orchestration.md)

This is the implementation-design companion for the existing
[Demo Orchestrator](../requirements/component-decomposition-and-interface-register.md#cmp-orch),
not a new component or a replacement for the accepted requirements.
It records the documentation audit, agreed direction and proposals still to
review. Publishing this draft does not authorize runtime or Cloud changes.

<a id="native-demo-desktop--accepted-direction-2026-09-07"></a>

## Native demo desktop — accepted direction 2026-09-07

The operator accepted a single native Driving Control + Engineering Telematics
window, while CARLA/Unreal remains a separate window. Keep the current composed
layout and black background. Do not embed or capture CARLA video; the decision
avoids additional complexity and overhead, not a measured performance defect.

All lifecycle operations remain in Demo Control and available from CLI. The
native launcher will reuse them for everyday start, explicit Stop Demo and
layout restoration; it must not independently implement provisioning, recreate
an existing environment on open or delete Cloud Units on stop. First-time
Prepare remains an explicit, separate operation. Platform Team state stays
Cloud-only; native telemetry reuses Gateway/VISS and retains stale/unavailable
and advisory-not-implemented semantics.

The [Native Demo Desktop Plan](../planning/active/native-demo-desktop.md) records
the accepted order: source commit/push and bounded housekeeping first, combined
control/telemetry second, launcher third, then one-time dedicated-Space setup.
The existing Terminal dashboard described below is the current implementation,
not the intended final native surface. No new desktop implementation has begun.
The accepted direction amends only these host-side presentation/lifecycle
details; Factory .31, VDP payloads, Safe Stop authority and Production FOTA
exclusions remain unchanged.

## Studio Test target contract — 2026-09-09

The current target is [UI-STUDIO-026](../demo/mockups/aosedge-demo-interaction-specification.md#ui-studio-026--current-test-studio-contract).
The dated implementation notes below describe the earlier code, not a competing
current workflow. In particular, dual-VM Prepare, mandatory approval, universal
.31 guards and guest-derived right-panel status are not the accepted target.
No application change is claimed by this document update.

Implementation started on 9 September after the separately approved 2.8 source
checkpoint. The first source increment exposes `demo plan/prepare --target test`
(default), explicit `--target all` for engineering, and `vehicle initialize test`
for the first stationary-Manual connection before provisioning. Ordinary
`vehicle select` still requires a provisioned target. Only provisioning may
retain a confirmed initial Test connection; deprovision/delete remain detached.

`component prepare --profile v1|v2|v3` may omit the engineering version override.
The shared allocator takes the maximum observed local/Cloud version and the
retained high-water mark in `.local/release-continuity.json`, then reserves the
next major release under the existing writer lock. The continuity record stores
only per-identity versions, not run history or credentials, and survives Retire.
CLI and API use the same request/result path. These source changes are not yet
a full Studio or live E2E qualification; the current phase and integration gates
are recorded in the [delivery plan](../planning/active/demo-studio-delivery-plan.md#implementation-execution--9-september-2026).

| Shared operation | Current target contract | As-built gap / phase |
|---|---|---|
| Create | Catalog copy/overlay + Test boot/DNS/role + both backend processes/storage | Compose existing low-level create/start; backend lifecycle/context in P1 |
| Initial connect | Public stationary-Manual initialization; preserve ordinary select semantics | Expose existing internal initialization; P1 |
| Provision | Running selected Test → official provisioning → Online → verification membership | Narrow provisioning-only detached-source guard; preserve retirement safety; P1/P3 |
| Release Prepare | Operator selects content profile; shared allocator returns opaque release handle/version | Durable reservation survives cleanup; engineering explicit-version CLI need not be removed; P1 |
| Publish | Signed deployment bundle → recorded processing result → independent recipient observation | No approval gate for verification Test; publication may precede Provision or occur while vehicle Offline; P2 |
| First service Deploy | Bind current Test to this service's retained Group Subject; add only that service identity | Separate Brake/Tire Subjects (11 September amendment); no version or instance-count argument; package readiness and runtime qualification remain separate; P5 |
| Cloud observation | Unit components + service detail/instances + DMIPS + sample/read freshness | No direct VM read or product-result inference; P2 |
| Park/Resume | Same disks, identity, installed releases and product data; full local stop/restart | Shared composition/journal missing; no Create/reprovision; P1/P3 |
| Finish / New cycle | One shared scoped Retire across Cloud, local runtimes and product records | Existing environment retire remains local-only, not full cleanup; P1/P3 |

Use the [delivery plan's command surface](../planning/active/demo-studio-delivery-plan.md#6-cli-surface-reuse-first-add-only-missing-operations)
for proposed CLI names and the [action audit](../research/demo-studio-action-audit.md)
for exact API payloads/results. These are shared application operations, not
new subprocess wrappers. Keep completed-stage receipts, exact entity IDs and
minimal cross-run release continuity in the existing journal design. Backend
cleanup must retain its original current-run UID context until records are
cleared, even after the Cloud Unit is deleted. Group/TTL settings are accepted in UI-STUDIO-026, not a
pending design question. Expanded logs/errors/concurrent mutations are deferred.


## Test-first Presenter integration — 2026-09-06

Operator amendment: one `democtl demo prepare --image VERSION/ARCHITECTURE`
command is shared with the main **Prepare demo** UI action. `democtl demo plan`
reads its plan without mutation. The native current-run journal owns stage
completion and release selection; page reload only observes that journal.
Prepare reuses this run's v1 candidate (13.0.1 for the interrupted run), otherwise
chooses a monotonically newer release from local and Cloud catalogs. It creates
or resumes the matching dual-VM environment, signs/publishes/approves v1 before
provisioning, starts both VMs, provisions each into its role set, starts the
simulator and connects Test. Production FOTA stays excluded. Each stage uses
existing core operations and stops on a blocker, with no blind replay.

The hidden-terminal input is replaced by a native macOS dialog in UI and the
composite command. `democtl access setup` exposes that same input independently.
Use once keeps the value in process memory; Save in Keychain is an explicit
dialog choice for the fixed factory-SSH service/account. Neither argv, logs,
Git nor browser receives the value. Cancel/180-second dialog expiry stops the
operation. Regular terminal `vm start` retains its terminal prompt.

After an execution-review pause, the operator explicitly authorized the narrow
stationary-Manual command-deadline exception. Initial Test selection still
physically stops, blocks both paths and resets, then confirms a real Manual
frame with zero throttle/full brake before opening Test's path. A native
operator session is required. Ordinary handover stays in Safe Stop. First
actuator input restores the command deadline; ownership timeout/disconnect
still invoke Safe Stop. No AosCore gate, Factory image or VDP content is changed.
The native controller presents this as waiting for an explicit Manual or
Autopilot selection: it keeps full brake and emits no neutral commands or
focus-loss stop while in `manual_ready`. Ordinary manual driving still stops
on focus loss. An interrupted initial connection can be cancelled by existing
`simulation stop` only after a fresh, owned, physically stopped frame and
confirmed blocked data paths; it does not reprovision or delete either VM.

Live preparation evidence, 2026-09-06: the failed hidden-input UI session was
stopped; native password input completed successfully. Preparation reused the
owned 13.0.1/v1 publication, approved its Test batch, started/provisioned both
.31 roles and confirmed their correct Unit Sets and Online state. A dispatcher
import error was corrected before source attachment. The subsequent connection
exposed the native UI focus-loss stop described above; that failed simulation
was stopped through Demo Control and the corrected session started through the
same command surface. Resume skipped all completed Cloud/VM/publication stages
and reached `READY_TO_DRIVE`. This is resumed-run evidence, not an uninterrupted
fresh-create qualification.

At handoff, Test alone had its source gate open, the TLS probe observed
advancing VISS frames, and Controller reported stationary `manual_ready` with
zero commands/command timeouts/ownership timeouts. Guest component status
reported no active VDP and an incoming 13.0.1 transaction in
`waiting-for-safe-stop`; a prior `safe_stop_timeout` was retained as failure
history, not hidden or claimed as a successful install. The operator's drive
and Safe Stop activation/VDP startup are still pending. Original Factory image
bytes and Production FOTA remain untouched. Targeted gates passed: 83 Demo
Control tests, 41 protocol/control tests, 19 native UI tooling tests, strict UI
build and 76 UI tests. The native Swift controller was rebuilt, not the VM.

The Cloud serializer discrepancy is proven: Unit Set list omitted
`update_strategy` (null), detail returned `MinimizeRestarts`. New pre-provision
Production guards use the detail representation consistently. The one old
RESPONDED/201 empty-set upload can migrate only when the old guard exactly
matches a fresh list observation and the sole differing field is previously
unknown `update_strategy`; previous and canonical observations are retained.
Membership, IDs, validation mode and other policy changes still block.

The operator accepted the existing interaction mockup as the visual basis and
the sequence: screen composition, two-VM initialization, then Platform VDP
v1/v2/v3 on Test. Production remains provisionable but FOTA rollout is deferred;
do not turn its Unit Set into a verification set. Brake/Tire navigation remains
available without presenting unimplemented operations as successful.

The first implemented slice is `democtl ui serve`, a foreground loopback
engineering preview on the existing software-delivery UI port 18080. It serves
the built Presenter bundle and a fixed read-only projection of existing local
`status` / `image list` operations. No Cloud/guest reads, image hashing, arbitrary
request dispatch, mutation, browser credential or session capability is exposed.
Existing fixture screens require an explicit fixture parameter; missing local
observations never fall back to simulated readiness. Current UI qualification,
Cloud Online and native-window placement are not claimed from these local reads.
The operator visually accepted this composition on 2026-09-06.

The operator subsequently explicitly authorized both-VM create/start/stop,
Cloud provision/deprovision/delete, simulation start/stop and Test connection,
selected Test VDP prepare/sign/upload/approve, and environment reset without
backups. This resolves the earlier execution-review pause. Production FOTA,
original image deletion and arbitrary native dispatch remain excluded.

The implemented protected boundary uses same-origin port 18080, strict
Host/Origin/JSON checks and exact action fields. The backend alone owns a 256-bit
ephemeral capability for private loopback port 18600 (directory 0700, file 0400).
Normal shutdown removes listeners and capability. Mutation confirmation names
the actor, selection, target and effect; UI SSH enrollment uses the native
macOS dialog described above.
The fixed native allowlist invokes existing Demo Control application operations.

Receipts are ephemeral UI progress, not a second lifecycle store. One job runs
at a time; request IDs deduplicate within the session, generation IDs reject
stale submissions, and unknown outcomes block mutations without automatic
retries. Existing native journals own reconciliation. Background reads are local;
Cloud/guest reads are explicit and timestamped. Stop the UI server when idle.
Native-window composition, prebuilt-container hosting and live UI E2E remain
outstanding; source tests do not qualify these boundaries.

Planned Test flow preserves the known ordering: select the catalog image,
create both overlays, prepare/sign/upload/approve a new v1 release before
provisioning, start/provision both roles, start simulation and connect Test.
Then publish and authorize increasing v2/v3 content-profile releases separately,
observing Cloud acceptance, Safe Stop waiting, installation, process startup and
data readiness as distinct facts. End/reset follows the existing simulation-stop,
Unit-deprovision, Unit-delete, remaining-VM-stop and local-retire order.
Inapplicable Cloud stages are skipped only from a never-provisioned journal;
empty environments use existing retire/orphan checks. No image rebuild is required.

First-slice evidence: production UI build and strict typecheck passed; 71
UI tests and 10 Presenter-server/CLI tests passed, including fixed read-only
requests, same-origin restrictions, unavailable-state handling and blocked
filesystem/mutation requests. This is not a live provisioning or FOTA proof.

Protected-slice source evidence: strict UI build/typecheck, 76 UI unit tests,
18 Presenter/API/CLI tests and documentation quality gate passed. Tests cover
Cancel, duplicate clicks/IDs, stale generations, unknown responses, same-origin
dispatch, private capability isolation/cleanup, result projection and reset
ordering (including empty/never-provisioned journals). Executors are test doubles;
these checks perform no real provisioning, publication or approval.

## Accepted Factory .31 Test baseline and corrections — 2026-09-06

Successor source integration, 12 September: `democtl image build
6.1.1-maninblack.32` uses pinned Platform source and the same offline Builder,
image layout, artifact catalog and transfer-digest check. It includes the proven
CM/SM service-recovery patches and persistent native service-resource/startup
configuration. Build success is not clean Test/reboot qualification; .31 and
Production remain preserved until the explicitly scoped successor check.
See the [current delivery checkpoint](../planning/active/demo-studio-delivery-plan.md).

Operator amendment after the fresh .31 run: `vm start` stages role assignment
in an owned transient SM `ExecStartPre`, after the existing store mount/bootstrap
and before the native process reads its configuration. This replaces early
writing into a potentially unmounted directory. The role's persistent location
and authority stay unchanged; no extra SM restart or image rebuild is introduced.
Provisioning confirms the actual role in its existing guest readiness read.

The same amendment authorizes removing repeated broad Cloud comparisons:
exact-ID bundle/batch confirmation replaces the second full snapshot; approval
does not depend on a local archive or Test Online; Unit wait cycles reuse one
authenticated client and known Unit/Node IDs. Keep OEM authority, exact target,
Production non-mutation observation, uncertain-attempt reconciliation and
destructive cleanup boundaries. The package README records the executable behavior.

Production update continuation is deferred by the operator on 2026-09-06,
after consultation with the Aos platform developers: the current platform
delivers updates only to Units in verification sets; delivery to ordinary
Production sets awaits a platform release. This is operator-reported platform
information, not an independently verified release guarantee. The earlier
HTTP 403 observation does not establish the cause and does not justify changing
OEM permissions or marking Production as a verification set. CARLA handover
completed, but Production FOTA/Safe Stop qualification did not. Ordinary
component status must not query the deferred fleet-validation/campaign APIs;
the Production non-mutation observation remains. Resume Production FOTA only
after the platform change is confirmed and its qualification is authorized.

The Test 10/v1 -> 11/v2 -> 12/v3 transitions and visual behavior were confirmed
by the operator. The [current baseline](../qualification/democtl-release-checkpoint.md#current-test-baseline)
records immutable artifact digests and the separate fresh-overlay repeat,
advisory, independent-consumer and broader qualification exclusions.
A v11 API correction replaces unsupported GET of an individual deployment
bundle (HTTP 405) with collection lookup of its exact UUID; verification-batch
detail GET remains valid.

The operator approved initializing the manufactured Test/Production role in
`vm start`, before provisioning enables SM. Source selection updates only its
public source inputs and does not restart SM. The existing Test-only
`component sm-build` / `component sm-apply` commands qualify the factory-marker
correction on the preserved .30 Test; they do not rebuild the Factory image,
alter CM timeouts, bypass Safe Stop or modify Production. The marker remains a
terminal empty-slot baseline during first-install waiting and becomes inactive
when a real component is installed. Runtime start rejection must return a
terminal failed status rather than leave an instance activating. Exact scope,
tests and live results are recorded in the
[release checkpoint](../qualification/democtl-release-checkpoint.md).

## Implementation Checkpoint — 2026-09-05

The user authorized the first read-only status implementation after reviewing
this draft. It now reads local QEMU/QMP state, optional guest SSH/DNS and
separate authenticated OEM/SP Cloud observations through the same CLI/API core.
Defaults are all targets and an 8-second per-probe budget. There are no hidden
mutations, repairs or lifecycle wrappers. The package README defines executable
options, local configuration and result/exit-code semantics.

The next authorized local increment implements image list and environment
create: one independent format-preserving factory copy, fresh requested role
overlays and an atomic current-run journal. Status reads its manufactured role
bindings without inheriting the retained .27 Unit identity. No live VMs or Cloud
objects were changed to test this increment. Prepare, handover, park/resume,
retirement, full recovery and AosCore connection proof remain unimplemented.
No historical baseline/topology discrepancy is resolved by local creation.

The next local increment, authorized 2026-09-05, implements environment retire
only for an unused successful create. It removes released, unmodified role
overlays, the local factory copy/manifest and finally the current journal; it preserves the original artifact,
and never calls Cloud. A full provisioned-environment retire remains unavailable.
Fixture proof covers create/retire/create, idempotent repeat, interrupted unlink,
held/modified disks and scope/path exclusions; no real demo environment was
deleted during this implementation.

The documentation gate now includes apps/*/README.md, resolving the audit's
unscanned package-link errors. Fixture tests cover stopped/missing/ambiguous
VMs, QMP allowlisting, SSH errors, role/owner/permission projection, partial
results and secret exclusion. Live reads observed the retained test VM stopped
and its Unit Offline/provisioned, with authenticated OEM and SP responses.
No VM was started, so live guest checks are not qualified by this checkpoint.

The authorized local VM increment now implements start/stop through the same
CLI/API core: exact owned QEMU processes, one shared DNS service, explicit
interactive first SSH enrollment, bounded guest readiness and graceful poweroff.
Successful stop can prove a booted guest remains unprovisioned and bind that
proof to its stopped disk, extending local retire without authorizing Cloud
retirement. Process/guest doubles and isolated protocol fixtures cover this
increment; no retained VM, Cloud object or original artifact was modified.
Live boot/SSH qualification remains an operator test, not an inferred success.

The subsequent authorized terminal-equivalent acceptance is recorded in
[local VM CLI acceptance](../qualification/democtl-local-vm-lifecycle.md).
It supersedes the initial fixture-only qualification limit for the exercised
.27 local create/start/stop/retire slice, not for Cloud or complete-demo flows.
It also records the measured 90-second ceiling adjustment, concurrent VM boot,
readonly SSH configuration, guest DNS utility and immediate TCP restart fixes.

## Purpose and First Slice

The subsequently authorized Unit slice implements unit provision/deprovision/delete
for the current run, through OEM APIs and the official SDK. Its commands,
postconditions and exclusions are defined under Unit Lifecycle below; actual
results and qualification gaps are in [Unit CLI acceptance](../qualification/democtl-unit-lifecycle.md).
It supersedes earlier placeholder statements for these three operations only.

Demo Control provides the same tools for engineering preparation and the
future Demo UI. An operator can use `democtl` without opening the UI; the UI
will call the same application core through a local API.

The initial operation scope is agreed as:

- selecting an immutable factory image, without hard-coding `.27`;
- targeting the test VM, production VM or both;
- observing status, including access and the Aos platform;
- creating and starting VMs, provisioning Units and selecting one Current Vehicle;
- safely switching the live source between Test and Production;
- parking/resuming the same environment without changing its identities;
- explicitly retiring Cloud Units and disposing of their local VMs.

Signing, deployment-bundle upload and explicit verification-batch approval are
implemented for the authorized VDP family increment below. Full driving/scenario automation
remains a later slice. Source selection and the Safe Stop/reset transitions required
for switching, parking and retirement belong to the agreed operation classes
below. Status, image list and local create are implemented today. The initial VM/Unit lifecycle is
not, by itself, proof of complete scenario retirement.

## Agreed Lifecycle Operation Classes

Design agreement: 2026-09-05. The five classes below are agreed for the shared
CLI/UI application core. The CLI surface below is agreed and its first local
creation increment, low-level VM start/stop and unprovisioned-local retirement are implemented; the other
classes and full Cloud-and-local retirement remain unimplemented; low-level
Unit retirement is now implemented separately.
Implementation authorization does not imply starting existing VMs or mutating
live Cloud objects as incidental tests.

### 1. Create a New Environment

Select an explicit prebuilt immutable factory image, without a fixed version
in code. Normally create two independent copy-on-write overlays: Test and
Production. Allocate separate local VM identities, access endpoints and
runtime resources. Never clone a provisioned overlay as a fresh vehicle.

The result is a local manufactured environment: no Cloud Unit identities and
no Current Vehicle assignment. The original image is unchanged. Single-role
engineering use remains distinct from the complete dual-role demo; the
existing layout/topology discrepancies below must still be reconciled.

### 2. Prepare the Environment for Use

Start the owned shared infrastructure (including DNS, CARLA and Gateway) and
the selected VMs. Provision each fresh VM once, retain its exact Unit/Node
binding, assign the corresponding Test or Production Unit Set and confirm
Cloud Online. Only then select the Current Vehicle and authorize its
Gateway/CARLA connection; the normal new demo starts with Test selected.

CARLA, Gateway and network reachability may be prepared before provisioning.
The authoritative vehicle selection/connection comes after provisioning,
because it is bound to the known Unit/Node identity and verified role.
This is the demo's identity/selection ordering, not a requirement for CARLA
to be running in order for AosCloud provisioning itself to work.

This follows [onboarding](demo-scenario-architecture-flows.md#af-m1-lc) and
the [per-Unit VISS identity lifecycle](../../contracts/viss-trust-telemetry-profile/viss-trust-telemetry-profile.v1.json).
VM boot, provisioning, set assignment and vehicle selection remain separately
observable steps, even when presented as one operator workflow. A parked
environment uses resume, not another fresh provisioning attempt.

### 3. Change the Current Vehicle

Switching Test to Production, or back, is an explicit operation:

1. Enter Safe Stop.
2. Disconnect the current VM from the live source and confirm detachment.
3. With no VM attached, perform the agreed scene reset and confirm its new
   reset generation.
4. Authorize the other exact Unit and establish its source connection.
5. Confirm the selected vehicle's stage-appropriate operation.

At all times, **zero or one VM** is assigned to CARLA/Gateway, never two.
Both VMs may remain Cloud Online; Cloud connectivity is independent of live
source selection. A failed or uncertain detach/reset blocks the next
assignment. Follow the existing
[exclusive live-source contract](../../contracts/exclusive-live-source-assignment/exclusive-live-source-assignment.v1.json),
not an additional source-selection mechanism or a reprovisioning flow.

### 4. Park and Resume

Parking is non-destructive: Safe Stop, confirmed source detachment, graceful
VM shutdown and shutdown of the environment's owned infrastructure. Preserve
overlays, image references, Unit identities, provisioning and current-run
recovery state. Parking is not deprovisioning, cleanup or automatic backup.

Resume uses those same VMs and Cloud identities. Re-read actual state after
restart, restore the owned infrastructure and VM processes, then restore the
intended single Current Vehicle through the same selection rules. Do not
create replacement overlays, reprovision or automatically resume driving.
An unresolved previous action remains visible and requires reconciliation.

### 5. Retire and Delete the Environment

Full retirement is explicitly distinct from parking. Safe Stop and detach
the live source, then retire the exact Units that were created for this
environment. Follow the existing
[retirement order](../../contracts/demo-run-state/demo-run-state-profile.v1.json):
Cloud offline/deprovisioning with authoritative new/Offline confirmation, VM shutdown
and overlay release, scoped role-set membership removal, Unit deletion and
authoritative absence reconciliation.

Delete local overlays and run-specific access/runtime material only after
the applicable Cloud retirement and owned-data cleanup are proven complete.
Do not infer Cloud deletion from local disk removal. Conversely, deleting a
Cloud Unit does not itself remove a local VM. Never invent a Cloud identity
or attempt deprovisioning for a never-provisioned local overlay.

Preserve the immutable factory image, persistent Unit Sets and Cloud
audit/release history. No automatic backup is added. When functional backends
or other later stages are in scope, their cleanup follows the existing full
retirement contract; completing the first VM/Unit slice alone is not proof
that complete scenario retirement has been implemented.

The initial implemented retire scope is UNPROVISIONED_LOCAL_CREATE: successful
create with no authoritative Cloud identities or live source and no open disk
handles. An untouched overlay must inherit all data from its factory backing.
A booted overlay instead requires the local stop proof described below.
This removes exactly the recorded overlays and generated access keys, then local factory copy
and manifest, and finally the journal without backup; it keeps the original
artifact. Unproven/changed stopped disks, unknown runtime files,
failed create and unobservable ownership block this narrow path. A separately
authorized Cloud-retired CLI-only path is described under Unit Lifecycle;
absent local Unit IDs alone are never a cleanup proof. Complete scenario runs
still require full R0.
The 2026-09-06 cleanup amendment extends this same `environment retire` command
to the stopped telemetry-demo source and completed component-operation records.
It requires deleted Cloud identities, stopped VMs, a stopped Controller/Gateway,
terminal source-run manifests and no live owner/open file handles. It removes
only the fixed source-output filenames inside owned UUID run directories,
the empty control directory, generated SSH access, overlays and factory copy,
then the journal. Unknown files, symlinks and unresolved publications block
cleanup. An uncertain Unit-scoped send may be discarded only after fresh
authoritative deletion of that exact target; this is not a successful-delivery
claim. A historical upload marked `RESPONDED` with HTTP 201, the exact recorded
deployment ID and a confirmed approval/batch ID is reconciled inside this same
command: read the deployment-bundle collection once, match the completed bundle
and its sole component/version, and read the recorded verification batch to
confirm OEM, component identity, architecture and version. No upload or approval
is repeated; deleted Units are not recreated or used as component-status targets.
The journal records `PUBLICATION_ONLY` confirmation, not retrospective proof of
an unchanged Production snapshot. Missing, ambiguous or unavailable Cloud proof,
unknown publication outcomes and unresolved approvals still block cleanup.
The runtime-file plan participates in existing interrupted-unlink
reconciliation. A stopped single-Test borrower may retire without stopping its
external canonical DNS bridge. Published images/bundles, Unit Sets, Cloud release
history, source repositories, Builder and caches remain untouched. This is not
general backend or full functional-scenario R0 cleanup.
An interrupted local retire preserves per-file intent; another explicit retire
reconciles remaining targets before continuing. Missing/corrupt journal data is
never replaced by guessed ownership or a recursive directory delete.

### Cross-Cutting Results and Recovery

Keep the operated-on VM set separate from the Current Vehicle selection.
An operation may target Test, Production or both, while source selection
remains Test, Production or none; selecting both targets never means
connecting both to CARLA.

Return the observed result of each step and each VM. If Test succeeds and
Production fails, retain both outcomes; do not erase success, report the pair
ready or restart the whole workflow. After interruption or response loss,
reconcile the prior attempt before another mutation. Status remains a
read-only operation, never an implicit repair or rollback.

Readiness is relative to the lifecycle stage. Distinguish VM Running, guest
access, DNS, Cloud Online, Current Vehicle assignment and live data flow.
At [the empty-provider baseline](demo-scenario-architecture-flows.md#af-g0-rt),
the infrastructure can be ready for VDP installation while the VDP data path
is absent by design. Do not report a connection fault merely because VDP has
not yet been deployed; equally, source selection alone does not prove the
complete VDP chain is working.

## Agreed CLI Surface

<a id="native-service-package-preparation"></a>

### Native service package preparation — 2026-09-11

The N4 source increment exposes:

```bash
democtl service prepare brake --profile v1
democtl service prepare brake --profile v2
democtl service prepare brake --profile v3
democtl service prepare tire --profile v1
```

`--profile` selects immutable functional content here; optional
`--cloud-profile` selects the configured SP (default `service-provider`).
The existing `service list/status/inspect --profile` still selects a Cloud
profile. Preparation requires the existing committed ARM64 product export
from `service build <team> --content-profile <profile>`; it never starts an
implicit build or a VM. Tire now has its own real ARM64 product export and
supports only functional profile v1; it never substitutes the diagnostic scaffold.

One SP session reads the owned service catalog and, for an existing exact
codename, its version collection. It does not scan Units, inspect an OCI
manifest, assign a Subject or mutate Cloud. Failed/pending published versions
also reserve their number. An incomplete or unavailable read blocks rather
than appearing as an empty catalog.

The existing continuity ledger allocates the next version once. A successful
result returns `releaseHandle` (for example `brake/8.0.0`), `version`,
`contentProfile`, bound SP/service identifiers and `packagePath`. The staging
layout is `services/<team>/releases/<version>/` in the artifact catalog. One
value populates publication metadata and root-owned/read-only package data at
`/usr/share/aosedge/service-release.json`. Only exported executables, public
licenses and that release file enter the payload. Unit/VDP metadata, native
instance identifiers, tokens and private trust never enter a reusable package.

The official installed Aos signer validates schema and paths without signing
credentials. Output is **PREPARED_NOT_RUNTIME_QUALIFIED**, not published or
deployable proof. The configuration requests the accepted quotas, minimum one
instance, seven-day offline TTL, team-specific input resource and exact KUKSA
paths; native outbound enforcement and loader/library closure still need N6
proof. No resource configuration is activated by preparation.

Temporary exception accepted on 11 September 2026: the platform team reported
via the user that the Cloud bundle builder fails on service `permissions`.
`service prepare <team> --profile <P> --without-permissions` omits only that
configuration section, keeps the compiled product payload unchanged, and marks
the receipt `withoutPermissions=true`, `DELIVERY_ONLY_NO_KUKSA_AUTH`. Signing
checks that the section remains absent. The normal default and accepted native
permission contract are unchanged. This mode qualifies delivery/version handling
only: no KUKSA access, telemetry, advisory or functional service readiness is
claimed. It must not trigger a shared token, disabled broker authentication or
an SM modification. Return to normal preparation with a newly allocated release
after the Cloud fix; do not overwrite a published workaround package.

The subsequent approved lifecycle experiment adds `--demo-no-telemetry`
alongside `--without-permissions`. Only this explicit mode appends the bootstrap
flag and overrides `noFileLimit` to 1024. The bootstrap still validates native
identity and public metadata, rejects Production, then stays alive until native
SIGTERM/SIGINT without starting analytics or any credential/network operation.
It emits `DEMO_LIFECYCLE_ONLY / NOT_READY / TELEMETRY_DISABLED`, not successful
telemetry. The receipt marks `demoNoTelemetry=true` and
`DEMO_LIFECYCLE_ONLY_NO_TELEMETRY`. This proves container launch/version
replacement only; native authorization, normal quotas and N6 functional gates
remain unchanged. There is no missing-secret fallback.

The [3.0.0 experiment](../qualification/demo-studio-implementation-progress-2026-09-11.md#permission-free-delivery-experiment)
exposed a native launch/update failure. The subsequent authorized SM/CM patch
proof reached Active Brake 6/v3 and Tire 5/v1 through normal publications, with
unchanged Subjects and no restart between updates. This closes replacement in
the inert no-telemetry mode, not authenticated functional operation.

### Explicit synthetic backend integration — 2026-09-11

The user-authorized `--demo-mocked-data` preparation mode requires
`--without-permissions` and is mutually exclusive with `--demo-no-telemetry`.
It selects the actual product bootstrap's isolated synthetic-data path, retains
native Test identity and allocated package version, and sets `noFileLimit: 1024`
only for this explicit demo mode. The receipt reports `demoMockedData=true` and
`DEMO_MOCK_BACKEND_ONLY`. It does not enable a missing-token fallback.

```bash
democtl service prepare brake --profile v3 --without-permissions --demo-mocked-data
democtl service prepare tire --profile v1 --without-permissions --demo-mocked-data
democtl backend inspect brake
democtl backend inspect tire
```

Prepare returns the handle used by the existing sign/upload/cloud-status
commands. No new publication or assignment path is introduced. Synthetic
samples/features use separate service state and backend databases; neither
normal product queries nor Gateway advisory output consume these records.
See the [bounded integration record](../qualification/demo-mocked-backend-integration.md).

`backend inspect <team>` is a read-only observation of the exact owned backend
container, its readiness/current-Test context and isolated mock summary. It
accepts only Brake or Tire; no arbitrary URL or selector is accepted. The
existing backend adapter makes bounded HTTP reads on its fixed loopback ports.
No guest, Cloud mutation, restart, database write or lifecycle journal write
occurs. A stopped backend is `STOPPED`; unavailable/malformed observations are
`PARTIAL` or blocked, never an empty successful result. `OBSERVED` proves the
read, not that the current service delivered a record.

Presenter reads this same operation through fixed same-origin routes
`/api/presenter/backend/brake` and `/api/presenter/backend/tire`. Cloud alone
supplies installation/instance/connection state. Backend readiness, received
records and Cloud runtime remain separate facts. The visible team view refreshes
at a ten-second interval without overlapping requests, shows last-known data
on failure and clears records when Test identity changes. Every synthetic
record is visibly marked `MOCK DATA`, with real service version/identity and
backend receipt time available in the detail view. No vehicle functionality
is inferred from mock records.

Existing retirement accounts for both ordinary and mock databases before
removing an owned volume. Private mock cleanup uses separate preview/execute/
empty-proof routes and evidence; an ordinary empty proof cannot authorize
discarding unproven mock data. This cleanup was tested with isolated fixtures;
the current live Test and backend volumes remain preserved.

A schema failure retains the allocated number and leaves no committed
package. Another explicit prepare allocates a new number; existing packages
are never overwritten. [Signing/publication](#native-service-publication)
consume the returned handle rather than asking for a second version. These
operations are not yet exposed as browser mutation capabilities. N4 public-input
projection and transient resource activation are available separately; full VM cold-start qualification remains pending
under the [accepted runtime-input contract](demo-control-service-inputs.md).

### Native service build and public-input engineering operations

```bash
democtl service build tire --content-profile v1
democtl service build-status tire
democtl service runtime-inspect test
democtl service runtime-prepare test
democtl service runtime-activate test
```

`service build` also supports Brake v1/v2/v3. It builds the committed product
source, runs its ARM64 tests and validates both real executables and the export
manifest. A completed source/profile receipt is reused without rebuilding.
`build-status` reads this repository's existing BuildKit history and bounded,
redacted error lines; it never starts or retries a build. Completed compilation
is **BUILT_NOT_LIVE_QUALIFIED**, not proof of service execution.

`runtime-prepare test` is a fixed engineering operation, not a Presenter read
or container launcher. It reconciles native IAM v6 `GetSystemInfo.system_id`
with the existing Test provisioning context, reads the committed VDP slot and
running process, then atomically publishes the five public fields and public
KUKSA certificate into both declared source directories. Native IAM is read
over a temporary SSH Unix-socket forward, with the installed SDK trust root,
server-authenticated TLS and fixed server name `main`. It does not log in to
Cloud, install an SDK in the guest, modify DNS or persist a second identity.

The result includes `changed`, `noOp`, `vdpVersion`, `metadata` and `sources`.
An unchanged repeat leaves files and directory inodes intact. Directories are
root-owned 0755; public files are 0444. Public trust comes only from the accepted
Unit-local certificate, validated for `Server`; no private-key content enters
the projection. Missing identity, active transaction, slot/process mismatch,
changed source, symlink, unexpected file or unsafe permissions fail closed.
No staging file becomes a successful readiness result after a failed check.

`resourcesActivated`, `containerActions` and `coldStartQualified` are explicitly
false. This command neither activates resource configuration nor restarts SM,
assigns services, publishes a package or proves retained-assignment recovery.
It is Test-only and is not exposed to browser mutations. The accepted cold/warm
split and remaining boot qualification are recorded in the
[runtime-input contract](demo-control-service-inputs.md#cold-start-ordering-conflict--11-september-2026).

`runtime-activate test` installs temporary configuration under
`/run/democtl-service-inputs` and one systemd drop-in. It preserves all existing
resources, changes only the per-container token tmpfs root to 1777 and adds the
two team-specific public-input binds. With no legacy service assignments, it
performs one controlled SM restart using the same executable. `ExecStartPre`
projects verified committed inputs without requiring a running VDP;
`ExecStartPost` checks recovered process/slot agreement. Native SM retains
container launch/recovery ownership. No new service daemon is installed.

The command returns `cold` and `verification` observations, the unchanged SM
binary digest, service status and `transient=true`, `rebootQualified=false`.
An exact unchanged repeat verifies/reuses the configuration without a restart;
conflicting staged data blocks rather than overwriting it. If SM startup fails,
only this new drop-in is removed and the original configuration is restarted
once. Interrupted VDP state defers public projection instead of fabricating
readiness. Full VM reboot requires later integration into the immutable image;
this temporary activation is not that qualification.

An explicit `democtl service runtime-activate test --restart-sm` restarts only
the already activated Test SM once, after verifying that its existing input
program, drop-in and resource configuration are unchanged. It writes no new
configuration and refuses first-time activation. The result includes the old
and new PIDs and verifies the same binary digest. Unlike initial activation,
this restart branch never retries or rolls back through a second restart on
failure or response loss; use read-only reconciliation before another decision.
An active SM does not by itself prove that assigned services recovered.

For the authorized .31 Test recovery, initial resource activation may retain
existing Cloud assignments only when the exact Unit/VM/factory identities,
the journaled qualified SM application and its current PID match, and native
inspection proves there are no container instances. This exception restores
lost `/run` declarations after reboot; it does not permit a general resource
migration while arbitrary services are running.

`democtl component cm-apply test --restart-cm` is an explicit CLI-only recovery
action for the already applied qualified Test CM. The default repeat remains
a no-op. The flag verifies the owned unchanged transient binary/drop-in and
qualified active SM, restarts CM once, and verifies that SM's PID and committed
VDP records were retained. It does not upload, reassign, reset native databases
or retry after a failed/uncertain response. Resource readiness must precede a
recovery attempt; a successful manager restart is not service-start evidence.

`component logs test` retains a bounded SM network/preparation projection
separate from the last general events, so an initial preparation failure is
not hidden by later status traffic. Native identities and fixed error labels
are retained; credentials, transport payloads and unrestricted instance bodies
remain excluded.

<a id="native-service-publication"></a>

### Native service signing and publication — 2026-09-11

Use the exact handle returned by preparation; `brake/8.0.0` below is only an
example, not an instruction to allocate or publish that number:

```bash
democtl service sign brake/8.0.0
democtl service upload brake/8.0.0
democtl service cloud-status brake/8.0.0
```

All three use the recorded SP profile/owner; there is no account, version,
Unit, command or path override. Neither signing nor upload rebuilds the
product or assigns a service. Signing confirms the bound SP, copies only the
verified prepared files to a temporary signer directory and uses the installed
official Aos signer. It verifies the real RS256 envelope, signed file hashes
and byte-for-byte payload/config equality before committing
`deployment-bundle.tar.gz` and `signed.json` beside `prepared.json`. A repeated
sign verifies and reuses that bundle. If a completed bundle survived an
interruption without its receipt, verification reconstructs the receipt without
resigning. Changed bytes, modes, unsafe paths or version/identity mismatch block.

Upload has one authenticated SP session: read bounded service/version/bundle
collections, prove the same owner/codename and an unused newer version, then
check existing assignments to this exact service. No assigned Units is valid
before Provision. Otherwise every assignment must be the current owned Test
from the existing lifecycle context. Any other Unit, including Production,
blocks without modification. No OEM role expansion, Unit Set scan, Subject
creation, batch approval or explicit send is hidden in publication.

The fixed shared transport performs one `POST /deployment-bundles/upload/`
with multipart field `file`. This is the same route used for FOTA, authenticated
as SP for SOTA. `201` returns **ACCEPTED**, not Ready or Running. It records the
deployment ID immediately and does not poll or sleep. A later explicit
`cloud-status` reads the bundle collection by that ID and the same owner's
service/version catalog. **READY** requires the exact completed service bundle
and a ready matching service version; it does not prove installation or
functional health. Processing, errors and unknown states remain distinct;
safe `build_info` is retained and sensitive text is redacted. These shapes are
from the [public Aos Cloud v11 OpenAPI](https://api.aoscloud.io/api/v11/openapi.json),
re-read on 11 September 2026. The bundle detail route has no GET operation.

The existing artifact directory holds one `publication.json` intent/receipt.
It is not a second Unit registry or a credential store. Intent is written
before the worker runs. An explicit failed-preflight response permits another
operator call because no POST was attempted. If a POST or worker response is
uncertain, further `upload` calls perform observation only, never a second POST.
If the response ID was lost, matching a codename/version alone cannot prove
the uploaded signed bytes: report **UNCERTAIN** and candidate IDs without
adopting them or silently retrying. No automated resolution is claimed for
that case. Observation preserves the original receipt and does not rehash
the payload or signed archive; signing/publication perform those trust checks.

Live Brake/Tire `1.0.0` bundles were signed and accepted by the upload API on
11 September, after migrated backend activation. Both Cloud builds then failed
with an architecture error; neither service was assigned. Exact evidence and
remaining runtime gates are in the [checkpoint](../qualification/demo-studio-implementation-progress-2026-09-11.md).
The observer treats `building` as processing, not success or an unknown state.
After the user's OEM architecture correction, both 2.0.0 uploads created service
identities/versions but failed Cloud bundle building; the checkpoint records
the exact IDs. `service inspect <service-id> <version-id>` exposes the documented
`container_build_info` through bounded secret-redacting projection; a null value
means the API provides no diagnostic, not that the build succeeded.
No browser mutation capability is added in this increment.

### Native service assignment — source implemented, live proof pending

```bash
democtl service assign <catalog-service-UUID> --target test
```

Use the catalog UUID returned by a publication observation, not a release
handle or team label. An accepted upload receipt and exact catalog read resolve
team/SP ownership. The published version is observed, not selected by assignment:
assignment sends only `service_ids`. Package `ready` is reported separately and
is not a local prerequisite to configuring Subject bindings; the native API may
still reject a request. An uploaded or failed bundle is never presented as ready.

The user-approved 11 September amendment replaces the shared Subject with two
retained OEM Group Subjects: `AosEdge SDV demo Brake` and `AosEdge SDV demo Tire`.
Each contains only its logical service, independent of release number, and is
bound only to the current Test's native system UID. Exact identities are stored
under `demoSubjects[serviceId]` in the existing run journal. Creating/assigning
one does not change the other; future per-Unit subsets need no shared-service
membership edit. Production remains unsupported by this command. Factory/default
Subjects are untouched. A legacy shared record is blocked for explicit
reconciliation, never silently adopted, renamed or discarded.

Each POST intent is recorded in the existing run journal before dispatch;
the returned exact UUID/creator is retained and authoritative reads reconcile
the result. A matching label is never enough to adopt an unrecorded Subject.
A lost create UUID remains uncertain and is not replayed. Known bind/assign
uncertainty can be reconciled by read; there are no blind retries.
`ASSIGNED` means desired binding only; Cloud-reported instances are separate,
and the result explicitly sets `runtimeQualified=false`. Browser mutation and
Subject retirement integration remain separate work; do not reset this run to
work around an assignment failure. The retirement guard covers both the legacy
record and the new per-service records; no retained identity can be lost through
the ordinary Retire path before that integration is implemented.

`service list --profile oem-delivery` also reads the available architecture
codes and those assigned to this exact OEM. This is read-only diagnosis; it
does not change tenant settings or pretend these lists prove why a Cloud build
failed. SP publication preflight does not add these OEM reads.

### VDP Family Increment — Authorized 2026-09-06

Repeat-cycle amendment, approved 2026-09-06: functional profiles `v1`, `v2`,
`v3` are independent of Cloud release numbers. Repeat the existing contents as
4.0.0/profile v1 (7 signals), 5.0.0/profile v2 (15), 6.0.0/profile v3 (23).
Later cycles may use 7/8/9 and onward with an explicit profile; release major
never selects functionality. This supersedes the old-version reapproval and
addressed-send experiment as the repeatable-demo workflow.

`component prepare VERSION --profile v1|v2|v3` reuses pinned signed
1.0.16/2.0.0/3.0.0 payloads. Only release metadata, capability digest, active
profile VERSION/MANIFEST_SHA256 constants, package version and provenance/SBOM
metadata change. Application code, native dependencies, paths, capabilities,
contract references and advisory declarations stay those of the chosen profile.
All active runtime/provider/manifest/inner/outer release versions agree. No
existing artifact is overwritten. Preparation increases local release numbers;
upload requires a number above the Cloud component catalog. Publish, approve
and observe each step before the next. Scope: Test .29 only, 4→5→6,
telemetry-only; full advisory/mTLS remain deferred. No component deletion,
force-send, reprovisioning, Factory rebuild or Production/fleet validation
change is part of this cycle. All actions remain Demo Control operations.

The operator approved implementing the real additive VDP v1/v2/v3 releases
and testing consecutive FOTA updates on Test only. All component preparation,
inspection, unpacking, validation, signing, deployment-bundle upload, explicit
batch approval and component observations must be Demo Control operations,
available from both CLI and the shared application core. No standalone workflow
helper or manual publication bypass is allowed. Official signer and Cloud
adapters may be used inside that core.

The sequence is: correct and prove physical Autopilot-to-Safe-Stop; preserve
immutable .28 and working v1 (release 1.0.16); prepare real 2.0.0 and 3.0.0 with
coherent metadata and the working component runtime/dependency layout; verify
7/15/23 additive signals and the full v3 typed advisory path; then run one fresh
Test .28 through v1, v2 and v3 without reprovisioning between releases. Approve
one version at a time and prove actual active version plus data, not merely
Cloud Installed. Production, original image bytes and existing signing trust
are unchanged; no VM image rebuild or backup is part of this increment.

Factory .29 continuation, explicitly authorized 2026-09-06: repeat the existing
1.0.16 -> 2.0.0 -> 3.0.0 artifacts on a fresh Test .29. Preserve Test .28's
provisioned Unit/disk and current Production. `component unapprove VERSION`
temporarily sets only the exact existing 2.0.0/3.0.0 verification batch approval
to false; `component approve VERSION` restores approval sequentially. Both
resolve existing artifacts/batches, journal before one attempt and confirm via
Cloud readback; neither uploads or changes fleet validation. A fresh single-Test
qualification observes the sole member of the already-bound Production set as
a read-only guard, without adopting that VM into its lifecycle journal.
`unit unassign test` requires a stopped, detached, provisioned Test and removes
only its bound Test Vehicles membership, preserving the Unit, disk and all
other memberships. It does not deprovision or delete. These amendments use the
same shared CLI/API core and journal, not standalone administrative helpers.

Addressed delivery amendment, explicitly authorized 2026-09-06:
`component send VERSION` requests one existing approved/Ready VDP 2.0.0 or
3.0.0 for the journal's exact Test Unit via the official
`POST units/{id}/components/send-requests/` with one `update_component_ids`
entry. The current live authorization is for 2.0.0 on Test .29. IDs are resolved
from the authenticated Cloud snapshot, not caller inputs. A signed local
artifact, unique existing bundle/batch, OEM approval and unchanged Production
are required. This explicit request is separate from approval and performs no
upload, re-signing, fleet validation, set/model change or guest restart. A
missing available-components entry is reported, not silently treated as proof
that Cloud will accept the request. Intent is recorded before one attempt;
repeat reconciles existing state without reposting. HTTP acceptance plus
request/Unit post-read is not proof of VM activation; observe runtime separately.

Implemented commands are `component list`, `component inspect VERSION`,
`component unpack VERSION`, `component prepare VERSION`, `component sign VERSION`,
`component verify VERSION`, `component upload VERSION`,
`component cloud-status VERSION`, `component approve VERSION` and
`component status <test|production>`. The package README is authoritative for
their exact behavior. Approval means verification batch only, never Production
promotion through fleet validation. The original increment published only
2.0.0 and 3.0.0; the repeat-cycle amendment above adds explicitly prepared
profile-replay releases. No caller-supplied UUID, URL, credential or filesystem path is
accepted. The shared writer and existing journal own publication intents.
`component logs <role>` and `component diagnose <role>` provide bounded redacted
runtime events and an installed-KUKSA-schema comparison. For Test-only delivery
diagnosis, `component cm-status test` also reads the current CM process's existing
journal (at most 30,000 records) and its persisted desired target through a
read-only SQLite connection. It returns message types/timestamps, public
deployment identities and the stored update phase, never certificates, tokens
or unrestricted protocol bodies. Truncated native log entries are explicitly
incomplete evidence, not malformed Cloud messages. It neither enables wire
logging nor restarts a manager. Upload checks required
leaf presence before mutation. This does not authorize changing the Factory
schema: .28 lacks the eight v3 ChaosWheel leaves. The operator subsequently
authorized a temporary Test-only Platform configuration continuation on
2026-09-06: `component schema-apply test` and `component schema-remove test`.
These shared-core operations use the existing writer/journal, accept no custom
paths or permissions, retain all existing leaves, and bind a public supplemented
schema only inside KUKSA's service namespace. The original .28, credentials,
ExecStart, Production and existing 3.0.0 bundle remain unchanged. One restart
loads the temporary schema; confirmed repeated application does not restart.
The exact `/run` files and reboot/removal behavior are described in the package
README. This does not authorize another Factory build or new VDP publication.

Operator amendment, confirmed 2026-09-06: retain the existing local server-TLS
profile and defer mTLS. This run qualifies only installation, actual startup
and additive 7/15/23 telemetry paths. Full v3 advisory and its differentiated
write-authority qualification are deferred. Do not enable any Gateway Set or
claim complete v3 specification conformance. The existing v1 binding label is
legacy local source identity, not a Gateway read ACL: Development already
permits telemetry reads. Release-specific subscriptions and KUKSA publication
must still match the exact release manifest; no permission expansion occurs.

This authorization does not waive D4-008: only the authorized VDP can send the
two typed advisory writes, Engineering Dashboard remains read-only, and no
vehicle-motion write is permitted. The existing local amendment deferred
client authentication for telemetry; it does not define how VDP and Dashboard
are distinguished for writes. That remains a deferred design gate for full v3,
not permission to authorize Set for every Development client. See the
[implementation and evidence checkpoint](../qualification/democtl-vdp-family.md).

### Environment Commands

Interface agreement: 2026-09-05. These are the agreed command names and
parameters, not a claim that every operation is implemented.

~~~text
democtl image list
democtl environment create --image 6.1.1-maninblack.27/main-qemuarm64 --target all
democtl environment create --image-path /path/to/factory.img --target all
democtl vm start test
democtl vm start all --timeout 90
democtl vm stop test
democtl vm stop all
democtl unit provision <test|production|all>
democtl unit deprovision <test|production|all>
democtl unit delete <test|production|all>
democtl simulation start
democtl simulation stop
democtl environment prepare --target all --current test
democtl vehicle select production
democtl vehicle select test
democtl environment park
democtl environment resume
democtl environment retire
democtl status
democtl status --cloud
democtl status --guest --cloud
democtl --output json status --guest --cloud
~~~

- The target selector accepts test, production or all; it never means that
  both VMs connect to CARLA.
- Image selectors come from image list. Its source is the existing
  DEMO_ARTIFACT_ROOT artifact store and published manifests, not a new manually
  maintained registry. The readable selector is version/architecture.
- --image and --image-path are mutually exclusive. A raw path does not waive
  factory provenance, immutable-image or metadata requirements. Missing or
  ambiguous metadata is visible; there is no automatic latest-image fallback.
- create only creates local VMs. It does not boot them, provision, launch CARLA
  or connect a live source. prepare performs those distinct subsequent steps.
- --current accepts test or production, never all.
- `--target` selects the VMs to prepare; it never selects multiple live
  consumers. `prepare --target all` requires an explicit `--current test` or
  `--current production`; omission is an input error before any action.
  The current role must belong to the prepared target set. Neither the CLI nor
  the shared application API silently chooses a current vehicle.
- `vehicle select test|production` changes only the one live CARLA/Gateway
  assignment. It does not create, provision or restart either VM. Both Units
  may remain Cloud Online. Switching follows Safe Stop, confirmed detach,
  canonical scene reset and then attachment of the exact selected Unit.
  Failed or uncertain detach/reset prevents attachment of the other Unit.
- Selecting the already attached role is an observed no-op: confirm the exact
  existing assignment without restarting the VM/Gateway or resetting CARLA.
  Missing or contradictory live assignment is not treated as an idempotent
  success merely because the journal names that role.
- park preserves VM/Cloud identity and disk state. resume restores that same
  environment without reprovisioning or automatically enabling driving.
- retire is the explicitly destructive Cloud-and-local retirement operation;
  the original factory image and persistent Unit Sets remain.
- Low-level vm start/stop use the same application core intended for prepare
  and park/resume; Unit operations also use that core.

Implementation order is image discovery/resolution, local VM creation,
VM start/stop, prepare, safe source selection, park/resume and full retirement. Each command
must report its actual implementation state. A parsed command is not a
successful operation, and a failed/unsupported command must not perform a
partial hidden workflow.

### Simulation Lifecycle and Fast Observations — Authorized Increment

Operator agreement: 2026-09-05. `simulation start/stop` own the CARLA,
Controller, Gateway and associated local UI process group. They never start or
stop VMs, provision/deprovision Units or change Cloud memberships. An existing
manufactured environment supplies the one journal and owned runtime paths.

- start blocks all existing VM source gates before opening the Gateway. It
  returns ready without selecting a VM. A healthy repeated start is a no-op,
  preserving current assignment and reset generation. Partial startup is not
  reported ready; explicit stop reconciles and shuts down exact owned processes.
- stop enters Safe Stop, confirms physical stop and both gates blocked, then
  gracefully stops the owned runner and simulator. Preserve VMs, disks, Cloud
  identities and compact run evidence. No reset, backup or forced process kill.
  A stopped repeat is a no-op after local ownership reconciliation. If the
  Controller has already exited, report physical-stop evidence unavailable;
  confirmed guest detachment and owned-process shutdown still permit cleanup.
- `vehicle select` returns `SIMULATION_NOT_RUNNING` when the simulator is
  absent, or `SIMULATION_NOT_READY` when its Controller/Gateway is not ready.
  These checks precede guest/Cloud work. It never implicitly starts or waits for
  simulator startup. Provisioned local role bindings are required; selection
  does not scan Cloud. Use lifecycle/prepare and explicit `status --cloud` for
  authoritative Cloud observations.
- `environment prepare` composes the same VM/Unit, simulation and selection
  primitives; attach only after both preparation branches are ready. They are
  independent; the initial implementation keeps mutation under one writer.
- Selection reuses pinned SSH within one operation and the already verified
  gate action results. It retains Safe Stop, confirmed detach, real reset,
  exclusive attach and server-verified advancing VISS frames. No background
  connection service or second state store is introduced.
- Ordinary status reads local runtime/Controller facts and the selected role.
  Last connection confirmation is a timestamped operation result in the same
  journal, never relabeled as a fresh connection probe. `--guest` freshly reads
  guest gates/VDP and probes only the selected path; blocked peers do not incur
  a deliberate network timeout. Source probes share a bounded read deadline.
  `--cloud` adds fresh Cloud observations. Status never persists observations.

Implementation and tests must use `democtl simulation start/stop` for all
simulator launches/shutdowns once those commands exist. Park/resume and full
retirement remain separate operations; simulation stop does not implement them.

### Built-in display composition — 2026-09-07 increment

#### Cloud-only Platform status and Engineering display — 2026-09-07

Operator clarification: the Platform perspective obtains operational status
only through Aos Cloud, never by reading a VM directly. Entering or re-entering
Platform Team performs a read-only `democtl component cloud-status` operation
(without a version). This focused form reads the bound Test Unit and the VDP
version catalog using the existing authenticated Cloud adapter. The local
journal selects the exact owned Unit only; it supplies no displayed Unit or
component state. Version-qualified `cloud-status VERSION` keeps its existing
release-specific behavior. No VM probe, artifact unpack/hash, Unit inventory,
Unit Set scan or Production read is added to this overview.

The fixed same-origin `/api/presenter/platform` projection exposes Online,
Cloud lifecycle, installed/pending release, reported update state, latest
published version and read time. It exposes no Unit UUID, private path or
credential. Installed does not imply Running, data READY, functional v1/v2/v3
profile or Safe Stop: those facts are not supplied by this Cloud read. The
three functional-profile cards remain workflow references, not inferred
acceptance. Failed reads are unavailable; old values are labelled stale while
refreshing and after 60 seconds. This presentation age is not a platform
timeout. A manual refresh is available, with no Cloud background polling.
Overlapping reads are coalesced; the native header does not independently
request the Platform observation. The former direct guest-state/log buttons
are removed. Legacy `observe-test` UI requests now read Cloud; `test-logs` is
rejected at the UI operation boundary. Engineer CLI guest observation remains
available outside the panel.

Engineering Telematics remains the existing read-only VISS Terminal client.
Its compact display adds Gateway drive mode, physical stopped-state
observation, a shortened live-exercise fingerprint/reset generation, and the
selected vehicle label from the existing run journal, joined to the same VISS
run ID. This label is local assignment context, not Cloud or VDP evidence.
An independent render timer labels values stale after five seconds without
received/advancing frames; it does not freeze a LIVE label on an idle stream.
This is display freshness, not the OEM runtime's FOTA authorization evaluator.
Separate Brake and Tire Driver Advisory rows explicitly remain UNAVAILABLE
until the real typed advisory chain is connected. No warning is fabricated
from installed v3, and no telemetry/advisory write is introduced.

The advisory implementation remains subsequent work. The external-connectivity
development increment below implements the Controller fault action separately
from the telemetry view. No Factory image, Unit identity or VDP release is
changed by these display additions.

<a id="vehicle-external-connectivity-development-increment--2026-09-07"></a>

### Vehicle external-connectivity development increment — 2026-09-07

Implements the Controller action in UI-INT-056 for the current demo vehicle:
`democtl vehicle connectivity status|off|on [--target test|production]`.
Omitting target uses Current Vehicle. OFF requires that selected, running VM
and a running simulation. ON accepts an explicit target after simulation stop.
A recorded OFF/uncertain state blocks handover until explicitly restored.

The existing pinned guest transport observes the actual default interface,
its journal-bound MAC and the maintenance path. One atomic, UUID-owned
`inet democtl_external` nftables table blocks input/output/forward traffic over
that interface (IPv4 and IPv6), retaining only local host VISS ports 6443/16443
and maintenance SSH. Existing source selection and platform tables remain
unchanged; there is no generic established-connection exception. Restore
deletes only the exact owned table. Existing services and identities are not
restarted or recreated, and the Mac/other VM are not faulted. This is a
transient demo policy, cleared by VM reboot, not Factory image configuration.

Intent/result use `vehicles[role].runtime.externalConnectivity` in the existing
journal. Uncertain outcomes require actual filter reconciliation before the
next explicit mutation. Status is one bounded guest read, without the global
writer lock, Cloud calls, full inventory or image hashing. ON/OFF describes
the filter, not Cloud Online/Offline or backend synchronization.

Driving Control invokes the same CLI asynchronously and reads its setting at
five-second intervals. Only one command is in flight; UNKNOWN is visible on
read failure. The telemetry child, keyboard bridge and UI remain independent.
The control app waits for its in-flight command when closing; closing does not
silently restore connectivity. Explicit CLI ON remains available if the app
has closed. Platform Team continues to obtain its observations only from Cloud.

This slice delivers the Controller button and CLI. Shared-header fault
projection and complete Brake/Tire offline buffering/backend replay remain
separate work; Test VDP continuity is not claimed as qualification of that
unimplemented advisory chain or of Production FOTA.

`democtl workspace status` observes and `democtl workspace restore` places the
current environment's owned windows. They do not invoke simulation, VM, Cloud,
source selection, release delivery or driving-mode operations. Neither accepts
arbitrary PIDs, window names, paths or executable commands from CLI/HTTP.
`democtl workspace close` gracefully terminates only the exact owned native
Presenter process (header, right panel and background), keeping its layout
profile for restore. It does not stop the local web server or any simulation,
VM or Cloud lifecycle. A repeated close with no owned host is a no-op.

The built-in-display profile uses a full-width header and approximately 45/55
left/right body columns, with CARLA in the upper 55% of the left column.
The compact Controller and native Terminal dashboard sit beneath it; CARLA
and dashboard share their right edge, with an 8px gap to the expanded panel.
On the 2056px built-in display the Controller is 402px wide, dashboard stays
504px wide, CARLA is 914px wide and the right panel is 1118px wide.
The right column remains the existing
Presenter Platform/Lifecycle interface. A small native WebKit host contains
the same local React UI in two windows; its only cross-window message is a
closed navigation enum. Runtime data/control stays with the existing adapters.

Operator-approved background: one opaque black, borderless, nonactivating
panel in the same Presenter process covers the built-in display's visible
work area, including gaps and margins. It is ordered behind the owned demo
windows, not kept always on top. No wallpaper, Dock/menu bar, external-display
or unrelated-window settings change. Restore reuses it; closing Presenter
removes it with the header/right panel. Rebuilding the small native host
reloads only Presenter windows; simulation, VM and Cloud lifecycles are not
invoked. Window ordering uses window numbers/owner PIDs, not screen capture.
Background implementation checkpoint: local uncommitted `main` tree, confined
to workspace/native Presenter code, workspace tests and documentation. Eleven
workspace tests and targeted Swift compilation passed. First and repeated
`workspace restore` completed without problems; the repeat kept Presenter PID
91670 and the background rectangle `[0, 39, 2056, 1224]`. Existing panel
rectangles were preserved. No VM/Cloud/build-image/security-policy gates or
cleanup were needed; caches and runtime evidence remain unchanged. The native
host binary remains in `.local/demo-control/workspace/Demo Presenter`.

`simulation start` launches the existing runner in one owned Terminal so the
existing Engineering Telematics client has a real PTY. Terminal acknowledgment
may precede exec; observe initial process appearance for at most five seconds,
without a second launch. Once observed, process exit fails immediately. A live
STARTING session can finish readiness observation without restarting it. After
the profile is enabled, a new simulation start restores the layout; a healthy
repeated start preserves assignment. Stop closes only an idle, single-tab
Terminal whose window ID and run-specific title still match ownership.

Layout status reports actual versus requested window rectangles. macOS access
denial, absent/ambiguous owners and geometry differences remain incomplete.
Accessibility permission must apply to the actual invoking app. Geometry alone
does not qualify readability; operator visual acceptance is still pending.
Closing the native Presenter leaves simulation, VMs and Cloud unchanged.

First built-in-display trial (superseded by the operator-approved compact
profile above): 2056 × 1224 usable logical pixels. Header,
Platform panel, Controller and Terminal matched their requested rectangles.
CARLA rendered its live scene at 914 × 614 inside the requested 1016 × 614
zone; this width difference deliberately remains `PARTIAL`, not a qualified
exact layout. Visual readability/acceptance is pending. The simulator was
restarted through `democtl` to expose its existing dashboard in Terminal;
Current Vehicle is now unselected. No VM or Cloud identity was recreated.

Compact-profile application on the same live session: `workspace restore`
completed with no problems. Header, Controller, dashboard and right panel
matched exactly; CARLA differed by one logical pixel in width/height (native
rounding, within the 3px geometry tolerance). All Controller labels and buttons
fit in the 402 × 502 window on visual inspection. Ten workspace tests passed.
No simulator/VM restart, Cloud action, build or cleanup was performed for this
layout-only change. The operator subsequently confirmed the composition looks
good and authorized the black background; background visual acceptance is pending.

The operator then accepted the background and requested a restart trial.
On 2026-09-07, the CLI sequence `simulation stop`, `vm stop all`,
`workspace close`, `vm start all`, `simulation start`, `vehicle select test`
completed. Shutdown confirmed physical Safe Stop; the two guest starts took
25.09s and 29.42s with SSH, DNS and role initialization successful. Both
original Cloud Units returned Online/provisioned without identity changes.
The new simulation start automatically recreated Presenter (PID 93614), the
Terminal dashboard and the black background. `workspace status` reported no
geometry problems. Final guest observation reported Test CONNECTED/OPEN,
Production BLOCKED, active VDP 13.0.1 with live READY data and zero service
restarts. The old `last-failure.json` predates the successful installed state;
it was retained, not deleted or treated as a new failure.

Scope/exclusions: the local web/API server on port 18080 remained running as
the control endpoint; its restart was not qualified by this trial. No
deprovision/delete, new artifact, upload, Cloud mutation or cleanup occurred.
The native Presenter close increment is local/uncommitted on `main`; twelve
workspace tests and `git diff --check` passed. Full visual restoration after
restart awaits the operator's observation, not a fabricated UI acceptance.

Current Vehicle UI correction — 2026-09-07: the lightweight Presenter endpoint
can report `selectedVehicle=test`, `currentVehicle=null` and
`state=SELECTED_NOT_PROBED`. Null here means no fresh connection probe, not no
assignment. The local UI now projects the accepted selection for stable
`SELECTED_NOT_PROBED`/`CONNECTED` states and displays connection evidence
separately. Unknown, invalid or conflicting state shows unavailable; a known
empty assignment shows Not assigned. The header uses “Connection not rechecked”
for the lightweight read and “Connection confirmed” only for CONNECTED.
No new guest/Cloud requests or polling frequency changes were introduced.
The existing layout/dependencies were retained. The local uncommitted UI
change passed 12 targeted tests, all 84 UI unit tests and the TypeScript/Vite
build. Only Presenter windows were reloaded through workspace close/restore;
the local route returned HTTP 200. Simulation, VMs and Cloud were not mutated.

Header simplification — operator accepted 2026-09-08: the earlier
`Connection not rechecked` / `Connection confirmed` captions, demo-title hint
and team-tab status subtitles are removed. The header keeps the demo title,
current logical vehicle and team names, vertically centered within unchanged
workspace geometry. Assignment remains derived from Demo Control's accepted
selection, refreshed from existing local snapshots and restored on UI reload;
detach/stop clears it. This is assignment context, not continuous link-health
evidence. No new guest or Cloud probes, state store or polling are introduced.
Detailed team status remains inside the corresponding perspective.

### Prepare and Select Implementation Increment

Operator agreement: 2026-09-05. Implement `environment prepare` and
`vehicle select` through the same CLI/UI application core and existing
CARLA/Gateway control interfaces. Do not introduce a second source selector.
Preserve already provisioned VM identities; provisioning is needed only for
fresh VMs. Status must distinguish infrastructure readiness, selected role,
authenticated connection and fresh VDP data. A factory baseline without VDP
can be ready for installation, but is not a proven live VDP data path.

Acceptance runs from `apps/demo-orchestrator` through `democtl`: explicit
current selection with both targets, Test-to-Production and reverse handover,
same-role no-op, rejection of missing/invalid current selection before side
effects, and no new attachment after an unconfirmed detach/reset. Real live
acceptance requires the supported source-control boundary and the explicitly
selected trust profile below; fixture success alone must not be reported as
live qualification.
Park/resume and complete scenario retirement remain separate increments.

Implementation checkpoint, 2026-09-05: prepare/select dispatch through the
shared application core. Selector validation precedes side effects. The
operator authorized extending the existing Controller with authenticated
`orchestrate` Safe Stop, status, standalone reset and release operations.
The native keyboard session remains owned by its UI; driving commands are
interlocked while orchestration holds Safe Stop. Only the existing tick owner
resets the ego actor. Completion requires a fresh, stopped physical frame and,
for reset, exactly one completed reset generation. Scenario is not started.

The local transport gate is a narrow, owned `inet democtl_source` nftables
table in each VM. Gateway listens on host loopback 16443; host 6443 must have
no listener. An OPEN gate redirects only the existing .28 client destination
`10.0.0.1:6443` to `10.0.0.1:16443`. A BLOCKED gate drops both incoming and
outgoing VISS traffic, including existing flows. Other firewall tables, SSH,
DNS and Cloud connectivity are unchanged. No SSH forwarding permission or
SELinux exception is added. On guest reboot the transient gate disappears,
so the fixed client endpoint has no listener and fails closed.

Studio's composed source profile uses the dedicated Traffic Manager TCP port
`18000`, not the generic CARLA sample's `8000`. A foreign listener on `18000`
blocks startup before launch; no port owner is stopped and no random-port
fallback is used. `simulation start|stop --target test` exposes the existing
Test-scoped primitive to CLI operators preserving a Production peer. Omitting
the selector retains the earlier engineering behavior; Presenter composition
uses its explicit Test scope.

The initial pre-Provision connection stages only the public Gateway CA under
the existing `/run/democtl-source` location and proves a real TLS/VISS read.
It writes no fabricated Cloud Unit/Node IDs and no files beneath the unmounted
SM store. Once provisioning establishes real Unit/Node IDs, guest Core and the
mounted store, `unit provision test` binds that same source before assigning
the verification set. No scene reset, source detach, SM restart or alternative
identity is part of this handoff. The existing SM VISS provider validates its
credential/binding on each frame read; this is not a new runtime API.

Both gates are confirmed BLOCKED before reset. Only the selected gate opens
after the Controller confirms reset. The selected guest must complete a
server-verified VISS read before release; the vehicle remains in Safe Stop.
Public per-run CA/binding inputs use the existing TEST_ONLY platform profile;
no private client credentials are generated. A baseline without an installed
VDP is reported separately from the guest's VISS connection. A TLS read does
not prove VDP-to-KUKSA readiness.

The current-run writer lock also covers composite operations. Source intent
is recorded before external actions; a repeated request for the same target
reconciles its exact Controller operation ID and actual gates. A confirmed
reset is never repeated. A different target or contradictory evidence blocks
attachment. A failed startup may reuse only the exact owned simulator after
runner exit, socket cleanup, failed manifest and both blocked paths are proven.
Live acceptance is recorded separately from fixture/regression success in
[the CLI source record](../qualification/democtl-source-selection.md).

Default `democtl status` identifies the connected role from Controller
freshness, actual guest gates and a server-verified guest read with advancing
frame IDs. It returns `none` for confirmed blocked paths and `unknown` for
unavailable/contradictory evidence. `--guest` also attempts an independent read
from the blocked peer. VDP's reported readiness is not an independent KUKSA
consumer proof.

This increment supports initial preparation of created targets and source
selection among prepared roles. Adding an unprepared role to an already
attached environment, parking, resuming after a guest/host reboot and full
source teardown remain follow-on lifecycle work, not successful hidden
fallbacks. Reboot fails closed; the current selection command reports the
missing live gate rather than silently rebuilding it.

### Local Demo Amendment: Defer Per-Unit VISS mTLS

Operator decision: 2026-09-05. For this local CLI demo, per-Unit VISS client
certificate issuance/enrollment and Gateway authentication of the selected
Cloud Unit are deferred. They are not prerequisites for implementing or
testing `environment prepare` and `vehicle select` in this bounded profile.
This amendment applies to both logical Test and Production demo VMs on the
presenter Mac, not to a real production deployment.

- CARLA knows only its simulated vehicle, never Cloud Unit/Node identities or
  Test/Production roles. `democtl` owns the role-to-local-VM mapping.
- Use the existing explicit server-authenticated local VISS profile. Retain
  server TLS verification, loopback host exposure, SSH authentication and all
  AosCloud/IAM provisioning authentication. Defer client mTLS only; do not
  disable TLS verification or create shared/placeholder client certificates.
- Enforce zero or one connected demo VM through the owned connection control.
  A selected-role label alone is not connection exclusivity. The unselected
  VM must have no usable live VISS data path, including a connection left from
  an earlier selection. Cloud connectivity remains independent.
- Safe Stop, confirmed detach before switching, scene reset, same-role no-op,
  current-state reconciliation and honest live-data readiness remain required.
- Identify the result as `LOCAL_DEMO_SERVER_TLS`, with per-Unit mTLS explicitly
  `DEFERRED`. Do not report D4-006 strict identity/security qualification.

The strict D4-005/D4-006 profiles remain the future target. This explicit
operator-selected local exception is not an automatic fallback when strict
credentials or authentication fail. Re-enabling strict mode requires its
separate onboarding/client integration and live qualification.

Backing-image decision, confirmed 2026-09-05: make one independent local
Factory Image copy under .local/factory; both role overlays use that copy,
never the artifact-store original directly. Preserve the original bytes,
format and SHA-256: raw uses oem-demo-factory.img, qcow2 uses
oem-demo-factory.qcow2. This is one common backing copy, not two full copies
and not a backup of a provisioned VM. The copy stays read-only during use.
The subsequent user-approved symmetry correction makes local retire remove
that copy and its generated manifest after both overlays; only the original
artifact remains. No image conversion or rebuild occurs. The command also
handles an exactly bound copy left by the former retire, without recreating VMs.

The first local creation increment resolves published images in the catalog
by selector or exact path. A path outside that catalog remains unsupported
until a producer manifest binding is integrated; metadata is never guessed.

### Local VM Start/Stop — Agreed Increment

- Target test, production or all already-created roles; reuse their image,
  overlays, local identities and ports. No implicit create, provision, CARLA,
  Current Vehicle change, backup, rebuild or full-demo readiness claim.
- Bind the initial main-qemuarm64 runtime profile to macOS ARM64/HVF, pinned
  firmware and accepted QEMU versions. Do not hard-code image .27 as the selector.
- start launches/reuses exact owned QEMU processes and one shared DNS bridge.
  Confirm QMP Running, authenticated guest SSH and guest DNS separately. Default
  guest wait ceiling is 90 seconds per VM; timeout leaves visible PARTIAL state.
  Both selected VM processes launch before readiness waits. Readiness ends the
  operation immediately; the ceiling is not an imposed boot delay.
- First SSH setup uses an explicitly entered guest password in the interactive
  CLI, the owned serial console and a new per-VM key. Pin the guest public host
  key through that console. Do not extract passwords from legacy tools or accept
  them in API/argv/journal. Noninteractive first start reports missing enrollment.
- stop asks the guest to power off over SSH, falling back to QMP powerdown.
  Wait for process exit and disk release, with no automatic forced kill. Keep
  overlay/identity/access material. Stop shared DNS only after the last owned VM.
  Block a direct stop of Current Vehicle; detach/park is a separate operation.
- Read actual process ownership before explicit retry, keep per-role outcomes,
  and retain unresolved operation scope. Do not erase another role's uncertainty.
- Extend local retire only for stopped, proven unprovisioned guests: before
  poweroff observe absent provision-state/PIN files, active provisioning IAM and
  inactive normal-mode IAM/SM/CM; after process exit bind this to overlay SHA-256.
  retire requires the same digest and deletes only tracked access files along
  with its existing local targets. Unknown/provisioned state blocks this path.

The [package README](../../apps/demo-orchestrator/README.md#start-and-stop-created-vms)
defines commands and readiness limits. This increment does not implement full
Cloud/scenario retirement, source selection or live qualification.

### Unit Lifecycle — Authorized Increment

- Operate only the current journal's Test/Production identities, with one
  run-exclusive writer. all serializes the created roles Test then Production.
- provision requires a running, SSH/DNS-ready guest. Read its real system/model/
  Main Node identity; invoke the official v6 SDK once; prove normal guest mode,
  Cloud Online, then scoped role membership. Pin the authenticated OEM owner,
  fleet and set UUIDs; Test is a verification set, Production is not. Reject
  missing, ambiguous, crossed-role or foreign-member bindings without removal.
- Reuse the qualified SDK 5.4.2 transition correction only as a library. No old
  VM/checkpoint workflow, backup, image patch or inherited baseline identity.
- deprovision stops only CM, waits for Cloud Offline, deprovisions once and
  confirms new/Offline, then stops the exact VM. By the operator's 2026-09-05
  amendment, no old-identity reconnect/probe is performed: Cloud owns identity
  revocation. Do not restart CM after deprovision or claim certificate-revocation
  testing. Preserve peer VM/DNS until the last VM stops.
- delete removes only the recorded systemUID from its role set, deletes the
  deprovisioned Unit once and proves Unit/Node absence using authenticated
  inventory visibility. Keep persistent role sets and campaign definitions.
- Every mutation records intent first; lost responses remain uncertain until
  authoritative reconciliation. Repeat commands do not repeat proven SDK or
  destructive requests. Retired overlays cannot start/provision as new Units.
- This slice retains overlays, access material, factory copy and the current
  journal. It implements neither backend/CARLA cleanup nor full R0/recreation.
  The retained baseline Unit is not a mutation target; its one Test membership
  was removed only under separate exact user authorization for this acceptance.

The subsequent user-authorized environment retire extension removes those
retained CLI-only files after fresh authoritative Cloud absence and empty-set
proof. Every provisioned role must already be DELETED; no old-identity rejection
flag is required. The same writer lock and per-file interrupted-unlink reconciliation
apply; Cloud reads repeat on resume, and no Cloud mutation is performed. Exact
overlays/access, working factory copy/generated manifest and journal are removed
without backup; the artifact-store original is preserved. This enables fresh
CLI-only cycles without implementing backend/CARLA/scenario retirement.

See the [executable commands](../../apps/demo-orchestrator/README.md#provision-and-retire-cloud-units).
Live coverage is explicitly bounded in the acceptance record; implementation
does not itself qualify every fresh-order or interruption combination.

## Agreed Direction and Current Implementation

| Area | Agreed direction | What exists on 2026-09-05 |
| --- | --- | --- |
| Location | `apps/demo-orchestrator/`, alongside `apps/presenter-ui/` in the Solution repository | Python package and editable-install instructions |
| Shared implementation | CLI and UI use one operation core | CLI plus a transport-neutral Python API adapter; no HTTP server or UI connection |
| Target names | `test` maps to `VALIDATION`; `production` to `PRODUCTION`; `all` selects both | Target parsing and mapping |
| Status | Report observed facts, including OEM and Service Provider access | Local/QMP observations plus optional guest SSH/DNS and authenticated Cloud reads |
| Lifecycle | Explicit VM and Unit operations | Local create, VM start/stop, Unit provision/deprovision/delete and unused/Cloud-retired CLI cleanup implemented; prepare/select/park/resume and full scenario R0 remain unavailable |
| Image selection | Explicit image reference; generated descriptor, not operator-written YAML | Published catalog discovery, exact selector/path resolution, format-preserving local copy and generated manifest |

The [package README](../../apps/demo-orchestrator/README.md) is the source for
commands that actually exist, installation and package tests. Status returns
`OBSERVED` or `PARTIAL`; neither means “the demo is ready.”

## Ownership and Integration

The CLI parses operator intent. The application core performs or observes an
operation; host, guest and Cloud adapters encapsulate their respective
interfaces. Human-readable output and JSON represent the same result.
The future local API calls this core, not shell commands assembled by the UI.

AosCloud remains authoritative for Units, memberships, reported/desired state
and delivery. QEMU and the guest report their own runtime facts. The local
journal correlates operations; it must not become a second Cloud database.

Existing scripts are evidence of working commands, not an automatic dependency
of the new core. Reuse an understood, bounded primitive when appropriate; do not
invoke an entire legacy workflow to obtain one fact. There are no implicit
backups, provisioning, restarts or repair steps inside `status`.

The integration must respect the
[local hosting and native-helper boundary](../../contracts/local-demo-hosting/README.md).
A local CLI profile selector is not permission for a browser caller to choose
arbitrary credentials, Cloud endpoints, executables or filesystem paths.
Browser operations must use the server-bound, authorized session context.

## Status: Implemented Slice and Remaining Design

### Reading Modes

The following interface is implemented:

```text
democtl status [test|production|all]
democtl status [test|production|all] --guest
democtl status [test|production|all] --cloud
democtl status [test|production|all] --guest --cloud
democtl --output json status [test|production|all] --guest --cloud
```

- Default: quick local observations, plus clearly dated last-known observations
  only if an approved source of those observations exists.
- `--guest`: add bounded, read-only guest checks.
- `--cloud`: add fresh Cloud access and relevant Unit reads.
- Both flags: combine independent observations; failure of one source must not
  erase results obtained from another.

The default target is `all`; the per-probe budget is 8 seconds. `--details`
and local CLI `--profile` options are implemented. No status observations are
cached. The selected-source operation's dated confirmation is shown separately
from fresh reads, as agreed in the simulation/fast-observation increment.

### What the Snapshot Contains

| Layer | Facts to expose | Important distinction |
| --- | --- | --- |
| Run and target | Selected role, image reference/version/digest reference, owned overlay reference, pinned Unit/Node identity and last operation outcome | Local intent is not confirmation of Cloud membership |
| Local VM | Overlay presence, owned QEMU process and QMP response | Process running does not mean guest ready or Cloud Online |
| Guest access | SSH connection/authentication result; configured host DNS bridge and guest resolution of the configured Cloud hosts | DNS failure, timeout, authentication failure and changed host key are different failures |
| Guest Aos platform | Observed release, provisioning/normal mode and expected services' state, result and restart count | Expectations depend on the selected image and mode |
| Host Cloud access | Endpoint response, credential availability, authenticated identity/role and owner/provider binding | Reachable API does not mean authenticated or authorized |
| Cloud Unit | Observed Unit/Node identity, Online state, Unit Set membership and role mismatch | Missing local UUID or denied read does not prove the Unit is absent |
| Operation history | Last requested action, observed result, timing and unresolved outcome | Request accepted does not mean operation completed |

Configured guest profiles should define the expected service set. For example,
the repository's current image tooling distinguishes provisioning
`aos-iam-prov` from normal-mode `aos-iam`, `aos-sm` and `aos-cm`.
That is an image-specific input, not a universal list frozen into `democtl`.
A stopped VM skips guest probes and reports why.

Cloud reachability here is an observation from this host. It is not a claim
that every AosCloud subsystem is healthy; guest connectivity and Unit Online
must be reported separately.

### OEM and Service Provider Access

Report each configured credential context separately: OEM delivery, any
separate Platform publication context, and each configured Service Provider.
Do not merge their permissions into one “Cloud access OK” flag.

For each context, show:

- whether a credential reference is configured and can be used non-interactively;
- public certificate expiry metadata when available without unlocking or
  exposing protected material;
- the role and owner/provider identity actually returned by an authenticated
  read, rather than inferred from a local profile name;
- effective permissions where the API exposes them, and “unknown” otherwise;
- which planned operation is affected by a missing or insufficient context.

Use the [Cloud role and action matrix](../requirements/d4-decision-register.md#d4-011)
and [artifact publication profile](../../contracts/artifact-publication-profile/artifact-publication-profile.v1.json)
as the authority for separation of roles. A successful read is not proof of
permission to provision, approve or delete.

No interactive unlock, credential enrollment, role change or TLS bypass is
part of status. Missing Service Provider access must not falsely make local
VM startup unavailable; likewise OEM access does not imply Service Provider
access. The implemented `users/me` and exact Unit-detail reads use the public
OpenAPI fields. The observed API role strings are `oem` and `service provider`;
profile names are not substituted for those source values.

### Observation and Execution Rules

Every external observation needs its source, local observation time, source
time if supplied, freshness/coverage and sanitized error. Preserve distinct
“not requested,” “not observed,” “stale,” “unavailable” and “confirmed absent”
meanings. Do not turn unknown results into a reassuring green summary.

The existing [Presenter read-source model](../../apps/presenter-ui/src/domain/sourceObservation.ts)
and [read-only adapter contracts](../../apps/presenter-ui/src/adapters/read-only/contracts.ts)
already describe source and freshness semantics. Their
[implementation work packet](../planning/active/work-packets/p1-ui-aoscloud-readonly-adapters.md)
records fixture-only integration, with live transport deferred. Align the
future serialized status contract with these semantics instead of creating a
competing UI read model; additional provider contexts still need explicit
mapping.

Status should batch compatible guest observations into one SSH session and
reuse authentication within one call per selected Cloud context. Query pinned
objects, not the entire account. Bound timeouts and return partial results
with the unavailable source identified.

Status does not write lifecycle state, fix DNS, start a service, request a
Cloud log archive or retry a mutation. If reconciliation is needed, show the
uncertain result and the explicit next operation. Detailed diagnostic log
collection remains separate.

## Configuration and State

Keep three concerns distinct:

| Concern | Proposed owner | Boundary |
| --- | --- | --- |
| Factory image descriptor | Build publication or explicit CLI registration | Version, artifact identity/digest and compatible runtime/network profile; no keys or fixed `.27` dependency |
| Local operator configuration | Local installation/profile configuration | Artifact root and credential references; machine-specific values and secrets stay outside Git |
| Current run | Existing [Demo Run State contract](../../contracts/demo-run-state/README.md) | One current run and its atomic journal, not a new history database |

The accepted journal path is `.run/demo-current/journal.json`; the accepted
factory/overlay layout is owned by that contract. The earlier discussion of
per-run `plan.json`/`state.json` directories is not an accepted replacement.
The read-only slice uses `.local/demo-control/status.json` for operator
observation bindings, not history or desired state. Its fields are documented
in the package README. Local creation reads the human-readable artifact store
and generates the copy descriptor; the journal takes precedence for managed
VM bindings, without importing the old experimental Unit/access references.

The accepted complete demonstration prepares two roles from the same factory
image. Single-role engineering use must be scoped explicitly; it does not
silently change the full-run topology or claim dual-role qualification.

## Documentation Audit and Placement

Audit scope: the Solution checkout at `main` commit `fe35641`, the local
orchestrator boilerplate and the retained `codex/ltvp-finalize-27` reference
at `6a943c4`. This was a document/source audit, not a fresh VM or Cloud check.

| Question | Owning documentation | How this document connects |
| --- | --- | --- |
| What the demo demonstrates | [Scenario](../demo/staged-post-sop-brake-health-demo-scenarios.md) | Reference the scenario; do not redefine its story |
| What coordinates what | [HLA](high-level-architecture.md), [flows](demo-scenario-architecture-flows.md), [component register](../requirements/component-decomposition-and-interface-register.md) | Implementation companion for the existing orchestrator |
| What is required | [Component requirements](../requirements/components/demo-orchestration.md), [D4 decisions](../requirements/d4-decision-register.md), [contracts](../../contracts/) | Link obligations and schemas; review conflicts at their source |
| What to implement next | [Planning](../planning/README.md) | Create a bounded implementation packet only after design agreement |
| How to operate implemented commands | [Package README](../../apps/demo-orchestrator/README.md), [operations](../operations/README.md) | Installation stays with the package; add a real runbook when operations work |
| What has been demonstrated | [Current baseline](../qualification/current-baseline.md), [qualification index](../qualification/README.md) | Link exact revisions and evidence; never infer qualification from a design |

The stable location is `docs/architecture/demo-control.md`. Version and status
belong in metadata, not filename suffixes. Navigation links from the document
map, architecture, development, operations and package README make it
discoverable without duplicating its content.

The audit found that the documentation gate omitted application READMEs.
The status implementation adds `apps/*/README.md` to its scan; package
backlinks now participate in the gate without scanning dependency/build trees.

### Discrepancies to Resolve Before Lifecycle Implementation

| Finding | Evidence and consequence | Owning follow-up |
| --- | --- | --- |
| Baseline pointers disagree | The root README still discusses `.11`; current-baseline/planning name `.21`; `.27` as-built/closeout records remain on the retained branch | Reconcile the accepted evidence and source integration, then update current pointers; preserve historical reports |
| Successful narrow experiment is not full qualification | The retained `.27` records describe a test-only VDP update path, not the complete production/campaign narrative | Publish explicit supported scope and limitations in qualification |
| DNS behavior has not been consolidated in main | The retained branch contains onboarding/network changes; the main onboarding check still assumes port `18053` | Integrate the intended source/profile behavior before using it as the new adapter's baseline; do not reuse the old checker wholesale |
| Cloud topology differs from the recent operating decision | Requirements/current baseline retain a dedicated demo Fleet; the agreed simplified experiment uses Default Fleet | Reconcile the owning topology decision and requirement, then bind verified IDs; do not guess live membership |
| Local creation layout reconciliation | User confirmed one local copy, format preservation and explicit engineering targets | Contract 1.2.0 records raw/qcow2 copy paths and single-role engineering scope; one current journal and full-demo two-role requirement remain |

None of those discrepancies is silently resolved by this draft. In particular,
it does not merge the retained branch, promote `.27` to full qualification,
change Cloud topology. The narrow user-approved local creation amendment is
recorded in run-state contract 1.2.0; other discrepancies remain open.

## Traceability and Next Review

The implementation proposal must preserve:

- [Cloud-authoritative read facts](../requirements/components/demo-orchestration.md#req-demo-005)
  and [visible decision basis](../requirements/components/demo-orchestration.md#req-demo-006);
- [exactly-once provisioning reconciliation](../requirements/components/demo-orchestration.md#req-demo-003)
  and [authoritative Unit/Unit Set binding](../requirements/components/demo-orchestration.md#req-demo-004);
- [ordered retirement](../requirements/components/demo-orchestration.md#req-demo-013)
  and [restart-safe recovery](../requirements/components/demo-orchestration.md#req-demo-015);
- [local least privilege](../requirements/components/demo-orchestration.md#req-demo-016)
  and [honest coverage](../requirements/components/demo-orchestration.md#req-demo-017).

Completed agreements: document ownership, status, the five lifecycle classes,
their CLI surface and the one-copy local manufacture increment. Next items:

1. Implement the remaining agreed commands with per-step results and explicit
   partial-completion/recovery semantics.
2. Reconcile the baseline, topology and configuration conflicts in their owning
   documents under the [documentation governance](../governance/documentation-and-requirements-management.md).
3. Close the current-run journal/recovery and source-selection integration
   needed by mutations without introducing a parallel lifecycle store.
4. Agree a bounded implementation increment and its tests; publish operator
   instructions and evidence only as that increment works.

Status, image list, local create, VM start/stop and unprovisioned-local retire are available for operator testing. The
remaining commands are agreed design, not working lifecycle automation yet.
No live execution qualification is implied by fixture tests. Open topology,
baseline and live-source integration decisions remain explicit prerequisites
for the corresponding later operations.
