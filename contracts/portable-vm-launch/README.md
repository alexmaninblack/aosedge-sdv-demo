<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Portable VM launch inputs

- Status: Accepted Stage 2 implementation slice; live qualification deferred.
- Version: 1.0
- Prepared: 2026-09-26
- Owner: Demo Solution Team
- Parent: [distribution plan, Stage 2](../../docs/planning/active/installable-distribution-and-reproducibility.md#stage-2-assemble-portable-demo-runtime-artifacts).

## Selection and dependency boundary

The fixed `vm-runtime` directory inside the existing artifact catalogue selects
packaged VM inputs. Absence retains the developer path. Invalid presence blocks
before image creation, helper execution or VM launch; no PATH/Homebrew or cached
firmware fallback is allowed. An integration-source lock pins its manifest.
The manifest contains the existing DNS helper, firmware, required virtual-NIC
ROM and their license notices,
and binds the independently locked [host runtime](../portable-host-launch/README.md).
QEMU and private Python are reused from that host closure, not copied again.

Validate canonical regular files, exact size/hash/mode, no links or extra files,
and the complete consumed native/Python dependency inventories. The unchanged
firmware SHA-256 is independently checked against the VM profile. No key,
certificate, journal, Factory image, provisioned overlay or user configuration
belongs in this small input bundle. Factory discovery and its existing copy,
integrity, backing and source-support checks remain authoritative.

Existing EnvironmentService image operations use the packaged `qemu-img`;
VMService uses packaged `qemu-system-aarch64`, the unchanged `virt-11.0` machine
profile and fixed firmware. All VM arguments, IDs, ports, disks, QMP/serial,
resource limits and safety/retirement gates remain unchanged. At explicit
execution verify the relevant closure and omit developer Python/DYLD overrides.
The existing DNS helper uses the fixed private Python entry with `-I -B`, so
its command no longer depends on which interpreter invoked Demo Control.
Resolver behavior, owner UUID, port 18053, log and lifecycle are unchanged.

Live closure proof additionally requires QEMU 11.0.3's `efi-virtio.rom`
(160,768 bytes, SHA-256
`26be36901db7f8181c306cc62bd74891d8646528965a78e40cceadba5dd7c8e7`).
Package it under `share/qemu` with the original QEMU license notices and pass
that directory explicitly using QEMU's `-L` input. Do not disable the NIC ROM,
change guest devices, search Homebrew at runtime or silently omit the file.
The negative diskless/paused NIC fixture reproduces `failed to find romfile`;
the same fixture with the exact ROM passes without touching a provisioned disk.

The packaged version-only preflight has a bounded 15-second first-launch
budget. Live relocation measured 3.38 seconds before a successful version
response, exceeding the developer path's 3-second limit; warmed calls took
0.017 seconds. A timeout returns `VM_VERSION_PROBE_TIMEOUT` before VM/DNS
launch or a durable start attempt, never an uncaught traceback or automatic
retry. The accepted version allowlist and all guest-readiness budgets remain
unchanged. This does not assert a specific macOS loader/security cause.

## Preserved-owner transition

Selection is not permission to take over or replace a running process. Exact
command matching still rejects foreign arguments, duplicate owners and an old
developer-owned helper/VM that does not match selected packaged inputs. Do not
accept an arbitrary Python prefix or terminate by port. The absent-selector
developer behavior, including the current interpreter's native macOS alias,
remains unchanged.

At the later authorized lifecycle handoff, reconcile and normally stop old
owners through their original owner before selecting the packaged inputs.
Preserve identities, overlays, source, backend/model data and release ledgers.
Do not stop the current Test merely to qualify this code slice. Proof that a
fresh packaged helper has the same command from both CLI and private UI is not
proof of migration of the current legacy owner.

## Gates and current scope

Require deterministic tests for absent/invalid selection, changed dependencies,
missing host bundle, extra files/links, no developer fallback, fixed commands,
cross-interpreter DNS identity and unchanged owner rejection. Build only the
small immutable input bundle from explicit pinned inputs; retain the 90 GiB
reserve. No QEMU, Game, service or Factory rebuild is needed.

The operator requested assembly before further live screen checks on
26 September. Guest boot, DNS handoff, repeated start/stop, ignition, UI and
full E2E are therefore deferred until the complete runtime is assembled.
Unit/static/integrity gates do not establish live or clean-Mac qualification.

Class B: affects VM/image/helper input selection, orchestration requirements,
scenario/flow annotations and tests. Revalidated unchanged: vehicle authority,
strict ownership, Factory identity, provisioning, FOTA/SOTA and offline behavior.
