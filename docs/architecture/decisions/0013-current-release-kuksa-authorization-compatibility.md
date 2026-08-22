<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0013: Use a Removable Current-Release KUKSA Authorization Compatibility Layer

- Status: Proposed
- Date: 2026-08-22
- Change class: C — authority, trust boundary, component ownership and interfaces
- Supersedes on acceptance: [ADR 0010](0010-aos-kuksa-credential-broker.md)
- Security input: [ADR 0012](0012-authorize-running-workloads-not-software-artifacts.md)
- Execution plan: [KUKSA JWT current-release change plan](../../planning/active/kuksa-jwt-current-release-change-plan.md)

## Context

The accepted baseline assigns a thin Aos–KUKSA Credential Broker to the
Vehicle Data Platform Component (VDP). That broker authenticates SOTA Service
instances through Aos IAM, translates permissions and issues KUKSA JWTs.

Current AosCore does provide a native SOTA permission lifecycle:

1. Service Manager reads immutable Service item metadata;
2. it registers the active Service instance and permissions with Aos IAM;
3. Aos IAM returns an opaque per-instance `AOS_SECRET`;
4. Service Manager injects that secret into the Service container; and
5. a functional server can resolve the active instance and registered
   permissions with `GetPermissions(AOS_SECRET, functional_server_id)`.

`AOS_SECRET` is not a JWT and Eclipse KUKSA does not accept it. The current
AosCore release does not prepare, inject, rotate or renew a KUKSA JWT for a
Service. The AosCore Platform Team intends to provide native JWT delivery in a
future release, but its file path, API, rotation behavior, JWT profile and
release contract are not yet released or frozen.

The demo must progress on the current release. At the same time, temporary
credential authority must not become permanent VDP product logic, Brake/Tire
analytics logic or a guessed imitation of the future native AosCore contract.

## Decision

### Keep the permanent architecture implementation-neutral

The permanent trusted-platform boundary shall:

- derive Service authority from immutable, OEM-approved Service metadata and
  active workload state;
- prepare a Service credential outside untrusted application logic;
- expose that credential through a platform-controlled mechanism;
- renew or replace it without allowing the Service to select its own
  authority; and
- leave unmodified Eclipse KUKSA as the final enforcement point for supported
  paths and operations.

The target HLA shall not predict the future native AosCore API, credential
path, transport, token lifetime, rotation mechanism or internal component
decomposition.

### Introduce a transitional current-release helper

The current demo shall introduce a separately identifiable transitional
logical component:

- ID: `CMP-KAC`;
- name: **Current-Release KUKSA Authorization Compatibility Helper**;
- lifecycle owner: OEM Platform Team / demo platform integration;
- lifecycle state: `TRANSITIONAL`; and
- removal trigger: accepted migration to released native AosCore KUKSA JWT
  delivery.

`CMP-KAC` is packaged as current-release factory/system integration. It is not
part of the VDP FOTA artifact and is not part of either SOTA Service artifact.
The target HLA shows it only as a visually subordinate current-release overlay,
not as a permanent vehicle-data capability.

### Use current native Aos IAM authority without delegating policy to callers

For each active SOTA Service instance:

1. a narrow compatibility bootstrap reads the native `AOS_SECRET` injected by
   the current Service Manager;
2. the bootstrap presents only that secret and a fixed KUKSA functional-server
   resource identifier to `CMP-KAC`;
3. `CMP-KAC` calls Aos IAM `GetPermissions`;
4. it validates and maps the authenticated instance's registered permissions
   to the exact claims supported by the pinned KUKSA release;
5. it derives the issuer-controlled audience, lifetime and remaining claims;
6. it issues a bounded short-lived JWT using Unit-local protected signing
   material; and
7. it makes the JWT available through a Service-private volatile credential
   location.

The Service may not supply authoritative paths, operations, subject, audience,
TTL, claims or signing payload. Unknown, stale, unregistered, malformed or
unsupported authority fails closed. Secrets, JWTs and private key material are
never written to demo evidence or logs.

After credential preparation, Brake Health and Tire Health connect directly
to KUKSA. Aos IAM and `CMP-KAC` do not enter the telemetry, analytics, advisory
or Cloud-data path.

### Bind credentials to the active Service lifecycle

The helper may renew a credential only while the Service instance remains
active and registered. Service stop, removal or unregistration prevents new
issuance and renewal; an already issued self-contained JWT expires within its
bounded lifetime.

D4-027.4/.5 fix that boundary for the current demo: IAM `r` maps only to
KUKSA `read`, IAM `rw` only to KUKSA `actuate`, and IAM `w`, wildcard or
provider authority fails closed. JWT lifetime is 300 seconds and renewal starts
at 180 seconds through a fresh IAM lookup. Replacement requires the Service to
reconnect and recreate KUKSA subscriptions; terminal denial disconnects the
cooperating Service immediately, while no instant cryptographic revocation is
claimed for a previously issued token before its signed expiry.

VM reboot does not restore an authorization cache as authoritative state. The
helper restarts empty and reconstructs authority from current Service Manager
and Aos IAM state. Already authorized local operation may continue without
Unit-to-Cloud connectivity within the accepted credential lifetime and renewal
model, but no Cloud connection is required in the local data path.

### Treat the VDP Provider as trusted OEM platform integration

The VDP remains responsible for VISS ingestion, validation, normalization,
signal selection, KUKSA Provider behavior and the typed outbound QM advisory
path. It does not issue Service JWTs.

For the first demo, the VDP is part of the OEM-qualified trusted platform. Its
provider-side KUKSA `provide/create` access is fixed platform integration
delivered and validated through the Platform Team's signed, evidence-backed
FOTA lifecycle. The project adds no dynamic Provider IAM/JWT exchange,
per-component attestation, or isolation between untrusted providers. Any
required fixed credential, protected local endpoint, or equivalent KUKSA
configuration remains an implementation detail of that trusted platform path,
not a second authorization architecture.

Service JWTs never grant provider authority. The versioned VDP contract,
signal validation, outbound allowlist and authoritative Vehicle Gateway policy
remain in force, but the demo does not claim containment of a malicious or
substituted VDP. C3 retires `IF-AUTH-006`, `SYS-SEC-005` and `REQ-VDP-008` as
dynamic Provider-authorization obligations; C4 records `D4-010.2` as closed by
this explicit trust assumption rather than by a new credential mechanism.

### Migrate only to a released native contract

When native AosCore KUKSA JWT delivery is released, the project shall inspect
the actual implementation and contract before documenting a migration. The
project shall then:

1. map the released native lifecycle and credential interface;
2. adapt the Service integration layer to the real contract;
3. run the current authorization, isolation, restart, offline and negative
   acceptance suite;
4. remove `CMP-KAC`, its startup/package wiring and compatibility-only
   signer/verifier material; and
5. remove the compatibility overlay from the active architecture.

Source adaptation is allowed. This ADR does not promise a drop-in migration
and does not invent a provisional native API.

## Consequences

- Current demo work can proceed without waiting for a future AosCore release.
- The VDP returns to a vehicle-data-only responsibility and independent FOTA
  lifecycle.
- Brake Health and Tire Health keep credential integration outside their
  analytics logic.
- A temporary trusted component is added to the OEM Demo Factory Image and
  must receive explicit requirements, contracts, tests and retirement
  evidence.
- D4-027 is fully frozen. D4-027.2 has
  frozen the local Unix-socket, named-resource and private-tmpfs boundary;
  D4-027.3 the strict wire schemas; D4-027.4 the permission/JWT profile; and
  D4-027.5 the 300/180-second lifetime and renewal boundary; and D4-027.6 the
  protected per-Unit signer, exact verifier-preparation service/runtime path,
  mandatory KUKSA verifier argument and fail-closed reboot lifecycle; and
  D4-027.7 the one-sync-per-boot trustworthy-time gate, UTC/boottime split,
  ordinary offline continuation and clock-discontinuity recovery; and
  D4-027.8 the exact frame, permission/path/JWT, concurrency, backlog, rate,
  timeout, retry, process-resource and redaction envelope.
- The architecture remains compatible with native platform evolution without
  claiming that compatibility will require no Service changes.

## Rejected Alternatives

- Keep a permanent Credential Broker inside the VDP.
- Let each Service translate permissions, construct claims or access signing
  keys.
- Let the caller request arbitrary KUKSA paths or operations during token
  exchange.
- Fork or modify Eclipse KUKSA to understand Aos-specific secrets.
- Guess and emulate the future native AosCore mounted-file contract.
- Wait for the future platform release before progressing with the demo.

## Open Detailed-Design Gates

This proposed ADR does not authorize implementation. The active change plan
and D4 must still freeze:

- executable evidence that the Provider path remains fixed OEM-trusted
  platform integration and cannot be obtained through a Service JWT.

Accepted D4-027.1 through D4-027.8 inputs are not open gates: the helper is a
separate unprivileged removable package; approved Services reach only its
private Unix socket through a platform-owned named resource; the compatibility
bootstrap alone reads `AOS_SECRET`; and the JWT exists only in that Service's
private volatile tmpfs. The strict versioned protocol exposes only `status`,
`issue`, fixed response/error enums and KAC-generated correlation. IAM modes
map only as `r -> read` and `rw -> actuate`; JWTs live 300 seconds, renew at
180 seconds and require KUKSA reconnect/subscription recreation.

## Acceptance Conditions

This ADR may become `Accepted` only when the complete class-C documentation
cascade agrees on the boundary, every retired identifier links to a successor,
the current-release executable contracts exist, documentation tests pass and
the reader-visible HLA clearly distinguishes the permanent model from the
temporary compatibility overlay.

Acceptance of this ADR does not authorize source implementation, image builds,
artifact signing, provisioning, deprovisioning or Cloud mutation.
