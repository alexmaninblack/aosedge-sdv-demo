<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Service input recovery: preserved Test and host regressions

Date: 18 September 2026. Status: bounded P1/P2 evidence, not full-chain or
active-profile qualification. No service package or Factory image was built
or deployed for these checks.

## Live boundary after the approved source transition

The [P1 source record](steering-source-numerics-2026-09-18.md) identifies the
approved local simulator/Gateway replacement and its rollback files. The
vehicle remained stationary in Safe Stop throughout this follow-up. The tool
review restriction on automated Autopilot activation was not bypassed.

The native Cloud read completed at 18:41:13 UTC for the existing staging Test
Unit `a842a53e-a30b-481c-8747-f73a96c351d7`:

- Online; no observation problems reported.
- VDP `79.0.0` installed, with no pending component candidate.
- Brake `59.0.0` and Tire `34.0.0` instances active; no reported instance errors.
- Factory `.35` retained. No Unit, VM or service lifecycle mutation occurred.

The bounded Gateway journal sample from 18:30:22 through 18:42:52 UTC contained
501 structural frame diagnostics: one initial 35-point record followed by
500 complete 41-point records. These are periodic diagnostic observations,
not a claim that every intervening source frame was captured. No raw telemetry
was copied to this record.

Service diagnostics showed both native containers alive, zero reported
thread/memory failure counters, and the same KAC/KUKSA/time-sync processes
with zero systemd restarts. The source-unavailable records corresponded to
the intentional source interruption; subsequent native telemetry showed
Monitoring for both services. The Brake backend still held assessments from
release `58.0.0`, not a new `59.0.0` result. None is relabeled as current proof.

## New regression scope

Only host test files were changed in the service repositories. Production
logic, schemas, quotas, thresholds, token leases and live service bytes are
unchanged. Tests use synthetic fixtures and temporary host storage; they do
not inject data into the live vehicle, KUKSA or functional backends.

| Service | Added proof |
| --- | --- |
| Brake V2 and V3 | Produce a fixture assessment, retain exact queued bytes and model state, disconnect, reread identical public metadata, reject an explicitly missing input, then accept a fresh stationary frame in the same Product instance. Metadata reread alone does not restore readiness; fresh input does. Recovery creates no assessment and does not reset the model. |
| Tire V1 | Retain a fixture model and exact queued record, disconnect, reread identical public metadata, reject a missing input, then follow the existing consumer sequence with a valid fresh frame. Readiness recovers; model, producer epoch, advisory sequence and old record bytes remain unchanged. |

Source tests:

- `brake-health-service/tests/cpp/runtime/product_tests.cpp`,
  `source_recovery_preserves_model_and_delivery`.
- `tire-health-service/tests/core_tests.cpp`, same named regression.

Local test-only checkpoints: Brake `3ce8a07` (base `90a9e2b`), Tire `43c37e4`
(base `e113183`). These commits have not been pushed or packaged by this work.

An initial Tire assertion incorrectly assumed FIFO delivery after a new status
record was added. Inspection confirmed that the existing outbox sorts by
message key. The test now verifies the exact retained record by its immutable
key; production ordering was not changed to satisfy the harness.

## Executed gates

Fresh isolated host builds in `/private/tmp/aos-service-recovery.IvjCq0`:

- Brake: all **7 CTest groups passed**, including the new V2/V3 recovery test.
- Tire: all **4 CTest groups passed** after correcting the harness assumption.
- Existing gRPC subscription source-contract tests: **5 Brake + 2 Tire passed**.

The host builds explicitly disabled the real KUKSA product executable. These
results exercise domain/storage logic and subscription construction guards;
they are not a TLS/gRPC reconnect integration test or VM restart/FOTA proof.
The immutable live setup and warm build caches remain preserved.

## P2 integration boundary still open

Source inspection confirmed the following distinctions:

1. Both services retry their KUKSA subscription and cancel it when their
   token, public metadata or CA file changes. Valid samples, not catalog
   presence alone, drive analytics readiness. The current graph recovered
   from this source interruption without redeploying either service.
2. The public input remains the accepted strict five-field schemaVersion 2.
   It contains Unit/role and the VDP family-document version/digest, not the
   active functional profile or component release. Rereading it cannot prove
   a V1/V2/V3 transition. The common `1.0.1` family version is not VDP V1.
3. The existing projector validates the committed slot, manifest and provider
   when explicitly invoked, and has cold-start/verify hooks. This inspection
   found no automatic successful-FOTA profile projection to service inputs.
   No new timer, transport, schema field or permission has been added.
4. Both bootstrap executables read/validate public metadata and the CA before
   their long-running retry loop. The product main functions also construct
   their runtime from metadata before entering subscription retry. Therefore
   recovery of an already-running service is not proof that an early install
   with absent initial metadata stays alive and recovers. This is a source
   finding; no live early-install failure was induced on the preserved Test.
5. Brake's diagnostic `DEGRADED / VISS_OR_GATEWAY_UNAVAILABLE` can mean that
   no request/reply has yet established advisory application in that session.
   Native Monitoring is a separate readiness fact, not an advisory ACK. Do not
   generate a fake SET/CLEAR to turn the diagnostic green.

Remaining work follows the accepted packet: close the service-local
compatibility/early-start integration without a Cloud dependency, freeze the
bounded observation wire contract before producer changes, then consumer-first
backend/service implementation. A genuinely new native input interface requires
the packet's bounded decision; these tests do not silently select one.

Moving-source validation, qualified Brake/Tire maneuvers and new current-release
result/advisory delivery subsequently passed the bounded
[preserved-Test follow-up](preserved-test-motion-and-results-2026-09-18.md).
Reset/offline tests, all version transitions and the clean UI cycle remain open
for this increment. No calibration or complete P1–P8 acceptance is claimed.
