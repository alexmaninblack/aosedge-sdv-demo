<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# OEM Camera Access Requirements

- Status: Accepted source and native-boundary contract; live deployment remains gated
- Version: 0.3
- Prepared: 2026-10-31
- Owner: OEM Vehicle Platform
- Architecture input: [High-Level Architecture 1.9](../../architecture/high-level-architecture.md)
- Flow input: [Camera Access flow](../../architecture/demo-scenario-architecture-flows.md#af-vis-cam)
- Decision: [ADR 0019 v0.9](../../architecture/decisions/0019-vision-pilot-single-node-lab.md)

## Boundary

Camera Access is the separate Vision VM's OEM platform component, not a VDP
extension or a Perception service. `aos-vehicle-platform` owns its source and
payload. It owns selected-camera image admission, metadata and bounded delivery;
Gateway owns simulator capture, Perception owns the three models, native Aos
owns resource/deployment enforcement. The retained Brake/Tire VM, its VDP,
component slot, credentials and data are outside this package.

The source foundation opens no file/device/listener, starts no runtime, decodes
no pixels and grants no native resource. Source binding is a trusted in-process
OEM input, not a service claim or a substitute for authentication. The initial
profile is front RGB 1280x720 JPEG/FOV 50, world-frame clock association with the
unchanged original sensor time. It does not qualify image/capture-time accuracy.

## Derived requirements

| ID | Requirement | Parent |
| --- | --- | --- |
| <a id="req-cam-001"></a>`REQ-CAM-001` | Keep Camera Access source/payload/target distinct from VDP and retain the old VM unchanged. Require exact trusted camera/source/epoch/calibration selection; an identical active selection is idempotent. | [`SYS-VIS-005`](../system-requirements-and-traceability.md#sys-vis-005), [`SYS-VIS-008`](../system-requirements-and-traceability.md#sys-vis-008) |
| <a id="req-cam-002"></a>`REQ-CAM-002` | Validate closed metadata, fixed profile, digest, 4-MiB JPEG size and SOF dimensions before decoder allocation. Reject foreign source/epoch/calibration, wrong clock, replay, regression and sensor/world disagreement over 75 ms; never interpolate time. | [`SYS-VIS-006`](../system-requirements-and-traceability.md#sys-vis-006) |
| <a id="req-cam-003"></a>`REQ-CAM-003` | Retain at most two immutable frames/8 MiB JPEG bytes, replace rather than queue, expose fixed counters and deliver the latest real 80–120 ms pair once per Perception cursor. | [`SYS-VIS-006`](../system-requirements-and-traceability.md#sys-vis-006) |
| <a id="req-cam-004"></a>`REQ-CAM-004` | Expose unavailable/warming/available/locally stale states. Bound both pair members to one second receiver-monotonic age; invalid input never refreshes age. Disconnect clears pixels without losing current-epoch replay protection; an explicit new binding flushes old frames. | [`SYS-VIS-007`](../system-requirements-and-traceability.md#sys-vis-007) |
| <a id="req-cam-005"></a>`REQ-CAM-005` | Keep metadata validation distinct from native authentication. Prove actual Aos peer/resource/SELinux/revocation isolation before container delivery; add no credential store, KUKSA permission shortcut or motion/configuration authority. Full IDs/pixels remain server-side, not public status. | [`SYS-VIS-008`](../system-requirements-and-traceability.md#sys-vis-008) |
| <a id="req-cam-006"></a>`REQ-CAM-006` | Qualify a distinct Camera Access OEM target before activation; never treat the VDP-specific slot/runtime as generic. A native process restart must establish a fresh authenticated upstream session/epoch before admission. Source-only tests are not FOTA/live/UI acceptance. | [`SYS-VIS-005`](../system-requirements-and-traceability.md#sys-vis-005), [`SYS-VIS-007`](../system-requirements-and-traceability.md#sys-vis-007), [`SYS-VIS-008`](../system-requirements-and-traceability.md#sys-vis-008) |

## Stable unit-test obligations

| ID | Isolated proof | Requirements |
| --- | --- | --- |
| <a id="ut-cam-001"></a>`UT-CAM-001` | Selection, identical reuse, foreign/new binding and composition/profile parity | `REQ-CAM-001` |
| <a id="ut-cam-002"></a>`UT-CAM-002` | Malformed/oversized JPEG envelope, exact schema/digest/dimensions, replay/regression and unchanged raw time | `REQ-CAM-002` |
| <a id="ut-cam-003"></a>`UT-CAM-003` | Bounded retention, latest pair, slow reader, immutable frames and counted replacement | `REQ-CAM-003` |
| <a id="ut-cam-004"></a>`UT-CAM-004` | Injected receiver clock, stale members, no age renewal, disconnect/reconnect and epoch/calibration flush | `REQ-CAM-004` |
| <a id="ut-cam-005"></a>`UT-CAM-005` | No runtime/Cloud/VDP/model dependency or public source/pixel disclosure | `REQ-CAM-005` |
| <a id="ut-cam-006"></a>`UT-CAM-006` | Distinct payload/target mapping and restart binding; native activation requires its separate live proof | `REQ-CAM-006` |

## Native allocation

The [signed Vision bootstrap](../../../contracts/vision-vm/bootstrap.v1.json)
supplies the isolated input before native acceptance. Verify its Apple identity,
base-program binding and source/image digests. Normal manufacture/VM/Unit owners
remain authoritative. Use a fresh native Vision instance/Unit; retain the old
Main and engineering Vision disks, keys and data. This adds no arbitrary image
override, public release, alternate lifecycle manager or motion authority.

`vision-camera-read` is a native Aos resource, allocated to at most one
Perception instance. It assigns `aos-camera-read` and mounts only the read
socket directory, never the OEM socket or component store. The protocol accepts
only status/pair, with a 4096-byte header and absolute two-second connection
deadline. Observe real UID/GID/mount/SELinux effects; read-only bind alone is
not socket authorization. Stop/reinstantiate consumers for resource revocation.

The `camera-access-v1` native OEM profile selects its own identity, unit,
health adapter and A/B store. Keep VDP defaults, physical Safe Stop and durable
recovery unchanged. The Vision-only bootstrap provides the missing dedicated
account/resource/target; no overlay rebase or Main image replacement is allowed.
An OEM-local producer is not authenticated Gateway ingress. Do not claim a
normal native service/activation pass from source, root or manual-crun probes.

The platform's `test_camera_access.py` isolates clocks and inputs without any
VM/network/simulator. Synthetic JPEG headers prove admission, not pixel decode.
Native first-create/repeat/restart, real consumer delivery, ingress security,
revocation, SELinux, OEM slot/update isolation and old-VM preservation require
one later scenario on M4. No source test substitutes for those gates.
