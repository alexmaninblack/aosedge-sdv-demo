<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter status audit: correction receipt

Date: 14 September 2026.
Scope: authorized implementation of the prioritized
[UI status audit](../research/demo-ui-status-audit-2026-09-14.md).

## Result and limits

The correction increment is implemented in the current working tree. It uses
existing Demo Control/Cloud read boundaries, not direct guest probes. No new
VM, factory build, component/service publication, Cloud assignment or live
demo cycle was performed. Production and the retired Test state are unchanged.
Only the idle Presenter server was restarted through `democtl ui stop` and
`democtl ui serve` to load its corrected backend. Its browser was reloaded and
left on Vehicle. The native control source will be compiled by the existing
launcher at its next start; CARLA was not launched for this increment.

Existing unrelated changes were preserved. No commit or push is claimed.

## Correction map

| Audit | Implemented behavior / remaining boundary |
|---|---|
| F01 | Running requires a current active instance of the exact selected and installed version, with no reported service error. The story cannot advance past an unconfirmed installed service runtime. |
| F02 | Component/service/package details resolve against the current inventory/catalog rather than a frozen row. Run/Unit changes clear selection. Removed entities are not relabelled current. |
| F03 | Component error text and failed update/publication states are visible. Failed installation is not described as waiting for Safe Stop. |
| F04 | Service-level errors, Aos/exit codes and pending ID/status without an expanded version object are consumed by presentation and pending detection. |
| F05 | Not created, not provisioned, no report, unavailable and last-known data are distinct. Unknown local state never proves the controller is absent. Empty Components explains its prerequisite. |
| F06 | HTTP 200 does not override failed monitoring section state. Error reason is displayed; retained samples retain their original timestamps instead of becoming zero/absence. |
| F07 | An expected release without backend results is explicit. Overview does not substitute the previous release's result; historical records remain accessible. Partial/unavailable reads do not claim current evidence. |
| F08 | An inventory refresh still outstanding after 15 seconds makes the previous report STALE. Observation age is visible; old dates are not reduced to time-of-day in Cloud views. Per-service detail report times survive aggregate merging; stale instance state is explicit. |
| F09 | Overlapping inventory requests share one read, but a later manual/post-action read is not a one-second cache hit. Slow publication reads no longer hold the Unit response: at most one bounded read per publication kind is retained and exact-run/release keyed. Unit fetch budget is 65 seconds, exceeding its 60-second worker budget. |
| F10 | Read-only diagnostics remain available during uncertain mutations; the blocking reason explains why Finish cannot overlap an unknown operation. Lost-response reconciliation uses the original request identity, including archived IDs. There is **no force-clear, replay or universal automatic reconciliation**: truly unknown outcomes still require engineering handoff. |
| F11 | Detailed history rolls over at 128 entries without disabling Finish. Compact original-request tombstones preserve at-most-once execution. An uncertain receipt is retained in the detailed history. |
| F12 | Trace and passive progress use the current run; an empty trace does not display the previous run's last job. An actually active session operation remains visible. |
| F13 | An ordinary browser announces a newer build. Reload is explicit and blocked during active/uncertain operations and dialogs. Native wrapper reload protection is unchanged. |
| F14 | Backend records, service lists, instance details and resource samples are paginated. Backend page capacity adapts to the fixed viewport; compact cards lead to full details. No whole-page scrolling was introduced. |
| F15 | Disabled publication/deployment prerequisites are explained. Active guide offers View progress; operation duration and active step are shown. Terminal receipts no longer show an intermediate step as current activity. |
| F16 | Native external-link label applies the same 15-second freshness limit as its click handler. Autopilot says MODE SELECTED, not VEHICLE DRIVING. Physical movement/telemetry remain separate; no new bridge heartbeat or real-time guarantee is claimed. |
| F17 | A newer successful configuration read outranks an old Cloud-selection receipt. OEM certificate inspection is explicitly not API/SP access verification. |
| F18 | Traceability authorization/current implementation and the abnormal-Finish contract now agree. Current-renderer regressions are separate from retained mockup/legacy fixture tests. |

## Verification

- TypeScript check and production frontend build passed.
- **125 frontend unit tests** passed, including the original seven audit
  reproductions converted into regressions, unknown/empty state, version-bound
  runtime, uncertain read-only access, configuration precedence and build notice.
  The live retired-Test response `NOT_APPLICABLE / TARGET_NOT_CONFIGURED`
  is explicitly covered as an initial Create state, distinct from UNKNOWN.
- **87 browser tests** passed. Populated 20-record pagination was checked at
  1280×720, 1512×982 and the native right-panel size 1118×1124, including access
  to the final record and no panel overflow. Existing Studio service progression,
  retirement, monitoring and retained legacy fixtures were included.
- **36 Presenter backend tests** passed with mocked operations. Added cases
  cover 128-receipt rollover plus Finish and duplicate replay rejection, a
  delayed publication alongside usable Unit inventory, and immediate fresh
  consecutive inventory reads.
- **2 native source-contract tests** and Swift type-check passed. These are
  not live native application/vehicle tests.
- Both touched repositories passed `git diff --check`.
- Live read-only smoke check after Presenter restart/reload confirmed
  `No controller created`, `Create a controller first`, no fabricated installed
  release, and an empty current-run Trace. No action confirmation was submitted.
- A subsequent frontend build was detected by the already-open ordinary
  browser, which displayed the new-build notice. Its explicit Reload UI action
  loaded the new entry without a demo operation. Final served entry:
  `index-DojYIyaG.js`, stylesheet `index-ZD7m5zpE.css`. Built artifacts are not
  committed as source.

Browser/unit cases use controlled API fixtures, not real Cloud timing. The
previous real RabbitMQ/network cycle is separate evidence. The first browser
verification exposed remaining 720-pixel-height clipping; the bounded page
capacity was corrected and the complete browser suite rerun successfully.

## Next gate

Run one agreed operator-visible full cycle using the corrected Presenter:
Create/provision, VDP transitions with native Safe Stop, service transitions
without Safe Stop, synthetic backend receipts, link OFF/ON with separately
observed Cloud connectivity, then Finish. Verify native control wording at
that launch. Do not infer live latency or complete Cloud deletion from local
packet-filter state or from these isolated tests.

Real service-to-KUKSA permissions/advisory, Production rollout and permanent
resolution of the Cloud stale-event/queue issue remain outside this increment.
