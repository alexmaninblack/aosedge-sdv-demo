<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Studio 2.8 implementation increment — 13 September 2026

## Scope and authority

The user authorized the six-step convergence plan after comparing the .33 live
demo with the accepted 2.8 mockup. The mockup is preserved unchanged. This is
an implementation/testing receipt, not a new flow or Factory qualification.
All system actions use existing Demo Control CLI/application operations.
Production, Factory .33 and Cloud configuration/permissions are not changed.

## Changes

| Plan slice | Implemented behavior | Boundary |
| --- | --- | --- |
| Native client synchronization | Small build/session descriptor; paired idle web-view reload; dialog/unknown outcome guards | No VM, service or simulator restart from polling |
| Service controls | Prepare profile; one Sign & publish action; observe processing; first READY Deploy by service UUID; later publish without Deploy | Fixed SP and OEM roles, two retained dedicated Subjects, current Test; no version/count in assignment |
| Story and recovery | Firmware selection, contextual Create/Connect/Provision/remaining registration, pending VDP guidance, software profiles, backend result, Session and actual Trace | No auto-Apply, fake transition, downgrade, automatic retry or inferred cancellation |
| Observation | Component-scoped details; installed versus runtime; node/service/Subject/instance/partition resource grouping; zero retained and units explicit | Right-side platform data from Cloud, never a guest probe |
| Backend UX | Synthetic result/quality/score, expected service version, backend receipts, Records and details | Real transport; not vehicle analytics or driver advisory |
| Native visuals | Fixed left/right composition; B2 icons; correct architecture connections; dark Driving Control with unchanged input geometry/behavior | CARLA unchanged; dashboard uses only the existing vehicle telemetry contract |

`democtl service releases` exposes small persisted authoring records without
payload hashing or Cloud calls. Old receipts remain available for exact
installed-version/profile mapping but cannot become actionable current-run
candidates without current-run provenance. No new workflow database is added.

Native advisory rendering now reads the existing typed dashboard field instead
of hardcoding both strings in the view. The producer still supplies Unavailable:
the permission-backed return path/expiry proof is not implemented by this UI
change, and synthetic backend data is never wired into the vehicle dashboard.

## Verification

- Frontend: 103 unit tests and 78 isolated Chrome tests passed; TypeScript and
  production build passed. Tests include service Prepare/cancel/Publish/first
  Deploy/peer preservation/higher-version publish-only/reload and viewport fit
  at 1280×720, 1512×982 and native right-panel 1118×1124.
  After the final display/receipt corrections, the nine affected Chrome
  regressions and all 24 Presenter bridge tests were rerun successfully;
  the final production build also passed.
- Demo Control: Presenter/command bridge, service packaging/receipts, assignment
  and Cloud observation suites passed (24, 22 with one optional skip, 30, 25).
  Test sockets use local test servers; browser fixtures never contact Cloud.
- Native: both Swift sources typechecked; 20 Driving Control/tool regressions
  passed. Updated host restored all owned windows to the recorded geometry.
- Live retained .33: UI Connect in Manual completed; Brake v3 preparation
  allocated 12.0.0. UI Sign & publish reached Cloud READY, installed 12.0.0 and
  one active instance. The Brake backend showed an assessment from 12.0.0,
  VALID_DEMO_SYNTHETIC provenance and a durable received timestamp.
- Simulator/control surfaces were stopped/started once through Demo Control to
  adopt the native palette. VMs and Cloud identities were preserved. Telemetry
  remained LIVE after Test connection; native Autopilot was exercised.
- Tire v1 preparation allocated 10.0.0; UI Sign & publish reached READY,
  Installed and one active instance without a second Deploy. Its backend
  returned a 10.0.0 TIRE_HEALTH_ASSESSMENT with condition score 40, confidence
  75%, DEMO_SYNTHETIC content provenance and a durable receipt. The display
  was corrected to use Tire's actual `confidencePercent`/`sourceEventTime`
  fields, rather than assuming Brake's `quality`/`assessedAt` shape.

- VDP v3 preparation allocated 24.0.0. UI Sign & publish was submitted while
  native Autopilot showed 19.4 km/h / MOVING. Cloud reported 24.0.0 pending,
  with 23.0.0 still installed. Native Safe Stop then produced 0.0 km/h /
  STOPPED, and the Cloud-only Platform view changed to Installed 24.0.0.
  A separate read-only `democtl component status test` engineering observation
  confirmed active 24.0.0 in slot b, matching process/slot, zero restarts,
  successful main process, REPORTED_READY and 23 read paths. This guest read
  is not used by the Platform panel and is not independent consumer proof.

A fresh Create → Provision → full profile progression → Finish cycle has **not** been
rerun through the new UI by this receipt. The existing .33 CLI qualification
remains valid but is not substituted for that P8 gate.

The final idle Presenter server was stopped/started through `democtl ui` to
adopt the tested changes, without VM/Cloud/simulator restart. The reloaded
architecture restored VDP 24.0.0, Brake 12.0.0 and Tire 10.0.0 from current
observations. Both backend views retained their exact service versions;
Tire's confidence and event-time display were checked in the real interface.
The car was left in Safe Stop with LIVE telemetry for visual review.

## Still open

1. User visual acceptance and the final clean operator UI repeat.
2. Cloud service-permissions/KUKSA fix: real data, analytics and complete
   in-vehicle advisory remain unqualified; keep explicitly synthetic packages.
3. Cloud stale disconnect ordering: packaged CM idle status workaround remains;
   no server fix or hard recovery deadline is claimed.
4. Machine-readable workspace/lock reconciliation remains OPEN-05; this UI
   increment does not silently pin uncommitted source or change repo ownership.
5. Unknown native outcomes require existing journal-based engineering
   reconciliation. Expanded logs/terminal failed-install recovery remain
   deferred by the accepted current amendment, not hidden by a Retry button.

No build artifacts, credentials or runtime databases belong in Git. This
increment's source is not reported as committed/pushed until a separate Git
receipt establishes that fact.
