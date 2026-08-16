<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R6.1 Vehicle-Data Integration Component Plan

- Status: Proposed for review
- Scope: planning only
- Current gate: architecture acceptance
- Cloud or Unit mutation authorized: no

## Objective

Give public, independently evolving vehicle-integration material an explicit
OEM FOTA lifecycle and make the vehicle-data provider depend on a compatible
installed version. The provider must not install when its public integration
component is unavailable or incompatible, and it must not run without a valid
credential.

This plan uses two separate controls:

1. Aos FOTA `runtimeDependencies` controls the component/version relationship
   in Cloud desired state.
2. Local readiness and health controls fail closed if files, KUKSA, VISS trust,
   or the provider credential are not usable at runtime.

The Cloud relationship is component-to-component, not batch-to-batch. A batch
is a validation and rollout vehicle; it is not a stable dependency identity.

## Lifecycle and File Ownership

| Item | Owner and delivery path | Secret | Update reason |
| --- | --- | --- | --- |
| Provider executable and ARM64 dependencies | `vehicle-data-provider` FOTA component | No | Provider implementation release |
| Embedded provider profile and timing defaults | `vehicle-data-provider` FOTA component | No | Provider implementation/contract release |
| External model-level provider configuration | `vehicle-data-integration` FOTA component | No | Vehicle integration or endpoint policy change |
| VISS CA | `vehicle-data-integration` FOTA component | No | Vehicle trust-anchor rotation |
| KUKSA public verifier | `vehicle-data-integration` FOTA component | No | KUKSA authorization-key rotation |
| KUKSA provider token | Credential delivery boundary; temporary demo helper, later AOS-5 adapter | Yes | Expiry, revocation, or permission change |
| Unit-specific endpoint or identity data | Provisioning or a future Unit configuration channel | Depends on value | Per-Unit configuration change |

The external provider configuration in this plan is the runtime file currently
expected below the platform-owned `configuration` directory. It is distinct
from the non-secret profile included inside the provider payload.

No private signing key, KUKSA token, Unit identity, user certificate, account
identifier, or raw operational evidence may enter either FOTA component or
Git.

## Proposed Component Identities

The final names are accepted before implementation. The current proposal is:

| Component | Proposed type | First planned version |
| --- | --- | --- |
| Public integration material | `aos-vm-1.0.0-main-qemuarm64-vehicle-data-integration` | `0.1.0` |
| Provider successor | `aos-vm-1.0.0-main-qemuarm64-vehicle-data-provider` | `0.2.1` |

Provider `0.2.1` will declare a `runtimeDependencies` constraint on a compatible
integration-component version. The exact initial constraint is chosen after
the compatibility contract is fixed. Prefer a minimum compatible version only
when forward compatibility is demonstrated; otherwise require the exact
accepted `0.1.0` version for the first deployment.

Signed provider `0.2.0` remains immutable. Its signed configuration cannot be
changed to add a dependency. It remains local evidence and is not the provider
selected by this plan.

## Unit Runtime Design Requirements

The existing rootfs candidate exposes only the provider component runtime and
its provider-specific archive contract. A second component therefore requires
a second independently reported runtime configuration. Reusing refactored
implementation code is allowed, but the two component types must not share a
working directory, slots, transaction state, active link, or garbage
collection boundary.

The integration runtime must:

1. use a bounded persistent A/B store separate from the provider store;
2. accept only a small allowlisted archive layout and reject links, devices,
   unsafe paths, unexpected files, ownership, modes, or oversized input;
3. validate the JSON schema and all PEM files before changing active state;
4. atomically switch one complete integration version;
5. activate the KUKSA verifier and prove KUKSA readiness;
6. expose stable read-only active paths for the provider configuration and
   VISS CA;
7. preserve the previous accepted version until the update is committed;
8. recover or roll back deterministically after interruption;
9. report its own type, version, status, and failure to AosCore and AosCloud;
10. never write a provider token or private key.

The provider runtime must be adjusted to consume the stable active public
paths without gaining write access to the integration store. Its systemd unit
must retain `LoadCredential` for the token and fail closed when that credential
is absent, invalid, expired, or has insufficient scope.

## Activation and Dependency Semantics

`runtimeDependencies` ensures that Cloud plans a compatible integration
component together with the provider. It does not replace local startup
ordering or health checks. The design must remain safe if both component
updates are delivered concurrently or status messages are delayed.

Required behavior:

1. stage and validate the integration candidate;
2. switch the public configuration atomically;
3. make KUKSA accept the selected verifier and pass its health check;
4. start or restart the provider only when public integration data and a valid
   token are available;
5. fail the provider update and retain or restore the previous accepted state
   if readiness cannot be established.

Installation blocking and runtime fail-closed behavior are separate tests:

- absent or incompatible integration component: provider installation is
  blocked by dependency resolution;
- missing or invalid token: provider does not become active even when both
  public components are installed;
- unavailable VISS or KUKSA endpoint: the installed provider remains fail-safe
  and follows its qualified reconnect and unavailable-value behavior.

## Compatibility and Rollback

The public integration component has its own semantic version and documented
schema version. A provider release declares the integration versions it can
consume.

The first accepted combination is planned as:

```text
next rootfs candidate
vehicle-data-integration 0.1.0
vehicle-data-provider 0.2.1
```

Qualification must prove these transitions:

- clean installation of integration first and provider second;
- a single desired state containing both components;
- provider request with no dependency candidate available;
- provider request with an incompatible dependency version;
- integration update while the current provider remains compatible;
- provider update while the current integration component remains compatible;
- provider rollback before any integration rollback;
- rejection of an integration rollback that would violate the active provider
  constraint;
- power-loss or process interruption during each component's prepare, switch,
  health, commit, and rollback phases.

KUKSA verifier rotation also requires an explicit token transition. If KUKSA
can trust an old and new verifier concurrently, qualification uses an overlap
window. If it cannot, the plan must define and measure the bounded service
interruption and rollback ordering before implementation is accepted.

## Revised Execution Gates

### Gate 1 — Architecture review

Accept or revise this document. Resolve component names, exact version
constraint, configuration schema ownership, Unit-specific configuration
boundary, KUKSA verifier rotation behavior, runtime implementation approach,
and rollback order. No implementation occurs in this gate.

### Gate 2 — Runtime implementation without Yocto

Implement the second runtime and integration archive validator in the platform
repository. Reuse the existing plugin only after removing provider-specific
assumptions; otherwise implement a focused sibling plugin. Run native and
isolated ARM64 tests without mutating a provisioned Unit.

### Gate 3 — Integration component packaging

Create reproducible unsigned `vehicle-data-integration` `0.1.0` packaging,
provenance, SBOM, size limits, validation, and secret-exclusion checks. Use
public demonstration material only.

### Gate 4 — Dependent provider successor

Produce provider `0.2.1` from accepted provider behavior and add the signed
component dependency. Do not modify, replace, or reuse the signed identity of
`0.2.0`.

### Gate 5 — Consolidated pre-build qualification

Run the complete component, security, dependency, activation, failure,
recovery, and rollback matrix. Analyze all failures together. Start no Yocto
build until this matrix is green and the rootfs delta is frozen.

### Gate 6 — Incremental rootfs candidate

Use the preserved builder disk, downloads, shared state, and work directories
to build only the accepted delta. The next candidate is provisionally `.12`.
It supersedes `.11` for deployment planning but does not erase `.11` evidence.

### Gate 7 — Disposable-VM acceptance

Qualify the new rootfs and both unsigned components on a disposable AArch64 VM
under SELinux Enforcing. Prove inventory reporting, storage isolation,
activation, restart, dependency failures, credential failures, data flow, and
rollback without a Cloud or provisioned-Unit mutation.

### Gate 8 — Freeze, sign, and verify

Freeze exact inputs and digests. Signing requires explicit authorization and
does not authorize upload. Independently verify all signed envelopes and their
dependency metadata.

### Gate 9 — Validation Unit rootfs

After separate authorization, refresh the protected checkpoint and deploy only
the accepted rootfs to the validation Unit. Verify boot and both empty runtime
inventories before assigning either application component.

### Gate 10 — Validation Unit components

Publish and assign the integration component and provider to the validation
Unit. Qualify Cloud dependency resolution as an observed platform behavior,
including the negative absent and incompatible cases. Account for the known
validation-set scope defect for every batch and assignment.

### Gate 11 — End-to-end and rollback

Run CARLA, VISS, provider, KUKSA, and the consumer. Prove live telemetry,
source loss, recovery, restart, public integration update, provider update,
credential failure, and dependency-safe rollback.

### Gate 12 — Promotion decision

Review sanitized validation evidence and decide separately whether to promote
the exact accepted graph to the demonstration Unit. Promotion is not implied
by validation success.

## Current Stop Point

This document is the only result of the plan change. No runtime, component,
bundle, rootfs, signed artifact, Cloud object, VM, or Unit has been changed.
Implementation begins only after Gate 1 is explicitly accepted.
