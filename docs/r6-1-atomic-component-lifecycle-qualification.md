<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R6.1-3 Atomic Component Lifecycle Qualification

- Status: Pass
- Date: 2026-08-14
- Scope: local and offline only
- Platform revision: `fa5e7cfa8c238419eb12a76ae6f0676f9243acd6`
- Project manifest SHA-256:
  `d1483a6bf6ae00a1b5fd279f8c745ea21fca8fe6681baa605cf9eb0a59df8539`
- Generated project Ninja SHA-256:
  `cbb63df9a498167a5233915589ecc630cf9aff265d5c30121d824a4a6167562b`

## Qualification Boundary

R6.1-3 qualifies the bootstrap-owned atomic lifecycle for one independently
delivered vehicle-data-provider component. All lifecycle payloads used by its
tests are synthetic and unsigned. No provider component was signed, uploaded,
published, assigned, or installed through AosCloud.

The provisioned demonstration VM, its persistent overlay, Unit identity,
Cloud catalog, Unit Model, Node Type, assignments, and provisioning state were
not accessed or changed. The accepted R6 side-loaded provider remains the
operational baseline.

The persistent Yocto builder VM, downloads, shared-state cache, build tree,
and source checkouts were retained. No builder disk or cache was recreated.

## Implemented Lifecycle

The pinned Aos Service Manager now contains the production
`systemd-slot-component` runtime and provider-specific restricted archive
preflight. The runtime implements:

- fixed A/B slots under persistent `/var` storage;
- pre-extraction USTAR validation and post-extraction payload validation;
- offline candidate self-test through a sandboxed fixed systemd template;
- durable prepare, unavailable, stop, switch, start, health, and commit phases;
- atomic active-link and state-file replacement with filesystem flushes;
- idempotent desired-state handling and semantic version policy;
- automatic rollback to the recorded previous release;
- restart recovery from every durable transaction boundary;
- fail-safe first-install and failed-rollback behavior;
- bounded two-slot retention, staging cleanup, and sanitized failure evidence;
- component status reporting without requesting a Node reboot.

The payload cannot select the launcher, systemd unit, health program,
credentials, KUKSA endpoint, SELinux domain, or host paths. The health
controller does not execute provider payloads as root. Candidate self-tests use
`DynamicUser`, `PrivateNetwork`, an empty capability set, and the stable
launcher boundary.

## Test Results

| Gate | Result |
| --- | --- |
| Platform contract and Yocto-layer validators | Pass |
| Platform repository Python tests | 17 passed |
| Platform repository quality gate | 79 tracked files passed |
| Exact pinned AosCore ARM64 production compile | Pass |
| ARM64 restricted-archive and Image Manager tests | 9 passed |
| ARM64 atomic lifecycle tests | 24 passed |
| ARM64 transaction-phase recovery tests | 5 passed |
| Integration repository tests | 56 passed |
| Source-lock and pinned-manifest validators | Pass |
| Shell syntax and ShellCheck for changed guest helpers | Pass |
| Incremental Yocto `aos-image-vm` build | Pass |
| Disposable ARM64 image boot and guest security gate | Pass |
| Unsigned bootstrap boot/full-rootfs FOTA structure | Pass |

The 38 ARM64 lifecycle tests cover first installation, idempotency, A-to-B
update, candidate offline/start/health failure, successful rollback,
first-install failure, failure of the previous release, explicit stop, stale
commit cleanup, and recovery from `prepared`, `unavailable`,
`previous-stopped`, `switched`, and `candidate-started` transactions. Negative
tests reject malformed manifests and archives, invalid checksums and end
markers, unsafe paths and links, duplicate entries, special files, unsafe
modes, whiteouts, reserved metadata, incompatible architecture or runtime
interface, invalid version transitions, excessive payload size, and
insufficient reserved storage.

## Built Artifacts

The signature-aware incremental build used the exact platform revision above
and reused 99% of the available shared state during the changed-image pass.

Complete disposable Main Node image:

```text
path: artifacts/r6-1/project/main-qemuarm64-r6-1-3.img
size: 6997147648 bytes
sha256: 17ea5b98943782027cea802717a61e24a6d8d36f9e71e71d2616963f9062347d
```

The image is retained as a read-only local artifact outside Git. It booted
through QEMU/HVF to the `main login:` prompt. Inside the disposable,
non-provisioned guest, the gate confirmed AArch64, read-only rootfs, writable
persistent `/home` and `/var`, cgroups v2, OCI namespaces, SELinux Enforcing,
the exact runtime configuration, an empty and permission-restricted component
store, loaded but inactive provider units, correct SELinux file types, no
credential-like files, and no boot AVC or fatal process failure. The VM then
stopped cleanly through ACPI/QMP.

The regenerated unsigned bootstrap FOTA output passed the existing structural
and secret-exclusion validator:

```text
config.yaml sha256:
  76b83af66775b99527e5a2a41ef25490a28897bc740e8f70a5ad3270cbed555b
boot component:
  size: 65187538 bytes
  sha256: 04296db2b8925b9596b485e57e0389b5cba161b97a5af508018b785c9a8afb39
full rootfs component:
  size: 128372736 bytes
  sha256: 5fb39d8e950c64c38f9d6fa4c374b2e9a2e103f1ed6aff134f5e329e1c243efb
```

These are unsigned bootstrap artifacts, not the independently delivered
provider component assigned to R6.1-4.

## Tooling Corrections Closed During Qualification

Moulin's generated Ninja output did not depend on the external platform Git
checkout revision. The first incremental invocation therefore reused an old
image even though the manifest selected the new commit. The guarded build
helper now asks BitBake to recalculate source task signatures before invoking
the Rouge image target. It also rejects a platform checkout whose origin,
`HEAD`, or worktree does not exactly match the pin before either image or FOTA
work. The subsequent image timestamp, digest, rootfs content, boot, and FOTA
checks all refer to the corrected build.

An earlier ARM64 chroot unit-test run had left 13 read-only synthetic test
directories under the Yocto image-staging `/tmp`. Only those exact
`r61-payload-*` test directories were removed before resuming `do_rootfs`.
Sources, downloads, shared state, build output, and the builder VM were
preserved; the resumed incremental build passed.

The minimal AosCore guest intentionally omits the `systemd-analyze` CLI. The
guest gate therefore verifies that its running systemd PID 1 loaded both fixed
provider units, in addition to checking their exact security directives. No
extra diagnostic package was added to the production rootfs.

## Decision

R6.1-3 passes its exit criteria. Atomic activation, rollback, restart recovery,
bounded storage, status behavior, restricted payload handling, and fail-safe
single-writer sequencing are locally proven without a VM checkpoint or manual
state repair.

R6.1-4 is the next review gate. It defines and produces the reproducible
provider component artifact, SBOM, provenance, notices, and OEM signature.
Signing, publication, Cloud assignment, and any change to the provisioned Unit
remain unauthorized until their respective explicit gates.
