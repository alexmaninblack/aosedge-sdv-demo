<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Vision Perception, Assessment and OEM Exchange Requirements

- Status: Accepted; implementation and live acceptance are separate gates
- Version: 0.1
- Prepared: 2026-11-01
- Owner: Vision services and OEM platform
- Architecture input: [High-Level Architecture 1.10](../../architecture/high-level-architecture.md)
- Flow input: [Native service flow](../../architecture/demo-scenario-architecture-flows.md#af-vis-services)
- Decision: [accepted packet](../../planning/active/vision-services-native-delivery.md)
- Executable contract: [Vision services v1](../../../contracts/vision-vm/services.v1.json)

## Boundary and stable obligations

Two headless applications use a nonroot OEM exchange adapter inside the separate
Vision Camera Access package. Native Aos owns resource/identity/quota/SOTA;
Source owns selected-Unit enrollment. No service gets a key, control connection,
VDP import, OEM lifecycle or inferred context/result authority from camera read.

Source/Gateway owns the digest-bound real-camera calibration profile and exact
per-image planar maps. Perception reads only this projection through pair-bound
publish-resource status; Assessment reads it through context-read. AutoDrive's
training-view warp and AutoSteer/AutoSpeed's resized-pixel fusion map are distinct.
Missing/invalid geometry is unavailable, not a borrowed example homography.
AutoSteer's raw finite `h_vector` is a height/mask, not a bounded probability;
preserve its values and the upstream mask threshold without sigmoid or clamp.

| ID | Derived requirement | Parent | Stable isolated proof |
| --- | --- | --- | --- |
| <a id="req-vis-001"></a>`REQ-VIS-001` | Separate targets/versions and exact role-specific native resources, no network/control dependencies. | [`SYS-VIS-009`](../system-requirements-and-traceability.md#sys-vis-009) | <a id="ut-vis-001"></a>`UT-VIS-001`: composition, permission and incompatible independent-update negatives |
| <a id="req-vis-002"></a>`REQ-VIS-002` | Bound JPEG decode and digest/profile/model/calibration validation; exact upstream preprocessing and raw FP32 outputs. | [`SYS-VIS-010`](../system-requirements-and-traceability.md#sys-vis-010) | <a id="ut-vis-002"></a>`UT-VIS-002`: injected model/decoder, shape/precision/profile/cadence/hash and malformed input cases |
| <a id="req-vis-003"></a>`REQ-VIS-003` | Exact-frame trusted speed/geometry only through OEM context scope; missing data never becomes zero/default data. | [`SYS-VIS-011`](../system-requirements-and-traceability.md#sys-vis-011) | <a id="ut-vis-003"></a>`UT-VIS-003`: source/frame/time/units, missing geometry/speed and wrong role cases |
| <a id="req-vis-004"></a>`REQ-VIS-004` | Explicit actual inter-result delta, independent horizon step, producer/source/calibration/gap reset and nullable target semantics. | [`SYS-VIS-012`](../system-requirements-and-traceability.md#sys-vis-012) | <a id="ut-vis-004"></a>`UT-VIS-004`: injected clock, first/reset/regression/gap, no-target sentinel and invalid-fusion cases |
| <a id="req-vis-005"></a>`REQ-VIS-005` | Closed bounded DTO/IPC, latest-only slots, finite values, exact compatibility and idempotent identical publication; conflicts fail closed. | [`SYS-VIS-013`](../system-requirements-and-traceability.md#sys-vis-013) | <a id="ut-vis-005"></a>`UT-VIS-005`: duplicate/unknown fields, bytes/counts, replay/conflict/epoch and replacement cases |
| <a id="req-vis-006"></a>`REQ-VIS-006` | Display-only interpreted results and matching frame overlays; no actuator/advisory route or full browser identity disclosure. | [`SYS-VIS-014`](../system-requirements-and-traceability.md#sys-vis-014) | <a id="ut-vis-006"></a>`UT-VIS-006`: forbidden operations/imports, stale/reset and public projection tests |
| <a id="req-vis-007"></a>`REQ-VIS-007` | Exact bounded ARM64 closures, licenses/SBOM and per-profile ceiling without global guard relaxation; measured fixed-VM quotas. | [`SYS-VIS-015`](../system-requirements-and-traceability.md#sys-vis-015) | <a id="ut-vis-007"></a>`UT-VIS-007`: escaping links/paths, architecture, digest, missing notice/model and ceiling cases |
| <a id="req-vis-008"></a>`REQ-VIS-008` | Preserve exact Vision/retained identities and data, serial known-intent delivery, independent actual effects and verified normal cleanup. | [`SYS-VIS-016`](../system-requirements-and-traceability.md#sys-vis-016) | <a id="ut-vis-008"></a>`UT-VIS-008`: scenario gate/unknown-effect/cleanup/retained target negatives |

## Verification levels

Isolated tests inject clocks, buffers, inference and transport and run no real
VM, Cloud, simulator or model. Reference algorithm fixtures, actual models,
native resource/UID/group/mount/SELinux and calibrated replay run on M4; CPU
build/compile work stays on SSD. A manual crun, SSH engineering worker or source
test does not establish native service identity/quotas or API/UI acceptance.
The final scenario retains live versus replay, independent SOTA and visible UI
as distinct gates, reports timings and NOT_RUN cases, then verifies owned exit.
