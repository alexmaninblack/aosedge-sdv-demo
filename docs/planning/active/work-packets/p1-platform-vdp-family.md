<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Vehicle Data Platform v1-v3 Implementation Work Packet

- ID: `WP-P1-PLATFORM-VDP-001`
- Lane: `L-PLATFORM`
- Increment: `IMP-03-VDP`
- Review state: `ACCEPTED — AUTHORIZED`
- Version: 0.1
- Prepared: 2026-08-28
- Accepted: 2026-08-28
- Authorized: 2026-08-28
- Implementation authorized: yes — only the bounded source scope in this packet
- Dependency download, artifact build, signing, FOTA and live qualification authorized: no
- Parent plan: [Demo Implementation Plan 1.2](../demo-implementation-plan.md)
- Readiness input: [WP-P0-PLATFORM-001 0.12](p0-platform-readiness.md)
- Requirements input: [CR-VDP 0.9](../../../requirements/components/vehicle-data-platform.md),
  SHA-256
  `acc1692c8147ef9a5236a29c01ae311afb4df6290d71b804611cf468423518a9`
- Executable contracts: VDP Compatibility 1.0.1
  `8e58e18e9d99a13409af6813e573cbe1c690e439ad746224426801f6b080c871`,
  VISS Trust and Telemetry 1.1.0
  `4a1a2bd804c3a49f707b5e640632bd8a0357901f59e4615c340622b043d4c12c`
  and Typed QM Advisory 1.0.2
  `f7ae78148fb3b3265c8b773117126665afb1edd97a73f59db5a1f3af7c223487`.

## Outcome

Implement three independent immutable Vehicle Data Platform Component source
profiles and a deterministic prebuild path for semantic versions `1.0.0`,
`2.0.0` and `3.0.0`. Each release is a distinct Platform FOTA candidate with
an exact capability manifest; no runtime flag may unlock a later release's
dormant behavior in an earlier signed artifact.

The existing Provider `0.2.0` and its accepted bytes remain immutable
historical qualification evidence. They are neither modified nor relabelled
as VDP v1.

## Repository and Isolation

| Item | Frozen value |
| --- | --- |
| Repository | `aos-vehicle-platform` |
| Base revision | `bdc72aba97a83c9868d454588189ef139710a6d7` |
| Required base relationship | clean `main`, equal to `origin/main` at authorization |
| Branch | `codex/imp-03-vdp-family` |
| Isolated worktree | sibling path `../aos-vehicle-platform-imp-03-vdp-family` |
| Dependency repositories | `aosedge-sdv-demo` contracts and Gateway interfaces, read-only |

## Writable Boundary

Only these owned boundaries may change:

- `providers/carla-viss-kuksa/**` for provider source, release profiles,
  configuration, package-owned tests and documentation;
- `packaging/fota/**` for the v1-v3 deterministic builder, validators,
  manifests, fixtures and compatibility entry points;
- `tests/test_provider.py`, `tests/test_fota_packaging.py`,
  `tests/test_contract.py` and new VDP-family owner tests;
- `DEPENDENCIES.json`, `THIRD_PARTY_NOTICES.md` and license/SBOM inputs only
  when an exact runtime dependency delta proves it necessary; and
- `providers/carla-viss-kuksa/README.md`, `packaging/fota/README.md`,
  `docs/architecture.md` and `docs/contract-compatibility.md` only where
  factual implementation wording changes.

The Yocto Factory/runtime layer, KAC, Gateway, functional Services, Demo UI and
all upstream repositories are read-only. A need to change any of them stops
the packet and produces a bounded change request.

## Immutable Release Family

### VDP `1.0.0`

The artifact contains exactly the seven accepted base-dynamics paths:

- `Vehicle.Speed`;
- three acceleration axes;
- accelerator and brake pedal position; and
- front-axle steering angle.

It contains no wheel-speed, wheel-slip or typed-advisory implementation.

### VDP `2.0.0`

The artifact is a strict v1 superset and adds exactly:

- four standard wheel linear-speed paths; and
- four standard wheel angular-speed paths in `degrees/s`.

Every v1 fixture and consumer remains behaviorally compatible.

### VDP `3.0.0`

The artifact is a strict v2 superset and adds exactly:

- four longitudinal-slip paths;
- four lateral-slip-angle paths; and
- the two accepted typed Brake/Tire maintenance-advisory request/status flows.

For each advisory, v3 validates exact caller, path, schema, value, canonical
encoding, freshness, lease, request identity, rate and replay bounds before
issuing the narrow VISS Set. It publishes the factual Gateway Status back to
KUKSA and never treats KUKSA or VISS transport success as application success.
It accepts no arbitrary text, arbitrary VSS write or vehicle-motion command.

## Trusted Platform Integration

1. VDP is an OEM-qualified trusted Platform Component. It performs no KAC
   request, `AOS_SECRET` lookup, Aos IAM permission exchange, dynamic Provider
   authorization or per-component attestation.
2. It consumes the fixed per-Unit Provider JWT only through the existing
   `LoadCredential=kuksa-token` boundary. The token is prepared outside the
   payload by `WP-P1-PLATFORM-FACTORY-RUNTIME-001`.
3. It consumes its distinct selected-Unit VISS mTLS client material only
   through protected systemd credentials. Wrong Unit, role, fingerprint,
   expiry or assignment state keeps VDP `NOT_READY`.
4. KUKSA remains unmodified and authoritative for API/path enforcement.
   Service JWTs can never grant `provide` or `create` and cannot be reused as
   Provider authority.
5. No private key, token, certificate, Unit/Node ID, assignment, Cloud target,
   signing credential or Service quota enters a VDP payload.

## Readiness, Failure and Logging

1. Separate process health from vehicle-data readiness. Missing or
   inconsistent VISS source, assignment, mTLS, KUKSA, Provider credential,
   active manifest/version or contract keeps VDP unready with a redacted fixed
   reason.
2. Validate complete source frames, types, ranges, timestamps, freshness and
   monotonic order. Missing, malformed, stale or disconnected inputs become
   explicit `NotAvailable`; never substitute zero or another normal value.
3. Recovery requires one complete fresh contract-valid snapshot from the
   current selected Unit and assignment generation.
4. Use fixed endpoint/connection topology, bounded retry/backoff and current
   state only. Persist no telemetry, analytics model or application history.
5. VDP is not an Aos SOTA tenant and receives no CPU/RAM quota, substitute
   resource manager or component-resource table.
6. Write only allowlisted factual diagnostics to standard output/error under
   the systemd unit. The native system journal and existing AosEdge/AosCloud
   log delivery are the only log path. Do not create a VDP log file, database,
   archive or retention policy.
7. Never log raw/high-rate telemetry, protocol frames, JWTs, credentials,
   certificates, VIN or unrestricted advisory payloads.

## Deterministic Artifact Boundary

1. Generalize the existing builder while preserving the exact historical
   Provider `0.2.0` compatibility path and accepted bytes.
2. Each new candidate contains only its selected executable/runtime modules,
   immutable capability manifest, contract identities/digests, provenance,
   dependency lock, SPDX SBOM, licenses and notices.
3. Deterministic double-build verification must produce byte-identical output
   for each release from the same pinned inputs.
4. VDP v1 cannot expose v2/v3 paths; v2 cannot expose v3 paths. Unknown,
   missing or mismatched profile/version/digest remains unready.
5. All three unsigned candidates are built, validated and digest-frozen before
   an audience session. Signing and submission happen during the demo without
   source edit, dependency download, compilation or rebuild.
6. Test-to-Production promotion uses the exact same signed artifact bytes.

## Required Verification

- all `UT-VDP-001` through `UT-VDP-008` obligations and existing repository
  tests pass;
- `tools/quality_gate.py` passes;
- exact v1/v2/v3 positive, negative and strict-superset fixtures pass;
- source staleness, disconnect/reconnect, wrong Unit/credential/assignment,
  manifest/version mismatch and dependency recovery pass;
- v3 advisory allow/deny, replay, rate, expiry, correlation and Gateway-status
  cases pass with fake VISS/KUKSA peers;
- Service credentials cannot obtain or reuse Provider authority;
- deterministic builder tests prove secret-negative payloads, exact metadata,
  historical `0.2.0` preservation and identical new-family bytes; and
- changed files remain entirely within the writable boundary.

Source completion cannot claim `QUALIFIED`. Exact ARM64 dependency retrieval,
the three immutable artifact builds, Factory Image integration, real
VISS/KUKSA, Test/Production FOTA and live advisory qualification require later
explicit gates.

## Explicit Exclusions

- no Factory/runtime, IAM/KAC, Gateway, Brake/Tire or Demo UI change;
- no dynamic Provider authorization, KAC Provider endpoint or Service secret;
- no VDP CPU/RAM quota, application store, log store or resource manager;
- no invented Brake/Tire model, threshold or predictive-maintenance claim;
- no dependency download, artifact build or external network access;
- no signing, Cloud upload, VM, provisioning, FOTA or live CARLA operation;
  and
- no push, merge or direct change to `main` by the worker.

## Authorization Gate

The user accepted the exact v1-v3 release graph, trusted-Provider boundary,
readiness/logging/storage behavior, source ownership, checks and exclusions on
2026-08-28. Implementation may begin only in the isolated branch/worktree.
Any writable-boundary expansion, dependency download, artifact build or
external operation requires a separately reviewed change request.
