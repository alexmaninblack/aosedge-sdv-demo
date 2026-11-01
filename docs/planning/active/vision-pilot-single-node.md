<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Single Node Vision Lab Implementation Plan

- Status: Authorized implementation — isolated M4 VM, previews and independent Camera Access
- Version: 0.9
- Prepared: 2026-10-28
- Updated: 2026-11-01
- Owner: SDV Lab integration
- Architecture proposal: [ADR 0019](../../architecture/decisions/0019-vision-pilot-single-node-lab.md)
- Execution status: M4 VM/engineering preview and Camera Access native-source/targeted-compile gates complete;
  native Camera Access deployment, full-pipeline fit and E2E acceptance remain open
- Authorization: implement the 2026-10-31 plan on the dedicated M4, preserving Main;
  source/build/cache work stays on the development SSD. No implicit Main merge or public publication.

## Delivery outcome

Deliver a separate Vision Lab preview on `codex/vision-pilot-single-node`.
Its single Main Node runs two independently deployable Aos services and shows
camera-derived results in Driving Control. Preserve the current Brake/Tire
Lab and its operator delivery route. The topology, authority and ownership
decisions belong to ADR 0019; this plan allocates their implementation.

The intended operator journey is install Vision Lab, connect existing authorized
OEM/SP access, create the Vision controller, prepare its platform, deploy
Perception and Assessment, then drive in CARLA and inspect the Vision page.
No compiler, ROS2 installation, multi-node configuration or manual model-path
entry is part of that journey.

## Scope and working defaults

- One new Cloud Unit with one Main Node; no Secondary, MP or node-placement work.
- Two AI services in one proposed public `vision-pilot-services` repository.
- Existing pinned CARLA/Game and Main Factory are reused where compatible.
- Linux ARM64 CPU inference; INT8 is a candidate subject to output validation.
- Initial VM candidate: 4 vCPUs and 4 GiB RAM, not a capacity guarantee.
- Initial camera candidate: 1280 by 720, 10 simulated frames/s, approximately
  50-degree horizontal FOV, rigid centered forward mount; validate before freeze.
- Model inputs remain 1024 by 512 with the upstream-specific transformations.
- JPEG/MJPEG only; no H.264/H.265/WebRTC. ROS2 is not a required dependency.
- Live camera/rendering/encoding characterization precedes AI implementation.
- Native Vision page with frame-matched overlays; no AI vehicle actuation.
- Vision-only OEM Camera Access package; no VDP, Brake Health or Tire Health
  installation or VDP-slot reuse in this VM. The existing VM is untouched.
- No new analytics Cloud backend, raw-video history or recording by default.
- Sequential Lab operation on the dedicated M4. A conflicting live owner blocks startup;
  stopping it preserves its Test/data and uses its normal owner, never a PID kill.

These starting defaults are reviewed and frozen at the relevant early gates.
They cannot be silently changed during final acceptance to convert a failure
into a pass. A real resource or architecture mismatch is reported once with
the measured alternatives, not hidden by another packaging iteration.

## ROS and controller image findings

The Lab's ARM64 controller uses Yocto Linux with AosCore and KUKSA, not a
general Ubuntu/ROS development image. Read-only inspection of the retained
Factory 42 rootfs found no `/opt/ros`, ROS executable or core ROS/DDS libraries
in the standard directories. The pinned AosVM sources and project additions
also do not select ROS. Factory 41 has the same ROS-free declared base; this
review did not inspect its binary or start an installed guest. Sources and
the optional upstream ROS2 build are linked in
[the architecture proposal](../../architecture/decisions/0019-vision-pilot-single-node-lab.md#controller-image-and-compute).

Reuse the compatible clean image. Neither camera characterization nor the
initial two-service pipeline requires adding ROS to Factory or macOS.
Vision Pilot can build with its ROS2 interface disabled. If a later concrete
consumer justifies ROS, scope the adapter and runtime closure explicitly;
check the actual distribution, libraries, QoS, permissions and package costs
instead of treating a recipe, DDS library or SDK as a complete ROS install.
Do not rebuild Factory merely to satisfy an assumed middleware prerequisite.

## Repository allocation

All component branches start from explicitly recorded `main` commits. Use
separate SSD worktrees/checkouts rather than deleting the current workspace.
Create branches only where code changes; exact revisions, not matching names,
form the integration lock.

| Owner | Planned changes | Preserved boundary |
| --- | --- | --- |
| `aosedge-sdv-demo` | Vision source/producer locks, VM profile, fresh-Test scope, service preparation/publication/assignment, Setup, Presenter, qualification and this design chain | Current `main`, option A, release descriptors and Brake/Tire data |
| `carla-ego-runtime` | Owned RGB sensor, bounded host image/result interface, native Vision page and semantic UI identities | Existing tick/control owner, Safe Stop and advisory contracts |
| `aos-vehicle-platform` | Independent OEM Camera Access core/payload, result adapter, native resource/security integration and compatibility metadata; image delta only if proven necessary | No VDP extension or VDP-slot reuse, service algorithms or copied credentials; existing Main Factory retained |
| Proposed `vision-pilot-services` | Headless Perception and Assessment, shared DTOs, upstream pin, model/dependency manifests, two Aos packages and tests | Independent service releases; no CARLA/VISS control or Cloud producer keys |
| Brake/Tire service/backend repositories | No implementation changes | Their release lines, source and state remain intact |
| CARLA/Unreal repositories | No planned source or content rebuild | Retained standalone simulator and dependencies |

The proposed repository layout is not another integration repository:

```text
vision-pilot-services/
  apps/perception/
  apps/assessment/
  common/
  packaging/aos/perception/
  packaging/aos/assessment/
  dependencies/
  tests/
  docs/
```

Pin upstream source without Git submodules. Record the precise imported paths
and patch set; keep model weights and binary libraries out of source Git.
Use Apache-2.0 for original service files with the project copyright policy,
retain upstream notices and produce an SBOM for the runtime closure.

## Ordered delivery gates

| Gate | Deliverable | Completion condition |
| --- | --- | --- |
| V0 | Isolated source, installation and Cloud scope | No Vision selector or mutable path can adopt the retained Brake/Tire instance |
| V1 | Early live-camera feasibility on the dedicated target | Actual RGB frames and measured rendering/readback/JPEG cost; M1 findings retained, M4 is the current pilot target |
| V2 | Architecture cascade and executable interfaces | Source/time/permission/compatibility contracts, calibrated input profile and negative fixtures are fixed |
| V3 | Two headless applications and bounded packages | Deterministic unit/contract gates pass and both ARM64 package layouts are verified |
| V4 | Real Aos deployment and replay characterization | Both services run under native Aos identity/quotas on M4 and meet the agreed measured envelope |
| V5 | Full live camera, VM delivery and result return | The combined CARLA/host/VM/AI workload fits and produces correlated interpreted results |
| V6 | Presenter and native Vision screens | Stable layout, honest states and semantic UI checks over real results |
| V7 | Signed standalone Vision DMG | Isolated install/repair/update entry works without developer paths or overwriting Main |
| V8 | Complete API and visible UI campaign | Exact candidate passes, independent SOTA works and retained Brake/Tire state is preserved |

### Current execution packet: M4 VM and compute pilot

This is the authorized first milestone, not a replacement for the complete
delivery gates above. Run it on the M4 Pro (24 GiB), not the development Mac.
Keep the existing `codex/vision-pilot-single-node` branch and preserve Main.

1. **Design and source isolation:** freeze the fixed resource profile and its
   lifecycle binding in ADR 0019 and an executable contract. Keep Main at
   2 vCPU/2 GiB; Vision starts at 4 vCPU/4 GiB. No generic resource editor or
   arbitrary QEMU arguments. Preserve existing requirements and IDs.
2. **Local VM proof:** create a fresh Test-only VM from retained clean Factory
   42 in internal-M4 `SDV-Vision-Lab-Data`. Reuse packaged native QEMU/HVF,
   EFI and immutable Factory under their existing leases; do not copy current
   journals, access keys or Cloud identities. Use loopback SSH 12022 and owned
   private serial/QMP paths. Verify boot/resources, DNS/time, cgroups,
   namespaces, SELinux and native container runtime, then normal stop/start.
3. **Early real-model compute probe:** freeze upstream source, model hashes,
   runtime/libraries, preprocessing and a bounded licensed image sequence.
   Build the affected Linux ARM64 closure on the SSD-backed build worker.
   Measure each model and their combined pipeline inside the Vision VM,
   first FP32; INT8 requires output-tolerance validation. Random tensors or a
   host-native run may support unit tests, not substitute for real guest proof.
   An explicitly selected uncalibrated tensor-timing probe may first establish
   library/model execution and rough cost using real recorded frames. It must
   state that AutoDrive BEV is omitted, publish no interpreted output and make
   no calibration, accuracy, five-Hz live-pipeline or native-Aos claim. It does
   not close the calibrated replay or combined moving acceptance gate.
   Preserve actual frame timestamps. An irregular but ordered bounded recording
   may support this tensor-cost-only diagnostic; report its intervals and mark
   temporal fusion unqualified. Never relabel it as a valid nominal-cadence
   sequence or silently resample timestamps to pass a functional gate.
4. **Combined load:** compare the same Vision VM with models idle, models
   active and CARLA plus the live camera active on M4. Retain image/frame/time
   metadata and bound all buffers. Report model rate, per-stage p50/p95/p99,
   memory, swap growth, throttling and simulator/control responsiveness.
   Do not infer GPU/Neural Engine availability or fit from average CPU.
5. **Native integration:** only after the compute boundary is understood,
   close V2 transport/permission/calibration contracts and implement separate
   Perception/Assessment Aos packages, isolated Test-role Cloud provisioning,
   real deployment and live result return. The earlier engineering closure
   is not native Aos identity/quota/SOTA acceptance.
6. **UI and delivery:** add matched-frame native results and the Vision
   Presenter, then produce its separate DMG and full API/visible UI campaign.
   No speculative CARLA/Factory rebuild or repeated installer packaging.

Before switching variants, stop the retained Main runtime through its normal
owner and verify release of its resources. Preserve its Test, overlay, data,
certificates and installed candidate; do not stop shared Docker. A fresh local
VM/compute probe needs no new Cloud Unit. Later provisioning uses the selected
Production Cloud with a distinct Test-role Unit, never the retired M1 identity.

All phases run through a named, resumable scenario with read-only preflight,
recorded intent, fixed diagnostic stages, timings, result reconciliation and
verified owned cleanup. Unknown effects block replay. Keep models, reusable
libraries and VM disks separate from owned scratch. On failure preserve the
exact VM/evidence; never delete it to retry manufacture.

M4 baseline evidence: `m4-clean-install-20261030` /
`m4-camera-baseline-02/report.html` in the private qualification store. At
720p/FOV 50 and 0.1 simulated-second cadence, static phases delivered about
20 world/10 camera FPS; moving JPEG delivered 17.82/8.91 FPS and camera-removed
recovery about 20 world FPS. The separate 300-second visible review delivered
17.78/8.89 FPS without stale controller samples. These are characterization,
not an inference fit, full E2E or a chip-only speedup comparison. The local
Test had no deployed VDP/Brake/Tire services, and GPU utilization was not
reliably measured. Camera calibration and the final workload remain explicit.

The proposed interactive goal remains at least five complete results per
wall second and p95 capture-to-display age at most 500 ms. Freeze exact
definitions and allowable simulator slowdown against the M4 baseline before
qualification; do not silently change thresholds or source timing to pass.

### Current pilot result

The fixed VM booted, stopped and restarted on M4 with four guest CPUs and
4,019,944 KiB total guest memory. Native OCI execution, namespace isolation,
seccomp denial and enforcing SELinux were observed; Main identity was preserved.

The pinned Linux ARM64 FP32 closure executed all three real models against
60 recorded CARLA JPEGs. Three parallel single-thread sessions completed
300 combined tensor cycles in 60.10 seconds: **4.99 cycles/s**, median 198.9 ms,
p95 207.1 ms and process peak RSS about 1.11 GiB. The containing 90-second
stationary live-camera phase delivered 19.99 world/10.00 camera FPS with no
stale controller samples. Exact counters for only the active 60-second
subwindow were not recovered and are not invented.

These numbers do **not** establish the complete five-results/s target: BEV,
calibration, per-frame input delivery/preprocessing, Assessment, native Aos
quotas and interpreted UI output are outside this cost proof. The recording
also contains real 50–150 ms pair intervals, not uniformly timed functional
input. Budget headroom and calibrated temporal handling must close before
claiming V4/V5 acceptance or investing in the final UI/DMG.

Private receipts: `vision-vm-m4/guest-continuation-3/vm-result.json` and
`vision-vm-m4/model-compute/compute-steady/reconciled-cost-result.json`.
The original sustained scenario remains `NOT_COMPLETE` because its observer
lacked the final close callback. The source fix is unit-tested; the separate
reconciliation preserves the original record, retains completed model/camera
measurements and verifies normal VM/source/listener/helper cleanup. It is not
a relabeled successful full scenario. No CARLA/Factory rebuild, Cloud mutation,
Main merge or public artifact publication was performed.

Gates are execution checkpoints within one plan, not requests for permission
after each routine step. Once implementation is authorized, proceed until
completion or an actual scope/security/credential/fit boundary. Reuse successful
immutable outputs; fix the failing owner and rerun its gate, not the entire
build. Do not claim later gates from replay, fixtures or another DMG's evidence.

## Current signed-bootstrap and native Camera Access packet

The operator authorized the early signed bootstrap on 2026-11-01. Apply
[bootstrap v1](../../../contracts/vision-vm/bootstrap.v1.json) and ADR 0019 v0.9.
Build/sign only on SDV-Dev; install/test only on M4 internal storage. Reuse the
warm Builder/cache and compatible Linux inputs. Preserve the current DMG and
both retained VM roots. No Main merge or public publication is requested.

The bootstrap is a separately identified signed resource bundle, not a duplicate
CARLA kit or the final Vision UI/installer. It contains the new Vision image,
source-bound tooling and Camera payload. Its closed catalog checks signature,
team/identifier, base-program selection and image digest before the normal
manufacture owner can consume it. No arbitrary image override is permitted.
Use a fresh `SDV-Vision-Native-Lab-Data` instance with the existing fixed 4-CPU/
4-GiB Vision profile; preserve the earlier engineering Vision overlay/models.

The closed Cloud setup profile selects `aos-vision-vm` and `SDV Vision Verification`;
it cannot adopt or amend the Main model/set. The existing Source owner projects
fresh native-Unit Safe Stop credentials only into the Vision SM. It never starts
VDP or gives Camera Access a Gateway credential. OEM Camera delivery reuses the
official signer, multipart uploader, bounded publication reader and journal;
only its exact Camera type and owned Vision verification recipient are permitted.
The static ARM64 reader fixture is a diagnostic Aos service, not Perception.
Its local JPEG fixture, UID/mount/protocol-denial and revocation observations
must remain distinct from authenticated Gateway camera ingress and final AI E2E.

The operator authorized native Aos-container access and separate OEM activation.
Keep the old Brake/Tire VM/data unchanged. ADR 0019 v0.9 allocates the fixed
resource, local IPC, own OEM target and Vision-only bootstrap. The platform
repository owns the executable native profile; the foundation receipt remains
frozen and is not relabelled as native acceptance.

1. Inventory the stopped Vision VM and actual resource/runtime/account/policy
   support, retaining exact old-Main journal bytes before/after. Missing Camera
   bootstrap is an observed Factory limitation, not a reason to reuse VDP.
2. Implement closed read/OEM IPC, peer checks, distinct payload/profile and
   disabled native unit. Preserve physical Safe Stop and the existing A/B
   transaction/recovery engine. Run offline gates and targeted ARM64 runtime
   tests before any package/image construction.
3. Compile only the fixed launcher and narrow policy module using preserved
   recipe toolchains. Prove Unix/identity/policy behavior transiently on Vision,
   with Enforcing, an armed stock-policy rollback and verified cleanup. This
   platform probe is not native SM allocation or FOTA acceptance.
4. Build one bounded Vision bootstrap/image successor, not CARLA or the Main
   Factory. Preserve the engineering overlay/models. Provision its own Test-role
   Unit through normal owners, without sharing Unit keys or changing a shared
   Cloud model in place. Keep the selected Production Cloud and OEM/SP accounts.
5. Activate Camera Access through native SM and prove first-create, idempotent
   repeat, restart/recovery, independent target/store, health versus source
   availability and malformed/wrong-identity denial.
6. Deploy the native read-resource consumer; independently observe UID/GID,
   read-only mount, matching frame pair, producer/control denial, stop/revocation,
   bounded retention, process stability and fresh scoped AVCs. Editing resource
   JSON alone is not revocation. Verify old Main remains unchanged and close all
   owned processes/listeners. Keep source, image and live receipts distinct.

Authenticated Gateway ingress and full Perception/Assessment product deployment
remain their own V2–V5 gates. Neither an OEM-local fixture nor a manual crun probe
closes them. Signing the separate engineering bootstrap is authorized; Main
merge, public publication and replacement of the current DMG remain excluded.

The [native source receipt](../../../contracts/vision-vm/camera-access-native-source.v1.json)
binds the platform commit, 32 camera cases, 274 Python cases (three skips),
83 completed ARM64 unit cases and the separately compiled launcher/policy. Two
opt-in live VDP qualifications were skipped, not passed. None of these is
native deployment acceptance. Inventory proves the current engineering image
has no Camera bootstrap and Vision has no provisioned Unit. The temporary
account probe returned exit 1; it was cleaned up and is not a functional pass.
No policy was loaded. Preserve that result rather than substituting root.

The installed input catalog currently accepts only package-owned immutable
images; it has no selected Vision bootstrap input. Close the normal Vision
bootstrap/catalog delivery binding before image installation and provisioning.
Do not invent an arbitrary image override, overwrite the installed Main input,
reuse a VDP target or rebase an engineering overlay to cross this gate.

## Current live-preview packet

The current moving packet uses `vision_live_campaign.py --moving` and preview
v2. Associate actual world snapshots by frame ID, retain raw sensor timestamps,
select only real 80–120 ms pairs and run all three models on each admitted pair.
Observe bounded frame-clock history and missed associations; do not alter CARLA
physics or rebuild its binary. Enable native Driving Control Autopilot through
the normal UI, then independently prove actual speed and travelled distance.
The native control session remains the only motion owner; no Cloud provisioning,
hold bypass, inference actuation or Test/data replacement is authorized here.
Record the visible moving results and verify normal end-of-check cleanup.

## Completed source foundation: independent Camera Access

The operator accepted this composition and implementation on 2026-10-31.
Update the class-C architecture cascade first. Keep the retained Brake/Tire
VM stopped/unchanged; this packet runs no VM or live mutation.

1. Implement Camera Access as a separate source package in the platform
   repository's Vision worktree. Its core must not import VDP, CARLA, KUKSA,
   models, Cloud, provisioning or runtime control.
2. Freeze a machine-readable front-camera profile and exact frame/binding
   metadata. Validate JPEG dimensions before any decode and reject foreign
   source/epoch/calibration, replay, malformed/oversized input and time regressions.
3. Retain at most two immutable JPEG frames, deliver only the latest actual
   80–120 ms pair, count replacements/rejections and expose explicit warming,
   unavailable and locally stale delivery. Preserve raw sensor timestamps.
4. Prove first selection, identical-selection reuse, explicit source reset,
   disconnect/reconnect, stale delivery, valid functional read, malformed input
   and no disk/network/runtime side effects through offline unit tests.
5. Commit the platform source, then fan its exact commit/digest into integration
   provenance. Keep public Main catalogs, release descriptors, DMG and caches
   unchanged. Report source-only status, not an installed Camera Access pass.
6. Continue with native Aos resource/IPC authorization, authenticated Gateway
   ingress, the distinct OEM component target and Vision-only activation.
   Prove native identity, SELinux, restart and physical slot isolation before
   Camera Access deployment. The existing VDP-specific runtime is not assumed
   generic. Assessment dynamics/result contracts remain their own V2 work.

This source packet neither rebuilds CARLA/Factory nor installs the core into
the old VM. The successful engineering preview and its frozen receipts remain
unchanged; its SSH model worker is not repurposed as the product camera service.

The foundation source packet is complete at the exact
[Camera Access source selection](../../../contracts/vision-vm/camera-access-source.v1.json).
Its single offline scenario passed 22 unit/contract cases, repository policy,
retained telemetry-contract and Factory-layer validators in approximately
0.3 seconds. The platform worktree is separate and Main remains unchanged.
No VM, container, listener, signing, Cloud mutation or image build was started.
Next implement and prove the native resource/IPC and distinct OEM-target gates;
do not report source completion as installed Camera Access or full V2 closure.

For the preceding stationary v1 proof, the operator requested connecting CARLA to the existing Vision VM
to inspect real model outputs. ADR 0019 v0.5 and the
[engineering preview contract](../../../contracts/vision-vm/live-camera-preview.v1.json)
freeze this bounded step before runtime work. Run `vision_live_campaign.py`
once with the pinned private M4 context and successful VM proof. Reuse the
verified Linux ARM64 FP32 payload; rebuild neither Factory nor CARLA.

The scenario checks target/desktop/owners, starts the existing Vision VM and
CARLA through normal owners, derives camera-specific planar geometry and runs
a 60–180-second visible preview. Existing authenticated SSH carries bounded
JPEG pairs and matched typed results. Show raw live video beside its processed
frame, predicted ego path, path-relative boxes and nullable AutoDrive estimates.
Wrong pair cadence invalidates AutoDrive instead of fabricating nominal time.
Keep native Safe Stop, no Cloud mutation, no model motion authority and no
ground-truth detections in the model path.

Save at most four UI snapshots and bounded timing/counter evidence; verify
sensor, guest process, source, VM, helper and listener exit while preserving
Main/Test/data/models. Raw model behavior and geometric consistency are the
outcome, not qualified accuracy, native Aos deployment, Assessment, moving
acceptance or full product API/UI acceptance. Production transport/resources
and the native Vision page still close at their existing V2–V8 gates.

The stationary live preview completed on M4 with verified cleanup. Over the
120-second view, 594 responses completed (one drained at shutdown; 593 timing
records), including 442 AutoDrive-valid responses. The other 152 responses
explicitly withheld AutoDrive for non-nominal capture-pair intervals. One
invalid startup pair was rejected, not retimed. The latest-pair buffer replaced
613 pending pairs rather than accumulating a queue. Measured guest processing
was 213 ms median/223 ms p95; host image-arrival-to-result was 255/311 ms.
These are not full sensor-capture-to-display latency or a complete 5-Hz
three-model acceptance. No stale controller samples were observed.

AutoSteer returned up to 33 ego-path points and AutoSpeed 2–3 path-relative
boxes in this stationary scene. AutoDrive's low lead probability left distance
absent rather than manufacturing an object. Four matched UI snapshots and the
original result are retained privately under `vision-vm-m4/live-camera-03`.

### Moving preview result

The v2 moving preview completed on M4 on 2026-10-31. Over 120.07 measured
seconds, native Autopilot covered 390.50 metres with 81 moving speed samples
and no stale controller samples. The live camera and all three raw model
outputs were visibly observed through Screen Sharing on M4; four matched
preview snapshots were retained. Model inference remained read-only.

All 528 measured responses contained valid AutoDrive, AutoSteer and AutoSpeed
results: **4.40 complete results/s**. Each admitted pair had two frame steps and
100 ms between actual world snapshots. The unmodified sensor timestamps for
those same pairs still contained 37 intervals of 50 ms and 59 of 150 ms
(432 were 100 ms). Exact frame association removes that metadata ambiguity
from engineering temporal input without hiding its original values or claiming
pixel/capture-time accuracy. Across the full capture, including native-input
waiting, no world-frame association was missing; the raw sensor/world offset
was either 0 or +50 ms. Four invalid startup pairs were skipped. The single
latest-pair buffer replaced 810 pending pairs across that full capture instead
of accumulating delayed work.

Guest pipeline time was 225.3 ms median/232.4 ms p95; host image-arrival-to-result
age was 279.2/342.2 ms. Neither includes the full sensor-capture-to-display path.
AutoSteer returned up to 37 path points and AutoSpeed up to eight boxes; these
are model predictions, not validated lane/object labels. The complete 5-Hz
goal is **not met**, and no model-accuracy, Assessment, native Aos or full E2E
acceptance is claimed. Local planar calibration remains an approximation during
motion.

Private receipt: `vision-vm-m4/moving-camera-02/live-result.json`, frame metrics,
motion observations and `live-01.png` through `live-04.png`. The first moving
attempt expired because the native Autopilot input was not supplied in time;
its failure and verified cleanup remain intact. Only after reconciliation was
the separate second attempt launched and Autopilot selected through the normal
native UI. This engineering scenario therefore has a native-input boundary,
not unattended UI acceptance. The successful scenario also verified sensor,
observer, guest worker, helper, source, VM and listener shutdown and preserved
Main identity and both Tests/data. No Cloud mutation, Factory/CARLA rebuild,
DMG change, Main merge or public publication occurred.

## V0 Isolate the Vision track

1. Record existing source commits, current operator descriptor and compact
   retained-instance identities/paths. Reuse artifact manifests; do not rehash
   large unchanged images or export private state into Git.
2. Create `codex/vision-pilot-single-node` worktrees on the development SSD for
   changed owners. Do not switch or clean the retained working installations.
3. Allocate a separate Vision product/bundle family, default private-instance
   and package-store roots, launcher/runtime selection, VM disks and release
   ledger. The proposed visible name is `AosEdge SDV Vision Lab`; exact bundle
   identifiers are frozen before signing and cannot alias the current app.
4. Define a new Vision Test Unit and distinct scoped Subject/Unit Set names.
   A proposed set title is `SDV Vision Tests`, not the current `Test Vehicles`
   title or its existing discovery suffix. Reuse authorized accounts, never
   their Unit identities or an unrelated existing object found only by name.
5. Reuse a shared Cloud model only when its metadata/configuration are
   identical. Otherwise create a versioned Vision-specific model/configuration;
   never patch the model currently used by Brake/Tire in place.
6. Make Vision build/preparation/resume resolve its own pinned sources and
   producer plan. Eliminate inherited defaults that download Main or reinstall
   its DMG. Main's public launcher, option A and catalogs remain unchanged.

Exit evidence: compact source/scope manifest, path- and identity-isolation
tests, and negative cases for wrong product, Unit, Subject, model or active owner.
No existing Test is retired to prepare this variant.

## V1 Measure the live camera before AI integration

This is the first runtime work after minimal source/owner isolation. It does
not wait for two AI packages, a new Cloud Unit, a ROS installation, a full
Vision UI, a Factory rebuild or a new DMG. Use the retained standalone CARLA
on the dedicated M4 and a small owned camera probe; freeze its attachment/cleanup boundary
and isolated unit tests before live execution. Keep the same reference
controller, services and visible-window load in all comparison phases.
Their identities, software and persistent data are not modified by the probe.

Use the camera profile of the proposed V8 campaign entry, not a second test
framework or agent-directed camera steps. It checks
the actual installed CARLA/Python API, `sensor.camera.rgb` availability and
supported attributes, selects the existing ego actor through its normal
owner, then performs these modes over the same scene and driving workload:

| Mode | Added work | Question answered |
| --- | --- | --- |
| A | None; no additional RGB sensor | What does the existing complete reference workload cost? |
| B | One forward RGB sensor and bounded raw-frame callback; no JPEG or AI | Can this CARLA build deliver real images, and what does rendering/readback/capture add? |
| C | The same sensor plus one bounded JPEG encoder; no AI | What CPU, memory and delay does encoding add, and how large are real frames? |
| A repeat | Remove only the owned camera/encoder; restore the same baseline | Did performance recover, or did thermal/background drift affect comparison? |

Start at 1280 by 720 and `sensor_tick=0.1`, using the proposed rigid mount/FOV.
Use the same map, route/seed, traffic, weather, graphics, simulation/tick
configuration and visible windows throughout; record any unavoidable change.
The first characterization uses six phases: A, B with a native live preview,
B without preview, C with the actual JPEG decoded in the native preview,
C without preview, then A repeat. This validates visible image content before
spending time on each isolated measurement. CARLA, Presenter and Driving Control remain
visible. This separates capture/encoding from the operator's viewing cost.
Each phase has 10 seconds of warm-up and 45 seconds of observation: 330 seconds
in one script. A 600-second probe deadline includes setup and cleanup.
Report startup and cleanup separately. Repeat only a classified invalid or
borderline comparison, not an unconditional lengthy soak. Do not change
physics, safety timeouts or the tick owner to get a pass.

Collect real image samples with advancing CARLA frame/time and verify content,
dimensions, color order and orientation; counting callbacks is insufficient.
Camera callbacks only offer frames into bounded storage. Encoding and slow
consumers must not block physics/control or accumulate every frame. Destroy
only the probe's sensor and close its own workers through normal cleanup.
Do not spawn a second vehicle, clock/tick producer or unauthenticated public
stream server. A sensor failure is investigated in the retained build before
proposing a targeted simulator delta; it is not grounds for speculative
Unreal or Factory rebuilding.

Measure the whole dedicated target, not only guest CPU or nominal camera FPS:

- Simulation progress per wall second, tick/frame intervals and real delivered
  camera rate, including p95/p99 intervals, source gaps and capture-frame lag
  at callback arrival. Keep callback-to-encode timings in host monotonic time;
  do not subtract simulation seconds from a wall-clock timestamp.
- CARLA/rendering throughput and host process CPU; GPU utilization only where
  reliable instrumentation is available, otherwise mark it unmeasured.
- Host memory pressure, swap growth, process RSS and VM CPU/memory, with the
  same running VM/UI/background workload in every mode.
- Raw-frame handoff, JPEG encode p50/p95/p99, encoded size/rate, dropped frames,
  bounded queue occupancy and control/UI responsiveness.

The profiler records the normal controller's `fresh`/held/mode observations,
including transient stale samples during capture. A stale read is a measured
quality deficit, not a command authorization: the probe performs no actuation
and never alters the product's freshness/safety decisions. Missing/replaced
source owners, a changed source/ego binding or failed status reads still stop
the probe. Separate the functional image/cleanup result from performance and
control-availability findings; a functional PASS is not a healthy-performance claim.

The RGB API produces four-byte BGRA pixels. The proposed 720p profile is
3.69 MB/frame and 36.9 MB/s at ten frames per wall second, before copies;
JPEG savings apply after capture, not to the camera's rendering/readback.
Derive transport demand from measured JPEG sizes, not a guessed compression
ratio. `sensor_tick` is measured in simulation seconds, so a slow simulation
can satisfy that interval while delivering fewer real frames. Camera output
also arrives after capture; retain frame/time metadata through every stage.
Do not disable rendering for this proof: no-rendering mode returns empty GPU
sensor data, and off-screen rendering is not free rendering. Validate these
[sensor](https://carla.readthedocs.io/en/latest/ref_sensors/#rgb-camera) and
[rendering](https://carla.readthedocs.io/en/latest/adv_rendering_options/)
behaviors against the actual retained Mac build.

If an authorized bounded guest receiver is already available, add an explicit
mode D for JPEG delivery/decoding with the proposed Vision VM but no models.
Otherwise mark D NOT_RUN and complete it in V5; do not hold the first camera
measurement behind full platform integration. A/B/C do not prove VM delivery
or model throughput. Even loopback delivery shares host resources.

Exit evidence: one comparison report with actual host/build/profile, real-frame
samples, phase timings, counters and verified cleanup. The probe must have
responsive controls, advancing valid images and bounded queues. For this first
characterization the functional gates are at least ten ordered camera frames
per measured capture phase, nonuniform visible image samples, unchanged world
settings and removal of only the owned sensor. No quantitative performance
acceptance threshold is claimed; measured responsiveness, memory and timing
must be reviewed to freeze those tolerances before later qualification. Use the results to
select the capture/JPEG profile and remaining CPU/memory budget before V2/V3.
Do not equate the remaining budget with proof that three models will fit.
Any lower rate/resolution or changed optical geometry is an explicit profile
decision with corresponding calibration/model validation, not a silent retry.

### First M1 characterization, 2026-10-29

The retained installed Factory 42 candidate was used without CARLA/Factory
rebuild, new Unit or Test replacement. The measured forward RGB sensor had
1280 by 720 pixels, FOV 50, `sensor_tick=0.1`; post-processing and the camera's
`use_ray_tracing` attribute retained their actual default `true` values. JPEG
quality was 85. The complete successful scenario took 539.6 seconds; its six
10+45-second camera phases took 331.7 seconds, excluding bootstrap/collection.
Earlier preparation/harness failures are separate from this successful duration.

| Phase | World frames/wall second | Camera frames/wall second | Stale controller samples / 45 |
| --- | ---: | ---: | ---: |
| A baseline | 6.80 | — | 0 |
| B RGB with preview | 3.91 | 1.96 | 13 |
| B RGB without preview | 4.09 | 2.04 | 18 |
| C JPEG with preview | 4.58 | 2.29 | 14 |
| C JPEG without preview | 5.29 | 2.64 | 9 |
| A recovery | 7.09 | — | 0 |

The capture queues remained bounded at one slot without raw-queue replacements.
JPEG encoding p95 was 13.3–14.0 ms; typical frames were about 255–289 kB and
measured compressed payload rate 5.3–5.4 Mbit/s. Capture interval p95 was
453–607 ms. Whole-host average CPU was approximately 39–44%; available memory
fell to about 3.2 GiB. Swap was already about 4.1 GiB and did not grow during
this run. GPU utilization was not measured.

Autopilot mode stayed selected in all sampled phases, but the car was stationary
throughout the RGB-without-preview measurement. The continuous route and traffic
therefore do not provide identical-scene replay: do not interpret the table as
an exact isolated percentage cost for JPEG or preview. The substantial capture
slowdown and recovery are observed findings, not proof of a particular GPU or
CPU bottleneck. The first JPEG-stage saved still was a raw transition companion;
actual JPEG preview was independently observed by 103 successful frame decodes.
The sample selector and timely progress forwarding were corrected offline after
this run; those two harness corrections have unit evidence, not a second live run.

Functional frame acquisition/preview, ordered metadata, unchanged world settings,
owned-sensor removal and normal runtime shutdown passed. Test/data and shared
Docker were preserved. This does **not** establish smooth video, healthy
control freshness under camera load, AI inference capacity, VM image delivery
or a full Vision Lab E2E result.

Before freezing V2, investigate the retained rendering/capture settings with a
separately declared comparison profile, including the camera's ray-tracing and
post-processing defaults. Resolve the required wall-clock frame rate and
control-availability budget from that evidence. Do not rebuild CARLA/Factory,
lower resolution/FOV, change physics or weaken freshness merely to obtain PASS.

### M1 optimization comparison, 2026-10-29

One automatic `vision_campaign.py --profile optimize` run completed in 573.4
seconds including startup, measurements and verified shutdown. Static and motion
probes took 246.1 and 111.1 seconds respectively, including bootstrap. It reused
the installed candidate, retained Test and isolated probe dependencies; no
CARLA/Factory rebuild, package change, provisioning or publication occurred.
The predeclared [comparison protocol](#bounded-m1-camera-optimization-characterization)
used the normal return-to-road and native Autopilot actions, not probe actuation.

| Stationary profile | World frames/wall second | Camera frames/wall second | Camera interval p95, ms |
| --- | ---: | ---: | ---: |
| No added camera | 8.68 | — | — |
| Reference 1280x720 | 6.52 | 3.28 | 358 |
| Camera ray-tracing flag off, 1280x720 | 6.92 | 3.44 | 335 |
| Post-processing and ray-tracing flag off, 1280x720 | 7.68 | 3.84 | 301 |
| Same reduced effects, 960x540 | 7.96 | 3.96 | 297 |
| Same reduced effects, 640x360 | 8.04 | 4.00 | 294 |
| Reference 1280x720 repeated | 6.84 | 3.44 | 339 |
| Camera removed | 9.28 | — | — |

This was the same stationary ego/view, but not a deterministic town/thermal
replay. The reference repeat drifted about 5%; the ray-tracing flag result lies
within that range and does not prove a ray-tracing optimization. At 720p the
reduced-effects result was about 12–17% above the two references, but disabling
post-processing also disables lighting/tonemapping features. Actual saved JPEGs
show significantly darker roads and lost dark-object detail. Do not accept that
image-domain change as a free optimization for the Vision models.

In the continuous Autopilot follow-up, no-camera world rate was 8.83 frames/s
over 69.7 m. Reference 720p delivered 1.97 camera frames/s (world 4.00; 31.1 m,
30/30 moving samples). Reduced-effects 720p delivered 2.03 frames/s (world 4.07;
17.7 m, 19/30 moving samples). Different traffic/views and a stop prevent an
isolated percentage comparison. There is no demonstrated useful moving gain;
camera interval p95 remained 549–565 ms. The normal freshness observer reported
17/30 and 11/30 stale samples; enforcement was not weakened.

JPEG encoding p95 was 12.6–14.9 ms in motion, versus roughly half-second capture
intervals. Raw queues stayed at one slot with no replacements. Whole-host CPU
averaged about 38–43%; minimum available memory during moving reference was
3.09 GiB. Existing swap did not grow. CPU average is not proof of GPU saturation
or remaining model capacity. Driver utilization counters were not validated;
GPU load remains NOT_MEASURED. Renderer logs contain three 500 ms GPU-wait
messages, which support investigating rendering but do not isolate its cause.

The installed host manifest derives from the retained host manifest
`f6ae4b1222e55a0d15501176ca0ab91aaa29ce011817419c1e6b3443c5dacff2`,
bound by the CARLA dependency lock to source
`eb09b82464076596ee47e42b3f5f9b48f9ff5b30` / Unreal
`9b705d6d2db5b769ab34edb04f3ca2bb8b960014`. Its Low selector deliberately keeps
GI quality 2 (software Lumen), AA/texture/view/shading quality 3 and TAA history
screen percentage 200. That last setting enlarges history buffers; it is not a
claim that the main render resolution doubles. Low already disables dynamic
shadows, foliage/grass and motion blur. The visible launch was 900x398, and the
app declares `NSHighResolutionCapable=false`; a speculative Retina-resolution
fix is not justified by this evidence. Current upstream CARLA documentation
describes a different Low implementation: do not apply its table to this pin.

The next optimization packet should introduce and measure a distinct M1 render
profile, preserving the existing profile for rollback: first remove excess TAA
history cost, then compare cheaper diffuse lighting with readable ambient fill
against software Lumen. Measure the visible viewport plus camera together,
check actual applied values, image content/exposure, motion/control freshness,
memory and recovery. Do not merely turn all post-processing off, hide CARLA,
change physics/timeouts, reduce scene contents or assume a new GPU API provides
hardware acceleration. Any simulator rebuild remains a separate authorized
step. Keep 720p/FOV/cadence until the model/calibration trade-off is explicitly
reviewed; lowering pixel count alone gave little improvement in this sweep.

Sources: [CARLA rendering options](https://carla-ue5.readthedocs.io/en/latest/core_rendering/),
[Epic macOS requirements, UE 5.5](https://dev.epicgames.com/documentation/en-us/unreal-engine/macos-development-requirements-for-unreal-engine?application_version=5.5),
and the retained source pin above. The upstream docs are explanatory context,
not evidence of this binary's effective settings.

Both probes passed functional frame/content/ownership gates, removed their
sensors and preserved world settings. Normal shutdown independently confirmed
no owned simulator/VM/native-runner processes or runtime listeners, detached
the scenario media and preserved Test/data and shared Docker. This is completed
characterization, **not** smooth-video or Vision-performance qualification.
Compact JSON measurements, JPEGs and executed-source snapshots are retained
under the private `vision-camera-20261029` / `optimize-01` evidence root.

## V2 Freeze interfaces and update the design chain

Apply the class-C cascade on the Vision branch: HLA, Scenario, Flows, system
requirements, component/interface allocation, relevant component packages and
D4 decisions. Keep stable IDs and unrelated expanded obligations. New Vision
requirements receive their own IDs and unit-test allocations at this gate.

Define versioned schemas and golden/negative fixtures for these boundaries:

| Interface | Producer to consumer | Required semantics |
| --- | --- | --- |
| Camera frame | Gateway/platform adapter to Perception | Selected source/epoch, camera and CARLA frame, simulation time, encoding, dimensions and calibration profile |
| Perception result | Perception to Assessment | Same frame, AutoDrive pair references, model/preprocessing versions, raw typed outputs, validity and timings |
| Vehicle dynamics | Approved Vision platform input to Assessment | Independently closed source/permission contract, original sample time, speed units and freshness; no Brake/Tire VDP or credential reuse, no cached-value re-timestamping |
| Assessment result | Assessment through platform adapter to Gateway | Matched source/frame, interpreted path/lead estimates, validity, producer epoch and compatible service versions |
| Native/browser observation | Gateway/server to Driving Control/Presenter | Matching display frame, actual age, honest state and opaque browser references |

Freeze the native permission/mount/IPC mechanism before implementing it.
Prefer existing Aos-managed named resources and private local IPC; verify
UID/GID, peer identity, restart and replacement behavior. The existing KAC
session authenticates KUKSA access, not arbitrary camera access. Do not add a
parallel credential database, distribute VDP keys or grant broad sockets/files
to make a prototype connect.

Use a separate bounded image channel alongside telemetry. For the host-facing
candidate use standard MJPEG multipart framing with explicit frame metadata;
structured results use a separately typed message. Final endpoint/port names
and the native container-to-container transport are outputs of this gate,
not invented SM APIs or an operator-configurable URL field.

Proposed bounds for contract review are a 4-MiB encoded frame, a 64-KiB JSON
result, up to 128 detections and 64 path samples. Check dimensions before
allocation/decode. The live input buffer retains the latest valid frame pair,
not an unbounded FIFO. Bound the host display cache independently by count,
bytes and age; decide its final limits from the latency target and measured
frame sizes. Overflow must be counted and visible in diagnostics.

Temporal requirements distinguish two intervals:

- The capture interval inside AutoDrive's two-image input pair.
- The interval between processed outputs used by fusion/tracking.

When inference skips outputs, it may consume a newer valid capture pair; it
must not pair arbitrary distant images or continue fusion with a fictitious
100-ms step. Define reset behavior for source changes, frame gaps, teleport,
service restart and incompatible versions. Keep host latency measurements in
one clock domain; guest monotonic time is not directly subtractable from host
monotonic time.

Use nullable estimates plus explicit validity/presence. In particular, the
upstream maximum-distance sentinel is not a detected object at 150 metres.
Define pixel/world coordinate conventions, crop/resize reversal and units.

Use V1 measurements to select the source and encoding profile before freezing
the transport/cache bounds and camera calibration. Generate/validate the
camera-specific homography and preprocessing maps against known scene
geometry. A successful raw-camera probe does not validate model calibration.
Define how capture frames map to host tick/arrival times and bound the
measurement error. Ingress-to-display timing must not be mislabeled as full
capture-to-display latency when GPU readback delay was not included.

Exit evidence: machine-validated schemas and fixtures, compatibility table,
permission/transport design, allocated requirements/tests and passing docs-check.

## V3 Implement headless services and native packages

### Perception

- Extract the inference portion from upstream fusion/planning/display code.
  Keep model-specific preprocessing, including two-image AutoDrive input and
  the distinct normalization used by the other models.
- Provide a platform-camera source and an explicit engineering replay adapter.
  Replay never becomes an automatic fallback when live images fail.
- Load exact digest-bound models/calibration from the package or declared
  resource. Validate ONNX input/output shapes and the selected precision.
- Bound session thread pools and worker concurrency. Disable the optional
  upstream ROS2 interface and remove GUI, CAN and actuation dependencies from
  the entry point; do not install ROS, a Python training stack or CUDA merely
  to run CPU inference.

### Assessment

- Extract fusion/tracking and shadow planning into a second application.
- Join by capture identity and compatible schema/calibration, not arrival order.
  Read actual authorized vehicle speed with original source time.
- Do not invent valid estimates for missing/invalid/stale perception or speed.
  Track temporal reset with a producer epoch; do not preserve a stale track
  across a service restart as if it were a current observation.
- Publish interpreted display data only. There is no actuator writer, motion
  permission or new route through the Brake/Tire advisory targets.

### Build and package

Build two Linux ARM64 closures using an SSD-backed compatible build worker and
preserved caches. If shared Docker stores layers internally, do not use it for
heavy SSD-only builds or relocate/restart it as a side effect; select an
isolated SSD-backed builder. No fresh Yocto Builder is required by default.

Add two typed Vision profiles to preparation, signing, publication and assignment
in the Vision integration branch. Verify every file, library, internal link,
architecture, mode, model hash and license in the closure. Existing Brake/Tire
binary-only layouts and the 256-MiB guard are not a generic Ubuntu importer.
Measure the closure and propose a justified per-profile size bound if needed;
never disable path/digest/size validation globally.

Generate independent service versions, release metadata and resource requests.
Define compatibility so one service can update without an obligatory update
of the other. Initially bundle the selected weights with Perception; separate
model/runtime layers are outside this delivery. Do not copy private credentials
into rootfs, fixtures, argv or logs.

Exit evidence: deterministic unit/contract tests with isolated doubles, verified
ARM64 package manifests, SBOM/notices, and negative tests for wrong model,
precision, schema, path/link escape, malformed result and actuation attempts.
Real model execution and real platform integration belong to M4, not a new
live experiment on the development Mac.

## V4 Deploy on the Vision VM and characterize replay

1. Create an independent VM from the clean retained Main Factory using the
   new instance's normal manufacture/provisioning path and its own keys.
   Keep one Main Node; no change from `nodes_count=1` is required.
2. Verify actual guest CPU/RAM, reported capacity and native DMIPS mapping.
   A fixed node capacity value must not misrepresent the larger VM. Check
   filesystem, cgroups, required resources and SELinux with enforcing policy.
3. If a named resource/policy/configuration is missing, prove one bounded
   platform delta before making a Vision-specific image. Do not start a full
   Factory rebuild or change the retained image from a speculative symptom.
4. Use the explicitly selected Production Cloud domain with a Test-role Unit
   and the existing authorized OEM/SP accounts. No automatic staging fallback
   or Production-role vehicle is part of the pilot.
5. Sign, publish and deploy each package through normal Aos paths. Verify
   actual service identity, process, quota/cgroup binding and emitted data,
   rather than treating Cloud Running as functional proof.
6. Run real inference and Assessment against a bounded licensed recorded
   sequence with speed/time data. Reuse a suitable short V1 capture, or a
   separately declared licensed fixture. Bound recording duration/bytes in
   advance; no continuous raw-video recording. Simulation ground truth is
   evaluation data only. Label replay separately from live-camera proof.

Characterize FP32 versus INT8 output behavior and bounded threading. Measure
warm-up, per-stage CPU/wall time, RSS/peak memory, result rate, p50/p95/p99 age,
drop counts, throttling and process restarts. Compare output within tolerances
fixed from the reference, not bitwise equality for stochastic filtering.

The proposed interactive target for review is a 10-Hz source, at least five
complete results per wall-clock second and p95 camera-to-display age at most
500 ms during the representative daylight scene. Replay establishes a compute
budget, not that final live target. Freeze the accepted metric definition and
reference workload before V5/V8. An initial 180-second steady-state sample is
bounded characterization, not a long-soak or safety claim.

Exit evidence: two real Aos instances, resource/output records, measured VM fit
and a frozen performance profile. If the M4 budget does not fit, report the
measured choice between profile tuning and another compute target before
investing in final UI/DMG work. Do not quietly move live testing to the work Mac.

## V5 Connect the complete live pipeline on the same M4

In Gateway, attach one owned RGB sensor to the existing selected ego actor.
Preserve tick ownership and manual/Autopilot/Safe Stop behavior. Camera callbacks,
encoding and network writes must not block the physics/control loop. Encode
once and distribute bounded JPEG frames rather than recording continuously.
Destroy only the owned sensor at normal shutdown or source replacement.

Use the V1 measured capture/encoding profile and V2 validated homography and
preprocessing maps. Verify the actual rigid mount, image orientation, FOV,
crop, aspect and projection against that profile. Never retain another camera's
`H.yaml` just because the overlay looks plausible.

Integrate the independent OEM Camera Access component and separate typed
result adapter using the V2 contracts. Relay images without unnecessary pixel
decoding in Camera Access. Do not install or extend the Brake/Tire VDP. Close
Assessment's approved dynamics input separately; preserve original source times.
Validate returned results at the host Gateway for selected source, epoch,
frame, schema, calibration, size, finite values, rate and age. Refuse old,
cross-source, incompatible or unauthorized messages.

On source reset/replacement, clear the relevant frame references and temporal
state through the contracted generation change. Distinguish internet/Cloud
loss from local camera-link loss; preserve existing connectivity operations
instead of using an AI connection to bypass them.

Exit evidence: a live API observation correlates CARLA capture, both service
stages and returned output. Camera stop/freeze, duplicate/out-of-order frame,
wrong generation, wrong calibration, loss/reconnect and invalid credentials
produce the defined states. Neither valid nor malicious AI output can change
vehicle motion. Repeat the performance measurement with CARLA rendering active.

Before UI/DMG work, complete the camera-to-VM/decode measurement (mode D) and
the fully loaded mode E: CARLA/rendering, capture, encoding, VM, Perception,
Assessment and return transport all running on the same M4. Compare against
V1, including host memory pressure/swap, VM throttling, scene progress,
freshness, drop/queue counters and control response. Record separate stage
costs as well as total age; a fast encoder or replay does not imply a fast
live system. The macOS host and Linux VM compete for the same CPU, unified
memory and bandwidth. More vCPUs or guest RAM cannot manufacture host capacity
or expose the Apple GPU/Neural Engine to the current CPU-only guest.

Exit evidence also requires the complete live workload to fit the agreed
envelope without unbounded queues, false freshness or changed safety limits.
If it does not fit, resolve one measured profile/compute decision here before
packaging, rather than iterating installers around an unresolved resource gap.

## V6 Implement the Vision user interface

Keep the existing layered visual language and icons. In the Vision variant,
show the Vision controller/platform and Perception/Assessment rather than
unavailable Brake/Tire cards or unrelated maintenance/history controls.
Separate installed version, Aos service state, input availability and output
freshness. Full private joins remain on the server; the browser receives the
existing opaque identity projection.

Add a fixed-size native Vision page. Its processed-camera image carries the
predicted path, path-relative boxes and an estimated lead distance only when
valid. Frame lookup precedes overlay rendering. If the matched image expired,
show that fact rather than drawing an old result on a new image. Keep the
latest driving controls and physical speed distinguishable from capture-time
AI inputs and proposed motion values.

Use stable slots and dimensions for warming, live, delayed, unavailable and
incompatible states. Loss of a detection is not loss of the service. Display
`Analysis only` consistently. Reuse the V5 measured profile for age labels;
do not weaken a safety/service timeout to make the UI appear ready.

Add semantic Accessibility identities and browser selectors as part of the
implementation, not after recording coordinate-based test clicks. Reuse the
existing native runner only after its exact target/bundle allowlist is reviewed;
do not grant it general desktop-control authority.

Exit evidence: state/geometry fixtures, real API-to-UI correlation on M4,
matched-frame screenshots, no moving/resizing controls across transitions,
and readable source/time/model provenance without duplicated diagnostic clutter.
Repeat the loaded V5 measurement with the Vision page visible, including
native image decode/overlay/paint costs. A UI-disabled pass is not proof that
the final visible demonstration fits.

## V7 Package a standalone Vision DMG

Assemble only after the previous gates pass. Reuse CARLA/Game, QEMU, tools and
the compatible Factory. Rebuild only changed Gateway/Driving Control, platform
payload, Vision services, Presenter, orchestration and Setup targets. Reuse
successful outputs for unchanged source/dependencies. Include prepared inputs
so the operator does not compile services or locate model files.

Use a distinct signed Setup/launcher identity and defaults from V0. Prove that
installation, Launch Services selection, repair and package update cannot
overwrite/adopt the current Lab's launcher, selected version or private state.
Reuse an authorized signing identity; check Keychain/desktop access before the
long build. Any required OS secure input remains native, not an embedded password.

Audit operator-side Docker usage. Do not add a new host backend merely to reuse
the Brake/Tire journey. If the Vision runtime has no Docker dependency, remove
its backend-preparation prerequisite in this branch after verifying the complete
closure; developer build tools may still require Docker. Never stop or move
shared Docker Engine as installation cleanup.

Create one candidate receipt binding source locks, platform/Factory, both
services/models, installer signature and DMG digest. Use a readable Vision
preview filename and a separate release descriptor. The current public option
A and rc.4 media are not replaced or relabeled. Public upload/promotion is a
later explicitly scoped action, not the last automatic step of a test build.

Exit evidence: exact candidate available on M4, normal signed Setup installation,
successful Vision first launch with no development fallback, and unchanged
retained Main installation records. Verify large bytes at creation and consumer
boundaries, not repeated download/hash loops.

## V8 Run one complete API and visible UI campaign

Extend `scripts/qualification/vision_campaign.py` using the existing qualification
infrastructure. Its camera and optimization profiles exist; the full Vision
profile below is not implemented. Its private selection binds candidate, M4, selected Cloud domain/owners,
Vision Test, preserved Main scope, fixture/camera profile and evidence root.

The scenario owns preflight, preparation, ordered operations, independent
observations, timings, bounded failure capture, reconciliation and cleanup.
The agent starts it and investigates failures rather than performing routine
steps by conversation. Distinct replay/API/UI profiles may reuse its modules;
only the complete installed profile counts as the final campaign.

| Case | Required observation |
| --- | --- |
| Clean Vision install | Own installation, Unit/VM and defaults; Main retained |
| Native deployment | Both signed services execute under their actual Aos identities/quotas |
| Live drive | Fresh advancing CARLA frames produce matching API and native UI results |
| No lead object | Explicit no-detection state, not an object at a sentinel distance |
| Perception update | Compatible new release observed; Assessment remains the same deployed version |
| Assessment update | Compatible new release observed; Perception remains the same deployed version |
| Incompatible version | Defined unavailable/incompatible output; no fabricated continuity or implicit rollback |
| Camera freeze/loss | Stale/unavailable display and bounded buffers; controls remain responsive |
| Source reset | New generation, no old overlay/track accepted |
| Service restart | New producer epoch, defined warm-up and valid recovery |
| Cloud disconnect/reconnect | Honest Cloud state, observed local-data behavior and normal reconciliation |
| Resource contention | Native quota behavior, measured age/drop counters and responsive control |
| Malformed/foreign output | Rejected at contracted boundary; no motion or cross-Test effects |
| Shutdown and preservation | Owned processes/listeners stop; both Tests/data and shared infrastructure remain |

API verification precedes the complete visible UI journey. Show Presenter,
CARLA and Driving Control on M4. Use semantic actions and verify independent
effects; screenshots alone do not prove delivery, and an API pass is not a UI
pass. Validate service publication on the appropriate platform/service surface,
not only on the page where the action was requested.

Preflight must detect locked desktop, missing native grants/signing access,
network/storage problems, wrong product/Unit and conflicting owners before
costly work. Poll advancing state/events within existing operation budgets;
avoid fixed sleeps and blind retries. Persist intent before Cloud mutations;
after timeout/loss, reconcile the exact operation before any replay.

Report total wall time as well as preflight, build, transfer, install,
provisioning, model warm-up, API, UI, diagnostics and cleanup time. Long actions
show named progress. A failure report contains the exact gate/reason and
bounded redacted evidence; it must distinguish FAIL, BLOCKED and NOT_RUN.

At completion, close scenario-owned windows, simulator, Vision VM and helpers
through their owners, and verify exit. Do not retire either Test, delete review
data, stop Docker Engine or auto-restart the Brake/Tire demo. Preserve the
installed Vision candidate and compact evidence for the requested human review.

## Bounded M1 camera optimization characterization

Reuse the installed Brake/Tire candidate and its retained Test for V1 only;
do not rebuild CARLA/Factory or install a modified runtime. Run one owned
`vision_campaign.py --profile optimize` scenario. Keep the existing Low quality,
visible simulator, selected ego, physics, 0.1 s simulation camera cadence,
50-degree FOV, JPEG quality 85 and unchanged freshness enforcement.

First hold the car stationary through the normal return-to-road action. Measure
25 wall-clock seconds per profile after five seconds of warm-up: no-camera
baseline, 1280x720 reference, explicit camera ray tracing off, post-processing
and ray tracing off, exploratory 960x540 and 640x360, repeated 720p reference,
and no-camera recovery. Every camera profile has the same visible JPEG preview.
The lower resolutions are diagnostic alternatives, not an accepted change to
Vision calibration. Confirm actual sensor attributes, advancing frames, camera
content, bounded queues, resource usage and unchanged world settings.

Then use the approved native Autopilot action and compare no camera, reference
720p and reduced-post-processing 720p while moving (30 seconds each plus five
seconds of warm-up). This is a continuous route, not identical-scene replay;
report motion, frame age/freshness and scene/thermal drift explicitly. The
scenario removes only its own camera and closes its owned runtime at the end,
preserving Test/data, installed artifacts, shared Docker and credentials.
Do not label unvalidated macOS driver utilization counters as measured GPU load.

## Definition of completion

The implementation is complete when the accepted contract and source gates,
M4 compute/live-camera proof, standalone signed candidate, full API/visible UI
campaign, independent SOTA cases and Main-preservation checks all pass for the
same declared candidate. Readiness is not inferred from a green process alone.

Keep one current English architecture/implementation set and a compact linked
qualification receipt. Update Vision README/installation/build instructions
with the actual outcome, not a second history diary. No merge into Main,
replacement of its artifacts or public Vision publication occurs implicitly.

## Decisions to settle inside the early gates

The current scope is fixed to single-node, two services, CPU and JPEG/MJPEG.
V0/V2 still need the exact isolated bundle/default roots, compatible Cloud
model handling and native camera/IPC authorization mechanism. V1 establishes
the camera/rendering/encoding baseline before AI work; V2 freezes calibration
and interfaces. V4/V5 establish INT8 tolerance and the combined compute envelope;
V6 adds the real visible UI cost.
Resolve these once in their owning contracts before dependent implementation;
do not turn every routine compile, signing or test action into a new question.
