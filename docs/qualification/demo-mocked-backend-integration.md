<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Explicit mocked service data and real backend integration

Status: implementation authorized by the user on 11 September 2026, after
the service replacement proof. This does not close authenticated KUKSA or
vehicle/advisory acceptance in the [delivery plan](../planning/active/demo-studio-delivery-plan.md).

- Existing `democtl service prepare` gains an explicit mocked-data mode,
  mutually exclusive with the inert no-telemetry mode and requiring the
  temporary permission-free package. Normal authentication remains unchanged.
- Only current Test is eligible. Native service identity and the allocated
  package version remain real; no invented Unit, Subject, token or Cloud state.
- Brake uses deterministic synthetic samples with its existing product engine;
  Tire uses explicitly synthetic normalized features while its production
  feature extraction is still unqualified. Neither opens KUKSA nor sends a
  Gateway advisory request or fabricates an applied advisory acknowledgement.
- Service mock state/outboxes use a dedicated `demo-mock` subdirectory under
  their owned storage. Normal queues and model state remain untouched.
- Real HTTP delivery uses `/api/v1/{team}/demo-mock/messages` and the explicit
  `X-Aos-Demo-Source: MOCK` marker. Existing payload validation, durable storage,
  content binding and retry acknowledgements remain in use.
- Backends keep mock records in a separate database inside their owned volume.
  Normal product queries never return them. Mock reads always identify
  `source: DEMO_MOCK` and `vehicleTelemetry: false`; access remains scoped to
  the current Test. Private cleanup must account for both owned databases.
- Build, activation, publication and observation are Demo Control operations.
  No external fixture uploader or alternate service launcher is introduced.

Required proof: two real service-to-backend deliveries, native identity/version
correlation, duplicate receipt stability, retry after temporary backend loss,
isolation from ordinary product records, and visibly synthetic presentation.
Mock generation is not evidence of sensor acquisition, KUKSA authorization,
production feature extraction or in-vehicle recommendations.

## Execution checkpoint — 11 September 2026, 22:08 UTC

| Boundary | Evidence | Result |
| --- | --- | --- |
| Brake product | Source `438cac887b7ef248f81b4dbf69285c89d903101d`; actual ARM64 v3 export and seven native tests | Passed |
| Tire product | Source `fc81a37dbb68425bf659f7bbd683898d64966792`; actual ARM64 v1 export and four native tests | Passed |
| Brake backend | Source `da7ee6b12fbc7c4a85fcd0c3d75566982e7f8f34`; 48 backend tests | Passed; new image activated through Demo Control, existing volume retained |
| Tire backend | Source `76a5cd2e8f40da842f16d6ad6c955b5472f4594b`; 14 backend tests | Passed; new image activated through Demo Control, existing volume retained |
| Product-equivalent HTTP fixtures | Actual native C++ output → real backend HTTP → durable SQLite; duplicate returns the same receipt after backend restart; ordinary queries exclude mock records; exact private cleanup | Passed for both teams in isolated fixtures, not the live VM |
| Brake publication | 7.0.0 / v3; Deployment Bundle `bb56e411-90fc-4a47-a5a1-dd142f90a040` | Accepted once; Cloud READY |
| Tire publication | 6.0.0 / v1; Deployment Bundle `c2767b6d-b1ee-4436-b9fa-d3e0cc78d944` | Accepted once; Cloud READY |
| Current native service delivery | Test Cloud Unit `2a29c145-bbd1-4494-a0e5-d4b79e6a9db5`, system UID `d53d05cd4c4649c9a896534b23b88273` | Brake 6.0.0 Active / 7.0.0 pending; Tire 5.0.0 Active / 6.0.0 pending |
| Live backend records | Both owned backends are ready, with current Test context | Zero mock records; real VM delivery is **not yet proven** |

The later Brake commit `76d80e9` changes only its Python export-test fixture
to expect the seventh native test; it does not alter the published binary.

### Cloud observation contradiction

The exact Unit API reports Offline since `2026-09-11T21:17:11+00:00`, while
native CM continues exchanging websocket traffic, acknowledging messages and
sending monitoring. Cloud's monitoring API returned an exact-Test sample at
`2026-09-11T22:07:29.661650+00:00` (17 DMIPS, RAM 349839360 bytes).
Guest/host DNS resolve, the explicit connectivity filter is ON, and both
native managers remain active with unchanged PIDs and no additional restart.

This proves a disagreement between Cloud's Unit/connectivity view and its
accepted telemetry transport. It does **not** identify the internal dispatcher
fault. No forced Online state, repeat upload, Subject reassignment, VM/manager
restart, reprovisioning or Production change is used to conceal the disagreement.
Retain the exact packages and diagnostic VM until authoritative reconciliation.
Bounded CM diagnostics expose allowlisted stage labels, not message payloads.

### Remaining live gate and next steps

1. Observe the existing publications reaching the exact native versions; do
   not prepare more releases merely to retry delivery.
2. Through `democtl backend inspect`, correlate real receipts with Test UID,
   service ID, retained Subject, native instance and installed package version.
3. Exercise one scoped backend outage/recovery and durable retry, preserving
   the peer backend and both service identities. Do not equate local fixture
   restart evidence with this VM proof.
4. Confirm the visible team dashboard labels synthetic evidence and separates
   Cloud runtime, backend readiness and records.
5. Continue the accepted P5–P7 service/UI work; leave KUKSA, actual vehicle data,
   Tire production feature extraction and advisory acceptance explicitly open.
   No Factory rebuild or full cleanup before these gates are resolved.

## Presenter and adapter verification — 12 September 2026

The existing Studio build now presents Cloud-installed service versions on
the architecture map and reads per-Subject instance details. Entering either
team view refreshes Cloud state and its own backend observation; a missing
detail is incomplete evidence, not an absent service. Backend transport stays
inside the fixed same-origin read adapter. The current live read showed both
backends Ready and zero isolated mock records; no fixture was injected into
the live stores.

Verification: 99 UI unit tests, four isolated browser scenarios, production UI
build, 64 backend/retirement adapter tests, 20 package tests (one optional SDK
test skipped), nine Presenter HTTP tests, six Cloud-reader tests and 25 bounded
component-diagnostic tests passed. Both backend suites were rerun successfully
(Brake 48, Tire 14); documentation navigation passed. Browser scenarios prove
clickable synthetic record details and no guest/mutation calls, not VM delivery.

Only the idle Presenter process was refreshed with `democtl ui stop/serve`.
VM, CM, SM, Cloud assignments and backend processes were not restarted by this
UI refresh. UI is available on the established loopback port 18080. The native
left-hand workspace was not restyled or automatically restarted. Service
publication/assignment controls in Studio and the full operator E2E remain
later plan gates; this increment exposes backend observations, not simulated
success or a completed service workflow.
