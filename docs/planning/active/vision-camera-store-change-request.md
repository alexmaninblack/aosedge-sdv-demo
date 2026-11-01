<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Vision Camera Store Isolation Change Request

- Status: Proposed; required before further native Camera activation
- Prepared: 2026-11-01
- Owner: SDV Lab architecture and OEM platform
- Parent: [Vision implementation packet](vision-pilot-single-node.md#current-signed-bootstrap-and-native-camera-access-packet)
- Requirement boundary: [`REQ-CAM-005` and `REQ-CAM-006`](../../requirements/components/camera-access.md#req-cam-005)

## Observed boundary

The separate signed Vision bootstrap was built on SDV-Dev and installed on M4.
Normal manufacture and official OEM/SDK provisioning created its own Vision
Unit, single Main Node and verification recipient. The retained Brake/Tire and
engineering Vision journals are unchanged. The Camera OEM bundle was signed
and uploaded once; Cloud verification queued the exact candidate automatically.
Cloud catalog readiness is not native activation.

The native runtime initially rejected `bin/camera-access` because archive
executable validation still allowed only `bin/vehicle-data-provider`. The
profile-bound source fix passed 86 ARM64 runtime/archive unit cases, with two
opt-in live VDP cases excluded. A temporary SM target on M4 passed this archive
gate and reached the real offline Camera self-test.

That self-test fails in Enforcing mode: Camera files have `aos_var_run_t`, while
the installed policy correctly expects `camera_access_store_t`. Audit records
show a denied file `getattr` by `camera_access_t`. The built Vision image's fstab
mounts the complete Aos workdirs filesystem with
`context=system_u:object_r:aos_var_run_t:s0`. This is a filesystem-wide forced
context, not an incorrect per-inode xattr. A scoped restorecon fails; a systemd
tmpfiles relabel does not change the effective context. Repeating either is not
a solution. No policy allowance was added, and no component activation pass
is claimed.

## Proposed bounded change

Use the platform's existing demonstration storage pattern described in the
[native OEM runtime decision](https://github.com/alexmaninblack/aos-vehicle-platform/blob/81d098e5a958710d8c12a6bfdb86c7c493274920/docs/decisions/0001-service-manager-component-runtime.md):
a fully allocated ext4 backing file inside Aos workdirs, mounted at the unchanged
logical component root with its own fixed SELinux context. Instantiate it
independently for Camera Access; never reuse a VDP file, filesystem UUID, mount,
slot, credential, Unit or data directory.

The proposed Camera binding is:

| Item | Proposed value |
| --- | --- |
| Logical root | `/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access` (unchanged) |
| Backing file | `/var/aos/workdirs/sm/runtimes/.camera-access-store.ext4` |
| Size and creation reserve | 512 MiB fully allocated; retain at least another 512 MiB free |
| Identity | Root-owned private identity record with a newly generated per-Unit filesystem UUID |
| Filesystem label | `aos-camera-store` |
| Effective context | `system_u:object_r:camera_access_store_t:s0` |
| Mount restrictions | `nodev,nosuid,noatime,errors=remount-ro` plus the exact context |
| Lifecycle | Existing bootstrap layout/prepare/attach/mount/check pattern, before SM and Source restoration |

Close first-create, interrupted preparation, idempotent reuse, identity checks,
bounded capacity, loop attachment, dependency ordering, cold boot and unmount
behavior before adding this backend to a signed image. Update the Vision Source
store check to verify this exact backing/mount identity; no arbitrary mount or
directory fallback. Keep signed Camera payload identity, A/B transaction engine,
physical Safe Stop, read-resource contract and current Main image unchanged.

This is a demonstration backend, not a production vehicle storage claim.
Changing the shared workdirs context, granting Camera general file access to
`aos_var_run_t`, using root for Camera, or reusing the VDP store are not accepted
alternatives. The storage backend is not yet implemented or approved by this
change request.

## Resume and acceptance

After the backend contract is accepted, first prove the exact storage binding
reversibly on the isolated native Vision target. Preserve the failing target
and its Cloud identity; do not hide existing contents beneath a new mount or
automatically migrate them. A clean successor uses the normal manufacture owner
with an explicitly declared retained-versus-fresh policy, never an overlay rebase.

Only after targeted compile, primitive/security proof and source gates pass,
build/sign one incremental Vision bootstrap successor on SDV-Dev. Then complete
native Camera first activation, repeat/restart, actual Aos consumer UID/GID,
read-only mount and JPEG pair hashes, producer/control denial, fresh scoped
AVCs and stop/reinstantiate revocation. Perception, authenticated Gateway camera
ingress, UI and full Vision E2E remain separate gates.

## Evidence and preservation

Private compact evidence is retained under the integration worktree's
`.local/remote-qualification/vision-vm-m4/`: `signed-bootstrap-01`, the two
inventory observations, and `native-camera-01` through `native-camera-05`.
Source/compile/image receipts are retained on SDV-Dev under
`sdv/build/vision-bootstrap/0.1.0/evidence`. The latest bounded scenario stopped
before CARLA, restored stock SM, stopped the native VM and verified both
retained journals unchanged. Earlier stop timeouts were reconciled through
the normal VM owner, not forced termination. No SP reader service or Subject
has been published/created. No Main merge or public upload occurred.
