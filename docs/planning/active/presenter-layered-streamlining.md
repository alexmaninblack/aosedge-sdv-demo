<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Layered Presenter implementation and qualification packet

Status: operator accepted, 26 October 2026; implementation in the separate
`codex/presenter-ui-stability` branch. Main and public option A do not advance
until the successor's review. This packet supersedes the previous visual
proposal, not its qualified immutable media or retained evidence.

## Accepted product contract

The owning [installed interaction contract](../../demo/mockups/aosedge-demo-interaction-specification.md#ui-studio-026--current-test-studio-contract)
and [D4 presentation decisions](../../requirements/d4-decision-register.md#d4-026-8)
remain authoritative. This is a presentation change, not another state store,
orchestrator, data interface or authority.

- Vehicle uses the **Layered** architecture. Independent Brake/Tire services
  sit side by side above their shared VDP capability inside one ARM64 virtual
  controller. AosCore is the platform runtime/lifecycle foundation, not another
  telemetry hop. Factory supplies the Linux/AosCore base; it is not an app.
  Vehicle/Gateway, both product backends and Aos Cloud remain outside that
  controller boundary. Retain the existing B2 miniatures and team colours.
- Platform navigation and VDP use the same component miniature. The hardware
  miniature denotes only the controller. Tabs keep Vehicle/Platform/Brake/Tire.
  Tabs open authoring contexts; installed nodes open read-only installed details.
- Keep Installed on this Test separate from Selected package. Only an exact
  reported pending target/active operation supports waiting-for-installation
  language. An earlier published selection is not a requested downgrade; release
  number order alone cannot establish supersession. Keep unknowns explicit.
- Local power/runtime, Cloud connection/report freshness, backend Now, retained
  assessment and native advisory remain independent facts. Retained values keep
  their source dates; unavailable reads do not mean absence, zero or Offline.
- One contextual primary action; repeat preparation is secondary. Preparation,
  signing/publication, first assignment and installation remain separate gates.
  Completion offers results; Stop/Start and Delete remain discoverable in Session.
- Setup owns normal paired Cloud configuration. Presenter shows access facts
  read-only. Exceptional existing repair/inspection controls remain disclosed
  under recovery; opening Session never initiates certificate inspection.
- One bounded detail surface and explicit Back for a child record/software item.
  Preserve its parent view/filter/scroll/focus rather than stack detail modals.
  Confirmation is still separate and names the target and consequence.
- Backend Now and Last assessment are separate. Neutral model-score display,
  humane state labels, compact history with current/earlier-release filters and
  distinct Loading/Empty/Unavailable/Last known states. Historical completed Reset
  receipts move to history; pending/uncertain/current-release outcomes stay visible.
  No data deletion, deduplication or hidden truncation; keep bounded-read notices.
- Operations shows the active job once and completed receipts newest first.
  Keep failures and technical evidence inspectable. Full identifiers remain on
  the server. Routine reports never move the fixed shell or reset profile input.

## Scope and protected material

Writable: Presenter source/tests, its interaction/readme documentation and the
existing M1 qualification selectors/assertions necessary for the accepted UI.
Do not change service algorithms, freshness/timeout policy, Safe Stop, native
driving authority, Cloud endpoints/owners, command guards or at-most-once protocol.
Adjacent Setup/native findings remain separately owned, not silently fixed here.

Preserve current/rollback DMG, retained Test and working disk, all data/history,
certificates, release ledgers, ready CARLA/Factory inputs and verified caches.
Build/packaging/scratch remain on SDV-Dev. M1 uses its internal storage. Docker
is reused without routine Engine restarts. No public distribution or merge yet.

## Ordered gates

| Gate | Work and acceptance | State |
| --- | --- | --- |
| 1. Contract/source | Update installed interaction text; implement all accepted review groups together with state/navigation regressions | Implemented; a captured Cloud inventory clipping correction follows the installed source freeze |
| 2. Local verification | Unit/type/static/docs/confidentiality gates; no developer-Mac browser or runtime | 390 Presenter unit tests, type/web compilation, 92 Python and 46 JavaScript qualification tests, docs and source gates pass |
| 3. M1 visual fixtures | One semantic fixture scenario on M1; layered boundaries, icon mapping, child navigation, state/geometry assertions | 154/154 pass after the captured Cloud row correction, no skips/retries/flaky tests; 39.889 seconds; browser and fixture server closed |
| 4. Immutable media | Freeze successor source; warm Setup/DMG assembly with existing CARLA/Factory and authorized signature | Canonical chain 17/17 built in 768.850 seconds; matching-M1-team media assembled in 540.183 seconds |
| 5. Retained update | Normal package update and launcher selection on M1; exact signature/capacity and unchanged Test/data bindings | Pass for the frozen `.2` candidate; Test and data retained |
| 6. Complete API/UI | One scenario owns ordered API observations then complete visible UI, real independent effects, source-specific statuses, Platform publication checks, Reset/offline/moving-SOTA/Stop-Start and cleanup | Not complete: retained VM dependency/startup failures stop API acceptance; full UI not run |
| 7. Review handoff | Before/after screenshots, timings and explicit PASS/FAIL/NOT_RUN map; preserve Test/data; close owned check runtimes | Partial screenshots and failed attempts retained; final owned runtime closure confirmed; no acceptance or promotion |

Use normal scripted entries under [qualification](../../../scripts/qualification/README.md).
The agent launches the scenario; routine steps do not wait for agent clicks.
Reconcile an uncertain action without replay. A failure closes later gates until
its bounded cause is corrected. No predecessor's passes qualify successor bytes.

## Source acceptance matrix

The captured audit groups map into this one packet: UX26-01 selected package;
02 access ownership; 03 deduplicated summaries/Layered; 04 action hierarchy;
05 Now/assessment; 06 retained history; 07 one detail surface; 08 operations;
09 read-state vocabulary; 10 names/metadata/spacing; 11 lifecycle guidance.
UX26-12 is adjacent Setup/native work and excluded explicitly.

Required negative regressions include: older selection without pending evidence;
stale assignment; missing profile binding; no initial loading-as-empty; Cloud read
failure while local runtime remains running; source-specific offline; partial
backend history; wrong-release result; pending/uncertain Reset; no navigation
mutation; no automatic certificate inspection; one detail dialog; stable anchors.

## Source-gate evidence

The M1-only source fixture campaign covers the canonical 876×908 composition
and compact/tall viewports. It verifies actual peer/shared/base geometry,
unclipped Reset controls, original icon mapping, one visible detail surface and
Back, scoped installed-versus-selected labels, retained records and source-specific
freshness. A current input report must not hide a conflicting product record or
remove the last-known qualification from an incomplete assessment. A late receipt
must not refresh the input source. These are explicit regressions, not changed
readiness rules.

Back uses the original record's presentation reference, not its old row number,
when background receipts change history ordering. If that row is no longer in
the visible page, focus returns to Records rather than another record. The
background-insertion regression was reproduced before correction and passes
with the final source; no history or data authority changed.

Short-screen history uses compact pagination; retained rows are not deleted.
The fixture harness now awaits its asynchronous monitoring read and permits one
normal five-second idle owner poll before asserting an externally changed job.
No product polling interval or freshness limit changed. Earlier failed fixture
attempts remain private, immutable diagnostics; they are not successor acceptance.

The retained-Test, desktop, Cloud and matching signing identity preflight passed
on M1 before media work. The operator completed the exact M1 keychain helper;
the continuation independently reconciled its signature without signing again.
No private key was exported or password recorded.

## Installed successor and qualification boundary

Final Presenter source is `45de82c5241387bf2a5b2a2e587529099f6713bd`;
the reviewed selection is `c2c463c` in this branch. Candidate version is
`1.2.0-rc.4-presenter.2`, application manifest
`bb81fda0338e159477affdae6abcca4bf6aff9f5ffaee12f6962669e42b3e473`.
The canonical local-development-signed DMG is 14,159,627,471 bytes, SHA-256
`a33845d34f3eb8e3683f43c59c4e77acd8e30e1ec49f5756b8f98d2a2511a0cd`.
That original development-team image is not the matching-team installed media.
The M1-team review DMG is 14,158,457,969 bytes, SHA-256
`378863973e01cb65fad2262ea69a61d0515c77795b9e371f325d3779d2fc418d`.
Its application manifest and runtime bytes are unchanged. Neither image is a
qualified public release.

Before the successful build, normal content revalidation handled only the
same SSD's remount device-number change; original receipts and payloads were
preserved. A subsequent first-source build was interrupted with owned cleanup
when the background-insertion focus regression was reproduced. Neither attempt
was delivered or installed, and neither supplies successor runtime acceptance.

The first media continuation found the predecessor `.1` DMG still occupying
the review mount. No new installation had occurred. Read-only reconciliation
proved the exact old mount and zero open handles; normal detach and the normal
new-media owner then completed the retained update. Original failed records
remain separate. Delivery took 172.637 seconds. The install/selection owner
took 250.236 seconds, including 128.874 seconds for install and 75.057 seconds
for selection; media verification accounts for the remaining time.

The installed API attempt passed ten steps before connection failed with
`SOURCE_GUEST_UNAVAILABLE`; shutdown also remained unresolved initially. The VM
was SSH-reachable. Its KUKSA databroker could not bind port 55555 because
`rpc.mountd` owned it, causing VDP/Service Manager startup failures. Bounded
runtime recovery preserved the NFS exports/configuration, restored mountd and
started the databroker. The same held initial-Manual operation was reconciled,
not replaced; fresh authenticated connection and normal shutdown were observed.
This is a transient environment recovery, **not** a permanent Factory fix.

A separate API attempt after recovery passed eight startup checks, then the
controller-start operation returned `PARTIAL`. Normal shutdown passed. Its total
campaign time was 121.226 seconds. Preserve this as another failed attempt,
not a successful retry or complete API result. No new release publication or
full UI sequence was reached. The final probe confirmed zero demo processes and
listeners; observer browsers and display assertions were closed. Shared Docker,
the retained Test, credentials, VM/data, immutable media and caches are preserved.

The visible API observer captured 497 presentation samples with zero fixed-shell
movement/error findings. This is limited startup evidence, not full-flow UI
acceptance. A captured three-component/two-service Cloud summary also exposed a
22-pixel row containing 30 pixels of text when inventory became last known.
The regression was reproduced on M1 before correction. The source-only layout
correction reallocates the same fixed card height; it changes no data or status
semantics. All 390 unit tests, type/web compilation and 154 M1 browser fixtures
pass after this correction, with no skips, retries or flaky tests. It is
**not included** in the frozen `.2` media above.

Before another immutable-media/full campaign, close these bounded items:

1. Own the native VM startup work separately: prevent the NFS/KUKSA port collision
   without disabling an in-use dependency or weakening policy, and preserve its
   cold-start/restart proof. No Factory rebuild is authorized by this packet.
2. Retain the exact reason for partial controller startup, distinguish a running
   guest from completed whole-demo startup, and qualify normal continuation without
   replaying an uncertain action. Do not silently increase timeouts or call a warm
   prestart a cold-start proof.
3. Freeze/package the verified Cloud row correction only after those native gates
   close, then complete the new candidate's API and continuous visible UI campaign.

Main and option A remain unchanged. Adjacent native startup work, a fresh Setup
first use, notarized distribution and the deferred VDP timeout are not qualified
or silently included by this Presenter packet.
