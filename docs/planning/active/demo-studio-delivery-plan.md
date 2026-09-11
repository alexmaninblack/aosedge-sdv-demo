<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Studio: staged delivery plan

- Status: **Implementation authorized; P1–P4 integration and P5–P7 source increments, not full E2E-qualified**
- Prepared: 9 September 2026
- Working language: English
- Review mockup: [Interaction Mockup 2.8 — reviewed B2 visuals and corrected simulation](../../demo/mockups/aosedge-demo-interaction-mockup-2-8.html); [2.6 retained flow baseline](../../demo/mockups/aosedge-demo-interaction-mockup-2-6.html); [2.5 retained](../../demo/mockups/aosedge-demo-interaction-mockup-2-5.html) as the original action-audit basis
- Basis: [action and integration audit][audit], including its 78 action/transition rows and 28 gaps
- Target: the accepted Studio B composition connected to a real, repeatable Test-vehicle demo
- Authorization: on 9 September 2026 the user authorized implementation and independent verification of P1–P8, in the accepted sequence. Production rollout and changes outside these phases remain excluded.

### Native service input migration — 11 September 2026

<a id="native-service-input-migration"></a>

[ADR 0015](../../architecture/decisions/0015-use-native-aos-service-runtime-inputs.md)
is **accepted**, and the user authorized documentation migration followed by
implementation. This is a bounded continuation of P5/P7, not a restart of the
Studio plan. The former manifest-before-assignment and SM token-owner patch
gates are retired. Earlier dated checkpoints below remain historical.

Subject amendment accepted on 11 September: Q09b now uses one retained OEM
Group Subject **per logical service**, Brake and Tire, not one shared Subject
and not one per release. Both may attach only to current Test in this packet;
Production is excluded. Demo Control records each exact Subject identity and
keeps assignment independent of package readiness. An accepted publication
receipt plus matching catalog service/SP identity permits the native assignment
attempt; upload/build readiness and actual runtime remain separate observations.
This supersedes the earlier local READY gate, not Cloud's native validation.
Q13 retention/reset applies independently to each Subject. No shared Subject
was created before the amendment, so this run requires no binding migration.

| Step | Change and owner | Gate / evidence | State |
| --- | --- | --- | --- |
| N1 | Solution: accept ADR, update HLA/flows/requirements, runtime-input contract and D4 migration mapping | English documents, navigation and deterministic docs-check | Complete; product wire migration remains N3 |
| N2 | Brake/Tire + Platform: private bootstrap sessions, dynamic token readers, native tmpfs resource mode; retire only token-owner patch | First create, isolation, atomic renewal, path/mode/symlink negatives, cleanup/restart, native host compilation | Host source tests passed; Linux/live proof remains N6 |
| N3 | Solution contracts, both producers/backends: package version and native identity; explicit new message schemas without required service/model OCI digest | Producer-consumer fixtures; legacy queues/history retained; no fabricated digest; model/VDP hashes unchanged | Consumer and producer/input source increments passed; live integration remains N6 |
| N4 | Demo Control: package the allocated version once; project public inputs; native configuration activation through existing commands | Package/publication equality; no manifest lookup dependency; stable-directory refresh after VDP commit | Both real ARM64 exports, signed-payload equality, warm projection and transient resource activation passed; after user changed OEM to arm64 only, both 2.0.0 uploads created service/version records but failed Cloud bundle building |
| N5 | Existing startup integration: restore public /run inputs before SM launches retained assignments | Exact hook/order documented and tested; no new daemon, persisted token or metadata authority | Cold/warm split accepted; pre-SM preparation and post-SM process verification passed with unchanged SM binary; persistent-image integration and retained-assignment VM reboot not qualified |
| N6 | Bounded current Test SOTA and backend integration through democtl | Real Cloud Running/version, KAC/TLS/subscriptions, renew/expiry, actual product records, retained state and scoped access proof | Separate Brake/Tire Group Subjects created and bound to Test; service association attempted once each but still absent on read. Both packages uploaded/not ready after generic bundle build failure; no Running/functional qualification |
| N7 | Checkpoint source/docs and record exclusions | Commit only tested source; no build artifacts; retain current VM/Factory/Production | N2/N3 local checkpoints created; full-migration checkpoint remains pending |

Source increments may be developed independently, but **no new producer is
published before its matching backend/contract migration**, and no configured
1777 token mount is activated with a legacy fixed-path bootstrap. N2 changes
credential placement only; it must not masquerade as completion of N3–N6.
The live source/publication permissions already granted remain bounded to the
current Test; this change does not authorize another Factory build, reset,
provisioning cycle or Production mutation.

User-confirmed execution boundary, 11 September 2026: use native AosCore
container preparation, launch and retained-instance recovery unchanged. N4/N5
must not introduce an SM patch, launcher or replacement container lifecycle.
Their remaining scope is our package/resource/input configuration and its
startup ordering. The [source-verified boundary](../../architecture/demo-control-service-inputs.md#native-launch-boundary--confirmed-11-september-2026)
records why the documentation's systemd-template example is not applicable
to the pinned direct-libcrun runner. Native startup support does not itself
generate our application metadata or restore its volatile source directories.

The [runtime-input contract](../../architecture/demo-control-service-inputs.md)
defines five public fields and immutable package metadata. Its
[executable schemas](../../../contracts/service-runtime-inputs/README.md) freeze
the input shapes before readers change. Product wire migration must remove
Brake's `modelArtifactSha256` dependency as well as `serviceArtifactSha256`;
both were tied to the unavailable final OCI manifest. Exact artifact identity
remains separate optional engineering evidence, not service readiness.
Existing model configuration hashes, VDP compatibility hashes, authorization,
algorithms, timing limits and persistent producer state do not change.

Earlier N4 package source increment: `service prepare brake --profile v1|v2|v3`
uses the existing product export without building or requiring a vehicle.
One SP catalog/version read feeds the existing continuity ledger; one allocated
version enters both the package release file and schema-2 publication input.
The returned handle identifies an immutable prepared directory. Native-input
overrides, private credentials and runtime files are excluded. The installed
official signer accepts all four fixed service configurations (Brake v1/v2/v3,
Tire v1) without signing credentials. Tire actual preparation still requires
its real product-build adapter; a schema test is not a Tire product build.
No signing, upload, assignment, runtime-resource activation or VM action has
occurred. Loader/library closure and exact outbound behavior remain live gates.
See [CLI/result/recovery contract](../../architecture/demo-control.md#native-service-package-preparation).

The subsequent N4 source increment added handle-based `service sign`, `upload`
and `cloud-status`, with SP binding, exact prepared/signed payload equality,
one Deployment Bundle POST, durable acceptance/uncertainty and read-only repeat.
READY is catalog readiness, not service execution. Existing service assignments
must be absent or scoped solely to the current Test. Public API schema reads,
temporary-key official signing and isolated transport/receipt tests passed;
no live product signing/publication or deployment occurred. N4 public inputs,
activation and N5 boot order were still next. The real Tire build adapter was
still open at that checkpoint; its later result is recorded below. N6
backend/runtime qualification remains open. See the
[publication contract](../../architecture/demo-control.md#native-service-publication).

Earlier N4 increment: Tire `1698ee4859fb66c210f386f485dad56234e37c15`
has a completed real ARM64 product export (bootstrap, service, dependency
closure and product tests), built through `democtl`; the repeated build command
reused the completed receipt with `noOp=true`. On current Test, native IAM TLS
identity reconciliation and public projection succeeded for committed VDP
18.0.0 / compatibility 1.0.1, followed by an unchanged repeat. Both metadata
files are root-owned 0444. No service assignment/publication, SM restart,
resource activation, VM reset or Production mutation occurred in this increment.

N5 is not closed by this warm result: the existing pre-SM bootstrap precedes
the component recovery that starts VDP, while public projection requires the
running committed VDP. The exact conflict and excluded workarounds are in
[cold-start ordering](../../architecture/demo-control-service-inputs.md#cold-start-ordering-conflict--11-september-2026).
The user subsequently accepted cold preparation from verified committed state
without a running process, followed by post-SM process verification. The
existing native IAM file identifier supplies the same Unit identity. A live
`runtime-activate test` proved this sequence with the unchanged SM binary and
both input resources. It is temporary `/run` configuration, not a retained-
assignment full-VM reboot proof; immutable-image integration remains open.

Earlier live publication boundary: Brake and Tire migrated backends are active
with data preserved. Both current-source ARM64 v1 packages were prepared as
`1.0.0`, signed and accepted by Deployment Bundle upload. Cloud rejected both:
`does not support architectures: {'arm'}`. Their verified configurations contain
only `arm64`; the current OEM architecture read returns `arm` and `arm64`.
This is evidence of a tenant/package architecture mismatch, not proof of an
SM fault. No architecture was relabelled, no OEM setting changed and no second
upload attempted. OEM-wide changes require separate authorization. The former
local READY-before-assignment gate is superseded by the amendment above. See the
[latest checkpoint](../../qualification/demo-studio-implementation-progress-2026-09-11.md).

Latest publication check: the user changed the OEM to `arm64` only and explicitly
authorized both 2.0.0 uploads. These reuse unchanged ARM64 binaries and v1
functional content, without a rebuild. Both uploads returned 201 and created
service/version records, but both bundles failed with `Failed to build deployment
bundle.` The missing-`arm` message did not recur. Exact version detail reports
`uploaded` with null build diagnostic/configuration, not READY. No Subject
assignment or VM action occurred during publication. Subsequent authorized
assignment created/bound both separate Group Subjects to Test, but service
association remains absent; see the latest checkpoint. Classify the Cloud build failure from its
internal diagnostic before another publication; no guessed package change.

N2 local source checkpoints: Brake `8d19381`, Tire `47ab08d`, Platform
`205f89d`. The Solution commit containing this record freezes the accepted
documentation/input schemas. Test evidence: Brake 5/5 CTest targets, Tire 2/2,
Platform 8 focused tests, Solution 36 input/KAC/docs tests and docs-check.
No full ARM64/gRPC service build, live activation, upload or backend/VM change
occurred. No source push occurred in this increment.

Unclosed Tire analytics functionality remains a separate P7 task. Resolving
credentials or process startup does not prove that its model/results work.

### N3 execution position — consumer and producer source checkpoints

Producer source checkpoints: Brake `bc0ed65`, Tire `a0c58b8`. Both remain
local commits on the existing working branches. No push or publication occurred.

This splits the existing N3 dependency order into source increments; it adds
no new audience flow, service, daemon or platform responsibility.

| N3 increment | Actual state | Next gate |
| --- | --- | --- |
| Contract and backend consumers | Nine explicit product revision-2 schemas and fixtures; old schemas retained; both backends accept old/new; exact native-instance correlation; Brake forward-only DB migration 003; mixed query envelopes | Source tests passed; not deployed |
| Demo Control admin compatibility | Existing empty-store proof accepts Brake database 2/3 and Tire 2 only; all ownership, counts and selector checks retained | Isolated adapter tests; no cleanup execution |
| Package/public/native readers and producers | Both entry points read package/public/native inputs separately; all nine product kinds use native v2 provenance; explicit old queue/binding decoding retained | Host Brake 6/6 and Tire 3/3; actual C++ output accepted by both matching backends; ARM64/live proof remains N6 |
| Product integration consumers | New query schema snapshots are frozen; team dashboards still use fixtures and the accepted Brake detail endpoint is not implemented on the active backend branch | Bind the real query/readiness/evidence consumers before claiming P7 |

The [product-message migration](../../../contracts/service-runtime-inputs/product-message-migration.md)
specifies the exact new fields, retained legacy behavior, query revisions and
non-publication gate. Backend tests use temporary databases and local HTTP
sockets only. They do not qualify actual ARM64 service startup, live outbox
recovery or production records. N4/N5 projection/boot order and N6 Test
integration remain pending. No Factory, VM, SM, Cloud release or Production
change is part of this checkpoint.

Consumer source checkpoints: Brake Cloud `d7626b7`, Tire Cloud `b383c02`;
44 Brake and 13 Tire backend tests passed. The Solution checkpoint includes
8 contract/input tests, the retirement adapter tests and the updated execution
record. These local commits were not pushed or activated in the demo.

<a id="implementation-execution--9-september-2026"></a>

## Implementation execution — 9 September 2026

Earlier checkpoint (11 September, before ADR 0015): the initial approved Studio composition is
connected to shared Test lifecycle/VDP operations and normalized Cloud-only
inventory/monitoring. Brake has a compiled ARM64 product profile; Tire has
scoped product source and a new backend cleanup protocol. These are source and
integration increments, not completed P4–P8 exit criteria. At that checkpoint, service launch had
two concrete unclosed prerequisites: native per-instance token-directory
ownership and authoritative ARM64 manifest identity before assignment. See the
[11 September checkpoint](../../qualification/demo-studio-implementation-progress-2026-09-11.md)
for actual tests, preserved live state and remaining work. Earlier observations
below are historical; accepted phase order and exit criteria are unchanged.

Latest continuation (10 September, evening): repeated completed Create/Prepare
now read current infrastructure rather than saved readiness; the existing
Platform Cloud view has single-flight visible-only polling and retained stale
values. The same Test passed full Park/Resume, with unchanged Unit/disk/VDP18;
the exact transient SM was separately reapplied after boot. See the
[current checkpoint](../../qualification/demo-studio-implementation-progress-2026-09-10.md#evening-continuation--reentry-cloud-observer-and-parkresume).
This closes those specific gaps, not the complete P1–P8 plan. New Studio binding,
full normalized inventory/metrics presentation, real Brake/Tire E2E, and clean
factory qualification remain. The records below describe earlier increments;
the phase definitions and exit criteria later in this document are unchanged.

Resumed on 10 September with explicit Test-only destructive-cycle authority
while preserving the existing Production peer. Docker build/start is now
proven, source publication to the three existing named remotes is authorized,
and new project repositories must be public. Current evidence and the remaining
service runtime/input gates are in the
[resumed implementation checkpoint](../../qualification/demo-studio-implementation-progress-2026-09-10.md#resumed-execution).
This does not promote the incomplete P1–P8 sequence to accepted E2E.

### Additional authorization — 10 September 2026

The user explicitly approved all three bounded proposals after the resumed
checkpoint: (1) a minimal platform-owned read-only metadata/public KUKSA trust
interface, first proved transiently on the current disposable Test without a
Factory `.31` rebuild; (2) use of the existing configured SP for a distinct Tire
service identity, temporarily simplifying separate team-SP publication authority;
and (3) source push to the public `alexmaninblack/tire-health-cloud` repository.
Separate Brake/Tire identities, instances, permissions, data and backend processes
remain required. This does not grant Production mutation, private-key exposure,
arbitrary service resource access, new credentials, main/force pushes or an image
rebuild. The exact resource producer and provenance mapping must be recorded
before the transient Test action and verified against actual platform sources.
The exact [temporary service-input mapping](../../architecture/demo-control-service-inputs.md)
records the seven fields, OCI manifest digest meaning, startup ordering and
public-certificate boundary. It is not a claim of a completed guest proof.

Implementation starts from `pre-studio-implementation-2.8-2026-09-09`,
commit `b997e6e6cffba02b61a588c40f14dba30942d17d`, on
`codex/demo-studio-implementation`. The historical review gates below describe
the preceding review; the authorization above now opens P1–P8.

- P0: source readiness audit completed. Factory .31 includes native container
  runtime and KAC resources; effective SOTA delivery still needs live proof.
- P1: shared Test lifecycle, release continuity and backend context migration
  in progress; not yet qualified.
- P3–P8: pending. Brake currently has domain libraries and a diagnostic package
  stub, not a deployable product runtime. VDP/Gateway advisory wiring and Tire
  are implementation work, not capabilities inferred from mockup tests.
- P2 Cloud-only reads and publication reconciliation are integrated; the full
  phase remains open. See [Cloud observations](../../architecture/demo-control-cloud-observation.md)
  and [Test publication](../../architecture/demo-control-component-publication.md).
- Final operator visual approval remains an explicit gate after automated tests.
- The [implementation checkpoint](../../qualification/demo-studio-implementation-progress-2026-09-10.md)
  separates completed source/tests, preserved live state, remaining code and
  decisions required before live qualification. It is not a completion report.

### Source increment and remaining live gates — 10 September

The first P1 increment has isolated regression evidence, not phase acceptance:
271 Demo Control tests passed; after the final API/selector changes, the changed
Presenter operations, ledger, CLI and Unit suites passed again. The Brake Cloud
contract suite passed 17 tests. Backend branch `codex/studio-test-backend`,
commit `77c99de0342cfb53077c01ab3d4c6721d2eb2228`, passed 31 backend tests,
12 architecture/UI tests, typecheck and quality gates. Its source supports one
Test context, optional Production, durable storage and separate process/query
readiness. Composed backend lifecycle and the remaining P1/P2 work are not yet
complete, so the new preparation sequence is not declared ready for a live run.

The existing live run was observed through `democtl status test --cloud`: two
owned roles, selected Test, running .31, fresh Controller Safe Stop. It was not
retired or reconfigured during source work. Production is not removed merely to
fit the new Test-only default.

P1 also has an isolated Demo Control context projector: exact successful current
Test identity, optional successful Production peer, no Cloud/runtime state in
the exported context, no silent replacement of a retiring UID, and retained
scope after Cloud deletion until backend cleanup. Five tests passed. Successful
provisioning refreshes this context when the run owns backend processes. Full
Create/Park/Retire composition remains pending.

The shared CLI/API now contains bounded backend start/stop/status primitives;
development image construction is an explicit CLI-only `backend build` action.
Six isolated tests cover digest pinning, loopback-only publication, no build/pull
on start, foreign-owner rejection, preserved storage and lost-response
reconciliation. These tests do not qualify Docker startup or guest routing.

The subsequent backend error-classification regression brings that suite to
seven tests. Both actual `backend build` attempts stopped before compilation
because Docker engine was unavailable; read-only status confirmed that exact
condition. No backend runtime resources were created. The
[backend increment](../../architecture/demo-control-backends.md) records its
remaining lifecycle gates. Brake container source is `f55bd74`, Tire foundation
is `565c3da`; neither has been Docker-built or live-qualified.

The new `unit cloud-status test` and `unit monitoring test` performed bounded
read-only tenant integration. Cloud reported Test Offline, VDP 15.0.0 installed,
no service rows and no resource samples. Missing reports remain unknown; no
guest runtime claim follows. No Cloud mutation or VM repair was attempted.

[Catalog component support](../../architecture/demo-control-image-compatibility.md)
now has an exact image/source-bound declaration reader instead of assuming a
version universally supports all payloads. The old .31 producer declaration
was registered using the explicit metadata-only Demo Control mode; repeat was
a noOp. The image bytes, SHA and qualification state were preserved and Builder
was not run. Eight source/metadata tests passed.

The integrated Test publication path now returns acceptance immediately and
reconciles processing/readiness/error separately without batch approval. Its
old-bundle live read returned `READY` for 15.0.0 while the Unit remained Offline;
no upload was repeated. The combined fixture suite at `bdee1b2` passed 337 tests.
The final checkpoint records the additional metadata-only tests and limitations.

Brake runtime source increment `dca3190c31bd9d593ec2e1a8a4763d2ed28ac984`
on `codex/studio-brake-runtime` adds host-tested v1 composition and bounded
transport primitives. CTest passed v1, v2 and seven runtime test groups (3/3
CTest targets). It is a library increment, **not a deployable service**:
bootstrap, real KUKSA adapter, growing-window transport and Linux ARM64 assembly
remain unimplemented. The diagnostic package must not be published as product.

Local Solution checkpoint: `619d107`. Remote push was rejected by the execution
permission review because the exact GitHub destination lacked explicit approval
in the current trusted request. No push workaround or remote modification was
attempted. Existing pre-implementation remote checkpoint remains unchanged.

Before P5 live SOTA there are precise integration gates, not bundle-format
guesses:

| Required service input | Proven source | Unclosed deployment binding |
|---|---|---|
| Unit UID | Native IAM `GetSystemInfo.system_id`; official SDK maps it to Cloud `system_uid` | Service access/mount to this authoritative identity |
| Unit role | Current Demo Control role input, consumed by the component runtime | No accepted service-visible role interface |
| Service version/artifact digest | Actual SM instance version and manifest digest | Exact digest meaning and trusted delivery to the service; not interchangeable archive/binary digests |
| Active VDP contract version/digest | Validated active VDP capability manifest | No current service-visible transport/change notification; an expected packaged profile is not active-runtime proof |
| KUKSA TLS trust | VM KUKSA public trust certificate; Provider uses its own systemd credential delivery | Existing service named resources do not mount that public certificate; no TLS verification bypass or Provider credential reuse |

Pinned AosCore `9eecb80c4994937b5c8cbe0464970f81e8ad4c2d`, container
`instance.hpp:138` and `instance.cpp:345`, agrees with the
[official launcher environment description](https://docs.aosedge.tech/docs/aos-core/architecture/service-manager/launcher):
standard injection gives item/Subject/instance identifiers and `AOS_SECRET`,
not the missing facts above. Per-instance environment overrides exist, but
choosing new metadata variables or resource mounts is a design/interface
decision, not evidence that a binding already exists. Platform resource
definitions are in `meta-aos-vehicle-platform/recipes-aos/aos-servicemanager/files/resources.cfg`
at platform revision `0bed8b3769b09fbe685ed599ca8d10e6594fbe53`.

Only one configured SP profile was found. This does not prove that it cannot
own Tire, but the accepted independent Tire authority mapping has not been
established. Do not reuse Brake authority by assumption, create credentials,
widen resource access or change the immutable image to bypass these gates.
Close these bounded integration decisions before claiming a deployable service
or a full UI/E2E result. No new bundle was uploaded during this increment.

The [pre-implementation source checkpoint](../../qualification/pre-studio-implementation-2026-09-09.md)
records the named return point, exact repository revisions and intentionally
excluded work. Creating or publishing that Git checkpoint does not authorize
starting P1 or any later implementation stage.

### Current gate — mockup first

Current closure, 9 September 2026: the user approved 2.8's appearance and
authorized the three post-visual audit fixes. Its
[corrective re-audit](../../research/demo-studio-action-audit.md#mockup-28-corrective-re-audit)
passes 45/45 isolated mockup checks. Cloud report isolation, continuous VDP
Safe Stop and populated-panel fit are corrected without changing the accepted
action sequence or introducing API calls. The P1–P8 order and 28 real integration
work items remain unchanged. Application implementation still needs separate
authorization. The subsequently authorized source checkpoint is recorded as
`pre-studio-implementation-2.8-2026-09-09` in the
[checkpoint record](../../qualification/pre-studio-implementation-2026-09-09.md#reviewed-28-source-checkpoint).

The following records the retained flow-review history:

After completing the questionnaire, the user explicitly required the updated
clickable mockup before any implementation. Version 2.6 simulates the agreed
normal, error, cleanup and repeat transitions without invoking Demo Control,
VMs, CARLA or Cloud. The existing screen composition is preserved.

Required order: update 2.6 → user clicks through and approves it → reconcile
the action matrix, gaps and exact call ordering in the comprehensive audit →
agree the bounded implementation plan → authorize implementation. Earlier
questionnaire statements that no mockup HTML had changed describe that earlier
review phase. They do not supersede this mockup-only authorization.

Simulation success is not evidence that an API field, native platform behavior
or current Demo Control capability has been implemented or qualified. In
particular, 2.6 exercises the conditional Q06 `Installed / runtime Not reported`
presentation; the supported Cloud runtime evidence audit remains open.

## Current reconciled sequence

9 September 2026, after the questionnaire and audit. These latest accepted
amendments supersede conflicting earlier wording and phase details. The current
Test contract is [UI-STUDIO-026](../../demo/mockups/aosedge-demo-interaction-specification.md#ui-studio-026--current-test-studio-contract).

- A warehouse variation may publish higher VDP profiles before Provision and
  receive the latest eligible release. Never force v1 or fabricate skipped chapters.
- Confirm terminal expected state even if Pending was not observed.
- Retain team authority/identity/peer bindings, but serialize foreground actions;
  concurrent team mutation is not a first-milestone requirement.
- Expanded logs/errors and terminal failed-install recovery are deferred. Basic
  truthful failure/uncertainty and safe refusal remain required. No automatic
  campaign-stop, cancellation or vehicle-service-center behavior is asserted.
- CPU is **DMIPS**. Percentages are not a substitute; unavailable is not zero.
- Subject retention is accepted. Group type and package lifetime are accepted; see the
  [accepted settings](../../research/demo-studio-action-audit.md#subject-and-package-proposal), not Cloud/package changes.

| Order | Required deliverable | Dependency / gate |
|---|---|---|
| Review now | 2.8 corrective re-audit closed; 2.6/2.7 retained; services/reload/offline/cleanup and visual-fit checks passed | Mockup/docs only; no application implementation authorization |
| P0 | Subject/package settings accepted; use the final re-audit and current contract cascade | Separate implementation authorization |
| P1 | Shared Test lifecycle/results, automatic release ledger, initial Manual connection; backend process/storage/current-Test context | Migrate backend cardinality/cleanup contracts with their implementation; retain dual-role CLI |
| P2 | Cloud inventory/instances, processing receipts, recovery, DMIPS, shared observations | Terminal state need not wait for missed Pending; expanded logs later |
| P3 | Full CLI lifecycle/VDP including warehouse variant, Park/Resume/Retire | P1 backend lifecycle already exists; product algorithms are not a startup dependency |
| P4 | Bind Presenter to the same operations; visual review | P3 and accepted composition |
| P5 | SOTA packaging/assignment/runtime and real Brake v1 durable results | Reuse P1 backend startup/context |
| P6 | Brake v2/v3 and expiring native advisory | Matching VDP capabilities and real product proof |
| P7 | Tire and offline/reconnect episode | Preserve Brake and shared SOTA/advisory boundaries |
| P8 | Full fresh CLI cycle → scoped Retire → visual UI repeat from same image SHA; qualification, commit/push, housekeeping | Contracts already current before implementation, not first updated here |
| Later | Expanded logs/errors, terminal failed-install recovery, concurrent mutations and Production | Separate bounded scope |

The existing executable backend profiles still describe a two-role API; this
is an explicit P1 migration, not a working capability. Allow exactly the owned
current Test for this flow and Test+Production for the existing dual-role flow.
Reject empty, duplicate and unrelated cleanup selectors. Change the HTTP
implementation and executable contracts together before depending on them;
never create a hidden Production VM to satisfy old cardinality.

## 1. Intended outcome and boundaries

The operator can prepare one Test vehicle from a catalog image, drive it, apply successive VDP profiles through Aos Cloud under the actual Safe Stop policy, deploy the Brake and Tire services, inspect Cloud monitoring and real product results, demonstrate offline behavior, and park or retire the owned run. A fresh run can repeat the story from the same immutable factory image with new monotonic software release versions.

The screen composition remains unchanged: separate CARLA window and native Driving Control/Telemetry on the left; architecture, lifecycle, release actions and team/Cloud views on the right. No CARLA embedding, new local database box or new navigation model is proposed.

Architectural boundaries remain in force:

- All environment and software lifecycle actions use the shared Demo Control implementation, available both through CLI and Presenter. No independent browser scripts, direct browser-to-Cloud credentials or new shell wrappers.
- Right-side Unit inventory and runtime monitoring come through Aos Cloud. Left-side driving/telemetry comes from the native vehicle/Gateway path. Product records come from their respective backend APIs.
- OEM authority owns Unit lifecycle and service assignment. Each SP owns its own service publication. A service update already assigned to a verification Unit may take effect after publication; a second manual version-specific Deploy gate must not be invented.
- Production remains part of the target product, but Production rollout is deferred. Existing Production objects are not deleted or repurposed to make Test work.
- Start with the existing qualified factory image. No VM rebuild is part of routine UX, orchestration or package-version work. A required guest change must first be identified as a separate, bounded change.
- Preserve the content-profile/release-version distinction for VDP **and services**. Never infer v1/v2/v3 functionality from a release's major version.

This plan is a review candidate beside the mockup, not a parallel normative specification. After approval, record accepted changes in the existing [interaction specification][interaction], [Demo Control design][control], affected scenario/contracts and the active implementation plan. Follow the project's [documentation change policy][doc-policy]; do not version-bump unrelated documents.

## 2. Separate mockup approval register

**Q01–Q14 and M01–M08 are ACCEPTED**, as recorded below on 9 September 2026. Q13a retains the dedicated demo Subject and accepts one scoped Retire for Finish demo and incomplete-cleanup recovery before New cycle. Q13b removes ordinary run history while preserving automatic release-number continuity. Q14 selects a complete CLI cycle followed by cleanup and a complete visually reviewed UI cycle from the same immutable image. The questionnaire is complete. Exact source/identity/type/state/order mappings remain comprehensive pre-implementation audit work, not implemented or qualified behavior. Decision approval does not authorize implementation, live cleanup or publication; present the audit and bounded implementation sequence before execution.

| ID | Recommended change | What remains unchanged | Reason / dependent work |
|---|---|---|---|
| M01 — Test scope — ACCEPTED (Q04a, option A) | The current run creates/uses **one Test VM**. Production remains visible in the target selection, disabled and labelled **Deferred**. No hidden Production VM is created or started to satisfy old guards. | CLI capability to operate test/production/all remains available; existing Production objects remain untouched. | Agrees the scope for preparation, publication and backend context. G01 implementation remains open. P1, P3, P5. Automatic/condensed preparation is a separate Q04b decision. |
| M02 — Create and baseline order — ACCEPTED | **Create option B:** create and immediately start the controller from selected Factory Firmware. **Platform Team option A:** visibly prepare, sign and publish fresh VDP v1 during the demo, before Provision. | Factory-image picker, manufacturing story, independent Platform Team and the same architectural participants. | Change the democtl pre-provision publication restriction, not the narrative. No artificial stop/start to upload; reuse the running controller for provisioning. P1, P3, P4. See the accepted decisions below. |
| M03 — Truthful states — ACCEPTED (Q06/Q07a/Q07b) | Use confirmed source-backed stages plus elapsed time; distinguish acceptance/processing/publication/pending/installed, with percentages only when measured. Use the shared visible-panel observer and stale-data policy. Q06 permits Installed / runtime Not reported only if the audit confirms no supported Cloud runtime source. | Installed differs from Running; real engineering/E2E runtime proof remains mandatory; no direct VM queries from the panel, timer-driven success or invented Pending reason. | The current adapter does not prove a Cloud limitation. Investigate supported evidence before applying the fallback. These accepted presentation policies do not close G05/G07/G12/G13/G14 implementation. P2, P4. |
| M04 — Factory VDP representation — ACCEPTED (Q05, option A) | Put meaning first: selected Factory Firmware version; **VDP — Factory baseline** for the known factory placeholder, then **VDP v1/v2/v3** with the exact release secondary. Put 0.0.0/IDs in Details. Truly absent Brake/Tire slots stay empty; unknown state stays Unknown. | Factory firmware and slot layout; pre-provision image description remains distinct from Cloud-observed installed state. | Q05 fixes the presentation, not the data integration. Resolve profiles from verified bindings, not SemVer; G25 implementation remains open. P2, P4. |
| M05 — Service release action — ACCEPTED (Q09a, option A) | First assignment to the current vehicle uses two explicit actions: **Publish service** under the owning SP, then **Deploy to Test** under OEM authority. For an already assigned identity, use **Publish update** and observe delivery/runtime, without a second version-specific Deploy. | Independent Platform/Brake/Tire ownership, shared Demo Control operations and separate service releases. | Subject assignment accepts service identity, not a version. Eligible delivery may begin after publication for an existing assignment. Amended Q09b uses distinct Brake/Tire Group Subjects; Q09c separates Cloud-confirmed update completion from functional readiness. G08/G09 integration remains open. P5, P6. |
| M06 — Session lifecycle — ACCEPTED (Q12a/Q12b/Q13a, option A) | Park/Resume preserves the owned environment; conflicting unfinished/uncertain changes cause prompt refusal without queued shutdown. Finish demo uses scoped Retire. New cycle offers/completes that same cleanup when needed before fresh Create; no mutation on page open. Retain the dedicated Subject but reset owned run bindings, and preserve persistent infrastructure/releases. | Shared Demo Control, distinct low-level lifecycle commands, no warm Pause/backups or blind replay, and explicit confirmation of owned cleanup scope. | Q13b adds scoped data deletion and persistent release-number continuity. Exact conflict/source/Subject-type/state/ordering mappings and G09/G15/G16/G17/G21/G22 implementation remain open. P3, P4. |
| M07 — Unconfirmed edge transitions — ACCEPTED (Q08b, option A) | Permit one outstanding update per component/service identity in the demo workflow. Preparation/signing of its successor remain available; Publish is unavailable until confirmed completion or resolution of the existing error. No hidden queue or timer wait. Do not claim cancellation/rollback/supersession without evidence. | Independent Platform/Brake/Tire releases remain independent; native driving controls and Safe Stop semantics are unchanged. | This is an agreed demo-tool restriction, not a Cloud limit. Exact native edge semantics and G27 implementation remain open; no new Core behavior or global team lock is authorized. P2, P3, P4. |
| M08 — Functional results and history — ACCEPTED (Q10b/Q11/Q13b, with the user's retention amendment) | Overview-first team dashboards and compact current-run history, with distinct Cloud, product and native advisory facts. A separate offline episode shows local function/advisory followed by observed delayed delivery. Retire removes owned ordinary run records, without backups, archives or automatically retained reports; preserve release numbers needed by the next run. | Existing composition, independent products, native telemetry, persistent infrastructure/releases and publication while Offline. Park preserves the current run. | Exact persistent numbering, cleanup selectors and G10/G18/G19/G20/G25/G26 integration and qualification remain open. No live cleanup is authorized. P5–P8. |

After the remaining review and pre-implementation audit, mockup corrections must stay within explicitly approved bounds. Any further change to composition, actors, authority, control semantics or the operator flow is a new explicit approval item, not an implementation detail.

### <a id="m02-accepted-create-and-platform-publication"></a>Accepted M02 decisions — 9 September 2026

The user explicitly selected **option B for Create** and **option A for Platform Team publication**. These letters belong to separate questions.

- **Create B:** the vehicle leaves manufacturing with its domain controller already running the selected base firmware. Presenter Create composes the existing disk-creation and VM-start operations through Demo Control. It does not silently provision the Unit. Keep the low-level `environment create` disk-only command and `vm start` available independently; do not silently change their CLI semantics. Show Running only after startup is observed.
- **Platform Team A — Full story:** show real preparation, signing and upload of a fresh release carrying the VDP v1 profile as Platform Team actions during the demo, before provisioning. Do not silently consume this chapter in Full story or replay an already completed upload as a new action. Explicitly selected Quick preparation is the separate Q04b case below. Exact button grouping remains a later UX detail.
- **Audience sequence, including accepted Q03:** Create and boot the factory controller → connect CARLA/Gateway with the vehicle stationary in Manual → Platform Team prepares/signs/publishes VDP v1 → provision the already running and locally connected controller and establish the agreed Test verification-set membership → observe delivery → apply under the native Safe Stop condition. Delivery and installation remain separate observations; this decision creates no manual Cloud install or approval gate.
- **Independent work:** the platform team can prepare its release while the vehicle is being manufactured. Publication is not inherently a command against a running or stopped VM. The current democtl power-state restriction must be revised for this pre-provision path while preserving artifact compatibility, authority and actual recipient-scope checks. It must not be worked around by stopping and restarting the controller.
- **Repeatability:** v1 names the content profile, not a fixed Cloud release number. A repeat uses a new monotonic release carrying that profile, published before provisioning, under the existing repeat-cycle policy.

The prior M02 recommendation to keep the controller stopped after Create is superseded. These decisions settle the narrative and required contract direction, not G02 implementation, other pending decisions or any live operation. Initial source-connection timing is settled separately by Q03 below.

Review impact: class B, behavior within existing component/authority boundaries. The affected targets for the final audit and canonical cascade are the interaction specification, demo scenario/flows, Demo Control lifecycle/publication contracts, Presenter mappings and their tests. This entry is the working approval record; the canonical cascade and implementation are not claimed complete. Mockup HTML and application code remain unchanged during this questionnaire.

### <a id="q03-accepted-initial-vehicle-connection"></a>Accepted Q03 — initial vehicle connection, 9 September 2026

The user selected **option A: connect after Create, before Provision**, with
the vehicle **stationary in Manual**. Once the factory controller has started,
start or reuse the session's CARLA/Gateway/native surfaces and establish the
first local vehicle connection through Demo Control. Do not automatically
activate Safe Stop, start Autopilot or reuse ordinary `vehicle select` if its
Safe Stop/reset behavior would change this initial state.

Preserve the local connection during the subsequent Platform publication and
provisioning chapter; do not insert a detach/reconnect or VM restart merely
to satisfy the existing provisioning guard. Local connectivity does not imply
Cloud registration or OTA installation. Safe Stop remains an explicit native
driving action governed by the vehicle runtime.

Required follow-up: expose the initial-connection operation, distinguish
provisioning from retirement in the shared source guard, and verify that the
official provisioning path preserves local telemetry and the initial mode.
Do not weaken the deprovision/delete guard as a side effect. Acceptance of
this behavior does not prove that G03 is implemented or qualified; it remains
an open implementation gap. This class-B decision updates the working review
record only, with the canonical cascade and full audit before implementation.

### <a id="q04a-accepted-test-scope-and-production-presentation"></a>Accepted Q04a / M01 — Test scope and Production presentation, 9 September 2026

The user selected **option A**: the current demo uses **one Test VM**;
Production remains visible in the target selection but cannot be selected or
operated from this demo flow, with the English label **Deferred**. Do not
instantiate a second vehicle merely to accompany that disabled choice.

Retain the existing CLI ability to address `test`, `production` and `all` for
separately scoped work. This decision neither starts a Production VM nor
authorizes deleting, repurposing or changing existing Production resources.
Align Test lifecycle, publication prerequisites and backend context with this
single-vehicle scope; do not require a hidden Production instance to pass a
guard. Genuine publication-recipient and ownership checks still apply.

This accepts M01's operational scope and presentation. The condensed
preparation mode is accepted separately under Q04b below. G01 remains an implementation and
verification gap. No application, mockup HTML or live system has changed.

### <a id="q04b-accepted-preparation-modes"></a>Accepted Q04b — Full story and Quick preparation, 9 September 2026

The user selected **option A: two explicitly selectable modes**, using the
same Demo Control operations and state/operation journal, not separate
helpers, scripts or lifecycle implementations.

- **Full story:** preserve the accepted chapters. The operator initiates
  Create, Platform v1 preparation/publication and Provision separately;
  technical steps within each chapter are automated. Initial CARLA/Gateway
  connection follows Create as agreed in Q03.
- **Quick preparation:** one explicit operator button/command composes the
  same ordered operations: create/start one Test controller → connect
  CARLA/Gateway, stationary in Manual → prepare/sign/publish a fresh release
  carrying VDP v1 → provision → confirm Cloud Online and Test verification-set
  membership. It completes before the first drive and Safe Stop, with no
  automatic Autopilot or Safe Stop action.
- **Honest state:** show stage/progress and completed preparation chapters as
  already completed. Do not reenact their upload or provisioning as new
  actions. Show the actual observed VDP state; completion of preparation does
  not assert installation or functional readiness and does not wait for the
  operator's future Safe Stop to claim that an update is installed.
- **Explicit start:** opening/reopening the page or merely selecting a mode
  does not create, publish or provision anything. The operator initiates the
  operation. Existing-operation reconciliation remains shared and does not
  replay completed mutations or silently create a second run.

This is an additional preparation path, not a change to Full story's visible
Platform chapter. Exact UI placement and the mode selector's CLI syntax must
be included in the final action mapping/audit. The current two-VM/approval
preparation implementation is not thereby accepted as correct; the recorded
G01/G03/G04/G21/G22 corrections and qualification remain pending. No code,
mockup HTML or live operation is changed by recording this class-B decision.

### <a id="q05-accepted-factory-slots-and-versions"></a>Accepted Q05 / M04 — factory state, slots and versions, 9 September 2026

The user selected **option A: meaning first, technical detail on inspection**.

- **Factory Firmware:** display the selected image's actual version from its
  catalog description; do not hardcode a factory revision.
- **VDP before OTA:** display **Factory baseline** for the known factory
  placeholder. Keep its raw **0.0.0** value in Details rather than presenting
  it as the first OTA capability profile.
- **VDP after an observed OTA installation:** display **VDP v1/v2/v3** as
  the primary capability label and the exact Cloud release as secondary
  information. Resolve the profile from a verified release/profile binding;
  do not infer it from the release's major version or fabricate an unknown
  profile. Keep component/version IDs and other technical fields in Details.
- **Brake/Tire slots:** leave the planned positions empty when their absence
  is confirmed. Failed, incomplete or unavailable observations mean
  **Unknown**, not an empty slot or a successful installation.
- **Source boundary:** before Provision, the selected image description is
  a **Factory configuration**, not a Cloud observation of the Unit. After
  registration, installed software is observed through Cloud. Do not invent
  a Cloud result before registration or substitute direct VM reads.

This accepts M04 and the related G25 presentation choice. Identity/profile
binding and source integration remain open implementation work. Q06 still
owns installation-versus-runtime evidence; this decision does not equate
Installed with Running. This is a presentation decision inside the accepted
source boundaries; only review documents are updated at this stage.

### <a id="q06-accepted-cloud-runtime-evidence"></a>Accepted Q06 — Cloud runtime evidence, 9 September 2026

The user selected **option A** for the first UI milestone. The final audit
must first investigate supported Cloud sources for the running state of the
specific installed VDP version. The current adapter's fixed
`NOT_REPORTED_BY_CLOUD` field is not proof that the platform lacks this data.

If no supported source is confirmed, show the Cloud-reported **Installed**
state and runtime **Not reported**. Missing runtime evidence alone does not
block acceptance of the first UI milestone; it means unknown, not stopped,
failed or healthy. If a supported source is found, use its actual result with
version/time context rather than retaining an unnecessary fallback.

Actual VDP operation must still pass engineering observation through the
existing `democtl` diagnostics and E2E. That separate proof does not populate
the Cloud-only Presenter model. Do not equate Installed with Running, use
native telemetry as VDP runtime proof, or query the VM directly from the
panel. New platform/guest interfaces are not implicitly authorized by this
decision. G05 implementation/evidence work remains open. Q06 settles this
part of M03 only; remaining presentation details are not silently approved.

### <a id="q07a-accepted-cloud-observation-refresh"></a>Accepted Q07a — shared Cloud observation and refresh, 9 September 2026

The user selected **option A: automatic refresh of the visible panel**.

- Read on entry and after relevant actions. During pending software delivery,
  start with a **2-second** observation interval and back off to **10 seconds**;
  use **10 seconds** for visible idle inventory. These are configurable
  observation intervals, not artificial command delays, completion deadlines
  or promises that the device reports new data at that rate.
- The architecture map and dashboards share one snapshot/read model and one
  in-flight request per observation key. Hidden tabs create no additional
  requests. Resource metrics are read only while their monitor is visible.
  Navigating away does not cancel an active operation or its required
  reconciliation; it stops duplicate view-driven observation, not the work.
- On read failure, preserve last-known values with an explicit stale/source-
  unavailable indication. Do not convert a read error into Unit Offline,
  empty inventory, zero metrics or a healthy state. Keep observation time
  distinct from the device/sample timestamp where that source provides one.
- This observer uses the existing Cloud adapter boundary. It does not repeat
  full environment/access audits, image hashing, unpacking or VM diagnostics
  as part of refresh. No direct VM data is added to the Cloud-only panels.

This records the approved policy, not a working observer. G12/G14 integration
and metric/source validation remain open; log requests and progress
presentation remain the separate Q07b decision.

### <a id="q07b-accepted-cloud-logs-and-progress"></a>Accepted Q07b — Cloud logs and operation progress, 9 September 2026

The user selected **option A: the complete log workflow in the demo UI**,
also available through the same Demo Control operations in the CLI.

- **Logs** lists existing Cloud log records/requests. Opening it may read the
  list but must not initiate another collection.
- **Request logs** explicitly starts collection for the selected Unit or
  service and time range. Preserve the relevant OEM/SP ownership/access
  boundary; do not request unrelated vehicle or team logs.
- Follow the actual asynchronous request IDs and show their observed state;
  provide viewing and download when results are ready. Handle multiple IDs,
  empty results, waiting and errors without creating replacement requests
  just because the operator reopened the panel.
- Across operations, display the **confirmed current stage and elapsed
  time**. Show a percentage only if measurable progress is available; do not
  advance installation, collection or success by a timer. Do not invent a
  reason for Pending. Upload acceptance is not completed processing,
  publication, installation or runtime proof.

Q07b completes the remaining M03 presentation decision and accepts the G13
UI/CLI direction. G07/G13 integration, safe response mapping and verification
remain open. This records the design only: no logs are requested, no Cloud
operation is performed, and no implementation or mockup editing starts here.

### <a id="q08a-accepted-offline-publication"></a>Accepted Q08a — publication while the vehicle is Offline, 9 September 2026

The user selected **option A: allow publication while a provisioned Test
vehicle is Offline**. The operator's computer must still be able to reach
Cloud with the appropriate publication authority. Vehicle connectivity is
not a prerequisite for the Platform Team to prepare, sign or publish.

Preserve compatibility, identity, ownership and agreed recipient-scope
checks. Upload is a release publication, not a Unit-addressed transport;
the selection of Test in the UI does not by itself constrain Cloud delivery
to that one Unit. If the recipient scope cannot be established, report the
actual blocker rather than weakening the guard.

Show publication processing/result, vehicle connectivity and delivery/install
observations separately. Offline alone does not prove a particular Pending
reason, successful publication or completed delivery. After reconnect,
observe the actual result without promising immediate delivery/installation
or automatically republishing the release. This decision adds no new local
installation gate and does not change the native Safe Stop policy.

Revise the democtl Online-publication guard accordingly after the final
audit. G06 implementation/verification remain open. Q08b still owns the
policy for another publication while an earlier update is outstanding. No
live upload or other system mutation is authorized or performed here.

### <a id="q08b-accepted-one-outstanding-update"></a>Accepted Q08b / M07 — one outstanding update per identity, 9 September 2026

The user selected **option A**. For the active demo workflow, allow only one
outstanding update per component or service identity. The next release may
be prepared, inspected and signed, but its Publish action is unavailable
until the current update has a confirmed completed outcome or its error has
been resolved. Apply this policy through the shared Demo Control core for
both UI and CLI; report the reason promptly, without a hidden queue, a
background delayed publication or an artificial command wait.

Do not serialize unrelated identities or teams: pending VDP does not itself
block independent Brake/Tire publication. This restriction does not mean the
Cloud platform forbids overlapping releases. It narrows this demonstration;
it does not introduce a dispatcher, a new update queue or cancellation API.

For VDP, confirmed Cloud installation of the expected release closes this
publication guard; do not add a requirement for an unavailable Cloud Running
field contrary to Q06. Actual engineering/E2E runtime proof remains required
for qualification. Service completion follows Q09c below and must use its actual supported status
mapping, which is part of the remaining SOTA review. Read failures, elapsed
timeouts and unknown outcomes do not prove completion. Reconcile the recorded
operation/error before enabling a successor; do not issue blind retries.

Do not claim that publishing a successor cancels/replaces a pending payload,
or that leaving Safe Stop cancels an installation. Native edge semantics
remain evidence questions, especially for later shutdown/recovery review.
G27 implementation/verification remain open. No release is published and no
code or mockup HTML is changed by recording this decision.

### <a id="q09a-accepted-service-publication-and-assignment"></a>Accepted Q09a / M05 — first service assignment and subsequent updates, 9 September 2026

The user selected **option A**. For a service not yet assigned to the current
vehicle, expose two explicit operator actions: **Publish service**, using
the owning Brake or Tire Service Provider publication authority, followed
by **Deploy to Test**, using the OEM delivery authority. Both UI and CLI use
the same Demo Control implementation; no manual scripts or direct
browser-to-Cloud mutation path is introduced.

Publication must be reconciled through its actual processing/ready state;
upload acceptance alone is not a deployable release. Under the 11 September
amendment, package readiness does not locally gate identity association. Deploy establishes the
service-identity/Subject/Test binding and observes the resulting assignment.
It does not assert that an instance has installed, started or become
functionally ready. First assignment means first assignment to this vehicle,
not necessarily the first publication of that identity in Cloud history.

For an identity already assigned to the vehicle, expose **Publish update**
and observe actual delivery, installed version and runtime. Do not require
a second Deploy click or pretend that Subject assignment selects the new
version: the API accepts `service_ids`, not a service-version UUID. An
eligible verification Unit may begin receiving the update after publication,
without validation-batch approval. Existing bindings must therefore be
reconciled before offering the first-assignment flow, particularly on a
repeated demo run.

This accepts M05's action semantics only. The subsequent Q09b decision below
settles Subject allocation, ownership and Test scope; Q09c below settles repeated profile releases and
completion/readiness criteria. G08/G09 integration and verification remain
open. No application, mockup HTML, live Cloud state or VM is changed by
recording this decision; the canonical cascade follows the final audit.

### <a id="q09b-accepted-shared-test-subject"></a>Accepted Q09b — dedicated service Subjects, amended 11 September 2026

The original 9 September choice of one shared Subject is superseded by the
user-approved 11 September change: **one dedicated Group Subject per logical
service**, Brake and Tire, both scoped to current Test. Do not create a new
Subject for every release.

- **Scope and authority:** record the exact Subject identity and its demo
  ownership. Its Unit membership is limited to the current Test `system_uid`;
  do not reuse an unrelated/shared Subject or include Production. OEM delivery
  authority manages the assignments through shared Demo Control. Brake and
  Tire retain their separate SP publication identities and permissions;
  Subject allocation grants neither team the other's publication authority.
- **Independent actions:** each service has its own first **Deploy to Test**.
  Assigning Brake does not assign Tire, and assigning Tire preserves Brake's
  existing binding. Resolve the requested service's exact recorded Subject;
  create it only when necessary and authorized, not on every click. Reconcile
  partial/uncertain binding outcomes before retrying. A Subject is not
  a combined release, a global update lock or a version selector.
- **Presentation:** keep the Subject as an integration detail, available in
  Details rather than another actor on the main architecture scene. The
  audience still sees services being deployed to the Test vehicle.
- **Lifecycle boundary:** Q13 will decide retention, reuse across retired
  runs and deletion. This decision does not authorize deleting an existing
  Subject or attaching a fresh Unit to stale service assignments. The repeat
  flow must preserve the agreed explicit first-assignment story.

This is a class-B working review decision within the existing OEM/SP and
Demo Control boundaries. The final audit/canonical cascade must cover Subject
binding, recipient scope, partial operations and cleanup. G09/G28 integration
and tenant/role qualification remain open; no rights, Cloud objects, VM state,
application code or mockup HTML are changed by recording the decision.

### <a id="q09c-accepted-service-update-completion"></a>Accepted Q09c — service update completion and functional readiness, 9 September 2026

The user selected **option A: separate technical update completion from
functional readiness and demonstrated results**.

- **Repeat releases:** retain each service's identity and owning SP. Repeating
  a v1/v2/v3 content profile uses a new monotonically increasing release
  version for that service, with a verified profile/release binding. Brake
  and Tire have independent release sequences. Do not reset a Cloud version,
  create a new service identity per run or infer the profile from SemVer.
- **Update completion:** close the outstanding service update only when
  Cloud confirms the expected version installed and the required instances
  of that version running on the intended Test/Subject/service binding.
  Use the accepted instance requirement and actual version/run-state/error
  observations; assignment alone, an old running version or zero instances
  does not qualify. This completion releases Q08b's per-identity publication
  guard for the next update; it is not full demo/E2E acceptance.
- **Separate function state:** report whether the function is awaiting
  required capabilities/data, ready to operate or has produced a result,
  based on authoritative functional evidence. A process may run while its
  function is deferred. Do not hold an otherwise completed technical update
  open until the operator brakes or another product event occurs. A missing
  functional signal is Unknown/Not reported, not fabricated readiness.
- **Evidence and errors:** the Presenter obtains installed/runtime facts
  through Cloud, not a direct guest probe. Missing/stale/ambiguous Cloud
  evidence or unresolved update errors do not count as successful completion.
  Map concrete API fields, instance requirements and error/reconciliation
  cases in the final audit; this decision adds no invented platform status,
  native FOTA dependency or local service admission gate.
- **Qualification:** functional results and applicable advisory delivery
  remain mandatory in the corresponding E2E scenario. A green technical
  update must never imply that a product result was received or that a driver
  advisory reached the vehicle. Q10/Q11 own their detailed source/presentation
  and delivery distinctions; Q13 still owns cross-run Subject cleanup.

This is a class-B working review decision. G10/G11/G25 implementation and
qualification remain open, including monotonic release allocation and the
real Cloud/functional mappings. Only review documents change; no application,
mockup HTML, VM, backend or Cloud release is changed by this acceptance.

### <a id="q10a-accepted-backend-preparation"></a>Accepted Q10a — prepare both product backends with the environment, 9 September 2026

The user selected **option A**: prepare the Brake and Tire backend
applications as part of the explicitly initiated environment preparation,
not when their services are first deployed.

- **Shared orchestration:** Full story's composed Create and Quick
  preparation use the same Demo Control backend lifecycle operations. Start
  the demo-owned applications or reuse the appropriately bound running
  instances; do not add a second UI implementation, helper or new operator
  step. The low-level disk-only `environment create` contract remains intact.
- **Independent products:** the backends are server-side team applications,
  not the Brake/Tire workloads inside the vehicle. Preparing them neither
  publishes nor deploys a service, changes a Subject assignment, provisions
  a Unit nor starts a Production vehicle. The two teams retain independent
  application/data ownership and their later explicit release actions.
- **Current vehicle context:** bind queries to the current Test identity once
  it is known through the agreed lifecycle. Before that, report that vehicle
  context is not yet available. Do not substitute an old Unit, mix records
  from another run or require a hidden Production identity. A live server
  alone does not prove current-vehicle query readiness or functional success.
- **Early dashboard access:** make the backend views available before service
  deployment. Show actual no-context/no-service/no-results or error states,
  based on their respective sources, without generated records. Opening or
  reopening a dashboard only reads; it does not start/restart an application
  or repeat a preparation action.

Q10b below settles the detailed result/advisory presentation. Q12a accepts
Park/Resume; Q12b/Q13 still own interrupted work, retirement and data retention. Backend reuse is not permission
to clear history. This class-B working decision settles preparation timing,
not existing implementation readiness. G18/G21 integration, persisted storage,
query context, guest routing and partial-startup/error mappings remain open
for the final audit and canonical cascade. No backend, VM, Cloud object,
application code or mockup HTML is changed by recording this acceptance.

### <a id="q10b-accepted-overview-first-backend-dashboards"></a>Accepted Q10b — overview-first team dashboards, 9 September 2026

The user selected **option A**. Clicking the Brake or Tire backend card
opens that team's dashboard in the existing right-hand panel. Preserve the
accepted screen composition and navigation; do not add an architectural
actor, move the native panels or replace the map with a new layout.

- **Service overview:** show the installed service version and runtime state
  from Aos Cloud, with access to the shared controller-monitoring view. Do
  not substitute direct guest observations or infer runtime from product
  records. Retain the actual role/read scope and missing-evidence states.
- **Latest result:** show the team's most recent persisted result, its time
  and data sufficiency/quality when supported by its backend API. Preserve
  the actual product distinctions: a captured window, an assessment and an
  advisory are not interchangeable successes. The UI does not calculate the
  product outcome or generate one after a timer or every Safe Stop.
- **Advisory:** show the recommendation recorded by the team's backend, or
  its source-backed absence/unavailability. A backend advisory record does
  not establish vehicle delivery or driver acknowledgement. Actual advisory
  display in the car remains on the left native telemetry panel, using its
  vehicle data source; do not bridge it into a fabricated Cloud/backend fact.
- **Compact history:** place recent records below the overview. Selecting a
  record reveals available input data, event correlation, software versions
  at the time of the event and capture/receipt times. Use event provenance,
  not today's inventory, and keep records scoped to the current Test/run.
  Use bounded history/pagination without removing access to older records
  in the permitted scope. This is not a retention/deletion decision.
- **Honest absence and freshness:** distinguish a successfully read empty
  result set, unavailable context, missing fields, stale last-known data and
  a read error. No-result or unavailable advisory does not mean healthy or
  normal. Opening/navigating the view remains read-only under Q10a.

This class-A presentation decision accepts the corresponding part of M08
within the existing source boundaries. Concrete field mappings, backend
implementation, error/freshness handling and E2E proof remain G18/G19/G25
work. Q11 below settles the offline episode and independent delivery observations;
Q13 owns retention. No application, HTML mockup, backend, VM or Cloud state is
changed by this working approval record; canonical updates follow the audit.

### <a id="q11-accepted-standalone-offline-episode"></a>Accepted Q11 — standalone offline episode, 9 September 2026

The user selected **option A**: demonstrate offline operation as a separate
chapter after the required VDP and service versions are installed and their
local functions have been established. Do not include a new software release
as a required action inside this episode.

1. Through the existing shared Demo Control/native action, disable only the
   current Test vehicle's external connectivity. Preserve local CARLA/Gateway
   telemetry and the operator computer's Cloud/backend access. Confirm the
   actual control outcome; do not equate it with Cloud already reporting
   Offline.
2. Exercise the installed local functions using suitable real data/stimulus
   and show actual in-vehicle advisory where produced. The backend cannot
   display records it has not received. Do not invent an outbox count, local
   result or Pending reason from a connectivity toggle or timer.
3. Restore the vehicle's external connectivity through the same control
   path. This removes the fault; it does not itself prove Cloud Online,
   backend receipt, queue drain or advisory acknowledgement.
4. Observe Cloud reconnection and delayed backend delivery independently.
   Correlate received records to the offline events and their original capture
   times/provenance. Use actual durable receipts and native advisory evidence;
   preserve duplicate/error/partial-delivery states rather than announcing
   that everything drained immediately.

Q08a's ability to publish while a provisioned vehicle is Offline remains
available; this decision changes the main story sequence, not the publication
guard or native update semantics. It does not freeze Cloud or cancel pending
work. Reconnection does not automatically republish software, restart the VM
or trigger Safe Stop. Native FOTA and QM-service policies remain unchanged.

The final G20 audit must prove that the fault blocks the vehicle's product
backend uplink as well as its Cloud link while preserving the local vehicle
data path and the operator's access. Local continuity, persisted outbound
records, retry/acknowledgement behavior and event provenance remain real
implementation/E2E requirements, not claims established by this acceptance.
This class-B working decision accepts M08's offline episode, not retention
or implementation. No connectivity, application, VM, backend, Cloud object
or mockup HTML is changed; Q12/Q13 and the final audit remain pending.

### <a id="q12a-accepted-full-park-resume"></a>Accepted Q12a — one full-stop Park/Resume, 9 September 2026

The user selected **option A**: provide one **Park/Resume** pair for a demo
break, without adding a separate warm **Pause/Continue** mode.

- **Park:** gracefully stop the owned local demo VM/runtime, CARLA/Gateway,
  native control/telemetry surfaces and product backend applications through
  shared Demo Control. Limit the action to the current run's owned resources;
  do not stop unrelated processes or Production. Preserve the working disks
  and their installed content, existing Cloud identity/assignments, backend
  records and the operation/session state needed for continuation.
- **No destructive lifecycle:** Park does not deprovision or delete a Unit,
  retire the overlay, clear product history, publish software or create a
  backup/snapshot. Cloud connectivity may subsequently become Offline; a
  local stop receipt is not itself a Cloud observation.
- **Resume:** start the same retained environment, restore its applicable
  connections and read current state. Do not replay Create, provision,
  signing/upload or already completed operations. Preserve a partially
  prepared session as such: Resume does not silently provision it. Existing
  identities and working disks are reused, not replaced with a fresh run.
- **Observed outcome:** report actual startup/stop progress and partial
  failures. Parked requires the scoped local runtimes to have stopped;
  Resume cannot report Online or software readiness from a saved UI flag.
  Preserving installed content does not freeze Cloud or prevent its native
  desired-state reconciliation after the vehicle returns.

This class-B working decision accepts ordinary Park/Resume scope. Q12b below
settles the active/uncertain-operation and recovery policy; its exact source
mapping remains audit work. Neither decision permits interrupting an
installation or claiming cancellation. Q13 separately owns retirement and
data retention. G15/G16/G22 integration, ordering and qualification remain
open. No process, VM, backend, Cloud state, application or mockup HTML is
changed by this approval record; canonical updates follow the final audit.

### <a id="q12b-accepted-prompt-park-refusal"></a>Accepted Q12b — prompt Park refusal and interrupted-operation recovery, 9 September 2026

The user selected **option A**. When a conflicting mutating operation or
update affecting the current environment remains unfinished, or its outcome
is unresolved, Park returns promptly with the actual reason and relevant
operation identity/stage. It does not begin stopping resources, wait for
completion or register an automatic future Park. Once the conflict completes
or its outcome is reconciled, the operator explicitly requests Park again.

- **Bounded conflict policy:** apply this to relevant changes, not ordinary
  background status reads or an unrelated team's activity. Reuse the shared
  operation/state model. This is not authorization for repeated environment
  audits, arbitrary sleeps or extra backup/preflight workflows.
- **No implied cancellation:** do not force-kill an installation, treat a
  lost response as success or cancellation, or automatically enter Safe Stop
  to finish an update. A pending FOTA operation must be considered in the
  shutdown analysis because stopping the simulator may affect its native
  gate. Exact pending/active/unknown cases and observation sources must be
  closed in the final audit, without inventing a Cloud Installing field.
- **Recovery after interruption:** on reopening or resuming after a crash,
  recover the existing operation journal and reconcile authoritative actual
  outcomes for the recorded identities. Do not replay completed publication,
  provisioning or other mutations blindly, create a replacement identity,
  or restart the entire workflow to resolve a lost response. An unresolved
  result stays explicitly uncertain until reconciled; show the required next
  action rather than claiming completion.
- **Shared behavior:** CLI and Presenter use the same conflict decision,
  reason and recovery state. The UI may observe the conflicting operation,
  but that observation is not a queued shutdown. An explicit Park retry after
  resolution is distinct from repeating the original uncertain mutation.

This class-B working decision accepts M06's Park/recovery policy, not a native
Cloud cancellation mechanism or proven shutdown ordering. G16/G22/G27 source
mapping, race/partial-outcome handling and qualification remain open for the
comprehensive audit. Q13 still owns retirement. No live operation is stopped,
queued or retried and no application/mockup HTML is changed by this record.

### <a id="q13a-subject-documentation-review"></a>Q13a documentation review — Subject retention subsequently accepted

On 9 September 2026 the user requested a documentation check before choosing
the Subject retirement policy. The [Subject lifecycle review in the action
audit](../../research/demo-studio-action-audit.md#subject-lifecycle-review)
shows that a Subject is not inherently a per-run resource. The earlier
recommendation to delete it on every Retire is withdrawn. API deletion
support is not a platform requirement to delete it with a Unit.

Q09b's accepted one-current-Test scope and independent Brake/Tire assignment
remain unchanged. The user subsequently accepted retaining a persistent
dedicated demo Subject and managing its bindings separately, as recorded below.
Before closing the remaining Q13a details, distinguish factory/NodeType Subjects from a demo-managed
Subject, agree group/state semantics and preserve explicit first deployment
when a fresh Unit is bound. Do not silently retain stale service assignments,
change `is_group`, delete an object or expand permissions. Actual tenant
Subjects and deletion cascades were not established by this documentation
review. Retire and backend retention remain pending.

### <a id="q13a-accepted-subject-retention"></a>Accepted Q13a part — retain the demo Subject, 9 September 2026

Following the documentation review, the user accepted the revised
recommendation: retain the dedicated demo Subject across runs and manage its
Unit/service bindings separately. Do not delete/recreate this Subject as a
routine Retire action. This does not authorize modifying factory/NodeType
Subjects, changing `is_group`, preserving stale assignments or adding another
Unit to a shared production scope. Q09b's independent Brake/Tire deployment
and one-current-Test targeting remain unchanged.

The user subsequently accepted the shared retirement policy below for the
end of a demo and the start of a new cycle. Implementation and live deletion
remain unauthorized at this review stage. Exact Subject identity/type/state
semantics require the final audit; backend retention is settled by Q13b below.

### <a id="q13-clean-cycle-cleanup-proposal"></a>Accepted Q13a — shared Retire at demo completion and before a new cycle, 9 September 2026

The user selected **option A**: an explicit **Finish demo** action executes
Retire, while **New cycle** offers/completes the same Retire if previous owned
resources or partial cleanup remain, then starts the fresh flow only after
confirmed cleanup. Use one shared Demo Control implementation for both entry
points, with explicit confirmation of the owned cleanup scope. A clean entry
does not replay already completed teardown. Keep Park as a separate choice
for preserving and resuming the same run. Opening the UI, selecting an image
or requesting status does not trigger deletion. The scope below is accepted,
including the subsequent Q13b product-data amendment; technical qualification
and actual implementation still follow the comprehensive audit.

| Scope | Accepted cleanup policy | Preserve / boundary |
|---|---|---|
| Current Test Unit | Ordered deprovision and Unit deletion; reconcile its exact Unit Set/Subject membership and Unit-owned Node absence | Permanent Sets/Fleet/Model and unrelated Units. Do not issue a separate blind Node delete or require Production. |
| Dedicated demo Subjects | Independently remove the retired Test binding and owned service assignment from Brake and Tire Subjects so each next first Deploy remains explicit | Retain both Subject identities/configuration, service identities/SP ownership and published versions. Never reset an unrelated/factory Subject or other recipients. |
| Cloud settings | Restore only explicitly recorded temporary run-owned changes to their agreed baseline, where such changes were actually made | Do not reset all Cloud settings, recreate roles/Sets, overwrite unrelated drift or infer baseline values. Persistent verification settings are not temporary by default. |
| Local run | Stop owned producers/runtimes; remove working overlays/factory copy, run-specific access material and transient runtime/operation files after external reconciliation | Source image/catalog, source repositories, reusable release artifacts, fixed OEM/SP credentials and the cross-run release-number record. No backups, ordinary run archives or image rebuild. |
| Product backend data | Q13b: after producers are stopped, remove only the retired run's records through each team's scoped preview/execute contract, then clear current-run context | Other Units' data and product schemas/configuration. No ordinary demo-result history is retained. Keep backend APIs alive until cleanup is confirmed. |
| Published Cloud software/history | No routine deletion in environment cleanup | Component/service identities, published versions/bundles and platform-managed audit records. A repeat publishes a higher release carrying the desired profile. |

Ordering must use the actual lifecycle, not start with a full Park: today's
deprovision needs a live VM and stops it only after Cloud revocation; backend
cleanup needs its applications running. Quiesce the owned data producers
before record cleanup. Reconcile external outcomes before removing the local
journal/selectors needed for recovery. Partial cleanup remains resumable and
does not qualify the next run as clean; do not replay completed mutations.

The clean-entry result is **no leftover owned run**, not an empty Aos Cloud:
no old Test Unit/bindings, no stale service assignments in the dedicated
Subject, no owned working VM/runtime, agreed persistent settings intact and
backend history handled under the chosen policy. Fresh Create then uses the
catalog image, publishes a new VDP v1-profile release before Provision, and
retains separate first Deploy actions for Brake/Tire. Do not delete Cloud
releases to force the initial profile.

This is a class-B working approval within existing Demo Control and OEM/SP
boundaries, not a command to clean the live environment. Map the approved
composition and results into canonical documents after the final audit.

Current implementation evidence: `Environment.retire` is local disposal with
Cloud absence verification, not deprovision/delete orchestration. Unit
deprovision/delete exist, but Subject/settings/backend cleanup is not joined
into that path. Product cleanup contracts use exact selectors and
preview/execute tokens; the current two-Unit requirement must become the
accepted Test-only scope without inventing a Production Unit. G01/G09/G18/
G21/G22/G26 and the final call/error/order audit remain open.

### <a id="q13b-accepted-clean-run-release-continuity"></a>Accepted Q13b — clean run with persistent release-number continuity, 9 September 2026

The user accepted removing ordinary run data and added one necessary
cross-run exception: **retain the software release numbers used during a run
so the next run starts with the correct higher releases**. This is operational
release continuity, not an archive of demo telemetry, product results or reports.

- Retire removes the owned run's Brake/Tire records and transient environment
  state; it does not generate backups, run archives or automatic result dossiers.
  Park continues to preserve the same run under Q12a.
- Preserve numbering independently for the VDP component, Brake service and
  Tire service, keyed by their actual software identity and owning Cloud scope.
  Retain explicit profile-to-release bindings: repeating profile v1 must not
  reset the published release number or infer functionality from SemVer.
- **Operator clarification accepted:** release numbers are assigned automatically
  by the shared Demo Control implementation, in both CLI and Presenter flows.
  The operator selects the product and content profile (v1/v2/v3), not a release
  number. Display the assigned number as read-only information and return it in
  the operation result; manual version entry is not an operator prerequisite.
  Allocate/reserve once when preparing a new release, before packaging/signing;
  signing and publication reuse that exact release. Status, navigation and
  recovery of the same operation must not allocate another number. Automatic
  numbering does not authorize automatic publication or another demo action.
- The next run starts its v1 profile above that identity's used release range,
  followed by higher v2/v3 releases as those actions occur. Do not force all
  three products onto one shared counter or require unused releases to exist.
- This minimal release record survives Retire and does not depend on old VM
  overlays, ordinary operation history or retained version directories.
  Source images, reusable profiles, permanent Cloud configuration/credentials
  and published Cloud releases remain reusable assets under Q13a, not run data.

Implementation recommendation for the final audit, not a new implemented
interface: maintain used/reserved release numbers, verified content-profile
bindings and the minimum publication identifiers/outcome needed for recovery.
Reconcile the scoped Cloud version inventory when allocating/publishing a new
release, reusing that observation rather than adding a full environment audit
or checking numbering on every status refresh. Account for releases made
outside this UI. An uncertain upload must not make its number reusable or be
blindly republished; record the reservation before publication and reconcile
the existing action. Skipped numbers are preferable to accidental reuse.
Exact storage/schema, concurrency and scoped recovery belong to G10/G22/G25.

Current implementation evidence: `Components.prepare` checks the maximum
version among local directories; `_publish` rejects a version not higher than
the Cloud `latestPublishedVersion`. Those guards do not constitute a durable
cross-run allocator independent of cleanup. Extend the shared Demo Control
path to preserve numbering for components and services, not a separate helper.
Today's explicit-version preparation interface must be mapped to this accepted
automatic operator flow during the final CLI/result-schema audit; it is not
already implemented merely because the monotonicity guards exist.

This class-B working decision supersedes the proposed ordinary-demo evidence
retention in Q13b. Reconcile the separate pre-existing formal qualification
contract during Q14 and the canonical audit; this planning approval does not
delete existing qualification artifacts or modify a live environment. No code,
mockup HTML, package, backend record or Cloud object is changed.

### <a id="q14-accepted-cli-then-visual-ui-repeat"></a>Accepted Q14 — full CLI cycle, then clean visual UI repeat, 9 September 2026

The user selected **option A**. After the pre-implementation audit and separately
authorized implementation, qualify the agreed complete Test-vehicle story in
two fresh cycles:

1. Execute the complete lifecycle, VDP/service profile transitions, functional
   backend/advisory observations and offline/reconnect story through `democtl`.
   Include the agreed Park/Resume behavior without substituting a new run.
2. Use the accepted shared Retire to remove the owned run and its Cloud
   bindings/product records; preserve reusable assets and automatic release
   numbering. No backup or archive of the ordinary run is required.
3. Create from the **same immutable factory image and SHA**, without rebuilding
   between cycles. Repeat the complete story through Presenter, with the user's
   visual control. Presenter invokes the same Demo Control core as CLI.
   Demo Control assigns new release numbers for each reused VDP/Brake/Tire
   profile; the operator never supplies them.

Production remains deferred. Installation, runtime and functional outcomes
require their agreed independent evidence; a simulated UI transition does not
pass E2E. Reuse completed targeted tests rather than repeating unrelated
infrastructure checks between releases. If the audit proves a guest change is
necessary, handle it as a bounded change before establishing the common image
for both cycles, not as an automatic rebuild during this review.

All agenda answers are now recorded. Next perform the promised comprehensive
review of all 78 action/transition rows and 28 gaps against the accepted
decisions, current code, documentation and Cloud API contracts. Report remaining
implementation work, technical unknowns and exact call/result/error mappings;
do not call an unresolved integration gap a working capability. No application,
mockup HTML or live environment change is authorized by this acceptance.

## 3. Delivery sequence and checkpoints

### <a id="decision-review-agenda"></a>Question-and-answer review protocol and agenda

Agreed on 9 September 2026: after each answer is explicitly accepted, record
the exact decision in this project in English, publish the updated agenda in
the conversation with answered/open items, and take the next question. Show
the alternatives and recommendation in the conversation, not only in a
separate question card. A topic with unresolved subquestions remains open.
Technical API/core facts must be investigated, not decided by preference.
Previously accepted architecture boundaries are not reopened by this agenda.
After all decisions, perform one comprehensive pre-implementation audit of
the 78 action/transition rows and 28 gaps before requesting implementation.

| Question | Topic | Review state | Related decisions / gaps |
|---|---|---|---|
| Q01 | Does Create start the controller? | ANSWERED — B: create and start | M02; G02 |
| Q02 | Is initial Platform v1 preparation/publication shown live? | ANSWERED — A: visible before Provision | M02; G02/G04 |
| Q03 | When does CARLA connect, and what is the initial driving mode? | ANSWERED — A: after Create, before Provision; stationary Manual, no automatic Safe Stop | G03; provisioning source guard |
| Q04a | Test-only operational scope and deferred Production presentation | ANSWERED — A: one Test VM; Production visible, disabled and labelled Deferred; CLI production/all retained | M01; G01 |
| Q04b | Any condensed/automatic preparation mode alongside the visible story | ANSWERED — A: explicitly selected Full story and Quick preparation; shared Demo Control; no action on page open | G21; accepted Q01–Q03 |
| Q05 | Factory baseline, empty slots and version/profile presentation | ANSWERED — A: meaning first, exact release secondary, raw placeholder/IDs in Details; empty differs from Unknown | M04; G25 |
| Q06 | Cloud installation/runtime states and acceptable missing evidence | ANSWERED — A: Installed with Not reported runtime is acceptable for the first UI milestone if the audit confirms no supported Cloud source; real runtime/E2E proof retained | M03 partially; G05 |
| Q07a | Shared monitoring and automatic refresh/freshness | ANSWERED — A: shared visible-panel observer; entry/post-action reads; pending 2s backing off to 10s, idle 10s; retain stale last-known values | M03; G12/G14/G24 |
| Q07b | Explicit Cloud log requests and remaining state/progress presentation | ANSWERED — A: list/request/observe/view/download in UI and shared CLI; actual stage/time, measured percentages only | M03; G07/G13 |
| Q08a | Publication while a provisioned vehicle is Offline, within the agreed recipient scope | ANSWERED — A: allow publication with host Cloud access and retained recipient/identity safeguards; separately observe delivery/install | G06/G07/G28 |
| Q08b | Outstanding-update publication controls and unconfirmed supersession/cancellation | ANSWERED — A: one outstanding update per identity; prepare/sign successors allowed; no global lock or hidden queue | M07; G27 |
| Q09a | First service publication/assignment versus subsequent updates | ANSWERED — A: Publish service (SP) then first Deploy to Test (OEM); Publish update for an existing identity assignment | M05; G08/G09 |
| Q09b | Service/Subject ownership, Test binding and team authority | AMENDED 11 September: separate retained Group Subjects for Brake/Tire, current Test only; independent OEM assignments and team-SP publication; Q13 applies to each | G09/G28 |
| Q09c | Repeated service profile releases and completion/readiness criteria | ANSWERED — A: retain identities with monotonic profile releases; Cloud-confirmed expected installed/running version completes the update; function/results separate and mandatory for E2E | G10/G11/G25 |
| Q10a | Backend startup and current Test/run context | ANSWERED — A: prepare/reuse both backends during composed Create or Quick preparation via Demo Control; bind current Test when known; navigation read-only, vehicle deployment separate | G18/G21; Q04b |
| Q10b | Backend dashboards, functional evidence and advisory presentation | ANSWERED — A: overview first (Cloud service state, latest backend result, recorded advisory), compact history/details; native vehicle display remains separate | M08 presentation; G18/G19/G25 |
| Q11 | Offline demonstration, reconnect and independent delivery acknowledgements | ANSWERED — A: standalone episode on installed versions; vehicle-only external fault, local functions/advisory, restore link, independently observe Cloud and delayed product receipt | M08 offline episode; G20 |
| Q12a | Park/Resume scope and retained session | ANSWERED — A: one full-stop Park/Resume; preserve owned disks, Cloud identity, product records and operation state; reuse the same environment without Create/provision/publication; no warm Pause | M06 Park/Resume; G15/G22 |
| Q12b | Interrupted operations and shutdown during an update | ANSWERED — A: prompt reasoned Park refusal for conflicting unfinished/uncertain changes; no queue, forced cancellation or automatic Safe Stop; recover/reconcile before mutation repeats | M06/M07; G16/G22/G27 |
| Q13a | Deprovision/Delete/Retire, owned resources and dedicated Subject lifecycle | ANSWERED — A: Finish demo runs scoped Retire; New cycle completes the same cleanup if needed; preserve Subject/persistent infrastructure, reset owned bindings and recorded temporary settings; Park remains separate | M06; G09/G17/G21 |
| Q13b | Product-history cleanup and cross-run release numbering | ANSWERED — scoped run-data removal without ordinary archives/reports; retain used release numbers/profile bindings; Demo Control automatically assigns releases for CLI and UI, never the operator | M08; G10/G22/G25/G26 |
| Q14 | Repeat demonstration, visual acceptance, audit and final checkpoint | ANSWERED — A: full democtl cycle, scoped Retire, then full visually reviewed UI cycle from the same image SHA; automatic new releases; audit before implementation | G10/G23/G24/G25; P8 |

Q03 implementation evidence: `UnitLifecycle.execute` currently rejects a
selected source for provisioning as well as retirement operations with
`UNIT_LIFECYCLE_REQUIRES_DETACHED_SOURCE`. Connecting during Create therefore
requires a bounded review of the provisioning guard; it is not supported by
merely exposing the existing initial stationary-Manual connection. Do not
remove the shared guard for deprovision/delete as a side effect. This is a
current Demo Control restriction, not evidence of a Cloud requirement.

| Phase | Work package | Observable exit condition | Dependencies |
|---|---|---|---|
| P0 | Agree change package and baseline | Mockup approvals and engineering scope recorded; every open authority/behavior decision has an owner | No live actions |
| P1 | Shared Demo Control contracts and Test scope | Test lifecycle/result/ledger plus backend process/storage/context contract ready | P0; no product algorithm dependency |
| P2 | Cloud observation and publication correctness | Real inventory, package processing/errors, service instances, bounded DMIPS monitoring and freshness have one consistent source | P1 shared result/identity contract |
| P3 | Complete lifecycle and VDP through CLI | One fresh Test run reaches v1 → v2 → v3 with actual Safe Stop transitions; Park/Resume and scoped retirement work | P1, P2; M01–M03, M06–M07 |
| P4 | Correct approved mockup and connect Presenter | The same lifecycle/VDP path works from the accepted composition; operator visually confirms it | Approved M items; P3 |
| P5 | SOTA/product path plus Brake v1; reuse P1 backend lifecycle | Published and assigned Brake service has a real running instance and stores a real braking window in its backend | P2/P3; M05/M08 |
| P6 | Brake v2/v3 and complete advisory chain | Assessment and driver advisory are independently confirmed through their real paths | P5 and corresponding VDP capability profiles |
| P7 | Independent Tire service and offline behavior | Tire result/advisory work without changing Brake; reconnect delivers durable queued records without false acknowledgements | P5 shared integration; P6 for shared advisory contract |
| P8 | Repeatable full demo and final checkpoint | Operator completes the whole agreed story; clean rerun works from the same image SHA; source/docs committed and scoped cleanup completed | P4–P7 |

P2 and P3 establish a complete Platform/VDP milestone before product-service integration. P5 is a real product work package, not merely a UI button: the earlier audit did not establish complete deployable Brake/Tire implementations. No completion date is promised until that bounded runtime/package work is sized.

## 4. Phase details

### P0. Freeze decisions without freezing the mockup as an implementation contract

1. M01–M08 and Q01–Q14 are already accepted, subject to the current amendments above. Subject/package choices are accepted. Use the final re-audit; no design questionnaire remains open. Use UI-STUDIO-026 and its replacement map; do not reopen completed choices.
2. Reuse the audited working tree and distinguish existing uncommitted changes from new work. Do not discard, rebase or commit unrelated changes.
3. Confirm one immutable image/catalog binding and the current run scope. This is a bounded implementation input check, not another full system audit or build.
4. At the start of authorized live work, perform one scoped API/role capability read: tenant API version, OEM and team-SP identity/rights, Test verification-set binding, existing service/Subject ownership. Do not increase rights or create Fleets/Sets automatically.
5. Record the supported SOTA runtime/resources/identity interfaces of the selected factory image. If a required execution or credential capability is absent, report the exact guest change before building or trying successive service bundles.

Output: accepted change list, named work packages and a concrete baseline, with no unreviewed mockup rewrite.

### P1. Fix shared operations once

Affected area: `aosedge-sdv-demo/apps/demo-orchestrator`, its tests and affected executable contracts.

1. Add explicit Test targeting to `demo plan/prepare` and Presenter actions. Remove the requirement for a live Production VM from Test preparation/publication. Keep genuine recipient/ownership protection: a deployment-bundle upload is not a Unit-specific transport simply because CLI says `test`.
2. Bind the run to catalog image identity/SHA, firmware compatibility metadata, Unit UUID/system_uid/Node and Test set. Replace the universal `.31` assumption with catalog-declared support; do not mark an arbitrary image compatible just because it is listed. Cache unchanged manifest facts rather than hashing the image at each action.
   For accepted M02, compose Presenter Create as disk creation followed by VM start. Revise the pre-provision publication contract to permit the compatible unprovisioned controller to remain running; do not make power-off a publication prerequisite or insert a stop/start workaround.
3. Expose the existing initial stationary-Manual connection as a public Demo Control operation immediately after Create and before Provision, per Q03. Retain ordinary `vehicle select` Safe Stop/reset behavior for its distinct operation. Narrow the provisioning restriction that currently requires a detached source so the agreed local connection is preserved, without weakening deprovision/delete safeguards. First connection, reconnect and vehicle switch remain distinct and cannot silently reset a running demonstration.
4. Keep the existing result envelope and writer/journal design. Return safe entity IDs, stage, elapsed time, terminal/pending/uncertain outcome and meaningful errors. Do not create a second workflow database or receipt system.
5. Reopening the UI/CLI resumes observation of a known operation. Reuse exact recorded IDs and completed stages. A recorded READY flag alone does not prove current readiness; one focused read handles reuse. A lost mutation response requires reconciliation, not another mutation.
6. Validate package content at preparation/signing and trust boundaries. Do not repeat extraction/hash/guest diagnosis on navigation or every status call. Retain only checks that protect the requested mutation or verify its actual postcondition.
7. Implement both backend process/start/stop/storage and current-Test context contracts now, including the minimal Tire backend lifecycle surface if absent. Change one-or-two-role context/cleanup validators and handlers/tests together; P3 cannot depend on a backend startup deferred to P5/P7. Product algorithms and full Tire result endpoints remain later increments.
8. Add the shared durable automatic allocator for VDP and services, returning a release handle/version from the selected profile. Keep its reservations/used numbers through Retire; do not require operator version input.

Exit check: deterministic tests for Test-only planning, image mismatch, first-connect versus select, repeat request, preserved Production scope and uncertain-result handling. No VM/Cloud E2E is repeated for every individual edit.

### P2. Make Cloud observations and publication results truthful

1. Build one normalized Cloud Unit read model used by the architecture map, Platform view and team runtime views. Include all reported components, installed/pending identities and versions, errors, subjects/services, instances and node scope.
2. Preserve raw Cloud state separately from the UI label. Read failure means unavailable/last-known, not Offline or absent. Mark local observation time separately from a device/sample timestamp.
3. Keep bundle upload at `POST /deployment-bundles/upload/` with multipart `file`. Return acceptance immediately through the existing asynchronous operation path. Follow the recorded deployment ID through the paginated bundle list, then catalog state. Preserve `build_info` and pending errors. Error bundles must not become successful noOp results.
4. Remove mandatory approval from the Test preparation flow and its upload-recovery dependency. Do not add explicit component send as a fallback. Preserve approval operations only as separate, explicitly requested operations outside this Test-delivery gate.
5. Add monitoring only for the visible monitor: CPU in DMIPS, memory/storage in verified units and sample timestamps separate from read time. Missing remains missing. Audit the tenant response shape once at integration, not on every tab switch.
6. Expanded Q07b logs are deferred. Retain their later contract: list existing requests, explicitly collect, follow every returned job ID, view/download within role/time scope. Opening a card never collects logs. Basic error/uncertainty remains required now.
7. Resolve VDP runtime evidence under Q06: first investigate an existing supported Cloud report/log result that reliably identifies the version and observation time. If none is confirmed, use Not reported; missing Cloud runtime detail alone does not block the first UI milestone. Actual runtime/E2E qualification remains mandatory. Engineer-only `component status test` may qualify the runtime but must not feed the Presenter Cloud model.
8. Implement accepted Q07a: one shared snapshot/read model, one in-flight request per observation key, entry/post-action reads and a bounded visible-panel observer. Use 2 seconds during pending delivery, backing off to 10 seconds; 10 seconds for visible idle inventory; metrics only while their monitor is visible. Hidden views add no polling and navigation does not cancel active work/reconciliation. Preserve stale last-known data on read failure. These are configurable observation intervals, not command delays, device sampling guarantees or completion SLAs.
9. Implement accepted Q08a: separate host publication access from vehicle connectivity and permit a correctly scoped upload while the vehicle is Offline. Preserve publication results separately from observed connectivity and delivery/install state; Offline alone must not manufacture a Pending reason. Retain recipient/identity safeguards and require explicit authorization because upload can affect other eligible verification Units. Observe the actual result after reconnect without automatically republishing or promising immediate completion. If scope cannot be established, return a precise blocker rather than weakening the guard.

Exit check: contract tests for 201→processing→ready/error, pagination, missing/zero values, stale/offline distinction, zero instances, loss of read access and response-loss reconciliation; one scoped live read of actual response shapes at integration time. No invented download percentage or FOTA Running status.

### P3. Finish the full CLI lifecycle and VDP path

1. Implement the M02/Q03 order, under the accepted Test-only scope: select image → create Test working copy/overlay and start with DNS/role initialized → start or reuse simulator/Gateway/native UI → initial stationary Manual connection → explicit Platform Team prepare/sign/upload of fresh v1 → confirm publication → official SDK provisioning of the running, locally connected controller → Cloud Online → Test membership. Do not auto-enable Safe Stop during first connection. Expose publication as the visible chapter, not a hidden side effect of Create. Preserve the decomposed CLI operations; no extra VM stop/start or source detach/reconnect is required just to publish or provision.
2. Preserve a placeholder/factory baseline until an OTA release is actually reported installed. The first operator drive and Safe Stop establish the first transition. Do not manufacture a gate-open observation from the button press alone.
3. Implement Park and Resume using existing primitives. Park preserves identity and disk; Resume starts the same disk and observes current Cloud state without provisioning again. Record/recover which processes belong to the session.
4. Keep deprovision order: detach/stop simulation, retain or restore the running VM when required by the current command, stop CM, observe Cloud Offline, deprovision, then stop VM. Delete removes exact membership and Unit; local retire removes only owned working files. Never re-provision the retired overlay.
5. Define shutdown while an update is in flight using actual core/CM behavior and available evidence. A focused source/log check must close this before relying on Park/Retire. Do not promise atomic cancellation or add a new “kill update” operation.
6. Perform one Test-only CLI run: fresh baseline v1, driving/pending, Safe Stop/installation, then the corresponding transitions to v2 and v3. Independently confirm the actual VDP process for engineering qualification with existing Demo Control diagnostics. Record that separately from the Cloud-only UI evidence.
7. Use the same run for Park/Resume and final retirement checks where compatible. Do not rebuild/reprovision simply to repeat an already passed unchanged stage.

Exit: a reproducible command sequence, known results and scoped cleanup. No ad hoc SSH command sequence outside Demo Control; its existing internal guest adapter may still perform legitimate VM lifecycle operations.

### P4. Apply approved mockup changes, then bind Presenter

1. Change only approved M items. Review the revised mockup before replacing the live Presenter flow. Keep a visible approval record for any newly discovered UX change.
2. Replace timer-derived facts with shared Demo Control operations and P2 read models. Preserve the existing native-session capability boundary; do not expose arbitrary command execution.
3. Map Create/Prepare, source connection, publication, details, logs and session actions explicitly. Keep navigation free of mutation. A one-action Prepare composes the same operations as the CLI, not a separate implementation.
   Implement Q04b's explicit Full story / Quick preparation selection through the same core. Full story keeps the Platform chapter audience-visible before Provision; Quick preparation composes it only after an explicit operator start and displays it as completed. Opening the page starts neither mode. Expose stage/progress without reenacting completed operations.
4. Allow the operator to leave a tab while its operation continues. Show actionable error/stage/elapsed time. Refresh data after actions without replaying them.
5. Visually check a complete Platform path with the operator: placement, readable states, native password dialog, progress, Cloud failure/last-known display, pending/install evidence, Park/Resume and confirmation scope.

Exit: the operator can perform the proven P3 workflow from the intended composition. Brake/Tire panels are not claimed functional until their work packages pass.

### P5. Implement SOTA and backend plumbing with Brake v1

Affected owners: Demo Control/Presenter, `brake-health-service`, `brake-health-cloud`; platform/runtime only if a specific missing capability is demonstrated.

1. Close the complete service contract before uploading: ARM64 OCI/service manifest, layers/entrypoint, execution identity, minimum instances, resource declarations/quotas, VDP/KUKSA access through the accepted credential boundary, networking and backend endpoint. Reuse accepted runtime/SDK/credential mechanisms; do not invent another helper or broaden permissions.
2. Establish the actual deployable Brake v1 runtime and its bounded braking-window output. Foundation code alone is not a deployable service. Register the immutable candidate and its functional profile/release version.
3. Add service preparation, inspection, signing, upload, assignment and observation to Demo Control. Reuse the deployment-bundle/signing machinery where applicable, selecting Brake SP authority for publication and OEM authority for assignment.
4. Apply amended Q09b: use separate retained OEM Group Subjects for Brake and Tire, each containing only its logical service and only current Test system_uid. Create only if necessary and authorized; retain each identity across updates. Preserve the peer Subject and default Subjects. Reconcile partial assignment before a repeat; send no service-version UUID. Package readiness is observed separately, not a local assignment prerequisite. Apply Q13 binding reset/Subject retention to each.
5. Reuse the P1 backend lifecycle/storage/current-Test context in composed Create and Quick preparation. Extend it with real Brake product ingestion/queries and validate durable records. Do not reintroduce the two-role requirement or defer basic Tire backend startup to P7. A healthy backend process alone does not prove product-query readiness.
6. Add backend REST reads to Presenter through the trusted application boundary. SSE announces a change and triggers a REST read; it does not replace persisted records.
7. Prove one chain: published ready service → desired assignment → a real expected instance/version in Cloud → actual braking window → durable backend record. This establishes the common SOTA/backend integration once.

Exit: real Brake v1 on the Test vehicle with inspectable runtime and functional evidence. No fictitious assessment/advisory is produced by the UI.

### P6. Brake v2/v3 and driver advisory

1. Implement/complete the accepted v2 local analysis and v3 advisory behavior, including insufficient-data/unsupported/deferred states. Prepare frozen profile artifacts and monotonically increasing release versions through Demo Control.
2. Apply corresponding VDP profiles through the proven path, then publish the service updates. An existing Subject assignment is not recreated to select each version.
3. Observe service process state separately from functional readiness. A service may be Running while waiting for required VDP capabilities; do not invent Cloud admission rejection for that condition.
4. Connect and prove the whole advisory path: service request → VDP → Gateway validation/status → native telemetry display. Backend receipt and vehicle advisory acknowledgement are separate facts; neither is driver acknowledgement.
5. Validate real event correlation/provenance, expiry/clearing and stale-data behavior according to the existing contracts. Use agreed reproducible stimulus, not “every Safe Stop means inspection advised.”

Exit: a real v1 window, v2 assessment and v3 in-vehicle advisory, each with corresponding backend evidence and stable team ownership.

### P7. Tire and offline behavior

Use accepted Q11's standalone offline chapter after local functionality is
established on the installed versions. New publication is not part of this
chapter; the separately accepted Offline publication capability remains.

1. Locate or implement the accepted independent Tire runtime/backend; the audit found a contract, not a complete implementation. Reuse common orchestration adapters, not Brake product identity, storage or lifecycle.
2. Publish with Tire SP and independently assign its identity with OEM through its own retained Group Subject under amended Q09b. Preserve Brake's separate Subject/bindings and prove real Tire instance, assessment and native advisory while Brake remains unchanged.
3. Use the existing native external-network button/Demo Control command. Keep CARLA, local telemetry and local functions alive while external VM traffic is blocked.
4. Confirm persisted outbound records, bounded retries and durable acknowledgements. After ON, independently observe filter removal, Cloud reconnect, backend delivery and Gateway advisory state. Do not turn reconnect into an instant queue-drain claim.
5. Exercise no-data/stale/unsupported states and one reconnect/retry/deduplication case through focused tests plus the same live demonstration, not a full environment rebuild.

Exit: independent Tire behavior and a truthful offline segment with correlated records and no duplicate functional events.

### P8. One final end-to-end checkpoint and repeat

1. Q14/A: run the agreed complete story through `democtl`, including lifecycle, profile transitions, functional results, Park/Resume and offline/reconnect. Reuse already passed targeted tests; do not rerun unchanged infrastructure checks between every release.
2. Retire the owned session under Q13a/Q13b. Preserve original factory image, approved source, published Cloud releases and release-number continuity. Delete only identified owned working copies/records; no ordinary run archive.
3. Create a fresh overlay from the same image SHA and repeat the complete story through Presenter with the user's visual control. Shared Demo Control automatically assigns new releases for each reused VDP/Brake/Tire profile. New Units must not inherit stale service assignments that bypass first Deploy.
4. If a guest change was proven necessary earlier, integrate the complete agreed set into one clean factory build, then perform this final qualification on that image. Otherwise keep the existing image; no ceremonial rebuild.
5. Update qualification and approved implementation deltas against the contracts already established in P0/P1; then commit/push scoped changes in dependency order. Do not defer the contract cascade to P8. No images, binaries, runtime databases, credentials or bundles enter Git.
6. Perform one final ownership-based housekeeping pass after success. Preserve the current canonical artifact and its manifest. Do not rewrite history or remove unrelated work.

Exit: qualified repeatable Test demo, documented commands and recovery, operator approval, committed source/docs and a clean owned runtime scope.

## 5. Required Cloud call order

Paths are relative to the credential profile's `/api/v11` endpoint. This is the sequence to implement through Demo Control, **not direct browser API access**. Resolve and retain exact IDs. POST acceptance never substitutes for the next required observation.

| Flow | Ordered calls | Observable completion / recovery |
|---|---|---|
| Initial scope, once per bound session | GET `/users/me/` for the required profile → resolve/read Test Unit Set and expected identities → bind current run | Appropriate role/permissions and exact ownership. Missing access or conflicting scope blocks the affected mutation; no automatic permission/Fleet/Set changes. |
| VDP baseline/update publication | Prepare/sign locally → OEM POST `/deployment-bundles/upload/` (`file`) → paginated GET `/deployment-bundles/` matching deploymentId → GET `/components/{C}/versions/` | 201 means accepted. Processing may continue; success requires a usable matching release. Preserve build errors. No batch approve or explicit send in this verification-set path. |
| Provision Test | Reuse the VM started by Create with DNS/role initialized and the Q03 local CARLA/Gateway connection preserved → official provisioning SDK, including POST `/units/provisioning/` and certificate exchange → GET Unit until provisioned/Online → POST `/unit-sets/{Q}/units/` with `system_uids` → read membership | Initial v1 publication precedes this step in the accepted story. No unconditional restart or source detach/reconnect; revise the current provisioning guard before this path is executable. Unit identity and exact Test membership confirmed. If membership fails after provisioning, keep the Unit and report that unfinished step; do not restart provisioning. |
| VDP delivery/install | Read `/units/{U}/` → observe current pending or terminal state → native Safe Stop when required → confirm matching installed | A missed Pending sample is not a blocker. No UI install/restart call. Runtime proof uses the separately agreed Cloud evidence source; otherwise remains Not reported. Timeouts retain pending/error information and do not publish another version. |
| First SOTA release | SP sign/upload deployment bundle → observe exact service identity and package state → resolve that service's retained Group Subject Q → POST `/subjects/{Q}/units/` (`system_uids:[UID]`) only if exact Test binding is absent → POST `/subjects/{Q}/services/` (`service_ids:[S]`) for missing service binding → read bindings → read `/units/{U}/subjects-services/` and `/{S}/` | Package READY is observed, not a local binding prerequisite. Native Cloud may reject association. Brake and Tire have distinct Q values; preserve the peer. Desired association is not installed version/Running. Create only when needed; no blind replay or unintended Unit. |
| Subsequent SOTA release | Verify the existing identity/Subject binding → publish higher release version with the same SP identity → observe service processing → observe Unit instances/version | Do not repeat version-specific assignment: the API accepts service identity, not a version. Verification-set delivery can start after upload. |
| Monitoring/logs | GET Unit/service inventory → monitoring only when requested/visible; list existing logs separately; explicit POST log request → follow all returned request IDs → download completed results | OEM/SP scope retained. A log request is an asynchronous mutation; opening a card is a read. Missing metrics/logs are not zero/healthy. |
| Deprovision/delete | Detach source → stop CM while VM is available → GET Unit Offline → DELETE `/units/{U}/deprovision/` → GET new/Offline → stop VM → remove exact Unit Set membership → DELETE `/units/{U}/` → confirm absence → local retire | Preserve partial outcomes. Do not stop the VM first and then discover that the deprovision command needs it. Do not create a new identity to recover an uncertain deletion. |

Subject bindings and backend cleanup must be reconciled during final retirement under the approved ownership policy. Do not delete a shared Subject or product dataset merely because its name resembles this demo.

The verification-set behavior is confirmed by the current [Unit Set description][verification-doc] and [service update documentation][service-doc], re-read on 9 September 2026. Exact request/response shapes are from the audited [public OpenAPI 6.1.53][api]; the tenant capability check in P0 remains required before implementation relies on its deployed feature set.

## 6. CLI surface: reuse first, add only missing operations

Names in the **Proposed** rows are a review contract, not available commands or instructions to run them now. Final flags/result schemas are recorded in the existing Demo Control design before implementation. These are entry points into the shared core, not separate helper programs.

| Status | Interface | Purpose / limits |
|---|---|---|
| Existing; retain | `image list`, `environment create --image <I> --target test`, `vm start/stop test`, `unit provision/deprovision/delete test`, `environment retire` | Existing primitives; fix scope/ordering/results only where identified. `environment retire` is local cleanup, not a hidden Cloud deletion command. |
| Existing; retain | `component prepare <V> --profile <P>`, `inspect`, `unpack`, `verify`, `sign`, `upload`, `cloud-status` | Keep version/profile semantics. Improve upload/result handling; do not add another publication wrapper. Guest `component status/logs` remain engineer-only observations. |
| Existing; extend | `demo plan --image <I> --target test`, `demo prepare --image <I> --target test` | Add explicit target to current plan/prepare; share one stage list with the decomposed workflow; remove mandatory approval. |
| Existing core; expose | `vehicle initialize test` | Q03: first stationary-Manual connection after Create, before Provision, without automatic Safe Stop. Guard it as initial connection, not an arbitrary reset. Ordinary `vehicle select` stays distinct. |
| Declared; implement | `environment park`, `environment resume` | Preserve identity/software/disk and resume the same run, using stored target/current-vehicle scope. |
| Proposed | `unit cloud-status test`, `unit monitoring test` | Complete Cloud inventory and separate metrics. General local `status` must not acquire an expensive full monitoring scan. |
| Implemented CLI; service live proof pending | `component prepare --profile <P>`; `service prepare <team> --profile <P>` | Operator form allocates automatically and returns release handle/version; sign/upload consume that returned handle. Existing explicit-version component form stays engineering-only. |
| Proposed | `demo retire` | Shared full Finish/New-cycle cleanup; composes Cloud, backend and local primitives. Not an alias for local-only environment retire. |
| Proposed; later phase | `unit logs list/request/show/download` with explicit Unit/node/time/request selectors | Cloud-only asynchronous logs. Separate the mutation verb from reads. No implicit request when opening Logs. |
| Implemented CLI; live proof pending | `service list/status/inspect`, `service prepare <team> --profile <P>`, `service sign/upload/cloud-status <handle>` | Distinct catalog UUID, functional profile and prepared-release handle; recorded SP binding. One upload, explicit observation, no hidden assignment/approval. |
| Implemented CLI; live proof recorded in latest checkpoint | `service assign <catalog-service-UUID> --target test` | Separate retained OEM Group Subjects for Brake/Tire, current Test only; native `service_ids`; independent readiness, peer preservation and explicit uncertainty. |
| Proposed | `service logs …` | Logs remain a separate explicit operation. |
| Proposed | `backend start/stop/status <team>`, `backend records <team> --target test` | Own backend lifecycle, persistent context and functional observations, shared by CLI and UI. Product-data cleanup requires an explicit scoped operation under M08, not a side effect of a read. |
| Existing; retain | `simulation start/stop`, `vehicle select test`, `vehicle connectivity off/on/status --target test`, workspace/native layout operations | Preserve accepted native behavior. Driving modes stay in the existing native control path; no Cloud driving API is introduced. |

## 7. Verification cadence and stop conditions

| When | Minimum relevant evidence | Do not repeat unnecessarily |
|---|---|---|
| A code/contract change | Its deterministic unit/contract tests; explicit error/result mapping | Full VM rebuild, all tenant inventory, complete E2E per field or per test |
| First connection to a new API shape/authority | One bounded real read or one authorized mutation with post-read, using the exact target | SDK/credential discovery before every request; broad role resets |
| P3, P5, P6, P7 milestone | One meaningful end-to-end transition through Demo Control; preserve the result and diagnose only a failed boundary | New release versions simply to “try again”; repeated already-passed lifecycle stages |
| P4/P8 visual review | Operator sees the real sequence, readable states and resulting behavior | Formal whole-system qualification on every visual adjustment |
| Final checkpoint | Relevant cumulative tests, full agreed story, fresh-overlay repeat and documentation/source verification | Unrelated historical security/platform tests or image builds without a guest change |

Existing mandatory acceptance/security obligations still apply at their relevant boundary and final checkpoint. This plan neither removes them silently nor expands them into repeated full audits. Checks cancelled by the user, such as proving old identity rejection after deprovision, do not return through this plan.

Stop and return a specific decision only when an affected boundary remains genuinely unresolved: tenant capability absent, unauthorized extra recipient, missing service runtime interface, undefined mockup change, destructive scope unclear or mutation outcome uncertain. Preserve useful progress; do not restart the entire workflow or repair unknown state with another upload.

Every live milestone needs its concrete action/recipient/version/deletion scope authorized before execution. Neither this planning request nor an accepted visual change grants blanket permission for Cloud publication or deletion.

## 8. Audit coverage and ownership

| Audit issue | Owning phase / approval |
|---|---|
| G01 Test-only scope | P1/P3/P5; M01 |
| G02 Create/image conflict | P1/P3; M02 |
| G03 Initial connection | P1/P3; accepted Q03, related M02; implementation/qualification pending |
| G04 Approval and recovery | P2/P3 |
| G05 FOTA runtime/gate evidence | P2/P3/P4; M03 |
| G06 Offline publication guard | P2/P7; accepted Q08a; implementation/verification pending |
| G07 Upload errors/results | P2; M03 |
| G08 SOTA tooling/artifacts | P5/P6/P7 |
| G09 Subject/version semantics | P5/P6; M05 |
| G10 Repeat SOTA versions | P5/P8 |
| G11 Instances/dependency | P5/P6/P7 |
| G12 Full Cloud dashboard | P2/P4 |
| G13 Cloud logs | Later explicit diagnostics scope; basic errors/uncertainty in P2 |
| G14 Freshness | P2/P4; M03 |
| G15 Park/Resume | P3/P4; M06 |
| G16 Shutdown order | P3; M06/M07 |
| G17 Fresh overlay | P3/P8; M06 |
| G18 Backend integration | P1 lifecycle/context/contracts; P5/P7 product and dashboard integration |
| G19 Functional proof | P5/P6/P7; M08 |
| G20 Offline/advisory delivery | P6/P7; M08 |
| G21 UI API surface | P1/P4/P5 |
| G22 Recovery | P1/P2/P3 |
| G23 Documentation drift | P0 and each affected phase; final P8 reconciliation |
| G24 Timing/progress | P1/P2/P4 |
| G25 Identity/provenance | P1/P2/P5/P8; M04 |
| G26 Data retention | P5/P8; M08 |
| G27 Supersession/cancellation | P2/P3; M07 |
| G28 Tenant/roles | P0/P2/P5 |

Implementation ownership follows existing repositories: Demo Control/Presenter and shared contracts in `aosedge-sdv-demo`; native control/source behavior in `carla-ego-runtime`; Brake runtime/backend in their respective repositories. Locate and confirm the Tire repository before creating another one. Changes to immutable guest content belong in `aos-vehicle-platform`, only after a demonstrated need and an approved work package.

[audit]: ../../research/demo-studio-action-audit.md
[interaction]: ../../demo/mockups/aosedge-demo-interaction-specification.md
[control]: ../../architecture/demo-control.md
[doc-policy]: ../../governance/documentation-and-requirements-management.md
[verification-doc]: https://docs.aosedge.tech/docs/quick-start/create-unit-set
[service-doc]: https://docs.aosedge.tech/docs/how-to/updates-and-campaigns/update-service
[api]: https://api.aoscloud.io/api/v11/openapi.json
