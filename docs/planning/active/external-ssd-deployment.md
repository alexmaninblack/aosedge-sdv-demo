<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# External SSD Deployment and Clean-System Test Plan

- Status: Plan accepted; disk preparation, Kit 004 transfer, isolated execution and native/negative-input follow-up complete.
- Version: 1.0
- Prepared: 2026-09-27
- Owner: Demo Solution Team
- Parent: [Installable distribution and reproducibility](installable-distribution-and-reproducibility.md)
- Current candidate: [Complete portable application](../../qualification/portable-application-2026-09-26.md)
- Retention input: [Post-assembly disk audit](../../research/distribution-stage2-retention-audit-2026-09-27.md)

## Working SSD configuration on 13 October 2026

The new 4 TB Samsung SSD 990 PRO is prepared for the working Mac with three
APFS volumes in one shared container. The former empty `Work` volume was
renamed to `SDV-Dev`; `SDV-Lab` and `SDV-Releases` were added without erasing
the disk. Existing build media and M1 storage were not changed.

| Volume and mount path | Planning budget | Intended use |
| --- | ---: | --- |
| `/Volumes/SDV-Dev` | 2.5 TB | Build workspaces, Unreal/CARLA, caches, warm Factory Builder disks and temporary installer assembly |
| `/Volumes/SDV-Lab` | 600 GB | Retained diagnostic VM images, checkpoints and reproduction data; not the M1 installation target |
| `/Volumes/SDV-Releases` | 300 GB | Completed releases, manifests, checksums and qualification reports |

The budgets use decimal units and leave approximately 600 GB of planned
container-wide headroom. They are **not APFS quotas or guaranteed reserves**:
each volume can consume the shared free pool. Free space must be counted once
per container, not added across these mounts. The headroom is an operating
policy, not a filesystem-enforced limit.

Durable identities for subsequent mount and migration checks:

| Object | UUID |
| --- | --- |
| APFS container | `30254FDA-F7B7-4A97-A3FB-471F4D423F2B` |
| Physical store | `2BDD6231-5066-4713-89C8-613AD29F2C17` |
| SDV-Dev | `F92AB578-22AA-4DAC-B8DD-7DC0EB831396` |
| SDV-Lab | `A9523BCA-821F-4A69-B71B-514D4EC85458` |
| SDV-Releases | `96800629-557C-46E2-9E8E-10A4DED64B55` |

All three volumes are mounted, writable, unencrypted APFS volumes with quota
and reserve values of zero. Ownership enforcement remains disabled, the
existing external-volume setting; this preparation made no broad permission
changes. Before a workload requiring ownership enforcement is migrated,
configure its ownership explicitly and use a dedicated user-owned project root.

The container capacity is 4,000,577,273,856 bytes; free space immediately after
preparation was 4,000,089,759,744 bytes. Other container and volume identities,
names, quotas and reserves were unchanged.

The operator subsequently authorized copying `/Volumes/SDV-Build/sdv` to
`/Volumes/SDV-Dev/sdv` and switching its active storage bindings. Native macOS
copying completed with exit code zero in 1,803.195 seconds; directory metadata
reconciliation completed with exit code zero in 38.485 seconds. The operator
accepted the copy and stopped the full repeated checksum comparison after
1,423.922 seconds. That comparison is waived, not passed; the remaining full
inventory and DMG checksum gates were not run for this storage operation.

The active preparation controls, input/build storage UUIDs and current release
selection now use `SDV-Dev`. Historical build manifests, completed campaign
selections and dated logs retain their original paths and identities. Current
source revisions and packaged bytes were not changed by the storage switch.
The old `SDV-Build` disk was normally ejected after confirming that no process
held its files; the new SSD remains mounted. Source data on the old SSD is
retained for recovery.

The source volume occupied about 188 GB because APFS clones shared blocks. Its
working tree has about 654 GB of logical file contents, and copying between
physical disks expanded those shared copies. No superseded artifacts were
deleted as part of this move.

The separate M1 remains the installation, API, UI and live E2E test host using
its internal disk. The new SSD is not an M1 dependency. Shared Docker storage
for unrelated projects remains on the working Mac's internal disk. Existing
1 TB media are retained for independent builds and selective recovery; this
configuration does not authorize deleting their contents. The
three new volumes share one device and are not independent backups.

## Clean host disposition on 7 October 2026

The current clean-host campaign uses a separate M1 and its internal disk.
External-SSD and host sleep/wake tests are excluded from that campaign.
The Work/Clean preparation and dual-boot plan below retain their dated scope;
they are not prerequisites for the current installer. Use the
[current baseline](../../qualification/current-baseline.md) and parent plan
for selected media and open gates. Historical disk IDs are never current
destructive-operation targets.

## Scope and authority

The user authorized formatting the newly connected 1 TB external disk, then
accepted this deployment plan and its execution. Preparation is operational infrastructure work,
not a new installer/runtime contract. No application, VM, credential, state root,
Cloud authority or release number changed. No operating system was installed,
no reboot occurred and no internal project artifact was deleted or moved.

Installer format, first-use credentials, state retention and rollback still
require the Stage 3 design gate. A storage directory is not an implicit new
application state store. Source/Git and the separate video repository remain
unchanged by the storage operation.

## Prepared disk and evidence

The new device is a Samsung Portable SSD T5, external physical USB SSD,
1,000,204,886,016 bytes (about 931.5 GiB). It is not the previously inspected
500,107,862,016-byte T5. Its negotiated USB link is 5 Gbit/s. Device identity,
capacity and external/physical status were checked immediately before erasing;
the mounted FAT volume had no observed open handles.

The previous MBR/FAT/Linux partition layout and its data were erased under
that authorization. They were not moved to Trash; no ordinary undo was created.
The internal SSD, current Test .39, Production .31 and their data were preserved.

| Purpose | Mounted volume | Container capacity | Filesystem |
| --- | --- | ---: | --- |
| Packages and isolated installation work | `/Volumes/SDV-Work` | 650,000,003,072 bytes, about 605.4 GiB | APFS |
| Future clean native macOS | `/Volumes/SDV-Clean` | 349,995,126,784 bytes, about 326.0 GiB | APFS |

These are **two separate APFS containers on a GUID-partitioned disk**, not two
volumes sharing the same container. Work artifacts therefore cannot consume
the clean-system partition's capacity. This is capacity separation, not a
security boundary, backup or permission to erase the physical disk again.
Apple documents [APFS container space sharing](https://support.apple.com/guide/disk-utility/add-delete-or-erase-apfs-volumes-dskua9e6a110/mac).

Preparation-time identities:

- Physical device: `disk12`; Work container/store: `disk13` / `disk12s2`;
  Clean container/store: `disk14` / `disk12s3`.
- Work volume UUID: `591578E3-8196-4B44-A575-CEC76B406789`.
- Clean volume UUID: `870130E1-51A1-4ED8-841E-DB84B7941376`.
- Partition-map verification and both read-only APFS filesystem checks passed.
- Neither volume is encrypted. Do not place operator secrets in package stores.
- Ownership enforcement on Work is now enabled and independently verified
  after native administrator authentication. The volume root is correctly
  system-owned. A separate user-owned project directory is required; do not
  change the entire volume's ownership or relax its permissions.

Disk numbers and mount names are not durable identity. Re-resolve UUID, physical
parent, capacity and external status before any destructive or migration action.
If a volume is absent, fail instead of creating an ordinary directory under
`/Volumes` and silently consuming internal space.

### Bounded I/O check

One disposable 1 GiB file was written with Darwin `F_NOCACHE`, flushed with
`fsync`, then read with `F_NOCACHE` and SHA-256 verified. Results: 2.385 seconds
write (450 MB/s), 2.932 seconds read including checksum (366 MB/s). The checksum
matched; the owned file and empty temporary directory were removed immediately.
No raw-device write test or user-file inspection occurred.

This short sequential check supports package-transfer feasibility, not a
sustained-speed claim or CARLA/VM/random-I/O qualification. Device caching and
thermal behavior are not excluded. Compact local evidence and the scoped probe
are in the ignored CARLA `Build-distribution-stage2-20260926` directory:
`external-ssd-io-20260927.json` and `probe_external_ssd.py`.

### Performance assessment and follow-up measurements

The 5 Gbit/s negotiated link has a 625 MB/s arithmetic ceiling before protocol
overhead. The measured 450 MB/s write and 366 MB/s checksum-read are adequate
for the first package-storage use case. At those rates, a 35 GiB sequential
pass takes approximately 84–103 seconds; a real transfer plus digest verification
takes longer because it performs both operations and handles many small files.
This is a planning estimate. The subsequent actual Kit 004 copy, inventory and
per-file hash verification completed in **135.87 seconds** for 32.7 GiB; see the
[external package proof](../../qualification/external-ssd-package-2026-09-27.md).

No comparative internal-SSD benchmark or random-I/O latency test has been run.
Do not turn this sequential result into an FPS estimate or a general slowdown
ratio. The workload distinctions are:

| Workload | Expected sensitivity; not yet comparative qualification |
| --- | --- |
| Package copying, checksum checks and installation | Sustained transfer and small-file metadata operations; appropriate first use |
| CARLA map load, VM boot and image creation | Likely sensitive to external I/O; measure cold and warm duration |
| Steady-state simulation | CPU/GPU/RAM remain important; measure frame-time spikes and asset reads rather than assuming unchanged FPS |
| VM/Docker databases and overlay writes | Latency/random-I/O sensitivity; do not migrate from the sequential result alone |
| Unreal/Yocto compilation and caches | Many small operations plus large temporary output; preserve internal warm build paths initially |

When both Clean macOS and Work packages are active, they share the same SSD and
USB link despite having separate capacity. Concurrent copies, hashing or builds
can compete with the demo. Avoid heavy background I/O during comparative runs.
The first transfer receipt records actual elapsed time and logical byte count;
later approved runtime testing should compare startup, frame-time distribution,
control-response latency and VM/backend behavior using the same package and
scenario, without running duplicate live owners. Keep source/package work and
the current active demo separate until that evidence is available.

## Proposed use of SDV-Work

Engineering artifacts now use one `AosEdge-SDV` directory with the children
below. `packages` holds verified Kit 004 and `reports` holds its compact proof;
`staging` is empty. `install-tests` retains small native-test records and a
192 KiB scratch disk, not a second full installation. The disposable negative
clone has been removed after preserving evidence. None is wired into live
runtime configuration.

| Child | Contents | Retention |
| --- | --- | --- |
| `packages` | Versioned complete candidates and their integrity/provenance manifests | Current candidate and one previous qualified candidate |
| `staging` | Bounded copy, verification and installer-assembly work | One active transaction; failed output removed after preserving useful evidence |
| `install-tests` | Isolated installations and explicitly disposable test state | Current test plus one bounded failure reproduction |
| `reports` | Compact sanitized receipts, measurements and qualification reports | Retain useful evidence; canonical documents stay in Git |

The complete Kit 004 currently accounts for about 32.74 GiB, including its
second Factory catalogue path. Budget approximately 35 GiB for a verified copy
before any test state or installer temporary space. The existing export uses
same-volume APFS clones; **do not assume they work across devices**. A transfer
must use a separately reviewed copy path and verify bytes at that trust boundary.
Do not silently alter the exporter, which currently requires cloning.

Keep at least **90 GiB free on the volume receiving packaging work**, with
additional space reserved for measured peak temporary/output needs. Also retain
the internal build guard for tools that still write internally. The partition
sizes are enforced; the directory retention rules are a plan, not installed
automatic quotas or cleanup jobs.

Do not initially migrate active Test/Production overlays, Docker's disk image,
the warm Yocto Builder, Unreal/CARLA sources, caches or the current runtime.
First prove the artifact and installation paths. Heavy build/cache migration is
a separate measured decision: the external USB link is not assumed equivalent
to the internal SSD, and changing a backing-file path can break a retained VM.

## Execution order and exit gates

1. **Close the ownership prerequisite.** Enable normal file ownership on Work
   using macOS administrator authorization and verify it. Keep Clean empty for
   OS setup. Record actual free space and resolve both volume identities.
2. **Preserve the current candidate.** Copy only Kit 004, manifests and compact
   evidence into an exclusive versioned staging directory; exclude credentials,
   `.local`, `.run`, ledgers, backend histories and provisioned VM disks. Verify
   the complete inventory and transferred hashes before promoting it to
   `packages`. Keep the internal original until independent verification passes.
3. **Repeat isolated artifact proof.** Deny development/Homebrew/Xcode and
   credential reads, use packaged dependencies, verify all five input groups
   and explicit missing-credential behavior. Do not start a second live demo
   beside the preserved one or infer clean-install success from imports.
4. **Implement the accepted installer design.** Close the parent Stage 3
   decisions first, then test installation, repeat/repair, interruption, update,
   removal and insufficient-space behavior in isolated directories. Preserve
   current live identities and release-number continuity. Test absent/wrong
   external volume before launch; do not pull an active disk to simulate it.
5. **Prepare native clean-system qualification.** In an agreed setup/reboot
   window, install a compatible macOS only in the Clean container, with no
   Migration Assistant/developer settings. Apple supports
   [macOS on an external startup disk](https://support.apple.com/en-us/111336).
   Follow its model/port/install requirements; erase neither the whole T5 nor
   Work. OS installation, first login, permissions and startup selection are
   separate steps, not completed by APFS formatting.
6. **Run the clean E2E.** Install only declared prerequisites and the frozen
   package. Prevent accidental reads from the internal development installation.
   Follow the parent Stage 6 scenario: serial version updates, VDP Safe Stop,
   QM service updates, real maneuvers/advisories, Reset, external OFF/ON,
   same-identity ignition, UI/status/layout evidence and authorized Finish.
   A same-Mac external boot is not qualification of other Apple Silicon models.
7. **Recover internal space only after proof.** Retire verified superseded
   artifacts using the retention audit, stopped-owner/open-file/backing checks
   and exact targets. Measure internal free space before/after: deleting an
   APFS clone may recover little while another clone retains the same blocks.

## Operational limits

### Transfer preflight checkpoint

The scoped transfer helper validated the pinned Kit 004 manifest, five input
inventories, Factory catalogue mapping, source file modes and the destination
volume identity/free-space guard. Its first directory creation failed with
`EACCES`: enabling ownership exposes the APFS root's actual `root:wheel` owner.
An explicit native administrator request to create only the user-owned
`AosEdge-SDV` directory then returned `Operation not permitted`. No project
directory or payload was created. Volume flags show a writable mount with no
immutable flag; the narrowly filtered privacy log provided no diagnostic.
The cause of that second denial is not established, and no OS protection was
disabled. The operator subsequently created this exact user-owned directory;
owner/group, mode `0700` and the volume were reconciled before resuming.
The verified transfer and external-only proof now pass, as recorded in the
[qualification checkpoint](../../qualification/external-ssd-package-2026-09-27.md).
An initial proof-harness environment error and its correction are retained there.
No volume-wide permission change or product rebuild was used.

The follow-up passed 27 native checks, including two paused diskless HVF/QMP
cycles and a scratch-image check, plus 12 corruption/missing-file rejections on
a disposable clone. Repeated QEMU preflight was within the existing limit;
62 targeted source regression tests also passed. These do not qualify a guest
boot, live CARLA graphics, fresh Docker engine, installer or clean macOS.
No duplicate simulator or live runtime handoff was attempted. Work free space
after the owned-clone cleanup is approximately 572.3 GiB.

### Preserved boundaries

- The disk adds approximately 931.5 GiB of capacity; formatting alone does not
  free internal space. Internal free space remained approximately 97 GiB.
- Work and Clean share one physical SSD: failure loses both. This is not a
  backup. Keep source and compact evidence in Git; define independent artifact
  recovery before deleting the last needed copy.
- Do not disconnect while processes use files on the disk. Verify stopped
  owners and eject normally; no automatic unsafe unplug/recovery is promised.
- A clean external boot interrupts the current desktop/agent session. User
  setup/login/security approval is still required; preserve checkpoints in files.
- Package transfer and an isolated source/network-denied proof are complete.
  No installer, OS installation, runtime switch, cleanup, source publication
  or clean-host acceptance was performed by this disk task.
