<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0019: A Separate Single Node Vision Lab

- Status: Accepted for the isolated M4 VM, engineering previews and Camera Access native-boundary implementation; live activation remains unqualified
- Version: 0.12
- Prepared: 2026-10-28
- Updated: 2026-11-01
- Owner: SDV Lab System Architecture
- Change class: C; Camera Access resource/IPC/OEM target allocated; downstream Gateway ingress and service contracts remain required
- Direction selected: independent Brake/Tire and Vision single-node tracks
- Scope: isolated VM, bounded compute, stationary/moving engineering previews and Camera Access source foundation authorized on 2026-10-31; no implicit Main merge, public release or unrelated Cloud mutation
- Architecture input: [High-Level Architecture 1.9](../high-level-architecture.md)
- Implementation plan: [Vision Lab delivery plan](../../planning/active/vision-pilot-single-node.md)

## Decision to implement

Develop Vision Lab as an independent single-node demonstration on a dedicated
feature branch. Preserve the current Brake/Tire Lab on `main`, including its
installation, Test, VM, Cloud Unit, data, release catalog and dependencies.
The Vision variant has its own single Main Node VM and separately provisioned
Cloud Unit. It is not a Secondary Node of the existing Unit.

Use two independently deployed Aos services inside the Vision VM:
Vision Perception and Vision Assessment. Feed a forward-facing CARLA camera
to them using JPEG frames or MJPEG, and display interpreted results in native
Driving Control. All computation is shadow analysis: no vehicle actuation.

The operator accepted the Camera Access composition on 2026-10-31. Vision
has its own OEM Camera Access platform package, not a camera extension of VDP.
Do not install VDP, Brake Health or Tire Health in this VM. Preserve the other
VM and its installed packages, Test, disks and data without migration. Sharing
an immutable Linux/AosCore base does not authorize sharing their mutable state
or adopting the existing VDP component slot.

The first version runs the two Lab variants sequentially. It does not require
a universal profile selector, simultaneous source attachment, multi-node
management, distributed scheduling or inter-node credentials.

Cloud Subjects, with explicit Unit membership and service assignments, own the
application-service grouping. The retained Brake/Tire Unit keeps its existing
Subject assignments; the Vision Unit receives only its separate Vision group
(Perception and Assessment in the product). Do not bind Vision to a Subject
that assigns Brake or Tire, and do not bind the retained Unit to Vision services.
The OEM components VDP and Camera Access use their own platform delivery/target
mechanism, not application-service Subject assignment. Image selection alone
does not isolate Cloud service assignments; verify both Cloud bindings and
actual native deployment. Diagnostic probe Subjects remain Vision-only.

There are two functional VMs in the Lab product. Preserved stopped engineering
or image-validation instances are evidence/rollback state, not a third product
node or a multi-node topology. The operator explicitly reaffirmed this boundary
on 2026-11-01; continuing validation must reuse the current Vision candidate,
not create another VM to work around a service-publication failure.

## Runtime boundaries

```text
Retained Brake/Tire track                 Separate Vision track
main                                     codex/vision-pilot-single-node
existing installation and private state   separate installation and private state
existing single-node Unit                new single-node Unit
existing Main VM                         larger Main VM: CM + IAM + SM
VDP + KUKSA/KAC + Brake + Tire             OEM Camera Access (no VDP/Brake/Tire)
                                         Vision Perception + Vision Assessment

Vision data flow
CARLA RGB camera -> Vehicle Gateway -> OEM Camera Access
                                          |
                                          v
                               Vision Perception
                                          |
                    approved dynamics -> Vision Assessment
                                          |
Driving Control <- Vehicle Gateway <- OEM result adapter
```

Camera Access owns selected-source image admission, metadata and bounded
delivery. The OEM result adapter owns typed result validation. Images do not
pass through scalar VSS/KUKSA values. Assessment's future vehicle-dynamics
input must close as a separate approved Vision contract; it is not a reason
to install the Brake/Tire VDP or silently copy its credentials. Services receive no CARLA control
endpoint, VDP private key, Cloud producer credential or arbitrary VISS writer.
The existing [QM containment boundary](0011-qm-service-containment-and-evidence-backed-oem-approval.md)
remains authoritative.

Camera Access belongs to `aos-vehicle-platform`, with its own payload identity
and explicit Vision-only platform selection. Reuse the native OEM/Aos lifecycle
mechanism only after proving that its target/profile supports this component;
never rename a Camera Access payload to VDP or reuse a VDP-specific slot. No
new lifecycle manager is introduced. Consumer access must use reviewed native
Aos resources and isolated local IPC, not another credential database. A
camera permission is not implied by ordinary KUKSA read permission.

### Camera Access foundation packet

The first source packet implements the transport-independent Camera Access
core: strict JPEG/metadata admission, immutable frame identity, two-frame
bounded retention, latest eligible pair delivery, stale delivery, source loss
and explicit source/epoch/calibration reset. It consumes a trusted source
binding supplied by the future OEM adapter; validating metadata is not source
authentication. No socket listener, host transport, IAM shortcut, runtime
resource grant, systemd unit or deployment is implemented by this core.

The first camera profile is fixed to front RGB 1280x720 JPEG/FOV 50. Preserve
world-frame and original sensor times separately under the engineering clock
association already qualified in preview v2; no synthetic capture timestamp or
pixel-time accuracy claim. Local delivery-age bounds use the receiver clock,
not subtraction of guest and host clocks. Read and delivery do not configure
the camera or grant motion authority. Core source tests precede the native
resource/IPC, Gateway ingress and distinct OEM packaging gates.

### Native Camera Access packet

The operator authorized native consumer access and independent OEM activation
on 2026-10-31. Allocate `vision-camera-read` through native Aos ResourceManager:
one instance, supplementary `aos-camera-read` GID and a read-only bind from
`/run/aos-camera-access/read` to `/run/aosedge/platform/camera`. The local
protocol accepts only `status` and `pair`. Read-only mounting alone does not
authorize Unix socket operations; kernel DAC, actual peer identity, the closed
protocol and observed SELinux policy enforce their respective boundaries.

The dedicated `aos-camera-access` process has no capabilities or Internet
listener. Its separate OEM socket is never projected into a service; it accepts
only the trusted OEM identity/root after SO_PEERCRED observation. A nonsecret
component generation binds requests to the current process. Source metadata
and this local generation are not host-to-guest authentication. Authenticated
Gateway ingress and its fresh source-epoch establishment remain a separate gate.

Reuse the existing OEM systemd-slot engine only with the explicit
`camera-access-v1` profile, Camera Access payload identity, own unit, health
adapter and `/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access` A/B store.
Preserve VDP defaults and physical Safe Stop/update/recovery rules. No VDP slot,
credential adoption, alternate installer or lifecycle manager is introduced.

The observed Factory has neither the Camera account/resource nor this target.
An explicitly selected Vision bootstrap/image delta supplies them; do not
overwrite the retained Factory, rebase the current overlay or rebuild CARLA.
Keep existing engineering Vision disks/models as retained state until a native
successor is qualified. Distinct source directories are not Cloud isolation:
normal provisioning must assign Vision its own Test-role Unit and keys.

Qualify source, targeted ARM64 compile, transient Unix/SELinux proof, bootstrap
package/image, normal OEM activation and actual native Aos container delivery
as separate gates. A root probe, manual crun or mocked runtime never counts as
native service authorization. Revocation stops/reinstantiates the native
consumer; editing resources.cfg alone is not active-instance revocation.

### Early signed Vision bootstrap delivery

On 2026-11-01 the operator authorized delivering a separate signed Vision
bootstrap before native Camera Access acceptance, rather than waiting for the
final V7 installer. This does not authorize replacing Main or publishing a new
operator DMG. The [bootstrap contract](../../../contracts/vision-vm/bootstrap.v1.json)
fixes its identity, scope, separate model, verification set and instance.

Use a resource-only macOS bundle with an independent identifier and the selected
Apple Development identity. It seals the Vision Factory, exact source tooling,
Camera Access payload and provenance. Reuse the installed verified QEMU/SDK
inputs; include neither CARLA nor credentials. Verify the Apple signature,
identifier/team, base-program manifest and image/source digests before use.
This is an engineering delivery, not notarized/public Vision distribution.

Native delivery has exposed the workdirs filesystem's forced SELinux context:
the declared Camera subtree label cannot override it. On 2026-11-01 the operator
accepted the [independent Camera-store binding](../../planning/active/vision-camera-store-change-request.md):
a separate fully allocated 512-MiB ext4 backend, per-Unit identity and fixed
Camera label, at the unchanged logical component root. Reuse the established
bootstrap layout/prepare/attach/mount/check pattern, never a VDP file or slot.
Do not change the shared workdirs label or grant Camera general Aos-file access.
Prove the backend before another image build; the resource/IPC/OEM logical
boundary is unchanged and native activation remains unqualified.

The operator also accepted the bounded
[first-enrollment correction](../../planning/active/vision-camera-first-enrollment-change-request.md).
For the same fresh Vision Unit only, the Source owner may initially project its
existing identity while the sole SM writer is stopped and an unchanged first
Camera install waits for Safe Stop. Require no previous/active/installed
component or enrollment; reject partial state, different identity and every
destructive phase. The ordinary native writer alone resumes and commits the
same transaction after real Safe Stop. Preserve the interrupted first Source
intent in a cancellation receipt when its actor is normally terminated or
independently proven absent; never fabricate a completed Safe Stop.

A closed signed-bootstrap catalog extends image selection only for the fixed
Vision profile and fresh native instance. Existing EnvironmentService/VMService
and UnitService own manufacture, VM and Unit lifecycle; no image-path override,
second VM manager or parallel state database is introduced. Preserve both the
Brake/Tire and engineering Vision roots. Native proof uses a fresh separately
provisioned Vision Unit; create an absent Vision-only model/verification set,
never modify a shared Main model. The diagnostic read-resource service is not
the final Perception/Assessment implementation or evidence of full Vision E2E.

## Service responsibilities

### Accepted Gateway camera ingress

On 2026-11-01 the operator accepted [camera ingress v1](../../../contracts/vision-vm/camera-ingress.v1.json)
in full for source, targeted compile and reversible live proof on the current
Vision VM. Add only the Vision-profile read-only MJPEG route on the existing
Gateway TLS listener. Require the selected Vision Unit/node's Source-owned
identity, exact certificate binding and an explicit camera-read grant; ordinary
VISS telemetry permission is insufficient. Preserve existing VISS quotas while
tracking one separate media slot in Source quiescence/detach.

The Camera Access OEM package has an internal nonroot ingress process with
its own narrow SELinux domain. Source's existing credential owner and systemd
LoadCredential supply its current per-instance identity; no new leaf, CA,
store, Main key or application credential is introduced. Keep the core's
domain/key isolation and existing local OEM/read IPC unchanged. Start only
after valid Source enrollment and active Camera component; stop/drain on
Source replacement and component restart. No third VM or Cloud application.

Keep the fixed 720p/FOV-50/JPEG-85 profile, real frame/world/sensor timestamps,
strict metadata/size/age/pair bounds and bounded latest-only queues. Reject
foreign roles/identity/generation, redirects, replay and invalid framing;
fresh authenticated source epochs replace stale sessions after reconnect.
Gateway alone owns capture, never inference or camera consumers. Qualify
transient code/policy removal, actual Aos live pair hashes, negative cases and
unchanged retained state in one M4 scenario. No CARLA/Main Factory rebuild,
new VM, rootfs rewrite or implicit permanent image update is authorized.
Permanent policy/image delivery remains a separate preservation-bound gate.

| Service | Owns | Does not own |
| --- | --- | --- |
| Vision Perception | JPEG decoding, model-specific preprocessing, AutoDrive/AutoSteer/AutoSpeed inference, raw typed outputs and their validity | Fusion, steering/brake commands, Cloud lifecycle or camera selection |
| Vision Assessment | Time-aligned fusion/tracking, shadow planning, interpreted path/object estimates and diagnostic state | Camera capture, model execution, vehicle actuation or installation |

The reviewed upstream is
[`e7e5c614832f175f1f9f10a0d0c0df2559ff2c38`](https://github.com/autowarefoundation/vision_pilot/tree/e7e5c614832f175f1f9f10a0d0c0df2559ff2c38).
Its [pipeline](https://github.com/autowarefoundation/vision_pilot/blob/e7e5c614832f175f1f9f10a0d0c0df2559ff2c38/VisionPilot/modules/models/src/inference.cpp)
currently includes fusion; splitting it requires source work, not two copies
of the executable. Its [main application](https://github.com/autowarefoundation/vision_pilot/blob/e7e5c614832f175f1f9f10a0d0c0df2559ff2c38/VisionPilot/app/vision_pilot.cpp)
also invokes the vehicle output interface. Remove that path from the integrated
entry point and deny motion access independently at the platform boundary.

AutoSteer predicts an ego path rather than measured lane boundaries.
AutoSpeed classifies objects relative to that path, not a general semantic
taxonomy. AutoDrive consumes two frames and estimates lead-object presence,
distance and curvature. UI wording and result schemas must preserve those
meanings. The upstream safety scope is not a vehicle certification.

## Repository and branch ownership

Keep integration, Gateway/native UI and platform changes on
`codex/vision-pilot-single-node` in their existing owning repositories, only
where changes are needed. Preserve `main` and the Brake/Tire repositories.
Exact source locks bind the component revisions; a common branch name is not
a reproducibility guarantee.

Propose one new public repository, `vision-pilot-services`, containing two
service targets, their shared inference types and a pinned upstream dependency.
It produces separately signed/versioned Aos packages. One repository is not
one mandatory release, and no repository per model/executable is required.
This follows [lifecycle-based ownership](0006-lifecycle-based-repository-ownership.md).
Do not create the remote repository as part of documentation planning.

The Vision branch has its own installer identity, defaults, runtime selection
and release descriptor. Git branches alone do not isolate mutable installation
state. Main's operator option A, published DMG and frozen producer records stay
unchanged. Shared fixes can be selectively ported after review; no automatic
merge of the experimental Vision branch into Main is planned.

## Controller image and compute

Start from the retained clean Main Factory, not a provisioned VM or its keys.
The retained Factory contains no installed VDP or functional services. It may
support the isolated core proof without an image rebuild; its VDP-specific
empty-slot runtime is not a qualified Camera Access deployment mechanism.
Use a proposed initial Vision profile of 4 vCPUs and 4 GiB RAM. Preserve the
existing controller's 2-vCPU/2-GiB profile. Additional vCPUs expose capacity to
the guest but do not reserve physical performance cores or provide Apple GPU/
Neural Engine access. Initial inference uses Linux ARM64 ONNX Runtime CPU.

Qualify existing image compatibility before deciding that a new Factory is
needed. If a missing named resource, policy or native configuration requires
an image delta, define one bounded Vision-specific change; do not modify or
replace the current Brake/Tire Factory or rebuild Linux/AosCore speculatively.
Never change a shared Cloud model/configuration in place if the current Unit
depends on it.

The retained Factory 42 root filesystem does not include a ROS installation:
read-only image inspection found no `/opt/ros`, ROS commands or core ROS/DDS
libraries in the standard executable/library directories. Its pinned
[AosVM recipe](https://github.com/aosedge/meta-aos-vm/blob/b13320898a2ed1cce504f90f70451638232d6a83/meta-aos-vm-common/recipes-core/images/aos-image-vm.bb),
[layer selection](https://github.com/aosedge/meta-aos-vm/blob/b13320898a2ed1cce504f90f70451638232d6a83/aos-vm.yaml)
and the project image additions do not install ROS. This is the Lab's Yocto
ARM64 image, not an arbitrary Ubuntu VM that happens to run AosCore. AosCore
and KUKSA are not ROS middleware. Factory 41's declared base uses the same
ROS-free layer selection; its binary was not inspected in this review.

Vision Pilot's
[CPU build](https://github.com/autowarefoundation/vision_pilot/blob/e7e5c614832f175f1f9f10a0d0c0df2559ff2c38/VisionPilot/docker/Dockerfile.cpu)
defaults to ROS2 disabled and installs Jazzy only when explicitly enabled.
The initial image/result path therefore needs no ROS installation in either
the host or Factory. A later ROS adapter must identify its concrete benefit,
runtime/package ownership, distribution, DDS/QoS and resource costs; it is not
an implied prerequisite of deploying an Aos service or running these models.

The dedicated M4 Pro replaces M1 as the installed/live Vision pilot target.
Its measured configuration is 12 CPU cores, 16 GPU cores and 24 GiB RAM.
Actual CARLA plus VM plus host use determines fit; nominal host capacity is
not a model-throughput guarantee. Only one Lab variant runs at a time.
Source/build/cache work uses the development SSD; M4 installation/runtime uses
its internal disk. No live test moves to the development Mac.

Characterize the live camera before implementing the AI services or building
a Vision DMG. Compare the same running workload with no added camera, RGB
capture and JPEG encoding. This separates the camera's rendering/readback and
host CPU/memory cost from inference. Later measure VM delivery/decode, both AI
services and the visible UI together on that same M4. Replay alone cannot
establish whether the combined system fits.

### Authorized first implementation boundary

The first milestone is an isolated Vision VM plus measured execution of the
real models, including a combined camera/compute measurement. It is not a new
DMG, a completed two-service Aos deployment or a full E2E claim.

- Reuse immutable clean Factory 42 and packaged QEMU/HVF. Give the Vision VM
  a new local identity and writable overlay; never clone provisioned keys.
- Keep Main's profile `aos-main-qemuarm64-v1` at 2 vCPU/2048 MiB. The fixed
  engineering profile `aos-vision-main-qemuarm64-v1` uses 4 vCPU/4096 MiB,
  Test role only, loopback SSH port 12022 and its own serial/QMP files.
- Record the selected resource profile in the existing lifecycle journal at
  creation. Reject another profile when a journal already exists; no in-place
  upgrade, silent CPU/RAM override, parallel lifecycle or second state database.
- [D4-029](../../requirements/d4-decision-register.md#d4-029-vision-vm-pilot)
  allocates this local-only resource profile; its executable definition is
  [Vision VM v1](../../../contracts/vision-vm/vision-vm-profile.v1.json).
- Pilot state lives in the separate internal-M4 `SDV-Vision-Lab-Data` instance.
  It may reuse immutable installed runtime/Factory inputs under their existing
  leases. An explicitly pinned engineering adapter is not an activated Vision
  product or permission to modify the installed Main package.
- Stop the retained Main runtime through its normal owner before the Vision
  pilot; preserve its Test, overlay, credentials, package and data. Shared Docker
  Engine is not stopped or relocated.
- Verify boot, actual guest resources, native container facilities, security,
  graceful stop/restart and Main preservation in one named scenario. Do not
  register a Cloud Unit merely to boot or benchmark a local VM.
- Run a bounded diagnostic model closure in the guest before final packaging.
  Measure models individually and together with real preprocessing and a
  bounded image sequence; random-input timings alone are not functional proof.
  Such diagnostics do not satisfy native Aos identity/quota/SOTA acceptance.
- Resource/camera calibration, authenticated image/result transport, complete
  service contracts and the affected design cascade must close before the
  downstream product integration. Keep motion access denied independently.

Plan version 0.4 allocates this boundary to V0/V2 and an early compute
probe; it preserves the V3–V8 obligations rather than claiming them from a spike.

### Authorized live-camera engineering preview

The bounded preview connects the real CARLA camera to CPU models in the
existing Vision VM and displays raw model predictions on M4. The stationary
[v1 preview contract](../../../contracts/vision-vm/live-camera-preview.v1.json)
defines the engineering-only framed input/result channel over the existing
authenticated SSH connection. It introduces no listener, new credential,
container IPC grant, Cloud Unit or alternative production interface.

The stationary profile keeps the unprovisioned source in native Safe Stop. Infer no permission to
release its hold or bypass first connection. Only the host adapter sees CARLA;
the guest worker receives bounded JPEGs and cannot issue motion commands.
Use actual camera/road-plane geometry to derive H and the unchanged upstream
model-view V to derive C. Do not borrow another camera's H.yaml. Geometric
projection checks do not qualify learned estimates on simulated imagery.

Preserve pair capture times and mark AutoDrive unavailable on irregular pairs;
the other models can still process the current image. Show live and processed
images separately, never paint old predictions over a newer live frame. Native
Aos deployment, Assessment, product-level moving acceptance and the installed Driving Control
Vision page remain downstream V2–V8 work. This preview is not a replacement
for the planned MJPEG/native-resource production interface.

The operator additionally authorized a moving M4 preview on 2026-10-31.
[Preview v2](../../../contracts/vision-vm/live-camera-preview.v2.json) retains
the original sensor timestamp while associating the image with the actual
WorldSnapshot timestamp by exact frame ID. No timestamp is extrapolated or
rounded to pass a pair gate; missing associations and genuine gaps are rejected.
Keep v1 receipts frozen. In retained evidence all 899 camera steps were two
world ticks, while 104 matched image timestamps were 50 ms ahead of the world
snapshot. The frame association is an engineering workaround, not proof of
pixel/capture-time accuracy or a CARLA source repair.

Motion comes only from the native Driving Control Autopilot action, with
independent mode/speed/distance observations. Respect holds and native rejection;
never release a foreign operation, directly drive the CARLA actor, provision a
Cloud Unit or fabricate a selected Test to make it move. Inference remains
read-only. Preserve Test/data and use the normal physical Safe Stop at shutdown.

## Image and result semantics

Use a fixed forward-facing sensor on the existing ego vehicle and reuse its
tick owner. Freeze camera calibration, crop/resize and coordinate conventions.
Begin characterization with a 10-Hz, 1280-by-720 source profile and 1024-by-512
model inputs. These are proposed starting parameters, not proven performance.
JPEG/MJPEG is intraframe compression. Interframe codecs and ROS2 are not
initial runtime dependencies; ROS is absent from the inspected Factory and
optional upstream, rather than an integration task assumed to be necessary.

CARLA's [RGB sensor](https://carla.readthedocs.io/en/latest/ref_sensors/#rgb-camera)
returns four-byte BGRA pixels before our JPEG encoding. The starting profile
therefore produces 3,686,400 raw bytes/frame, about 36.9 MB/s at ten delivered
frames per wall second, before copies and rendering/inference costs. JPEG
reduces downstream bytes, not the need to render and read those pixels.
`sensor_tick=0.1` specifies simulation time, not ten frames per wall second.
Measure simulation progress and wall-clock delivery separately. GPU camera
[delivery may lag simulation by several frames](https://carla.readthedocs.io/en/latest/adv_synchrony_timestep/);
use capture identity/time rather than callback arrival as the observation time.

Carry source generation, camera/frame identity, simulation capture time and
calibration identity through every stage. Preserve both the interval within
AutoDrive's input pair and the interval between processed results used by
fusion. Do not treat dropped outputs as equally spaced 100-ms samples.
Render each overlay only on its matching source frame and display actual age.

Keep image buffers, result sizes and diagnostics bounded. No continuous video
recording or new functional Cloud backend is required for the initial live
view. Distinguish no detection, invalid output, stale input, incompatible
versions, service failure and Cloud disconnection. Missing perception never
becomes a zero-distance object or a motion command.

## User experience and independent updates

Vision Presenter presents one Vision controller, its platform and two services.
Replace irrelevant Brake/Tire product controls in this variant rather than
showing them as unavailable. Native Driving Control gains a fixed-size Vision
page without moving driving controls or changing keyboard/Safe Stop semantics.
Preserve the existing icon system and fingerprint-only browser identities.

Perception and Assessment have independent SOTA lifecycles and an explicit
compatibility contract. Demonstrate one compatible independent update of each
service. A mismatched schema/model/calibration profile blocks valid output;
it does not trigger an implicit package replacement or rollback. Keep physical
motion control and the OEM FOTA Safe Stop gate unchanged.

## Alternatives not selected for the initial delivery

AosCore already supports multi-node operation, including
[multiple SM connections](https://github.com/aosedge/aos_core_cpp/blob/9d613a46df3c7f550062e2f19ae3406c57715694/src/cm/smcontroller/smcontroller.cpp),
[placement](https://github.com/aosedge/aos_core_lib_cpp/blob/5560291ba6914e36a5b841ade4d8fc54134a9e91/src/core/cm/launcher/balancer.cpp)
and [targeted node provisioning](https://github.com/aosedge/aos_core_cpp/blob/9d613a46df3c7f550062e2f19ae3406c57715694/src/cm/communication/communication.cpp).
That alternative would introduce topology, network and lifecycle work before
the first Vision result. It is deferred, not a required fallback or a missing
platform capability. Two independent single-node Units do not automatically
become one multi-node Unit later.

A single bundled AI service is simpler but does not demonstrate independent
perception/assessment delivery. One service per neural network adds joins and
data duplication before there is a measured benefit. The two-service cut is
the proposed initial compromise.

## Acceptance and architecture cascade

The [implementation plan](../../planning/active/vision-pilot-single-node.md)
defines ordered deliverables, interface decisions, metrics, failure cases and
candidate-bound API/UI acceptance. Camera characterization is complete;
isolated VM/compute implementation is authorized, not yet accepted as complete.

Before downstream Vision deployment, close the selected-source camera permission,
native IPC/resource placement, service compatibility and standalone installer
contracts. Apply the affected HLA, Scenario, Flows, requirements, component and
D4/interface updates on the Vision branch, preserving IDs and unrelated
obligations. This proposal does not amend those accepted sources on `main`.

Success means a separately installed single-node Vision Lab receives real
CARLA images, executes both services under AosCore, shows matching results,
demonstrates independent updates and passes one automated API/UI scenario,
while the retained Brake/Tire installation and data remain available.
