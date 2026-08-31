<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 AosCloud Read-Only Presenter Adapters Work Packet

- ID: `WP-P1-UI-AOSCLOUD-READONLY-ADAPTERS-001`
- Lane: `L-UI` / Demo Interface Train
- Increment: bounded fixture-first slice of `IMP-06`
- Review state: `IMPLEMENTED — FIXTURE-ONLY READ PROJECTION INTEGRATED / LIVE TRANSPORT DEFERRED`
- Version: 0.5
- Prepared: 2026-08-29
- Authorized: 2026-08-30
- Rebaselined: 2026-08-30
- Completed and integrated: 2026-08-31
- Initial implementation authorization: yes, only after the synchronized entry
  gate below passed
- Initial packet exclusions: network access, live Cloud/backend access,
  credential use, helper execution, signing, publication, VM/Unit operation and
  SOTA/FOTA. Later local build, commit and integration evidence is recorded
  below.
- Orchestration input:
  [Consolidated Implementation Execution Trains](../infrastructure-first-critical-path-proposal.md)
- Completed shell input:
  [`WP-P1-UI-001`](p1-ui-presenter-shell.md)

## Objective

After one consolidated Demo Interface Train authorization, extend the
completed fixture-only Presenter shell with one
typed, fixture-first read projection for:

1. authenticated AosCloud session role, owner binding and effective
   permissions;
2. the exact current Test and Production Unit, Main Node and persistent role
   Unit Set bindings;
3. Unit reported connection/software state, pending Verification Batch
   references, Verification Batch, Fleet Validation Batch and Campaign reads;
4. role-scoped native Unit-log and Brake Service-log request states; and
5. current-Unit Brake Backend windows, assessments, events and advisories.

The slice normalizes deterministic contract fixtures into the existing
Presenter read model and visibly preserves source, source time, observation
time, freshness classification, partial/unavailable/error state and redaction.
It does not implement an HTTP transport, hold a credential, contact AosCloud
or the Brake Backend, request/download/delete a log, or submit any mutation.
Every displayed fixture remains explicitly labelled **fixture — not live**.

This packet is deliberately smaller than complete `IMP-06`. It proves the
read model, source ownership and fail-closed routing before a later packet
selects and qualifies a browser-safe local transport. It neither implements
nor authorizes `IMP-07` protected actions.

## Repository, Base and Isolation

| Item | Frozen value |
| --- | --- |
| Solution/product repository | `aosedge-sdv-demo` |
| Exact future branch base | `ebc144fd95e4a0f9485ddb9c4ab91834ee227388` |
| Required relationship | clean `main`, exact commit above; completed Presenter shell commit `106d340a6fe2e945de055642f2e016355ea6cf91` must be an ancestor |
| Presenter shell tree | `90abac62816a879060a0d793081726c9cf72b4aa` |
| Proposed future branch | `codex/imp-06-readonly-adapters` |
| Proposed isolated worktree | sibling `../aosedge-sdv-demo-imp-06-readonly-adapters` |
| This proposal's writable boundary | this work-packet file only |

The synchronized solution base is clean and contains the accepted `.21`
Factory baseline, live demo Cloud topology, Brake v2 contract cascade and
successor launcher. A future worker creates the isolated worktree from the
exact committed base rather than copying product or generated files from
another checkout.

## Frozen Inputs

All repository file digests in this table are the exact accepted bytes after
solution governance commit `ebc144fd95e4a0f9485ddb9c4ab91834ee227388`. Presenter-shell
identity remains the accepted ancestor
`106d340a6fe2e945de055642f2e016355ea6cf91`.

| Input | Version / identity | SHA-256 |
| --- | --- | --- |
| Consolidated execution trains | synchronized authorization record, 2026-08-30 | `e97a2c597ff1039685bbc70fcde1171c4a2cc28c8f33d87bdd623c4d961071e2` |
| Presenter shell completion packet | `WP-P1-UI-001` 0.3 | `e918ced919eed551b539c8bd85e905cda8e2c0b0f4a80429b6788b542609b426` |
| Presenter lockfile | shell commit `106d340a`; Node 26.0.0 / npm 11.12.1 | `fcb9e6114b021dfa02f93a76d453f2ca06980c780947dbe38ac9a5d378a7364c` |
| Presenter architecture test | shell commit `106d340a` | `e4b603477473374ff9d3dd2c75cc6044e1683f124c475dad34d733ed2fee3948` |
| Interaction Specification | 2.5 | `2adf18fd5037590f55fe2895a4945bcdb53504f74943c8d5f31f0c104d4c7235` |
| UI Traceability Register | 1.1 | `84cb86ba668b13fb979b1b1df219761a49ed410856629fde712051001cd63bd3` |
| `CR-DEMO` | 1.1 | `a67e2d37f0f37127b6596a1d1c0e06d36edab7707927878d30da4a5867a02d43` |
| `CR-AOS` | 0.4 | `485a66ee27287475d7144e01721c5ccbff99b2792cb57fc07124747b43eb50e2` |
| D4 Decision Register | D4-011, D4-012, D4-014, D4-021 and D4-026 | `91842de2ec12a8f802a9bc2ae402e2db77af76ccf9d248ca1a44463a3943e556` |
| Component/interface register | `CMP-SW-DASH`, `IF-LC-005`, `IF-OBS-001`, `IF-FUNC-002` | `b37205720325f127b9d4a020e64c75f97af18ae58ee74c40abe9fc168c7d0dc3` |
| AosCloud lifecycle research | API v11 implementation 6.1.26 | `dac5e0804dc45cbeefeb9afa2c89b8675174f59e3d3c1790445d032e439d5f65` |
| R6.1 source lock | includes OpenAPI 3.0.3 observed 2026-08-14 | `cf945d31882d5e54c15b57cec675c754779b203343b2e9f49bca243f0345c0af` |
| Frozen AosCloud OpenAPI bytes | v11 / implementation 6.1.26 | digest recorded only: `a587d7a308cb7c9ea0d274f1c5f2ff4ae3a99e2e492b753436ae6c9e2dbf508a` |
| Demo Run State README | D4-021 / 1.1.0 | `e111fef168e3e27cc0745aeb3409edc6470f430ce1a5c576ccb1dea3635d0bdd` |
| Demo Run State profile | 1.1.0 | `3cc284f15b0b81f2c145b64e813c6081e255cf74b883f8feb6111db4bf47dcf2` |
| Brake Cloud API README | Query/SSE/Admin 1.0.0 | `41d5ced4bb51108c898e165fbe7b9a9f81d0024219fd28299e5bb705e7135a56` |
| Brake Query/SSE/Admin profile | 1.0.0 | `2b04089106b8263ff1efd68240623168f4dcf9d1bf6d92748ed253a3ba8ad29c` |
| Brake query-page / error / SSE schemas | 1.0.0 | `17b13d55462e97ca2011391e1ce78e272124839b1851cfcf675ad9434d802c38`, `53ff0a6073f6d3eb51e67165d62bdc512bcd98c2d200690f8607ee146d4ea30b`, `7e8bccc76167722910e9c671f46223caf53708a29758587906a4afcac4356d1b` |
| Current Unit context schema / fixture | 1.0.0 | `f5733d7750b2fbda863201f66503e40f97c146f426ff4ec290f195efdcca4681`, `c9b623b368dd17053a94fbc612375f8aae14d2e99026325a4ce9cb5c5742d022` |
| Brake window / pending-VDP event fixtures | 1.0.0 | `8ab6af3c6f82c2333d7339f0b8453a83031de76c4159aee338290eedbd01f9c9`, `3056242db14d4c97a7cbf1e33fe6e388c8a6447b6bccb471407869db9d2b49b6` |
| Brake error / SSE fixtures | 1.0.0 | `a5b59e4166d14479e912817a8a776f99c0a90699c6c17737cd3f0a759d08c1d6`, `34f0a3707bdc37f888bfdd481b22d5d374880da677dc1d50bd57d9e93cf6f488` |

The source lock records the exact OpenAPI digest but the repository contains
neither those bytes nor closed endpoint-specific AosCloud response fixtures.
That blocks live wire-shape and account claims, but it does not block this
fixture-only projection: contract-synthetic fixtures validate the closed local
records below and are never represented as captured AosCloud responses.

## Existing Shell and Required Delta

The completed shell already provides one `PresenterReadPort`, one immutable
`PresenterSnapshot`, deterministic fixture selection, a `SourceStamp`, a
fixture-only action preview and architecture tests that reject `fetch`,
`XMLHttpRequest`, `WebSocket`, `EventSource`, browser persistence and excess
runtime dependencies. The fixture `SourceReference` is currently restricted
to `fixture: true`, and the general observation model currently exposes
`CURRENT`, `STALE`, `UNAVAILABLE` and `ERROR` only.

The smallest coherent next slice is therefore not a second application or a
live client. It adds source-specific contract records and pure normalization,
extends the observation vocabulary to the accepted interaction states, and
composes an immutable Presenter snapshot through the existing port. The
existing fixture adapter remains available for shell regression tests.

## Exact Future Product Writable Boundary

After separate authorization, only the following paths may be changed or
created. No directory-wide wildcard is granted.

1. `apps/presenter-ui/src/domain/model.ts`;
2. `apps/presenter-ui/src/domain/index.ts`;
3. `apps/presenter-ui/src/domain/sourceObservation.ts`;
4. `apps/presenter-ui/src/adapters/read-only/contracts.ts`;
5. `apps/presenter-ui/src/adapters/read-only/aosCloudReadModel.ts`;
6. `apps/presenter-ui/src/adapters/read-only/brakeCloudReadModel.ts`;
7. `apps/presenter-ui/src/adapters/read-only/composePresenterSnapshot.ts`;
8. `apps/presenter-ui/src/adapters/read-only/FixtureReadOnlyAdapter.ts`;
9. `apps/presenter-ui/src/adapters/read-only/fixtureCatalog.ts`;
10. `apps/presenter-ui/src/adapters/read-only/index.ts`;
11. `apps/presenter-ui/src/app/composition/createPresenterDependencies.ts`;
12. `apps/presenter-ui/src/shared/components/SourceStamp.tsx`;
13. `apps/presenter-ui/src/features/evidence-overlays/DetailsDialog.tsx`;
14. `apps/presenter-ui/src/features/evidence-overlays/OperationalLogsDialog.tsx`;
15. `apps/presenter-ui/src/features/global-lifecycle/GlobalLifecyclePage.tsx`;
16. `apps/presenter-ui/src/features/brake-team/BrakeTeamView.tsx`;
17. `apps/presenter-ui/tests/unit/architecture.test.ts`;
18. `apps/presenter-ui/tests/unit/readOnlyAdapters.test.ts`;
19. `apps/presenter-ui/tests/unit/fixtures.test.ts`;
20. `apps/presenter-ui/tests/unit/domain.test.ts`;
21. `apps/presenter-ui/tests/unit/components.test.tsx`;
22. `apps/presenter-ui/tests/browser/ui-at-fixture.spec.ts`;
23. `apps/presenter-ui/tests/browser/ui-at-read-only-fixtures.spec.ts`.

`package.json`, `package-lock.json`, generated output, current contract files,
existing fixture-adapter files and every shared planning/requirements file are
read-only. Any need for another file, an executable proxy/helper, an HTTP
transport, configuration, a credential reference, a new package or a lockfile
change stops implementation and requires a bounded packet revision.

## Adapter and Composition Interfaces

All interfaces are framework-independent TypeScript values. They expose no
URL, certificate, token, password, header or raw response to a React
component.

### Read request plan

`ReadRequest` is a closed discriminated union with:

- one `source` of `AOSCLOUD_OEM`, `AOSCLOUD_BRAKE_SP1` or `BRAKE_BACKEND`;
- one fixed `routeId` from the tables below;
- `method: "GET"` only;
- exact opaque object selectors supplied by the fixture context;
- required complete-pagination state where the contract is paginated; and
- no arbitrary path, query name, body, header, host or credential field.

`FixtureReadOnlyAdapter.read(plan, context, clock)` returns immutable
source-specific fixture records. The pure `aosCloudReadModel` and
`brakeCloudReadModel` normalizers validate their closed fixture shape and
produce `Observed<T>` projections. `composePresenterSnapshot` joins them by
the exact role/Unit/release identities and creates a new snapshot. It must not
mutate the previous snapshot or keep an authoritative cache.

`PresenterReadPort.subscribe` remains a notification seam only. A fixture
notification causes a complete source reread. It never carries authoritative
state and never changes a source fact by itself, matching the accepted Brake
SSE contract.

### Source records

The fixture records must keep these layers separate:

| Record | Required facts | Never inferred or stored |
| --- | --- | --- |
| `SessionObservation` | route, role, owner binding, exact returned `effective_permissions`, source time/read time | permission from role name, publication authority, credential material |
| `CurrentUnitBinding` | Test/Production role, `system_uid`, Cloud Unit UUID fingerprint, Main Node UUID fingerprint, exact Unit Set UUID fingerprint | wire `VALIDATION` role used as an audience vehicle label, VIN, full private identifiers in ordinary view |
| `UnitObservation` | exact verbatim connection/reported state, source time, desired/actual component and Service identities, pending batch references | demo G-state as a Cloud field, functional health from connection state |
| `UnitSetObservation` | persistent set identity, `is_validation_set`, complete paginated member Unit UUID set | title as identity, Node UUID as member, incomplete-page success |
| `ReleaseObjectObservation` | distinct candidate, Verification Batch, Fleet Validation Batch and Campaign IDs/states/targets/results | one combined approval, automatic owner/OEM decision, invented Campaign recipient |
| `NativeLogObservation` | exact scope, request ID fingerprint, verbatim Cloud state and source time, sanitized metadata only | raw/free-form content, second archive, retention duration, mutation result |
| `BrakeFunctionalObservation` | exact current Unit role/UID, resource type, source/backend times, delivery/projection state, nullable VDP provenance and query error | Unit readiness, Cloud lifecycle, run ID, source-generation or comparative-success claim |

## Strict Read-Only Role and Route Matrix

The route context is chosen by application composition and cannot be selected
by fixture data, a component or a query parameter. Names ending in `-read` are
logical fixture routing labels, not credentials.

| Logical route context | Allowed reads in this packet | Explicitly forbidden |
| --- | --- | --- |
| `oem-delivery-read` | `GET /api/v11/users/me/`; paginated Unit list; Unit detail; Unit-owned Node list/detail; Unit subject-services; Unit Set list/detail/membership; Verification Batch list/detail; Fleet Validation Batch list/detail; Campaign list/detail; Unit-log list/detail metadata | every `POST`, `PATCH`, `PUT`, `DELETE`; publication profiles; Service-log scope; raw log download; arbitrary URL |
| `brake-sp1-read` | `GET /api/v11/users/me/`; Brake-owned Service-log list/detail metadata only | Unit/system log scope; OEM lifecycle or other-provider data; raw log download; every mutation |
| `brake-backend-read` | four accepted `/api/v1/brake/units/{systemUid}/{windows|assessments|events|advisories}` collections for exactly one Unit from `CurrentUnitContext`; fixture notification followed by complete REST reread | ingestion, cleanup/admin socket, health-as-Unit-readiness, arbitrary Unit, state-bearing SSE, every mutation |

The `oem-delivery-read` fixture must prove `users_me` and the returned owner,
role and `effective_permissions` appropriate for every requested read. A role
name alone never implies permission. A `brake-sp1-read` fixture must prove the
Brake owner and matching `service_logs_*` read permission. Cross-route data is
rejected before projection.

The browser receives only the sanitized projection and logical source label.
It never receives, chooses or transmits a Cloud certificate, PKCS#12 path,
private key, token, password, `Authorization` header or helper capability.

## Unit, Node, Unit Set and Release Semantics

1. `Test Vehicle` is the only user-facing label for the technical Validation
   Unit. The wire/journal role remains `VALIDATION`; the persistent technical
   set remains `Verification Unit Set`. `Production Vehicle` maps to
   `PRODUCTION` and `Production Unit Set`.
2. The fixture context contains exactly two distinct `system_uid` values and
   their exact Cloud Unit, Main Node and persistent Unit Set bindings from the
   current-run provisioning journal. It contains no Cloud lifecycle truth;
   each Cloud fact is separately reread.
3. Main Node identity must be observed as a child of its Unit but is never a
   Unit Set member. Set membership is normalized to Cloud Unit UUID and must
   consume every fixture page.
4. Exact current membership is Verification=`{VU}` and Production=`{PU}`.
   Crossed, duplicate, prior-run, absent, additional, truncated or ambiguous
   membership is `INCOMPLETE` or `UNKNOWN`; it cannot be presented as current.
5. Verification Batch, Fleet Validation Batch and Campaign remain distinct
   objects. Pending component recipients come from Unit detail; pending
   Service recipients come from complete subject-service pages. Membership
   alone never proves effective recipients.
6. The accepted unresolved live Campaign spelling/timing anomalies remain
   visible fixture variants. A fixture must not choose `unit_ids` versus
   `units_ids` as proven live truth or invent per-Unit preview timing.
7. Friendly M0/M1/G0/G3/G4/R0 and owning-team acceptance presentations remain
   explicit derived/local layers. They are never serialized as AosCloud state.

## Source, Freshness, Error and Redaction Model

### Observation state

The accepted closed audience condition is:

`CURRENT`, `STALE`, `UNKNOWN`, `INCOMPLETE`, `REDACTED`, `NOT_APPLICABLE`.

Each observation additionally carries source owner/class, source timestamp if
provided, local read-completion time, an injected freshness-policy identifier,
and at most one sanitized reason. Transport/error classification is separate:

`AVAILABLE`, `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND_OR_INACCESSIBLE`,
`REJECTED`, `SCHEMA_INVALID`, `SOURCE_UNAVAILABLE`, `MALFORMED`.

No error is converted to `CURRENT`. A prior value may remain visible only as
`STALE` with its original observation time and `Current state cannot be
confirmed`. A source with no accepted prior value projects `UNKNOWN`. One
source failure affects only its owned groups; an AosCloud failure may affect
several Cloud-backed groups but never marks CARLA, Gateway or vehicle external
connectivity offline. Brake Backend failure does not change Cloud Unit state.

### Frozen error mapping

| Fixture outcome | Projection |
| --- | --- |
| `401` | `UNKNOWN` + `UNAUTHENTICATED`; no role/permission fact retained as current |
| `403` | `UNKNOWN` + `FORBIDDEN`; preserve only the sanitized route/scope reason |
| `404` | `UNKNOWN` + `NOT_FOUND_OR_INACCESSIBLE`; absence is not proven without independently established visibility |
| `400` | `UNKNOWN` + `REJECTED` |
| `422` | `UNKNOWN` + `SCHEMA_INVALID` |
| timeout, connection loss or fixture source unavailable | prior value `STALE`, otherwise `UNKNOWN`, plus `SOURCE_UNAVAILABLE` |
| malformed, duplicate-key, unknown-enum or incomplete-page fixture | `INCOMPLETE` or `UNKNOWN` + `MALFORMED`; never partial success |
| accepted Brake `UNIT_NOT_CURRENT` | source-local `UNKNOWN`; no fallback to another Unit |
| accepted Brake `CURRENT_UNIT_CONTEXT_UNAVAILABLE` | Brake groups `UNKNOWN`; no stream/notification authority |

### Freshness

Fixture tests use an injected clock and an explicitly named fixture policy;
they do not call the wall clock or sleep. Numeric Cloud-object and Brake-view
freshness windows are not yet frozen by the accepted contracts. Until that
decision is closed, fixtures may exercise explicit `CURRENT` and `STALE`
classifications but product code must not hard-code a duration or promote an
old value based only on local receipt time.

### Redaction

Allowlisting occurs before a value enters `PresenterSnapshot`. The browser may
receive role labels, public semantic versions, non-secret digests, sanitized
object fingerprints, documented state strings, source times and reviewed
reason codes. It may not receive credentials, certificate content, PKCS#12 or
key paths, auth headers, VIN, full Unit/Node/`system_uid` or private Cloud IDs
in the ordinary view, raw API response bodies, arbitrary error text, backend
cleanup tokens, raw/free-form log text or another provider's data.

A required hidden fact is `REDACTED`; it is not absent, empty or CSS-hidden.
The fixture secret-negative test scans both serialized raw fixture inputs and
the complete rendered browser state.

## Native Log Read Presentation

This packet models read-only log-request metadata only. It preserves the exact
Cloud states `created`, `sent`, `waiting unit`, `receiving`, `done`, `error`
and `empty log has been provided` verbatim. `empty log has been provided` is a
factual empty result, not a transport failure.

Platform/OEM sees only `unit-logs` through `oem-delivery-read`; Brake sees only
Brake-owned `service-logs` through `brake-sp1-read`. The view always states
`Retention policy not exposed by current API` and never claims fixed or
indefinite retention. Create/request, raw download, parsing, temporary-file
handling and deletion remain outside this fixture-first read packet because
they are protected operations or require a browser-safe sanitizer/transport
contract not yet frozen.

## Brake Backend Projection

1. The accepted `CurrentUnitContext` supplies exactly current Test and
   Production `systemUid` values and roles. The adapter may select only one of
   them per query. It performs no Cloud lookup and infers no Unit state.
2. Current Unit with no data is a truthful `200` empty page. Non-current Unit
   is `404 UNIT_NOT_CURRENT`; missing/invalid context is
   `503 CURRENT_UNIT_CONTEXT_UNAVAILABLE`.
3. The fixture adapter validates the closed page shape, exact resource type,
   Unit/role match, limit and cursor handling. It preserves source time and
   `backendReceivedAt` without computing cross-clock latency.
4. Window projection remains hidden until authoritative start; partial and
   terminal states are presented factually. A durable receipt is not a
   terminal result.
5. Event VDP version/digest remain null with
   `PENDING_ASSESSMENT_CORRELATION` until exact accepted assessment
   correlation. Nearby records or Service version never fill them.
6. A notification carries no state. Every notification, reconnect, gap or
   backend restart causes the fixture model to discard continuity claims and
   reread all affected REST collections.
7. `/health/live` and `/health/ready` describe only backend process/database
   readiness and must never become AosCloud Unit or Service readiness.

## Required Fixture Package

After consolidated train authorization, the fixture package must include
deterministic, closed objects for:

- valid Test/Production session, Unit, Main Node and disjoint Unit Set binding;
- no Unit before M1, Unit `Online`, Unit `Offline`, missing/ambiguous Unit,
  wrong Main Node, crossed/duplicate/prior-run membership and truncated pages;
- component and Service pending-recipient exact match, extra PU, missing VU,
  stale batch and incomplete visibility;
- distinct Verification, Fleet Validation and Campaign states plus both
  unresolved Campaign response-shape variants;
- `/users/me/` valid OEM, valid Brake SP1, wrong role, wrong owner, missing
  permission and the exact `400`/`401`/`403`/`404`/`422` classes;
- every documented native-log state, wrong log family/owner, empty result,
  unauthorized/inaccessible record and redacted field;
- Brake empty current Unit, complete/partial window, pending/correlated event,
  pagination/cursor, notification/reread, backend unavailable, wrong Unit and
  invalid context cases; and
- mixed-source atomic/current, stale, unavailable, malformed, incomplete,
  redacted and not-applicable presentation groups.

Synthetic contract fixtures must say `CONTRACT_SYNTHETIC` and never claim to
be captured live response evidence. Sanitized captured fixtures, if approved,
must retain their source OpenAPI digest and capture provenance while containing
no credential or private identifier. Fixture content must not be selected by
the UI to force a success verdict.

## Required Fixture-Only Verification

An authorized implementation must use the existing exact lockfile and add no
dependency. With dependency materialization separately allowed from the
already verified local cache, the required commands are:

```text
npm ci --ignore-scripts --offline
npm run typecheck
npm run test:unit
npm run test:browser
```

The relevant test obligations are `UT-DEMO-004`, `UT-DEMO-005`,
`UT-DEMO-007`, the read-only part of `UT-DEMO-011`, and `UI-AT-004`,
`UI-AT-006`, `UI-AT-007`, `UI-AT-008`, `UI-AT-014`–`018`, `UI-AT-020`–`025`,
`UI-AT-027`–`029`, `UI-AT-032`, `UI-AT-035`, `UI-AT-040`–`043`,
`UI-AT-046`, `UI-AT-048` and `UI-AT-050` only where the fixture-first read
slice owns their source presentation. Mutation, live transport and human
qualification portions remain open.

Tests must prove:

- exact GET-only route/role allowlists and compile-time/runtime rejection of
  every other method, route, arbitrary URL and cross-owner request;
- full pagination, exact identity joins, Test Vehicle mapping and all Unit,
  Node, Unit Set, pending-recipient and lifecycle-object negatives;
- the closed source/freshness/error/redaction mapping, partial-source
  independence and no hidden success;
- exact Brake contract fixtures, REST-after-notification behavior and no Unit
  readiness inference;
- no `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, browser storage,
  service worker, credential field, raw response, helper capability, mutation
  method or new runtime dependency anywhere in the owned source;
- no second lifecycle, desired-state, approval, Unit, batch, Campaign,
  functional-data or log store; and
- all existing shell unit, component, browser, architecture and full-screen
  fixture regressions remain passing.

Tests are deterministic, inject time, use no network and do not sleep. A test
must not silently skip because live Cloud, a browser credential or a backend is
absent; those are intentionally outside this packet.

## Dependency Impact

No new runtime or development dependency is allowed. `package.json` and
`package-lock.json` remain byte-identical to the completed Presenter shell.
The slice uses TypeScript discriminated unions, immutable objects,
`structuredClone` where already used, React, Vitest, Testing Library and the
existing Playwright installation only.

No schema generator, OpenAPI client, HTTP library, state framework, cache,
database, SSE library, credential SDK, redaction package or fixture download
is introduced. Any claimed need for one is a stop condition and design review,
not an implicit dependency authorization.

## Explicit Exclusions

- no actual AosCloud, Brake Backend, Internet, LAN or loopback request;
- no browser or Node HTTP transport, proxy, BFF, helper or credential broker;
- no certificate, PKCS#12, private key, token, password or authentication
  header access;
- no `POST`, `PATCH`, `PUT`, `DELETE`, log request/download/delete, Unit Set
  write, approval, validation, Campaign, provisioning, retirement or cleanup;
- no signing, publication, SOTA, FOTA, VM, Unit, QMP, CARLA, Gateway or live
  source operation;
- no mutation preview, dry-run that could reach an external source, operation
  journal or reconciliation state machine;
- no Tire Backend adapter or Tire Service-log implementation;
- no raw log display, second log archive, functional-data copy or second
  lifecycle/state database;
- no invented OpenAPI response field, Campaign recipient/timing fact, Cloud
  lifecycle state, numeric freshness window, production authentication or
  retention duration;
- no container/static bundle packaging, ARM64 image, deployment or live
  qualification;
- no shared implementation-plan, requirements, D4, traceability or docs-index
  cascade under this proposal; and
- no stage, commit, push, merge or modification of `main`.

## Stop Conditions

Stop and return for review if:

1. the exact base, Presenter ancestor/tree, lockfile or any frozen input digest
   differs;
2. implementation attempts a live wire-shape, browser-safe transport, numeric
   freshness calculation or Brake Backend authentication behavior deferred by
   the safe-default bundle;
3. a response field/state cannot be traced to the frozen OpenAPI evidence,
   accepted D4/CR contract or Brake schema/fixture;
4. a requested route is not an exact allowlisted GET or needs a credential in
   browser state;
5. full pagination, role/owner/permission proof or exact current Unit binding
   cannot be established;
6. the slice needs to modify a path outside the exact 23-file boundary;
7. a package, lockfile, generated client, persistent store, network access or
   external operation appears necessary;
8. raw logs or arbitrary Cloud/backend error content would enter the browser;
9. fixture or existing Presenter tests fail; or
10. a concurrent change touches an owned file and cannot be reconciled without
    broadening behavior or overwriting another owner.

## Bundled fixture-only safe defaults

The consolidated Demo Interface Train authorization accepts these six
closures together. They deliberately defer every live transport or production
claim while allowing the closed read projection to be implemented and tested:

| ID | Bundled closure for this packet | Deferred live boundary |
| --- | --- | --- |
| `UI-RO-RD-01` | Validate only `CONTRACT_SYNTHETIC` closed local records traced to accepted contracts; do not invent, fetch or claim captured AosCloud wire fields. | Sanitized pinned OpenAPI/response evidence is required before a live adapter claims exact wire compatibility. |
| `UI-RO-RD-02` | Keep `FixtureReadOnlyAdapter` as the only transport and keep every credential/proxy capability absent. | A session-scoped loopback read proxy with fixed route contexts and pre-browser redaction requires a later packet. |
| `UI-RO-RD-03` | Carry named fixture policy IDs and explicit `CURRENT`/`STALE` inputs with injected time; hard-code no numeric age and enable no gate from freshness. | Source-owner durations are required before production freshness calculation. |
| `UI-RO-RD-04` | Model Brake notifications as fixture hints followed by a complete fixture REST reread; add no listener, origin, CORS or auth behavior. | Exact Query/SSE listener/auth/origin remains a live-transport decision. |
| `UI-RO-RD-05` | Project only the fixed sanitized metadata/state fields already listed; no raw text, body, download or arbitrary error crosses into the browser. | Native response bounds and sanitizer allowlist are required before a live proxy exposes metadata or preview. |
| `UI-RO-RD-06` | Preserve `unit_ids` and `units_ids` as negative/incomplete fixture variants; project no per-Unit preview timing or completion claim. | Account-bound 6.1.26 qualification must establish live spelling and timing. |

These defaults are frozen recommendations until the train is authorized. They
do not reopen the accepted authority, Test/Production terminology, Unit Set
isolation, no-second-store or read-only decisions.

## Completion Record

- The accepted product train over exact base
  `ebc144fd95e4a0f9485ddb9c4ab91834ee227388` is
  `a18f56908361a5f558068e1b192fbb7a364c9131`,
  `7c8d9064eec87efdd13bd95c71814314e4deb009`,
  `7fa4b1ca3c48cb5b4fdf761be1e54ad5d58e4e41` and final product tip
  `a8bc6d0c57a2f5d12112b5ab13beb0d24f53e420`.
- Every cumulative change remained inside the exact accepted 23-path boundary;
  `package.json` and `package-lock.json` remained byte-identical.
- Independent review accepted the final fail-closed projection. Offline
  dependency materialization, typecheck, unit, browser, architecture, quality,
  diff/boundary and credential/secret/storage/mutation-negative gates passed.
- The product train is integrated in solution `main`; the later documentation-
  only digest correction places current solution `main == origin/main` at
  `3d4c87fb6b74734c6a5ab36602f1bd745655ea6b`.
- The adapter remains `CONTRACT_SYNTHETIC` and fixture-only. It has no network,
  credential, helper, mutation, live AosCloud/Brake Backend or log-delivery
  capability.

`IMPLEMENTED` and `INTEGRATED` mean only that the accepted fixture read
projection and failure/redaction behavior are source-traceable. Live wire
shapes, browser-safe transport, account qualification, freshness windows,
credentials, log delivery, packaging and protected actions remain open; the
integrated demo is not yet qualified.
