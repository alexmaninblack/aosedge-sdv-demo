<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0019: A Separate Single Node Vision Lab

- Status: Accepted for the isolated M4 VM, compute and engineering live previews; downstream interfaces remain subject to V2 closure
- Version: 0.6
- Prepared: 2026-10-28
- Updated: 2026-10-31
- Owner: SDV Lab System Architecture
- Change class: C; bounded VM pilot accepted, downstream Vision contract closure remains required
- Direction selected: independent Brake/Tire and Vision single-node tracks
- Scope: isolated VM, bounded compute and stationary/moving live-camera engineering previews authorized on 2026-10-31; no implicit Main merge, public release or unrelated Cloud mutation
- Architecture input: [High-Level Architecture 1.8](../high-level-architecture.md)
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

The first version runs the two Lab variants sequentially. It does not require
a universal profile selector, simultaneous source attachment, multi-node
management, distributed scheduling or inter-node credentials.

## Runtime boundaries

```text
Retained Brake/Tire track                 Separate Vision track
main                                     codex/vision-pilot-single-node
existing installation and private state   separate installation and private state
existing single-node Unit                new single-node Unit
existing Main VM                         larger Main VM: CM + IAM + SM
VDP + KUKSA/KAC + Brake + Tire             platform image/data adapter + local KUKSA
                                         Vision Perception + Vision Assessment

Vision data flow
CARLA RGB camera -> Vehicle Gateway -> OEM platform adapter
                                          |
                                          v
                               Vision Perception
                                          |
                          vehicle speed -> Vision Assessment
                                          |
Driving Control <- Vehicle Gateway <- OEM platform adapter
```

The platform adapter owns selected-source access and typed result validation.
Images do not pass through scalar VSS/KUKSA values. Vehicle speed continues
to use the authorized platform/KUKSA path. Services receive no CARLA control
endpoint, VDP private key, Cloud producer credential or arbitrary VISS writer.
The existing [QM containment boundary](0011-qm-service-containment-and-evidence-backed-oem-approval.md)
remains authoritative.

Prefer extending the existing VDP application with an isolated, bounded image
and result worker, delivered through its OEM lifecycle, over introducing a
second platform lifecycle manager. Freeze the actual service-facing native
resource/authentication mechanism before implementation. A camera permission
is not implied by a service's ordinary KUKSA read permission.

## Service responsibilities

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

Before downstream Vision product implementation, close the selected-source camera permission,
native IPC/resource placement, service compatibility and standalone installer
contracts. Apply the affected HLA, Scenario, Flows, requirements, component and
D4/interface updates on the Vision branch, preserving IDs and unrelated
obligations. This proposal does not amend those accepted sources on `main`.

Success means a separately installed single-node Vision Lab receives real
CARLA images, executes both services under AosCore, shows matching results,
demonstrates independent updates and passes one automated API/UI scenario,
while the retained Brake/Tire installation and data remain available.
