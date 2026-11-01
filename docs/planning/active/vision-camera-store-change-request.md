<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Vision Camera Store Isolation

- Status: Accepted on 2026-11-01; storage and activation passed, transient native-resource proof passed, permanent image-policy acceptance pending
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

## Accepted bounded change

Use the platform's existing demonstration storage pattern described in the
[native OEM runtime decision](https://github.com/alexmaninblack/aos-vehicle-platform/blob/81d098e5a958710d8c12a6bfdb86c7c493274920/docs/decisions/0001-service-manager-component-runtime.md):
a fully allocated ext4 backing file inside Aos workdirs, mounted at the unchanged
logical component root with its own fixed SELinux context. Instantiate it
independently for Camera Access; never reuse a VDP file, filesystem UUID, mount,
slot, credential, Unit or data directory.

The accepted Camera binding is:

| Item | Accepted value |
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
bounded capacity, loop attachment, dependency ordering and unmount behavior
before adding this backend to a signed image; qualify cold boot on that exact
image before accepting the native deployment. Update the Vision Source
store check to verify this exact backing/mount identity; no arbitrary mount or
directory fallback. Keep signed Camera payload identity, A/B transaction engine,
physical Safe Stop, read-resource contract and current Main image unchanged.

This is a demonstration backend, not a production vehicle storage claim.
Changing the shared workdirs context, granting Camera general file access to
`aos_var_run_t`, using root for Camera, or reusing the VDP store are not accepted
alternatives. Operator acceptance authorizes implementation, not a claim of
successful native activation or a broader storage migration.

## Resume and acceptance

The encrypted workdirs volume is created by native OEM provisioning, so an
unprovisioned disposable VM cannot qualify this backend. Prove the binding on
the existing isolated native Vision Unit: stop its SM, rename the complete
failing Camera subtree to a fixed private preservation path, and restore the
same directory after the proof. Arm rollback before moving it. Preserve the failing target
and its Cloud identity; do not hide existing contents beneath a new mount or
automatically migrate them. Preserve its disk/identity while a clean successor
uses the normal manufacture owner
with an explicitly declared retained-versus-fresh policy, never an overlay rebase.

The successor is `SDV-Vision-Camera-Lab-Data`, Factory
`6.1.1-vision-camera.2`, with its own `SDV Vision Camera Verification` set.
Retain the previous `SDV-Vision-Native-Lab-Data` and its Cloud identity/set.
Reuse the exact already signed/published Camera Access 0.1.0 payload after
authoritative catalog and digest checks; do not republish it or widen the
existing global OEM verification-recipient guard. SP probe assignment is
limited to the new Unit's own Subject.

Only after targeted compile, primitive/security proof and source gates pass,
build/sign one incremental Vision bootstrap successor on SDV-Dev. Then complete
native Camera first activation, repeat/restart, actual Aos consumer UID/GID,
read-only mount and JPEG pair hashes, producer/control denial, fresh scoped
AVCs and stop/reinstantiate revocation. Perception, authenticated Gateway camera
ingress, UI and full Vision E2E remain separate gates.

## Evidence and preservation

The reversible storage scenario `camera-store-proof-11` passed: first-create,
idempotent repeat, detach/reattach with retained data and UUID, wrong label and
malformed UUID denial, unsafe backing-mode denial, nonempty-root denial and
partial-identity denial. Enforcing remained enabled; no fresh scoped AVCs were
observed. The original directory inode and kernel policy were restored, all
temporary mounts/module removed, VM stopped and three retained journals
verified unchanged. This is not native Camera or container acceptance.

The original successor image passed 86 completed ARM64 runtime/archive unit cases and
package/rootfs QA; two opt-in live VDP cases remain excluded, not passed.
That image's platform Camera suite passed 34 cases; its full Python suite
completed 276 cases with three skips. The image reused the warm SSD Builder
and did not rebuild CARLA or the Main Factory.

The signed 0.2.0 successor passed normal manufacture and OEM/SDK provisioning
in `signed-bootstrap-02` (152.34 seconds on M4, 190.48 seconds including
transfer). Its independent store was verified live. The initial native campaign
observed a different boundary: Cloud had automatically queued the previously
published Camera package before Source's first enrollment. The native writer
was waiting for Safe Stop while Source refused initial enrollment. The accepted
[first-enrollment change request](vision-camera-first-enrollment-change-request.md)
is now implemented and signed in bootstrap 0.2.1. On the same retained VM/Unit,
the normal SM committed that same candidate after real physical Safe Stop.
Daemon restart and an independent retained cold boot confirmed the installed
record, store and guest hardware. No transaction was deleted or rewritten to
manufacture an activation pass.

The [native-resource source/proof receipt](../../../contracts/vision-vm/camera-access-native-resource-source.v1.json)
records actual Aos-container UID/GID, read-only delivery and JPEG hashes,
producer/control denial, SOTA revocation and clean fresh scoped AVCs under a
reversible policy. The corrected policy passed 35 Camera cases, 277 Python cases
with three skips, and targeted compilation of the full Camera policy and both
native launchers. It is committed but not installed in image
`6.1.1-vision-camera.2`: the temporary kernel policy was restored exactly and
removed. The retained cold-boot check is functional-only, not permanent
image-policy acceptance. The remaining delivery boundary is recorded in the
[first-enrollment packet](vision-camera-first-enrollment-change-request.md#remaining-native-image-acceptance).

Private compact evidence is retained under the integration worktree's
`.local/remote-qualification/vision-vm-m4/`: `signed-bootstrap-01` and
`signed-bootstrap-02`, `camera-store-proof-11`, the inventory observations,
and `native-camera-01` through `native-camera-13`, including the separate
retained-cold-boot observation. Failed receipts remain failed, with their
diagnosis and restoration evidence intact. Source/compile/image receipts are
retained on SDV-Dev under `sdv/build/vision-bootstrap/0.1.0/evidence` and
`sdv/build/vision-bootstrap/0.2.1`.

Owned Source/CARLA/VM/DNS and Builder processes are confirmed stopped; the three
other retained journals are unchanged. The diagnostic SP reader and its Subject
are limited to this Vision Unit; the latest delivered service version has no
Camera resource, and cold boot retained that revocation. Preserve the current
VM, Unit, installed component, evidence and data. No Main merge, public upload,
replacement VM, rootfs remount or overlay rebase occurred. Authenticated Gateway
camera ingress, Perception and full Vision E2E remain separate unexecuted gates.
