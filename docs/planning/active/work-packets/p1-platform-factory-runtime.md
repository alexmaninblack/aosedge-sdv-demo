<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Platform Factory and Runtime Implementation Work Packet

- ID: `WP-P1-PLATFORM-FACTORY-RUNTIME-001`
- Lane: `L-PLATFORM`
- Increment: `IMP-03-FACTORY-RUNTIME`
- Review state: `IMPLEMENTED — PINNED SOURCE COMPILE/TEST PASSED; IMAGE QUALIFICATION PENDING`
- Version: 0.3
- Prepared: 2026-08-28
- Accepted: 2026-08-28
- Authorized: 2026-08-28
- Implementation authorized: yes — only the bounded source scope in this packet
- Bootable image build, demo/disposable VM, provisioning, signing, FOTA and
  live qualification authorized: no
- Parent plan: [Demo Implementation Plan 1.2](../demo-implementation-plan.md)
- Readiness input: [WP-P0-PLATFORM-001](p0-platform-readiness.md)
- Compile qualification:
  [WP-QUAL-P1-PLATFORM-RUNTIME-001](p1-platform-runtime-compile-qualification.md)

## Outcome

Implement only the product-layer IAM configuration and OEM Component Runtime
Safe Stop source changes required by the accepted successor Factory Image.
The packet preserves the existing provider-specific A/B runtime, empty VDP
slot and bounded 512-MiB working-storage backend while adding native IAM
Permission Handler enablement and the accepted Platform FOTA Safe Stop
application gate.

KAC named-resource, fixed-Provider signer preparation and final image-package
composition were removed from this packet on 2026-08-29. They are owned by the
separate blocked
[`WP-P1-PLATFORM-KAC-FACTORY-INTEGRATION-001`](p1-platform-kac-factory-integration.md)
packet and must not be guessed here.

Successful source verification does not qualify or freeze a Factory Image.
The full image build, disposable-VM checks and live FOTA qualification remain
separate explicit gates after the Factory/runtime, KAC and VDP branches are
integrated.

## Repository and Isolation

| Item | Frozen value |
| --- | --- |
| Repository | `aos-vehicle-platform` |
| Base revision | `bdc72aba97a83c9868d454588189ef139710a6d7` |
| Required base relationship | clean `main`, equal to `origin/main` at authorization |
| Branch | `codex/imp-03-factory-runtime` |
| Isolated worktree | sibling path `../aos-vehicle-platform-imp-03-factory-runtime` |
| Dependency repositories | `aosedge-sdv-demo` contracts and pinned AosEdge sources, read-only |

The implementation must stop if the base, dependency pins or worktree
cleanliness do not match. Generated build output stays outside every source
repository.

## Writable Boundary

Only the following owned boundaries may change:

- a new product-owned
  `meta-aos-vehicle-platform/recipes-aos/aos-iamanager/**` bbappend and its
  deterministic build-time configuration validator;
- `meta-aos-vehicle-platform/recipes-aos/aos-servicemanager/files/sm.cfg` and
  `files/systemd-slot-component/**` only for Runtime, Safe Stop
  adapter/evaluator, tests and their build wiring;
- `meta-aos-vehicle-platform/recipes-aos/aos-vehicle-data-provider-platform/**`
  only for Safe Stop runtime systemd and protected credential-source wiring;
- `tools/validate_r6_1_layer.py` and package-owned Factory/runtime validators;
- `tests/test_r6_1_layer.py` and package-owned Factory/runtime tests; and
- `meta-aos-vehicle-platform/README.md`, `docs/architecture.md` and
  `docs/contract-compatibility.md` only where factual implementation wording
  changes.

No file under `authorization/aos-kuksa-compat/` or
`providers/carla-viss-kuksa/` is writable in this packet. Any need to patch
upstream AosCore, KUKSA or another repository stops the packet.

## Exact Required Change

### Product-owned IAM configuration

1. Add one deterministic `aos-iamanager` product-layer transformation after
   the upstream/AosVM configuration is composed.
2. Set only Boolean `enablePermissionsHandler` to `true`; preserve every other
   main/secondary configuration difference.
3. Fail the build/source gate if the effective value is missing, false or not
   Boolean.
4. Keep the result independent of provisioning state and introduce no
   generated mode switch or second configuration authority.
5. Prove that Factory composition contains no Unit identity, Cloud credential,
   registered Service permission, `AOS_SECRET`, JWT, private signing key or
   shared static verifier.

### OEM Component Runtime Safe Stop gate

1. Add a transport-only VISS 3.1 mTLS adapter implementing
   `VehicleStateProviderItf` for the purpose-bound
   `PLATFORM_UPDATE_RUNTIME` role.
2. Add a pure evaluator for Platform FOTA Safe Stop Profile 1.1.1. It consumes
   only the ten accepted Gateway paths and requires 12 distinct monotonic
   observations. Every admitted frame must be no older than 250 ms when
   acquired; the accumulated history proves stability only. The latest
   complete frame must again be no older than 250 ms when the gate opens and
   immediately before every destructive runtime operation. Every frame has:
   - active mode `SAFE_STOP`;
   - stable transition state;
   - no reset in progress or reset discontinuity;
   - speed at most `0.3 km/h`;
   - accelerator at most `0.5%`; and
   - brake at least `95%`.
3. After candidate preparation and durable transaction metadata, return the
   native `Activating` state while one bounded asynchronous worker waits for
   Safe Stop for at most 480 seconds.
4. Never hold the Runtime mutex across the wait. Runtime stop performs bounded
   cancel-and-join.
5. Persist only transaction metadata. Never persist or reuse Safe Stop samples;
   Runtime or VM restart requires a new complete frame sequence.
6. First install leaves the slot empty while waiting. Replacement and removal
   leave the current healthy release active until the gate succeeds.
7. Loss of Safe Stop before destructive apply returns to waiting. Loss during
   destructive apply fails and rolls back.
8. Never resume driving automatically; readiness is followed by a separate
   presenter action.

### Safe Stop credential seam

1. Consume distinct per-Unit `PLATFORM_UPDATE_RUNTIME` VISS material only from
   protected persistent overlay sources delivered with `systemd
   LoadCredential`.
2. Keep all credential material outside Factory Image, FOTA artifacts, Git,
   logs and dashboards, and make missing/inconsistent material fail closed.
3. Preserve the existing empty VDP component slot and OEM Runtime A/B working
   storage; do not introduce a VDP application/log store.

## Required Verification

- all existing Platform Python tests plus new Factory/runtime tests pass;
- `tools/quality_gate.py` passes;
- the layer validator proves handler enablement, secret-negative Factory
  composition, fixed empty-slot/runtime-storage boundaries and protected
  credential-source wiring;
- the pure Safe Stop suite covers valid windows, threshold boundaries,
  repeated/out-of-order/stale/missing/contradictory frames, resets and
  discontinuities;
- Runtime tests cover first install, replacement, removal, timeout,
  cancellation, same-candidate reattach, different-candidate rejection,
  restart while waiting, Safe Stop loss and rollback;
- tests prove that no destructive stop, switch or activation occurs before the
  accepted gate; and
- changed files remain entirely inside the writable boundary.

The completion record must distinguish source verification and pinned
AosCore/Poco/GTest qualification from the later Yocto image build and
disposable-VM qualification. Passing the pinned C++ suite permits this packet
to claim `IMPLEMENTED`; it does not make the branch merge-ready or the Factory
Image `QUALIFIED` without the remaining integration gates.

## Source-Draft Checkpoint

- Recorded: 2026-08-29
- Isolated branch: `codex/imp-03-factory-runtime`
- Base: `bdc72aba97a83c9868d454588189ef139710a6d7`
- Checkpoint commit: `458cd95e2fe281ea96ce357a9863c4c7fb4f6038`
- Worktree after commit: clean

The checkpoint contains only IAM Permission Handler enablement, Safe Stop
runtime/adapter/evaluator source, protected Safe Stop credential wiring and
their package-owned tests/validators. It contains no named-resource guess,
fixed-Provider signer, KAC package inclusion or generated credential.

At the source-draft checkpoint, available verification passed 37 Python tests,
the R6.1 layer validator, the 91-file quality gate, Python bytecode compilation,
`git diff --check` and a strict standalone C++17 compile of the pure Safe Stop
evaluator. The integrated compile/test gap recorded at that checkpoint was
subsequently closed by the qualification below.

## Pinned Compile/Test Qualification

- Completed: 2026-08-29
- Final isolated commit:
  `4d8800636ded58386e2872a7e415dc1cc322c92c`
- Final source tree: `db3d316675a0cf0a60574c90634a75207a4a26c4`
- Toolchain: pinned R6.1 `qemuarm64` / `aarch64-aos-linux` GCC 13.4.0
- Result: two consecutive clean offline `aos-servicemanager` compiles passed;
  after each final compile, all 51 applicable tests passed and the two
  explicitly out-of-scope real-provider/image tests were skipped.
- Boundary: all 20 changed paths remain in this packet's writable ownership;
  no upstream or KAC source was modified.

The detailed recipes, cache/configuration hashes, corrective commits and test
evidence are recorded in
[`WP-QUAL-P1-PLATFORM-RUNTIME-001`](p1-platform-runtime-compile-qualification.md).
This closes the source implementation packet but does not authorize integration
to `main`, image construction or disposable-VM/live FOTA qualification.

## Explicit Exclusions

- no KAC executable, named resource, signer/verifier preparation, image-package
  inclusion, JWT issuance, Service bootstrap or permission mapping;
- no VDP v1-v3 implementation or artifact build;
- no upstream AosCore or KUKSA patch;
- no Demo UI, Cloud API or lifecycle-helper change;
- no dependency download, full Yocto/image build or external network access;
- no key, certificate, token, Unit identity or secret generation;
- no VM creation, provisioning, signing, upload, FOTA or live CARLA operation;
  and
- no push, merge or direct change to `main` by the worker.

## Authorization Gate

The user accepted the exact Safe Stop and IAM source outcome, repository base,
writable ownership, checks and exclusions on 2026-08-28, accepted the KAC
integration split on 2026-08-29 and authorized the bounded corrective
compile/test work on 2026-08-29. Source implementation is complete only in the
isolated branch/worktree. Integration, image construction and any external or
live operation require separately reviewed authorization.
