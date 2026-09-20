<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Preserved Test: moving source, real results and advisory

Date: 18 September 2026. Status: bounded live P1/current-release functional
proof; not complete P1–P8, version-transition or clean Factory acceptance.

## Scope and identity

This follow-up uses the approved source corrections described in the
[steering source record](steering-source-numerics-2026-09-18.md) and the same
preserved staging Test. No package was published, no VM/service was restarted,
and no model reset, threshold adjustment or synthetic telemetry injection was
performed during these checks.

- Cloud: `aws-stage.epmp-aos.projects.epam.com`.
- Test Unit: `a842a53e-a30b-481c-8747-f73a96c351d7`.
- Factory `.35`, VDP functional V3 `79.0.0`, Brake functional V3 `59.0.0`,
  Tire functional V1 `34.0.0`.
- Source run: `09324e5b-5e95-4666-914b-6f5ae9d99a65`.
- Source checkpoints: Gateway `d5536e9`, restricted Unreal `9b705d6d2`.

The earlier execution-review denial was resolved by a new, explicit screenshot
check of the local CARLA button and stationary state, followed by an accepted
click. No security setting, keyboard/CLI workaround or approval policy was
changed. Native telemetry independently showed Autopilot / Moving.

The prepared Brake/Tire maneuvers intentionally stop and prepare the simulated
car through the existing single controller. This scene preparation was announced
and does not reset the service models, backend records or Cloud identity.

## Executed checks

| Check | Observed result | Limit |
| --- | --- | --- |
| Cloud read, 19:00:03 UTC | Same Test Online, VDP79 installed with no candidate, Brake59 and Tire34 instances active with no reported errors | Installation/runtime evidence is not product readiness |
| Autopilot source probe, 18:59:55–19:02:55 UTC | 3,598 frame-coherent reads; no opposite/invalid wheel pair, crossed frame or probe error | Independent source reads, not a capture of every Gateway frame |
| Repeat Autopilot probe, 19:09:58–19:10:58 UTC | Another 1,200 coherent reads with no invalid pair, crossed frame or probe error; 4,798 reads across both windows | Separate observation windows, not uninterrupted full-run recording |
| Gateway diagnostics in the same interval | All 120 sampled diagnostic frames had 41 points | Periodic samples do not exclude an unsampled missing path |
| First Brake maneuver | Completed; new Brake59 assessment durably received at 19:03:32.220 UTC, MONITOR, 25 active and 13 qualified straight samples | No guaranteed warning from a single maneuver |
| Second Brake maneuver | Completed; new Brake59 assessment received at 19:05:22.822 UTC, INSPECTION_RECOMMENDED, 26 active and 13 qualified straight samples | Existing accumulated model state was retained |
| Brake advisory | Backend SET fact confirmed the active recommendation, Gateway reason NONE at 19:05:23.151 UTC; later renewal observed | Request/application and backend product result are separate facts |
| Tire maneuver | Completed; Tire34 assessment durably accepted at 19:06:20.914 UTC, INSPECTION_RECOMMENDED, 44 valid active samples | This is one real maneuver, not calibration closure |
| Concurrent Brake processing | Tire maneuver also produced an eligible Brake59 assessment at 19:06:22.456 UTC, 17 active and 9 qualified straight samples | A maneuver label does not isolate physical effects from the other service |
| Native advisory display | Both Brake and Tire showed Inspection recommended; live telemetry continued | Current display was checked separately from backend records |
| Tire return to normal driving | A new Good result was followed by a CLEAR fact received at 19:12:09.438 UTC; Gateway observed active NONE/reason NONE at 19:12:09.354 UTC; native display returned to Monitoring | Natural model outcome, not a backend Reset; Brake's warning remained active |
| Presenter | Open Brake dialog changed from no result to MONITOR and then INSPECTION RECOMMENDED without a manual refresh; overview and Tire dialog showed corresponding current-release results | Exact UI propagation latency was not measured |
| Control transitions | Manual selected without pedal input, physical Safe Stop confirmed, then Autopilot resumed | No deliberate live timeout or disconnect was injected |
| Controller stability, 19:12:32 UTC | Session active in Autopilot; 12,566 heartbeats; command timeouts, ownership timeouts and disconnects all zero in this source run | Earlier intermittent timeout cause remains unproved |
| Host control regressions | 49 tests passed using isolated test sockets | Not a replacement for live interruption/recovery proof |

The first Brake result source time was 19:03:32.167 UTC; receipt was 53 ms
later. The second result source time was 19:05:22.676 UTC; receipt was 146 ms
later. Tire's source time was 19:06:20.867 UTC; receipt was 47 ms later. These
are cross-clock timestamp differences, **not** a measured transport latency
bound or a real-time guarantee.

The schema's `VALID_DEMO_SYNTHETIC` quality label describes the accepted demo
model. The input path in this test was real CARLA physics → Gateway/VISS →
VDP/KUKSA → deployed service, not the backend's separate mock-data route.

## Stability and preserved state

Bounded guest observations showed both containers alive, no reported
thread/memory failure counters, and no systemd restarts of SM, CM, VDP, KAC,
KUKSA or time synchronization. The later VDP journal contained both services'
`FORWARDED_TO_GATEWAY` and `VISS_SET_ACCEPTED` advisory events and no projected
update errors. These are bounded observations, not a fresh full SELinux audit.

No credentials, tokens or raw driving samples are included in this record.
No image build, cleanup, signing, publication or remote push occurred in this
follow-up. The original engine/Gateway rollback files and warm caches remain
preserved as recorded in the steering source document.

The documentation quality gate passed: 219 Markdown documents, 658 stable
identifiers and 38 Mermaid diagrams. `git diff --check` passed. This follow-up
changed evidence/plan documents only; running code and package versions were
not changed. Final UI observation retained Autopilot / Moving, Brake Inspection
recommended and Tire Monitoring; Cloud remained Online in Presenter.

## What remains open

1. The ordinary Autopilot drive still generated Brake episodes skipped as
   `INSUFFICIENT_QUALIFIED_WHEEL_SAMPLES`. Prepared maneuvers prove the real
   result path works, but the Presenter cannot yet explain each skipped episode
   through backend function observations. Do not report a missing Brake result
   as a delivery failure or assume any stop must produce an assessment.
2. Brief KUKSA-unavailable/recovery events still occurred during the later
   drive. The exact per-frame downstream cause was not correlated here. The
   zero-invalid-pair source probe and periodic 41-point diagnostics do not prove
   uninterrupted end-to-end input. No completeness/freshness rule was relaxed.
3. P2 service-local active-profile evidence, early-install metadata handling
   and automatic version-transition recovery remain open. Cloud/receipt-based
   Presenter profile binding is a separate completed slice.
4. P0's bounded function-observation wire contract and consumer-first P3/P4
   implementation, P5 native recovery UI and P6 richer status presentation
   remain governed by the accepted work packet; this test adds no interface.
5. Current-release success is not all-version P7 or clean-Factory P8 closure.
   Model reset, offline renewal, live restart, cross-version continuity and
   clean UI/Finish were not repeated by this follow-up.

See the [implementation work packet](../planning/active/work-packets/versioned-service-observability.md)
for ownership and the remaining gates.
