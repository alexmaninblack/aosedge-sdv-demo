<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Preserved Test: function observation activation

Date: 19 September 2026. Status: P7 in progress, not end-to-end acceptance.
Authority: the accepted versioned-service observability work packet.

## Preserved live boundary

The 04:20 UTC native Cloud read confirmed the existing staging Test Online,
Factory `.35`, VDP `79.0.0`, Brake `59.0.0` and Tire `34.0.0` installed; both
service instances were active and no pending component was reported. The
selected endpoint is `aws-stage.epmp-aos.projects.epam.com`. Production remains
untouched. The run is `ac456637-7e30-474f-be40-5716f944a21b` and the current
Cloud Unit is `a842a53e-a30b-481c-8747-f73a96c351d7`.

## Consumer-first activation

| Consumer | Source checkpoint | Container image | Storage proof |
| --- | --- | --- | --- |
| Brake | `42395715103d9f512c2586a2c9b98c3975c06ab7` | `sha256:48f633748d225b27079e69a439e875745067a5248a7006c3b9685dc8a5e2baf1` | Schema 5 ready; all 4,358 pre-existing message rows unchanged |
| Tire | `47cfa632a80c89a7eaab0c501fe437c4ae2cb180` | `sha256:5dddd12060c3e65f928e844a65f92ae8826d1e8e52dce66329f86682934c3326` | Schema 4 ready; all 8,973 pre-existing message rows unchanged |

Each consumer was built from its clean checkpoint, then stopped, activated
and started once through the existing `democtl backend` path. Its named data
volume and current-Test context were preserved. Message-prefix counts and
SHA-256 checks before/after migration matched exactly; no raw samples were
copied into this report. No VM, simulator, native controller or service
restart was part of these replacements.

The normal `backend inspect` reader observes both new function resources with
the expected closed envelope and empty items. Empty is expected before the
new producer releases, not an input-health failure. A retained real Brake V1
window from release `56.0.0` was read through `backend window-detail`, returning
its 41 stored samples without fabricated points.

Before activation, Brake passed its source/security gate, 58 backend tests
and 12 dashboard tests. Tire passed 20 backend tests and its source-only
credential/binary scan. Demo Control passed 35 backend, 12 Presenter, 7 CLI
and 35 retirement tests; no test performed live cleanup.

## Presenter activation

The idle Presenter server alone was stopped and restarted after activating
the isolated P6 build. Its previous compiled assets are retained at
`/private/tmp/aos-service-p4.MutJS1/presenter-before-p6` for rollback.
The existing browser's Reload UI action loaded the new interface. It shows
old-service function input as unreported, while preserving actual product
results and source/receipt times. The Brake dialog independently displays
the previously confirmed Reset, product assessment and unreported function
axes. This is not evidence that a new producer is working.

P6 gates: TypeScript, 222 unit and 107 browser tests, plus production build.
The compact V1 detail table/overflow correction is recorded in the separate
native recovery and Presenter qualification note.

## Producer preparation

Source checkpoints: Brake `52d7c4ff67898cac44d4fc5b1ed49c9c6218dd7a`, Tire
`1a747fff72df053dcd05a83df91adc2d12dfea1d` (local, not pushed by this increment). The export gate now requires
the added function-observation CTest suite: all eight Brake/five Tire groups
must pass; omission is rejected. Four Brake and fifteen Tire export tests pass.
The existing compiled Linux ARM64 tests passed again in their network-disabled
fixture container. A host invocation initially referenced container-only
`/checks` paths and failed to open its log; correcting the harness path did
not change the product or waive a gate.

Brake V3 was built, packaged as `brake/60.0.0` with permissions and pidsLimit
24, then signed using the selected staging SP certificate. Prepared payload
and signature verification passed. The SP service read at 04:38 UTC reported
complete assignment coverage containing only the current Test. Publication
and real service behavior remain separate, unexecuted gates in this record.

The Tire build completed at 04:38:29 UTC; all five mandatory CTest groups
passed. After the original tool session was no longer available, its immutable
build receipt and read-only build history were reconciled; no build was retried.
It was packaged as `tire/35.0.0` at 04:44 UTC with permissions and real telemetry
enabled. This release is prepared, not signed or uploaded.

At 04:43 UTC, a fresh Cloud read still confirmed the same Test Online, Brake
59 and Tire 34 active, VDP79 installed, and no pending component. The Brake60
publication reader returned `NOT_PUBLISHED`. The subsequent upload invocation
was rejected by execution review before process creation: it required explicit
approval of the exact new release, considering the earlier Brake59 approval
insufficient. No upload or alternative transport was attempted after rejection.
The operator was asked to authorize Brake60 and Tire35 for the selected staging
SP/current Test. Pending that answer, P7 publication and dependent live gates
are blocked; local consumer/source evidence remains valid.

A subsequent engineering-only guest read confirmed both original service
processes alive, KUKSA and auth-compat running with zero systemd restarts, and
no reported allocation/thread failure markers in the bounded service journals.
Brake still reports skipped ordinary-drive captures for insufficient qualified
wheel samples and brief authorization-renewal interruptions; these are existing
behavior, not acceptance of the uninstalled successor. Presenter returned HTTP
200. No rootfs remount, permission change or restart was used for these reads.

## Authorized successor installation and live results

The operator explicitly renewed authorization for both exact staging
successors. Brake60 was uploaded once at 04:47:26 UTC (deployment
`633da15b-79b6-4603-b755-6c9a1ad7380d`), Tire35 once at 04:49:03 UTC
(`0963338b-8bd1-4439-b1ad-6dac7d7f6df0`). Both returned HTTP 201 and
subsequent native Cloud readers reported READY. The 04:50:25 UTC Unit read
confirmed Brake60 and Tire35 installed/active with no pending service or
reported error. Service updates did not require Safe Stop. VM, CARLA,
existing native allocation IDs, models and prior records were preserved.

The existing serialized CARLA maneuver commands then produced real results:

| Check | Evidence |
| --- | --- |
| Brake maneuver | 267 frames, 13.35 s, maximum 30.589 km/h, 31 braking frames above 10 km/h; physical stop confirmed |
| Brake60 product | Assessment `dad13d4d-2961-543f-87bb-6858cc29e1b4`, source assessment time 04:51:54.904 UTC, receipt 04:51:55.025 UTC; 26 active/13 qualified straight samples; Inspection recommended |
| Brake retained state | First successor result starts from wear index 74, matching the preceding Brake59 result; warning ACK existed before this new assessment |
| Tire maneuver | 260 frames, 13 s, maximum 35.103 km/h, physical stop confirmed |
| Tire35 product | Assessment `7197c7cd-8331-57a1-a883-57608d484f75`, source 04:52:32.907 UTC, receipt 04:52:32.984 UTC; Inspection recommended |
| Function observation | Both actual producers report version/profile, receiving input, independent activity/delivery and correlated advisory status through the new backend resource |
| Native vehicle view | Both advisories displayed Inspection recommended separately from backend results |

These are demo model results from real CARLA physics, not calibration or
production-diagnosis claims. Cross-clock source/receipt differences are not
latency guarantees.

### Reset-history presentation defect found during SOTA

The live successor initially showed a fully confirmed Brake59 Reset as an
uncertain Brake60 Reset and would suppress its new result. An isolated test
reproduced the selector failure. The corrected selector fully validates the
retained command/result/request/Gateway correlation against its own release
and the same Unit/service/Subject/allocation, then labels a different-release
confirmed CLEAR as historical. It does not apply an old cutoff to the current
release or reissue a Reset. Corrupt, partial and current unconfirmed outcomes
still fail closed.

All 223 unit tests and the 19 dialog/browser cases passed; the isolated
production build passed. Static assets were activated without a server,
VM or simulator restart, retaining the previous assets at
`/private/tmp/aos-service-p4.MutJS1/presenter-before-reset-history`. A live page
reload showed the old Reset explicitly as history and the real Brake60 result.

### External network off and queued delivery

The normal Test packet filter switched OFF at 04:55:28.769 UTC and ON at
05:00:18.596 UTC. No backend container, service, KUKSA, VM or simulator was
restarted. Real Brake and Tire maneuvers completed while OFF. Guest diagnostics
showed new assessments, backlog, live processes and local token replacements.
KUKSA/auth-compat retained their process identities with zero systemd restarts;
the bounded service journals contained no thread/allocation failure markers.

At 05:00 UTC the backend's last product/function receipts were still:

| Backend | Product count / last receipt UTC | Function count / last receipt UTC |
| --- | --- | --- |
| Brake | 4,443 / 04:55:23.194 | 35 / 04:55:25.038 |
| Tire | 9,117 / 04:55:14.218 | 31 / 04:55:15.265 |

Counts matched the earlier OFF sample. The initial pre-command Brake sample
was 4,441/33; the two additional records arrived before filter completion,
not during OFF. The Cloud reader independently reported OFFLINE at 04:58:56
UTC, and ONLINE at 05:01:22 UTC after reconnection. Native telemetry remained
LIVE with both warnings while the Presenter aged its function report to
LAST KNOWN and disabled remote Reset after service contact expired.

Immediately before reconnect, a bounded read hashed all 16 Brake and 15 Tire
queued product messages (including 2 Brake/1 Tire assessments). After reconnect,
all 31 hashes matched exactly one backend message each; none were missing or
duplicated. Queued content was not copied into this report. This proves the
recorded bounded backlog, not unlimited queue capacity or all V1/V2 cases.

### Independent Reset and renewed warnings

Brake60 Reset `03819858-5b56-49c3-9c7c-9cc85d412bb3` was issued once at
05:01:18 UTC and Gateway CLEAR confirmed at 05:01:20.620 UTC. Native Brake
changed to Monitoring while Tire retained its warning; the Presenter excluded
the preceding result without deleting history. Two independent real Brake
maneuvers produced MONITOR (wear 54→60) and INSPECTION_RECOMMENDED (60→66),
assessment `1c5e7a59-5c79-5c98-83f9-c1e5979ec999` at 05:03:54.058 UTC.
No model thresholds or reset baseline were changed.

Tire35 Reset `6be8250e-edba-4eb8-b17f-1302ab73d40e` was issued once at
05:04:38 UTC, CLEAR confirmed at 05:04:38.743 UTC. Native Tire changed to
Monitoring while Brake retained its warning. One real Tire maneuver produced
assessment `866f6f6d-9a0e-5bba-aea5-476e92d8809f` at 05:05:58.360 UTC with
41 valid active samples and INSPECTION_RECOMMENDED; its current advisory ACK
was observed separately. These checks used the normal backend command path,
not direct service/model edits or mock records.

The UI ACK explanation was also made neutral: confirmation can represent
SET or CLEAR, not necessarily an active warning. The targeted 28 selector/view
tests and a final isolated production build passed after this wording change.

### Native controls and source recovery

The approved simulation-only restart activated the changed native application
at 05:08–05:12 UTC. Test VM, Cloud identity and service allocations remained
unchanged; the new source run is `b5157766-2838-4080-9bc8-b28ca16129cb`.
Both services resumed receiving inputs and renewed their existing warning
requests without redeployment or model Reset. The initial Monitoring display
after reconnect was followed by independently observed APPLIED SET facts and
both native inspection warnings; it was not a model-state loss.

Return to road was clicked in the native application first from Safe Stop and
then from Autopilot at approximately 19.4 km/h. Both finished stationary in
Manual with explicit subsequent Autopilot selection required. The first
relocation left Brake assessment `e343cedb-bc59-52ff-bfeb-5de7c09a6d94`
(05:05:59.962 UTC, wear 74) unchanged: no fictitious assessment was created by
that stationary discontinuity. Current control counters remained zero for
command timeouts, ownership timeouts and disconnects. This does not replace
the still-required manual off-road case or claim that real stopping motion
can never constitute a valid braking episode.

Both new native maneuver buttons completed through the normal serialized
Demo Control path:

| Button | Operation | Physical evidence | New backend assessment |
| --- | --- | --- | --- |
| Brake | `b97f2167-6213-4765-80c2-4a0f6b710acd` | 266 frames, 13.3 s, maximum 30.507 km/h | `2c5baf10-88f9-570a-9fa3-14496ae8ba41`, 05:15:23.191 UTC, wear 74→80 |
| Tire | `1927f721-2ea8-4632-becc-7436307863a9` | 260 frames, 13.0 s, maximum 35.089 km/h | `b7294037-7e74-5769-94ab-8c6f14d6d7f7`, source 05:15:51.070 UTC, INSPECTION_RECOMMENDED |

At this stage no factory-owned change had been identified. The later
Park/Resume failure below supersedes that provisional clean-cycle decision.
Changed service packages remain Cloud-delivered; host controls and UI are not
baked into Factory.
The documentation quality gate passed (224 Markdown documents) before the
clean cycle. No clean-cycle acceptance is implied by these preserved-Test
results.

### Final UI regression and clean-cycle boundary

The final Presenter tree passed all 223 unit tests and all 108 isolated browser
tests (32.1 seconds), including the newly added historical Reset after SOTA
case. These are fixtures, not the clean live-cycle result.

At approximately 05:17 UTC, the UI Finish confirmation for the current Test
was rejected by the execution safety reviewer before submission. No cleanup
started and no CLI or indirect deletion was attempted. The operator was asked
for exact approval covering the current Unit, bindings, local working files
and scoped backend records while preserving .35, releases and Production.
The independent, non-destructive Park/Resume check proceeded; its final
recovery evidence is recorded only after observation.

### Park/Resume: native CM storage-retention failure

**FAIL — P7/P8 remain open.** Park completed at approximately 05:19 UTC;
Resume was submitted at 05:20:07 and completed at 05:21:57.157 UTC. The same
Unit and releases returned Online, but successful lifecycle status did not
prove preservation of service state. Both local models and their function
observation ledgers had been recreated, while the backend retained history.

Bounded boot logs identify CM PID 1042 at monotonic 10.996–11.016 seconds:
it loaded 11 instance records, including two current service instances and
cached older versions with identical service/Subject/index identities. It
then logged `Image invalid for cached instance`, followed by `Remove instance`
and `Remove storage and state from system` six times for Brake/Tire. The
removed directories were the same persistent ext4 storage paths mounted by
the current versions, not ephemeral container filesystems. Boot wall time
was subsequently synchronized; monotonic order establishes this sequence
without assuming pre-sync wall timestamps were accurate.

The pinned AosCore library `60cb83535f773762c61ac5f544b31b7b88c502e3`
corroborates the path: `InstanceManager::Start` loads instances and calls
`ClearInstancesWithDeletedImages`. `ServiceInstance::Remove` deletes storage
by `InstanceIdent` without a version, then deletes the version-specific
instance database row. Older and current versions share that storage identity.
The `RemoveOutdatedInstances` path calls the same method and also needs a
regression. Read-only comparison with upstream main
`5560291ba6914e36a5b841ade4d8fc54134a9e91` found the same unconditional
storage removal; no claim is made about an unpublished platform-team fix.

After Resume, Brake returned to initial wear 54 and Tire had no model. Both
function producers restarted at generation 1; pending observations accumulated.
Read-only backend queries confirmed one content conflict per service and no
new accepted function observations after 05:19:09.749 (Brake, 120 records)
and 05:19:10.588 (Tire, 137 records). Existing history is not new receipt.
Do not bypass conflict checks, erase history or fabricate a generation to
conceal the native retention defect.

The retained Test, overlay, Cloud identity, storage and journals are preserved.
No Finish, model Reset, redeployment, further reboot or native patch activation
was performed after this discovery. The operator was asked for a bounded
extension to CM, which is outside the original P1–P8 source boundary. An
isolated red regression has now reproduced both missing-image and expired-TTL
cleanup against the exact pinned library. All 17 original launcher cases
passed; both new retention cases failed at the assertion that removing an
old version must not remove the current version's shared storage. The test
also confirms removal of the old version-specific database row and retention
of the current row, isolating shared storage cleanup from version selection.

The proof uses an isolated Linux ARM64 container with networking disabled,
the original launcher/utility sources, and GoogleTest v1.14.0 pinned to
`f8d7d77c06936315286eb55f8de22cd23c188571`. The initial whole-library test
configuration required unrelated SoftHSM fixtures; a focused launcher harness
avoided that unrelated dependency without modifying product code. A missing
container `jq` affected only the shell summary after the complete test run;
the GoogleTest JSON was read on the host and confirms 19 tests / 2 failures.
Evidence remains under `/private/tmp/aos-service-p4.MutJS1/`:
`aos-core-storage-proof`, `cm-storage-harness`, and
`cm-storage-baseline-results.json`. These contain no guest credentials or
customer payloads. At 05:42:59 UTC the JSON reported 19 tests, 2 failures,
0 disabled, 0.336 seconds. Its SHA-256 is
`533a9f29d0eb4a104c21f83cee5a56ac71774592f75add2f2f5c825e567f39ee`;
the test source SHA-256 is
`022c48471077c16932b938b49491cbf06d2ff2ca9b9e8fcc3d27ec908f2d925c`.
No candidate CM fix or successor Factory build has started.

The bounded candidate design must separate version-record retirement from
shared storage ownership: retain data when another version with the same
service/Subject/index still exists, and remove it only when the last owner is
retired. Regression acceptance must cover active and cached survivors, removal
of all old versions, independent Subject/index isolation, repeat startup,
ordinary final cleanup, and error handling. This is a proposal pending the
native-CM scope extension, not an implemented interface change.

Earlier .35 Park/Resume qualification did not compare
pre/post model and producer continuity and therefore does not close this case.

## Accepted disposition after diagnosis

The operator accepted [ADR 0017](../architecture/decisions/0017-continuous-demo-lifecycle-and-upstream-core.md):
do not implement the proposed native CM fix now. Remove Park/Resume from the
operator interface, keep the retained Test for evidence until confirmed Finish,
and qualify a fresh continuous cycle. The bounded storage-owner fix above is
an upstream proposal, not an outstanding request to patch this VM. Periodic
cleanup still reaches the same defect; no unlimited-uptime guarantee is made.
The [sanitized handoff](aoscore-shared-storage-handoff-2026-09-19.md) retains a
test-only reproduction. No upstream submission is implied by preparation.

## Open acceptance

- Native CM retention across cleanup of old service versions and restart;
  current preserved Test is diagnostic evidence, not a clean passing run.
- Broader version/early-input recovery, repeat and negative/reset outcomes.
- Interrupted moving capture and manual off-road recovery, beyond the native
  stationary and Autopilot recovery cases above.
- V1/V2 offline queues and all clean profile transitions, beyond the bounded
  V3 Brake/V1 Tire proof above.
- All clean profile transitions and Factory/P8 qualification. No Factory image
  has been built by this increment.

These are explicit exclusions, not completion claims or a request to stop.
