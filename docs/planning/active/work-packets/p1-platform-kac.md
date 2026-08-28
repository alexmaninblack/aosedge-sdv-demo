<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Platform KUKSA Authorization Compatibility Work Packet

- ID: `WP-P1-PLATFORM-KAC-001`
- Lane: `L-PLATFORM`
- Increment: `IMP-03-KAC`
- Review state: `ACCEPTED — AUTHORIZED`
- Version: 0.1
- Prepared: 2026-08-28
- Accepted: 2026-08-28
- Authorized: 2026-08-28
- Implementation authorized: yes — only the bounded source scope in this packet
- Image build, VM, provisioning, signing, FOTA and live qualification authorized: no
- Parent plan: [Demo Implementation Plan 1.2](../demo-implementation-plan.md)
- Readiness input: [WP-P0-PLATFORM-001 0.12](p0-platform-readiness.md)
- Requirements input: [CR-KAC 0.12](../../../requirements/components/kuksa-authorization-compatibility.md),
  SHA-256
  `ab0d6bf039d94d52b82ff77c6bcf74ffe397f9f2b6110f8be032ed07198c3e39`
- Executable contract: [KUKSA current-demo authorization 1.7.0](../../../../contracts/kuksa-current-demo-authorization/kuksa-auth-compat.v1.json),
  SHA-256
  `1ddd097976dc8606533307bf2f0f0619b166a295a38391e593340487b8d2931c`

## Outcome

Implement the separately packaged, deliberately removable current-release
KUKSA authorization compatibility helper. It translates the current active
Aos IAM permission decision for one SOTA Service instance into one bounded
short-lived KUKSA Service JWT without changing upstream AosCore or KUKSA and
without entering the subsequent Service-to-KUKSA data path.

KAC is not part of VDP, a telemetry proxy, a permission database, a Provider
credential endpoint or functional analytics. The future native AosCore
replacement must satisfy the same contract and negative qualification before
this package is deleted.

## Repository and Isolation

| Item | Frozen value |
| --- | --- |
| Repository | `aos-vehicle-platform` |
| Base revision | `bdc72aba97a83c9868d454588189ef139710a6d7` |
| Required base relationship | clean `main`, equal to `origin/main` at authorization |
| Branch | `codex/imp-03-kac` |
| Isolated worktree | sibling path `../aos-vehicle-platform-imp-03-kac` |
| Dependency repositories | `aosedge-sdv-demo` contracts and pinned AosEdge sources, read-only |

## Writable Boundary

Only these owned boundaries may change:

- `authorization/aos-kuksa-compat/**` for C++ source, build files, fakes,
  package-owned unit/contract/security tests and component documentation;
- a new
  `meta-aos-vehicle-platform/recipes-aos/aos-kuksa-auth-compat/**` recipe,
  systemd units, tmpfiles and KUKSA verifier-startup drop-in;
- KAC-specific files under
  `meta-aos-vehicle-platform/recipes-security/refpolicy/files/` and only the
  minimum corresponding entries in `refpolicy-aos_git.bbappend`;
- package-owned `tools/validate_kac.py` and `tests/test_kac.py`; and
- `docs/architecture.md` and `docs/contract-compatibility.md` only where
  factual implementation wording changes.

Factory image composition, Aos named-resource registration, IAM
`kuksa-jwt` module configuration and fixed Provider-JWT preparation remain
owned by `WP-P1-PLATFORM-FACTORY-RUNTIME-001`. VDP, Brake/Tire bootstrap and
all upstream repositories are read-only.

## Exact Required Change

### Helper process and protocol

1. Build one C++ `aos-kuksa-auth-compat` process running as dedicated
   `aos-kac:aos-kac` with no root fallback, public listener, persistent state
   or dependency on VDP.
2. Listen only on `/run/aos-kuksa-auth-compat/request.sock`, owned
   `aos-kac:aos-kuksa-clients`, directory mode `0750` and socket mode `0660`.
3. Implement protocol `aos-kuksa-auth-compat/v1`: exactly one LF-terminated
   UTF-8 JSON request and response per Unix stream connection, followed by
   server close.
4. Accept only credential-free `status` or `issue` containing the single
   opaque `aosSecret`. Resource `kuksa` is implicit. Reject duplicate/unknown
   fields, invalid UTF-8, trailing objects, caller identity, authority,
   endpoint, resource or correlation.
5. Return only the accepted `ready`, `issued` or fixed-code `rejected`
   envelopes on the same connection.

### Native IAM and permission mapping

1. On every issue or renewal, call only pinned native v6
   `IAMPublicPermissionsService/GetPermissions` at TLS
   `127.0.0.1:8090`, trusting the Aos CA and verifying server name `main`.
2. Perform no DNS lookup, external connection, caller-selected endpoint,
   cached policy or parallel authority lookup.
3. Map exact leaf paths only: `r` to KUKSA `read`, `rw` to KUKSA `actuate`.
   Reject the whole issuance for `w`, wildcard, `provide`, `create`, malformed,
   unknown or broadened authority; never trim permissions to fit.

### Service JWT and signer

1. Sign through the provisioned per-Unit `kuksa-jwt` RSA-2048 PKCS#11 object
   using `RS256`; never export the private key or use a file-key fallback.
2. Use issuer `aosedge-kuksa-auth-compat`, audience `kuksa.val`, native IAM
   instance subject, exact scopes, TTL 300 seconds and renewal at 180 seconds.
3. KAC may issue only Service JWTs. It cannot issue, renew or expose the fixed
   OEM Provider credential.
4. Receive the dedicated PIN only through private systemd `LoadCredential`;
   never place it in URI, environment, arguments or logs.

### Verifier preparation and time

1. Add a short root-owned, networkless verifier-preparation executable/unit.
   It locates the exact `kuksa-jwt` object, performs protected sign/verify and
   atomically publishes only root-owned mode-`0444`
   `/run/aos-kuksa-verifier/kuksa-jwt-public.pem`.
2. Missing, ambiguous, malformed or unverifiable state publishes no verifier
   and keeps KUKSA and KAC unready without blocking unrelated AosCore work.
3. After every boot, require successful `systemd-timesyncd` synchronization
   plus a 10-second stable window before issue/renewal. Use `CLOCK_REALTIME`
   for JWT epochs and `CLOCK_BOOTTIME` for schedules.
4. Reject issue/renew as retryable `TIME_UNTRUSTED` when elapsed clock
   deviation exceeds five seconds. Add no anchor, continuous monitor, KUKSA
   lifecycle controller or instant-revocation claim.

### Bounds, isolation and diagnostics

1. Enforce the accepted frame, authority, JWT, path, concurrency, backlog,
   rate, 2/3/3/8-second deadline and retry/backoff bounds.
2. Set `TasksMax=32` and `LimitNOFILE=128`. Do not impose an unmeasured CPU or
   memory ceiling and do not present KAC as an AosCore quota-controlled tenant.
3. Permit only `AF_UNIX` plus fixed outbound IAM-loopback `AF_INET`; deny a TCP
   listener, DNS, external IP, shell, capabilities, systemd management,
   arbitrary `/var/aos` and Service-private token tmpfs access.
4. Use separate `aos_kuksa_auth_compat_t` and networkless
   `aos_kuksa_verifier_prepare_t` SELinux domains. Initial SoftHSM backend
   access is read/open/lock only; any required create/delete/rename access
   stops the packet for review rather than widening policy automatically.
5. Emit only fixed low-cardinality event code, KAC-generated correlation,
   outcome and retryability. Never log secret, JWT, permission/path/claim,
   signing/key, raw-frame or high-cardinality identity content.

## Service Bootstrap Boundary

Brake and Tire each own their Service-local SOTA bootstrap in their respective
artifacts. This packet supplies only the common protocol contract and fixtures;
it does not implement either container bootstrap. The bootstrap alone consumes
`AOS_SECRET`, atomically maintains the private mode-`0400` token file and
starts analytics with only `KUKSA_TOKEN_FILE`.

## Required Verification

All `UT-KAC-001` through `UT-KAC-010` obligations must pass with fake IAM,
signer and controlled clocks. In addition:

- the KAC C++ target and package-owned tests compile without a live Unit;
- repository Python tests and `tools/quality_gate.py` pass;
- executable-contract fixtures prove strict framing, mapping, JWT claims,
  lifecycle, timing, rate, retry, redaction and CPU/RAM-limit absence;
- package/systemd/SELinux inspection proves the exact user, paths, modes,
  dependencies, sandbox and removable boundary;
- no secret or generated credential enters source, test output or build
  artifacts; and
- changed files remain entirely within the writable boundary.

Real Aos IAM registration, PKCS#11 signing, KUKSA verifier loading,
cross-Service/cross-Unit denial, reboot, offline and R0 behavior remain later
image/integration qualification gates. Source completion cannot claim
`QUALIFIED`.

## Explicit Exclusions

- no Provider JWT or VDP connection authority;
- no Service-container bootstrap or analytics code;
- no Aos named-resource or Factory image-composition edit;
- no upstream AosCore/KUKSA modification or second policy store;
- no CPU/RAM quota or resource-manager claim;
- no dependency download, image build or external network access;
- no key, token, Unit identity or certificate generation in the workspace;
- no VM, provisioning, signing, upload, FOTA or live Cloud operation; and
- no push, merge or direct change to `main` by the worker.

## Authorization Gate

The user accepted the corrected KAC boundary, including removal of unmeasured
CPU/RAM ceilings while retaining deterministic process limits, on 2026-08-28.
Implementation may begin only in the isolated branch/worktree. Any writable-
boundary expansion, SoftHSM policy widening or external operation requires a
separately reviewed change request.
