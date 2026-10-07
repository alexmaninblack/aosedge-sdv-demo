<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Documentation reconciliation — Kit028 / Setup042

- Status: documentation reconciliation; no new runtime or live-test verdict
- Version: 1.0
- Prepared: 2026-10-07
- Owner: SDV Lab integration
- Source checkpoint: candidate/kit028-setup042, integration commit b6600cf
- Candidate: Kit028 / Setup042 / Factory .41

## Result and reading order

Use [the current baseline](current-baseline.md) for selected artifacts and proof,
[installation](../getting-started/installed-preview-cloud-first-use.md) for the
operator entry, [workflow](../operations/current-demo-workflow.md) for the demo,
and [implemented architecture](../architecture/current-implementation.md) for
requirements-to-source mapping. The [protocol map](../../contracts/implementation-status.md)
separates current wire behavior from retained design profiles.

The previous front doors mixed the September demo-v1.1/Factory .39 checkpoint
with October installer code and results. This revision makes the current
candidate explicit without changing old tags, images, source locks or receipts.
Project documents remain English. Video, Unreal/CARLA upstream manuals and
licensed/reference material are outside this edit scope.

## Coverage and method

The [file inventory](../../workspace/checkpoints/documentation-inventory-2026-10-07.json) covers 412
previously tracked Markdown files across seven project repositories before
adding this report. It records each path, document class and edit disposition.
It is a scope inventory, not 412 passed semantic tests.

| Repository | Markdown files inventoried |
| --- | ---: |
| Solution integration | 331 |
| Vehicle platform | 29 |
| Gateway / Driving Control | 27 |
| Brake service | 13 |
| Tire service | 4 |
| Brake backend | 6 |
| Tire backend | 2 |

Review followed the canonical HLA → Scenario → Flows → System Requirements →
Component Register → thirteen component packages, then runtime/product and
distribution contract maps, operator/developer instructions, active-plan
pointers, component entry documents and dated evidence indexes. Current-state
claims were checked against source, executable profiles and candidate records.
Stable identifiers and accepted obligations remain intact.

Historical research, qualification and execution notes are preserved with
their original dates and results. They are not rewritten to suggest a test
passed on a later candidate. Unchanged specialist references were screened for
current-baseline conflicts; this was not a fresh proof of every individual
requirement, protocol edge case or visual mockup.

## Corrected discrepancies

| Area | Previous discrepancy | Reconciled documentation |
| --- | --- | --- |
| Baseline | .39/v1.1 presented as today's installer | Kit028/Setup042/.41 and exact source/media records; old tag explicitly historical |
| Installation | Early offline-only preview mixed with later capabilities | Real Setup button sequence; separate install, select, backend preparation, Cloud access and Presenter launch |
| Operator prerequisites | Editor/developer checkout looked necessary | Prebuilt DMG route separate from source builds; Apple silicon/macOS 26+, Docker and access prerequisites explicit |
| Cloud topology | Two separate SP accounts implied for first use | One associated SP, separate Brake/Tire identities and lifecycle; expanded two-provider design preserved |
| Native return path | Open demo could be read as a full cold resume | Presenter only; missing native Power on action explicitly recorded |
| Evidence | Earlier .39-only gaps or synthetic-only analytics presented as current | 98 installed scripted steps and partial native observations distinguished from incomplete full E2E |
| Lifecycle/UI | Presenter README still advertised Park/Resume | Safe Stop pause, distinct ignition and destructive Finish; no automatic Autopilot |
| Runtime provenance | Generic/unmodified KUKSA wording hid retained patches | As-built scope-path and original-source-timestamp corrections explicitly separated from upstream target |
| Tire quotas | Requirement/catalog prose still said 150 DMIPS, 32 files, 8 processes | Existing signed-profile candidate is 600 DMIPS, 1024 files, 16 processes; freshness unchanged and isolation proof still open |
| Ownership | Docker dashboard operation confused with engine readiness | Reuse running engine; import exact backend images explicitly; normal shutdown does not stop Docker |
| Planning | Historical “next” actions appeared current | One distribution checklist; retired M1 Test not described as retained; current/native gaps preserved |
| Component docs | Six repositories pointed at different old integration checkpoints | Shared current baseline and source lock, with dated component evidence preserved |

### Change classification and traceability

This is a **corrective documentation reconciliation**, not a new architecture
decision. Existing authority comes from ADR 0015/0016/0017/0018, UI-STUDIO-026,
the accepted installed-workstation cascade and dated D4 amendments.
The Tire resource correction propagates the already authorized 3 October
D4-023 Level-B envelope amendment into stale component/catalog prose. It does
not newly accept 600 DMIPS as a production-qualified limit or change any JSON.

The owning HLA/Scenario/Flows/System/Register implementation views and derived
component status maps were revalidated against that chain. Their accepted
semantic versions and stable IDs are retained: no new obligation or authority
is introduced. Original quota trials and review states remain dated provenance.
No requirement or test obligation is retired simply because it is unimplemented.

### Source and evidence used

- [Source return point](kit028-setup042-source-publication-2026-10-05.md),
  [source lock](../../workspace/checkpoints/installer-kit-028-source-lock.json),
  [candidate results](../../workspace/checkpoints/installer-kit-028-candidate.json)
  and [Factory .41 record](../../workspace/checkpoints/factory-41-candidate.json).
- [Native Setup](../../scripts/distribution/native/Setup.swift),
  [dispatch](../../scripts/distribution/setup_bridge.py),
  [backend preparation](../../scripts/distribution/setup_backends.py),
  [launch](../../scripts/distribution/setup_launch.py) and
  [complete-media builder](../../scripts/distribution/full_dmg.py):
  actual controls, ownership and action boundaries.
- [Brake runtime profile](../../contracts/brake-health-runtime/brake-health-runtime-profile.v1.json)
  and [Tire product profile](../../contracts/tire-health-model/tire-health-product-profile.v1.json):
  current requested quota values, not measured usage.
- [Boot recovery owner](../../apps/demo-orchestrator/src/aosedge_demo_orchestrator/source_boot_recovery.py),
  [runtime-input placement](../architecture/demo-control-service-inputs.md)
  and [platform compatibility](../../../aos-vehicle-platform/docs/contract-compatibility.md):
  recovery, credential and source-time boundaries.
- [M1 journey](m1-live-journey-2026-10-03.md): serial releases, offline/ignition,
  native observations, deferred readiness and later retirement.

## Remaining discrepancies and work — not hidden by wording

1. **Native acceptance:** moving SOTA, secure native token entry, full operator
   journey and target-host interruption/repair remain open.
2. **Returning stopped Test:** no native Power on action. Engineering
   restoration is not native acceptance; the product flow still needs a decision
   and implementation under the existing plan.
3. **Installer experience/distribution:** the complete DMG is not the finished
   guided wizard or persistent launcher. Local Apple Development signing is
   not Developer ID/notarization or public redistribution approval.
4. **Executable Tire cleanup drift:** the legacy two-UID schema/profile differs
   from the implemented Test-scoped handler. Use the
   [current wire description](../../contracts/tire-cloud-api/studio-current-wire.md).
   Versioned schema/profile/fixture synchronization remains controlled work;
   this audit does not silently change pinned wire data.
5. **Qualification scope:** fixed-load CPU control/worker D4-023 is not
   implemented; complete calibration, negative/resource, nonempty-outbox power
   loss and expanded production/dual-provider matrices remain separate.
6. **Deferred/excluded:** VDP-TIMEOUT-01 and brief load-sensitive readiness are
   deferred. Laptop sleep/wake and external SSD are excluded from this M1
   internal-disk campaign, not proven by controller ignition.
7. **Historical visual references:** old Draw.io/PNG and mockups retain the
   expanded design, not a screenshot of the current one-SP installation.
   Their scope is labeled; no visual source or frozen export was regenerated.

No new accepted behavior is inferred from an unexplained code difference.
The published tag/DMG continue to contain their original documentation;
this working-tree revision accompanies them until separately committed and,
if needed, included in a future package.

## Validation

Validation on 7 October:

- Documentation quality gate: PASS — 329 Markdown documents, 662 stable
  identifiers, 38 Mermaid diagrams. Navigation, anchors, canonical metadata
  and traceability checks passed.
- Integration repository suite: 759 tests run in 41.027 seconds; 758 passed,
  one skipped. This includes documentation and executable-contract regression
  checks; it is not a new installed/live E2E run.
- Component lock validation: PASS; no component/source/artifact pin changed.
- Whitespace/error checks: PASS in all seven edited repositories.
- Changes are documentation plus this audit's inventory only. Runtime code,
  executable JSON profiles/schemas, source locks and delivered media unchanged.

The inventory was initially placed under documentation, where the gate rejects
JSON artifacts. It was moved to the existing workspace checkpoint directory;
the gate then passed without relaxing any validator.

No simulator, VM, Docker, Cloud operation, installer build, image deletion,
live qualification or video edit was performed. No commit, push or release tag
was created by this documentation task.
