<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Portable VM inputs: assembly and source integration

- Date: 2026-09-26.
- Status: Initial small candidate/source checkpoint; later live handoff linked below.
- Parent: [Stage 2 work packet](../planning/active/portable-runtime-artifacts.md).
- Contract: [portable VM inputs](../../contracts/portable-vm-launch/README.md).
- Preserved baseline: [demo-v1.1 / Factory .39](demo-v1.1-return-point.md).

## Changed boundary

This section records the original source slice. The later
[complete application proof](portable-application-2026-09-26.md#corrective-live-findings-and-final-assembled-successor)
supersedes its deferred owner state: legacy VM/DNS were stopped normally, the
same Test booted on packaged inputs, missing NIC ROM data was added, and raw
reboot recovered its retained route automatically. It also records the final
host/VM pins, bounded first-use QEMU probe and preserved Production .31.
No clean-install or fresh all-version cycle is implied by that continuation.

The opt-in selector supplies packaged QEMU/image tools, fixed firmware and the
unchanged DNS bridge to existing EnvironmentService/VMService. It reuses the
previously assembled native/Python host closure. It does not create a second
launcher or change VM arguments, networking, identity, resource limits, disks,
QMP/serial, safety gates, DNS resolver logic or process ownership policy.

DNS uses a fixed private Python invocation with `-I -B`, independent of whether
the caller is a developer CLI or private UI. Foreign or legacy commands still
fail exact owner matching. This fixes input selection for a fresh packaged
lifecycle; it does not migrate the current development-owned DNS process.
An explicit preserved-owner handoff and its live proof remain required.

Invalid selected inputs fail before an image process, new journal or helper
spawn. Native/Python dependency inventories reject modified or undeclared files;
developer Python/DYLD overrides are omitted at packaged execution. Absence of
the opt-in directory preserves existing developer commands.

## Artifact

The new build-only `scripts/distribution/vm_inputs.py` assembles exactly three
files: unchanged firmware, unchanged DNS source and the integration license.
It validates the existing independent host/vehicle-input locks and the original
firmware pin. It rejects links, oversized/writable inputs, existing output and
insufficient free disk. It neither boots QEMU nor starts DNS/Docker.

- Local candidate: `/private/tmp/aosedge-stage2-native.cir6B1/VM Inputs Candidate 001`.
- Payload: **3 files, 2,111,657 bytes** (approximately 2.01 MiB).
- Manifest: **839 bytes**; SHA-256
  `b8222b9bb8de59af834252d3b53817f6045945544f895d5bfd4bf5788591c5dd`.
- Source lock: [VM input manifest pin](../../contracts/portable-vm-launch/vm-runtime.lock.json).
- Reused host manifest:
  `da72bce6d1785424b93564d280f9ae7786f8795437fd9019e89a1082b1db1634`.

The source reader verifies the actual candidate, all three file hashes/modes,
the independently bound host manifest and consumed native/Python inventories.
The DNS input is byte-identical to current source. No QEMU, Python, CARLA or
Factory payload was copied or rebuilt; no service/image compilation occurred.
Approximately **101.82 GiB** remained available at the recorded disk observation,
above the unchanged 90 GiB reserve. No cleanup was performed.

## Source checks

- 13 new selector tests pass: fixed commands, calling-interpreter independence,
  absent/invalid selection, no developer fallback, before-create failure,
  dependency tamper, missing host, changed pins, extra files/links, duplicate
  rows, firmware identity, environment isolation and strict owner rejection.
- The complete VM-focused suite passes **41 tests**.
- 8 new assembler tests pass; all **100 distribution-tool tests** pass.
- The first full orchestrator run executed 1,133 test cases and found one
  incomplete Factory .31 test double: its mocked catalogue lacked a filesystem
  path. The fixture now supplies its explicit empty catalogue path; no product
  check was weakened. The focused Factory .31 suite then passed all 11 cases.
- Corrected full regression: **1,133 cases, OK with 17 explicit skips**
  (1,116 executed), in 118.993 seconds. No further product change or artifact
  rebuild was required after correcting that fixture.
- Documentation gate: **282 Markdown documents, 658 stable identifiers and
  38 Mermaid diagrams**, PASS. Whitespace gate also passes.

The unit suite uses process/guest doubles and disposable local fixtures. Its
progress strings about VM/CM/SM operations are fixture output, not changes to
the current demo. Native live tests remain disabled.

## Deferred and preserved

The candidate is **not promoted into the active catalogue**. Existing Test,
Production .31, Docker, CARLA and native panels are not restarted, replaced or
otherwise operated by this continuation. No credentials, state, model data,
release ledger, signing, publication or Cloud identity is changed. Large warm
build inputs and the separate video repository remain untouched.

The operator requested assembly before more live-screen validation. See the
[retained backend/advisory observations](distribution-deferred-live-checks-2026-09-26.md).
Do not mark those issues fixed or turn scoped input integrity into guest-boot,
DNS recovery, live UI, offline/ignition, serial-version E2E or clean-Mac proof.

Remaining Stage 2 work: backend-image and Cloud-worker selectors, complete
application assembly with current source modules, then explicit lifecycle
handoff and integrated qualification. This is an uncommitted working-tree
increment after `0d132125f8c88776b173060dc0cbc414332bcc45`; no push, tag update,
installer or external distribution is claimed.
