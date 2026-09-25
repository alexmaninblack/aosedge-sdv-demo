<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Implementation and documentation audit — 24 September 2026

## Scope and authority

This audit follows publication of `demo-v1.1` and the Factory39 ignition,
offline and cleanup receipts. It changes documentation, not executable behavior,
Factory contents, service packages, Cloud state or the running demo. The tag
remains an immutable source return point. No new live qualification is implied.

The inventory covers 347 tracked Markdown files in seven owned repositories:
267 integration, 28 platform, 27 Gateway/runtime, 13 Brake service, six Brake
backend, four Tire service and two Tire backend documents before this update.
The complete tracked Markdown inventory was classified; detailed review covers
current entry points, all thirteen requirement packages, all 25 contract
families, implementation descriptions, active-plan summaries and latest receipts.
This is not a claim that every dated research transcript was revalidated line
by line against current upstream behavior. Dated reports and accepted design
are cross-referenced, not rewritten into claims that later work had already
passed. Upstream CARLA/Unreal documentation and the private video repository
are outside this documentation update.

Implementation is the source of truth for **what exists**. Accepted requirements
remain the authority for **what is required**; a missing implementation or test
does not silently remove a requirement. Historical architecture versions and
stable requirement/interface identifiers are preserved. The operator explicitly
confirmed demo-v1.1 / Factory39; the earlier mention of 1.8 is not a new release.

Change class: corrective implementation-baseline documentation, with no new
behavior or authority. Owners: integration and the six owned component
repositories. Requirements, HLA/Scenario/Flows semantics and frozen contracts
are revalidated through their accepted amendment maps, not version-bumped into
a new architecture. Retired identifiers: none.

## Implemented state and evidence

| Area | Implementation inspected | Evidence / limitation |
| --- | --- | --- |
| Source return point | Workspace and hosted CI dependency pins; `demo-v1.1` | [Return point](demo-v1.1-return-point.md); no image bytes or live state in Git |
| Factory/mainline | Platform recipes, validators and effective AosCore pins | [Factory39 build](factory-39-build-2026-09-24.md); mainline-derived with explicit retained patches, not stock upstream |
| Boot recovery | `source_boot_recovery.py`, source trust and lifecycle guards | [Ignition](factory-39-ignition-2026-09-24.md); same identities, stationary recovery; externalON only |
| Packaging and delivery | Component common runtime, unsigned preparation, selected-session signing, release allocator | [Operator workflow](../operations/current-demo-workflow.md); serialize version publication; FOTA Safe Stop distinct from SOTA |
| Local service chain | KAC, provider, Brake runtime profiles and Tire model/input contract | Actual KUKSA-derived .39 products; no synthetic fallback and no Cloud dependency for local input checks |
| Offline delivery | Independent durable service outboxes, backend receipts and IDs | [305.50-second OFF proof](factory-39-offline-2026-09-24.md); 33 assessment/advisory messages checked exactly; ten legacy Tire status messages have count/time evidence only |
| UI status and resources | `cloud_observation.py`, resource formatting/graphs, visible observer, backend observation and Reset views | Cloud authority separate from backend and native advisory; bytes/DMIPS, explicit freshness and instance binding |
| Native control | Gateway and native Driving Control implementation/tests | Real Brake/Tire maneuvers, Return to road, motion projection and bounded window placement; host sleep/wake still planned |
| Retention/cleanup | Current image catalog and dated cleanup inventory | [.39/.31 retained](factory-39-cleanup-2026-09-24.md); .36/.37/.38 binaries removed, evidence retained |

## Documentation discrepancies corrected

| Discrepancy | Correction |
| --- | --- |
| Current setup still described .33/.36, synthetic inputs or missing repositories | Current entry points identify .39 and the seven implemented owned repositories; old checkpoints remain dated evidence |
| Demo Control described as read-only and real permissions/advisory as future work | Current lifecycle, native authorization, products, advisory and delivery are documented with scoped proof |
| Park/Resume, raw controller ignition and laptop sleep/wake conflated | Normal pause is Safe Stop; Studio Park/Resume remains retired; .39 ignition is separately qualified; laptop recovery remains planning |
| Source reconciliation still called an open blocker after v1.1 publication | Published return point and immutable historical locks are distinguished from current workspace pins |
| Source/test success read as complete end-to-end acceptance | Source checks, image build, focused live tests and full all-version E2E are separate gates |
| Cloud graphs/units and backend/native statuses insufficiently explained | Operator guide states units, attribution, freshness, independent authority and private-network accounting limit |
| Reset and version/profile semantics ambiguous | Selected service model/advisory reset preserves history; allocated release number is not functional profile; Tire V1 is advisory-capable |
| Component/design and mockup allocation labels looked like today's delivery state | Historical design labels preserved with current implementation overlay; retained mockup is not the live UI contract |

## Updated documentation boundary

87 Markdown files were added or updated across seven repositories: 72 in the
integration repository, seven platform, one Gateway/runtime, four Brake service,
one Brake backend, one Tire service and one Tire backend. Five integration
files are new: this audit, the current operator workflow, the implemented
architecture matrix, the complete contract-family map and Tire's current-wire
supplement. No executable code, JSON profile, schema, dependency pin or image
was changed.

The [architecture/requirements matrix](../architecture/current-implementation.md)
connects every component package to its owner and proof scope. The
[protocol map](../../contracts/implementation-status.md) covers all 25 contract
families. Entry points, package baselines/open gates, interface status, runtime
and backend descriptions, scenario amendments and mockup-versus-live distinctions
are aligned with this current slice. Historical D3 snapshots and dated reports
remain explicitly historical, not competing current instructions.

## Open items — not fixed by editing documentation

1. Complete a fresh, strictly serial VDP V1→V2→V3 / Brake V1→V2→V3 / Tire V1
   cycle on .39, including final Finish. Focused reuse of 117/92/49 does not
   replace it; Factory39 remains `BUILT_NOT_LIVE_QUALIFIED` in its manifest.
2. Investigate short advisory readiness transitions and the reused VDP117
   installed/profile-not-confirmed Presenter observation. Do not hide them by
   relabeling unavailable as healthy.
3. Keep reconnect milestones separate: Cloud Online was observed within 8.13s,
   empty queues within 29.30s, with later function/UI freshness around 65s in
   the recorded .39 check. These are sampled upper bounds, not product SLAs.
4. Qualify cold ignition with externalOFF, nonempty-outbox power loss, longer
   soak and the remaining negative/recovery matrix before broader promotion.
5. Implement/qualify the accepted host sleep/wake recovery packet separately.
6. The historical VDP109 SIGSEGV has no captured root-cause core and was not
   reproduced by the later common-runtime checks. Temporary core capture was
   removed; absence of recurrence is not proof of its original cause.
7. Keep service calibration, standalone backend fixture dashboards and the
   broader CPU/negative test matrix distinct from the integrated Presenter and
   the actual live checks. The fixed Tire CPU isolation endpoint returns
   `501 NOT_IMPLEMENTED`; no CPU load worker is enabled.
8. **Executable Tire cleanup contract drift:** the retained profile/preview
   schema requires two UIDs and fewer record categories; the tested current
   handler permits current Test alone and ten categories. The [as-built wire](../../contracts/tire-cloud-api/studio-current-wire.md)
   records exact authority, selectors, fields and transaction behavior. Next
   maintenance step is a versioned contract/fixture synchronization with
   handler-generated responses, wrong selectors and peer-preservation negatives.
   Preserve old digest-addressed evidence and do not weaken the handler to fit
   the old schema. Static legacy contract-test success is not conformance of
   that current response.
9. Older three-container hosting, dual-Unit and full qualification-dossier
   designs are not the current host-Presenter/Test-only implementation. Their
   amendment map is explicit; generating clients or acceptance verdicts from
   an unamended legacy profile is not supported.

## Verification

Checks executed for this documentation audit:

| Check | Result / exact boundary |
| --- | --- |
| Integration unittest suite | PASS, 365 tests; also passed within the full boundary gate |
| Repository boundary gate, existing source-gate environment, allow-dirty | PASS: ownership/public-source checks, Platform and Brake source tests, eight Brake host CTests plus the separate V2 CTest, component-lock validation, Platform/Brake REUSE |
| Documentation gate | PASS: 269 scanned Markdown documents, 658 stable identifiers, 38 Mermaid diagrams |
| Changed-document cross-repository link existence | PASS: 2,761 local links, no missing paths at the recorded check |
| Brake backend | TypeScript compilation and 58 isolated backend tests PASS |
| Tire backend | 20 isolated Node 26 backend tests PASS, including current-Test cleanup, peer preservation, migration and observations |
| Whitespace / secret guard | Working diff checks in all seven repositories and tracked confidential-input guard PASS; all 87 changed/new Markdown files additionally passed direct working-file confidential-material and private-key/API-key marker checks |

The first integration-suite invocation used the orchestrator environment and
encountered three import errors because PyYAML was missing; the established
source-gate environment passed without product changes. Tire's first sandboxed
run passed 14 tests and could not start six loopback-listener cases
(`listen EPERM`); the authorized isolated rerun passed all 20. Neither was
reported as a live product regression or hidden by changing code.

Tests use synthetic temporary stores/listeners and host builds. They do not
contact the running demo or qualify Factory, Cloud or native CARLA behavior.
No VM/image build, ignition, Cloud package publication, provisioning, network fault, cleanup
of user artifacts, video edit or fresh E2E was performed. Existing warm caches,
Factory39, Production31 and both live/runtime data boundaries are preserved.
The immutable demo-v1.1 tag and release/dependency pins are unchanged.

At the 24 September audit handoff, this documentation correction remained local
for review, with no commit, push or tag movement. It is not a replacement release.

## Documentation publication — 25 September 2026

The user subsequently authorized committing and pushing the reviewed changes
to the seven repositories' existing `main` branches. The six component
documentation commits below have been pushed, with each exact commit verified
against the remote `main` ref:

| Repository | Documentation commit |
| --- | --- |
| `aos-vehicle-platform` | `a3eb9b63d9606c2020799cf20a75d01d8b829392` |
| `carla-ego-runtime` | `4e384798c95298a706709775c6fb33367edd00c6` |
| `brake-health-service` | `a52f462c2efa82f958f163a1e9abca226d9dea81` |
| `brake-health-cloud` | `7c64adf7b3d99535ecc7c8cbe468bc527cbcdc12` |
| `tire-health-service` | `0ddaf76ecb712b8c64f4f1e8ea91004a8c4ee611` |
| `tire-health-cloud` | `ea2d6deec9b704cb866d362eaefc9d87356ddeb5` |

The integration documentation is identified by the commit containing this
section. These documentation-only successors do not move `demo-v1.1`, change
its checkpoint or repin the implementation dependencies. Factory .39, the
running demo and Production .31 are unchanged. Git publication is distinct
from Cloud package publication and does not extend the qualification claims
recorded above.
