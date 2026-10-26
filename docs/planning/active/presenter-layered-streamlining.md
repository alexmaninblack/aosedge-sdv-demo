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
| 1. Contract/source | Update installed interaction text; implement all accepted review groups together with state/navigation regressions | Complete; successor media remains unqualified |
| 2. Local verification | Unit/type/static/docs/confidentiality gates; no developer-Mac browser or runtime | 390 Presenter unit tests, type/web compilation, 92 Python and 46 JavaScript qualification tests, docs and source gates pass |
| 3. M1 visual fixtures | One semantic fixture scenario on M1; layered boundaries, icon mapping, child navigation, state/geometry assertions | 152/152 pass, no skips/retries; 41.185 seconds; browser and fixture server closed |
| 4. Immutable media | Freeze successor source; one warm Setup/DMG assembly with existing CARLA/Factory and authorized signature | Not run |
| 5. Retained update | Normal package update and launcher selection on M1; exact signature/capacity and unchanged Test/data bindings | Not run |
| 6. Complete API/UI | One scenario owns ordered API observations then complete visible UI, real independent effects, source-specific statuses, Platform publication checks, Reset/offline/moving-SOTA/Stop-Start and cleanup | Not run |
| 7. Review handoff | Before/after screenshots, timings and explicit PASS/FAIL/NOT_RUN map; preserve Test/data; close owned check runtimes | Not run |

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
on M1 before media work. Its SSH login keychain is locked: matching-team signing
may require secure local input. No private key is exported or password recorded.
Full installed API/UI gates below remain **not run** until successor media exists.
