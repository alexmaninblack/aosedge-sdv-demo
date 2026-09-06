<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Control VDP Family Checkpoint

- Status: VDP 6.0.0 ACTIVE/23-path READY on Test with temporary SM demo-5s; Cloud installed and pending=null; native Stop/Start retry defect remains
- Version: 0.12
- Prepared: 2026-09-06
- Owner: Demo Solution Team
- Design: [Demo Control](../architecture/demo-control.md)
- Contracts: [VDP Compatibility](../../contracts/vdp-compatibility-profile/README.md)
  and [Typed QM Advisory](../../contracts/qm-advisory-profile/qm-advisory-profile.v1.json)

## Scope and source boundary

Subsequent operator decision: keep mTLS deferred; proceed with installation,
startup and the 7/15/23 telemetry sequence only. Full v3 advisory remains
unimplemented/unqualified and is not a gate for this narrowed experiment.
Gateway continues to reject all Set requests. No credential or ACL is widened.

The operator authorized Safe Stop correction and a Test-only .28 / VDP
1.0.16 -> 2.0.0 -> 3.0.0 sequence, with all component manipulations through
Demo Control. The continuation below demonstrates the narrowed telemetry
sequence with a temporary Test-only schema correction, not an unchanged .28
Factory qualification or complete v3 advisory conformance.

Source checkouts at entry: Solution main `fe35641917033c83e778f80c4402941379b08941`
with existing uncommitted orchestrator work; Gateway main
`4f6da4c3c82448e98f12c55e7c6f728a50ee7f90` with existing controller integration;
working VDP packaging source `0a2c824` on retained `codex/ltvp-finalize-27`;
Factory .28 source `e0a0d101a58a9aaec5123ff9eda4e0459f5db62d`.
Changes in this increment are uncommitted Gateway Controller/test/documentation
and Solution component CLI/core/tests/documentation. Existing dirty work is
preserved; no Platform/Factory source was changed. The publication continuation
below records the subsequently authorized Cloud mutations.

## Safe Stop evidence

The old Controller's CARLA Vehicle proxy retained its last full-brake command
while Traffic Manager changed the actor via independent batched control.
LibCarla `Vehicle::ApplyControl` suppresses equal commands when sticky control
is enabled. The Controller now sets `sticky_control=false` on the owned ego
blueprint before spawn, requiring that attribute explicitly.

The expired prior session was stopped with `democtl simulation stop`, honestly
reporting physical stop NOT_OBSERVED because Controller had already exited.
`democtl simulation start` launched the corrected source without image build.
The existing native Keyboard Control buttons were used for Autopilot and
Safe Stop; no second tick owner, traffic-light override or actuator bypass was
introduced.

Run `29f7fea0-70fa-432a-b050-6388340a4893`, actor 25:

| Observation | Completed frame | Mode | Speed km/h | Brake |
| --- | --- | --- | --- | --- |
| Before operator stop | 2271 | AUTOPILOT | 19.4198 | 0.0 |
| After operator stop | 2962 | SAFE_STOP | 0.0 | 1.0 |
| After Test attachment/reset, settled | 8495 | SAFE_STOP | 0.0 | 1.0 |

These are fresh Controller observations returned by `democtl status`.
The command/control log records operator stop at `2026-09-05T15:28:22.317Z`
and applied Safe Stop at `15:28:22.364Z`. The table is not a measurement of
braking distance or latency; observation intervals differ.

`democtl vehicle select test` completed physical Safe Stop, blocked both paths,
reset once and connected Test. Subsequent `status test --guest` showed advancing
server-verified VISS frames, VDP active, reported data READY, NRestarts=0, and
IAM/SM/CM active with NRestarts=0. Production's source remained BLOCKED and its
provider inactive. This is not an independent KUKSA consumer or FOTA update proof.

A second Autopilot activation after scene reset encountered a red traffic light:
read-only CARLA frame 19803 confirmed `sticky_control=false`, throttle 0,
brake 1, `is_at_traffic_light=true`, light Red. It is not a second moving-stop
qualification. The operator-mode request was returned to Safe Stop without
changing traffic-light state.

## Component command evidence

Executed from `apps/demo-orchestrator`, using `democtl` only:

```text
democtl component list
democtl component inspect 1.0.16
democtl component unpack 1.0.16
```

The catalog retains signed 1.0.15 and 1.0.16. Inspected 1.0.16 is 6,612,398
bytes, SHA-256
`b36e3064166739c98ec028fc75980bf4ea937d531a7e7a7889e11283dd1d7d9c`.
Its full/gzip payload SHA-256 is
`e30f260d819201064a3659f3c242f97126d03da2eb3ccb868a68e4d5765d6cc7`.
Outer, component, provider and capability versions agree; seven read paths,
zero advisory endpoints and explicit runtime binding are present. Signature
presence was observed; cryptographic verification was NOT_PERFORMED.

Unpack created 247 non-executable, owner-only inspection files at
`$DEMO_ARTIFACT_ROOT/aosedge-sdv-demo/components/vehicle-data-provider/1.0.16/unpacked`.
Original bundles and images are unchanged; no backup or cleanup occurred.

## Original analysis before the scope amendment

| Boundary | Actual implementation | Required work |
| --- | --- | --- |
| Component package | Working full/gzip and runtime-binding path explicitly includes only 1.0.14/15/16; 2.0.0/3.0.0 still select old media/layout | Port working packaging to real family releases; pin sources and validate coherent inner/outer metadata |
| Local source configuration | Demo Control and VDP's TEST_ONLY reader use `pathSet=VDP_V1` | Reconcile family source binding explicitly; do not mislabel a wider release as VDP_V1 |
| KUKSA Provider authority | .28 source has fixed provide scope for all 23 telemetry paths and both advisory statuses, plus read scope for both requests | Retain least privilege; source scope is not a live consumer proof |
| VDP v3 runtime | `advisory_enabled` is populated; tested AdvisoryPolicy is not wired into the running KUKSA/VISS bridge | Implement real target subscription, validation/forwarding and correlated GatewayStatus return |
| Gateway advisory | HandleSet currently rejects every Set | Implement exact typed handler and authoritative state machine; no arbitrary/motion writes |
| Gateway caller identity | Local server-TLS mode returns the same Development role for every client | Resolve write authentication before enabling the handler |

The last row is a real design gate. D4-008 requires the Engineering Dashboard
to remain read-only and only the authorized provider to write. The earlier
local amendment deliberately deferred client mTLS, so the active mode cannot
distinguish those callers. Opening the two paths to all Development clients
would violate the contract even though motion commands remained blocked.

Resolution proposed before the operator amendment (NOT authorized for this run): enable the already designed strict
VDP/Gateway client-authentication roles for the advisory phase, including the
existing onboarding and credentials boundary, with separate read-only dashboard
identity. Do not invent a shared token, trust a caller-supplied role, issue
placeholder certificates or silently undo the previous deferral. Scope and
credential provisioning must be agreed before live activation of that profile.

The operator subsequently retained the server-TLS profile and deferred advisory.
The table's advisory implementation work is therefore deferred, not a gate for
the narrowed telemetry experiment. The legacy `VDP_V1` binding label is only a
local source-identity field, not a read ACL; release subscription paths remain
explicit. Publication and activation results follow below.

## Tests

- Demo Control: 145 tests passed, including eight new component tests.
- Targeted Gateway M6 tests: 28 passed, including required blueprint attributes
  and the independent Traffic Manager/ApplyControl-cache regression.
- Full Gateway launcher tests: 53 passed; orchestration control tests: 9 passed.
- Final `democtl simulation stop`: COMPLETED, physicalStop=CONFIRMED,
  Current Vehicle=null. Repeated stop: COMPLETED, noOp=true.
- Final ordinary status: simulation STOPPED, both existing VMs RUNNING.
  No final Cloud Online claim is inferred from that local-only read.

The simulator was stopped to finish this bounded proof while the advisory
design gate remains open. Both VM overlays and their Cloud identities remain
available for continuation. Compact run logs remain under the current-run
source directory; no transient credential or permission exception was created.

## Publication continuation — telemetry-only scope

Every preparation, signing, verification, upload, approval and guest component
read used `democtl` from `apps/demo-orchestrator`. There was no raw signer,
multipart upload, SSH component manipulation or standalone workflow script.
The new internal adapters are the shared CLI/API application implementation.
Signature verification checks RS256 against the configured OEM certificate,
SHA3-512/size for both signed members, matching configs, and coherent payload
metadata. The installed official Aos Signer performs signing.

Both candidates reuse the exact ARM64 dependency files from qualified 1.0.16,
and common runtime files are matched byte-for-byte to Platform source commit
`0a2c8249ec780e822bff90f29f9d3d5ba5dd7feb`. Their release-specific source and
manifests come from that same commit. Preparation produces deterministic
full/gzip payloads with explicit runtime bindings and no Builder/download step.
The v3 manifest is the target capability declaration, **not proof of functional
advisory**; provenance and the qualification scope explicitly defer advisory.

| Release | Read paths | Signed bundle SHA-256 | Deployment bundle |
| --- | --- | --- | --- |
| 2.0.0 | 15 | `8cea21f1280961f997fe38c724b346a1c4ee2cb246d7da660849afac87599450` | `e5341eb5-29f1-4af8-92b7-88f4225a2be9` |
| 3.0.0 | 23 | `451965e1d03259a7edf66a4c742125c290f5efbfb2089530572395da2a1901fd` | `1bb90217-14c2-4c2b-ade9-1b4e76540343` |

The exact v2 verification batch `17a4f529-96b1-42b3-9835-2b906cc19211`
and v3 verification batch `fe8ea8a9-a966-4074-902a-2b69dc71a9f3` were approved
for arm64, independently of upload. API response and post-read confirmed Valid.
No fleet-validation approval or Production promotion was performed. The
existing run journal owns exact intent, attempt-started markers, digests,
deployment IDs, confirmation state and the Production guard.

### Observed run and limits

Run `a3524515-24a9-4180-8db7-87ec0ade3890` was started through
`democtl simulation start`; `vehicle select test` confirmed Safe Stop and
advancing VISS frames. This continuation reuses the existing .28 Test Unit
`4279840f-d81f-410b-abf3-376e69719fc2`, not a fresh reprovisioning cycle.
Production Unit `766f8fcc-e733-4d1c-a928-fb25176a2f4f` retained factory 0.0.0,
Online state and unchanged memberships in every publication guard.

- Baseline: active slot a, actual process config matches 1.0.16, seven paths,
  provider reports READY/LIVE/NONE, NRestarts=0.
- v2: active slot a, actual process config matches 2.0.0, fifteen paths,
  capability digest `6abda9b8771d01fa5fe2ce4280cf164973c4944739c732d0326134e4cf43e629`,
  provider reports READY/LIVE/NONE, NRestarts=0, Result=success.
  Offline self-test passed at 2026-09-05 17:06:49 UTC; CM reported
  installed/error=none at 17:06:50 UTC. No manual activation or retry occurred.
- v3: uploaded/approved; offline self-test passed and SM attempted actual starts.
  Runtime initialization failed with `KUKSA publication is unavailable`.
  CM reported component `installed` while the runtime instance was `failed`;
  Cloud retained installed_component=2.0.0 and pending_component=3.0.0 with
  pending_component_status=installed. This is **not a running v3**.

The v2 transition included a real gap with no active provider. Approval was
16:59:05 UTC; v2 became active at 17:06:50 UTC. Logs include a failed component
status publication (`not found`, database.cpp:669) and, in the next transition,
CM `not found` at instancemanager.cpp:198. The runtime source has a fixed
480-second Safe Stop wait, but timing similarity alone does **not** prove this
is the cause of the gap. No timeout or SM behavior was changed. This is not a
seamless or latency-qualified update claim.

`component status` reports active manifest path count and the provider's fresh,
complete-frame readiness after KUKSA publication. An independent KUKSA consumer
read has not been performed. Full v3 advisory, fresh-Test initialization,
reboot/restart qualification and a new SELinux audit are not completed by this
continuation. Existing Provider `pthread_getschedparam failed: 1` warnings were
observed without a restart; their absence is not claimed.

`component logs <role>` reads bounded per-service tails, decodes journalctl's
binary-message arrays and projects redacted service events. Repeated READY
events are aggregated; no raw Cloud message bodies or credential values are
returned. Initial log-reader format/filter failures were harness defects, not
evidence that VM logs were absent; no artifact was rebuilt to correct them.

Local checks: 155 full orchestrator tests passed after the final diagnostics and
publication guard; 18 component tests passed, including binary-log decoding,
secret redaction, deterministic archive output, no blind upload retry,
unconfirmed approval rejection and Production/non-target guards. Documentation
gate passed for 149 Markdown documents, 658 identifiers and 38 Mermaid diagrams.
Source remains uncommitted with pre-existing changes preserved. No cleanup,
backup, Factory image rebuild, reprovisioning or permission expansion occurred.

### Confirmed v3 platform prerequisite and continuation boundary

`democtl component diagnose test` read the exact schema loaded by the deployed
KUKSA service, `/usr/share/vss/vss.json`. All fifteen v1/v2 leaves are present;
all eight v3 ChaosWheel leaves are absent:

- `Vehicle.CarlaSimulation.ChaosWheel.Row1.Left.LongitudinalSlip`
- `Vehicle.CarlaSimulation.ChaosWheel.Row1.Right.LongitudinalSlip`
- `Vehicle.CarlaSimulation.ChaosWheel.Row2.Left.LongitudinalSlip`
- `Vehicle.CarlaSimulation.ChaosWheel.Row2.Right.LongitudinalSlip`
- `Vehicle.CarlaSimulation.ChaosWheel.Row1.Left.LateralSlipAngle`
- `Vehicle.CarlaSimulation.ChaosWheel.Row1.Right.LateralSlipAngle`
- `Vehicle.CarlaSimulation.ChaosWheel.Row2.Left.LateralSlipAngle`
- `Vehicle.CarlaSimulation.ChaosWheel.Row2.Right.LateralSlipAngle`

This missing data-model prerequisite is independently observed, not inferred
from the generic publication error alone. It should have been checked before
publication. Demo Control now performs this exact schema/manifest compatibility
check before an upload attempt and rejects a missing required path before
journaling a mutation. The test suite covers that fail-closed boundary.

The required continuation was an explicit Platform/KUKSA schema correction for
these existing contract leaves, **not a new VDP version, broader JWT, Gateway
Set permission, mTLS restoration or a signing change**. The operator subsequently
approved the temporary Test-only schema proof recorded below; it was not
silently included in the initial frozen-.28 telemetry scope.

SM autonomously repeated failing v3 starts about every two seconds. These were
not repeated `democtl upload` or manual restarts; systemd `NRestarts=0` alone
does not prove stability when SM starts separate jobs. To contain the run,
`democtl simulation stop` confirmed physical Safe Stop and detach and stopped
Controller/Gateway/UI. Its first CARLA shutdown wait returned
`SIMULATION_STOP_TIMEOUT:simulatorCommand`; reconciliation is recorded below.
`democtl vm stop test` was requested to stop the failing loop while retaining
the overlay, image, Unit/Node identity and evidence. Production was not stopped
or changed. No candidate, Cloud object or historical evidence was deleted.

Final containment, 2026-09-05 17:33 UTC: Test shutdown completed in 3.91 seconds;
`democtl status` confirmed Test STOPPED, Production RUNNING (PID 40993), and
Current Vehicle=null. The exact existing simulation-stop operation
`970ca671-cfc2-420b-9695-b61af86c9da0` remains DETACHED/physicalStop=CONFIRMED.
One explicit reconciliation of that operation again reached the CARLA shutdown
timeout. Controller/Gateway/UI are stopped, but the owned CARLA process has not
completed normal exit; simulation STOPPED is **not** claimed. No SIGKILL was used.
Do not start another simulation over this pending stop operation. Source/evidence
and both immutable inputs/overlays are preserved. No final post-shutdown Cloud
Offline observation is implied by the local Test STOPPED result.

### Authorized temporary schema proof — 2026-09-05 23:03–23:08 UTC

The operator accepted continuing with a temporary Test-only schema correction.
All live operations were issued using `.venv/bin/democtl` from
`apps/demo-orchestrator`; there was no raw SSH mutation, standalone helper,
new bundle, upload, approval, reprovisioning, Factory build or Platform source
change. The old simulation-stop operation reconciled to STOPPED at
22:54:14 UTC. `vm start test` completed with SSH/DNS=true in 24.97 seconds.

The new shared-core `component schema-apply test` generated a supplemented
public schema and added a service-specific read-only bind using systemd's
[documented BindReadOnlyPaths semantics](https://github.com/systemd/systemd/blob/v256/man/systemd.exec.xml).
The existing `--vss` argument continues to load the same path, consistent with
the [KUKSA custom VSS documentation](https://github.com/eclipse-kuksa/kuksa-databroker/blob/main/doc/user_guide.md).
Only eight sensor leaves were appended. All fifteen existing leaves and all
other schema data were preserved. The release source uses finite floating-point
values for the eight leaves; lateral angles are degrees and longitudinal slip
is dimensionless, as recorded in the accepted VISS telemetry contract.

| Input/observation | Result |
| --- | --- |
| Unchanged base `/usr/share/vss/vss.json` SHA-256 | `3285d35ca5a108f65cd77f348a28cd0cbffd0fa27b9b4ab0e0db7722d3316ef0` |
| Temporary schema SHA-256 | `357e5af4e1ee6fa881c6a0ddf55e87320bedc966dd4faf7c70e14e57ba0fa73d` |
| KUKSA restart | One, 23:03:26 UTC; PID 1272, active/success |
| Effective service namespace | All 23 required leaves present, none missing |
| Repeated schema application | `noOp=true`; no second restart |
| VDP | 3.0.0, active slot `a`, actual process configuration matches slot |
| VDP start | 23:05:38 UTC; PID 1414, Result=success, ExecMainStatus=0 |
| Provider telemetry | `VDP data READY; source LIVE; reason NONE`, 23-path manifest |
| Stability read | Same PID/start time; READY and NRestarts=0 at the second read; fresh source at 23:08:09 UTC |
| Security observation | SELinux Enforcing; current-boot kernel journal read succeeded, five records, zero observed AVC denials |

`simulation start` created run `2df52fe1-b0b2-43f8-90c3-74b94889061d`.
`vehicle select test` completed exclusive attachment; Production's gate stayed
BLOCKED. The source continued producing frames (4136→4138 at the final read).
CARLA remained SAFE_STOP, speed 0, brake 1. No new Autopilot-to-Safe-Stop motion
test was performed in this continuation; the prior live proof above remains
the evidence for that fix.

The already-installed candidate started under SM management after Test was
attached to its live source. No direct provider start or manual SM retry was
issued. Redacted logs show SM starting to monitor the instance at 23:05:38 UTC
and eighty recent provider READY events. SM, CM and provider all report active,
success and NRestarts=0. The retained `last-failure.json` timestamp is from the
earlier failed experiment, not a new failure in this successful start.

Cloud API readback confirms Test Unit `4279840f-d81f-410b-abf3-376e69719fc2`
Online, installed VDP **3.0.0**, `pending_component=null`. Existing deployment
`1bb90217-14c2-4c2b-ade9-1b4e76540343` remains done and its verification batch
remains Valid/approved. Production Unit
`766f8fcc-e733-4d1c-a928-fb25176a2f4f` remains Online with factory VDP 0.0.0,
no pending component and its existing memberships unchanged. No Cloud writes
were issued during this continuation.

The narrowed hypothesis is proven: providing the missing schema leaves allows
the unchanged VDP 3.0.0 to start and report successful complete-frame KUKSA
publication. READY is still provider-reported evidence, not an independent
KUKSA consumer read. Full v3 advisory, mTLS, a new clean Factory build and
restart/reboot qualification of such a build remain outside this result.

Transient state is **deliberately retained** on Test for inspection:

- `/run/democtl-vss/vss.json` (public schema, mode 0644, exact base label
  `system_u:object_r:usr_t:s0` copied; no policy change).
- `/run/systemd/system/kuksa-databroker.service.d/90-democtl-vss.conf`
  (owned drop-in; only BindReadOnlyPaths, no ExecStart or credential changes).

These are lost on Test reboot. To explicitly remove them, first detach using
`democtl simulation stop`, then `democtl component schema-remove test`.
Removal restores stock KUKSA and deletes only the two owned temporary files;
v3 then lacks its schema prerequisite again. Automatic failure restoration,
explicit removal, ownership conflicts, schema preservation, Test-only selectors
and no-op repeat are covered by fixtures; live removal/reboot was intentionally
not performed so the successful state remains available.

Validation: 161 orchestrator tests passed (including 24 component tests); local
Unix-socket fixture tests require normal socket access and passed when run with
that access. No new compiled artifact, backup or disk cleanup was needed.
Source remains uncommitted on the entry revisions, with existing dirty work
preserved. No experimental images, caches, historical evidence or keys were
deleted.

## Factory .29 permanent schema build — 2026-09-06

The operator authorized a new Factory image and explicitly required repeating
**all three** VDP telemetry versions, not only 3.0.0. The fixed artifacts remain
VDP 1.0.16, 2.0.0 and 3.0.0. No component was rebuilt, repackaged, signed,
uploaded or approved during this build continuation.

Platform branch `codex/factory-29-vss`, committed revision
`45dfa22fce9b0b0fa636f1ca2dce876482ca5f68`, tree
`716a104f47a399b53d081a53e441c7e225d3436b`, is based on exact .28 revision
`e0a0d101a58a9aaec5123ff9eda4e0459f5db62d`. The functional change is a VSS
recipe post-install function that composes the eight public v3 sensor leaves
into packaged `/usr/share/vss/vss.json`. It preserves all existing data and
validates the complete 7/15/23 release path sets and types. This is build-time
recipe code, not another operator helper or runtime mount.

SM/CM source code, KUKSA executable, certificates, ACLs, SELinux policy and VDP
payloads are unchanged. The release identity becomes .29. SPDX-only headers
were added to three inherited qualification/backport files to satisfy the
existing repository quality gate; their C++ patch hunks are unchanged.
The initial BitBake parse rejected a Python append to upstream's shell
`do_install`. It was corrected to a Python post-function before any image task
ran, and the correct recipe form is covered by regression. No failing image
was exported or used as a VM.

Source validation passed: 132 Platform unit tests, including six VSS-specific
tests and 21 R6.1 layer tests; layer validator; quality gate (189 files);
`git diff --check`. Offline package build passed 1422 tasks (1403 reused),
including package QA. Image build passed 7547 tasks (7489 reused), including
image QA. Existing downloads/sstate were reused; this was not a from-scratch
cache purge. New filesystem outputs were assembled with the existing pinned
Rouge disk description.

One immutable manufacturing image serves both roles; Test and Production use
separate overlays and identities, not different role-specific builds:

- Catalog selector: `6.1.1-maninblack.29/main-qemuarm64`.
- Artifact directory: `$DEMO_ARTIFACT_ROOT/aosedge-sdv-demo/factory-images/6.1.1-maninblack.29`.
- Raw disk: `main-qemuarm64.img`, 6997147648 bytes, six GPT partitions, mode 0444.
- Disk SHA-256: `fb6f77cb280b0836ba0979373260af50a9b30cdb1bf9b3365fb6b2f775b2cf6a`.
- External `manifest.json` state: `BUILT_NOT_LIVE_QUALIFIED`.
- Packaged VSS SHA-256: `357e5af4e1ee6fa881c6a0ddf55e87320bedc966dd4faf7c70e14e57ba0fa73d`, exactly the successful transient schema.

Host transfer SHA matched. Packaged `os-release` reports .29. The checked
provisioning, private credential and active-component state paths and
`/run/democtl-vss` are absent from the new rootfs. SM/CM executable digests are
recorded in the external manifest; no whole-file binary identity to .28 is
claimed. Builder was stopped cleanly after export. `democtl image list` lists
.29 with metadata available and no catalog issues; that inventory is not
runtime qualification.

### Live matrix and exact continuation boundary

| Required .29 observation | State |
| --- | --- |
| Fresh empty-slot VM, SSH/DNS, provision and Cloud Online | Not run |
| VDP 1.0.16 actual process and complete seven-path publication | Not run |
| VDP 2.0.0 actual process and complete fifteen-path publication | Not run |
| VDP 3.0.0 actual process and complete twenty-three-path publication | Not run |
| CARLA/Gateway exclusive attachment and Autopilot-to-Safe-Stop | Not run on .29 |
| Restart/reboot, persistent schema, no temporary override | Not run |

Old Test .28 remains running with its authorized transient proof; its Unit,
disk, role membership and simulation were not changed. Production and fleet
validation are untouched. No .29 environment has been created yet.

Read-only API examination found both 2.0.0 and 3.0.0 verification batches
already approved. The official `units/{id}/available-components/` endpoint
returns an array; current Test listed only historical 1.0.0, not the qualified
1.0.16 or 2.0.0. Therefore this is not evidence that a forced-send request can
select the older qualified versions. Demo Control's `component cloud-status`
now reports that filtered array directly, with a regression for the actual
non-paginated response shape.

The proposed sequencing needs operator agreement before Cloud changes:
temporarily unapprove only verification batches
`17a4f529-96b1-42b3-9835-2b906cc19211` (2.0.0) and
`fe8ea8a9-a966-4074-902a-2b69dc71a9f3` (3.0.0), then restore approvals in order
after observing each version. Stop and remove only old Test .28's membership
from Test Vehicles, preserving its provisioned Unit and disk, to permit a fresh
.29 Test in that exclusive role set. No unapproval or membership removal has
been performed. Cloud's actual selection after approval changes still requires
readback; this sequence is a proposed live test, not a proven result.

All subsequent demo VM, Cloud and component operations must use Demo Control.
The preserved .28 is not to be retired before .29 acceptance. No new Production
deployment, extra Unit Set, fleet-validation change, credential expansion or
new VDP version is authorized by this checkpoint. Full v3 advisory and mTLS
remain deferred. Source commits and build artifacts are local; nothing was
pushed by this continuation.

## Authorized .29 live continuation — 2026-09-06

The operator approved temporarily removing 2.0.0/3.0.0 verification approvals
and stopping/unassigning old Test .28 while preserving its provisioned Unit
and disk. All VM, membership, approval, component and simulation operations
below used Demo Control. Production and fleet validation were not changed.

`component unapprove 3.0.0` and `component unapprove 2.0.0` each returned HTTP
200, approved=false, Cloud state Invalid and Production unchanged. Invalid
here is the deliberate approval state, not a package parsing failure.
`simulation stop` confirmed physical Safe Stop and detach. Controller/Gateway/UI
exited; CARLA exceeded two 30-second waits, then exited. Reconciliation of the
same operation confirmed STOPPED. No SIGKILL was issued. `vm stop test` took
3.8 seconds; `unit unassign test` took 10.43 seconds and preserved old Unit
`4279840f-d81f-410b-abf3-376e69719fc2`, its provisioned state, other memberships
and disk. Its former `/run` schema override does not survive shutdown.

Fresh qualification uses `$WORKSPACE_ROOT/aosedge-sdv-demo-qual-29.l2uRZv`:
the same CLI source, existing Python environment and PYTHONPATH from its
`apps/demo-orchestrator` directory. No old journal or credentials were copied.
`environment create --image 6.1.1-maninblack.29/main-qemuarm64 --target test`
created a fresh factory copy and overlay; existing pinned QEMU firmware was
copied separately. No image or component rebuild occurred in this continuation.

Canonical Production remains running. The isolated single-Test qualification
uses its exact DNS bridge as a read-only dependency, verifying the owner's
journal, command/PID and script bytes. An unknown listener is rejected. The
consumer journal records EXTERNAL_DEPENDENCY and cannot stop that bridge.
Keep the canonical owner running while .29 depends on it. Regression covers
borrowing, changed-script rejection and prohibition on stopping the owner.

| Fresh .29 observation | Result |
| --- | --- |
| `vm start test` | PASS, 59.12 seconds, SSH=true, DNS=true |
| `unit provision test` | PASS, 46.78 seconds, one official SDK attempt |
| Unit | `7cc3327d-b2e2-4db4-8f18-680990773f52` |
| Node | `73b15e9d-2438-45d7-b895-9f0b3de5250e` |
| localVmId | `540cdea7-3fb8-4554-93aa-75cdf0ed577d` |
| Cloud role | Online in Test Vehicles `f83dee0e-d93c-4dd2-905f-a3b4f8dc9878` |
| Packaged VSS | All 23 leaves; exact build SHA, no temporary schema applied |
| SM/CM/IAM | Active, success, NRestarts=0 |
| Security read | Enforcing, current-boot kernel read succeeded, zero observed AVCs |
| CARLA/Gateway | Run `574018c9-84c8-4a8a-9445-b1eb176196c8`, only Test connected |
| First component | Existing 1.0.16 received; offline self-test passed |
| Activation | No active provider; waiting-for-safe-stop; safe_stop_timeout recorded |

### Proven blocker: incompatible time contracts

A guest-side authenticated VISS read of the same ten paths requested by native
SM returned complete, internally co-timestamped snapshots, advancing frame IDs,
SAFE_STOP/STABLE, speed=0, accelerator=0, brake=100%, and both reset flags false.
This root network probe is not claimed as execution by the SM process.
The SM mount namespace contains the public CA and exact schema-2 Test-only
binding; profile, Unit, hardware Node, generation, endpoint, server name and
path set match. Private client certificate/key files are absent as required.
No credential content was printed and no ACL or policy was widened.

Latest VISS point timestamp in a correlated read:
`2026-09-06T00:17:13.710Z`. Guest time at probe completion:
`1788653837001` ms. Mac time immediately afterward:
`2026-09-06T00:17:17Z`. Apparent age at probe completion was 3291 ms, including
the final 100 ms probe pause. A previous read showed the same approximately
three-second lag. Mac and VM clocks agree; this is not a multi-second
guest-only clock skew. SM admits source age <=250 ms at acquisition.

Gateway `src/runtime_carla.cpp` initializes SimulationClockAnchor once;
`src/vehicle_state.cpp` computes UTC anchor plus elapsed **simulation** time.
This is expressly required by Gateway `docs/telemetry-contract.md`, Time and
synchronization, and accepted ADR 0006. Pauses or slower-than-real-time periods
can leave even new frames behind real UTC. SM `pocovisstransport.cpp` compares
that UTC with VM wall time; SafeStopEvaluator applies the 250 ms limit. Each
side follows its current rule, but these rules conflict in the live handover.

This proves the observed frames cannot pass freshness, not that no subsequent
defect can exist. No SM/Gateway executable, image, bundle or safety threshold
was changed to force success. The bounded read-only `component diagnose` now
exposes public binding checks and ten-path timing without credential content.
All 168 orchestrator tests passed after the continuation's changes.

### Preserved state and required decision

.29 remains Online and connected in Safe Stop. Cloud still identifies installed
0.0.0 and pending 1.0.16 (pending_component_status=installed); this is not a
successful active-slot swap or running provider. v2/v3 remain deliberately
unapproved to avoid skipping v1. Sequential restoration, all three runtime/
telemetry gates, Autopilot-to-Safe-Stop on .29 and reboot acceptance remain open.
Production remains Online on .28 with factory VDP 0.0.0, no pending component
and unchanged memberships. Old Test, its disk/Unit and immutable .28 remain;
Builder is stopped; no cleanup or push occurred.

Agreement is required before changing the accepted Gateway timestamp contract:
separate real source-frame freshness time from deterministic simulation time,
preserve RunId/FrameId/SimulationTime and coherent per-frame values, and preserve
correct source timing for retained GNSS samples. Do not restamp cached
responses with request time, relax SM freshness, change VM clocks, or rebuild
.29/VDP as a workaround. Prove that bounded Gateway correction before resuming
this same pending Test cycle.

## Authorized Gateway acquisition-UTC correction — 2026-09-06

The operator approved the Gateway clock correction. The live proof changed
only Gateway acquisition timestamps: capture real UTC once immediately after
receiving a world snapshot, before telemetry/camera/control waits; capture GNSS
UTC once in its callback. Normalization, retained-frame reads and GNSS merges
do not retimestamp data. Run/frame/simulation-time identity, all-or-none matched
control facts, ordering checks, SM's 250 ms admission limit, VM time, .29 image,
VDP bundles, schema and all security policies are unchanged.

This is **Gateway acquisition time**, not an independently measured remote
simulator capture time. The accepted Gateway telemetry contract is amended to
v0.4 and ADR 0006 records the amendment. Remote transport-latency compensation
is not claimed by this local CARLA/Gateway proof.

The existing native build uses Gateway worktree `carla-tm-order` at base
`c308c4195f8f9eebd7a5a59ff630d2b13237afb2`, with the bounded UTC patch. Only
Gateway and its affected tests were compiled. Executable is arm64, SHA-256
`5afb2cd74cc0fb3cb646466b8bdec4d61569adf72f7c0b12d60bf26d988a667d`.
Vehicle-state, GNSS and VSS-projection suites pass, including post-pause real
timestamps, unchanged cached-read timestamps, coherent Safe Stop facts and
retained GNSS source time. After the live proof the same UTC source/test delta
was applied to canonical `carla-ego-runtime`; its unrelated existing dirty
changes were preserved. No Yocto/VM/VDP rebuild or new helper was used.

`democtl simulation stop` confirmed physical Safe Stop, detach and STOPPED.
`simulation start` launched the corrected Gateway; `vehicle select test`
performed canonical reset and exclusive attachment. New run:
`433f4d70-589d-4e15-9e75-4c47f77acad8`. No reprovisioning, component upload,
manual SM restart or direct provider start was issued.

| Observation | Confirmed result |
| --- | --- |
| Pending VDP 1.0.16 activation | SM activated slot `a` at 00:34:09 UTC; PID 2105; process configuration matches slot |
| v1 telemetry | Seven paths, provider-reported READY/LIVE/NONE, Result=success, NRestarts=0 |
| Stability | Repeated status retained same PID/start time; 80 recent READY events; SM/CM active, NRestarts=0 |
| Freshness after scene reset | Frame 1851 timestamp 00:34:54.441 UTC; guest probe completed at 1788654894572 ms: 131 ms apparent age including final 100 ms probe pause |
| Native safety result | Already waiting SM transaction completed with unchanged freshness policy; root timing probe is not claimed as SM execution |
| Packaged schema | KUKSA active, all 23 leaves loaded from original packaged schema in service namespace, no temporary override |
| v1 Cloud | Online, installed 1.0.16, pending_component=null |
| 00:42 UTC guest/security | .29 NORMAL, DNS resolves, SM/CM/IAM active, Enforcing, kernel journal read succeeded (380 records), zero observed AVC denials |
| Source stability | Frames 10853→10855 continued at 00:42:24 UTC; SAFE_STOP, speed=0, brake=1 |

The retained last-failure timestamp 1788654558 precedes successful activation;
it is historical evidence, not a new failing attempt. READY remains
provider-reported complete-frame publication, not an independent KUKSA client
read. Full advisory/mTLS and new .29 moving Autopilot-to-Safe-Stop/reboot gates
are not claimed.

### Separate Cloud sequencing blocker

After repeated v1 READY and Cloud confirmation, exactly one
`democtl component approve 2.0.0` restored batch
`17a4f529-96b1-42b3-9835-2b906cc19211` at 00:37:15 UTC. HTTP 200 and post-read
confirm Valid/approved=true and unchanged Production. Deployment remains done
and update component `c8eaf7b8-68f7-4e96-a99f-cf3eafc3c3b5` Ready.

However, subsequent authoritative reads still show Test installed 1.0.16,
pending_component=null, and available-components contains only historical
1.0.0, not 2.0.0. Bounded VM logs contain no install request for 2.0.0. Reapproval
has therefore **not demonstrated reassignment** of the old bundle to this new
Unit. The public verification PATCH schema only documents approval; it does
not promise recomputation of Unit targets. The historical
[stale validation-scope defect](r6-1-validation-set-scope-defect.md) is relevant
background, not proof of the present backend cause.

No blind reapproval, forced-send request, new upload, version bump,
Unit/model/set mutation or fleet-validation approval was attempted to bypass
that boundary. v3 remains deliberately unapproved, so v2 is not skipped.
The agreed automatic reapproval sequence is incomplete and needs a supported
way to assign the existing 2.0.0, then 3.0.0 to this exact Test Unit. Any proposed
forced-send or replacement-batch operation must be agreed before execution;
availability of a generic API endpoint is not proof of eligibility.

Current state is deliberately retained: .29 Online with working v1, simulator
connected in Safe Stop; old .28 Test stopped/unassigned but disk and Unit kept;
Production Online on factory VDP 0.0.0 and unchanged memberships; Builder
stopped. No artifacts, history or caches were deleted. Source remains local
and uncommitted for review; no push occurred in this correction.

## Authorized addressed v2 send — 2026-09-06 00:53 UTC

The operator explicitly approved one addressed delivery attempt for the existing
VDP 2.0.0 to Test .29, without upload or rebuild. `democtl component send 2.0.0`
was added to the shared CLI/API core. It resolves the exact current Test Unit,
unique Ready/non-fake version and approved OEM batch, verifies the retained
signed artifact, checks Production unchanged, and journals intent before a
single POST. It accepts no caller-supplied target, UUID, URL or credential.
Cloud request acceptance is deliberately separate from runtime activation.
Existing request/Unit state can reconcile an uncertain response; an unresolved
attempt cannot be blindly posted again. The current live authorization covers
v2 only; no addressed v3 send was attempted.

The API v11 schema documents one UUID array in the body and HTTP 201 with an
array of request receipts. The one actual request, intent recorded at
00:53:51.297666 UTC, was:

```http
POST /api/v11/units/7cc3327d-b2e2-4db4-8f18-680990773f52/components/send-requests/
Content-Type: application/json

{"update_component_ids":["c8eaf7b8-68f7-4e96-a99f-cf3eafc3c3b5"]}
```

Result: **HTTP 400**, surfaced as `BLOCKED component.send / CLOUD_HTTP_400`.
No second POST or parameter/ID variation was attempted. The existing adapter
exposes the HTTP code but does not preserve the error response body; therefore
the specific backend validation reason is **not proven**. Absence from
available-components is an observation, not a substituted explanation.

Post-read through `component cloud-status 2.0.0` confirms no send requests,
Test Online on installed 1.0.16 with pending_component=null, and unchanged
Production Online on factory 0.0.0 with no pending component. The available
array still contains historical 1.0.0 only. `component status test` confirms
same PID 2105/start time, active slot `a`, 1.0.16, seven paths, READY and zero
restarts. No VDP2 activation or VDP3 test is claimed. The failed attempt remains
protected as UNCERTAIN in the CLI journal (no successful response receipt); the
explicit HTTP 400 and absence read are recorded here rather than inventing a
successful mutation or manually clearing the attempt marker.

Validation: 20 component delivery tests passed, including exact one-Unit/one-ID
POST, approval/readiness guards, response loss/no retry, post-read requirement,
reconciliation and forbidden target overrides; the full 174-test orchestrator
suite passed in 26.22 seconds. Canonical and qualification CLI source copies
were synchronized for the six changed runtime files. No image/bundle build,
signing, upload, VM restart, fleet-validation change, Production mutation,
backup or cleanup occurred. Existing dirty changes remain; no commit or push
was made in this increment.

## Monotonic release / frozen content cycle — 2026-09-06

The operator replaced old-version reassignment with new increasing Cloud
releases carrying the existing functional profiles. This supersedes the
addressed-send experiment above; it does not delete or downgrade components.
The exact Test .29 Unit, image SHA, source connection and Production guard are
unchanged. No Factory/Gateway/SM build or guest restart is part of this cycle.

Shared CLI/API preparation now accepts an explicit content profile:

```text
democtl component prepare 4.0.0 --profile v1
democtl component sign 4.0.0
democtl component upload 4.0.0
democtl component approve 4.0.0
democtl component status test
```

The same commands prepare 5.0.0 with `--profile v2` and 6.0.0 with
`--profile v3`; publish sequentially only after the prior release is actually
active and provider-reported READY. Release major never selects functionality.
All three bundles were prepared and signed through Demo Control. Preparation
compares every payload member against its pinned original signed bundle;
only seven release metadata/version-constant files change. Runtime code,
native ARM64 dependencies, functional paths/capabilities, contract references
and profile-selected advisory declarations remain unchanged. Inner/outer,
provider/manifest and selected runtime constants agree on the new release.

| Release | Frozen profile | Signals | Signed bundle SHA-256 |
| --- | --- | --- | --- |
| 4.0.0 | v1 / 1.0.16 | 7 | `f53beac680f68749e4dc345a8776c18bb278cbd57d9787b7375b265516d7d481` |
| 5.0.0 | v2 / 2.0.0 | 15 | `a3a734e92cf7f092eb9f2b135ea653f015f3231e995519b6d60c7d8aa980ac34` |
| 6.0.0 | v3 / 3.0.0 | 23 | `bfbe690a11eb6b78e7596683298b4c4bd8c8e3e5d5ded362313716dcf99204dc` |

Artifacts remain outside Git under the shared catalog's
`components/vehicle-data-provider/<release>/vdp-<release>-deployment-bundle.tar.gz`.
Each directory retains its prepared/signed manifest and coherent payload.
Tests: 178 orchestrator tests passed, including four explicit-profile replay
tests for byte preservation, deterministic output, metadata cohesion and
CLI/API scoping. Existing compatibility JSON and its hash did not change.

### 4.0.0 delivery, initial failure and automatic recovery

One upload returned HTTP 201, deployment
`cafdd3b7-c3bf-4bf6-bd09-2393da4f39ee`; processing completed (`done`).
Verification batch `68c62aa7-8efd-4043-a48a-3417f176a340` was approved once,
HTTP 200, Valid/approved=true at 01:21:53 UTC. Update Component UUID is
`9dc1e27a-eb37-4223-9c5b-16977aba3ae3`. Test delivery had already started
before that approval; do not attribute validation-Test delivery to the approval.

Read-only `component logs test` proves this initial sequence:

| UTC | Event |
| --- | --- |
| 01:20:17.701 | Launcher calls StopInstance for the prior instance |
| 01:20:17.717 | Image manager records 4.0.0 installed |
| 01:20:17.719 | StartInstance fails: `a different component transaction is already active` |
| 01:20:18.352 | Old provider is stopped; active slot/install marker subsequently absent |
| 01:30:18.361 | Native stack automatically issues another stop/start update |
| 01:30:18.606 | New payload offline self-test passes |
| 01:30:19 | 4.0.0 active in slot `a`, PID 2780, seven paths, READY, NRestarts=0 |

No operator retry, forced-send, restart, source reselection or re-upload was
issued between failure and recovery. The read-only guest status implementation
only reads service state. Its initial DISCONNECTED text was the stopped
provider's unavailability report, not proof of Gateway/DNS failure. Subsequent
guest/source observation at 01:30:57 confirms advancing verified VISS frames
69102→69105, SAFE_STOP, speed=0, brake=1, Enforcing and zero observed AVCs.

The failure matches the pinned Platform runtime source: `StopInstance` saves
an asynchronous remove transaction and returns while it is still running;
`StartInstance` rejects a different active transaction before preparing the
new candidate. Pinned AosCore launcher waits for the StopInstance call, not
that private worker. This is a stop/start completion-contract mismatch, not
evidence of invalid 4.0.0 metadata. The roughly ten-minute automatic retry
allowed activation but does not qualify immediate replacement, A/B rollback
continuity or absence of telemetry downtime. The existing direct-runtime tests
wait after StopInstance; they do not prove this immediate launcher sequence.

Demo Control's bounded log projection now preserves two fixed allowlisted
runtime failure labels even when its instance-body redaction hides the suffix.
No raw identity body, credential or telemetry is exposed; 20 delivery/log tests
passed after this diagnostic-only change. No Platform implementation was changed.

Pinned CM `desiredstatushandler.hpp` declares
`cWaitActiveTimeout = Time::cMinutes * 10`; `WaitInstancesActive()` waits while
any instance is Activating. This is a platform wait, not time spent uploading
or an extra Demo Control retry. The measured upload+post-read commands were
12.14 s for 4.0.0 and 10.73 s for 5.0.0; approval+post-read was below 9 s each.
The exact source of the second desired-status trigger is not separately
attributed to a Cloud timer; only the native second launch and its ten-minute
interval are observed.

The separate Platform correction must cover the real
`StopInstance(old) -> StartInstance(new)` launcher sequence with a deliberately
unfinished stop worker, not only direct StartInstance-to-StartInstance tests.
It must retain the safety gate, fail-closed behavior, predecessor rollback
state, explicit removal semantics and reboot recovery. Merely adding a sleep,
retrying a command or waiting while holding the transaction mutex is not an
accepted fix. This correction is identified but not implemented in the
release-packaging increment.

5.0.0 upload returned HTTP 201, deployment
`d11af03e-3a0f-4503-aa01-7dd2b49b431f`; its live result follows below. At this
checkpoint 6.0.0 is signed locally and has not been uploaded. Production
remains Online on factory 0.0.0 with no pending component and unchanged sets.
Old .28 Test/Unit/disk and stopped Builder/caches are retained. Full advisory,
mTLS, independent KUKSA consumer reads, new moving-stop and reboot gates are
not claimed. All source changes remain uncommitted; no push or cleanup occurred.

5.0.0 verification batch `d4c7f3d3-9b6f-414b-af80-6d19b7941243` is
Valid/approved=true (HTTP 200 at 01:33:28 UTC); Update Component UUID
`976d16a9-57b5-4c15-bb06-28b4dacd0db7`. Its first replacement at
01:32:58.715 UTC reproduced the same fixed transaction-conflict error; the
prior provider stopped at 01:32:59.308. At 01:38 UTC Cloud still shows installed
4.0.0/pending 5.0.0, with no Production pending component. No manual retry
or restart was issued.

After the diagnostic change, the complete 178-test suite also passed in
27.21 s with temporary Unix-socket fixture permission. An earlier restricted
invocation failed four fixtures at `socket.bind` with sandbox PermissionError,
before their assertions; no product change was made to bypass that harness
restriction. Documentation/link validation is run on the final checkpoint.

### 5.0.0 remaining boundary and preserved final state

At 01:42:59 UTC the native stack retried 5.0.0. Its payload self-test passed
at 01:42:59.608, and the durable transaction entered `waiting-for-safe-stop`.
This did not mean it had started the provider. Read-only diagnosis initially
returned ConnectionRefusedError for VISS. The simulation manifest records
`status=failed`, `error=VSS dashboard stopped during live handover`, finished
01:33:24.740 UTC (started 00:33:22.783). The exact dashboard-exit cause is not
claimed; no new Gateway code or timeout change was made.

Recovery used only `democtl simulation stop`, `simulation start`, then
`vehicle select test`. Stop honestly reported physical stop NOT_OBSERVED because
Controller was already absent; it stopped the owned remaining CARLA process.
New run `693c8f74-edbb-4af9-8f2a-7df32bfee76e` connected only Test at 01:48:08,
with advancing server-verified VISS frames. VM PID 54143, SM PID 1651, Unit/Node
identity and signed 5.0.0 remained unchanged. This was simulation recovery, not
a VM restart, reprovisioning or another component publication.

A read-only clock comparison then proved an additional boundary:

| Same bounded observation | UTC |
| --- | --- |
| Mac before Demo Control probe | 01:50:56 |
| Gateway frame 4167 | 01:50:58.690 |
| Guest clock at probe completion | 01:51:00.853 (`1788659460853` ms) |
| Mac after the command completed | 01:50:58 (whole-second output) |

Thus the guest clock was at least 1.853 seconds ahead of the Mac at the end
of the probe. The apparent source age in the guest was 2163 ms, including the
probe's final 100 ms pause, versus SM's 250 ms freshness admission. The same
samples report speed=0, accelerator=0, brake=100, SAFE_STOP/STABLE and both
reset flags false; frame IDs advance. This rules out a physically moving
vehicle in those samples. It is a root network/time observation, not a log of
the SM evaluator's individual reason; the source of guest clock drift and
its time-sync service configuration are not yet established.

Final component status shows no active provider/slot. `last-failure.json`
records 5.0.0 `safe_stop_timeout` at guest epoch 1788659459; a native repeated
transaction at epoch 1788659460 is again waiting for Safe Stop. Cloud Test is
Online, installed_component still 4.0.0, pending_component 5.0.0 with
pending_component_status=`installed`. That Cloud status is explicitly **not**
proof of runtime activation. No manual SM restart, time adjustment, clock
tolerance relaxation or forced-send was performed. 6.0.0 remains local,
signed, NOT_UPLOADED, so v2 is not skipped.

The repeat-cycle implementation is complete and its 178 local tests pass;
live qualification is **partial**: 4.0.0/profile v1 proved seven-signal READY,
5.0.0/profile v2 delivered and self-tested but not active, and 6.0.0/profile v3
not delivered/tested. Correct stop/start completion and trustworthy VM clock
synchronization are the next Platform boundaries, not reasons for another VDP
version change. Production final read remains Online/factory 0.0.0, no pending
component, same memberships and non-validation set. Test VM and restored
simulation stay running to preserve this diagnostic state; old .28, immutable
.29, Builder/caches, signed artifacts and all Cloud identities remain.

### Clock investigation correction — 2026-09-06 02:04 UTC

The operator authorized correction of the clock problem. Further read-only
evidence corrects the initial attribution: **the Mac is behind reference time,
not a proven faulty guest clock**. Relative host/guest skew alone did not identify
which clock was wrong.

Existing `democtl component diagnose test` now includes a bounded, allowlisted
native clock observation. VM `systemd-timesyncd.service` is loaded/active with
NRestarts=0. No chronyd/ntpd service is installed. Its timesync D-Bus read shows
the packaged Google fallback servers, current server `time3.google.com`,
last accepted NTP message at 01:45:58 UTC, stratum 1, PacketCount=9,
Ignored=no and Jitter=2.840 ms. Poll interval is 34 min 8 s. The separate
timedatectl settings read returns exit 1 and is not substituted for evidence
of synchronization; the timesync service/message read succeeds.

Mac's built-in `sntp` was invoked **without** `-S`/`-s` (no clock mutation):

| Reference | Correction needed on Mac | Reported uncertainty |
| --- | --- | --- |
| time3.google.com | +2.014640 s | 0.038022 s |
| time.apple.com | +2.015066 s | 0.004617 s |

Both independent references agree with the observed guest-to-Mac difference.
Mac `timed` is running (PID 392). Noninteractive administrative reads of the
host network-time settings fail with `sudo: a password is required`; no
administrator credential was supplied or requested in chat. `/etc/ntp.conf`
is absent, which does not establish that automatic time is disabled.
The reason Mac's running time daemon retained this offset is still unknown.

Correction requires a host-administrator action, for example the built-in
one-shot `sudo /usr/bin/sntp -S time.apple.com`, followed by a read-only NTP
offset check and VM/VDP observation. This command has **not** been executed.
No VM clock adjustment, new time service, NTP source replacement, SM freshness
relaxation, restart, package upload or Production mutation occurred in this
investigation. Automatic host time configuration and sustained convergence
must also be checked before claiming a durable fix; a one-shot correction is
not that proof.

Two new clock-observation tests pass, covering exact read-only commands,
bounded public fields, missing tools and failed observations. The diagnosis is
preserved; clock correction and renewed 5.0.0 activation remain unperformed
pending host administrator access.

### Operator-approved demo age allowance — 2026-09-06 02:43 UTC

This supersedes the preceding current-status/host-admin blocker, not its
historical evidence. The operator manually corrected Mac time; VDP 5.0.0
activated at 02:09:41 UTC (PID 3317, slot a, 15 paths READY). Mac `timed`
subsequently applied a -2.016095400-second correction at 02:10:27 UTC.
The operator explicitly deferred clock diagnosis and authorized a 5-second
source-age allowance for this local demo.

The [Test-only exception](../../contracts/platform-fota-safe-stop/README.md)
is an explicit `safeStopFreshnessProfile: "demo-5s"` bootstrap SM setting.
The absent/default `standard` value remains 250 ms. Both admission and latest
sample revalidation use 5000 ms only in the demo profile. All other conditions,
including rejection of future timestamps, remain unchanged. This admits real
source delay as well as clock skew; it is not unchanged profile 1.1.1 compliance.

The exact .29 Platform base 45dfa22 was used for an offline SM-only compile:
1716 tasks, 1708 reused, no image build. The complete native runtime suite ran
61 cases: 59 passed, including new demo-boundary/config regressions, and two
real-provider cases were explicitly skipped as usual. ARM64 executable SHA-256:
`f0e8c3806c95befc880276f7ca1a05de82a9d866abe9bb665ba3ba868aaedde2`.
Builder stopped cleanly after export. Artifact and compact test evidence are
outside Git in `demo-artifacts/aosedge-sdv-demo/runtime-proofs/sm-demo-5s`.

Demo Control applies the exact binary and generated configuration through
read-only systemd namespace binds from `/run/democtl-sm-demo-5s`; it does not
write the immutable image or replace files in the base rootfs. One Test SM
restart produced PID 3739, ActiveState=active, Result=success, NRestarts=0,
effective binary SHA matching the artifact and profile `demo-5s`. The source
binary was assigned the existing binary's label (bin_t), the config retained
aos_conf_t; the running sandbox executable is reported as a crun-cloned memfd
with tmpfs_t. No SELinux rule, certificate, ACL or systemd security restriction
was widened. Fresh AVC inspection is still a separate observation.

The restart cleared SM's ephemeral public CA/binding. The existing
`democtl vehicle select test` restored those public inputs and reported no-op:
same Test assignment generation 1, same simulation run, SAFE_STOP, speed 0,
brake 1, advancing VISS frames 66150→66153. The SM apply operation now restores
the already selected Test's public source inputs after its one restart; it
does not select Production or reset the scene. VDP 5.0.0 remained PID 3317,
slot a, 15 paths READY, zero restarts and matching process/slot configuration.

Commands for this bounded qualification are `democtl component
sm-builder-start test`, `sm-build test` (compile/tests/export then Builder stop),
`sm-apply test`, and read-only `sm-status test`; `sm-builder-stop test` is the
explicit graceful stop operation. They use fixed Test/artifact/source targets,
not caller-supplied commands. They are qualification tools, not a general
Factory image deployment interface. Temporary mounts disappear on VM reboot.

VDP 6.0.0 upload was **not executed**: the execution safety reviewer rejected
the attempted command because it requires exact authorization for this binary
payload to the external Aos Cloud destination. No workaround/retry, approval,
publication or new Cloud release occurred. Consequently an update under the
5-second profile is **not yet demonstrated**. Production, immutable .29,
existing signed bundles and Cloud identities are unchanged. The separate
StopInstance/StartInstance async transaction race is not fixed by this change.

The post-reselection SM namespace observation corrected the initial public
input restoration claim: the host files existed, but systemd masked the whole
`/run/credentials` parent inside the newly sandboxed process. The proof
drop-in now uses standard `LoadCredential` for exactly the existing public
CA and Unit/generation-bound JSON; no private key or permission widening is
introduced. One additional SM restart was required (two total for this proof).
Final SM PID 4030 has both public inputs visible in its own namespace, the
expected executable SHA and `demo-5s`, ActiveState=active, Result=success and
NRestarts=0. Repeated apply can observe this completed state without restarting.
All 183 local Demo Control tests passed; the 41 component tests passed again
after the credential-view correction. End-to-end 6.0.0 activation remains
unperformed pending exact Cloud upload authorization.

### Authorized 6.0.0 delivery — 2026-09-06 02:55 UTC

The operator explicitly authorized the prepared VDP 6.0.0 upload to Aos Cloud
and validation batch approval for Test. `democtl component upload 6.0.0`
returned HTTP 201, deployment `6f04cf7e-981f-49ac-a6ae-d4fad4ab2e42`.
`democtl component approve 6.0.0` returned HTTP 200, batch
`e5076e29-f42d-4587-b909-5fc737e1358a`, approved=true, state=Valid.
Cloud identifies the Ready component version as
`0aaa275d-3f95-4a4e-a3db-3f956fb5fec1`. Post-read: Test Online, installed 5.0.0,
pending 6.0.0; Production Online/0.0.0, pending null, same memberships,
non-validation Production set and allow_unknown_components=false.

SM received and installed the 6.0.0 item at 02:52:17 UTC, but immediate
StartInstance returned `a different component transaction is already active`:
the previous release's asynchronous StopInstance is still outstanding. This
is the already diagnosed independent lifecycle race, not a new package or
Cloud delivery fault, and the age-window patch deliberately does not change it.

The old simulation stopped answering Gateway connections around 02:48 UTC;
VDP logs report connection refused. Its Controller was absent when the owned
`democtl simulation stop` reconciled/stopped CARLA, so physicalStop was
NOT_OBSERVED (not claimed). The replacement `democtl simulation start` is in
progress. No VM/SM restart, republish, forced-send, clock manipulation or
Production mutation was performed in this delivery continuation. The pending
native update and its state are preserved while the existing simulator is
restored.

### Completed Test 6.0.0 proof — 2026-09-06 03:05 UTC

The restored simulation run is `35ae0119-2f8a-471e-884a-ab126b5cd7e3`.
`democtl vehicle select test` completed at 02:56:52 UTC, assignment generation
1, verified TLS and advancing frames, with the car remaining in Safe Stop.
At 02:56:54.859 UTC the waiting SM operation successfully stopped VDP 5.0.0.
The nearby root-network observation had SAFE_STOP/STABLE, speed=0,
accelerator=0, brake=100, both reset flags false and advancing frames 2970→2972.
Its newest source timestamp 02:57:48.274 UTC versus guest observation epoch
1788663470407 gives an apparent age of 2133 ms including the probe pause.
This is consistent with the new gate allowing the existing clock offset; it
is not a per-sample SM evaluator trace or a clock repair claim.

AosCore retried the lifecycle at **03:02:18.272 UTC**, approximately 600.66
seconds after the first rejected StartInstance. The unchanged pending 6.0.0
candidate passed its offline self-test at 03:02:18.547 UTC and became active
at **03:02:19 UTC**. No force-send, second upload, manual VDP start or SM/VM
restart was used to accelerate that retry.

Final observations through Demo Control:

- VDP version 6.0.0, active slot a, process PID 4292, matching slot/config,
  Result=success, ExecMainStatus=0 and NRestarts=0.
- Provider-reported READY/LIVE/NONE with all 23 v3 telemetry paths; capability
  manifest SHA `60e23b1cd91a698c56e4c6b4931d0128c95e62a71233dc7a0514edba6ec46d43`.
- Cloud Test Online, installed=6.0.0, pending_component=null and no pending
  validation batch. Its residual pending_component_status=`installed` does not
  represent another pending item. Production remains Online/0.0.0, no pending
  component, unchanged memberships and original non-validation set settings.
- SM PID 4030, expected proof binary and `demo-5s`, both public inputs visible,
  no automatic restarts. SELinux Enforcing, zero kernel AVC denials since SM
  start, full observed window covered (381 current-boot kernel entries).

One VISS non-monotonic frame warning at 03:03:51 caused a transport reconnect;
the provider reconnected to verified VISS and KUKSA within about 0.6 seconds
without a process restart. The final subsequent read again reports 23-path
READY. Native logs also retain the factory 0.0.0 placeholder's downgrade
rejection and the old async remove/status bookkeeping warnings; no blanket
error-free Platform claim is made.

The requested 5-second local-demo update proof **passes**. The prior 4.0.0/v1,
5.0.0/v2 and now 6.0.0/v3 observations complete the narrowed 7/15/23 telemetry
sequence, but only the last update uses the transient demo-5s SM. This does not
qualify an unchanged Factory .29, a reboot-persistent deployment, full advisory,
mTLS or the live moving-negative matrix. The independent Stop/Start race still
causes a roughly ten-minute recovery delay and a gap without the previous
provider; it requires its own fix. Builder is stopped; Test, simulation and
Production are left in their observed running states. No commit, push, image
build, deprovisioning or cleanup occurred in this continuation.
