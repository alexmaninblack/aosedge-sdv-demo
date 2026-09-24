<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .39 — retained controller ignition recovery

Status: immutable build and isolated first/repeat offline smoke passed.
Still **BUILT_NOT_LIVE_QUALIFIED**; retained installed-service ignition on .39
and fresh staging E2E remain open. No accepted baseline pin is promoted.

## Scope

Platform checkpoint `793b1fc035d2b7c123f9a4161788955f389bb81d` retains
.38's pinned mainline triplet, security policy and installed runtime behavior.
It adds only the proven generated-component startup reconciliation in CM and
early reconstruction of existing strict Test credential declarations in the
existing store bootstrap. See the [retained .38 proof](factory-38-staging-e2e-2026-09-24.md).

The accepted host behavior is automatic reconnection of the same Test after
controller boot, preserving Unit/Node/enrollment/assignment/scene/models and
holding physical Safe Stop. No reprovisioning or Autopilot activation. Host
partial outcomes remain UNCERTAIN and are not automatically retried.

## Ordered gates

1. Clean committed Platform and Demo Control source; host/UI/crypto/negative
   regression gates. Platform217cases:215passed/2skipped. Factory tooling41/41.
   Demo Control1072cases:1056passed/16skipped; Presenter324tests/32files,
   TypeScript and production bundle pass. Documentation gate260documents and
   confidential-input/whitespace gates pass. Unit-test stop/restart output is
   mocked, not a mutation of the running demo.
2. Existing warm Builder only, offline guards and minimum60GiB free on host
   and Builder. Effective and compiled mainline pins must match. Preflight
   measured147GiB host and104GiB Builder.
3. Affected target compile; production-toolchain native matrix requires
   CM launcher53 (not47), unchanged SM32 and all earlier security/runtime gates.
4. Package/QA before image. Assert the packaged early-projection helper and
   bootstrap bytes equal the committed source, with correct mode and ordering.
5. One immutable image, unchanged six-partition disk layout, creation/transfer
   hash verification; preserve .38 bytes and current diagnostic Test. No debug
   keys, certificates, core collector, temporary policy or /run proof enters it.
6. Isolated offline clean boot and repeat with no enrollment; then separately
   reconcile the live replacement/publication boundary for fresh staging E2E.
7. New-image retained ignition off/on must restore service/VDP readiness without
   startup failure/restarts, retain models/queues and stay stopped. ExternalOFF
   continuous inference and queued delivery recovery remain mandatory; offline
   cold boot is a distinct unqualified case until measured.

No accepted baseline promotion, live Test retirement, new Cloud object or
publication is part of this build. Historical VDP109 SIGSEGV is still unresolved
and has not recurred; neither this image nor its source claims to fix that crash.

## Build outcome

- Platform checkpoint remains793b1fc0. Exported build tooling checkpoint:
  `e3b20c7e4c04d08bb4bd044f9db8d4e3bf6874ab`.
- Compile1819tasks/19executed; package6505/46executed;
  image7547/15executed; all succeeded. Three nonfatal CM `buildpaths` warnings
  are the previously classified recipe-private path category; no QA bypass.
- Production-toolchain native matrix435passed,2VM-only skipped,
  2upstream-disabled; CM launcher53/idle11/storage15/lock17, SM32, IAM
  permissions7/PKCS#11 cache14/server61, VDP81, container42, crun5, network97.
  KAC/provider/verifier executables also exit0 and five initial Factory input
  regressions pass. Package helper/bootstrap bytes match source, including mode
  and early ordering. No image was built before these gates passed.
- Image transfer/hash verification completed; warm Builder stopped cleanly.
  No existing image was overwritten; caches and proof evidence are retained.

| Artifact | Value |
| --- | --- |
| Version | `6.1.1-maninblack.39/main-qemuarm64` |
| Bytes | `6997147648` |
| SHA-256 | `741a9717c4152dfe9baa997fcdd948fa5662e71473b0a7c91faba942aa63c557` |
| State | `BUILT_NOT_LIVE_QUALIFIED`, image read-only0444 |

## Isolated offline checks

Only disposable .39 overlay/auxiliary store and SSH port10031 were used. The
current Test .38 was not replaced. First host-observed boot began16:20UTC;
the normal console adapter enrolled key-only access with the operator-provided
demo password through a hidden prompt. No credential was recorded in evidence.

First boot and graceful stop/start (~16:25UTC) both report .39, SELinux Enforcing,
IAM-provision active and CM/SM/IAM/provider inactive as expected before
provisioning. Manager results are success, automatic restarts0, no SEGV/ABRT,
no provision marker, no private provision PIN, no runtime credential projection
and no diagnostic core collector. SSH enrollment survives the power cycle.
Boot IDs differ; binary/helper digests are stable and the packaged helper matches
source. These guests intentionally use the disposable adapter's offline RTC;
guest2025timestamps are not actual host execution dates or timing evidence.

The bootstrap is condition-skipped before the component store is initialized.
An initial harness assertion incorrectly required it active; the authoritative
unit read proved `ConditionResult=no`, success and no execution. This is not a
product startup failure. An explicit unit start also condition-skipped. Direct
execution of the packaged helper twice returned `VISS_BOOT_PROJECTION_NOT_ENROLLED`
and created neither declaration. This no-op proof does **not** claim that the
full enrolled bootstrap path ran on an empty Factory; that path's existing
live ordered-start proof is in the .38 report and needs the fresh .39 E2E.

The inherited empty-Factory NFS failure is unchanged: its service cannot stat
CM-owned storages/states before provision. Scoped AVCs are the same previously
recorded audit/getty/SSH categories, not new VDP/projection denials. No policy
was relaxed. Both observations remain explicit exclusions, not a blanket
zero-failed-unit/security claim. The isolated .39 VM was stopped cleanly after
the repeat; its small overlays and logs remain preserved for reconciliation.

## Host shutdown guard and preserved Test

Review found that CLI `ui.stop` did not see the new background restoration as
an active operation. A mocked negative control reproduces three unsafe shutdown
decisions (busy/attempted/failed recovery). The source correction refuses each
and still permits idle shutdown after completion. Presenter40/40 tests pass
with local socket permission; an earlier sandbox-only run's14bind errors are
excluded, not product failures. This host-only guard needs no image rebuild.

16:26UTC read of preserved .38: IAM1019/SM5292/CM5146/KAC1047/VDP5318 unchanged,
all successful with0automatic restarts since the15:54ordered-start proof. VDP
READY/LIVE; models/UIDs/quotas/inodes retained, Brake generation6/recent5 and
Tire recent2, both Inspection recommended; outboxes empty. No new crash/core.
The new Presenter worker is not yet activated on the old immutable .38 image.
Coordinated .39 live replacement must keep the same no-Autopilot rule. No Cloud
mutation, release publication, Test retirement or accepted baseline promotion
occurred in this build/smoke continuation.

Compact evidence is under the dated private proof root: `factory39-build.log`,
`factory39-smoke-*`, and `source-boot-ui-stop-*`. The image catalog also retains
the manifest and compact native-test archive. Host free space after the build
is137GiB; no disk cleanup is required or performed during this diagnostic stage.
