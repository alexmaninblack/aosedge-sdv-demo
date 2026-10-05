<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Development disk audit and cleanup

- Date: 2026-10-02
- Status: Authorized cleanup and LFS relocation complete; full media assembly follows
- Scope: Development Mac internal storage and the connected SDV Work volume

Internal free capacity increased from approximately 142.7 GiB to 185.4 GiB
(about 199 GB). The two scoped operations measured approximately 42.5 GiB of
recovery. Small differences reflect concurrent application writes. The Work SSD
now has approximately 403.5 GiB free, before full DMG assembly.

## Audit results

Allocated-directory figures below may share APFS blocks and must not be added
as independent physical usage. Whole-volume free space is the recovery measure.
Protected macOS directories could not all be traversed; no permission bypass or
full-disk-access grant was used. The audit covered visible project, home,
Library, Applications, system-data, temporary and Docker storage categories.

| Area before cleanup | Approximate GiB | Disposition |
| --- | ---: | --- |
| OpenAI project directory | 364.6 | Inspect project categories, not a recursive cleanup target |
| CARLA tree | 108.1 | Includes 40.4 GiB of LFS objects relocated below; working source and assets retained |
| Unreal Engine checkout | 99.7 | Retained source and rebuild toolchain |
| Video project | 96.0 | Only five completed verification jobs removed; original media and current montage retained |
| Demo artifact catalogue | 35.0 | Preserve current Factory, Production dependencies, releases and build inputs |
| Yocto Builder | 79.0 | Retain stopped warm Builder with its backing chain, downloads and shared cache |
| Docker data directory | 14.4 | Five unrelated Watt application containers are running; no engine stop or prune |
| User Library | 231.9 | Includes Builder and Docker above, personal cloud documents, application state and caches; not a deletion target |
| Applications | 40.8 | No application removed |
| Temporary directory | 0.3 | No material capacity gain available; keep compact diagnostic inputs |

No Data-volume APFS snapshots were reported. Docker's reported 11.16 GB build
cache is not independently additive to its virtual disk; global pruning was
not justified while preserving unrelated work. Personal iCloud/OneDrive,
Downloads, application databases and active updater caches were left unchanged.

## Verified actions

### CARLA LFS object relocation

Copied all 43,972 objects, 43,321,303,526 logical bytes, from the CARLA content
repository's `.git/lfs/objects` to
`/Volumes/SDV-Work/AosEdge-SDV/build-data/carla-content-lfs/objects`.
The SSD was identified by volume UUID
`591578E3-8196-4B44-A575-CEC76B406789` with ownership enabled.
Every destination object's SHA-256 matched its LFS object ID; the complete set,
source identity, sizes and modification times were reconciled. No open
consumers were found. The repository's existing `lfs.storage` facility now
points to the external storage root; no new product configuration mechanism
or source change was introduced.

After switching the local Git setting, Git's reported media location and
working-tree status were checked. The pre-existing modified RoadMaster material
remained unchanged. Only the verified internal LFS object directory was removed.
Measured recovery: **43,424,423,936 bytes, approximately 40.44 GiB**.
The source checkout and ordinary Git history remain internal. LFS operations
that need stored objects now require this SSD; existing checked-out assets and
the installed demo do not. Restore by copying the verified object set back and
restoring the local Git setting, with writers stopped. This is relocation, not
an independent backup or deletion of the only resource copy.

### Completed video verification jobs

Removed exactly these directories under the private video repository's `work`:

- `organization-v27-rebuild`
- `organization-native-render`
- `organization-checkpoint-restore`
- `organization-picture-workspace`
- `organization-picture-workspace-v2`

All 3,609 listed files matched the retained cleanup inventory, inode, size,
modification time and recorded hashes; no open consumer was present. Canonical
media, recipes, v21 baseline, current v27 outputs, recovery archives and compact
verification evidence were preserved. Measured recovery: **2,235,564,032 bytes,
approximately 2.08 GiB**, rather than the clone-shared 33.26 GiB logical total.
Removed scratch is reproducible from the retained tools; it is not in Trash.

## Preservation and next step

No VM, Cloud Unit, certificate, credential, Factory image or installed version
was changed. Source and dirty worktrees remain; no commit, push or tag changed.
Builder relocation would need backing-path and launcher validation and was not
silently combined with this task. Existing standalone compiler/cook/DDC inputs
are already on SSD. Current Kit 025 and rollback Kit 024 remain available.

All full-media staging and output go to SDV Work, not the internal disk. Avoid
copying the full runtime back into internal temporary directories for packaging.
Compact execution evidence is retained at
`CarlaSim/Build-distribution-stage2-20260926/disk-cleanup-20261002/`, including
the exact LFS inventory and per-operation physical-space measurements.

## Superseded installation cleanup on 3 October

The operator additionally authorized removal of old installation copies before
the next installer release. On the test M1, 11 exact payload targets were
removed: two transferred kits, three old Setup DMGs, the Kit 025 full DMG and
five installed versions in the previous package stores. The old selections
were disabled through the normal installed-version API. Their small receipts,
manifests, histories and enrollment credentials remain. Kit 026, its current
Test and its full DMG were preserved. Both unused mounted installers were
ejected; Docker Engine was not stopped.

M1 free space increased from 229,996,273,664 to 350,516,371,456 bytes:
**112.24 GiB recovered**, with about 326.44 GiB free afterward.

On SDV Work, 42 exact targets were removed: kits 020–025, Setup previews 030–039
and their available DMGs, the Kit 025 full DMG, four superseded input-recovery
payloads and twelve historical installed versions. Manifests and recovery
receipts remain; old payload copies are not in Trash and would require
reconstruction. Current Kit 026/Setup 040, Factory .41, source, warm CARLA/LFS
and Yocto inputs, current video and Production dependencies remain protected.

Work free space increased from 397,601,124,352 to 420,378,750,976 bytes:
**21.21 GiB net recovery**, about 391.51 GiB free. A small concurrent new UI
build is included in that net result. The internal development disk gained no
material space in this batch; these old payloads were already on SSD.

Five old development registrations and six dependent installed versions are
deliberately retained. Four registrations have open directory references held
by the virtualization process despite no demo containers remaining. The fifth
has a legacy workspace-only journal. No product ownership guard was bypassed,
no journal was discarded and the shared Docker Engine, with five unrelated
running containers, was not restarted for cleanup. These are explicit cleanup
remainders, not a claim that every old instance has been removed.

Exact inventories, retained public manifests, per-target deletion receipts and
free-space measurements are in
`CarlaSim/Build-distribution-stage2-20260926/cleanup-20261003/dev/` and, on M1,
`SDV-Qualification/cleanup-20261003/`. APFS directory totals are not physical
recovery: cloned copies share blocks. No Cloud object was deleted by this
storage operation.

The subsequent release transition separately retired Kit 026's owned staging
Test through normal Finish: VM `4f77ccb2-eb23-461b-88c8-15a1c277ac74`, Cloud
Unit `d61e7036-aeb0-4495-b906-a4e6da558fcc`. Its working VM and run-specific
backend data were removed irreversibly; published releases, credentials,
evidence and the rollback media remain. Post-read confirmed the automotive
journal absent, no demo processes and no Docker containers on M1. Docker
Engine itself remained available. M1 then had approximately 335 GiB free
before transfer of Kit 027; this is a later capacity observation, not included
in the 112.24-GiB payload-cleanup measurement above.

The subsequently rejected Kit 027, Setup 041 and their full DMG were also
removed from SDV Work after Kit 028 assembly and signed Setup 042 verification.
Kit 027 failed its VM/host manifest binding before creating any Test; its
application/input manifests, build receipt and diagnostic evidence were retained.
These three targets represented 46.33 GiB of directory totals, not reclaimable
physical space. Net free-space change during this deletion was only about
28.8 MiB while the replacement DMG was being compressed; no larger independent
recovery is claimed. Receipts are in `cleanup-20261003/rejected027-dev/`.

After Kit 028 installation and selection passed on M1, the rejected Kit 027
registration was unselected through the ordinary guarded API. Its installed
payload and full DMG were removed, with metadata and evidence retained. This
second M1 batch recovered 49,707,827,200 bytes, approximately **46.29 GiB**,
leaving 310,498,385,920 bytes free before the new controller was created.
Receipts are in `SDV-Qualification/cleanup-20261003/rejected027/`. Combined with
the first payload-cleanup batch, measured recovery on M1 is about 158.53 GiB;
this is not the current free-space increase because new media and installation
consume space between measurements. Kit 026 rollback remains until replacement
qualification; credentials, reports and Docker Engine remain unchanged.

The final local sweep removed the two obsolete Setup 022 application payloads
from `CarlaSim/Build-distribution-stage2-20260926/setup022-dmg-stage/` and
`setup022-hardened-proof/`. Their build/proof receipts and operator documents
remain in place. Both had zero open handles and no current delivery dependency.
Net internal-disk recovery was 179,777,536 bytes, approximately 171.45 MiB.
Receipts are in `cleanup-20261003/setup022/`.

At closure, approximately 162.62 GiB was free on the development Mac's internal
disk, 371.48 GiB on SDV Work and 282.68 GiB on the M1. These are capacity
observations after new media, installation and partial Test creation, not sums
of the cleanup measurements. A total of 60 exact obsolete payload targets were
removed across both machines. The five guarded development registrations and
six dependent versions listed above remain, as does Kit 026 rollback. No claim
is made that every historical instance was removed. Removed payloads are not
in Trash; source, retained manifests and receipts permit reconstruction.

The new Kit 028 run stopped at first native VM access before starting the VM or
creating a Cloud Unit. Its exact partial identity was reconciled and normal
owner shutdown verified zero demo processes/listeners and no M1 demo containers.
The partial Test state was preserved, not included in superseded cleanup.
