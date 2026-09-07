<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Control Source Checkpoint and Next Factory Release

- Status: Factory .31 Test VDP 15/v3 and desktop source checkpoint; fresh-overlay repeat remains
- Version: 0.10
- Prepared: 2026-09-07
- Owner: Demo Solution Team
- Design: [Demo Control](../architecture/demo-control.md)
- Evidence: [VDP family checkpoint](democtl-vdp-family.md)

## What is demonstrated

<a id="current-test-baseline"></a>

<a id="desktop-preparation-checkpoint--2026-09-07"></a>

### Desktop preparation checkpoint — 2026-09-07

Before new native desktop work, the operator requested source commits, pushes,
plan documentation and bounded housekeeping. The accepted next steps are in
the [Native Demo Desktop Plan](../planning/active/native-demo-desktop.md).
No combined telemetry window, native launcher or Space automation is implemented
by this checkpoint. CARLA remains a separate window.

Current source scope: native Presenter/workspace and black background; visible
VM credential input and journaled preparation; safe initial stationary Manual;
Cloud-only Platform observation; current-vehicle selection projection;
telemetry freshness/context and unavailable advisory; interactive lifetime fix.
Runtime source is `a3e22ae` on `carla-ego-runtime/main`. Solution implementation
is `9d62e50` on `aosedge-sdv-demo/main`; the documentation commit containing
this entry follows it. Platform
remains `0bed8b3769b09fbe685ed599ca8d10e6594fbe53`, with immutable Factory .31.
These pins do not rewrite existing binary or Factory build provenance.

The one-hour shutdown was diagnosed from the previous run: its Controller
completed at 3600.0369 seconds under `maximum_session_seconds=3600`; dashboard
termination was downstream. The interactive runner now passes `--until-stopped`
and records that lifetime. Bounded runs retain their duration limit, and
explicit stop, command/ownership expiry and disconnect behavior remain active.
Targeted lifetime tests and actual restarted-run configuration were checked;
no new hour-long endurance test was performed.

The latest cold-start session is `5fd8a8c7-478c-4917-bf8c-ac457edd85cb`.
After stopping the previous simulation, both VMs, Presenter and idle UI server,
the operator restarted the UI server, VMs and simulator using Demo Control.
Simulation initially remained unassigned because `vehicle select test` had
not been run; this was not evidence of a failed attachment. After the command
was supplied, the operator confirmed that everything started and worked.
This is operator-confirmed cold-start evidence on the preserved environment,
not a new fresh-overlay or independent Cloud/security qualification. The
earlier measured VDP 15/v3 replay remains the detailed update evidence below.

Local checks executed for this checkpoint:

- Demo Control: 249 tests PASS in 52.652 seconds; VM/Cloud/Builder are fixtures.
- Presenter: TypeScript typecheck PASS and 87 unit tests PASS.
- Runtime tooling: 50 tests PASS; control/protocol/orchestration: 41 tests PASS.
- Existing compiled `viss-dashboard-test`: PASS, no rebuild required.
- Source-only staged scan: 68 implementation files PASS across both repos;
  no binary/private-key/token signatures found by the bounded scan.
- Documentation navigation/metadata gate: PASS, 151 Markdown documents,
  658 stable identifiers and 38 Mermaid diagrams. Explicit stable anchors
  were added for the new plan/checkpoint links.
- Initial sandbox-only test attempts could not bind temporary sockets/read
  processes/write Vite cache; the same tests passed with the required local
  permissions. Product source was not changed to accommodate that restriction.
- New browser/live E2E, native recompilation, image build, signing, upload and
  Cloud mutations are excluded from this bookkeeping step. Previously recorded
  native compilation and operator evidence are retained, not relabelled.

Housekeeping preserves the current `.local` environment (about 8.2 GiB),
`.run` evidence (about 19 MiB), Factory/profile/published artifacts and caches.
The old Gateway worktree `carla-tm-order` remains referenced by the installed
runtime build's CMake cache; it is not safe to classify all old worktrees as
disposable. Historical qualification directories and unrelated dirty/untracked
work are retained, not implicitly retired or published. The inactive 41 MiB
temporary dashboard qualification build `/private/tmp/aosedge-dashboard.sVnt6a`
was permanently removed after its test passed, its source was committed and
`lsof` found no open handles. The installed client is a separate regular file
and remains unchanged. This scratch can be regenerated from source, not
restored as an original directory. There is no backup. The filesystem reported
about 294 GiB available afterward; that global change is not attributed solely
to the 41 MiB cleanup. No branches or worktrees were deleted by this checkpoint.
Push results are recorded in the final handoff.

Historical pending/uncommitted statements below describe their original runs
and do not override this source checkpoint or authorize deferred work.

### Cloud-only Platform observation and dashboard increment — 2026-09-07

The Platform perspective now obtains Unit/component status exclusively through
the existing authenticated Aos Cloud adapter, via `democtl component
cloud-status` without a version. The same operation serves the fixed local
Presenter endpoint. No guest probe supplies this view; legacy UI guest-state
requests now map to Cloud reads, and the guest-log action is rejected.
Cloud Installed is not presented as Running, data READY, Safe Stop or an
inferred functional profile. Read failures and expired observations are
explicitly unavailable/stale.

Checks for this increment: 75 focused Demo Control tests, 8 Presenter-operation
tests, 87 UI unit tests, the UI production build, and the native
`viss_dashboard` test passed. The live Platform endpoint reported Test Online,
`15.0.0` installed, no pending release, and `15.0.0` latest published. Runtime
state and data readiness were explicitly `NOT_REPORTED_BY_CLOUD`.

Only the native VISS dashboard target was built and installed; no Factory,
VDP package, Unit identity or Cloud configuration changed. The dashboard adds
drive mode, Gateway physical stopped-state observation, run/reset context,
freshness expiry and explicit unavailable Brake/Tire Driver Advisory rows.
The advisory chain itself remains deferred, not implied by these indicators.

Simulator stop/start and workspace close/restore used `democtl`. The final
local Presenter observation selected Test; it is `SELECTED_NOT_PROBED`, not
a fresh independent connection proof. Workspace observation found all
surfaces present, with the Controller 30 points taller than the requested
geometry; other surfaces matched within existing tolerance. Operator visual
review remains pending. The stop reported Controller absent and physical
stop not observed; this increment does not claim a new driving/Safe Stop E2E
run. Source changes remain uncommitted; no publication was requested.

### Latest operator-assisted Test replay — 2026-09-07

On the existing Factory .31 Test VM, the operator-assisted sequence
`13.0.1/v1 -> 14.0.0/v2 -> 15.0.0/v3` completed. All preparation, signing,
upload, verification-batch approval and guest/Cloud observations used
`democtl component` commands. Autopilot and Safe Stop were operated by the
user, with movement and button presses confirmed in the conversation.

| Observation | Before Safe Stop | After Safe Stop |
| --- | --- | --- |
| v1 -> v2 | `13.0.1`, slot A, 7-path READY; removal transaction `waiting-for-safe-stop` | `14.0.0`, slot B, 15-path READY/LIVE; process matches slot; `Result=success`, restarts 0 |
| v2 -> v3 | `14.0.0`, slot B, 15-path READY; removal transaction `waiting-for-safe-stop` | `15.0.0`, slot A, 23-path READY/LIVE; process matches slot; `Result=success`, restarts 0 |

Both post-press observations already showed the successor running; no manual
restart, resend, retry or ten-minute wait was used. Guest service start times
were `2026-09-07 01:00:46 UTC` for v2 and `01:03:14 UTC` for v3. The retained
`last-failure.json` refers to the earlier `13.0.1` attempt and predates both
successful installs; it was not deleted or treated as a new failure.

Signed bundles remain outside Git under
`demo-artifacts/aosedge-sdv-demo/components/vehicle-data-provider/`:

| Release / content | Signed bundle SHA-256 | Deployment / verification batch |
| --- | --- | --- |
| `14.0.0` / v2 | `22a83fd5da2f246c3cddb027549bb608b2bc933c029e17fde7c572865c7193a0` | `bbd553b4-eb06-4b45-8268-53a2afee39e8` / `5953ecfe-0875-4b91-8d91-9c3b23ff9142` |
| `15.0.0` / v3 | `685a0bbd7bd0c842276dc0a4a4208b74ceb4a2f8bbe5ecf92207c17dd100ed11` | `2489fb29-8169-4451-8d32-4926c12c0607` / `ff8f8183-f565-4159-8456-f41fca6af283` |

Both signatures verified as RS256 using the configured OEM certificate.
Final Cloud reconciliation reported Test Online, `15.0.0` installed, no
pending component, deployment `done`, and verification batch `Valid`.
Production remained Online on its `0.0.0` baseline with no pending component;
no Production promotion, Unit Set changes or identity/lifecycle operations
were performed. The immutable .31 image and runtime source were unchanged.

This verifies the existing-VM telemetry update path, not a fresh-overlay run,
independent consumer reads, full v3 advisory or reboot/security qualification.
READY is provider-reported, and v3 advisory remains `DEFERRED`. No build,
cleanup, commit or push was performed as part of this replay. The earlier
accepted checkpoint and its outstanding scope below remain historical evidence.

### Current Test baseline — 2026-09-06

The accepted checkpoint is Factory .31 with the operator-confirmed Test
sequence 10.0.0/v1 -> 11.0.0/v2 -> 12.0.0/v3. Both replacements waited while
driving and occurred after Safe Stop, as confirmed by the operator. The final
provider reports 23-path READY/LIVE with zero restarts and a matching slot.
This is a Test functional/visual checkpoint, not full production qualification.

Artifacts stay outside Git under `demo-artifacts/aosedge-sdv-demo/`:

| Artifact | Relative path | Recorded SHA-256 |
| --- | --- | --- |
| Factory .31 | `factory-images/6.1.1-maninblack.31/main-qemuarm64.img` | `a9019f4adfe70499bde339c8e9d95eb8568736b73dc218f6c0e390fbcd28ddf4` |
| VDP 10 / v1 | `components/vehicle-data-provider/10.0.0/vdp-10.0.0-deployment-bundle.tar.gz` | `f2ebeb12bf3560b379c32a3b23c432eeeda24c026be11fe4d4909071d0dac93c` |
| VDP 11 / v2 | `components/vehicle-data-provider/11.0.0/vdp-11.0.0-deployment-bundle.tar.gz` | `103446ed046be38beb3ca936f5763944d785dc23bb22f0f60caa645fafd4e653` |
| VDP 12 / v3 | `components/vehicle-data-provider/12.0.0/vdp-12.0.0-deployment-bundle.tar.gz` | `fd4f36e56fe9985ddbc26e7a4ae46a22e6554f4d5a4d6155c3a17536ce6110d3` |

Digests above come from the existing Factory manifest and each release's
`signed.json`; unchanged artifacts are not rebuilt, repackaged or rehashed for
this source checkpoint. Factory source is Platform
`0bed8b3769b09fbe685ed599ca8d10e6594fbe53`. The Factory manifest retains its
build-time `BUILT_NOT_LIVE_QUALIFIED` record; this document records subsequent
operator acceptance without rewriting immutable build provenance. Frozen
profile inputs 1.0.16/v1, 2.0.0/v2 and 3.0.0/v3 remain required for preparation
of later monotonically increasing Cloud releases.

Outstanding scope: a fresh-overlay repeat from the same Factory SHA; full v3
advisory; independent-consumer validation; reboot/security qualification beyond
the recorded tests. Production FOTA is separately deferred below. No image
build, new release upload or live E2E rerun is part of this source finalization.
Historical sections below describe state at their own timestamps; their
pending/uncommitted wording does not override this current checkpoint.

#### Source finalization and checks

| Repository | Published implementation revision | Scope |
| --- | --- | --- |
| `aosedge-sdv-demo` | `84fbfcddbcb4339d8612dc34d22603987d6de56e` | Mounted-store role initialization, bounded exact-target Cloud reads, Test workflow regressions; no deferred Production validation probes |
| `aos-vehicle-platform` | `0bed8b3769b09fbe685ed599ca8d10e6594fbe53` | Existing immutable Factory .31 source, unchanged in this finalization |
| `carla-ego-runtime` | `93459ee8f39c57b7db05e3a6bbd225de3623c871` | Publishes the previously committed Safe Stop/acquisition-UTC changes (`bbff7f0`) and Traffic Manager port selection (`93459ee`) |

The documentation commit containing this record follows the implementation
checkpoint; use Git history to resolve its exact revision. These source pins
do not claim a new Runtime binary build or change the original build provenance
of the already tested Factory/VDP artifacts.

Checks executed for source finalization:

- Full Demo Control local regression suite: 202 tests PASS in 42.146 seconds.
  Builder/Cloud/VM interactions are fixtures; no live build or lifecycle ran.
- Runtime orchestration-control regression: 9 tests PASS. Native C++ tests and
  binaries were not rebuilt/rerun in this checkpoint; the previously recorded
  live acceptance is preserved rather than relabeled as a fresh run.
- Documentation navigation/metadata gate: PASS, 150 Markdown documents,
  658 stable identifiers and 38 Mermaid diagrams. Four internal anchors were
  corrected; only the documentation gate was rerun afterward.
- Changed-file public-source boundary scan: PASS for 37 Solution/Runtime files,
  checking binary/credential content, private URLs and personal absolute paths.
  Confidential-input commit/push guards and `git diff --check` passed.
- The older whole-repository source scan stops at the pre-existing presenter UI
  asset `apps/presenter-ui/src/assets/icons/connectivity-available.png` because
  it rejects all binary content. The asset and validator were not changed or
  deleted to bypass this unrelated gate. A full repository/CI qualification is
  not claimed; the scoped publication scan above passed.

Only source, tests and documentation were committed/pushed. Factory disks,
overlays, bundles, keys, credentials, raw logs and runtime state remain outside
Git. No VM/Cloud mutation, Safe Stop trigger, source switch or new upload was
performed during this finalization.

#### Subsequent empty-environment cleanup — 2026-09-06

After source finalization, the operator authorized returning the current demo
to its initial CLI state. The existing commands completed in order:
`simulation stop`, `unit deprovision all`, `unit delete all`,
`environment retire`. Both exact Unit/Node identities were confirmed absent
and both role Unit Sets empty. No new Safe Stop functional proof is claimed:
the Controller was already absent when simulation stop ran.

Retire initially preserved local state because historical VDP 11/12 uploads
were marked RESPONDED despite their confirmed approvals. The authorized narrow
fix reconciles the exact deployment IDs and OEM/component/version-scoped batch
reads without repeating uploads or approvals. Both were confirmed and retire
completed. The affected regression suites passed 87 tests; the documentation
gate passed. The original sandbox test invocation could not inspect host
processes; the same tests passed with process-read access, without live VM or
Cloud activity in the tests.

Removed without backup: Test/Production overlays, generated SSH access, the
working factory copy/manifest, stopped source output files and current journal.
Original Factory .31, published VDP artifacts and Cloud releases, role Unit
Sets, credentials, repositories and Builder/caches remain. Previously authorized
original Factory .28/.29/.30 image deletion also completed; .27 was already
retired. Compact artifact metadata remains. This cleanup is not a new E2E run
or proof of the still-deferred Production FOTA path.

#### Housekeeping outcome at source finalization (before the cleanup above)

Removed after confirming clean tracked/untracked/ignored state, no open files
and zero commits outside the published Platform main:

- Platform branch `codex/cm-stream-write-fix` and worktree
  `CarlaSim/.worktrees/aos-platform-cm-stream-write-fix` (about 1.4 MiB).
- Platform branch `codex/factory-29-vss` and worktree
  `CarlaSim/.worktrees/aos-platform-factory-29` (about 1.5 MiB).

Neither branch existed on the remote, so no remote deletion was necessary.
Their commits remain in main; the worktrees can be recreated from Git. No
backup copy was made. Host free space at audit was about 271 GiB.

Preserved pending a separate exact deletion decision:

- Original Factory .28/.29/.30 artifacts: about 6.5 GiB each, 19.5 GiB total.
  They are candidates, not part of the current .31 acceptance; dependency and
  live backing-image checks are required before deleting original artifacts.
- The Solution and Platform `codex/ltvp-finalize-27` branches/worktrees: their
  tips are not ancestors of main. The Platform branch retains release/packaging
  commits for frozen VDP 1.0.16 input; semantic integration must not be assumed
  merely from the newer Factory version number. Remote refs remain untouched.
- Unrelated Brake Health worktree, untracked CarlaSim directories/scripts,
  `.tmp` (about 4.8 MiB) and `.codex-build` (about 25 MiB): ownership/dependency
  closure was not established, so they were not treated as disposable.

Preserved without a cleanup proposal: Factory .31, VDP 10/11/12 and manifests,
the frozen v1/v2/v3 preparation inputs, current Test/Production overlays and
identities, simulator connection, Cloud release history, Builder/caches and
credentials. This was source housekeeping, not environment retirement.

### Production handover completed; FOTA deferred by platform limitation — 2026-09-06

The operator authorized switching CARLA to the existing Production and
installing the tested 12.0.0/v3 without another image or bundle. Executed
`democtl vehicle select production`: COMPLETED, physical Safe Stop confirmed,
both paths blocked before reset, then Production OPEN and Test BLOCKED.
Production's provider is inactive; Test retains its active provider.

Read-only `democtl component cloud-status 12.0.0` confirmed Test
`3d5cdbc8-8b53-42d9-acba-ff49b067cdb5` installed 12.0.0, Production
`fa972f67-990b-4af6-b81c-4d86a8e6634f` Online with factory 0.0.0 and no pending
VDP. Verification batch `e08ed503-d9cf-4a88-8c36-4c8e2942d6c9` is Valid with
arm64 approved. The deployment is `c8a9f996-0fe3-4a29-94e3-0bcc9abfd3b6`.

The operator subsequently reported direct confirmation from the Aos platform
developers: the current release sends updates only to Units belonging to
verification sets; ordinary Production delivery requires a future platform
release. The operator explicitly deferred this work. This report supersedes
the earlier hypothesis based on HTTP 403 from fleet-validation listing. It is
not a claim that a particular future version/date is known or independently
tested. Do not change OEM permissions, create campaigns as a workaround, or
enable verification on Production to claim Production qualification.

Read-only `democtl component logs production` at 10:07:24 UTC showed three
received desired-status messages at 08:12:55, 08:12:56 and 08:13:05 UTC with
configuration/subject processing and no VDP 12 assignment. These preceded
the 08:20:28 arm64 approval. No later receipt appeared in the bounded current
boot journal; CM/SM were active with zero restarts and VDP remained inactive.
This is bounded guest evidence, not access to Cloud dispatcher internals.

No role, permission, Unit Set, campaign or Production approval was changed;
no addressed-send fallback was used. Production installation/Safe Stop gating
is NOT_PROVEN. The last observed simulator connection is Production in Safe
Stop, with both VMs retained; source checkpointing does not move or retire them.

An unrelated Cloud observation defect was corrected during this attempt:
`deployment-bundles/{id}/` supports DELETE, not GET. Exact bundle reads now
select the UUID from the documented collection endpoint. Ordinary component
status no longer probes deferred fleet-validation/campaign APIs. It retains
component/verification/Unit reads and the Production non-target observation.

<a id="factory-31-operator-acceptance"></a>

### Factory .31 operator acceptance after CLI correction — 2026-09-06

The operator ran the agreed democtl sequence and supplied the final
`democtl component status test` output. In response to the explicit question
whether both 10 -> 11 and 11 -> 12 replacements waited while driving and
occurred only after Safe Stop, and whether visual operation worked, the
operator confirmed both transitions and visual acceptance.

The final supplied observation records VDP `12.0.0` / v3 active in slot `a`,
`processSlotMatches=true`, `vdpRestarts=0`, `gate=OPEN`,
`vdpData=REPORTED_READY`, `readPathCount=23`, and
`VDP data READY; source LIVE; reason NONE`. Service result is `success`,
`ExecMainStatus=0`, PID 2005, active since `2026-09-06 08:20:52 UTC`.
Capability manifest SHA-256:
`ae4bfc5604a69992df3122de6e4c088c66f80dc99f03af6c75edcf17474e3e38`.

Evidence boundary: this is operator-confirmed functional/visual acceptance
of the Test update sequence on the existing .31 image, plus the supplied
provider/process status. Intermediate command outputs and transition timings
were not supplied in this confirmation. `PROVIDER_REPORTED_NOT_INDEPENDENT_CONSUMER`
and `advisory=DEFERRED` remain explicit; this does not qualify independent
consumer validation, full v3 advisory, Production updates, reboot/security
gates, or a second clean-overlay lifecycle run. No new Factory build, VM/Cloud
operation, cleanup, commit or push was performed to record this acceptance.
The Demo Control role/Cloud corrections are finalized with the current source
checkpoint; this paragraph retains the boundary of the earlier live evidence.

The earlier failed-run and pending-acceptance entries below are historical.
The remaining agreed repeat is retirement and recreation from the identical
immutable .31 image SHA, with higher Cloud release numbers; it is not recorded
as completed here.

### Factory .31 build and first operator run — 2026-09-06

Factory `6.1.1-maninblack.31/main-qemuarm64.img` was built from Platform
`0bed8b3769b09fbe685ed599ca8d10e6594fbe53`, transferred and frozen at
SHA-256 `a9019f4adfe70499bde339c8e9d95eb8568736b73dc218f6c0e390fbcd28ddf4`
(6,997,147,648 bytes). Five native SM configuration/factory tests passed;
package/image tasks completed. Builder was stopped. Buildpaths QA warnings
were present; this is not a warning-free or live-qualified claim.

The operator uploaded and approved VDP 10.0.0/v1, booted/provisioned both roles
and started CARLA. Test received 10.0.0 and its offline self-test passed.
`vehicle select test` failed with `SOURCE_FACTORY_ROLE_NOT_INITIALIZED:test`.
Read-only observations showed detached/blocked source gates, working DNS and
CM/SM, no configured source inputs, and SM profile `standard`. No successful
VDP activation or completed .31 E2E is claimed. The mount-order correction and
Cloud request reductions are source-level changes in Demo Control; their live
acceptance remains the next fresh operator-driven run using the same .31 image.

Local regression result after these CLI changes: `PYTHONPATH=src:tests
.venv/bin/python -m unittest discover -s tests -q` passed all 202 tests in
36.263 seconds. This includes deferred role initialization for both roles and
exact-target Cloud request paths; mocked tests do not constitute live E2E
acceptance. No VM or Cloud mutation was performed for this regression run.

### Authorized Factory .31 execution — 2026-09-06

Platform main `0bed8b3769b09fbe685ed599ca8d10e6594fbe53` is committed and
pushed, containing the proven factory-placeholder correction and new offline
factory-31.conf. Platform source quality gate passed for 193 files. Demo Control
builds only this pinned revision, runs five native factory/profile regressions
before package/image QA, and retains the warm caches. No provisioned disk,
temporary SM executable or guest credential is an image input.

Agreed next sequence: build/freeze .31 once; fresh Test/Production overlays;
stage VDP 10/v1 before Test provisioning, then 11/v2 and 12/v3 with moving
negative/Safe Stop positive evidence. Operator visual acceptance and a repeat
from fresh overlays of the identical image SHA remain required. This entry is
execution intent, not a claim that .31 build or E2E has passed.

### Pre-.31 environment cleanup — 2026-09-06 06:17 UTC

The user authorized deletion of all current demo VM environments through
Demo Control, and explicitly authorized extending the existing environment
retire implementation for stopped telemetry source outputs/history.
No .31 build or provisioning has started.

`simulation stop` confirmed physical Safe Stop and stopped Controller,
Gateway, keyboard/dashboard group and CARLA. `unit deprovision` followed by
`unit delete` retired these exact identities, with Unit/Node absence and empty
role sets confirmed by authenticated Aos Cloud reads:

| Environment | Role | Deleted Cloud Unit |
| --- | --- | --- |
| isolated .30 | Test | d8aceca5-8044-4f57-8ca3-e8f6dd223a86 |
| isolated .29 | Test | 7cc3327d-b2e2-4db4-8f18-680990773f52 |
| canonical .28 | Test | 4279840f-d81f-410b-abf3-376e69719fc2 |
| canonical .28 | Production | 766f8fcc-e733-4d1c-a928-fb25176a2f4f |

The two older stopped Test VMs were briefly started through `vm start` solely
because the existing deprovision command requires a live guest to disconnect
CM. No new provisioning or update publication occurred. All four VMs and the
canonical owned DNS bridge were then stopped. The borrowed-DNS records in
isolated environments did not acquire or stop that external bridge.

`environment retire` removed four overlays, three local factory copies and
their manifests, four generated SSH access sets, thirteen stopped source-run
directories, empty control directories and the three current-run journals,
without backup. The earlier isolated .28 qualification returned
NO_CURRENT_ENVIRONMENT. Main status now reports Test/Production NOT_CREATED,
source NOT_PREPARED and NO_MANAGED_CURRENT_RUN; a scoped filesystem search
found no remaining current-run journal/overlay/factory-copy files in these
three roots. Final host free space was 284 GiB.

The retire extension uses the existing exact-file intent/recovery mechanism,
checks terminal run receipts and stopped owners, rejects unknown files and
symlinks, and never recursively deletes a source tree. Thirty-five environment
tests passed in 21.077 s; the subsequent borrowed-DNS and exact-retired-send
regressions passed in 1.256 s and 2.548 s. The isolated .29 journal contained
an old UNCERTAIN VDP 2 send to its own deleted Unit. Fresh absence of that exact
Unit allowed discarding the obsolete local send record; delivery was not
claimed and no send/publication was retried. Uncertain global publication
remains blocked. These cleanup source changes are pending, not committed.

Preserved: original immutable Factory artifacts (.28/.29/.30), published VDP
bundles and frozen functional profiles, Cloud release/audit history and Unit
Sets, source repositories/worktrees (including pending SM correction), compact
qualification evidence, credentials, Builder and caches. The prior transient
SM bind/proof on .30 no longer exists because that VM overlay was removed.
This is a clean VM/runtime starting point for .31, not deletion of the reusable
build inputs or of all workspace source copies.

### Moving Test VDP 8 → 9 with Safe Stop — 2026-09-06 05:52 UTC

The preserved .30 Test Unit `d8aceca5-8044-4f57-8ca3-e8f6dd223a86` completed
the next live update with the temporary factory-placeholder SM correction.
All component preparation, signing, publication, approval and guest/Cloud
observations used `democtl` from the isolated .30 demo-orchestrator directory.
The operator selected Autopilot and then Safe Stop in the existing Controller;
no new mode-control interface or standalone helper was introduced.

`component prepare 9.0.0 --profile v3` reused frozen 3.0.0 functional content
with coherent release metadata and 23 read paths. `component sign 9.0.0`
verified RS256 against the configured OEM signing certificate. Signed bundle
SHA-256: `6fa0eec0ebfe2c902c06e98803daa215acc740443e1c4bef07a42c1ac706047f`
(6624628 bytes). Deployment `c08c4189-3bfd-42f8-b524-65b0d1a1551a` is done;
verification batch `9d8c8ecd-2678-4d6a-86ed-10f6bb62dda0` is Valid and approved.
The initial upload execution was rejected before process creation; read-only
confirmation of the Aos-only trust domain and official endpoint cleared that
review. Exactly one upload reached Cloud (HTTP 201).

Negative proof: desired VDP 9 reached CM at 05:50:52.847858 UTC. At
05:51:01.153090 SM was asked to stop VDP 8. A subsequent component observation
showed slot b/version 8/PID 2154 still READY with 15 paths and a remove
transaction in `waiting-for-safe-stop`. At 05:51:59.887 Controller still
reported AUTOPILOT, 19.1197 km/h, brake 0. Thus receiving/approving the update
did not replace the running provider while the vehicle was moving.

After the operator pressed Safe Stop, native events were:

- 05:52:23.307215 UTC: CM accepted VDP 8 inactive.
- 05:52:23.328107: SM called StartInstance for VDP 9.
- 05:52:23.677827: CM entered activating; the full node report kept factory
  VDP 0.0.0 inactive, not activating.
- 05:52:24.602177: CM received VDP 9 active.
- 05:52:24.602382: CM entered finalizing.
- 05:52:24.617942: CM entered none, with VDP 9 installed.

StartInstance-to-update-complete was 1.289835 seconds; activating lasted
0.924555 seconds. No ten-minute timeout occurred in this update. This does
not measure button-to-stop latency: the later Controller observation at
05:52:51.987 confirmed SAFE_STOP, speed 0 and brake 1 on the same run/ego/reset.

Final provider: slot a, version 9.0.0, PID 3255, 23 paths, READY/LIVE/NONE,
NRestarts 0; no transaction or last-failure file. Capability manifest SHA-256:
`21660641d8221329fbb43efc52911213156155703cc1cf6de582021154fc78ee`.
This is provider-reported telemetry readiness, not independent verification
of all 23 consumer values; v3 advisory remains deferred.

Final Cloud: Test Online, installed 9.0.0, pending component null;
component version ID `cc103d0e-ef7d-4b9a-9f2e-fd008ddd33a3`. Production remained
Online at factory 0.0.0, no pending update, unchanged memberships/settings.
SM stayed PID 2864 with NRestarts 0 and the same temporary binary hash below.
SM/CM/provider service results were success; SELinux remained Enforcing with
zero denials in the complete kernel window since SM start. No VM/SM restart,
reprovisioning, image rebuild, Production promotion or backup occurred.

The bounded log projection also contained CM `not found
(instancemanager.cpp:198)` while stopping 8, SM `Remove instance info from
storage failed`, and provider `pthread_getschedparam failed: 1`. These did not
prevent this observed transition but are retained as unclassified diagnostics;
this result is not a claim of error-free logs. No speculative fix was made.

This closes the targeted moving-to-Safe-Stop 8 → 9 proof. Consolidating the
pending correction into a new immutable Factory image and repeating from a
fresh overlay remain separate, uncompleted qualification steps.

### Factory-placeholder correction — 2026-09-06 05:33 UTC

The preserved .30 Test Unit `d8aceca5-8044-4f57-8ca3-e8f6dd223a86` had a stale
preinstalled VDP 0.0.0 instance in activating while the real VDP 8.0.0 was active.
CM WaitInstancesActive consequently timed out at desiredstatushandler.cpp:485.
The trigger was the first source-selection SM restart during VDP 7 installation.

The agreed correction handles the factory marker before transaction conflict
checking, retires it through inactive status when a real release is installed,
and returns failed status on early StartInstance rejection. Demo Control writes
the Test/Production role in vm start before provisioning; source configuration
no longer restarts SM. No CM timeout, Safe Stop policy or VDP payload changed.

`component sm-build test` compiled only SM (1716 tasks, 1708 reused), executed
three ARM64 regressions successfully in 43 ms and stopped Builder. The transient
binary SHA-256 is `a9da669ace53e21a798bf9a9d3fe8988936ae924c7ed9513dd97520a1ae194d7`;
its manifest and tests are under
`$DEMO_ARTIFACT_ROOT/aosedge-sdv-demo/runtime-proofs/sm-factory-placeholder`.
Source is the pending runtime delta on Platform `c3e0858`, not a new Factory image.

One `component sm-apply test` replaced only the binary via
`/run/democtl-sm-factory-placeholder/aos_sm_app` and
`/run/systemd/system/aos-sm.service.d/91-democtl-sm-factory-placeholder.conf`.
The Factory config and persistent public inputs were unchanged. These exact
temporary proof files remain intentionally installed and disappear at VM reboot.

At 05:33:22.742104 UTC CM accepted factory VDP 0.0.0 inactive; at
05:33:22.742111 it entered finalizing; at 05:33:22.828634 it entered none.
The blocked native update finalized in 86.530 ms, without another upload,
provisioning, CM restart or ten-minute wait. VDP 8 remained in slot b, PID 2154,
with its 15-path profile and zero restarts. A later observation reported
NOT_READY/TELEMETRY_DISCONNECTED when the separate Controller session completed
at 05:34:34.915 UTC (configured maximum session duration 3600 seconds).
`simulation stop`, `simulation start`, and `vehicle select test` restored the
source as run `e1e178ac-1975-4eb2-94bf-64bc9f595069`, assignment generation 1.
At 05:41:25 UTC verified VISS frames advanced 1571 to 1573; the following VDP
read confirmed READY/LIVE/NONE, same PID 2154 and zero restarts. Reconnecting
the source preserved SM PID 2864, proving no second SM restart. SM has zero
automatic restarts,
SELinux Enforcing, complete fresh kernel window and zero AVC denials.
Final Cloud read: Test Online/8.0.0 installed, pending component null;
Production Online/factory 0.0.0 with no pending update or membership changes.

The host role fixture and four CLI/API boundary tests pass. The subsequent
moving-to-Safe-Stop update is recorded above. Clean Factory rebuild,
fresh-overlay repeat and full operator E2E remain outstanding; this transient
proof is not Factory qualification. No
Production mutation, source commit/push, image build, cleanup or backup was
performed for this correction.

### Earlier checkpoints

Latest confirmed increment: Test VDP 7.0.0 (v1 content) is READY/LIVE/NONE,
Cloud installed=7.0.0, pending=null. Native Stop returned at
03:48:35.001468 UTC and Start was called at 03:48:35.747153 UTC; the new
installation was committed at 03:48:36.825068 UTC. The native stop-completion
fix is committed in Platform `e5e9ffd`, with seven targeted regressions passing.
The Gateway Traffic Manager port delta is consolidated in main `93459ee`.
These close the earlier Stop/Start and source-consolidation issues below.

Factory .30 source `c3e0858` packages persistent public source inputs and
role selection, with missing/Production role retaining standard freshness.
The new host-side packaging fixture, source fixture, CLI/API boundary tests
and 15 source-operation tests pass. The ARM64 configuration tests pass 2/2
in 2 ms. SM compile passed 1716 tasks (1706 reused); package QA/build passed
6367 tasks (6332 reused); image QA/build passed 7547 tasks (7532 reused).
`democtl image build 6.1.1-maninblack.30` assembled and exported the immutable
6997147648-byte image with SHA-256
`b33165364be8798c05762a5f2523a350167c0865b77ed25e655c65b58cc3791a`.
Transfer digest matched and Builder stopped cleanly. Artifact directory:
`$DEMO_ARTIFACT_ROOT/aosedge-sdv-demo/factory-images/6.1.1-maninblack.30`.

Solution checkpoint `6c831e9` owns the release command, durable source input
integration and associated documentation. An isolated terminal-equivalent
Test environment was created at
`$WORKSPACE_ROOT/aosedge-sdv-demo-qual-30.G9eUof`; it contains a factory copy
and fresh overlay, not the .29 provisioning/SSH state. Local create/start
completed; first boot/enrollment took 60.37 seconds, SSH/DNS are ready and
the unprovisioned state was confirmed. New local Test VM ID is
`7a2d4419-5a37-4838-ab5c-ed0d2792b9e8`. Provisioning and live component E2E
remain in progress; these are not yet operator acceptance results.

The previous .29 Test VM was stopped through Demo Control in 3.99 seconds,
then removed only from Test Vehicles (10.33 seconds). Its disk and Cloud Unit
are retained; other memberships are unchanged. Its expired Controller was
already absent, so simulation stop records physical stop `NOT_OBSERVED`, not
a new successful Safe Stop test. Production remains outside these mutations.

The recorded 2026-09-06 03:05 UTC observation is Test VDP 6.0.0 active,
23-path READY/LIVE/NONE, Cloud installed=6.0.0 and pending=null. Production
was unchanged. This proves the narrowed telemetry update, not complete v3
advisory, mTLS or a clean Factory release. Earlier functional v1/v2 releases
4.0.0 and 5.0.0 reported 7 and 15 paths respectively.

Factory .29 already exists and remains immutable, with SHA-256
`fb6f77cb280b0836ba0979373260af50a9b30cdb1bf9b3365fb6b2f775b2cf6a`.
Its SM is not the temporary demo-5s SM used for the successful latest update.
The next changed Factory image must therefore be .30, not an overwritten .29.

The transient Test SM uses runtime mounts and systemd LoadCredential for the
public CA/binding. It is not reboot-persistent Factory integration. The
demo-5s profile is an explicit Test demo exception; the standard 250 ms
default and Production policy remain unchanged.

## Source boundaries to preserve

- Solution main: Demo Control CLI/API, lifecycle/component operations, tests,
  contracts, documentation and DNS ownership integration.
- Gateway main: Controller orchestration, physical Safe Stop correction and
  UTC acquisition semantics with associated tests and contracts.
- Gateway `codex/ltvp-traffic-manager-order`: actual live native Gateway build
  source, including UTC acquisition changes. This branch explicitly selects
  the Traffic Manager port; canonical main is not yet an exact replacement
  for this build. Consolidate the existing branch delta before claiming a
  reproducible canonical Gateway release.
- Platform `codex/factory-29-vss`: explicit demo-5s configuration/evaluator,
  targeted tests and transient-proof record. This checkpoint does not alter
  the published .29 image and does not fix the Stop/Start lifecycle conflict.

Local source checkpoint commits: Platform `70f91f4`, actual Gateway build
branch `d1838ab`, canonical Gateway/Controller `bbff7f0`. The Solution commit
containing this record captures Demo Control and its associated documentation.
These are engineering checkpoints, not clean-build acceptance tags; no push
was performed.

The earlier recorded test evidence is retained: SM 59 pass / 2 explicit
provider skips, Demo Control 183 local tests pass with a subsequent 41-test
component rerun, and three native Gateway UTC tests pass. These results are
not a claim that every later checkpoint file was independently requalified,
or that the complete combined source has passed a new clean-build E2E.

Generated images, compiled executables, bundles, credentials, runtime journals
and local artifact stores are excluded from source commits. Existing published
bundle identities and immutable artifact hashes are not rewritten.

## Why the update took roughly ten minutes

The observed failed StartInstance at 02:52:17.610 UTC returned
`a different component transaction is already active`. StopInstance had
started an asynchronous remove transaction and returned before it completed;
the native launcher proceeded to StartInstance while that transaction was
still active. The automatic second launch at 03:02:18.272 UTC succeeded.

Pinned AosCore library revision
`60cb83535f773762c61ac5f544b31b7b88c502e3` contains two relevant CM waits:

- `src/core/cm/updatemanager/desiredstatushandler.hpp`: cWaitActiveTimeout,
  ten minutes; WaitInstancesActive waits while an instance is Activating.
- `src/core/cm/launcher/nodemanager.hpp`: cStatusUpdateTimeout, ten minutes;
  scheduled/resend operations wait for node instance statuses.

The source and timestamps establish a native lifecycle/status recovery issue,
not an intentional ten-minute democtl delay or a demonstrated Cloud timer.
They do not uniquely identify which wait was responsible for this particular
retry. Node status notification is attempted even when updating the instance
manager returns an error; do not infer its absence solely from a not-found log.
Do not shorten unrelated timeouts as a substitute for fixing the known
StopInstance/StartInstance transaction contract.

## Authorized next release gates

1. Preserve these source checkpoints and existing proof. Do not rerun already
   passed tests merely to repeat evidence during bookkeeping.
2. Resolve the known StopInstance/StartInstance conflict with one targeted
   asynchronous stop-then-start regression test. Consolidate the Gateway
   build-source delta and durable public CA/binding lifecycle. Do not broaden
   Production access or silently apply the Test-only freshness exception.
3. Build Factory .30 from pinned, committed sources, using retained offline
   build caches. Publish one immutable image and its source/artifact hashes;
   never package a provisioned overlay or copy transient /run state.
4. Engineer E2E exclusively through democtl: fresh environment, provision,
   correct role sets, Online, CARLA/Gateway selection, physical Safe Stop,
   functional v1/v2/v3 delivery and startup, then lifecycle teardown.
   Check the demo profile and public inputs survive the intended VM lifecycle.
5. Operator repeats E2E through documented democtl commands using a fresh
   overlay from the same .30 image SHA, without rebuilding the image.

Proposed component versions are 7.0.0/8.0.0/9.0.0 for engineer v1/v2/v3 and
10.0.0/11.0.0/12.0.0 for the operator repeat, subject to the existing Cloud
release state when the agreed cycle starts. Version progression is monotonic;
functional content is reused. Stage and approve the next v1-content release
before a fresh Unit joins the delivery set, so Cloud's latest release does not
skip the initial v1 stage. All preparation/signing/upload/approval uses democtl.

The operator authorized the above release plan and the StopInstance contract
correction. Continue the remaining build/E2E gates through Demo Control. No
Production mutation or push is implied by this checkpoint.
