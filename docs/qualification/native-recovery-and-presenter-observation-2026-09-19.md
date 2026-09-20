<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native recovery and shared Presenter observation

Date: 19 September 2026. Source/fixture qualification in progress; not live
qualification. Authority: P5/P6 of the accepted
[versioned-service work packet](../planning/active/work-packets/versioned-service-observability.md).
This record covers source/fixture work before activation. Subsequent backend
and Presenter activation is recorded separately in the
[preserved-Test activation record](preserved-test-function-observation-2026-09-19.md).
The preserved Test, Factory .35, CARLA and native app remain unchanged.
P7/P8 remain open.

## Native Driving Control

- Adds Return to road, Brake maneuver and Tire maneuver through a trusted
  Demo Control argv prefix, without a shell, new inbound listener or tick owner.
- Reuses the environment writer, persistent operation identity and private
  orchestration socket. Held manual keys are cleared; ordinary controls remain
  disabled during the helper; Safe Stop remains available. The UI worker is
  asynchronous and its output/deadline bounded.
- Return to road requires an actual stop, validates the configured known-good
  lane-aligned spawn and vehicle/walker/prop clearance, resets the same actor,
  waits for advancing settled road-placement evidence, then releases stationary
  Manual. Autopilot is an explicit subsequent action. No service/model Reset.
- Known rejected placements are recorded and released only into confirmed
  Safe Stop. An uncertain reply retains the same operation for reconciliation,
  including response loss after final release; it cannot trigger another
  relocation by blind retry.
- Native Swift compilation succeeded into an isolated temporary output, not
  the installed application. 138 Gateway Python tests and 64 Demo Control
  source tests passed, including road geometry, occupied placement, duplicate
  commands, stationary completion and lost-response reconciliation.
- Live activation, native visual layout, real collision/off-road recovery and
  proof that discontinuity/interrupted capture produces no spurious assessment
  are still required. Existing control discontinuity facts are not claimed as
  a new service input or as completed live proof.

## Shared backend and result projection

- Cards, details and current chapter proof use one source-ordered selector.
  A late receipt does not supersede a newer source result. Incomplete windows,
  transport-only messages, unknown source time, future source time, unbound
  legacy history and wrong native allocation cannot establish current proof.
- Cloud `instance_id` is the numeric native allocation index. It is not the
  opaque local `AOS_INSTANCE_ID`. The read projection matches exact current
  Unit, service, Subject, allocation index and installed release. Multiple
  opaque process identities within that allocation/release remain ambiguous;
  the UI never selects one by latest receipt or invents a Cloud-reported ID.
- The independent v3 function resource additionally matches the verified
  package profile. Reports use source generation/sequence and source freshness;
  delayed, future, conflicted or truncated reads cannot become a green current
  report. No report means unreported, not a proved service failure. Backend
  receipt/contact is not input readiness or vehicle advisory.
- Function facts show input, activity and delivery separately. The Gateway
  ACK reported by a service is distinguished from the native vehicle advisory.
  V3 may activate retained model state without a newly generated assessment.
- The chapter no longer retains a sticky proof that bypasses a subsequent
  unknown/reset outcome or changed current observation.

## Reset chronology

Command `issuedAt` is not a model-reset boundary. The shared selector accepts
completion only from a matching current native allocation/release, exact
command and producer epoch, correlated CLEAR request/Gateway response, valid
sequence and bounded timestamps. The conservative new-result boundary is the
Gateway's confirmed application timestamp, not command submission or receipt.
Pending/failed/rejected/expired/unconfirmed outcomes suppress current proof
and retain history: local model state may already have changed. No automatic
Reset retry, expiry extension or changed product command is introduced.

## Brake V1 detail

`democtl backend window-detail brake <event-id>` and the fixed same-origin
Presenter GET use the same application/backend reader. Current Test and owned
backend binding are resolved locally; the browser cannot supply a Unit, URL,
guest path or command. Only a bounded UUIDv4 event selector is accepted.

The reader requests the accepted backend WINDOW_DETAIL resource, caps the
response and 150 actual retained samples, and rechecks Unit/window provenance.
The view shows PRE/ACTIVE/POST counts, missing sample indices, source-time speed
and brake points and paged samples. It does not interpolate, resample or invent
a model score. Old wire provenance remains inspectable as history, not current
instance proof. No continuous raw telemetry transport is introduced.

## Tests and exclusions

- Presenter TypeScript check and 222 unit tests passed after the final
  expanded browser matrix. Focused selector tests include native binding,
  reset correlation, source-versus-receipt ordering, stale/conflicting reports
  and invalid window samples.
- 35 backend-adapter, 12 Presenter HTTP and 7 CLI/API tests passed. Local HTTP
  fixtures use ephemeral loopback ports. A test-discovery command selecting a
  nonexistent `test_api.py` ran zero tests; it is not counted as evidence.
- Browser fixture checks reproduce the new compact-layout overflow before its
  correction. All 107 browser tests subsequently passed, including new input
  versus activity/source-age/conflict cases and populated dialogs at 1280×720,
  1728×1117 and native-panel 1118×1124. Three added 150-sample V1 window tests
  reproduced compact-dialog overflow and misaligned table cells. The view now
  uses aligned table columns, side-by-side source-time traces and the existing
  Studio dialog variant; pagination and nested Escape/focus remain tested.
  An isolated production artifact was built successfully in
  `/private/tmp/aos-service-p4.MutJS1/presenter-p6`; it is not live activation.
  A fixture screenshot is not a live runtime screenshot.
- No VM/image build, backend activation, service publication or live renewal,
  offline/reconnect, Reset or clean E2E acceptance is implied by these results.

Temporary binaries/fixtures are preserved under the exact isolated
`/private/tmp/aos-service-p4.MutJS1` directory pending the corresponding live
and packaging gates. Factory .35 and the original warm caches are preserved.
