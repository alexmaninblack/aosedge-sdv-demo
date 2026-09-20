<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter displayed-fact corrections

Date: 19 September 2026. Status: implemented, local regression gates passed,
and updated Presenter activated. Live demo qualification is not claimed.

## Authorization and preserved state

The operator requested corrections for all findings in the
[UI truth audit](presenter-ui-truth-audit-2026-09-19.md): F1–F7, L1–L2 and
O1–O7. One writer changed the Solution repository's Presenter, bounded backend
reader, regression tests and documentation. HEAD at entry is
`d2298ba2f283896717c8cd8aa123fc1c76149782`; extensive pre-existing dirty sources
were preserved. No commit/push, VM/image/service rebuild, package publication,
Cloud mutation, backend data deletion or simulator restart belongs to this pass.

## Corrections and evidence boundaries

| ID | Source correction | Regression boundary |
| --- | --- | --- |
| F1 | Separate latest result receipt from Backend checked; preserve source date in detail and last-known qualifier on card/dialog. Compact cards show age with exact timestamp tooltip. | Old receipt/current check, stale native binding, no invented expiry or proof. |
| F2 | Shared component-pending/status label in overview, detail and Platform guide. Missing version remains unknown; errors retained. | Downloading/installing/pending without expanded version; failure/stale/completed, authoring guard. |
| F3 | Preserve per-instance numeric Aos/exit errors; generic Service issue is not automatically called an update failure. Running rejects conflicting errors. | Failed/active plus codes, valid zero codes. |
| F4 | Cloud checked/Last successful Cloud read replaces Cloud report for API-read timestamps. | Fresh and retained read wording; no fabricated device timestamp. |
| F5 | Offer the actual alternate disk metric; Disk selects it when usedDisk has no samples and disk is current. | Missing usedDisk/current disk; raw unitless values/partition retained. |
| F6 | Exact-event window Refresh with snapshot check time; scope validation on every response. | Late 1/2→2/2 chunks; wrong release/instance fails closed. |
| F7 | V1 recording explanation separate from health model estimate. | V1 acquisition and V3 model labels. |
| L1 | Ten-second aggregate backend observation budget, at most three seconds per HTTP exchange, including streaming body watchdog; no retry. | Selective slow resource, multiple timeouts, cancellation on success, real loopback dribble fixture. |
| L2 | Per-resource product retention, independent function/reset outcomes and explicit partial-read notice. | History or reset failure cannot hide a valid current function report; incomplete product/reset reads cannot prove the story. Foreign/malformed input still rejects the read. |
| O1 | Next in the demo names the team/result even on a different authoring page. | Tire page can truthfully name the next global Brake result. |
| O2 | Dismissible, at-most-60-second acknowledgement from an existing completed retirement receipt. No new persistence. | No acknowledgement from absence, wrong/missing receipt or expired receipt. |
| O3 | Known no-controller cards/dialogs show setup state, with visible empty service slots. | Not-created is distinct from failed observation. |
| O4 | Accessible meter label: Demo model condition score. | Same model meaning as visible explanation. |
| O5 | Resource detail names exact node and Subject as well as service/instance/partition/parameter. | Similar service rows remain distinguishable without summing. |
| O6 | Product detail shows supplied condition, previous condition, score, recommendation, operation, event, reason, quality/confidence. | Preserve zero and only display actual fields. |
| O7 | Unproved service path is labelled Configured data path; retained result is separately labelled. | No candidate/Test is not called connected real telemetry. |

The backend timeout change stays within nine fixed owned loopback endpoints,
the existing size caps and scope checks. It changes no backend schema or retry
policy. Timed-out and not-attempted-after-budget resources are unavailable;
they are never successful empty pages. Partial reset/history cannot establish
fresh input or complete story proof. A fresh function report still needs exact
native scope, generation/sequence, profile and the unchanged 90-second bound.

The compact window and summary layouts were checked after extra status text
exposed overflow. Spacing and age presentation were adjusted, not fonts or
model/evidence contents. The full source/receipt dates remain in detail.

## Verification

| Gate | Result |
| --- | --- |
| Presenter unit tests | 261/261 passed across 24 files. |
| Presenter browser fixture tests | 117/117 passed, including compact/responsive dialogs, stale binding, status-only pending and partial backend reads. All API traffic in these fixture tests is intercepted; this is not live Cloud evidence. |
| Related Demo Control tests | 111/111 passed: backend reads and budget, Presenter, protected operations, Studio Cloud reader, Cloud observation and Presenter performance. |
| Real loopback slow-body fixture | Passed; an ephemeral test server dribbles response bytes and the scoped watchdog terminates the read within the asserted bound. No live backend is used. |
| Production build and type checking | Passed; assets `index-gXI-mt1i.js` and `index-DaPK5ALo.css`. |
| Patch whitespace check | `git diff --check` passed. |

Before activation, the owned Presenter server reported no active or uncertain
operation. Its guarded `ui stop` command stopped only that idle UI server;
`ui serve` then started the tested sources on `127.0.0.1:18080`. VMs, Cloud,
simulator and services were not restarted or changed.

A separate temporary browser tab verified the built Vehicle page: both team
cards show `No controller created` / `Ready for setup`, Cloud shows
`No Cloud Unit yet`, service slots are empty, and the Brake popup explains that
no vehicle data is expected before setup. The temporary tab was closed. The
operator's existing tab was not force-reloaded and needs Reload UI/page reload
to load the new bundle. Native-window visual verification was not possible
while macOS was locked; browser and fixture checks do not claim that coverage.

## Remaining qualification

No active Test remains from the .36 cycle. These synthetic fixtures are not
live service/advisory or version/offline qualification. Historical source-order
R2, broader P8 branches and separate guest-reboot engineering evidence retain
their recorded status. Factory .35/.36 and all published releases are unchanged.
The retained mockup 2.10 is not overwritten; the interaction specification owns
these accepted implementation amendments.
