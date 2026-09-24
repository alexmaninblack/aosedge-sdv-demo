<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .39 — retained controller ignition recovery

Status: source gates complete; build and clean qualification pending.

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
