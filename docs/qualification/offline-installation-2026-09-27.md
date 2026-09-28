<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Offline Installation Transaction — Stage 3 First Slice

- Date: 27 September 2026.
- Status: Isolated source checks, complete-kit first installation and explicit
  verified repeat PASS; not native first-use or activation qualification.
- Decision: [ADR 0018](../architecture/decisions/0018-installable-demo-and-first-use.md).
- Contract: [Offline installation](../../contracts/distribution-installation/README.md).
- Parent: [Distribution plan](../planning/active/installable-distribution-and-reproducibility.md).

## Scope and preserved boundaries

Implemented an engineering `plan` / `install` / `verify` entry point and a
bounded complete-kit reader. This is not yet a native first-use wizard, DMG,
signed application, runtime activation or clean-Mac qualification. Its only
successful installation state is `INSTALLED_NOT_ACTIVATED`.

The tool accepts an independent application-manifest pin and an explicit
volume UUID. It verifies all five input groups and the Factory catalogue
mirror, copies into private resumable staging, and promotes a verified version
atomically. Repeated installation verifies and reuses that version. Source
files, operator state and unknown destination content are not modified.

The accepted first-use topology is one OEM and one SP owning two distinct
services. No accounts, certificates, VM identities, Docker state or Cloud
resources were created or changed by this slice. No package code is executed
by the installer. Source work remains on `codex/installable-demo-stage3`; the
immutable `demo-v1.1` checkpoint and previous unrelated working changes remain.

## Source acceptance

The reviewed working source starts from integration commit
`0d132125f8c88776b173060dc0cbc414332bcc45` plus existing work and this increment;
this is not a new published release. The final installer source/test identities
are recorded separately from the unchanged payload pin:

| Source | SHA-256 |
| --- | --- |
| [Transaction engine](../../scripts/distribution/installation.py) | `301d861029b5c965ed8efc9b1d370267dddb9d7c0cd08795de3c117b548b251e` |
| [Complete-kit reader](../../scripts/distribution/installation_inputs.py) | `795ee8d26be554eb94765da97adb7c3d82cdba5b3442b9f5124c82046c3b0371` |
| [Isolated tests](../../tests/test_distribution_installation.py) | `2a0bbb675a276b779f14894f04dedd93bb545ab179e27ec9ebd24ac5a3d04fd3` |

- **34 installer tests PASS**, using the packaged host Python 3.12 without
  additional dependencies. Fixtures are small, local and never executed.
- **152 distribution tests PASS**, including the installer and existing
  application, native/Python, Cloud/backend and vehicle-input packaging tests.
- First installation, verified repeat, changed-source rejection, changed
  completed-file rejection, corrupted promoted-version preservation, single
  writer, interrupted-copy resume, partial-copy replacement and post-promotion
  receipt recovery are exercised. Recovery reconstructs the store object from
  on-disk state; it does not depend on a retained progress counter.
- Negative cases cover missing/wrong/changed volume, absent parent, foreign
  destination, inadequate/free-space loss, wrong pins, incomplete inventory,
  metadata/path duplicates, traversal, case collision, links, unsafe modes,
  source/store overlap and missing Factory mirror.
- Full verification also reconciles the final inventory and identities to
  reject mutation of an earlier file while a later file is being checked.

The broad suite's Cloud **build** tests require the documented `packaging`
dependency. An initial run with host-only Python could not import that test
module; no installation test depended on it. The complete suite subsequently
passed with the already-present Cloud Python runtime (Python 3.12.14,
`packaging` 26.3), without installing or downloading anything. This is a test
harness dependency, not a new operator prerequisite or installer fallback.

## Complete-kit proof target

Source: the unchanged [SSD Kit 004](external-ssd-package-2026-09-27.md), under
`/Volumes/SDV-Work/AosEdge-SDV/packages/runtime-kit-004-20260927`.
Independent application-manifest SHA-256:
`c7f5b967ae08407b4f1ee09714a7a0cea5ba555e5076598761052b3b990187bd`.

Destination: the exclusive
`/Volumes/SDV-Work/AosEdge-SDV/install-tests/stage3-store-001`.
The store is bound to Work UUID `591578E3-8196-4B44-A575-CEC76B406789` with
normal ownership enforcement. The Clean volume is not used.

The read-only plan passed: **17,679 files; 35,114,325,564 logical bytes**;
required free space **131,751,089,724 bytes**, including the conservative
90 GiB reserve. Planning deliberately reports `payloadDigestsVerified: false`;
full payload verification belongs to installation, not this metadata preflight.
Installation started with **614,611,550,208 bytes free** on Work.

Installation uses same-volume APFS per-file clones where supported, with an
ordinary-copy fallback and identical verification. Logical file size is not
unique physical allocation. Do not use a simple directory-size sum to infer
duplicated disk consumption from clones.

### Corrected volume-identification defect

The first real preflight exposed two differences from the initial mock:
`diskutil info` does not accept an arbitrary nested directory, and its actual
plist reports `MountPoint` rather than a `Mounted` Boolean. Neither failed
preflight started a copy. The corrected implementation resolves the device
with `df`, validates its form, obtains the volume UUID/ownership/mountpoint,
and checks that the device is unchanged. It preserves the specific fixed
ownership error rather than catching it as a generic parse failure.

Regression tests use the observed plist shape and reject a non-device source
and disabled ownership. Stable per-file device checks plus periodic and
pre-promotion UUID checks avoid spawning one disk query for every file.

### Measurements and disposition

The complete first install passed in **311.68 seconds** including manifest,
inventory and volume preflight, copy, per-file verification, final identity
reconciliation, promotion and receipt. It returned all 17,679 files and the
expected logical byte count, `reused: false`, with all runtime/Cloud effects
false. No payload was launched.

An explicit second invocation in a fresh process passed in **98.81 seconds**.
It revalidated the complete installed inventory/digests and volume, returned
`reused: true`, and left exactly **one version** and **empty staging**. Its copy
callback was replaced with an assertion failure, proving that no second payload
copy was attempted. The normal private receipt was updated successfully;
all runtime/Cloud effect fields remained false. No third full hash pass was
performed merely for reporting.

Free space after that operation was **614,534,115,328 bytes**: an observed
volume-wide reduction of **77,434,880 bytes (73.85 MiB)**, not another 32.7 GiB
copy. This includes filesystem/background effects and is not a precise
exclusive allocation measurement. Source and installed package both remain;
future modification can increase clone allocation. No internal artifact was
deleted and no internal disk-space gain is claimed.

During transfer the existing QEMU, CARLA, Driving Control and Presenter PIDs
were still 18914, 19988, 20208 and 51041, unchanged in the final post-install
observation. This proves those observed processes
were not restarted by this work; it is not a fresh functional/E2E assessment.

The store root, version root and staging are mode `0700`; the store marker
and writer lock are mode `0600`, owned by the current operator. Free space at
the end of the repeat was **614,533,877,760 bytes** on Work. Clean, the internal
original, the transferred source package and the running demo are preserved.

The documentation gate passed with **291 Markdown documents, 658 stable
identifiers and 38 Mermaid diagrams**; `git diff --check` passed. The final
distribution regression rerun passed **152 tests**. These are source/document
and isolated installation gates, not a live scenario result.

## Remaining gates

Complete the installed-state canonical requirements/architecture cascade and
separate immutable input selection from private durable state before runtime
activation. Then implement the native first-use wizard and DMG, account-access
checks/enrollment, explicit updates, data-preserving repair/removal and safe
rollback. Developer ID/notarization, redistribution review, clean-system
installation and the complete live scenario remain separate gates.

No new Factory build, package publication, source push, credential enrollment,
live runtime switch or removal was performed for this slice.
