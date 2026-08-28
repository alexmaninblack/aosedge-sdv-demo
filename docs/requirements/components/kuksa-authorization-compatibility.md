<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current-Release KUKSA Authorization Compatibility 0.8

- Status: D3 design-reviewed
- Version: 0.8
- Prepared: 2026-08-22
- Accepted: 2026-08-28
- Owner: Platform Team
- Package: [`CR-KAC`](../component-decomposition-and-interface-register.md#cr-kac)
- Architecture input: [High-Level Architecture 1.5](../../architecture/high-level-architecture.md)
- Scenario input: [Demo Scenarios 2.0](../../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Architecture Flows 2.0](../../architecture/demo-scenario-architecture-flows.md)
- System requirements input: [System Requirements 2.0](../system-requirements-and-traceability.md)
- Accepted authority: [ADR 0013](../../architecture/decisions/0013-current-release-kuksa-authorization-compatibility.md)
- Implementation, build, signing, Cloud, or Unit mutation authorized: no

## Purpose and Boundary

`CMP-KAC` is the removable compatibility implementation of the permanent
platform-controlled Service credential boundary for the current AosCore
release. It enables independently deployed Brake Health and Tire Health SOTA
instances to obtain short-lived KUKSA JWTs from their active native Aos IAM
authority without changing upstream KUKSA and without placing an issuer inside
VDP or either functional Service.

The helper is separately packaged Platform Team infrastructure in the OEM Demo
Factory Image. It is outside the VDP FOTA payload, both SOTA payloads, analytics
logic and the runtime telemetry/advisory path. It owns no Service identity,
permission database, vehicle-data contract, Provider authority, Cloud state or
future native AosCore interface.

Provider-side KUKSA connectivity is a distinct OEM-trusted platform integration
assumption. `CMP-KAC` shall never issue, renew or imply KUKSA `provide` or
`create` authority for VDP.

## Accepted Deployment Boundary

[`D4-027.1`](../d4-decision-register.md#d4-027-1) freezes the current-release
deployment boundary:

- planned source: `aos-vehicle-platform/authorization/aos-kuksa-compat/`;
- separate Yocto recipe/package and systemd unit:
  `aos-kuksa-auth-compat` / `aos-kuksa-auth-compat.service`;
- dedicated unprivileged runtime identity: `aos-kac:aos-kac`;
- inactive before provisioning; after provisioning, require active
  `aos-iam.service` and successful protected-signer/public-verifier
  preparation before becoming ready;
- no VDP dependency, no public listener and no global hard dependency from
  `aos-sm.service`; only a KUKSA-consuming Service remains functionally
  `NOT_READY` while credential preparation is unavailable; and
- independently removable package boundary for later native AosCore migration.

The current source contains `aos-iam.service`, `aos-sm.service` and
`kuksa-databroker.service`, but no helper or verifier-preparation unit. Their
implementation remains future work and is not created by this document.

## Accepted Local Transport and Credential Delivery

[`D4-027.2`](../d4-decision-register.md#d4-027-2) freezes the current-release
Service-local transport:

- `CMP-KAC` listens only on
  `/run/aos-kuksa-auth-compat/request.sock`, owned by
  `aos-kac:aos-kuksa-clients` and mode `0660`;
- the platform-owned Aos named resource `kuksa-auth-client` grants only an
  approved KUKSA-enabled Service the socket-directory mount, supplementary
  group and container-private tmpfs `/run/aosedge/secrets/kuksa`;
- the compatibility bootstrap is the only process in the Service container
  that consumes `AOS_SECRET`; it uses the implicit fixed `kuksa` resource and
  executes the analytics application with that secret removed;
- Aos IAM `GetPermissions` remains authoritative; the named resource, group and
  Unix peer credentials are defense in depth;
- the bootstrap atomically maintains mode-`0400`
  `/run/aosedge/secrets/kuksa/token.jwt` and gives the analytics application
  only `KUKSA_TOKEN_FILE`; and
- stop, replacement, removal or reboot destroys the private tmpfs. No TCP
  listener, public port, shared host token directory or persisted JWT exists.

The exact JWT mapping, timing, signer/verifier preparation, trustworthy-time
behavior and operational bounds are accepted in D4-027.4 through D4-027.8.
D4-027 is complete.

## Accepted Local Exchange Protocol

[`D4-027.3`](../d4-decision-register.md#d4-027-3) and the
[machine-readable contract](../../../contracts/kuksa-current-demo-authorization/kuksa-auth-compat.v1.json)
freeze one strict protocol:

- `aos-kuksa-auth-compat/v1`, one LF-terminated UTF-8 JSON request and one
  response per Unix stream connection, followed by server close;
- request operation `status` with no credential, or `issue` with only opaque
  `aosSecret`; renewal repeats `issue`;
- implicit fixed resource `kuksa`, strict field allowlists and rejection of
  unknown/duplicate fields, trailing objects or caller-selected authority;
- success status `ready` or `issued`; `issued` carries only KAC-generated
  correlation, JWT, expiry and renewal timestamps;
- one `rejected` envelope with fixed non-secret code and `retryable`; and
- no free-text error, identity, permissions, path/mode details or caller-chosen
  correlation value.

## Accepted Permission and Timing Profile

[`D4-027.4`](../d4-decision-register.md#d4-027-4) and
[`D4-027.5`](../d4-decision-register.md#d4-027-5) freeze the executable Service
JWT profile:

- pinned `RS256`, issuer `aosedge-kuksa-auth-compat`, audience `kuksa.val` and
  IAM-derived Service-instance subject;
- exact leaf paths only, with IAM `r` mapped to KUKSA `read` and IAM `rw`
  mapped to KUKSA `actuate` because pinned KUKSA `actuate` includes read;
- IAM `w`, unknown modes, wildcards, partial trimming, `provide` and `create`
  reject the complete Service issuance;
- TTL 300 seconds, renewal at 180 seconds and a 120-second bounded recovery
  reserve;
- a fresh IAM lookup for every renewal, atomic token replacement and mandatory
  Service reconnect/subscription recreation with the new JWT; and
- immediate cooperative disconnect on terminal denial, retryable use only
  until signed expiry for transient failure, no instant-revocation claim and
  no Cloud dependency in renewal.

## Accepted Per-Unit Signer and Verifier Preparation

[`D4-027.6`](../d4-decision-register.md#d4-027-6) materializes the accepted
D4-010.1 lifecycle for the current compatibility helper:

- provisioning creates one Unit-unique protected `kuksa-jwt` RSA key pair;
  private-key bytes never leave PKCS#11 and no file-key fallback exists;
- `aos-kuksa-verifier-prepare.service` performs a protected sign/verify
  self-test and atomically publishes only the public key as root-owned
  mode-`0444` `/run/aos-kuksa-verifier/kuksa-jwt-public.pem`;
- unmodified KUKSA always starts with that exact file through
  `--jwt-public-key`, while KUKSA and `CMP-KAC` both fail closed when
  preparation is absent, malformed or unverifiable;
- `CMP-KAC` invokes only the protected `RS256` sign operation and cannot
  export the private key;
- reboot recreates the volatile verifier from the existing Unit key and starts
  the helper with empty state; KUKSA restart is required to load a verifier;
  and
- VU and PU fingerprints differ, cross-Unit JWTs fail, live rotation is
  deferred, and R0 retires the key by discarding the provisioned overlay after
  Cloud reconciliation.

## Accepted Trustworthy-Time Boundary

[`D4-027.7`](../d4-decision-register.md#d4-027-7) freezes the time source and
clock-discontinuity behavior:

- each boot requires one successful `systemd-timesyncd` NTP synchronization
  and a 10-second stable window before authorization becomes ready;
- JWT epoch claims use UTC `CLOCK_REALTIME`; renewal and retry scheduling use
  `CLOCK_BOOTTIME`;
- a current-boot-ID-bound mode-`0600` anchor at
  `/run/aos-kuksa-auth-compat/time-anchor.json` survives helper process restart
  but never VM reboot;
- normal loss of external connectivity after synchronization does not revoke
  time trust or require continuous NTP, Cloud or backend access;
- more than five seconds of wall/boot-clock deviation yields
  `TIME_UNTRUSTED`, blocks issue/renew, stops KUKSA and makes bootstraps
  disconnect and delete private tokens; and
- recovery requires another NTP sync and stable window, KUKSA restart and
  fresh JWTs. A cold offline boot remains `NOT_READY` without blocking
  unrelated AosCore services.

## Accepted Operational Envelope

[`D4-027.8`](../d4-decision-register.md#d4-027-8) freezes the remaining helper
bounds:

- maximum request/response/JWT sizes are 16/32/16 KiB, with at most 64 exact
  permissions and 512 bytes per VSS path;
- four concurrent requests, backlog eight, per-peer 12/minute with burst four,
  and global 30/minute with burst ten;
- request/IAM/sign/whole-request deadlines of 2/3/3/8 seconds;
- retry backoff 1/2/4/8/16/30 seconds with ±20% jitter, never beyond current
  JWT expiry;
- `IAM_UNAVAILABLE`, `SIGNER_UNAVAILABLE`, `TIME_UNTRUSTED` and `BUSY` are
  retryable; the other four fixed codes are non-retryable;
- systemd bounds of 64 MiB, 10% CPU, 32 tasks and 128 descriptors, with only
  `AF_UNIX`, no ambient capabilities or TCP/IP, `NoNewPrivileges`, strict
  system protection and private temporary storage; and
- fixed low-cardinality diagnostics only. Secret, JWT, permission/path/claim,
  signing/key and raw-frame content is forbidden.

## Context and Interface Summary

| Interface | Direction | Required behavior |
| --- | --- | --- |
| [`IF-AUTH-007`](../component-decomposition-and-interface-register.md#if-auth-007) | Service bootstrap → `CMP-KAC` | Named-resource-mounted private Unix socket; instance-bound `AOS_SECRET`; implicit fixed `kuksa` resource; no caller-selected authority |
| [`IF-AUTH-008`](../component-decomposition-and-interface-register.md#if-auth-008) | `CMP-KAC` → Aos IAM | Native `GetPermissions` lookup against current active Service state |
| [`IF-AUTH-009`](../component-decomposition-and-interface-register.md#if-auth-009) | `CMP-KAC` → requesting Service instance | Same-connection rejection or short-lived JWT; bootstrap atomically maintains a private tmpfs token file |
| [`IF-AUTH-010`](../component-decomposition-and-interface-register.md#if-auth-010) | Factory/Aos security substrate → `CMP-KAC` and KUKSA | Permission-handler availability, protected signing, atomic verifier preparation and fail-closed lifecycle |

After successful preparation, the Service connects directly to KUKSA over its
normal KUKSA data/advisory interfaces. `CMP-KAC` is not a network proxy and does
not observe Service telemetry, analytics results or advisory payloads.

## Component Requirements

### <a id="req-kac-001"></a>`REQ-KAC-001` — Separate removable platform package

- Statement: The current-release helper shall be packaged and lifecycle-managed
  as the separate `aos-kuksa-auth-compat` factory package and
  `aos-kuksa-auth-compat.service`, outside VDP, Brake Health and Tire Health
  payloads. It shall run as dedicated unprivileged `aos-kac:aos-kac`, start
  with no active Service authority only after provisioning, active Aos IAM and
  successful `aos-kuksa-verifier-prepare.service`, and remain removable without
  changing the permanent KUKSA or Service permission model after a released
  native AosCore contract is qualified. It shall have no VDP dependency,
  public listener, root fallback or global `aos-sm.service` hard dependency.
- Parents: [`SYS-MFG-002`](../system-requirements-and-traceability.md#sys-mfg-002),
  [`SYS-SEC-008`](../system-requirements-and-traceability.md#sys-sec-008)
- Flow: [`AF-M0-LC`](../../architecture/demo-scenario-architecture-flows.md#af-m0-lc),
  [`AF-X-AUTH`](../../architecture/demo-scenario-architecture-flows.md#af-x-auth)
- Verification: Inspection, component, integration

### <a id="req-kac-002"></a>`REQ-KAC-002` — Fixed-resource request and caller isolation

- Statement: The helper shall accept only one strict
  `aos-kuksa-auth-compat/v1` request per connection on
  `/run/aos-kuksa-auth-compat/request.sock` from a peer admitted through the
  platform-owned `kuksa-auth-client` resource and `aos-kuksa-clients` group.
  The bootstrap may submit `status`, or `issue` with only the current instance
  `AOS_SECRET`; resource `kuksa` is implicit and fixed by the endpoint. The
  helper shall reject unknown/duplicate fields, extra frames and any request or
  peer that attempts to select identity, paths, modes, subject, audience, TTL,
  claims, signing input, correlation value or another instance's response.
  Unix peer credentials and named-resource admission are defense in depth;
  native Aos IAM remains authoritative.
- Parents: [`SYS-SEC-001`](../system-requirements-and-traceability.md#sys-sec-001),
  [`SYS-SEC-008`](../system-requirements-and-traceability.md#sys-sec-008)
- Interface: [`IF-AUTH-007`](../component-decomposition-and-interface-register.md#if-auth-007)
- Verification: Unit, contract, integration, security-negative

### <a id="req-kac-003"></a>`REQ-KAC-003` — Current Aos IAM authority only

- Statement: For every issuance or renewal attempt, the helper shall call native
  Aos IAM `GetPermissions` with the presented instance credential and fixed
  resource and shall treat only that current result as authoritative. It shall
  store no parallel Service identity, allowlist, permission database or
  caller-supplied policy.
- Parent: [`SYS-SEC-008`](../system-requirements-and-traceability.md#sys-sec-008)
- Interface: [`IF-AUTH-008`](../component-decomposition-and-interface-register.md#if-auth-008)
- Verification: Unit, contract, integration

### <a id="req-kac-004"></a>`REQ-KAC-004` — Pinned JWT derivation

- Statement: The helper shall translate only supported active IAM paths and
  modes into the pinned KUKSA JWT profile: exact mode `r` becomes
  `read:<path>`, exact mode `rw` becomes `actuate:<path>`, and mode `w` is
  unsupported because KUKSA actuation includes read. The helper shall use
  `RS256`, fixed issuer `aosedge-kuksa-auth-compat`, fixed audience
  `kuksa.val`, IAM-derived Service-instance subject and required `sub`, `iss`,
  `aud`, `iat`, `exp` and `scope` claims. Wildcards, `provide`, `create`,
  unknown modes, malformed paths, unsupported or broadened permissions, wrong
  Unit, invalid/stale secret, missing/unverified per-Unit signer/verifier or
  untrustworthy time
  shall reject the complete exchange without partial trimming or fallback
  credentials.
- Parents: [`SYS-SEC-004`](../system-requirements-and-traceability.md#sys-sec-004),
  [`SYS-SEC-008`](../system-requirements-and-traceability.md#sys-sec-008)
- Interfaces: [`IF-AUTH-008`](../component-decomposition-and-interface-register.md#if-auth-008),
  [`IF-AUTH-010`](../component-decomposition-and-interface-register.md#if-auth-010)
- Verification: Unit, contract, integration, security-negative

### <a id="req-kac-005"></a>`REQ-KAC-005` — Private volatile delivery and direct KUKSA use

- Statement: The helper shall expose either a bounded factual rejection or the
  short-lived JWT only on the requesting socket connection using the strict
  D4-027.3 schemas. `ready` describes technical substrate readiness only;
  `issued` carries a KAC-generated correlation ID, JWT, expiry and renewal
  timestamps; `rejected` carries only a KAC-generated correlation ID, fixed
  code and retryability. The Service
  bootstrap shall atomically maintain that JWT as mode-`0400`
  `/run/aosedge/secrets/kuksa/token.jwt` inside the Service-private mode-`0700`
  tmpfs, expose only `KUKSA_TOKEN_FILE` to the analytics application and
  execute that application without `AOS_SECRET`. The helper shall not persist
  the JWT or remain in the subsequent Service-to-KUKSA telemetry/advisory data
  path.
- Parent: [`SYS-SEC-008`](../system-requirements-and-traceability.md#sys-sec-008)
- Interface: [`IF-AUTH-009`](../component-decomposition-and-interface-register.md#if-auth-009)
- Verification: Unit, inspection, integration, cross-Service negative

### <a id="req-kac-006"></a>`REQ-KAC-006` — Renewal and failure behavior

- Statement: Renewal shall repeat the same fixed-resource IAM lookup before a
  fixed refresh point by sending `issue` again; no separate renewal operation
  exists. Each JWT shall expire 300 seconds after `iat`; renewal shall begin
  180 seconds after issue, preserving a 120-second recovery reserve. Success
  shall atomically replace the private token and cause the Service to reconnect
  and recreate KUKSA subscriptions with the replacement JWT. A transient
  failure may retry with the current token only until expiry; expiry deletes
  the token, disconnects KUKSA and makes the Service functionally `NOT_READY`.
  Terminal `DENIED` or `POLICY_UNSUPPORTED` shall delete and disconnect
  immediately. An already issued self-contained JWT may remain cryptographically
  usable only until signed expiry; no instant-revocation claim is allowed and
  renewal shall require no Cloud connection. JWT epoch claims shall use trusted
  UTC `CLOCK_REALTIME`, while renewal/retry scheduling shall use
  `CLOCK_BOOTTIME`; a clock discontinuity shall follow D4-027.7 and shall never
  extend the accepted lifetime. Retryable failures shall use the accepted
  1/2/4/8/16/30-second backoff with ±20% jitter and shall never retry beyond
  the current JWT's `exp`; terminal codes shall not retry.
- Parents: [`SYS-SEC-004`](../system-requirements-and-traceability.md#sys-sec-004),
  [`SYS-SEC-008`](../system-requirements-and-traceability.md#sys-sec-008)
- Verification: Unit with controlled clock, component, integration

### <a id="req-kac-007"></a>`REQ-KAC-007` — Reboot, stop, unregistration and removal

- Statement: VM reboot shall delete volatile helper/JWT state and reconstruct
  the root-owned public verifier from the existing protected Unit key before
  restarting KUKSA and the empty helper, then reconstruct authority only from
  active Service Manager and Aos IAM state. Service stop,
  container replacement, removal or unregistration shall destroy the private
  tmpfs/token and prevent issuance or renewal. Restart shall request a new
  credential rather than recover a persisted token. R0 overlay disposal shall
  destroy all current-run helper state and Unit-specific signing material
  without modifying the Factory Image. A boot-local time anchor may restore a
  helper process in the same boot but shall not cross VM reboot; a cold offline
  boot remains authorization `NOT_READY` until time synchronization succeeds.
- Parents: [`SYS-SEC-008`](../system-requirements-and-traceability.md#sys-sec-008),
  [`SYS-RET-001`](../system-requirements-and-traceability.md#sys-ret-001),
  [`SYS-RET-005`](../system-requirements-and-traceability.md#sys-ret-005)
- Flow: [`AF-X-AUTH`](../../architecture/demo-scenario-architecture-flows.md#af-x-auth),
  [`AF-R0-LC`](../../architecture/demo-scenario-architecture-flows.md#af-r0-lc)
- Verification: Unit, component, integration, end-to-end

### <a id="req-kac-008"></a>`REQ-KAC-008` — Offline-local operation

- Statement: Loss of the Unit's external connections to AosCloud and functional
  backends shall not disable local IAM lookup, bounded renewal or direct
  authorized Service-to-KUKSA operation while the Service instance remains
  active and trustworthy time was established earlier in the same boot. Loss
  of fresh NTP packets after that gate shall not revoke trust by itself. The
  helper shall require no Cloud round trip in the local credential path.
- Parents: [`SYS-SEC-008`](../system-requirements-and-traceability.md#sys-sec-008),
  [`SYS-OBS-007`](../system-requirements-and-traceability.md#sys-obs-007)
- Flow: [`AF-X-OFFLINE`](../../architecture/demo-scenario-architecture-flows.md#af-x-offline)
- Verification: Integration, end-to-end demonstration

### <a id="req-kac-009"></a>`REQ-KAC-009` — Bounds and redaction

- Statement: The helper shall enforce bounded request size, concurrency, rate,
  queueing, response size, timeout and resource use using the exact D4-027.8
  16/32/16-KiB frame/response/JWT, 64-permission, 512-byte-path,
  four-concurrent/eight-backlog, 12/30-per-minute and 2/3/3/8-second limits. It
  shall run within 64 MiB, 10% CPU, 32 tasks and 128 descriptors with only
  `AF_UNIX`; fail closed under excess;
  strictly reject invalid UTF-8, unknown or duplicate fields and trailing
  objects; emit no free-text protocol diagnostics;
  and never expose `AOS_SECRET`, JWT, private key, signing input or full
  permission content in logs, metrics, errors, process arguments, command lines
  or retained demo evidence.
- Parents: [`SYS-SEC-008`](../system-requirements-and-traceability.md#sys-sec-008),
  [`SYS-OBS-003`](../system-requirements-and-traceability.md#sys-obs-003)
- Verification: Unit, inspection, resource-negative, log scan

### <a id="req-kac-010"></a>`REQ-KAC-010` — Native-migration deletion seam

- Statement: Helper-specific transport, package/startup wiring, signer/verifier
  compatibility configuration and Service bootstrap adaptation shall be
  isolated behind versioned boundaries so a released native AosCore credential
  contract can replace and delete them after the same authorization and
  negative acceptance suite passes. No provisional native API is part of this
  requirement.
- Parent: [`SYS-SEC-008`](../system-requirements-and-traceability.md#sys-sec-008)
- Verification: Architecture inspection, component dependency inspection,
  future migration qualification

## Required Unit-Test Obligations

| ID | Requirement coverage | Required isolated proof |
| --- | --- | --- |
| <a id="ut-kac-001"></a>`UT-KAC-001` | `REQ-KAC-002` | Accept exact `status`/`issue` schemas only from an admitted Unix-socket peer; `issue` carries only current `AOS_SECRET` and implicit fixed `kuksa`; reject unknown/duplicate fields, extra frames, caller-selected authority, unauthorized group/resource access and cross-peer response access |
| <a id="ut-kac-002"></a>`UT-KAC-002` | `REQ-KAC-003` | Invoke IAM on every issue/renew path; reject invalid, stale, inactive and unavailable results; prove no retained policy source |
| <a id="ut-kac-003"></a>`UT-KAC-003` | `REQ-KAC-004` | Exact `r -> read` and `rw -> actuate` mapping; reject `w`, wildcard, `provide`, `create`, malformed, unsupported or broadened authority as one complete transaction; prove pinned claims |
| <a id="ut-kac-004"></a>`UT-KAC-004` | `REQ-KAC-005` | Exact `ready`/`issued`/`rejected` envelopes, KAC-generated correlation, same-connection delivery, atomic mode-`0400` token replacement in private tmpfs, scrubbed analytics environment, cross-Service denial and absence from the direct Service-to-KUKSA path |
| <a id="ut-kac-005"></a>`UT-KAC-005` | `REQ-KAC-006`, `REQ-KAC-008` | Controlled UTC/boottime clocks, per-boot NTP gate, 10-second stable window, 300-second lifetime, renewal at 180 seconds, 120-second reserve, fresh IAM lookup, atomic replace plus reconnect/subscription recreation, ordinary offline continuation, ±5-second boundary and larger forward/backward discontinuity fail-closed behavior |
| <a id="ut-kac-006"></a>`UT-KAC-006` | `REQ-KAC-007`, `REQ-KAC-008` | Same-boot helper restart from matching boot-local anchor, boot-ID mismatch, empty VM reboot, online reconstruction, cold offline `NOT_READY`, stop/replace/unregister/remove denial, tmpfs deletion and no persisted-token recovery |
| <a id="ut-kac-007"></a>`UT-KAC-007` | `REQ-KAC-001`, `REQ-KAC-004`, `REQ-KAC-007` | Protected sign/verify preparation publishes only the atomic mode-`0444` public verifier; missing/malformed verifier blocks KUKSA and helper; no private/file-key fallback exists; reboot reconstructs the verifier; wrong Unit/verifier/signing context rejects and fresh provisioning uses distinct trust state |
| <a id="ut-kac-008"></a>`UT-KAC-008` | `REQ-KAC-008` | Cloud/backend reachability is absent from local authorization dependencies |
| <a id="ut-kac-009"></a>`UT-KAC-009` | `REQ-KAC-006`, `REQ-KAC-009` | Exact frame/JWT/permission/path boundaries ±1, four-concurrent/eight-backlog and per-peer/global token-bucket boundaries, every 2/3/3/8-second timeout, retry schedule/jitter/expiry cutoff, 64-MiB/10%-CPU/32-task/128-FD limits, invalid UTF-8/JSON/duplicate/unknown/trailing frames and every retryable/non-retryable mapping fail closed; only fixed low-cardinality codes/correlation are emitted and diagnostic output is fully redacted |
| <a id="ut-kac-010"></a>`UT-KAC-010` | `REQ-KAC-001`, `REQ-KAC-010` | Packaging/dependency inspection proves the exact package/unit/user boundary, no VDP/SOTA business-code ownership, no root/public-listener/global-Service-Manager dependency and one removable native-migration seam |

Unit tests use fake IAM, protected-signer and clock adapters plus private
temporary credential locations. They do not unit-test external AosCore or
KUKSA implementation. Real IAM registration, PKCS#11 signing, KUKSA verifier,
cross-Service/Unit isolation, reboot and offline behavior remain contract,
integration and end-to-end obligations.

## Verification Allocation

| Level | Required proof |
| --- | --- |
| Unit | Pure request validation, IAM result mapping, JWT profile, lifecycle state machine, bounds and redaction |
| Component | Process/package isolation, private credential location, startup/readiness, empty restart and teardown |
| Contract | `IF-AUTH-007`–`010` schemas, errors, pinned JWT fixtures, permissions and lifecycle cases |
| Integration | Real Service Manager/IAM, per-Unit signer/verifier, unmodified KUKSA, two independent SOTA instances and direct Service access |
| End-to-end | VU before PU, restart/reboot, stop/removal, targeted vehicle offline operation, R0 destruction and fresh next-run authority |

## Open D4 Gates

[`D4-027.1`](../d4-decision-register.md#d4-027-1) closes process ownership,
package layout and top-level startup ordering. [`D4-027.2`](../d4-decision-register.md#d4-027-2)
closes local Unix-socket placement, named-resource isolation, Service-private
tmpfs delivery and bootstrap secret separation. [`D4-027.3`](../d4-decision-register.md#d4-027-3)
closes request/response/rejection/readiness schemas and fixed error semantics.
D4-027.4 through D4-027.8 close permission translation, JWT timing,
signer/verifier preparation, trustworthy time and all operational bounds. No
D4-027 subdecision remains. Source implementation, image build or Unit
mutation still requires the active change plan and remaining cross-package D4
gates.

Provider dynamic authorization is not an open D4 gate for the first demo. The
VDP remains an OEM-qualified trusted platform component, Service credentials
cannot grant provider authority, and malicious/substituted-Provider containment
is outside the accepted claim.

## Review Record for Version 0.8

Version 0.8 incorporates D4-027.8 and contract profile 1.4.0: exact size,
permission/path, concurrency, backlog, rate, timeout, retry, systemd resource
and redaction bounds. D4-027 is complete. Version 0.8 was design-reviewed on
2026-08-28 and is the current architectural requirement baseline;
implementation has not begun.

## Review Record for Version 0.7

Version 0.7 incorporates D4-027.7 and contract profile 1.3.0: one NTP sync and
10-second stable window per boot, UTC claims plus boottime scheduling,
same-boot anchor recovery, ordinary offline continuation, five-second
discontinuity threshold, fail-closed KUKSA/token handling and cold-offline
`NOT_READY`. At that version operational bounds were the final open D4-027
gate.

## Review Record for Version 0.6

Version 0.6 incorporates D4-027.6 and contract profile 1.2.0: one protected
per-Unit RSA key, exact preparation unit and volatile public-verifier path,
protected sign/verify self-test, mandatory KUKSA `--jwt-public-key`, fail-closed
startup, reboot reconstruction, cross-Unit rejection and R0 retirement. At
that version trustworthy-time behavior and operational bounds remained open.

## Review Record for Version 0.5

Version 0.5 incorporates accepted D4-027.4/.5 and contract profile 1.1.0:
exact non-widening `r`/`rw` mapping, rejection of `w` and provider actions,
fixed JWT claims, 300-second TTL, renewal at 180 seconds, a 120-second reserve,
fresh-IAM renewal and mandatory KUKSA reconnect/subscription recreation. At
that version signer and trusted-time preparation plus operational bounds
remained open.

## Review Record for Version 0.4

Version 0.4 incorporates accepted `D4-027.3` and its machine-readable schemas:
strict one-request/one-response JSON framing, `status`/`issue`, implicit
resource `kuksa`, `ready`/`issued`/`rejected`, fixed error codes, KAC-generated
correlation and no free-text or caller-selected authority. At that version JWT
mapping/timing, signer preparation and operational bounds remained open.

## Review Record for Version 0.3

Version 0.3 incorporates accepted `D4-027.2`: a private host Unix socket,
platform-owned named-resource mount/group admission, authoritative IAM lookup,
bootstrap-only `AOS_SECRET` use, atomic mode-`0400` JWT delivery in a
Service-private tmpfs and deletion on stop/replacement/removal/reboot. Exact
wire schemas, JWT profile/timing, signer preparation and bounds remain open.

## Review Record for Version 0.2

Version 0.2 incorporates accepted `D4-027.1`: exact repository/package/unit
and process identity, provisioning/IAM/signer startup boundary, absence of VDP
and global Service Manager dependencies, least-privilege fail-closed rule and
independent native-migration removal boundary. Exact transport, schemas, JWT,
timing, signer preparation and resource bounds remain open. This version
authorizes no source or image change.

## Review Record for Version 0.1

Version 0.1 creates the transitional package required by HLA 1.5 and ADR 0013.
It allocates current-release Service authorization behavior outside VDP and
both SOTA products, defines ten stable component requirements and ten isolated
unit-test obligations, and preserves unmodified KUKSA plus direct Service data
paths. Review and acceptance remain pending; this package authorizes no
implementation or external operation.
