<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0012: Authorize Running Workloads, Not Software Artifacts

- Status: Accepted as a technology-neutral security architecture input
- Date: 2026-08-21
- Current demo mapping: SOTA Service workloads follow this model through
  ADR 0013; the OEM-qualified VDP is an explicit trusted-platform exception
  recorded under `D4-010.2`

## Context

`Component` is a release and composition concept, not a sufficient runtime
security principal. A component may be a bootloader, operating-system library,
system daemon, container image, VM image, FOTA payload or SOTA service. Some
are passive artifacts; others create one or more independently isolated
running instances. Giving a reusable token to the artifact confuses software
provenance, execution identity and authorization and makes update, revocation,
multi-instance isolation and offline operation unsafe or ambiguous.

KUKSA is the motivating resource server, but the decision is intentionally
technology-neutral. The same model applies to any local service that accepts
capability-bearing tokens.

## Decision

### Separate four identities

The architecture shall distinguish:

1. **artifact identity** — component type, version, digest, signer and release
   provenance;
2. **device identity** — the vehicle, ECU or Unit on which execution occurs;
3. **workload identity** — the exact running process, container or VM instance,
   including runtime generation and isolation boundary; and
4. **authorization** — the operations and resources allowed to that workload
   at the current time.

A token is issued to a running workload identity. It is never issued merely
because an artifact exists, was downloaded or is present in an inactive slot.

### Establish identity at the runtime boundary

A trusted runtime verifies the artifact and creates the workload instance. It
shall provide non-caller-controlled evidence binding the workload to the
verified artifact digest, deployment/device identity, runtime type, active
generation and isolation principal. The exact evidence may be supplied by a
service manager, system manager, container runtime, VM manager, measured-boot
facility or component runtime, but the workload may not self-assert those
facts.

The isolation boundary determines the principal:

| Software form | Authorization principal |
| --- | --- |
| Bootloader or pre-runtime firmware | Normally no application token; use verified/measured boot, anti-rollback and device identity for any required authenticated channel |
| In-process library | The host process identity; a library does not receive independent authority |
| System daemon | The exact service instance bound to its verified executable, system-service identity and confinement domain |
| Container | The running container/workload instance bound to image digest, sandbox and runtime generation |
| VM | The running VM instance bound to verified image/measurement and VM identity |
| FOTA component | The active component-runtime instance bound to accepted type, digest, slot and generation |
| SOTA service | The active service instance established by the service runtime |

If a library or module requires authority different from its host process, it
shall be moved behind a separate process/service isolation boundary.

### Keep the issuer outside the authorized workload

A **Platform Workload Credential Service** belongs to the platform trusted
computing base. It is outside every workload for which it issues credentials.
An updated component may contain only a client or protocol adapter; it may not
contain an unrestricted issuer or obtain the token-signing private key.

The Credential Service authenticates runtime evidence, reads authoritative
platform policy and current deployment state, and computes effective authority
as the intersection of:

```text
requested component capability
∩ OEM-approved capability
∩ capability supported by the active software contract
∩ capability allowed for the workload type
∩ current runtime and lifecycle state
```

The caller cannot widen this result, select its own artifact identity or
supply an authoritative permission document. An invalid, inactive, stale,
unverified or mismatched workload receives no token.

### Use local, short-lived and narrowly scoped tokens

For KUKSA, a platform-owned policy adapter issues short-lived tokens from a
protected per-device/Unit signer. KUKSA remains a generic unmodified resource
server that trusts the configured public verifier and enforces only claims
supported by the pinned implementation.

The token profile shall include, where supported by the resource server:

- a subject identifying the workload instance rather than only the artifact;
- a fixed KUKSA audience;
- not-before and expiration bounds;
- exact paths and operations;
- an instance/deployment generation and unique token identifier when useful;
- an issuer claim for audit and validation only where the resource server
  actually enforces it; and
- proof-of-possession/channel binding when supported and justified.

Private signing material stays in a platform-protected key facility. Workloads
receive no static token or reusable signing secret; tokens are retained only
in bounded runtime memory and renewed only after current identity and policy
are revalidated.

### Bind revocation to workload lifecycle

Stop, removal, update, rollback, deprovision or loss of authorization prevents
renewal immediately. Existing self-contained tokens expire within their short
bounded lifetime. A runtime-generation/authorization epoch, verifier change or
online introspection may provide faster invalidation where required, but the
first implementation shall not claim immediate JWT revocation without one of
those mechanisms.

The Credential Service and resource server are local to the vehicle/ECU so
that already authorized local operation and bounded renewal do not require
Cloud connectivity. Cloud policy and lifecycle decisions may synchronize when
connectivity exists but are not inserted into the local data/control path.

## Consequences for the KUKSA Case

- Telemetry publishers receive only exact `provide` scopes for existing
  contract paths; `create` is not granted unless an explicit qualified use case
  requires dynamic path creation.
- Functional consumers receive only exact `read` and narrowly accepted
  `actuate` scopes.
- Independent publisher, advisory-adapter and functional-service workloads use
  distinct subjects and permissions even when delivered in one release.
- KUKSA does not need to understand FOTA/SOTA, artifact signatures, active
  slots or Cloud lifecycle. Those facts are evaluated before token issuance.
- One compromised workload cannot mint credentials for itself or another
  workload merely because it can call KUKSA or inspect its own artifact.

## AosEdge Mapping Gate

This ADR does not assume which AosEdge facility establishes every workload
identity. Before `D4-010.2` is accepted, the project shall determine:

1. whether Aos IAM exposes a supported non-SOTA/FOTA workload-instance
   registration and invalidation lifecycle;
2. which runtime facts are authoritative for an active FOTA provider;
3. where the Platform Workload Credential Service and its KUKSA policy adapter
   reside in the OEM Factory/Platform lifecycle;
4. how SOTA, FOTA, system-service and future container principals use one
   model without sharing credentials; and
5. which current `VDP-owned Credential Broker` statements must be replaced or
   narrowed once that mapping is selected.

Until that mapping is accepted, this ADR is a binding security constraint but
does not close `D4-010.2` or authorize implementation of a project-specific
identity substitute.

### Current-demo scope resolution

For the first demo, [ADR 0013](0013-current-release-kuksa-authorization-compatibility.md)
applies this workload model to independently delivered Brake Health and Tire
Health SOTA instances through active Aos IAM authority and short-lived KUKSA
JWTs.

The VDP is instead accepted as part of the OEM-qualified trusted platform. Its
Provider-side KUKSA connectivity is fixed Platform Team integration delivered
through the signed, evidence-backed FOTA lifecycle. The demo does not add
dynamic Provider IAM/JWT, per-component attestation, or containment of a
malicious or substituted VDP. This closes the current-demo `D4-010.2` action by
an explicit scope and trust assumption; it does not prove or invalidate the
stricter technology-neutral model above. Any future scenario with third-party,
independently distrusted, or mutually isolated providers must reopen that
mapping and satisfy this ADR before claiming secure workload authorization.

## Rejected Alternatives

- Give a component artifact a long-lived token.
- Bake tokens or private keys into a Factory Image, container, FOTA or SOTA
  artifact.
- Let a workload self-declare its digest, identity or effective permissions.
- Place an unrestricted token issuer or signing key inside the component it
  authorizes.
- Give an in-process library authority independent of its host process without
  creating a separate isolation boundary.
- Depend on Cloud connectivity for every local authorization decision.

## Verification Implications

Qualification shall prove artifact-to-workload binding, instance separation,
scope intersection, wrong-digest/generation rejection, cross-workload and
cross-device rejection, short-lived renewal, stop/update/rollback invalidation,
offline operation and absence of reusable credentials in artifacts,
filesystems, process arguments, environments and logs.
