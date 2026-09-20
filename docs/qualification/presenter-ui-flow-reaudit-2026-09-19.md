<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter UI flow, message and status re-audit

Date: 19 September 2026. Status: audit complete; five confirmed findings remain.
This pass implements no product correction and makes no live qualification claim.

Subsequent disposition: the operator approved U1–U5 and their local corrections
are implemented, tested and activated as recorded in the
[follow-up](presenter-ui-reaudit-fixes-2026-09-19.md). The analysis below remains
the pre-fix audit evidence; it is not the current implementation status.

## Scope and baseline

The operator requested another full audit of displayed facts, flows, messages,
status transitions and consistency after the
[displayed-fact corrections](presenter-ui-truth-fixes-2026-09-19.md).
The review covers Vehicle, Platform, Brake and Tire, their detail popups,
Cloud monitoring, Session, operation/retirement guidance, observation timing,
Reset semantics and the native Driving Control status contract.

The accepted [interaction specification](../demo/mockups/aosedge-demo-interaction-specification.md),
[Cloud observation architecture](../architecture/demo-control-cloud-observation.md),
[versioned-observability packet](../planning/active/work-packets/versioned-service-observability.md)
and [function-observation contract](../../contracts/service-function-observation/v3-contract.md)
remain authoritative. The retained 2.10 mockup is not the authority for its
superseded Park/Resume controls or subsequent accepted implementation amendments.

Repository HEAD at inspection: `d2298ba2f283896717c8cd8aa123fc1c76149782`.
The audit is of the current dirty working tree, including the preceding fixes,
not an assertion that HEAD alone contains them. Existing changes were preserved.
The serving Presenter contains assets `index-gXI-mt1i.js` and `index-DaPK5ALo.css`.
No build, restart, commit, push, publication, provisioning, Reset or Finish
operation was performed in this audit.

## Executive result

The existing regression gates pass. They do not cover all important combinations:
four extra UI characterization tests and one full-path backend-read test
reproduce the five findings below. Those tests assert the current defective
behavior; their passing result is evidence of reproduction, not defect closure.

The highest-priority issue is presentation of a conflicted Brake product record
as an ordinary received result. The software-story proof already rejects that
record; the visible summary does not. The other findings concern conflicting
next-step guidance, incomplete timeout coverage and observation/selection display.

Identifiers U1–U5 below are specific to this re-audit. They do not replace the
historical source-order issue named R2 or the earlier F/L/O audit identifiers.

## Confirmed findings

| ID | Priority | User-visible inconsistency | Confirmed cause | Recommended bounded correction |
| --- | --- | --- | --- | --- |
| U1 | P1 | A Brake result with `deliveryState: CONFLICT` can show `Good` and `Result received` on the card and ordinary model information in Overview, while Records exposes the conflict and the chapter is not proved. | Product selection accepts the row as the latest result; conflict checking is applied to completion proof, not the displayed summary. | Expose an integrity-conflict state consistently on card and Overview. Keep the record inspectable. Do not silently promote an older good record or change model thresholds. |
| U2 | P2 | Backend reads can still outlive the browser deadline and fall back to unavailable/last-known despite the new ten-second HTTP budget. Window detail has the same preflight issue. | Two sequential Docker ownership-preflight calls each have a twelve-second timeout before the HTTP budget starts. Window detail also uses a socket inactivity timeout rather than an absolute response-body deadline. | Bound the whole observation path, including existing ownership checks and window reads, inside the client deadline. Keep ownership validation and no-retry behavior; merely extending the browser timeout is not sufficient. |
| U3 | P2 | When certificate inspection fails in a fresh session, Selected Cloud remains `Reading configuration…` even though a configured session domain is known and the read has terminated. | The field only reads `selectedDomain` from a completed job, not the independently available session configuration. Failed certificate reads provide no such successful receipt. | Show the configured domain separately from certificate inspection progress/error. Use one authoritative current selection, not an inferred certificate destination. |
| U4 | P2 | The UI recognizes a status-only component update as pending, but its automatic Cloud observation stays on the idle interval. | The observer checks `pendingVersion` but does not use the shared component-pending interpretation for status-only `downloading`/`installing` reports. | Share the pending predicate between display and polling. Keep the accepted 2/4/8/10-second bounded schedule and one observer. |
| U5 | P2 | On the first assigned service installation, the service panel says Pending and blocks publication, but the story guide says `Next software profile` / `Prepare and publish` / `Open Brake v1`. | No guide branch handles a pending first service with no installed version. The runtime branch requires an installed version or issue, so profile selection treats it as an unprepared capability. | Add truthful first-installation pending guidance before choosing the next profile. Observe Cloud installation/runtime; do not ask for another Publish or Safe Stop. Apply to Brake and Tire. |

### U1: product integrity versus presentation

Relevant source:

- `apps/presenter-ui/src/features/service-team/backendSelection.ts:71–86`
- `apps/presenter-ui/src/features/service-team/useBackendObservation.ts:99–133`
- `apps/presenter-ui/src/features/service-team/BackendEvidence.tsx`
- Related Brake backend: `brake-health-cloud/apps/backend/src/brake-data-store.ts:722–730`

The backend explicitly projects `CONFLICT` when the message identity has a
`CONTENT_CONFLICT` quarantine record; this is not an invented API condition.
The temporary test supplied an exactly bound current-release Brake assessment,
valid source timestamp, observed reset state, `currentBand: GOOD`, score 100 and
`deliveryState: CONFLICT`. It confirmed all three simultaneously:

1. Chapter proof is absent, correctly.
2. Summary status is `Result received`, incorrectly unqualified.
3. The rendered card displays `Good` with no visible conflict explanation.

This finding is about product integrity, not the separately handled function
observation conflict. A failed or missing function report must not automatically
invalidate an independently valid retained product record.

### U2: the timeout boundary is only a substep

Relevant source:

- `apps/demo-orchestrator/src/aosedge_demo_orchestrator/backends.py:58–85`
- Same file: `_docker`/`_inspect` at 209–234; `_window_detail` at 589–618;
  `execute` at 620–656.
- `apps/presenter-ui/src/adapters/local/LocalPresenterReadAdapter.ts:16–27`

The full-path characterization executes production inspection and observation
control flow with synthetic Docker/HTTP responses and a virtual monotonic clock.
Two preflight calls taking seven seconds each plus the ten-second HTTP budget
produce 24 seconds, exceeding the browser's fifteen-second backend-read limit.
Each individual preflight remains below its own twelve-second timeout.
This is a controlled timing reproduction, not a measured 24-second live hang.
Window detail's browser limit is eight seconds and its preflight is the same.

Earlier L1 is therefore **partially closed**: the aggregate HTTP exchange/body
budget works and its slow-body regression passes; end-to-end request budgeting
is not closed. No ownership validation should be removed to close this gap.

### U3: selected configuration and certificate availability are different facts

Relevant source:

- `apps/presenter-ui/src/app/CloudConnectionPanel.tsx:13–33`
- `apps/demo-orchestrator/src/aosedge_demo_orchestrator/cloud_connection.py:190–209`

The temporary component test used a known session domain and a terminal blocked
inspection with `CLOUD_CREDENTIAL_MISSING_OR_UNSAFE`. The error appears, but the
known selected domain does not; the field still claims it is being read.
This is a display defect, not evidence that requests are sent to the wrong Cloud.
In the current live read-only session, certificate inspection succeeded and both
fields correctly displayed `aws-stage.epmp-aos.projects.epam.com`.

### U4: component pending presentation and cadence disagree

Relevant source: `apps/presenter-ui/src/domain/visibleCloudObserver.ts:81–87`.

A fake-timer test supplied a current observation with no `pendingVersion`,
`updateStatus: downloading` and a component with
`pending_component_status: downloading`. After the initial read there was no
read at two seconds; the next read occurred at ten seconds. This can add up to
eight seconds of avoidable initial display lag, plus request time. It is not a
deadlock and does not justify real-time requirements or more aggressive polling.
Earlier F2 presentation guards pass; observer alignment was not covered.

### U5: first installation is not a request to prepare again

Relevant source: `apps/presenter-ui/src/app/StudioWorkspace.tsx:175–191`.

The characterization renders a provisioned, connected controller with confirmed
VDP V1, a published and assigned Brake V1 candidate, pending service release
7.0.0, no installed service version and no running instance. It confirms the
Pending label and disabled Sign & publish button together with the contradictory
prepare/publish guide. Publication protection is working; operator guidance is
not. This scenario must be distinct from a prepared-but-not-published candidate,
a published-but-not-assigned service and an installed-but-not-running instance.

## Coverage and preserved semantics

| Area | Checked expectation and evidence | Outcome / limitation |
| --- | --- | --- |
| Initial Vehicle / empty slots | Built UI in a separate temporary tab; source and browser fixtures. | No controller, no Cloud Unit and setup preview correctly shown. No fabricated installed services or live backend input. |
| Create / simulator / provision | Accepted order, guide branches, operation plans and fixture gates. | Publish-before-Provision supported; simulation reused and post-provision connection remains distinct. No new live provisioning performed. |
| VDP V1–V3 | Source/profile binding, published versus installed, pending/failed/stale display, authoring guards. | Existing gates pass. Status-only pending polling gap U4 remains. Safe Stop applies to component installation, not services. |
| Brake V1–V3 / Tire V1 | Candidate, publication, assignment, installation and running evidence; compatibility separate from function. | Existing gates pass; first service delivery guidance U5 remains. Release number is not treated as profile number. |
| Backend cards and popups | Exact Unit/service/Subject/release binding, result versus input/activity, partial reads and reset state. | Existing gates pass, including function conflict; product conflict U1 remains. |
| Braking-window detail | Complete/incomplete recording, counts, scoped refresh and late chunks, responsive dialog tests. | Existing gates pass; full-path latency/body bound needs U2. |
| Reset | Pending/Cleared/Expired/Failed/Rejected, prior-release reset, history retained and operation ownership. | Existing gates pass. Gateway CLEAR is explicitly not telemetry-readiness or repair proof. No Reset was submitted. |
| Cloud card and monitoring | Actual Unit state, installed counts, pending state, CPU DMIPS, compact memory and node/Subject/instance/partition identity. | Existing gates pass. API read time is labelled Cloud checked, not device report time. Empty monitoring preview inspected. |
| Offline / stale / recovery | Retention, expiry, incomplete sources, independent native/backend/Cloud authorities; source and fixture checks. | No new display contradiction confirmed outside U1–U5. Local service continuity, transport recovery and backend silence were not live-tested this turn. |
| Session and Cloud selection | Lifecycle/Cloud/Test setup sections inspected without mutation. | Current staging selection correct. Failed inspection display case U3 remains. No Park/Resume offered. |
| Finish / interrupted run | Confirmation, active/uncertain-operation guards, paused retirement, continuation and recent-receipt acknowledgement. | Existing browser/unit gates pass. No actual retirement repeated; absence is not treated as proof of a new successful Finish. |
| Native Driving Control | Mode versus physical motion, external-link freshness, local advisory labels and Return to road receipt projection. | Three source-contract tests and one executed pure Swift projection test pass. Native windows were not running; no new visual/driving qualification. |

Minor consistency polish: some secondary authoring/Software views still use
`Not reported` while the overview already explains `No controller created`.
This does not assert false telemetry or block a flow, but shared setup wording
would make the empty-state experience less technical. It is not counted as a
sixth confirmed functional defect.

## Verification performed in this pass

| Gate | Result |
| --- | --- |
| Presenter type checking | Passed. |
| Existing Presenter unit tests | 261/261 passed across 24 files. |
| Existing Presenter browser tests | 117/117 passed. Fixture API calls are intercepted; not live Cloud qualification. |
| Related Demo Control tests | 111/111 passed: backends, observation budget, Presenter, operations, Studio Cloud reader, Cloud observation and performance. |
| Native status and scene projection | 4/4 passed: three source assertions and one production pure Swift projection execution. No native app launch. |
| Additional audit reproductions | Four UI characterizations and one virtual full-path backend timing characterization passed, reproducing U1–U5. |
| Built UI navigation | Vehicle, Platform, Brake, Tire, backend setup popup, monitoring Software/Resources and Session sections inspected. Certificate metadata inspection succeeded. No lifecycle or Cloud-configuration mutation. |
| Patch whitespace | `git diff --check` passed before adding this report; report checked separately afterward. |

The isolated characterization harness is under
`/private/tmp/ui-reaudit-20260919.qmBRfr/`; it does not alter application sources
or the accepted regression suite. The scenarios above are sufficient to turn
the reproductions into permanent correction tests in a subsequent authorized pass.

## Remaining qualification and proposed order

The preceding Test was retired; no active controller exists during this audit.
Factory .35/.36, published releases, VM/Cloud identities and simulator state
were not changed. Existing P8, historical source-order R2 and separate guest
reboot evidence retain their recorded status. Passing UI fixtures does not
close any of those live engineering checks.

Recommended next bounded correction order: **U1, U5, U2, then U3/U4**, with
regression cases derived from each reproduction. After those corrections,
run a live cycle to verify first delivery, all version transitions, offline
local continuity versus backend silence, Reset and Finish. Keep runtime and
product semantics unchanged; this report does not authorize implementation.
