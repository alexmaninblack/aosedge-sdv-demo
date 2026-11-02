<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native Vision Services — V2/V3 Boundary Packet

- Status: Accepted by the operator; implementation and same-VM verification authorized
- Version: 0.7
- Prepared: 2026-11-02
- Owner: SDV Lab integration, Vision services and OEM platform
- Parent: [Vision implementation plan](vision-pilot-single-node.md#v2-freeze-interfaces-and-update-the-design-chain)
- Accepted basis: [ADR 0019](../../architecture/decisions/0019-vision-pilot-single-node-lab.md),
  [Camera requirements](../../requirements/components/camera-access.md) and
  [permanent Camera acceptance](vision-ingress-permanent-delivery.md#permanent-ingress-acceptance-result)

## Why this boundary must close once

Camera Access is qualified on the same `.5` Vision VM, including actual native
read and revocation. It is not a pair of functional AI services. The previous
three-model preview is an SSH engineering worker, not an Aos service or an
approved product result transport. Do not relabel it or reopen camera delivery.

The accepted architecture explicitly leaves three product interfaces open:
Perception-to-Assessment transport, the approved Vision dynamics input, and
Assessment-to-Gateway result return. In particular, HLA and ADR 0019 require a
separate approved dynamics contract; ordinary camera access cannot grant speed
access, result publication, an arbitrary VISS connection or motion authority.
This packet freezes those decisions together before implementing their users.

On 2026-11-01 the operator accepted S1–S6 in full and authorized implementation
and checks on the same Vision VM, preserving data and VDP/Brake/Tire. Build on
SSD; do not rebuild CARLA or Main Factory. Routine exact-scope source, targeted
compile, signing, native delivery and verification need no further prompts.
This is not authority to weaken security, reset/reprovision the VM, promote
Main, publish a public Vision artifact or claim unexecuted acceptance gates.

## Preserved target and exclusions

- M4, existing `SDV-Vision-Camera-Image-Lab-Data` only: Unit
  `af6d074a-6ce1-49ba-b613-0476e7b6d1b5`, VM
  `89273f16-4be0-4b22-b4cb-58d08533c8bc`.
- Preserve that VM, Unit/node, Camera store, data, enrollment, all four retained
  instance roots, current DMG, dependencies, Builder and caches.
- Retained VDP/Brake/Tire VM, services, Subjects and data are outside the packet.
- No new VM, reset/deprovisioning, staging fallback, multi-node work, GPU/ROS,
  CARLA/Unreal/Main Factory rebuild, Main promotion or public Vision release.
- Source, targeted compile and package work stay on the development SSD. Model,
  native service, replay, simulator and UI execution stay on M4 internal storage.

## Accepted decisions

### S1 — Keep two independently deployed application services

This is the already accepted composition, not a request to reconsider it.

Create the planned `vision-pilot-services` source repository, Apache-2.0 for
original code, pinned upstream without submodules, separate Perception and
Assessment targets/manifests/versions. Public source creation follows project
policy; no model weights, binaries, keys or runtime data enter Git. Do not
publish an integrated installer or change option A.

Perception owns bounded JPEG decode, exact calibrated/model-specific
preprocessing and all three FP32 models. Assessment owns fusion/tracking and
shadow interpretation/planning. Neither opens CARLA, Cloud producer, VISS,
advisory or actuator interfaces. No service per model and no third AI service.

### S2 — Native local exchange, not application network credentials

Reuse existing `vision-camera-read` for Perception only. Add an internal
nonroot OEM Vision exchange adapter **inside the Camera Access platform
package**, separately isolated from the image-admission core. It is not a new
Cloud service or lifecycle owner. Keep the Camera read/OEM protocols unchanged.

Use native Aos named resources and closed Unix-socket operations for:

| Resource | Sole application consumer | Operations |
| --- | --- | --- |
| `vision-perception-publish` | Perception | Publish raw typed Perception result only |
| `vision-perception-read` | Assessment | Read latest compatible Perception result/status |
| `vision-context-read` | Assessment | Read frame-bound authorized dynamics/vehicle profile |
| `vision-assessment-publish` | Assessment | Publish typed interpreted result only |

Each resource has its own projection/group and at most one allocated instance.
Native Aos remains allocation/revocation authority. Verify DAC, peer identity,
namespaces, supplementary groups and Enforcing SELinux on actual native
instances. No shared application key, parallel identity database, generic file
access, arbitrary socket path or manual crun substitute. A read-only mount by
itself is not permission proof. The broker accepts no camera-selection, control,
Cloud, update, file or shell operation.

Retain one latest raw result, one latest interpreted result and at most 128
bounded context records for frame matching. Use a 4-byte network-order length
followed by strict JSON, at most 64 KiB/result and 4 KiB/request/context record;
an absolute two-second request deadline. Count replacements/rejections, never
build an output FIFO or retain raw video. Exact schemas and native paths become
the executable contract after acceptance, before producer/consumer code.

### S3 — Dynamics from the selected Gateway, not the Brake/Tire VDP

The OEM adapter obtains only factual ego speed and a trusted static vehicle
geometry/profile from the same selected Vision Source. Gateway supplies speed
in metres/second with the original physical frame and simulation sample time;
it retains at most its bounded frame-history window. Simulation ground-truth
object labels, lanes and lead position are never inputs to inference/fusion.

Use a Vision-only read route on the existing enrolled Gateway TLS listener:
`GET /vision/v1/context`, with a closed source/epoch/frame query. It returns
only that actual frame's speed/status plus the digest-bound vehicle profile,
or explicit unavailable. Reject unknown fields, foreign source/epoch, replay,
missing records and arbitrary VSS paths. No interpolation, old-value
re-timestamping or zero-speed default. Exact frame matching is preferred over
arrival-time joins; if unavailable, Assessment withholds dynamics-dependent
output rather than silently choosing a nearby sample.

Add an explicit selected-Vision-Unit `vision-context-read` scope. It does not
derive from camera permission or grant VISS Set. A separate narrow OEM adapter
domain uses the existing Source-owned enrollment/credential lifecycle; apps and
Camera core receive no TLS key. Bind to the selected Unit/node/generation,
drain on detach and deny other roles. Do not rotate or copy Main credentials.

Front-axle/CoG distance, coordinate conventions and speed limit must come from
an exact trusted vehicle profile or remain unavailable. Never borrow upstream
`L=2.860` or its speed-limit constant as measured CARLA geometry. Missing speed
or geometry invalidates shadow planning, not camera/perception status.

### S4 — Typed return to the Gateway, with no actuation

Use `POST /vision/v1/results` on the same existing TLS listener. Only the
selected Vision Unit's OEM exchange adapter receives an explicit
`vision-assessment-publish` scope. No new listener, application TLS key, public
URL input or inference-to-control socket. The local service cannot choose a
host destination or request another operation.

Gateway validates the strict schema, source/epoch/frame/calibration, producer
epoch, compatibility, finite numbers, count/byte bounds and rate before caching
one latest interpreted result. Duplicate delivery is idempotent by producer
epoch/sequence; conflicting content for an existing identity fails closed.
At most ten results/second; a slower producer never causes frame substitution.
On loss/stale/reset/replacement, clear valid display data. Old results cannot
attach to a newer live image or mutate throttle/brake/steering/advisories.

Native Driving Control may display full server-side associations and matched
overlays. Browser/Presenter receives only opaque references and bounded status;
full Unit/source/node/certificate IDs remain server-side. UI implementation
follows transport/native proof rather than screenshots or fabricated results.

### S5 — Explicit time, validity, calibration and independent versions

Freeze three closed versioned DTOs: raw Perception, frame-bound Vision context
and interpreted Assessment. Carry the exact capture-pair references, current
component/source/calibration and producer epochs, original sensor/world times,
precision/model/preprocessing identities and service compatibility.

Keep the accepted real 80–120 ms AutoDrive pair. Distinguish that capture
interval from elapsed simulation time between processed results. Call both
upstream fusion modules with the latter real positive delta; never silently
take their nominal 0.10-second fallback. Reset temporal state on producer/source/
calibration changes, discontinuity, time regression or gaps over one simulated
second. First output after reset is explicitly warming for temporal estimates.

Preserve all 64 raw AutoSteer positions/confidences, bounded AutoSpeed boxes
and class probabilities, and AutoDrive normalized distance/raw curvature/
presence probability. Missing/invalid/stale/incompatible differs from valid
no-detection. A 150-m upstream free-road sentinel maps to `present=false` and
nullable distance, never a detected lead object at 150 m. Interpreted world
coordinates use forward metres and left-positive lateral metres.
The raw AutoSteer `h_vector` is a finite height/mask, not a calibrated 0–1
probability. Preserve its values and the upstream `>=0.5` mask; do not add a
sigmoid/clamp or reject a finite value merely because it is outside 0–1.

Reuse upstream fusion/planning algorithms rather than introduce another
heuristic under their name. The shadow planner's **processing elapsed time**
must be made explicit; keep its prediction-horizon step separate. Preserve
thresholds/model semantics and prove deterministic/reference tolerances before
claiming behavioral parity. Missing dynamics/geometry, invalid fusion or stale
input suppresses a valid plan. Any acceleration/steering prediction remains
display-only, with no actuator writer or control permission.

Freeze calibration from the actual rigid camera and exact preprocessing maps.
The earlier moving preview used an approximate local plane, not qualified
whole-route calibration. An invalid plane/mount must produce calibration
unavailable; visually plausible overlays are insufficient. Use a declared
bounded stationary/planar reference before moving characterization.

Compatible SOTA of either service must not update the other. Schema/calibration/
model-profile incompatibility withholds output; no automatic rollback,
replacement or unrequested deployment. Precision remains FP32 initially; INT8
needs separate comparison, not a performance shortcut.

### S6 — Build, delivery and acceptance envelope

Reuse verified model/runtime inputs at upstream
`e7e5c614832f175f1f9f10a0d0c0df2559ff2c38`. The retained engineering payload is
145,774,349 compressed bytes / 303,758,366 extracted bytes, not a verified Aos
closure. It already exceeds the old 256-MiB binary-service layout. Use an
isolated **512-MiB extracted Perception profile ceiling**, including interpreter,
libraries and models; retain all path/link/digest/architecture/license checks
and existing limits for every other profile. Measure the actual closure before
qualification and refuse overflow, rather than raise the ceiling automatically.
Assessment gets its own measured closure/manifest and no duplicated model weights.

Preserve the current 4-vCPU/4-GiB VM. Freeze native service CPU/DMIPS and memory
quotas from isolated measurements and the real node-capacity mapping before
publication. Do not increase VM resources or weaken a freshness policy to pass.
Initial characterization remains 180 seconds, not soak or safety acceptance.
The five-results/s and 500-ms capture-to-display goals remain unproven; previous
moving results were about 4.3/s and measured only partial-path age.

The packet's writable boundaries are this integration branch, the
existing Gateway/platform Vision worktrees and the new service repository.
Keep one writer per owner, freeze exact revisions and fan in service → platform/
Gateway → integration selections. No edit to prepared build sources.

After source/unit and targeted reversible native proofs pass, permit at most
one warm incremental **Vision-only** image/rootfs successor if required by the
new accounts/resources/policy, with a proven stopped-VM recovery checkpoint.
Use a new immutable version, normal native update and same retained Unit/VM.
Do not reuse `.5` for changed bytes or assume Camera OEM payload alone can
install rootfs-owned resources. First versions are Perception `0.1.0`,
Assessment `0.1.0`, Camera Access `0.1.2`, Vision-only rootfs
`6.1.1-vision-camera.6` if required, and signed host bootstrap `0.6.0` if its
tooling changes. Check absence/collision before preparing any changed bytes.
Use only a distinct Vision-only `SDV Vision Pilot` Subject, containing this Unit
and these two services; reuse only an exact verified owned definition, never
by title alone. Freeze authoritative Cloud IDs, source pins and artifact
digests in the implementation receipt before signing. Unknown effects or an
occupied version fail closed. Reconcile unknown effects; never blindly retry
an upload. Routine exact-scope source/build/deployment steps need no additional
operator prompts.

## One ordered implementation and proof ladder

### Accepted frame-calibration completion

On 2026-11-01 the operator also accepted the bounded calibration completion:
Source/Gateway derives calibration from the real rigid CARLA camera. Perception
obtains only calibration through `status` of its existing publish resource;
Assessment obtains the same profile through its existing `context-read`.
No new endpoint/resource/application key, dynamics grant for Perception or
motion authority is introduced. An unusable frame calibration is unavailable.

Separate the immutable **camera/model calibration profile** from its evaluated
**per-frame planar mapping**. The profile binds actual intrinsics/rigid mount,
the exact pinned upstream model-view matrix, coordinate convention and the
declared planar projection/validity policy. Its ID is SHA-256 of the complete
strict UTF-8 profile document, not only a mount-name string. Each actual
physical-frame context binds the evaluated `rawToModel` matrix and validity to
that original image/time/hash. Pose changes are frame geometry, not a new
intrinsic/mount calibration; a changed profile ID still resets temporal state.
The two AutoDrive images use their own frame mappings, not the current image's
mapping twice. Never reuse the upstream example OpenLane ground homography.
AutoDrive uses `rawToModel = inverse(V) * H_raw`, whereas AutoSteer/AutoSpeed
fusion uses the current frame's `resizedToVehicle = H_raw * T`, where `T`
undoes their top-crop/resize. Keep the pinned training-view `V` as
`modelViewToVehicle` in the profile; it is not the fusion homography for these
two models. This matches upstream `InferencePipeline::set_H_resized`.

The initial scope is an OpenDRIVE local planar reference, not qualified learned
accuracy or a guarantee about arbitrary rendered terrain. Source verifies
finite positive camera/plane geometry and a declared 15–150 m reference patch:
at most 0.02 m map-plane residual and 0.5 degree normal difference. Missing or
incompatible map/camera/plane facts produce explicit unavailable and no valid
model-dependent output. These engineering bounds do not change safety,
control, freshness or model thresholds. Each matrix remains bounded, finite
and nonsingular; consumers verify the full profile digest and exact captures.

`status` without capture arguments still returns only readiness/epoch.
Perception's calibration status accepts a closed binding plus the exact pair
references, returns no dynamics/vehicle geometry, and uses the same 4-KiB
deadline/size guard. Other role status operations cannot request this data.
Assessment's context adds only this bounded calibration projection. Browser
projection remains opaque; full associations stay server-side/native.

### Execution sequence

1. S1–S6 are accepted; cascade current HLA/Flows/requirements/D4 and freeze
   executable schemas, resource roles and machine-readable source/dependency pins.
2. Extract model/fusion data types, separate headless targets and build only
   affected closures on SSD. Unit-test preprocessing, outputs, time/reset,
   no-detection, bounds, compatibility, calibration and no-actuation negatives.
   Keep third-party notices/SBOM and weights outside Git.
3. Prove exact broker/resource/credential/policy behavior transiently on the
   same Vision VM. Require first-create, repeat, real functional read/publish,
   wrong-role denial, revocation, restart, scoped AVCs and stock restoration.
4. Freeze measured ARM64 closures, quotas and the narrow permanent platform
   delta. Build/sign once only after all known rapid-debug blockers close.
   Check the recovery path before any native image update. No speculative
   whole-Factory/CARLA rebuild.
5. Through existing authorized OEM/SP owners, preflight exact isolated Unit,
   verification recipient and a Vision-only Subject. Publish each independently
   versioned service serially, with recorded intent and authoritative/native
   reconciliation. Diagnostic reader `0.1.7` stays without camera allocation.
6. One scenario characterizes licensed calibrated replay, then real CARLA
   capture → Camera → Perception → Assessment → Gateway. Check actual native
   UIDs/groups/mounts/quotas, independent SOTA, loss/reset/stale/incompatible
   states, pixel/frame correlation, measured fit and containment.
7. Add matched native/Presenter screens and run visible semantic UI tests only
   after API/native gates. Finish with owned Source/CARLA/VM/helper shutdown,
   released listeners and unchanged retained journals. Keep data and evidence.

No implementation gate is claimed passed by accepting this packet. Acceptance
closes the design choices, not a failing security check, an unmeasured artifact
digest or full Vision E2E.

## Current implementation checkpoint

The native Perception and Assessment successors are `0.1.1`, application
source `a10c6f354866e5d3e839ee59a18344bb7cad96df`. SSD closure `closure-09`
contains 345,724,486 and 57,595,214 extracted bytes respectively. Recipe,
Debian, model/runtime and header-library notices and the case-collision notice
map are retained. `signed-04` verifies both official SDK signatures against
their prepared configuration/files. No weights, runtime binaries or keys enter
Git. The prior versions remain immutable history, not new build inputs.

### Completed native gates on the retained M4 Vision VM

- `vision-services-native-live-11` proves the real calibrated route through
  native Camera resources, all three Perception models, Assessment and Source.
  The 180.01-second characterization observed 768 unique results (4.2663/s);
  sampled capture-callback-to-observation age was 441.6 ms median, 559.5 ms
  p95 and 615 ms maximum. This is a partial-path observation, not hardware
  camera latency, exact camera FPS, full-display latency, accuracy or soak.
  The five-results/s and 500-ms full-path goals are **not qualified**.
- Gateway `34bdea3dfb254dc7aedf34c7915054a29898837e` uses the measured Unreal
  physical rigid-camera convention. The twelve same-snapshot samples match
  within 0.000009 m; the generic installed SDK composition differed by
  0.05786 m. The original 0.001 matrix and 0.02-m/0.5-degree plane bounds
  remain unchanged. Six targeted Gateway C++/TLS regressions pass.
- Native UID/GID, named resource mounts, NNP, capabilities, namespaces,
  CPU/RAM/PID/FD/tmp limits and fresh scoped AVC checks pass. The fixed
  [allocation](../../../contracts/vision-vm/services-allocation.v1.json) remains
  Perception 7,000 DMIPS/768 MiB and Assessment 250 DMIPS/128 MiB, on the
  unchanged 4-vCPU/4-GiB, 10,000-DMIPS VM.
- `native-live-15` proves wrong-role/protocol denial, Unix-only socket
  restrictions in actual native identities, input-loss invalidation and
  recovery without restarting the applications. The fixed C service entry
  now installs the same AArch64 seccomp filter before Python, closes inherited
  descriptors and denies non-Unix socket families and io_uring entry points.
  `native-live-16` observes Seccomp=2 in both real `0.1.1` main processes.
  Empty Core allowedConnections alone was not an egress-denial proof.
- `native-live-16` serially publishes and observes independent native SOTA
  for both `0.1.1` versions. The other service's PID, version, source and
  resources remain unchanged each time. Both successors are READY and
  desired only by the recorded Vision Subject/Unit. Never replay those uploads.
- `vision-services-recovery-01` rehearses stopped-overlay recovery on the
  same VM, including a marker write/restore/reboot and retained Camera store,
  enrollment and identity checks. The checkpoint and original evidence remain.
- `native-live-17` proves supported native CM install and SM image cache
  paths on the existing downloads filesystem. Original caches, databases,
  application state/storage and the Camera backing file remain preserved.
  No disk/LVM resize, VM resource increase or weakened acquisition guard is
  used.
- `native-live-19/group-alias-acceptance.json` reconciles the live short-name
  role proof. Linux group names are at most the Builder shadow tool's 24
  characters; resource names, numeric group IDs and permissions are unchanged.
  Both native successors produce a valid result with fresh scoped AVC count
  zero. The original NOT_COMPLETE report is preserved: its final assertion
  compared JSON object order instead of resource-name mappings. The separate
  derived receipt binds the original report and actual configuration/security/
  functional evidence; no live run is relabelled or repeated.

The normal Source-owned broker lifecycle also passes: separate nonroot
`vision_exchange_t`, NNP/all-zero capabilities, four role sockets, read-only
credentials, idempotent start, wrong-root denial, restart and reconnect.
Completed reversible campaigns restore stock configuration/policy, preserve
the same Unit/VM and all four retained journals, then stop Source/VM/helpers.

### Permanent platform and visible acceptance

The default-off Vision platform delta includes the proven five-resource Core
capacity, standard IAM cpuInfoPath projection from the real four-vCPU topology,
fixed native accounts, short internal role groups and supported CM/SM cache
paths. Main's flags, quotas and privileges do not change. No manual crun
application, rootfs remount, unsafe rebase, database rewrite or new credential
interface substitutes for native ownership.

Installed boot was inspected read-only again. Its current compressed archive
differs from an older receipt, but all four installed update helpers exactly
match the pinned meta-aos sources. The explicit compatibility receipt preserves
both archive digests and this distinction; no boot update is required or built.

The one warm incremental Vision-only rootfs successor `6.1.1-vision-camera.6`
is built (`rootfs-fota-09`), officially signed/published and natively committed
on the same retained VM. It booted read-only from /dev/sda3 with no pending
rootfs/update flags and healthy Core; Camera identity/store/enrollment/data are
preserved. The first attempt's Cloud HTTP 503 is preserved, not retried as a
publication. Read-only reconciliation found an open defect: Cloud's Unit
inventory lists Boot and Camera but omits Rootfs, although native CM/SM report
the exact new rootfs component/version active. `permanent-rootfs-close-01`
records this as **NATIVE_ROOTFS_COMMITTED_CLOUD_INVENTORY_MISSING**, not PASS,
and normally stops the committed VM. Do not promote a release or fabricate a
Cloud inventory row to hide this disagreement.

The independent, already authorized Camera OEM update `0.1.2` then passes on
the same store (`vision-services-camera-update-01`), including exact installed
entry bytes and Cloud-installed version, physical Safe Stop, retained data and
normal Source/VM cleanup. Rootfs's aggregate Cloud-inventory defect remains
open; it is not counted as passed by continuing the independent native/API/UI
checks. No second rootfs/manufacturing/boot image is built.

Signed host `0.6.2` is the calibrated transient candidate, retaining the
immutable `.5` manufacturing input. Signed `0.6.3` carries the coordinated
short-name observer and read-only Vision Presenter; `0.6.4` isolates each HTTP
observation's SourceDriver session/deadline from other reads and API actions.
The new view uses only the
existing loopback Presenter snapshot route and the existing same-UID Source
status socket: no additional product listener, operation or application key.
The Source Vision projection remains at most 3,072 bytes inside the unchanged
4-KiB response. Full Unit/source/node/certificate associations remain server-side.
A bounded 16-point ground-plane plot is explicitly not an overlay on a newer
live image. Missing/stale input clears the prior valid display.

The new view passes four focused units, all 73 Vision units and 62 existing
Presenter units. Live acceptance then ran against the permanent `.6` rootfs,
Camera `0.1.2` and native Perception/Assessment `0.1.1`, without transient
platform, policy, identity or resource overrides:

- `vision-services-permanent-api-ui-01` completes the native/API portion,
  including broker lifecycle, independent Cloud/native version reconciliation,
  quotas/identities and a 180.19-second stationary calibrated characterization.
  It observes 774 unique results (4.2954/s); capture-callback-to-observation age
  is 432.9 ms median, 547.1 ms p95 and 605.3 ms maximum. These are **partial-path**
  measurements, not the five-results/s or 500-ms capture-to-display goal.
  Its original final UI-helper import failure remains NOT_COMPLETE. The
  following UI receipt binds the completed API/security/characterization
  files by SHA-256; it does not relabel the failed aggregate or repeat inference.
- `vision-services-permanent-api-ui-03` passes actual **headed** Chrome on the
  unlocked M4 desktop: Overview, Perception and Assessment, both service
  versions, advancing opaque references, no full browser identifiers and stable
  element rectangles. Stopping real camera ingress clears the path/lead/plan;
  restarting it produces a new valid reference without restarting either app.
  Fresh scoped AVC count is zero. Five actual browser screenshots are retained.
  The preceding UI attempt passed its assertions but failed process-pipe
  cleanup; that receipt remains failed. The corrected final campaign confirms
  browser/server/process cleanup as well as the visual assertions.
- The final visible campaign takes 121.90 seconds overall: VM start 37.48 s,
  warm Source start 30.88 s and semantic browser actions/loss/recovery 9.74 s.
  The API campaign takes 341.87 s including its mandatory 180-s sample and
  preserved import failure. These are scenario times, not the total overnight
  development, compilation, signing, diagnosis and evidence-collection time.

Owned Source, simulator, browser, localhost server, VM and awake helpers are
stopped at the end. The same Vision Unit/VM and data remain; all four retained
instance journals are unchanged. No Docker restart or public release occurs.

Visible browser coverage is all three **new Vision views**, not native Driving
Control button automation, a camera overlay, a moving-route accuracy test or
the retained Main VDP/Brake/Tire screens. Perception's cards explain the three
model roles; they do not pretend to show three separately deployed services or
raw model tensors through an unapproved browser interface. A review finding
remains: camera-ingress loss projects `SOURCE NOT SELECTED` while the Source
owner remains running; the diagnostic wording needs clarification. Previous
valid results do clear, and layout does remain stable.

Rootfs aggregate Cloud inventory remains a separate required gate until its
explicit reconciliation receipt confirms the installed component. The native
commit, Camera delivery, API and browser passes cannot stand in for that gate.
Do not publish a Vision installer or promote Main on these bounded results.

### Rootfs catalog defect and bounded follow-up

The final read-only `vision-services-root-cache-11` confirms a healthy native
`.6` read-only root, Camera `0.1.2`, Enforcing policy, no update transaction or
temporary pending files, and CM restart count zero. The same Vision identity
and all retained journals remain unchanged. Reading only the exact Rootfs rows
of CM's `imagemanager` table finds **no Rootfs catalog row**. The five original
OCI index/manifest/config/item-config/layer blobs remain intact in the old
cache, but are absent from the new cache. Descriptor transfer sizes include
encryption padding; raw cached bytes retain their original verified digests.

This separates the failed migration from payload corruption or a model/UI
failure. Copying the immutable blob closure alone does not register an item:
native CM removes those copies as unreferenced. This agrees with the pinned
[Core image-manager ownership](https://github.com/aosedge/aos_core_lib_cpp/blob/5560291ba6914e36a5b841ade4d8fc54134a9e91/src/core/cm/imagemanager/imagemanager.cpp)
and [CM catalog storage](https://github.com/aosedge/aos_core_cpp/blob/9d613a46df3c7f550062e2f19ae3406c57715694/src/cm/database/database.cpp).
The one normal same-version assignment request receives HTTP 400. Subsequent
read-only reconciliation finds no queued Rootfs send request. No upload,
new-version publication, manual database/spec rewrite or second image follows.
All unsuccessful receipts are preserved. The eleven bounded cache/reconciliation
campaigns total 725 seconds of execution; this diagnosis time is separate from
the 9.74-second visible UI action sequence.

The future services-rootfs delivery preflight now refuses publication unless
the old native CM/SM owners already use the successor's cache paths. It fails
with `ROOTFS_NATIVE_CACHE_MIGRATION_REQUIRED_BEFORE_PUBLICATION` rather than
letting a reboot strand the just-acquired catalog. This source guard is unit
tested, not a claim that a fresh corrected FOTA has been run.

The current packet ends **NOT_COMPLETE_ROOTFS_CLOUD_INVENTORY_GATE_OPEN**.
Closing it needs a bounded supported native catalog-recovery procedure, or an
explicitly agreed recovery/re-staging plan that reconciles current retained
data before changing state. Do not invent an installed database row, discard
the current VM, or spend another image build outside this packet. After that
recovery, require native/Cloud version agreement through a cold restart and
repeat the short functional and headed UI loss/recovery scenario. The current
data, stopped VM, recovery checkpoint, original image inputs and evidence are
retained for that work.

### Recovery continuation proposal — not yet authorized for execution

After transport on 2 November, all three SSD volumes and the same M4 are
available. The integration branch remains at the recorded checkpoint; all five
M4 VM/Source journals remain stopped. Read-only
`vision-rootfs-recovery-preflight-02` confirms the same Unit/node/set, the exact
published `.6` version still Ready and no queued component send requests.
The Unit is Offline because its VM is stopped, not because a new connection
failure was observed. The existing send endpoint rejects OPTIONS with 405;
this supplies no recovery operation and does not justify retrying its failed
POST. No VM, simulator, build or Cloud write is part of this preflight.
The initial isolated-helper import failure is separate from product status;
the corrected explicit helper path passes its isolated-loader regression.

The pinned native image-manager interface exposes ordinary download/install,
status and removal; no separate catalog-repair operation was found in that
interface. The proposed bounded fallback therefore needs **explicit operator
acceptance of active-state rollback**, not an inference from a request to resume:

1. Inventory current persistent data and space; retain a complete stopped copy
   of the current disk and journals for exact return. Keep the proven
   pre-update checkpoint and all original blobs. Delete nothing.
2. Restore a working copy of that checkpoint to the **same** Vision VM/Unit.
   This rolls active guest state back. Post-checkpoint data remains preserved
   in the full current copy; it is not automatically merged into the restored
   guest. Define and verify the required data reconciliation before acceptance.
3. Perform the first recovery boot without outbound Cloud traffic, while
   retaining the existing explicitly forwarded SSH access. QEMU documents
   [user-network restriction](https://www.qemu.org/docs/master/system/invocation.html#network-options)
   without disabling explicit forwarding. This is a proposed narrow recovery
   mode, not a live-qualified mode or permission to change global Mac networking.
4. Under stopped native writers, prepare/verify the supported CM/SM cache-path
   migration **before** allowing any new Rootfs acquisition or Cloud assignment.
   Keep native ownership and metadata coherent; no manual database row, writable
   immutable root, overlay rebase or fabricated installed status.
5. Reconnect normally and reconcile the restored real catalog. Reuse the
   already published `.6` image and Camera `0.1.2`; do not rebuild/re-upload
   them or issue an uncertain request twice. Restore the current service/data
   state through its normal owners and the agreed reconciliation plan.
6. Require native/Cloud agreement through cold restart, then the short native
   functional and three-view headed UI loss/recovery scenario, followed by
   normal shutdown and unchanged retained-instance checks.

This proposal does not authorize a new VM, Unit retirement, current-disk
replacement without preservation, Main/VDP/Brake/Tire changes, another image
build or a public release. If the required active data cannot be reconciled
without forbidden state edits, stop before the swap and use a separately
supported native recovery procedure instead.

A valid absent lead is present=false with null distances. The current trusted
vehicle geometry profile is unavailable, so a valid shadow plan is withheld;
this is intentional fail-closed behavior, not a value to invent from upstream
example defaults. Path/lead observations do not qualify model accuracy, a
geometry-dependent planner, motion control or vehicle safety.

## Upstream semantic basis

The pinned inference pipeline originally combines inference and fusion and
omits explicit elapsed-time arguments. The separated services pass actual
positive inter-result simulation time to fusion; planning processing elapsed
time remains distinct from its horizon step. Finite AutoSteer height/mask
values retain their upstream >=0.5 semantics without a sigmoid or 0–1 clamp.
The upstream free-road 150-m sentinel means valid absence, not a detected
vehicle at 150 m. Example geometry/speed limits are not trusted CARLA vehicle
measurements or authority to actuate. Dependency/precision/reference proof is
kept separate from native allocation, UI acceptance and performance goals.
