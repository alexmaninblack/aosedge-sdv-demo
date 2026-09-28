<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installed Runtime State Separation — Stage 3

- Date: 27 September 2026.
- Status: Source and isolated installed-package proof PASS; native activation,
  first-use onboarding and live E2E remain unqualified.
- Parent: [Distribution plan](../planning/active/installable-distribution-and-reproducibility.md).
- Decision: [ADR 0018](../architecture/decisions/0018-installable-demo-and-first-use.md).
- Contract: [Installed state](../../contracts/distribution-installation/installed-state.md).

## Delivered boundary

The existing Demo Control now has an explicit engineering installed-instance
scope. Code/contracts and the five locked input groups are read from the
installed version. Journals, working data, release continuity, generated VDP
and service packages, backend outputs and credential references belong to a
separate private instance. Developer mode keeps its previous layout.

Creation accepts only a fresh directory or a recognized private marker. Unsafe
paths, unknown state schemas, foreign state roots, missing input groups,
developer artifact overrides, changed package receipts and wrong mounted
volume identities fail closed. Native VM-password Keychain items use an
instance-specific namespace. No existing credentials or operator state are
copied. Developer build/patch operations are not available in installed mode.

The public Cloud Unit model template was missing from the earlier portable
export. It is now exported, allowed by the bounded installer inventory and
read from program files rather than from mutable operator state. No Cloud
model, account or Unit was changed to test this path.

## Canonical change and traceability

Class C, limited to the installed workstation boundary: HLA 1.8 → Scenario 2.1
→ Flows 2.2 → System/Register 2.2 → Demo Orchestration 1.3. Allocation:
[installed entry flow](../architecture/demo-scenario-architecture-flows.md#af-dist-entry),
[separate data authority](../requirements/system-requirements-and-traceability.md#sys-dist-001),
[installed instance requirement](../requirements/components/demo-orchestration.md#req-demo-025)
and [isolated test obligation](../requirements/components/demo-orchestration.md#ut-demo-025).

Other vehicle/service packages were reviewed for this host-only change: their
input references advance to the canonical versions, but no guest wire contract,
model threshold, security authority or semantic package revision changes.
Historical acceptance paragraphs retain their original version references.
One OEM/one SP for two distinct services is the accepted first-install scope;
the older two-provider model is an expanded scenario. Enrollment and its
publication-profile wiring still require their own contract/implementation gate.

## Source tests and fault classification

- Existing Demo Control suite: **1,163 tests, PASS, two explicit skips**.
- New installed-state suite: **20 tests PASS**.
- Final focused routing/compatibility regression: **102 tests PASS**, including
  the new cases and the existing five input selectors.
- Distribution suite: **152 tests PASS**.
- Documentation and whitespace checks: PASS.

Tests cover fresh/repeat creation; malformed/private/link/socket constraints;
program/input/output routing; missing/corrupt groups; namespaced Keychain with
no credential read; private TLS/Cloud defaults; program-owned Unit template;
child CLI propagation; receipt/volume rejection; blocked developer operations;
redacted errors; and a real release-continuity read across two program-version
selections while history/configuration sentinels remain unchanged.

The first broad run had 37 errors. Five were routing/test-protocol regressions:
generic Mock attributes and a minimal environment lacking a root on the legacy
absent-input path. Both causes were corrected and their affected tests passed.
The remaining errors were denied temporary loopback/Unix sockets or read-only
process enumeration in the execution sandbox. The authorized local suite then
passed with those test facilities enabled; no product security was weakened.
A new template-read fixture also needed the existing prior Cloud-selection
precondition; it was corrected without making a Cloud call.

## Complete Kit 005 installation

Source candidate:
`/Volumes/SDV-Work/AosEdge-SDV/packages/runtime-kit-005-20260927`.
Application-manifest SHA-256:
`2df0fc0e4bd6e25342c626a4e9cb17f935040d7712bbeb87ba628c7928de30ef`.

It exports **85 application files / 70 Python modules**, reusing all five locked
Kit 004 input groups. Factory, service binaries, native applications and CARLA
were not rebuilt. The independent manifest pin was supplied to the installer.
The new version was fully transferred/verified into the existing isolated
`/Volumes/SDV-Work/AosEdge-SDV/install-tests/stage3-store-001` store; Kit 004 remains.
The receipt records **17,681 files, 35,114,340,426 logical bytes** and
`INSTALLED_NOT_ACTIVATED`, with runtime/state-copy/Cloud/activation flags false.

Work volume binding: `591578E3-8196-4B44-A575-CEC76B406789`. During assembly plus
installation its container free bytes changed from 614,526,275,584 to
614,354,853,888: about **163.5 MiB**, not another physical 32.7 GiB allocation.
This is an observed interval delta, not an exclusive storage benchmark. APFS
clones share the unchanged input blocks. About 572 GiB remains free on Work;
the separate Clean volume remains unused.

## Isolated execution proof

The installed private Python ran with `-I -B` under a deny profile: no network,
no developer/Homebrew/Xcode/credential/Keychain reads, and no writes anywhere
in the installed package store. Deliberate denial controls passed. A short
disposable internal instance was created; no live run was selected.

Result: `PASS_ISOLATED_INSTALLED_STATE`:

- All 70 application modules load from installed bytes.
- All five input selectors resolve; consumed host/Cloud/backend/runtime inputs
  pass their existing integrity checks.
- Factory .39 metadata and all four Brake/Tire profile configurations resolve.
- A separate packaged CLI process receives the instance selection and lists
  Factory .39 twice without writing into the application directory.
- The real release-continuity reader retains VDP `123.0.0` and proposes
  `124.0.0` on both entries; the ledger and history sentinel bytes are unchanged.
- Missing TLS and missing Cloud credentials report their existing explicit
  prerequisite errors. Nothing is adopted from the developer environment.

Reusable proof: [installed-state probe](../../scripts/distribution/installed_state_probe.py).
Local invocation material: `/private/tmp/ipproof.sR5IPk/probe.py` and
`/private/tmp/ipproof.sR5IPk/installed.sb`. These are compact proof assets, not
operator configuration. The temporary private instance was removed by the test.

Source marker for [runtime routing](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/runtime_paths.py):
`1a8366142987fff5ae4a25ba45278569b656e394e54a813be97f230875d03316`.
The complete-kit reader now also allows the public Unit template; its SHA is
`3c06809a0dc25bda5a01f07ad319ad0b46f7200cbf66010034db604158b2c62a`.
The earlier [installation report](offline-installation-2026-09-27.md) retains
its historical source hashes rather than silently relabeling the previous run.

## Preservation and remaining gates

Test .39, Production .31, their identities/data, existing source edits, video
repository and warm caches were not changed. The same QEMU, CARLA, Driving
Control and Presenter process IDs were present before and after this slice.
No live restart, publication, signing, provisioning, Finish, commit, push or
tag change is claimed.

This is **not** the complete Stage 3 exit gate. Remaining work:

1. Native active-process ownership and explicit version selection; compatible
   update/repair/rollback and data-preserving removal. No automatic pointer or
   running-setup replacement exists in this slice.
2. Native first-use wizard, internal-storage/default-path preflight, trust and
   Cloud access/enrollment. The current state guard requires the home filesystem;
   an externally located home is not qualified. One OEM/one SP remains the goal.
3. Long-lived mounted-volume removal/reconnection, full installed live E2E,
   fresh Docker prerequisite/import, signing/notarization and redistribution.
4. DMG delivery and actual clean-Mac qualification. An isolated test on this Mac
   does not substitute for another Mac's OS/account/permission behavior.
