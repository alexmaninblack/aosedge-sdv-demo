<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .36 follow-ups: local correction and diagnostic pass

Date: 19 September 2026.
Authority: operator selected R1–R5 from the
[follow-up review](factory-36-follow-up-review-2026-09-19.md).
Status: R1 and R3–R5 locally verified; R2 diagnosis remains open.

## Scope and results

| Item | Change | Evidence / remaining boundary |
| --- | --- | --- |
| R1 | Brake and Tire distinguish a missing token in an already validated private directory from unsafe credentials and RPC denial. The missing-token diagnostic projects to existing STARTING / WAITING / AWAITING_INPUT. | Both regression tests failed on the original code, then passed. Unsafe mode, malformed content, links, missing/replaced inputs and renewal tests remain fail-closed. The actual ARM64 gRPC products/bootstrap compile. No new service release was uploaded. |
| R2 | Add fixed diagnostic categories SAME_TIMESTAMP_CHANGED and TIME_REGRESSION to the existing VDP ordering exception. Neither category emits telemetry values, identifiers or credentials. | Both paths reproduce the original indistinguishable exception locally, clear values and now identify the category. Identical duplicate frames still do not republish or renew freshness. No ordering/freshness rule changed. The cause of the specific retired-run event is NOT established. |
| R3 | Separate plain-language recording outcome from chunk-delivery outcome. Preserve phase counts, actual samples, raw terminal code and record history. Cards/detail use the same recording label. | Incomplete recording plus durable 3/3 delivery displays both facts. Equal counts without durable receipt, unknown totals and inconsistent counts do not become success. Compact windows paginate three sample rows instead of five; samples are not discarded. |
| R4 | One shared selector guides empty results in cards and dialogs from current input/activity/delivery facts. | Stale, denied, invalid, disconnected, waiting, renewal, active recording, skipped recording, delivery pending/blocked and unknown/last-known cases covered. Reset confirmation alone and backend contact do not establish input readiness. Current-release and instance matching are unchanged. |
| R5 | Native scene completion projects the confirmed operation receipt into the banner mode. Return to road requires confirmed stationary Manual and Autopilot off; terminal Brake/Tire maneuvers use the existing confirmed Safe Stop/release contract. | Pure production Swift projection executed for completion, abort, failure, wrong kind/operation/target, missing stop proof and incomplete Manual receipt. Uncertain receipts retain reconciliation state. No extra drive command, CARLA restart or model reset is introduced. |

## R2: what is known and what is not

The old .36 event at 16:12:05.426 UTC only records
`VISS source frame is not monotonic`. That exception represents two different
conditions. The Test was subsequently retired with approval; a new live source
trace cannot be extracted from the deleted overlay.

Source inspection narrows, but does not settle, the cause:

- Gateway acquisition stamps frames with `system_clock::now()` in
  `carla-ego-runtime/src/runtime_carla.cpp`.
- `FormatIso8601Utc` in `src/vss.cpp` serializes milliseconds. Distinct
  acquisition instants within a millisecond can therefore share a serialized
  timestamp; this is a possible mechanism, not proof of the old event.
- `LatestVssSignalStore::Publish` enforces increasing frame IDs and uses a
  mutex for complete snapshot publication. Frame identity does not prove
  increasing wall-clock timestamps.
- VISS subscription events are serialized through the server event loop and
  write queue. No evidence in the retained log proves transport reordering,
  a clock correction, or same-millisecond changed values.

The local regressions prove both rejection branches and retained duplicate
freshness behavior. The next candidate VDP must include the diagnostic, with
normal source pin/provenance updates during release preparation. On recurrence,
collect the category and bounded source clock/frame timing evidence before
changing any source semantics. Do not treat a quiet observation interval as
proof that this intermittent defect is fixed.

## Completed gates

| Gate | Result |
| --- | --- |
| Brake native CTest | 8/8 pass |
| Tire native CTest | 5/5 pass |
| gRPC subscription wiring guards | Brake 7/7; Tire 5/5 |
| Real service compilation | Brake V3 and Tire V1 service plus bootstrap compiled with pinned gRPC/Protobuf/KUKSA in the existing offline ARM64 compiler image |
| VDP provider, family and ordering diagnostics | 14 + 35 + 2 tests pass |
| Presenter unit tests | 244/244 pass; 23 files |
| Presenter typecheck / production assets | Pass |
| Browser dialog/summary fixtures | 21/21 pass; 1280×720, 1728×1117, 1118×1124 layouts, keyboard return/focus, matching observations, negative source/profile evidence |
| Native control tests | 22 launcher/control, 20 orchestration, 4 road recovery and 1 executable Swift projection test pass |
| Complete native Swift source | Typecheck passes |
| Whitespace checks | Pass in affected source repositories |

Two test-harness issues were corrected rather than weakening the product:

- The observation persistence tests used `/tmp`, a macOS symlink rejected by
  production path validation. They now create their fixture under a canonical
  temporary directory. Production path restrictions are unchanged.
- Browser text assertions are scoped to the dialog because the same truthful
  guidance now also appears on its background card.

Browser screenshots of interrupted recording were inspected at compact and
native-panel dimensions. No modal/body overflow remains in the tested default
views. Technical record expansion remains an explicit diagnostic view.
These are isolated fixtures, not fresh vehicle/backend evidence.

## Activation and remaining work

- Presenter production assets are built. No forced reload of the user's page.
- Service products were compiled locally; no signing, upload, Subject mutation,
  deployment or package publication occurred.
- No new VM/Test, image rebuild, guest change or Cloud mutation was performed.
  The retired .36 run stays retired. Factory .35/.36 and Production remain.
- Native source was typechecked, not relaunched against a running simulator.
- No commit/push was performed in this pass; earlier unrelated dirty work was
  preserved. Source ownership remains main demo, Brake, Tire, runtime and
  vehicle-platform repositories.

Next, agree the remaining live matrix, prepare source-pinned candidates and
qualify first token issuance, replacement/reauthentication, real Brake/Tire
input and recording, Return-to-road → maneuver mode, and offline recovery.
R2 needs actual discriminating evidence, not just new labels. Keep the
previously separated bare guest-reboot check and optional R6–R9 outside this
pass. Do not claim full P8/clean E2E acceptance from these local gates.
