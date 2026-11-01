<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native Vision Services — V2/V3 Boundary Packet

- Status: Proposed bounded contract delta; not implementation/publication authority
- Version: 0.1
- Prepared: 2026-11-01
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
This packet proposes those decisions together before implementing their users.

The operator's instruction to proceed is authority to prepare this next packet,
not acceptance of previously unspecified endpoints, resource grants, a new
credential consumer or an image update. No VM/Cloud mutation, model run, build
or new repository/publication was started while preparing it.

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

## Recommended decisions for acceptance

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

Propose a Vision-only read route on the existing enrolled Gateway TLS listener:
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

Propose `POST /vision/v1/results` on the same existing TLS listener. Only the
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
closure. It already exceeds the old 256-MiB binary-service layout. Propose an
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

The packet's proposed writable boundaries are this integration branch, the
existing Gateway/platform Vision worktrees and the new service repository.
Keep one writer per owner, freeze exact revisions and fan in service → platform/
Gateway → integration selections. No edit to prepared build sources.

After source/unit and targeted reversible native proofs pass, permit at most
one warm incremental **Vision-only** image/rootfs successor if required by the
new accounts/resources/policy, with a proven stopped-VM recovery checkpoint.
Use a new immutable version, normal native update and same retained Unit/VM.
Do not reuse `.5` for changed bytes or assume Camera OEM payload alone can
install rootfs-owned resources. Proposed first versions are Perception `0.1.0`,
Assessment `0.1.0`, Camera Access `0.1.2`, Vision-only rootfs
`6.1.1-vision-camera.6` if required, and signed host bootstrap `0.6.0` if its
tooling changes. Check absence/collision before preparing any changed bytes.
Use only a distinct Vision-only `SDV Vision Pilot` Subject, containing this Unit
and these two services; reuse only an exact verified owned definition, never
by title alone. Freeze authoritative Cloud IDs, source pins and artifact
digests in the implementation receipt before signing. Unknown effects or an
occupied version fail closed; this proposed document authorizes no upload or
retry. Once accepted, routine exact-scope source/build/deployment steps need
no additional operator prompts.

## One ordered implementation and proof ladder

1. Accept S1–S6 together; cascade current HLA/Flows/requirements/D4 and freeze
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

No current gate is claimed passed by this proposal. Acceptance of the packet
would close the design choices, not pre-approve a failing security check,
invent an immutable artifact digest, or claim full Vision E2E.

## Source facts checked while preparing the packet

Read the exact retained Git objects, not an evolving upstream branch:

- `VisionPilot/modules/models/src/inference.cpp` currently mixes inference
  with fusion; the two fusion calls omit their optional elapsed-time argument.
- `.../safety_guardian/fusion/include/fusion/{longitudinal,lateral}_fusion.hpp`
  and their sources accept an explicit delta and otherwise use nominal 0.10 s.
- `.../fusion/src/longitudinal_fusion.cpp` returns valid/150 m when neither
  model confirms a target. The new DTO must preserve absence independently.
- `.../planning/src/longitudinal_planning.cpp` defines global `dt=0.05`;
  `planning.cpp` uses it for inter-cycle displacement and horizon prediction.
  These are distinct time semantics in the separated asynchronous pipeline.
- `.../planning/CMakeLists.txt` brings Eigen 5.0.0 and IPOPT; fusion requires
  OpenCV and currently depends on the combined model target. This dependency
  cut must be real, not two copies of the existing executable or an implicit
  ROS/CUDA/GUI installation.
- `VisionPilot/config/vision_pilot.conf` contains example geometry/speed limits;
  neither constitutes measured CARLA vehicle data or authorization to actuate.

These are local source/inventory findings only. M4 and all VMs remained stopped.
