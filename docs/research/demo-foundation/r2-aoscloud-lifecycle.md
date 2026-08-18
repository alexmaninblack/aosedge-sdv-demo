<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R2 — AosCloud Lifecycle, Targeting, and Reset Semantics

Status: **research pass complete; implementation not authorized**.

## Decision scope

This workstream maps G0–G4 to the actual AosCloud/AosCore lifecycle, verifies
how validation and promotion are represented, and determines which parts of a
G4-to-G0 reset are supported versus still hypothetical.

The evidence uses official AosEdge documentation, the public AosCloud API v11
schema for implementation `6.1.26`, and sanitized local qualification records.
No Cloud mutation or credential use occurred.

## Executive conclusion

The OEM release narrative is achievable, but the draft scenario compresses
three separate Cloud gates into one:

```text
signed Deployment Bundle
        |
        v
Artifact Verification Batch
(per architecture; OEM/SP approval)
        |
        v
Verification Unit Set delivery
        |
        v
Fleet Validation Batch
(Waiting_validation -> Valid or Invalid)
        |
        v
Campaign bound to that Validation Batch
(targeting the Demonstration Unit Set)
        |
        v
Unit actual state converges and reports status
```

AosCore has declarative desired-state reconciliation. AosCloud does not expose
one API object named `G0`, `G1`, and so on. Those are demo-level classifications
derived from Cloud records plus Unit-reported actual state.

## Findings

| Finding | Classification |
| --- | --- |
| AosCloud sends the complete desired set of services, layers, components, and instances; AosCore reconciles actual state toward it. | **PROVEN** |
| SOTA removal is represented by removing the service from desired Subject-service state; a prior Hello World test proved instance/process/network removal. | **PROVEN** |
| FOTA `RevertUpdate` is available only before `ApplyUpdate`; post-Apply rollback is outside that transaction. | **PROVEN** |
| An applied P3 component can be arbitrarily removed or downgraded P3→P2→P1→absent through normal Cloud desired state. | **REQUIRES EXPERIMENT** |
| A higher-version reset provider that disables or removes feature behavior is compatible with monotonic FOTA delivery. | **PROPOSED** |
| Component manifests support version constraints and component-to-component runtime dependencies. | **PROVEN** |
| Service configuration supports layer dependencies and resource/runtime constraints but exposes no documented Service-to-FOTA-component dependency. | **PROVEN** |
| Mixed SOTA/FOTA Deployment Bundles exist as a coordinated platform model. Exact atomic failure behavior in the current Cloud is unqualified. | **PROVEN model / REQUIRES EXPERIMENT behavior** |
| Campaign creation requires a Fleet Validation Batch and can target Unit Sets. Campaign data exposes phase, state, statistics, and Unit results. | **PROVEN** |
| Stopping a campaign or invalidating a batch prevents further delivery; it does not prove rollback of Units that already applied the update. | **PROVEN limitation** |
| Service versions and component sequences are monotonic; committed lower-version component installation is not documented as a supported downgrade. | **PROVEN limitation** |

## Platform roadmap update — 2026-08-18

The AosEdge Platform Team stated that native Service-to-FOTA-component
dependency enforcement is on the platform roadmap but is not implemented in
the current release. No implementing release or delivery date was committed.
This is stakeholder roadmap input, not released-API evidence.

The project therefore keeps the native pre-deployment rejection scenario in
the target demo design but defers its execution. It will not add a temporary
Software Delivery Dashboard admission controller. Service-side compatibility
metadata and fail-closed readiness remain the current defense-in-depth
mechanism until the native Cloud capability is released and qualified.

## Honest G0–G4 representation

| Stage | Cloud-derived definition |
| --- | --- |
| G0 | Units provisioned and online; no Brake Health Subject-service assignment; no active provider capability according to the selected reset design |
| G1 | Provider P1 installed and reported; Brake Health service absent |
| G2 | P1 installed; Service S1 assigned and `Active` |
| G3 | P2 installed; Service S2 assigned and active |
| G4 | P3 installed; Service S3 assigned and active |

The exact allowed versions and identities belong in a version-controlled demo
release manifest. The Software Delivery Dashboard derives a stage only when
actual component and service state matches one accepted manifest exactly.

If committed provider removal is impossible, G0 must instead mean a
higher-version **feature-disabled reset provider** with no active capability.
That would be a deliberate scenario change and must not be hidden behind the
word rollback.

## Verification target hazard

The public Verification Batch response lists artifact items, architectures,
and approval states but no explicit effective target-Unit list. Target evidence
must be derived from:

- current Verification Unit Set membership;
- each Unit's component `pending_validation_batch_id`;
- equivalent pending batch references for service versions;
- campaign Unit Sets and campaign per-Unit statistics.

Sanitized local evidence proves that an existing stale batch retained the
Demonstration Unit after that Unit was removed from the Verification Set. A new
batch created after correcting topology targeted only Validation.

This suggests targets are snapshotted or persisted at batch creation, but the
platform team must confirm the intended behavior. The operational rule is
clear now: never approve from current Unit Set membership alone. Compare the
recorded pending recipients with the intended set and block on any mismatch.

## Dependency policy

Because a documented Service-to-FOTA-component dependency is absent, use:

1. strict release ordering: provider first, service second;
2. a versioned application capability contract;
3. fail-closed service startup/readiness when the required provider contract
   is missing or incompatible;
4. an exact accepted Pn+Sn graph manifest;
5. reverse service-first reset ordering.

A mixed Deployment Bundle may later strengthen coordinated delivery, but its
failure and rollback atomicity must be proved before it becomes the demo's
dependency mechanism.

## Reset recommendation

### Primary candidate — forward/native reset

1. Remove S3 from Subject-service desired state.
2. Wait until the service instance and its runtime state are absent.
3. Deliver a higher-version provider reset component that empties or disables
   the provider capability if normal removal/downgrade is unsupported.
4. Verify actual Unit state matches the G0 manifest.
5. Reset CARLA, Function Backend, bounded AosCloud log-request artifacts, and
   transient dashboard run state separately.

This is a **forward reset release**, not a rollback.

### Fallback — protected G0 snapshot

Restore the correct per-Unit golden image only after Cloud target state is G0
or while the VM remains isolated. Enforce single-active-copy identity and the
reconciliation controls defined by R3.

## Required experiments

1. Create a fresh component batch and compare intended Verification Set
   members with every Unit's pending batch reference before approval.
2. Repeat the target comparison for a service update.
3. Exercise the complete Fleet Validation Batch → Campaign → Demonstration
   flow and capture actual state strings and timing.
4. Prove whether a committed provider can accept a lower component version in
   a higher-sequence bundle.
5. Qualify a higher-version feature-disabled provider reset.
6. Qualify a mixed provider/service Deployment Bundle, including partial
   failure and restart behavior.
7. Confirm that campaign stop or invalidation prevents new targets without
   claiming rollback of completed targets.
8. Request platform confirmation of stale target retention and whether a
   public effective-target endpoint is planned.

## Draft statements requiring later correction

- `Desired graph G0` is a demo manifest, not an AosCloud API object.
- Verification Batch does not directly return the effective Unit target list.
- `remove P1` and reverse provider rollback to G0 are unproven operations.
- `select G0, then remove providers` is proposed orchestration, not one
  confirmed Cloud action.
- Component SHA-256 evidence is available; a service OCI digest is not
  documented by the public service-version API.
- Single-Unit verification targeting is safe only for a fresh batch after
  recipient reconciliation.

## Sources

- [AosCore desired-state concepts](https://docs.aosedge.tech/docs/aos-core/system-overview/key-concepts)
- [AosCore Unit status handler](https://docs.aosedge.tech/docs/aos-core/architecture/cm/unit-status-handler)
- [AosCore service lifecycle](https://docs.aosedge.tech/docs/aos-core/service-lifecycle)
- [AosCore deployment flows](https://docs.aosedge.tech/docs/aos-core/deployment-flows)
- [AosCore error handling](https://docs.aosedge.tech/docs/aos-core/error-handling/)
- [AosEdge component update schema](https://docs.aosedge.tech/docs/reference/core-component-configs/core-update-config)
- [AosEdge service configuration schema](https://docs.aosedge.tech/docs/reference/core-component-configs/core-service-config)
- [AosCloud campaign management](https://docs.aosedge.tech/docs/v1/aos-cloud/components-view/campaign-management-component)
- [Local validation target-scope defect](../../qualification/r6-1-validation-set-scope-defect.md)
