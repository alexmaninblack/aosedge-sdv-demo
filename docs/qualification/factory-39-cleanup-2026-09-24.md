<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .39 — artifact revision and cleanup

Date:24 September2026. Status: authorized cleanup completed, with explicitly
retained dependencies and open-handle exclusions below. No new build or baseline
promotion. Source at entry: solution `e7c3b85`, platform `793b1fc`.

## Authorization and retained state

The operator requested removal of previous images and obsolete artifacts made
on the way to .39. After dependency inspection the operator explicitly selected
**preserve Production and its .31 image**. No Production retirement is attempted.

- Current Test VM `48a0e19c-857f-44b8-9b68-38b585a8278f` and staging Unit
  `5395f7d6-2ff3-4d10-9e7f-efa85e7994eb` remain intact.
- Retain Factory .39 catalog image, its independent local Test backing image,
  current validation overlay and immutable manifest. Catalog SHA-256 remains
  `741a9717c4152dfe9baa997fcdd948fa5662e71473b0a7c91faba942aa63c557`.
  Use recorded creation/transfer hashes and unchanged identity/size/mtime; no
  redundant multi-gigabyte rehash was performed for cleanup.
- Retain Production VM `54d45d8f-7813-43aa-81c9-09152cbee0f7`, its overlay and
  `.local/factory/oem-demo-factory.img` (.31). Its recorded Cloud Unit is
  `d87ba9cb-b21f-45db-8773-553e52d0353e`. Journal metadata is unchanged; a stale
  recorded RUNNING PID is not treated as proof of an actually running process.
- Retain Builder, its .31/.39 outputs, source layers including active
  `aos-vehicle-platform-793b1fc035d2b7c123f9a4161788955f389bb81d`, Yocto work tree,
  downloads/sstate, .39 evidence, service packages, credentials and release ledgers.
- Preserve Git/source, all image manifests, compact build/qualification logs,
  the video repository/assets, CARLA binaries/shader caches and other projects.

## Removed on the Mac

Artifact prefix: `demo-artifacts/aosedge-sdv-demo/factory-images/` relative to
the workspace. These three independent regular files were removed:

- `6.1.1-maninblack.36/main-qemuarm64.img`
- `6.1.1-maninblack.37/main-qemuarm64.img`
- `6.1.1-maninblack.38/main-qemuarm64.img`

Before removing the parents, deleted the eight disposable smoke disks below
`/private/tmp/aos-mainline-migration-20260923.A2qEwO/`:

| Subdirectory | Removed files |
| --- | --- |
| `factory36-smoke/local` | `factory36.qcow2`, `factory36-store.qcow2` |
| `factory37-smoke/local` | `factory37.qcow2`, `factory37-store.qcow2` |
| `factory38-smoke/local` | `factory38.qcow2`, `factory38-store.qcow2` |
| `factory39-smoke/local` | `factory39.qcow2`, `factory39-store.qcow2` |

These are completed smoke-test disks, **not** the active .39 validation overlay.
Their scripts, manifests, logs and test results remain. Allocated file blocks
removed:21,151,956,992 bytes (**19.70GiB**),11 files.

## Removed inside the isolated Builder

Builder was initially stopped. Started it through its established lifecycle on
port10024 only, audited without compiling, then returned it and its DNS bridge
to STOPPED. Test/Production ports and lifecycle were not changed.

Under `/home/yocto/r61-build/project/`, removed:

- `factory29/main-qemuarm64.img`;
- `main-qemuarm64-factory-30.img`;
- `main-qemuarm64-factory-32.img` through `main-qemuarm64-factory-38.img`
  (seven individually inventoried exact files).

Under `/home/yocto/r61-build/`, removed only these completed diagnostic outputs:

- `sm-async-live-proof/build`
- `sm-async-live-proof/core-build`
- `cm-cold-live-proof-20260924/build`
- `cm-cold-live-proof-20260924/core-build`

Parent source/dependency directories, retained binaries, receipts and exported
test evidence remain. Allocated blocks removed:7,304,859,648 bytes
(**6.80GiB**),9 files and4 build directories. Both .31 and .39 images and active
`bblayers.conf` retain their pre-cleanup identity/size/mtime.

Normal `fstrim /` in this Builder reported107.2GiB of free guest ranges submitted
to its `discard=unmap` disk. That number is **not** additional space deleted or
necessarily new host space recovered. Downloads13,207,572KiB and
sstate17,287,344KiB are unchanged by the cleanup. The Builder disk still contains
the warm build environment and occupies about106GiB on the host.

## Checks, accounting and remaining candidates

- Exact targets were resolved before mutation; regular-file/directory identity
  checks, backing graph and mounts/loop devices were inspected. Every deleted
  target had zero open handles. No active compiler/build process was present.
- Each target has a flushed ATTEMPTED→REMOVED receipt; no broad glob deletion,
  reset, overlay rebase, rebuild, Cloud deletion or Docker prune was used.
- The image catalog now lists **only .39**, with no metadata issues. Historical
  manifests remain, but their absent old binaries are not offered for Create.
- Full-interval source/control/Cloud checks remain separate from this disk task.
  The post-cleanup Cloud read at19:04:29UTC reports ONLINE,117/92/49 installed,
  both services active and no pending/error. At19:02:29 control is fresh/unheld,
  Safe Stop,0km/h, brake1.0, same source run. Both demo backends remain healthy;
  other running Docker projects remain uninterrupted.
- Total removed allocated file blocks: **26.50GiB**. Mac free space observed
  approximately143GiB at entry and167GiB at exit. These rounded live filesystem
  readings include concurrent system activity/APFS effects, not an exact
  attribution of every free byte to this cleanup.
- About**2.12GiB** of host diagnostic outputs (`app-build`, `lib-build`,
  `cm-build`, `cm-lock-build`, `openssl-build`, `gtest-1.14-build` beneath the
  dated mainline proof root) remain: Docker's virtualization file service still
  holds files there despite the build containers having ended. Do not remove
  them under the zero-open-handle rule. A later coordinated Docker stop/restart
  and fresh handle check is needed; that would interrupt active demo backends
  and an unrelated running project, so it was not done here.
- Docker reports11.16GB build cache (10.17GB reclaimable) and291.7MB reclaimable
  images. These are shared/warm caches or insufficiently attributed images,
  not approved exact obsolete targets. No global prune or volume removal.

Host cleanup proof/receipts:
`/private/tmp/factory39-cleanup-20260924.lsXUuP`. Builder receipts:
`/home/yocto/r61-build/cleanup39-evidence-20260924`.
Deleted binaries/disks are not in Trash and cannot be undone in the application;
retained source/manifests permit rebuilding artifacts, but not restoring a
deleted smoke VM's runtime state. Existing Test and Production state is preserved.
