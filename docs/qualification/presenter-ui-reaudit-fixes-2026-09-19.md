<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter U1–U5 re-audit corrections

Date: 19 September 2026. Status: all five corrections implemented, local gates
passed and updated Presenter activated. Live demo qualification is not claimed.

## Authority and boundary

The operator accepted all five findings in the
[flow/status re-audit](presenter-ui-flow-reaudit-2026-09-19.md).
One writer changed the Solution repository only: Presenter, its bounded local
backend reader, tests and documentation. HEAD at entry remains
`d2298ba2f283896717c8cd8aa123fc1c76149782`; existing dirty work was preserved.
No VM, Factory, AosCore, service, model, schema or Cloud change belongs to this
pass. No publication, provisioning, Reset, Finish, simulator action, commit or
push was executed. The historical audit remains a record of the pre-fix state.

## Corrections

| ID | Implemented correction | Regression evidence |
| --- | --- | --- |
| U1 | Conflicted product heads remain selected for inspection but show Result conflict / Result not trusted, explicit integrity guidance and no Overview condition meter/quality claim. Records retain raw facts; record detail exposes delivery integrity. No fallback to an older healthy record or chapter proof. Next-result guidance no longer presupposes successful delivery. | Assessment and window conflict tests; source ordering with an older healthy record; card, Overview and Records; compact 720/1000px browser dialogs. |
| U5 | Current pending service installation gets an explicit observation step with team/release, no repeat Publish and no Safe Stop. Existing runtime issues, stale inventory and component update gates retain precedence. | First Brake and Tire assignment with no installed version; publication stays disabled; browser guide offers Refresh Cloud state. |
| U2 | The read request creates one absolute deadline before inspection: ten seconds for summary, six for window detail. Both Docker inspection calls receive only remaining time; HTTP receives the same deadline. Window detail also uses the existing body watchdog. | Deterministic full execute/ownership path; shrinking subprocess timeouts; no HTTP after failed preflight; foreign ownership still rejected; slow window body interrupted. Existing real-loopback dribble regression remains green. |
| U3 | Selected Cloud reads current session configuration, independently of certificate result. A completed old selection receipt cannot override it. Missing configuration is Not available after session load, not indefinite Reading. | Failed certificate inspection with and without historical successful selection; current session wins; Use this Cloud stays disabled without a valid certificate inspection. |
| U4 | Cloud observer reuses componentPending for inventory and aggregate update status, preserving one flight and existing backoff/idle schedule. | Both status-only sources execute 2/4/8/10-second reads, then return to ten-second idle after completion. |

The pre-fix targeted tests failed on the exact expected behaviors before source
correction. Timing tests use simulated subprocess/HTTP latency, not a claim of
measured live Docker performance. No fixture request is sent to Cloud. The
previous tests' optional session-domain fixture was aligned with the actual
session configuration field; its old-selection protection remains asserted.
The expanded Python invocation needs `PYTHONPATH=tests:src` for legacy shared
test fixtures; an initial import-only failure was corrected in the invocation,
not by changing the product or removing tests.

## Verification

- Presenter TypeScript passes. **269/269 unit tests** across 25 files and
  **120/120 browser tests** pass. Browser API responses are intercepted fixtures,
  not live Cloud evidence.
- Production build passes: `index-rETPP7ln.js` and unchanged
  `index-DaPK5ALo.css`. No layout/font change was needed.
- Expanded Demo Control gate: **157/157 passed** (backends/read budget,
  Presenter/operations, Studio Cloud reader, Cloud observation/performance,
  backend retirement and CLI). Only local fixtures and ephemeral loopback
  test servers were used.
- Screenshot inspection: conflict is visibly labelled, model meter absent,
  independent input/activity/delivery facts retained, dialog fits 1280×720.
- Original interpretation protections remain: no missing→healthy inference,
  no latest-receipt override of source order, no unconfirmed Reset→readiness,
  no service Safe Stop dependency, no shortened advisory/token leases.

## Activation and remaining scope

After final gates, the existing Presenter reported no active or uncertain
operation and the selected staging domain. The guarded `ui stop` verified owner
and idle state and stopped only that server. `ui serve` started the tested
sources and built assets on `127.0.0.1:18080`.

A temporary browser tab verified the built Vehicle empty state and Session:
the configured staging domain is now already visible while certificate
inspection is in progress. The read completed with the same certificate domain;
no configuration was selected or changed. The temporary tab was closed, and the
operator's existing tab was preserved without forced reload. It needs Reload UI
or a page reload to pick up the new bundle. VMs, services, CARLA and Cloud were
not restarted or mutated.

`git diff --check` passes, including the new correction report. No temporary
runtime binary or configuration was installed. The prior audit's isolated
characterization harness remains in its recorded temporary directory; permanent
regressions now live with the owning UI/reader suites. Existing build caches,
Factory images and evidence remain unchanged.

The retired Test remains absent. This correction pass is not a new live version,
offline, Reset or Finish cycle. Historical source-order R2, broader P8 and
separate guest-reboot evidence remain as previously recorded. The retained 2.10
mockup is unchanged; the accepted specification records these amendments.
