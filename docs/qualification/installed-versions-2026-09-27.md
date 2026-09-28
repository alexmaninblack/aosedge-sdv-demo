<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installed Version Selection and Recovery — Stage 3

- Date: 27 September 2026.
- Status: Source and final Kit 007 isolated installed proof PASS; native delivery
  and clean-Mac qualification remain open.
- Parent: [Distribution plan](../planning/active/installable-distribution-and-reproducibility.md).
- Decision: [ADR 0018](../architecture/decisions/0018-installable-demo-and-first-use.md).
- Contract: [Version selection and recovery](../../contracts/distribution-installation/version-selection.md).
- Previous slice: [Kit 005 state separation](installed-state-2026-09-27.md).

## Delivered scope

One private instance can explicitly select a fully verified compatible installed
manifest. Its revisioned selection record is atomic; stale requests cannot
overwrite newer choices. A compatible predecessor can be selected again without
restoring old run data, decrementing release numbers or changing Cloud. Unselect
retains all data and package bytes and reports zero bytes freed: it is not uninstall.

Managed runtime entry leases both instance and package and re-reads the selection.
Selection/repair refuses active leases and detached owned processes holding store
or instance files. Failed process inspection is unknown, not idle. The first
selection slice also refuses retained current-run journals/VM overlays; no Finish,
journal deletion or implicit teardown is used to unblock an update.

Repair independently verifies a complete source kit, stages a replacement and
retains original program bytes under quarantine. Runtime entry is blocked during
incomplete promotion. Explicit replay reconciles interruption before/after the
two renames. A second damaged generation is blocked rather than overwriting the
retained original. Healthy program bytes are verified/reused and their receipt
can be reconciled; no instance state is repaired or reset.

This is a staged implementation refinement of the already accepted installed
workstation cascade, not a new vehicle boundary or runtime owner: HLA 1.8 →
Scenario 2.1 → Flows 2.2 → System/Register 2.2 → Demo Orchestration 1.3.
Traceability remains `SYS-DIST-001` → `REQ-DEMO-025` / `UT-DEMO-025`.
Native delivery, retained-run update compatibility, destructive removal and
clean-Mac behavior are not inferred from these engineering checks.

## Source and isolated fault proof

- Existing orchestrator regression: **1,183 tests PASS**, two explicit skips.
- Distribution regression: **183 tests PASS, no skips** in the final run with
  explicit local process-inspection proof enabled. The ordinary sandbox run
  skips that one opt-in native test; it also passed separately.
- New version-management cases: 31, covering selection/repeat/reconstruction,
  rollback/unselect, revision conflicts/exhaustion, compatibility, unsafe state,
  volume binding, active locks, retained runs, atomic failure, interrupted copy
  and promotion, source rejection, recovery and unchanged data.
- Documentation/link/identifier and whitespace gates: PASS before full-kit proof.

The native inspection proof starts one disposable child holding a temporary
file. The guard detects it; after that test child closes, the guard accepts the
same directory. A separate real child holds the shared lock and blocks an
exclusive writer. No existing CARLA/QEMU/Presenter process is stopped.

The first broad distribution run exposed a test-harness import-path error in
the new test module. The harness was corrected, then the entire suite passed;
no packaged runtime behavior was relaxed. Fault injection uses tiny disposable
fixtures only, never damage to a retained full kit or working demo.

A later review reproduced one product defect: an interruption after creating
repair work but before committing its first record was incorrectly treated by
runtime entry as no repair in progress. A new failing test proved it. The guard
now blocks that state; explicit repair safely recreates only a recognized
initial record after independent source verification. Empty work, interrupted
record rename and unknown-content preservation tests all pass. Kit 006 remains
historical proof; Kit 007 includes this correction and is the final candidate.

## Intermediate Kit 006 evidence

Source candidate: `/Volumes/SDV-Work/AosEdge-SDV/packages/runtime-kit-006-20260927`.
Application-manifest SHA-256:
`5b1a097c102f0381adcb5b2ac349b4a97c0ebb43dbbc780c38dd1cc170a95585`.

The candidate exports **86 application files / 71 Python modules**. All five
locked input groups are reused from Kit 005; no CARLA, Factory, guest service,
Python or native application rebuild occurred. The managed compatibility
declaration is `aosedge-demo-installed-state/1`; earlier undeclared Kit 005
remains retained but is not a managed rollback candidate.

Target: `/Volumes/SDV-Work/AosEdge-SDV/install-tests/stage3-store-001`.
Work volume UUID: `591578E3-8196-4B44-A575-CEC76B406789`.
The independent manifest digest above is supplied explicitly to installation
and selection; this is not external signature/notarization qualification.

Complete installation passed with **17,682 files / 35,114,347,510 logical bytes**.
Its receipt is `INSTALLED_NOT_ACTIVATED`; runtime change, operator-state copy,
Cloud access and active selection are all false. Earlier Kit 004/005 remain.
The source file count changed by one shared control module; large inputs did not.

Its complete-kit selection/repeat proof passed (96.69 / 96.78 seconds for full
verification). Undeclared old compatibility, active leases and retained-run data
were rejected without changing selection. Installed read-only execution passed
with 71 modules, all five selectors, private CLI repeat and unchanged synthetic
history/release ledger; network, developer/credential reads and package writes
were denied. Unselect/repeat retained all bytes/data and blocked subsequent CLI
entry. This does not qualify the subsequently identified repair-record gap.

## Final Kit 007 evidence

Candidate: `/Volumes/SDV-Work/AosEdge-SDV/packages/runtime-kit-007-20260927`.
Application-manifest SHA-256:
`f62e35f7b068c9d06b30d6536c4400790f0e53dbff50e6ed61682a98f5fcd0b3`.
Assembly passed with 86 application files / 71 modules, the early repair-record
correction above and all unchanged input groups. The full 1,183-test application
regression passed again after that correction (two explicit skips). Full
installation passed: **17,682 files / 35,114,347,644 logical bytes**, status
`INSTALLED_NOT_ACTIVATED` and all runtime/state-copy/Cloud/activation flags false.

Final complete-kit results:

- `PASS_COMPLETE_KIT_SELECTION`: first/repeat selection both pass; full
  verification takes **97.04 / 96.91 seconds**. Repeat leaves the selection
  record byte-identical at revision 1. This is the explicit trust-boundary
  operation, not the cost of ordinary status reads.
- Undeclared Kit 005 compatibility is rejected. Active leases and a retained
  current-run fixture block switching without changing selection or deleting
  the retained data.
- `PASS_ISOLATED_INSTALLED_STATE`: all **71 modules**, five input selectors,
  Factory .39, all four service profile configurations and two packaged CLI
  entries pass from installed bytes. Network, developer/Homebrew/Xcode and
  credential/Keychain reads, and writes into the package store are denied;
  deliberate denial controls also pass.
- Real release-continuity reads retain synthetic VDP `123.0.0` and propose
  `124.0.0`; the original ledger and history sentinel bytes stay unchanged.
  Missing transport trust/credentials remain explicit missing prerequisites.
- `PASS_COMPLETE_KIT_UNSELECT`: unselect/repeat ends at revision 2, retains the
  package and all instance data, reports zero bytes freed, and the actual
  installed CLI then refuses entry with `INSTALLED_VERSION_NOT_SELECTED`.

Proof material: `/private/tmp/vproof7.npbV5Z/{prepare.py,probe.py,finish.py,installed.sb}`.
The disposable instance is left unselected with its synthetic preservation
sentinels; it contains no live journal, VM, Cloud identity or credentials.
The reusable [installed-state probe](../../scripts/distribution/installed_state_probe.py)
supports an explicitly preselected disposable instance for managed packages.
Real rollback/repair fault injection is on tiny fixtures, not on these large
retained kits; full-kit native activation and clean-Mac acceptance remain open.

## Preservation and storage

Across Kit 006/007 assembly and installation, Work container free bytes changed
from **614,361,096,192** to **614,131,372,032**: approximately **219.1 MiB**,
with about **572 GiB** still free. This interval delta includes shared APFS
metadata and is not an exclusive storage benchmark; it is not another physical
35 GB copy per kit. Large input blocks are shared. The Clean volume is unused.

The same live process IDs were observed before and after: QEMU 18914, CARLA
19988, Driving Control 20208 and Presenter 51041. Test .39, Production .31,
their Cloud/runtime state, working images, credentials, video repository and
warm caches were not changed. No live restart or migration was performed.

Final documentation/identifier/link and whitespace checks pass. Previous
source edits are retained; this slice makes no commit/push/tag claim.

## Source markers

| Source | SHA-256 |
| --- | --- |
| `installed_control.py` | `81ec2d6fa8b18d5af97a0ad22293868e694479e2ff9172947eefb672972c079a` |
| `runtime_paths.py` | `94851ff75f5af6f7c50d808afa827054a42b2a91c9b4ccc4e56a0b26273c4228` |
| `version_management.py` | `7c91c2f815e153bbfd302bda9ab9e7e54d706e7f8f876ee7fd4a6bf56f79e152` |
| `installation.py` | `7d8b594ac2b83793b14db5e9e87cc8010efd79122868840c4d27a90d3fa3f1d9` |
| `installed_state_probe.py` | `9f6f3f2e22fa3c4d48fb5e40ae5641b4781df406e4464c0865d93904eeece413` |

## Remaining gates

1. Native launcher/wizard consumption of explicit selection and lock/ownership
   errors; a usable DMG/application entry, not just engineering tools.
2. Updates around a retained provisioned run with exact native-owner proof;
   no demand to erase a run simply to update the host program.
3. All-instance package/Factory reference accounting before pruning or actual
   data-preserving uninstall. Quarantine and predecessor bytes are retained now.
4. First-use internal-storage preflight, official registration/secure enrollment,
   one OEM/one SP configuration and separate Docker prerequisite/import.
5. Mounted-volume reconnect, full installed live E2E, signing/notarization,
   redistribution and actual clean-Mac acceptance.

The source tag `demo-v1.1` and current Test/Production remain separate from this
engineering candidate. No Cloud call, publication, provisioning, live restart,
Finish, commit, push or tag update belongs to this slice.
