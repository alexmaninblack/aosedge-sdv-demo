<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .38 successor candidate — 24 September 2026

Status: immutable build and clean offline boot/repeat passed.
Image remains **BUILT_NOT_LIVE_QUALIFIED**, not an accepted replacement baseline.

## Scope and source checkpoint

The operator authorized closing the diagnostic/security stage and moving to a
new Factory and fresh E2E. [Diagnostic closure](factory-37-staging-e2e-2026-09-23.md)
records the proof and exclusions. Platform checkpoint:
`378c00efad0ec67b2fb0c90328b68c4e8970b511`.

The candidate keeps the coordinated mainline triplet and adds only the proved
SM asynchronous-status correction, exact three-rule KAC/crun integration and
seven optional VDP-probe deny/dontaudit decisions. No diagnostic collector,
temporary credentials, core, policy lease or live state enters the image.
Demo Control also prepares all VDP profiles with the reviewed common runtime,
preserving7/15/23 signals, V3-only advisory and existing immutable release bytes.

Historical VDP109 SIGSEGV remains unexplained and unclaimed as fixed. The reviewed
current runtime passed deployed-identity transport fault/security tests and live
observation without recurrence. Stop a new run on recurrence and collect bounded
evidence under a separately scoped capture; do not hide or retry a crash away.

## Mandatory ordered gates

1. Clean committed source; Platform202cases/200pass/2skip, policy25/25,
   exact recipe reconstruction, license/secret/whitespace checks.
2. Host and warm Builder each at least60GiB free; offline network/fetch guards,
   effective pins and actual compiled source bindings. Do not clear caches.
3. Compile CM/SM/IAM, KAC and refpolicy. Execute production-toolchain regressions,
   including **32 SM launcher cases** (five additional asynchronous/identity
   negative controls); retain .37's27-case historical matrix unchanged.
4. Package QA, source/configuration checks, then one image/assembly; hash at
   creation and transfer, freeze read-only with BUILT_NOT_LIVE_QUALIFIED manifest.
5. Isolated new overlay clean boot/repeat; expected empty Factory identity and
   metadata, labels, security/manager health, no diagnostic residue.
6. Fresh staging E2E only with exact publication/provision/retirement authority:
   VDP V1→V2→V3 and Brake V1→V2→V3, Tire V1, each next release uploaded only after
   its predecessor is installed and checked. Safe Stop gates VDP, not QM updates.
7. Stable service UID/storage/quotas and Cloud metrics, real local advisories,
   independent Reset/history retention, Return to road and UI timing/status
   observation. External network OFF must stop backend ingress while local
   processing/token renewal continues; ON must recover Online and drain queues
   without duplicates or a manager restart. Cold persistence is a separate check.

Preserve the existing .37 Test, Cloud Unit, storage, .36/.37 images and evidence
until successor acceptance. No new signing, publication, provisioning, retirement
or Production action is implied by the build command. Do not change the accepted
solution baseline pin or call the candidate qualified on compilation alone.

## Execution log

- 12:16:25UTC: temporary core collection explicitly disabled/removed; no captured
  real core. Stock policy restored, Enforcing, all live managers/VDP unchanged.
- Source/recipe reconstruction passes for CM4patches/SM4patches/IAM2patches.
  Platform license/secret gate passes244files. No collector/debug pattern found
  in the platform recipes or Factory specifications.
- Demo Control regression1043cases:1027passed/16skipped; focused Factory
  matrix38/38 after the exact .38 pin assertion. Documentation/whitespace pass.
  Printed restart/stop messages in unit tests are mocks, not live mutations.
- Pre-build space: host162GiB, warm Builder106GiB.
- Build tooling checkpoint `5dda934a7da5a3c01eedef03bc80b4a55b797f56`; Platform
  checkpoint unchanged from above. Both were clean when exported. No push or
  accepted workspace-pin promotion was performed.
- Compilation1811tasks/18executed; package6486/49executed; image7547/15executed;
  all succeeded. Refpolicy compiled before the image. Three nonfatal SM
  `buildpaths` warnings refer to private upstream source/build paths, the
  previously classified category; no QA test was disabled.
- Production-toolchain native matrix: **429 passed**,2VM-only skipped,
  2upstream-disabled. SM32, CM launcher47/idle11/storage15/lock17, IAM
  permissions7/PKCS#11 three-token cache14/server61, VDP81, container42,
  crun5, network97. KAC/provider/verifier executables also exit0; five initial
  Factory-placeholder/input regressions pass. Skip/disabled counts are not passes.
- Immutable image transferred and digest verified by12:34UTC; Builder stopped
  cleanly. Catalog retains the read-only disk, manifest, configuration log and
  compact native evidence archive. No existing image was overwritten.

| Artifact | Value |
| --- | --- |
| Version | `6.1.1-maninblack.38/main-qemuarm64` |
| Bytes | `6997147648` |
| SHA-256 | `9ae2d96830f6ee0aade2dfc9bc540211aaa2754148962c3bfa8eebdd2bb11961` |
| Manifest state | `BUILT_NOT_LIVE_QUALIFIED` |

## Clean offline first boot

New disposable overlay/workdirs disk, dedicated localhost10030 and QEMU
`restrict=on`; no provisioning, Cloud call or source/Gateway handover. Console
enrollment used the previously authorized fixture password without saving it,
then pinned the SSH key through the owned console.

First login12:36:12UTC: OS reports .38, SELinux Enforcing, provisioning state and
IAM user PIN absent. `aos-iam-prov` is active/running; normal IAM/SM/CM are
conditionally inactive, all results success and restart counts zero. No temporary
collector exists; `core_pattern=|/bin/false`, `core_pipe_limit=0`.

The only failed unit is the known unprovisioned NFS export precondition:
`/var/aos/states` and `/var/aos/storages` do not exist yet. Sanitized NFS/AVC
diagnosis is **byte-identical** to the retained .37 first-boot report. The initial
read sees9AVCs; another SSH read adds a known search denial. Categories remain
auditctl/auditd→initrc socket read/write, sshd directory search and agetty
checkpoint_restore. This is not a zero-warning claim or a new permission grant.

Complete compiled-policy comparison with the captured stock .37 policy passes:
only ten expected TE statements added (three KAC allows, seven exact VDP
deny/dontaudit statements), none removed; every other policy category, type,
attribute membership, boolean, permissive flag and constraint is unchanged.
No policy was loaded or modified during this read-only comparison.

First-boot manager binary digests:

- IAM `d60f45b1e8e60cbab61a5e0f4afcd076b0220399f8ee507041ac400b362b89b2`
- SM `358b3fe9de049a7a4aec29ee8bc686c70773c96c21ffe577b57a34891de09af6`
- CM `88cac5efe8001f64f2c7fa0ed565bfc8141ee41faaf5248776f5e61b2db254cd`

Compact logs remain in the dated private proof root: `factory38-build.log`,
`factory38-smoke-read.log`, `factory38-smoke-diagnosis.log`,
`factory38-policy-comparison.log` and the isolated `factory38-smoke` directory.
The preserved live Test remains stock .37 with its known KAC renewal restriction;
building .38 does not permanently repair that running VM.

## Repeat and disposition

The disposable VM shut down cleanly, restarted, and reached a fresh login at
12:39:19UTC. Repeated health output is byte-identical to the first read: manager
states/results, zero restart counts, binary digests, Enforcing and absence of
core-capture configuration. Full compiled-policy comparison passes again after
reboot with exactly the same ten additions and no other semantic changes.
The offline VM was then stopped cleanly; no forced termination was used.
Both stopped qcow2 images pass `qemu-img check` without errors.

The original Test, Cloud identity, histories, .36/.37 images, warm Builder/cache
and proof records are preserved. Only the three temporary core-receiver files
and21generated synthetic credential files were removed after stopped-owner /
zero-open-handle checks; no user credential or real dump was removed. The
disposable overlays are retained stopped pending live acceptance.

Fresh staging E2E has **not started**. The normal Presenter owns one current
Test, so exact permission to retire diagnostic Test .37 (Unit
`2737ef63-4781-4ee6-a770-52e0a01e95e0`) and create fresh .38 was requested.
Fresh signed releases/publication retain their own exact set and sequential
authorization gate. No image selection, retirement, new Unit, signing or upload
occurred in this build/smoke operation. Production and the video remain untouched.

Final preserved-Test read at12:43:19UTC: VDP114 PID159575 still READY/LIVE,
NRestarts0,149m52s continuous since10:13:26, one ready transition and no matched
stale/reconnect/non-monotonic/SEGV event. Core capture is off, no dump exists,
SELinux Enforcing. This observation does not explain the historical109 crash.
