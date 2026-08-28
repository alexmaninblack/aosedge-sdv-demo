<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Platform Factory and Runtime Implementation Work Packet

- ID: `WP-P1-PLATFORM-FACTORY-RUNTIME-001`
- Lane: `L-PLATFORM`
- Increment: `IMP-03-FACTORY-RUNTIME`
- Review state: `ACCEPTED — AUTHORIZED`
- Version: 0.1
- Prepared: 2026-08-28
- Accepted: 2026-08-28
- Authorized: 2026-08-28
- Implementation authorized: yes — only the bounded source scope in this packet
- Image build, VM, provisioning, signing, FOTA and live qualification authorized: no
- Parent plan: [Demo Implementation Plan 1.2](../demo-implementation-plan.md)
- Readiness input: [WP-P0-PLATFORM-001](p0-platform-readiness.md)

## Outcome

Implement the product-layer Factory configuration and the OEM Component
Runtime Safe Stop source changes required by the accepted successor Factory
Image. The packet must preserve the existing provider-specific A/B runtime,
empty VDP slot and bounded 512-MiB working-storage backend while adding the
native IAM configuration enablement and the accepted Platform FOTA Safe Stop
application gate.

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

- `meta-aos-vehicle-platform/recipes-core/images/aos-image-vm.bbappend`;
- a new product-owned
  `meta-aos-vehicle-platform/recipes-aos/aos-iamanager/**` bbappend and its
  deterministic build-time configuration validator;
- `meta-aos-vehicle-platform/recipes-aos/aos-servicemanager/files/sm.cfg`, the
  product-owned named-resource configuration input and
  `files/systemd-slot-component/**` only for Runtime, Safe Stop
  adapter/evaluator, tests and their build wiring;
- `meta-aos-vehicle-platform/recipes-aos/aos-vehicle-data-provider-platform/**`
  only for Factory/runtime systemd, credential-source and image-composition
  wiring;
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
2. Add a pure evaluator for Platform FOTA Safe Stop Profile 1.1.0. It consumes
   only the ten accepted Gateway paths and requires 12 distinct monotonic
   frames, each no older than 250 ms, with:
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

### Credential and image-composition seam

1. Consume distinct per-Unit `PLATFORM_UPDATE_RUNTIME` VISS material only from
   protected persistent overlay sources delivered with `systemd
   LoadCredential`.
2. Keep all credential material outside Factory Image, FOTA artifacts, Git,
   logs and dashboards, and make missing/inconsistent material fail closed.
3. Preserve the existing empty VDP component slot and OEM Runtime A/B working
   storage; do not introduce a VDP application/log store.
4. Register the fixed `kuksa-auth-client` named resource in the product-owned
   Aos resource configuration: shared count four, the single supplementary
   group, read-only KAC socket-directory mount and container-private 64-KiB
   token tmpfs. This transport allocation contains no authority or secret.
5. Add one post-provision, platform-owned and non-networked preparation step
   that signs exactly one seven-day fixed Provider JWT from the accepted
   per-Unit `kuksa-jwt` key into the protected persistent credential source
   used by `LoadCredential=kuksa-token`. It is not a KAC endpoint, performs no
   renewal and contains only the accepted v1-v3 Provider path union.
6. Add the accepted future `aos-kuksa-auth-compat` package to successor image
   composition only as an integration dependency. The Factory/runtime branch
   must not merge to `main` until the independently implemented KAC package is
   present and the combined source gates pass.

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

The completion record must distinguish source verification from the later
pinned AosCore/Yocto compile, image build and disposable-VM qualification.
The packet cannot claim `QUALIFIED` without those later gates.

## Explicit Exclusions

- no KAC executable, JWT issuance, Service bootstrap or permission mapping;
- no VDP v1-v3 implementation or artifact build;
- no upstream AosCore or KUKSA patch;
- no Demo UI, Cloud API or lifecycle-helper change;
- no dependency download, full Yocto/image build or external network access;
- no key, certificate, token, Unit identity or secret generation;
- no VM creation, provisioning, signing, upload, FOTA or live CARLA operation;
  and
- no push, merge or direct change to `main` by the worker.

## Authorization Gate

The user accepted the exact source outcome, Safe Stop semantics, repository
base, writable ownership, KAC merge dependency, checks and exclusions on
2026-08-28. Implementation may begin only in the isolated branch/worktree.
Any boundary expansion or external operation requires a separately reviewed
change request.
