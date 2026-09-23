<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .37 — mainline build and offline qualification

Date:23 September2026. Status: build and scoped offline smoke complete;
**not live-qualified**. The current .36 Test, Cloud identity, working service
data, CARLA and Presenter were not changed. Production was not accessed.

See the [authorized migration plan](../planning/active/aoscore-mainline-migration-2026-09-23.md)
for residual patch decisions, negative controls and the remaining live matrix.

## Reproducible source and artifact

| Item | Immutable value |
| --- | --- |
| Platform source | `77d99770a3d9476736da55c3e2196396899bc563` |
| Demo Control build/gates | `1c7a9d3672d4b66b80d7cc124491e76200709de6` |
| AosCore application | `9d613a46df3c7f550062e2f19ae3406c57715694` |
| AosCore library | `5560291ba6914e36a5b841ade4d8fc54134a9e91` / v9.1.2 |
| AosCore API | `af3552a0a5eb0237eff7f5f183780ca46c339cd3` |
| Factory selector | `6.1.1-maninblack.37/main-qemuarm64` |
| Raw disk bytes | `6997147648` |
| SHA-256 | `00d02074ea55e44817c840eac0cec27507441497378e38df9ad03daba6cae237` |

The catalog stores the image read-only with `manifest.json`,
`configuration-tests.log` and `mainline-tests.tar`. Hashes were checked at
creation and host transfer; unchanged large disks were not repeatedly hashed
for status. The manifest remains `BUILT_NOT_LIVE_QUALIFIED`. Source checkpoints
are local; no push or accepted workspace-pin promotion occurred.

## Gates actually executed

- Source reconstruction matches the isolated native candidate; Platform
  regressions198/198 and source/license gates passed.
- Demo Control regression1035 cases:1019 passed,16 skipped. Focused Factory
  tests33/33 and permission tests15/15 passed. Initial sandbox socket/process
  denials and the corrected historical capacity fixture are excluded attempts,
  not native product failures.
- CM/SM/IAM compiled together with the actual production toolchain. SM includes
  boot/rootfs/container/VDP. Each effective and compiled dependency binding was
  checked; permission-key256 and IAM cache3 remain. Core unit fixtures and
  actual application compilation/configuration are separate evidence classes.
- Production-toolchain native matrix:424 passed,2 VM-only skips,2 upstream
  disabled. CM launcher/UID47, idle11, storage15; SM replacement27; IAM
  permissions7, PKCS#11 three-token cache14, gRPC61; VDP81, container42,
  crun5, network97 and CM disconnect/lock17. KAC, provider and verifier-prepare
  executables also passed. No skipped/disabled case is counted as passed.
- The formal image operation reran these gates from committed tooling before
  package/image construction. Native package QA completed. The earlier package
  pass retained9 nonfatal `buildpaths` warnings for private upstream source
  paths in manager/debug/staticdev binaries; no QA check was disabled.
- One warm offline Factory build:7547 image tasks,15 executed, all succeeded;
  image QA passed. Existing six-partition Rouge assembly and caches retained.
  Builder stopped cleanly after freeze and transfer.

## Isolated clean boot and repeat

Booted .37 through the existing disposable-VM adapter with a new overlay and
synthetic workdirs disk. QEMU user networking had `restrict=on`; no Cloud
access, provisioning, service publication or source/Gateway handover occurred.
Local console enrollment used the authorized fixture password without saving
it, then pinned the SSH host key through that owned console. Only the disposable
overlay received the local access public key.

Both first start and a clean shutdown/start verified:

- installed OS version exactly `.37`;
- SELinux Enforcing;
- unprovisioned state, with no provisioning marker or IAM user PIN;
- `aos-iam-prov` active/running, result success, zero restarts;
- normal IAM/SM/CM conditionally inactive, result success, zero restarts;
- stable digests for all three new manager binaries across the repeat.

### Classified baseline observations, not a zero-warning claim

The only failed unit was `nfs-server`: its export precondition requires
`/var/aos/states` and `/var/aos/storages`, absent before provisioning. This is
the [documented baseline behavior](aosvm-apple-silicon-baseline.md), not a new
mainline boot failure.

The first probe counted9 AVC entries. A subsequent SSH read added an SSH
entry. Do not report zero AVCs: their sanitized categories were:

| Process/context | Denied operation |
| --- | --- |
| auditctl/auditd to initrc_t | unix_stream_socket read/write |
| sshd to aos_var_run_t | directory search |
| agetty | checkpoint_restore capability |

To classify them, booted the immutable .36 image in a **second isolated fresh
overlay**, not the existing Test. The same read sequence produced the same
NFS failure and byte-identical sanitized denial report. .37 repeat boot
retained those categories and produced no Aos-manager-specific denial. No
SELinux permission was added, no denial suppressed, no rootfs remounted.
These baseline observations remain visible; they are not a claim that all
general-purpose distro services are warning-free. Offline smoke does not
qualify DNS/time/TLS or actual Cloud reconnection.

Both disposable VMs stopped cleanly; both qcow2 checks reported no errors.
Small stopped overlays and compact logs are intentionally retained in the
dated transient proof area pending live acceptance. Original .36, .37,
Builder/caches, current Test and video artifacts were not deleted.

## Still required — live acceptance

The normal Presenter has one current Test. Retiring its existing diagnostic
state is not implied by a build authorization. A separate exact Finish gate
has been requested; no destructive action has started. Do not silently create
another live lifecycle or switch the active source underneath that Test.

After authorization, qualify a clean .37 Test in staging:

1. Selected OEM/SP credentials, synchronized time, provisioning and Online.
2. VDP V1→V2→V3 and Brake V1→V2→V3; Tire V1. Publish each next version only
   after confirming the preceding installed version and functional result.
3. VDP Safe Stop, QM update behavior, persistent data/outbox, stable UID and
   service resource metrics across updates; no legacy-UID automatic-repair claim.
4. Real telemetry/advisory and UI observations; external network OFF stops
   backend ingress while local analytics continue; ON restores Online and
   queued delivery without CM deadlock.
5. Owned-Test Finish and final source/artifact promotion only after that matrix.

Signing/publication and destructive actions retain their exact authorization
gates. The existing demo-v1.0 checkpoint and accepted workspace pin remain the
rollback baseline until this live matrix is complete.
