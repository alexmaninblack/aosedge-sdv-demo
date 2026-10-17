<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Audience surfaces and interaction ownership

This register allocates visible surfaces and preserves stable I0 decisions.
The [interaction specification](aosedge-demo-interaction-specification.md) owns
exact UI rules; [traceability](aosedge-demo-ui-traceability-register.md) connects
them to requirements and acceptance cases. Read
[the baseline](../../qualification/current-baseline.md) for implementation/proof.
Directory names do not require a mockup or prototype as a runtime dependency.

## Installed composition

One Test, one OEM and one associated SP use the integrated Presenter beside
native CARLA and Driving Control/Telemetry. Actor/component cards, contextual
dialogs and release actions preserve product independence. Native control owns
motion, maneuvers, Safe Stop and Return to road; Presenter owns no vehicle or
Cloud authority. Stop/Start preserves Test; confirmed Finish retires it.

Expanded Validation/Production promotion, separate SP organizations and the
full qualification dossier remain explicit design obligations. They are not
additional installed processes, mandatory screens or proof of implementation.
CPU load/isolation is a planned proof, not an enabled service feature.

## Interaction decision allocation

Each stable decision below has one canonical detailed owner. No version-by-
version review narrative or competing presentation baseline is retained here.

### <a id="i0-dec-001"></a>I0-DEC-001 — Linear audience interaction

Keep live native evidence visible beside factual producer context. Navigation cannot impose a global release state machine or fabricate a missing dependency.

Detailed owner: [D4-026-7](../../requirements/d4-decision-register.md#d4-026-7).

### <a id="i0-dec-002"></a>I0-DEC-002 — Independent producer contexts

Platform, Brake and Tire retain separate ownership and resource identities. Installed mutations serialize; expanded disjoint-resource concurrency preserves exact conflicts and run-exclusive operations.

Detailed owner: [D4-026-10](../../requirements/d4-decision-register.md#d4-026-10).

### <a id="i0-dec-003"></a>I0-DEC-003 — Vehicle and update-state presentation

One selected source/vehicle context is independent of actor navigation. Native Safe Stop gates Platform FOTA; moving QM SOTA retains all other authority/readiness checks.

Detailed owner: [D4-026-8](../../requirements/d4-decision-register.md#d4-026-8).

### <a id="i0-dec-004"></a>I0-DEC-004 — Validation and released operation

Test evidence, owning-team acceptance, OEM authorization and expanded Production operation are different decisions/facts. Expanded promotion reuses accepted bytes without another product test.

Detailed owner: [D4-026-9](../../requirements/d4-decision-register.md#d4-026-9).

### <a id="i0-dec-005"></a>I0-DEC-005 — Action and authoritative result

Name the actor and exact target; keep intent, local operation, external result and function evidence separate. Reconcile uncertainty before another effect; no browser keys or hidden auto-approval.

Detailed owner: [D4-026-10](../../requirements/d4-decision-register.md#d4-026-10).

### <a id="i0-dec-006"></a>I0-DEC-006 — Details, isolation and logs

Read-only detail preserves context and source/freshness. Quota proof is not a Details field; native logs remain optional, role-scoped and bounded without another archive.

Detailed owner: [D4-026-11](../../requirements/d4-decision-register.md#d4-026-11).

### <a id="i0-dec-007"></a>I0-DEC-007 — Failure, offline and recovery

Scope failure to its owner and give a factual reason/safe next action. Vehicle external loss is not presenter Cloud failure. Unknown, stale and measured zero remain distinct.

Detailed owner: [D4-026-12](../../requirements/d4-decision-register.md#d4-026-12).

### <a id="i0-dec-008"></a>I0-DEC-008 — Live evidence correlation

Correlate native vehicle event, service decision, backend receipt and display by exact scope/source times. Receipt time is not a new event or a latency benchmark; replay is not live proof.

Detailed owner: [D4-026-13](../../requirements/d4-decision-register.md#d4-026-13).

### <a id="i0-dec-009"></a>I0-DEC-009 — Traceability and acceptance

All stable UI interactions map to upstream requirements, owning surfaces and acceptance cases. Mechanical fixtures, API proof and visible/native UI qualification remain separate verdicts.

Detailed owner: [D4-026-14](../../requirements/d4-decision-register.md#d4-026-14).

### <a id="i0-dec-010"></a>I0-DEC-010 — Manufacture, provision and retirement

Installed Create makes one Test; Provision connects its same identity/source; Stop preserves it and Finish retires only owned data. Expanded use additionally requires independent Production manufacture and retirement.

Detailed owner: [D4-026-15](../../requirements/d4-decision-register.md#d4-026-15).

### <a id="i0-dec-011"></a>I0-DEC-011 — Independent releases and derived milestones

VDP, Brake and Tire retain separate release objects and acceptance. G3/G4 summarize observed compatible graphs; no combined approval, Campaign or automatically advanced release is introduced.

Detailed owner: [D4-026-16](../../requirements/d4-decision-register.md#d4-026-16).

### <a id="i0-dec-012"></a>I0-DEC-012 — Workspace and header ownership

The host owner places native/browser windows; Presenter owns factual content/navigation. Workspace state is separate from the vehicle journal and restores no Cloud authority.

Detailed owner: [D4-026-17](../../requirements/d4-decision-register.md#d4-026-17).

### <a id="i0-dec-013"></a>I0-DEC-013 — Global demo controls

Installed runtime/Stop/Start/Finish controls reuse existing owners. Expanded qualification and lifecycle views add evidence, not a second orchestrator or automatic next run.

Detailed owner: [D4-026-18](../../requirements/d4-decision-register.md#d4-026-18).

### <a id="i0-dec-014"></a>I0-DEC-014 — Actor context and scrolling

Keep selected context and readable native evidence stable. Installed integrated cards/dialogs replace mandatory five-stage scrolling cards; view state never substitutes for fresh owner facts.

Detailed owner: [D4-026-19](../../requirements/d4-decision-register.md#d4-026-19).

### <a id="i0-dec-015"></a>I0-DEC-015 — Icons and native evidence boundary

Icons/colour supplement readable labels without changing evidence semantics. Native Driving Control/Telemetry is not a browser rendering or required text-only Terminal dashboard.

Detailed owner: [D4-026-20](../../requirements/d4-decision-register.md#d4-026-20).

## Audience-Visible Surface Register

| ID | Surface | Actor and purpose | Authoritative source | Protected action owner | Disposition |
| --- | --- | --- | --- | --- | --- |
| <a id="ui-i0-001"></a>`UI-I0-001` | Presenter Workspace Shell / Vehicle Controller | Presenter starts and ends the local session, sees readiness and current stage, opens and physically arranges the measured header/native/browser workspace, restores only its local layout, and selects accepted Scenario/Manual/Autopilot controls | Local launcher/window/process probes and measured display profile for composition; run journal while needed; Gateway/controller state and current authoritative stage reads | `CMP-ORCH`/session helper own physical composition and host operations; `CMP-SW-DASH` owns shared-header meaning; Gateway/controller own vehicle controls | Extend the existing native macOS panel without redesigning its controls; no content, Cloud or lifecycle authority |
| <a id="ui-i0-002"></a>`UI-I0-002` | CARLA Scene | Audience sees the physical vehicle, obstacle and braking behavior | Live CARLA world and selected actor | Scenario Controller/Gateway, not the browser | Existing surface reused; no redesign and no invented telemetry overlay |
| <a id="ui-i0-003"></a>`UI-I0-003` | Engineering Telematics Dashboard | Presenter/audience sees live vehicle telemetry, drive context, source freshness and Brake/Tire advisory return | Read-only authenticated Gateway/VISS stream | No lifecycle action; accepted vehicle-control actions remain in `UI-I0-001` | Native Driving Control/Telemetry with factual source/advisory rows; no required Terminal renderer |
| <a id="ui-i0-004"></a>`UI-I0-004` | OEM Software Delivery Dashboard | Platform Team and OEM presenter inspect candidates, Units/Sets, effective recipients, validation evidence, approvals, lifecycle/log state, qualification status and R0 | AosCloud APIs plus immutable local candidate catalogue and bounded local operation state | Platform Team protected publication; owning team acceptance; OEM `oem-delivery` confirmation for Unit-affecting actions | Integrated Presenter lifecycle/contextual release view; expanded governance separately scoped |
| <a id="ui-i0-005"></a>`UI-I0-005` | Brake Health Function Dashboard and Release Client | Function Team 1 selects prebuilt Brake v1-v3, sees metadata/quota/data contract, explicitly signs/publishes and observes current-run Brake results | Immutable Brake catalogue, protected `brake-sp1` publication result and Brake backend | Function Team 1 for release decision/publication; OEM remains separate for deployment approval | Independent function cards/dialogs; standalone backend shell is a component fixture |
| <a id="ui-i0-006"></a>`UI-I0-006` | Tire Health Function Dashboard and Release Client | Function Team 2 selects prebuilt Tire v1, signs/publishes, observes tire condition/advisory and inspects the separate planned CPU-isolation proof | Immutable Tire catalogue, protected `tire-sp2` result, Tire backend and factual qualification inputs | Function Team 2 for release/publication and bounded load request; AosCore alone enforces quota | Independent function cards/dialogs; standalone backend shell is a component fixture |
| <a id="ui-i0-007"></a>`UI-I0-007` | Qualification Status panel | OEM presenter sees whether the exact baseline is ready for an audience and why not | `.local/qualification/qualification-status.json` derived from the current sealed dossier and baseline comparison | No lifecycle authority; human withdrawal is separately authenticated/reviewed | Allocated qualification surface, not an implemented automatic health verdict; no separate evidence browser |
| <a id="ui-i0-008"></a>`UI-I0-008` | Native Helper status | Presenter sees only whether the protected local operation boundary is available | Authenticated launcher-to-helper health probe | Native helper; caller cannot select credentials, paths, profiles, URLs or arbitrary commands | `READY/UNAVAILABLE` indicator inside `UI-I0-001`; no helper UI |
| <a id="ui-i0-009"></a>`UI-I0-009` | Native AosCloud UI | Technical reviewer may inspect the upstream product when explicitly requested | AosCloud itself | Native AosCloud roles | Optional technical reference; not part of the normal core flow and not mocked as project UI |

## Required state semantics

Every surface labels its owning source, exact scope and observation freshness.
Requested, pending, installed, function-ready and Gateway-applied states stay
distinct. Missing, stale, failed, uncertain and measured zero are not collapsed
into healthy/offline. A protected action exposes target and consequence; private
paths, tokens, keys and raw credentials never enter audience content.

Qualification surfaces retain ABSENT/STALE/WITHDRAWN/NOT_QUALIFIED outcomes;
there is no manual green override. Planned isolation tests retain NOT_READY,
INCONCLUSIVE and FAIL and cannot display PASS without exact native evidence.
Optional detail never displaces the core story or changes its lifecycle.

## Native evidence and shutdown

One actor/tick owner supplies real motion. Native Driving Control handles
Manual/Autopilot, Brake/Tire maneuvers, Safe Stop and separate Return to road.
Reset Driver Advisory is service-local and preserves history. At session end
use Stop demo and keep data, then close windows; leave shared Docker running.
Closing Presenter alone is not runtime shutdown. See the
[operator workflow](../../operations/current-demo-workflow.md).

## Maintenance

Keep these stable allocation IDs linked to their canonical rule and acceptance
case. Current implementation/proof remains in the baseline. Prior visual
iterations and review chronology are retained in Git, not another active
mockup, requirement copy or installation prerequisite.
