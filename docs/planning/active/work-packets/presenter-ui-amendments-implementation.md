<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter UI amendments — final implementation plan

Date: 20 September 2026.
Status: UIA0–UIA8 completed; implemented and activated on the preserved staging
Test, with scoped live/fixture qualification recorded separately. The operator
reviewed the resource presentation and accepted the Driver Advisory wording.
Subsequent audit/cleanup/publication is recorded in the
[checkpoint receipt](../../../qualification/ui-amendments-checkpoint-cleanup-2026-09-20.md).

Authority: the operator accepted all three entries in the
[UI decision register](../presenter-ui-amendments-2026-09-20.md), then accepted
the Resources navigation and long-Offline presentation choices and requested
this final plan. The subsequent instruction to begin work authorizes execution
of this packet. Preserve the current Test; no VM/CARLA/service rebuild,
publication, Production change or retirement is included.

## Outcome and preserved boundary

1. Brake and Tire each have a one-click **Reset Driver Advisory** on their Vehicle
   backend card, separate from **Backend details**, without a confirmation
   popup. Correlated CLEAR, not command submission, establishes success.
2. Resources has one **Disk** view without an alternate-parameter button.
3. The Aos Cloud card shows five-minute controller CPU/RAM graphs. Its popup
   shows separate controller, Brake and Tire CPU/RAM rows. Resources navigation
   is **CPU & Memory / Disk / Inbound / Outbound**.

Preserve the native-left/Presenter-right composition, B2 miniatures, service
colors, architecture arrows, existing software/update/connectivity facts and
other demo flows. Preserve backend records, pending deliveries, reset command
identity, source timestamps and all existing uncertainty/lifecycle guards.

Only the solution repository's Presenter, fixed host-side read adapters,
associated contracts/documentation and tests are in the source boundary.
No change to AosCore, VM images, Gateway, service algorithms/packages, quotas,
backend command protocol, authentication or Cloud deployment is planned.
No new guest collector, SSH polling, browser credential or direct public
backend mutation path is permitted. No service publication or factory rebuild
is necessary. Production remains untouched.

This packet supplements the
[versioned observability packet](versioned-service-observability.md); it does
not close that packet's deferred native/manual/calibration checks.

## Audit constraints to carry into implementation

| Area | Existing behavior / conflict | Required treatment |
| --- | --- | --- |
| Card interaction | Each backend card is currently one button | Use a semantic card with independent detail/reset actions; no nested buttons or event bubbling into details. Preserve anchor geometry and keyboard focus. |
| Confirmation | The common controller confirms every mutation | Make only `backend-reset` a one-click exception through the existing guarded submission path. Do not classify it as a read or bypass request IDs, session checks, serialization or uncertain-result reconciliation. |
| Reset feedback | Job completion and backend CLEAR are different observations | Share progress between card and popup; retain submitting/pending/uncertain state until a correlated observation reconciles the same command. A late old response must not re-enable Reset or restore an old result. |
| Disk | Parameter fallback is global today | Resolve per matching scope/partition. Preserve zero, missing, stale and conflicting values; do not sum aliases or let one controller metric hide instance data. |
| History | Latest-only projection collapses a series to one point | Add a distinct time-series projection; keep existing latest readings independently available. |
| Wire contract | Staging history uses a keyed services object; OpenAPI describes an array | Validate documented and observed shapes with explicit fixtures, not permissive parsing. Normalize numeric instance indices and timestamps without losing identity. |
| Units | RAM currently has `unit: null` | Record verified byte-scaling provenance in the adapter before MiB/GiB conversion. Unknown-unit inputs remain explicit; CPU stays DMIPS. |
| Freshness | A successful read can return an old measurement | Keep sample time, read time, source availability and freshness separate. Resource reads cannot refresh software or backend evidence age. |
| Read ownership | Resources currently polls only while its popup is open | Share one scoped observer between visible card and popup; independent latest/history failures must not block operations or other observations. |
| Layout | Fixed-height workspace and broad button CSS | Refactor affected selectors and check compact layouts, long messages, graph loading and arrows; do not hide required status text to force a fit. |

## Implementation sequence

Execute in order. An earlier gate failure prevents activation; a passing fixture
test does not establish live behavior.

### UIA0 — Freeze baseline and contract changes

- Record actual Git state and the served Presenter build before editing.
  Planning reference HEAD is `de5e038`; re-read it at execution time rather
  than assuming it remains current. Preserve unrelated changes and the
  previous runnable UI/host-adapter pair for rollback. Do not assume local
  commits are pushed or publish without the applicable authorization.
- Reconcile the accepted amendments with the
  [interaction specification](../../../demo/mockups/aosedge-demo-interaction-specification.md),
  [Cloud observation contract](../../../architecture/demo-control-cloud-observation.md)
  and [reset contract](advisory-readiness-and-demo-reset.md). Narrowly document
  the Reset confirmation exception and superseded summary-resource rule.
  Historical mockups remain historical; do not overwrite them.
- Freeze an additive, fixed current-Test history-read contract in the existing
  democtl/Presenter path, separate from the latest-monitoring operation. Use
  the same selected OEM, tenant, domain and Unit ownership checks. The browser
  cannot supply arbitrary Cloud URLs, credentials or Unit targets.
- Verify `not_older_than` syntax from authoritative documentation/source before
  using it. Do not guess a duration or timestamp format. If only the already
  proven optional-parameter-free read is available, retain hard response/point
  bounds and explicitly limited coverage; never imply guaranteed retention.
- Confirm RAM scaling through the supported source/API path and record the
  evidence. Define time-series identity, null/invalid handling, duplicate and
  conflicting-point handling, coverage and source-time fields in fixtures.

Gate: contracts and tests describe one coherent target; no new product choice
is required. Any newly discovered authority/protocol expansion stops this
packet for a bounded review rather than becoming an implicit change.

### UIA1 — Implement bounded, independent Cloud resource reads

- Keep the existing latest-monitoring path compatible. Add the independent
  history read using `GET /api/v11/units/{item_id}/monitoring/dashboard/` and
  the explicit `units_monitoring_dashboard` permission check.
- Preserve current-Test preflight, selected-certificate authority, redaction,
  existing per-request/process/result bounds and no account-wide scans.
  A history failure, missing permission, malformed response or oversize result
  must not discard a valid latest reading or alter Unit connectivity.
- Normalize series by Cloud/tenant/Test/Node/service/Subject/instance/metric.
  Retain timestamps as instants; sort and deduplicate without fabricating
  data. History cannot establish that an old instance/version is current.
- Introduce one shared resource observer for the visible Vehicle card and
  Resources popup. Latest and history have independent bounded reads and
  outcomes. Use nominal 30-second polling, no overlapping identical requests,
  visibility-aware suspension and scoped cancellation/late-response rejection.
- Clear cross-run/Cloud/tenant retained data on binding changes. Do not add a
  persistent telemetry database. Keep all other refresh cadences unchanged.

Gate: adapter, authority, schema, bounded-failure and isolation tests pass;
slow/failed history cannot block latest metrics, functional backend reads or
command submission. Existing monitoring consumers remain compatible.

### UIA2 — Refactor cards and move Reset scenario

- Convert the clickable backend-card wrapper to a semantic container with
  separate detail and Reset actions; retain its appearance, team colors,
  miniature, architecture anchor and accessible labels.
- Route the one-click Reset exception through the existing submission code.
  Preserve synchronous duplicate protection, native checks and uncertain
  request reconciliation. Keep all other mutation confirmations unchanged.
- Share reset availability/progress/outcome projection between card and
  details. Keep immediate submission feedback even before an operation receipt
  arrives. Do not infer CLEAR from a successful HTTP response or completed job.
- Preserve existing disconnected, incompatible, busy, retiring, pending and
  uncertain-state behavior with a visible reason. Brake V1/V2 must not acquire
  reset capability merely because a card exists. Preserve the peer service.
- Remove only the popup's Reset action; keep last-reset information/history.
  Reset changes neither Cloud resource history nor the five-minute graph clock.

Gate: click/keyboard/double-click, delayed/reordered responses, expiry,
release-change and response-loss tests pass; a detail click never resets and
a Reset click never opens details. No other confirmation is removed.

### UIA3 — Consolidate Disk and resource navigation

- Introduce **CPU & Memory / Disk / Inbound / Outbound** without duplicating
  resource observers. Retain the existing Cloud **Software / Resources** tabs.
- Replace global Disk fallback with scope/partition-specific resolution. Show
  each logical measurement once, preserving source/quality information.
  Do not treat two differing parameter values as interchangeable without
  verified semantics; expose an unresolved conflict instead of inventing a total.
- Preserve Node and service-instance selection in Disk/traffic views. Missing
  metrics or unknown units remain explicit; zero remains a valid measurement.

Gate: primary-only, alternate-only, mixed scopes/partitions, both parameters,
zero, null, missing and stale cases pass. Disk and traffic remain accessible.

### UIA4 — Render graphs with truthful time and state

- Add two compact controller graphs to the Aos Cloud card, retaining installed
  software, updates, connectivity and the detail entry. In Resources, show
  controller/Brake/Tire rows with CPU and memory graphs and latest values.
- Use actual timestamps and a common time axis; identify scales, units and
  sample ages. Controller usage is guest-node usage, not the host Mac's total.
  Do not add controller and service consumption or invent quota percentages.
- Keep gaps and last-known states visible. Do not append a new point for an
  unchanged sample on each refresh, interpolate an outage into live activity,
  or claim that a missing Cloud measurement proves a stopped service.
- Keep the current five-minute interval anchored to the present. After a long
  outage it may be empty; keep the last value and age outside it. Any retained
  historical graph displays its real dated range, never a shifted live range.
- Distinguish initial loading, successful empty response, partial history,
  unavailable history and retained stale data. Label ambiguous/unmapped
  instances rather than assigning their values to the first matching service.
- Recheck native right-pane and compact viewport layouts, keyboard/focus,
  contrast, long messages and architecture arrows. Avoid graph animation that
  implies extra samples or forces card/layout jumps.

Gate: rendering fixtures preserve value/time/identity across updates,
navigation, reload, Offline/Online and history/latest response reordering;
required facts and actions remain readable and reachable.

### UIA5 — Run regression and response-time qualification locally

- Run affected Python adapter/operation tests, Presenter type checking and
  unit tests; then the existing browser suites and production UI build.
- Add deterministic delayed/hung/failed Cloud and backend fixtures. Opening
  or closing a popup and showing local Reset submission feedback must not
  await a resource response. The operation may still be rejected by its own
  valid guard; never remove a guard to make a timing test pass.
- Measure click-to-feedback, request duration, backend-command acceptance,
  CLEAR-to-visible outcome and source-sample-to-render separately. Record
  minima/typical/maxima and polling phase where available; do not describe
  operator reading time as latency or set a new real-time system requirement.
- Explicitly check no old/new state oscillation, no duplicate submission,
  bounded request counts, independent peer updates and unchanged confirmation
  behavior for Finish/publication. Use short deterministic fixture deadlines
  to test timeouts without waiting on real Cloud failures.
- Run documentation/link and secret/diff checks. Review the complete diff;
  unrelated code changes and guest/service dependencies fail this gate.

Gate: affected and regression suites/build pass, timing findings are resolved
or clearly block activation, and the previous runnable build remains available.

### UIA6 — Activate narrowly, verify live UI and hand off

- After runtime activation and relevant live checks are authorized, activate
  only the required host Presenter/read-adapter processes at an idle operation
  boundary. Preserve CARLA, Driving Control, VM, Cloud identity and services.
  Verify the served build before attributing a visual result to the change.
- Through the Presenter UI, check resource graphs against read-only native
  Cloud observations, card/popup consistency, and each independent Reset
  through matching CLEAR and a later real result. Confirm history and peer
  service state are retained. Do not manufacture warnings or telemetry.
- Exercise External Network OFF for more than five minutes, then ON, only
  under live-test authorization. Verify resource ageing/empty current window,
  functional backend receipt interruption, local service continuity and honest
  recovery/backlog. A resource timeout is not itself Cloud Offline evidence.
- Test initial/no-Unit, uninstalled-service and wrong-Cloud cases in fixtures;
  do not destroy/reprovision the preserved Test solely to obtain those screens.
  No Finish, publication or VM restart is part of this packet by default.
- Consolidate test/timing/visual evidence and exact source/build references.
  Review checkpoints and public-push authority separately. A local build or
  commit is not reported as deployed, pushed or live-qualified.
- If activation fails, restore the previous compatible Presenter/adapter pair
  without rolling back the VM, resetting service models or deleting run data.

Gate: the live UI matrix passes, no unexplained status regressions remain,
runtime is preserved, and the operator can perform final visual review.

Execution evidence: [qualification report](../../../qualification/presenter-ui-amendments-qualification-2026-09-20.md).

## Mandatory acceptance matrix

| Scenario | Required evidence |
| --- | --- |
| Reset from Brake/Tire card | Correct service, one submission, no confirmation popup, immediate feedback, matching CLEAR only |
| Details click / keyboard / rapid repeat | No unintended reset or popup; accessible focus; duplicate guard remains effective |
| Reset pending, expired, failed or uncertain | Honest state on card and popup, no success shortcut or blind resubmission |
| Reset during SOTA, Finish or peer operation | Existing binding/lifecycle/serialization checks remain; peer data preserved |
| Disk mixed response | Controller/instance/partition data preserved with no aliases double-counted |
| CPU/RAM latest and history | Correct units, separate scopes, true timestamps; valid latest data survives history failure |
| Missing history permission or malformed payload | Explicit scoped failure, no false Offline or fabricated empty history |
| Delayed/hung Cloud request | Local navigation/actions and independent backend observations remain responsive |
| Resource refresh while Reset executes | No shared blocking dependency; no request flood or status rollback |
| Reload, navigation, concurrent surfaces | Shared bounded reads, no repeated mutation, no obsolete in-flight result applied |
| New Test / tenant / Cloud / service identity | No cross-scope cached measurements or reset outcome |
| OFF longer than five minutes / ON | Empty current interval where appropriate, last value aged, historical dates retained; real samples resume |
| Compact and native layout | All actions/facts reachable; miniatures, colors, arrows and native-left composition preserved |

## Completion and remaining authority

There are no open product choices within these three amendments. Technical
schema, timing and compatibility proofs are execution gates, not assumptions
of success. The preceding audit passed 42 targeted local tests and the
documentation gate; those results qualify the existing mechanisms only.
They do not qualify the proposed UI or close deferred work outside this packet.

The operator authorized implementation; scoped execution is complete. This plan does not authorize external publication,
Production changes, destructive cleanup or an expanded VM/service project.

## UIA7 — disk/traffic units follow-up

Authorized after the operator's live resource review on 20 September 2026.
The diagnosis verified bytes from protocol/Core, deployed Cloud frontend and
live guest/source comparisons. Native private-network exclusions explain zero
service traffic; a new backend network is deferred.

1. Add verified byte metadata to the existing disk/traffic projection without
   changing source values, permissions, endpoints or refresh cadence.
2. Format byte volume adaptively; label used partition space and daily traffic
   volume. Preserve unknown/missing/zero/conflict/retained-source distinctions.
   Show all four current controller partitions on one page. Explain local
   backend accounting exclusions without implying missing delivery.
3. Test formatting boundaries, controller/service identities, four partitions,
   daily versus per-second semantics, previous-day samples and unavailable reads.
   Run Presenter regression/typecheck/build and affected Python tests.
4. Preserve the previous build; activate only the Presenter display/host read
   path and inspect live Disk/Inbound/Outbound. No VM/service/CARLA restart,
   Reset, network toggle, publication or full demo cycle is needed.
5. Record actual qualification and handoff. Do not claim public push or change
   the accepted native resource source of truth.

Status: implemented, activated and qualified on 20 September 2026. See the
[UIA7 qualification](../../../qualification/presenter-ui-amendments-qualification-2026-09-20.md)
for test totals, live observations, preserved runtimes and rollback evidence.

## UIA8 — Driver Advisory reset wording

The operator approved the label/message follow-up on 20 September 2026.
Rename the visible button on both cards to **Reset Driver Advisory**, with
team-qualified accessible names. Submission/waiting says **Resetting driver
advisory…**; only correlated CLEAR says **Driver advisory reset**. Align detail
feedback and the operation title. Do not rename the native command or alter
reset behavior. Cover both teams and pending/confirmed states in tests, build
the Presenter, preserve its preceding assets and activate without runtime
restarts or a live advisory reset. Record scoped qualification.

Status: implemented and activated; typecheck, 322 unit tests, 137 browser tests
and production build passed. See the
[qualification report](../../../qualification/presenter-ui-amendments-qualification-2026-09-20.md).
