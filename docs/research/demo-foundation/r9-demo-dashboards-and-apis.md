<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R9 — Demo Dashboards and AosCloud API Feasibility

Status: **research pass complete; implementation not authorized**.

## Decision scope

This workstream determines which Software Delivery Dashboard claims can be
supported by the current public AosCloud API and clarifies authority boundaries
among the Engineering, Software Delivery, Function, and ELK views.

## Executive conclusion

A useful read-only Software Delivery Dashboard is feasible. Existing public
API data can show:

- Validation and Demonstration lanes;
- Unit provisioned/connection state;
- installed and pending components;
- assigned service versions and instance state;
- Artifact Verification and Fleet Validation state;
- Campaign phase, statistics, and per-Unit results;
- alerts, resource monitoring, and existing log requests.

It cannot truthfully provide every requested story element directly. G0–G4,
effective verification targets, application readiness, and some artifact
identity fields must be derived or supplied by version-controlled evidence.

## Recommended architecture

```text
Browser on localhost
  -> read-only dashboard backend
       -> private key remains server-side
       -> allowlisted GET endpoints only
       -> response normalization
       -> target-recipient mismatch guard
       -> short, non-authoritative cache
  -> AosCloud API v11 over mTLS
```

Use a dedicated least-privilege read-only OEM identity if the platform permits
a suitable permission group. Do not place the private key or PKCS#12 material
in browser JavaScript. Direct browser mTLS and CORS are **REQUIRES EXPERIMENT**;
the backend is the safe default.

Write operations belong in a separate action adapter, disabled by default and
outside the first dashboard release. Approval, campaign creation, assignment,
and deletion must never occur as background polling side effects.

## API capability map

| Dashboard data | Public read API |
| --- | --- |
| Unit lanes, provisioning, online state | `GET /units/`, `/units/{id}/`, `/units/{id}/connection-info/` |
| Unit Sets and membership | `GET /unit-sets/`, `/unit-sets/{id}/units/` |
| Artifact Verification | `GET /verification-batch/`, `/verification-batch/{batch_id}/` |
| Fleet Validation | `GET /fleet-validation-batch/`, `/fleet-validation-batch/{id}/` |
| Promotion Campaign | `GET /campaigns/`, `/campaigns/{id}/` |
| Installed/pending FOTA | Unit detail, `/components/`, `/update-components/` |
| Installed/pending SOTA and instances | `/units/{id}/subjects-services/`, `/services/versions/` |
| Component SHA-256 evidence | `/update-components/{id}/` |
| Monitoring | `/units/{id}/monitoring/`, `/units/{id}/monitoring/dashboard/` |
| Alerts | `/alerts/` |
| Existing log requests | `/service-logs/`, `/unit-logs/` |
| Audit/action history | `/metrics/` |

Creating a log request is a POST and is therefore an explicit operator action,
not part of the read-only poller.

## Proposed views

### 1. Release Overview

Two lanes show Unit role, online/last-reported time, derived G-stage, actual
provider version, assigned service version, and instance state.

### 2. Candidate and Target Guard

Show artifact identity, architecture verification state, current Verification
Set members, and Units that actually carry the candidate's pending batch ID.
Raise a blocking mismatch banner when those sets differ.

### 3. Validation

Show the Fleet Validation state, source/target graph manifests, qualification
evidence link, timestamp, and decision. Do not combine it with Artifact
Verification.

### 4. Promotion

Show Campaign, target Unit Set, phase, waiting/in-progress/success/failure
counts, and per-Unit outcome.

### 5. Technical drill-down

Show raw pending/installed component fields, service instances, errors,
alerts, monitoring, and log-request status with original API timestamps.

## Honest display limitations

| Requested claim | Honest implementation |
| --- | --- |
| Effective Verification target | Derive from pending batch references and compare with current Unit Set; no direct batch target field |
| G0–G4 | Derive only from a version-controlled accepted graph manifest; not an AosCloud entity |
| Provider/service readiness | Cloud status plus separate qualification or application health evidence; install state alone is insufficient |
| Download progress | Show only actual structured status/campaign data; fine-grained byte progress is not guaranteed |
| Artifact digest | Component SHA-256 is available; public service-version response does not document an OCI digest |
| ELK availability | Show log-request state only; API presence does not prove ELK export |
| Real-time state | Display `last reported`; Unit aggregation can lag and must not be presented as instantaneous |

## Authority boundaries

| Surface | Authoritative for | Not authoritative for |
| --- | --- | --- |
| Engineering Dashboard | Gateway VISS telemetry and factual advisory request/status | KUKSA delivery, Cloud lifecycle, functional backend |
| Software Delivery Dashboard | Human-friendly presentation of AosCloud release and Unit state | Vehicle telemetry and prediction results |
| Function Dashboard | Brake Health samples, predictions, reports, backlog and model state from Function Backend | FOTA/SOTA state and Gateway receipt |
| AosCloud UI/API | Technical lifecycle source and drill-down | Functional telemetry product view |
| ELK | Selected operational log evidence | Vehicle signal truth or lifecycle authority |

## Security and robustness

- Permit only a fixed list of read endpoints in the first backend.
- Never log client certificate details, private keys, bearer data, raw response
  bodies, or unredacted Unit identities.
- Normalize to a small internal schema and preserve source timestamps.
- Cache only briefly for UI stability; the cache is never desired-state
  authority.
- Treat absent/stale/ambiguous data as `UNKNOWN`, not success.
- Store display aliases for Unit roles separately from Cloud identifiers.
- Show the source API field beside a friendly label in technical drill-down.
- Make the target-recipient mismatch a visible safety condition, not a hidden
  warning in logs.

## Required experiments

1. Test localhost backend mTLS without exporting private key material.
2. Measure latency and eventual consistency for every proposed GET endpoint.
3. Verify target derivation against pending batch IDs on both Units.
4. Capture actual pending/install/run-state strings during one harmless update.
5. Confirm service-version identity and digest evidence exposed in the live
   environment.
6. Verify whether a least-privilege custom OEM read permission group can see
   the entire required view.
7. Confirm browser CORS behavior only to validate that direct access remains
   rejected as the architecture choice.
8. Design guarded write actions only after the read-only dashboard is accepted.

## Impact on demo planning

The first Software Delivery Dashboard can be implemented without reproducing
all AosCloud functionality. Its strongest value is one aligned narrative
surface plus the verification-target guard. The official UI remains the
technical source-of-truth drill-down.

## Sources

- [AosCloud API entry point](https://docs.aosedge.tech/docs/aos-cloud/api-info)
- [AosEdge Monitor a Unit](https://docs.aosedge.tech/docs/how-to/advanced-device-operation/monitor-device)
- [AosEdge Monitor a Service](https://docs.aosedge.tech/docs/how-to/advanced-service-operation/monitor-service)
- [AosCloud campaign management](https://docs.aosedge.tech/docs/v1/aos-cloud/components-view/campaign-management-component)
- [Local validation target-scope defect](../../qualification/r6-1-validation-set-scope-defect.md)
- [Architecture flows](../../architecture/demo-scenario-architecture-flows.md)
