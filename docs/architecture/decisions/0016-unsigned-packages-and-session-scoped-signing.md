<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0016: Unsigned Packages and Session-scoped Signing

- Status: Accepted — implemented; offline verification and live staging publication passed; guest E2E blocked by missing staging Unit Sets
- Version: 1.1
- Prepared: 2026-09-15
- Owner: Demo Solution Team
- Change class: C — local source-artifact trust and publication-context separation
- Architecture input: [High-Level Architecture 1.7](../high-level-architecture.md)
- Scenario input: [Demo Scenarios 2.0](../../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Existing contract: [Certificate-selected Test Cloud](../certificate-selected-cloud.md)
- Delivery context: [Demo Studio delivery plan](../../planning/active/demo-studio-delivery-plan.md)

## 1. Accepted decision

Keep reusable package content unsigned and independent of a destination Cloud.
Prepare an immutable release, then use the currently selected OEM certificate
for a VDP publication or the configured, matching SP certificate for a service
publication. A different destination or signer creates a separate signed
representation of the same prepared content; it does not mutate that content.

The user approved implementation and isolated verification after this audit.
The existing Test remains parked while code and package tests run. This
amendment supersedes the historical-public-certificate requirement for normal
VDP preparation. It does not authorize a new live publication or claim staging
qualification; the operator resumes that run after the implementation handoff.

After the handoff the user separately authorized the agent to run live checks.
VDP, Brake and Tire publication reached Ready in the selected staging; Unit
provisioning stopped at the absent role-set preflight. See the
[verification receipt](../../qualification/unsigned-package-signing-2026-09-15.md)
for the evidence and the preserved Parked state. This does not expand the
Cloud-selection contract to automatic fleet or Unit Set creation.

## 2. Confirmed failure and current-session evidence

The OEM certificate was replaced for staging. Session successfully read and
explicitly applied the new domain. The subsequent `component.prepare` returned
`COMPONENT_ADAPTER_FAILED_InvalidSignatureError`.

The default `componentBaselineCertificate` points to `aos-user-oem.pem`, which
was also replaced with the new destination certificate. Prepare still verifies
the historical VDP input using this file. A read-only
`democtl component verify 1.0.16` reproduced the same failure. New bundle
signing and upload were not reached.

Read-only `democtl component inspect` confirmed all three retained inputs:

| Profile | Existing source version | Pinned signed-archive SHA-256 | Read paths | Inspection |
| --- | --- | --- | --- | --- |
| V1 | 1.0.16 | `b36e3064166739c98ec028fc75980bf4ea937d531a7e7a7889e11283dd1d7d9c` | 7 | No structural problems; digest matches the source pin |
| V2 | 2.0.0 | `8cea21f1280961f997fe38c724b346a1c4ee2cb246d7da660849afac87599450` | 15 | No structural problems; digest matches the source pin |
| V3 | 3.0.0 | `451965e1d03259a7edf66a4c742125c290f5efbfb2089530572395da2a1901fd` | 23 | No structural problems; digest matches the source pin |

These observations prove equality with already pinned bytes, not a new
cryptographic verification under the replaced certificate.

During the audit the operator completed Park. The Presenter and persisted
lifecycle receipt both reported `PARKED`, with `stop-simulation`, `stop-test`
and `stop-backends` complete at 09:23:14 UTC. The retained connection is Test;
the simulator had been running. Test has no Cloud Unit/Node identity, component
or service operation receipts, conflicting source operation or uncertain UI
operation. The selected staging domain and existing Factory .33 are retained.

The release high-water marks observed after the failed preparations were VDP
57.0.0, Brake 36.0.0 and Tire 24.0.0. They are observations, not recommended next
versions. Failed preparation may already reserve a number. Never roll it back
or ask the operator to fill a gap; use the normal allocator and destination
catalog when the next release is actually prepared.

## 3. Implementation audit and required changes

Paths below are relative to `apps/demo-orchestrator/src/aosedge_demo_orchestrator/`.

| Area | Actual behavior / gap | Required treatment |
| --- | --- | --- |
| Source trust | `components.py:prepare`, `component_worker.py:verify-baseline`, `status.py` require a historical PEM for pinned signed inputs | Convert only the three exact pinned inputs to canonical unsigned sources; verify source digest and structure without a historical key |
| VDP provenance | `component_build.py:PROFILE_BASES`, `replay`, `compose` and `_inspect` use signed-archive digests | Distinguish the legacy input digest, new unsigned-source digest and prepared-release digest; update consumers together, without changing V1/V2/V3 content |
| Artifact selection | `components.py:_bundle` prefers a signed archive whenever it exists | Separate prepared-content selection from signed-publication selection; changing credentials must not make an unrelated old signed envelope the Prepare input |
| VDP repeat signing | `sign` finds one signed output and verifies it with the currently selected credential | Make signing idempotent only for the same prepared digest and destination/signer context; a new context needs a new derived output |
| Service repeat signing | `service_packages.py:sign` has one `deployment-bundle.tar.gz` and one `signed.json` | Apply the same context-specific derived-output model to Brake and Tire, retaining the ordinary SP authority |
| Service destination binding | Service `prepared.json` stores `serviceProviderId`, `serviceId`, `cloudProfile` and `runId`; workers reuse them | Keep reusable payload provenance separate from destination owner/catalog identities. Resolve or validate the target binding in the publication context; never transplant another Cloud's IDs |
| Publication history | VDP current-run records are keyed by version; services use one `publication.json` per release | Bind attempt receipts and returned IDs to the selected Cloud, role/owner, prepared digest and signed representation. An uncertain attempt remains tied to its original context |
| Session switching | `CloudConnection.select` protects an already provisioned/used Test; changing a domain is not VM migration | Preserve that guard. Artifact portability does not authorize moving a provisioned Test or adopting another Cloud's Subjects. Package-local readiness and run-external receipts must be distinguishable |
| Version continuity | Prepare queries the selected catalog and durably reserves a version before all later work completes | Preserve monotonic allocation. Re-signing alone does not allocate a version. Reusing a version is valid only when the destination permits it; never overwrite an existing Cloud release |
| UI facts | Current service receipts and job results can represent one prior signing/publication context | Display Signed/Published for the active context only; invalidate stale job-derived readiness when selection changes. Installed/Running remain Cloud observations |
| Park/Resume | Park preserves disks and context; Resume uses existing Test and restores the source in stationary Manual | Preserve the parked journal and its successful stop checkpoints. Package tests must not resume, provision, reset or retire Test |
| Cleanup | Current-run retirement checks component receipts; source artifacts and version continuity are protected separately | Retain canonical unsigned source inputs and existing retention policy; retire only the owned run's disposable outputs. Do not turn cross-Cloud signing into an unbounded backup archive |
| Diagnostics | A raw `InvalidSignatureError` does not distinguish source trust, payload corruption or destination mismatch | Return bounded actionable diagnostics for each boundary; never expose PEM, PKCS#12 contents, keys, JWTs or raw signer output |

The service payload configuration already identifies a logical codename rather
than a Cloud UUID. The early SP/service binding is in the local prepared record
and worker requests; correcting it does not require replacing service binaries,
adding credentials to the payload or modifying AosCore.

## 4. Accepted artifact and signing contract

### Unsigned source and prepared release

- Canonical VDP source profiles are immutable, unsigned local build inputs in
  the existing artifact catalog, with reviewed digest/provenance metadata.
- A prepared package contains the existing upload configuration, payload and
  its version/architecture/profile metadata. Preparation records exact content
  digests independently of any signature envelope.
- Prepared content does not contain certificate paths, keys, Unit IDs, Subjects
  or destination service/owner UUIDs. Local runtime/publication receipts remain
  separate from reusable content.
- Prepare may still read the destination catalog for automatic version
  allocation. Unsigned does not mean every step of Prepare is network-free.
- Existing profile, release and CLI selectors remain. No arbitrary archive
  import, separate wrapper, new signing service or general package registry is
  introduced by this work.

### Signed representation and upload

- Existing `component sign <version>` and `service sign <handle>` select the
  current credential, check the proper OEM/SP authority and domain, and invoke
  the installed official Aos signer. UI Publish continues to compose Sign and
  Upload through the same core operations.
- A signed representation is identified locally by the prepared digest and
  destination/signer context. The frozen schema/path is below; the UI never
  constructs paths or handles private signer identities.
- Same context plus unchanged content is an idempotent reuse. A changed signer
  or Cloud produces a separate signature output from the unchanged unsigned
  content. The old certificate is not required to create that new output.
- Rotation at the same credential path must be detected. A path or domain
  alone is not sufficient signer identity. Any public-key/certificate identity
  used internally stays local and is not printed into public evidence or Git.
- Validate content before signing and verify the new envelope afterwards.
  Upload checks that selection and credential still match this representation
  immediately before its one external attempt. A changed selection blocks
  upload; it is not silently re-signed inside Upload.
- Keep the official deployment-bundle upload route and existing role, recipient,
  TLS and version checks. Never upload unsigned content to bypass Cloud checks.
- A prior accepted/uncertain upload is reconciled by its recorded destination
  and identifiers. It must not be replayed, overwritten or labelled successful
  just because another context has a signed file.

This is a portable artifact design, not a promise that every Cloud has suitable
accounts, catalog ownership, architecture, Unit Models, permissions or free
version numbers. Those target requirements remain independently observable.

### Frozen local schema and compatibility

All paths are under the existing artifact catalog; binaries and receipts stay
outside Git. New files use the following schema-1 representation:

| Object | Path / identity | Required content |
| --- | --- | --- |
| VDP source | `components/vehicle-data-provider/.source-profiles/<source-version>/package.tar.gz` and `source.json` | Exact unsigned inner archive; source version, reviewed legacy and unsigned SHA-256, `trust: REVIEWED_SOURCE_DIGESTS` |
| Prepared VDP | Existing release directory, unsigned archive and `prepared.json` | Existing immutable payload/file digests and profile; replay provenance adds `unsignedSourceSha256` while preserving legacy source provenance |
| Prepared service | Existing `services/<team>/releases/<version>/prepared.json` and payload | Existing file inventory and logical Cloud profile; no authoritative SP/service UUIDs in new prepared records |
| Signature | Release directory `.signatures/<context-digest>/deployment-bundle.tar.gz` and `signed.json` | `signingContext` contains schemaVersion, domain, role, signerId and preparedSha256; receipt records verified signed SHA-256 |
| Publication | Release directory `.publications/<destination-digest>/publication.json` | Domain, role and configured authenticated owner select the directory; immutable attempt owner, signed SHA, exact response ID and observations remain in the receipt |

Digests of objects use SHA-256 over sorted, compact JSON. VDP preparedSha256
hashes the unsigned archive; service preparedSha256 hashes its sorted file
inventory. Private signerId is the selected certificate SHA-256 fingerprint.
It is never an API/UI field. A cheap credential file-identity stamp only
invalidates local Signed display; it is not a cryptographic trust decision.
Sign/Verify/Upload use real verification and a per-worker private temporary
credential snapshot so replacement at the same path cannot change a worker's
key halfway through an operation. Normal completion removes the snapshot.

Publication directories deliberately exclude signer identity. Rotation must
not unlock a second POST for an accepted or uncertain attempt. Its recorded
owner is checked on subsequent reads; a different owner cannot adopt its IDs.
Service Upload, Cloud status and Deploy use the same destination resolver.
A legacy domain/role-only receipt is reused only for the same recorded owner;
missing owner provenance requires reconciliation rather than assignment.
Source/prepared content is shared across destinations, but publication status
is not. No automatic version allocation occurs during Sign or re-signing.

Legacy prepared content is readable. Unscoped old signatures are not active
signatures: explicit Sign creates the selected-context representation without
reading the old certificate. An attempted legacy service `publication.json`
without trustworthy destination provenance requires reconciliation; it is
neither silently adopted nor resent. Legacy VDP current-run receipts retain
the journal's guarded Cloud scope. No old artifact is deleted by migration.

Reviewed unsigned-source SHA-256 values (exact inner archive bytes):

| Source | Unsigned SHA-256 |
| --- | --- |
| 1.0.16 | `d6757035407968553f27fe7e93caae00bbab72bb13fc4f3527a37700e8f34fa1` |
| 2.0.0 | `8728a0779cb1665910f2953457a1140ccfcda07ee236f215836193ff0d6b1a90` |
| 3.0.0 | `746a38d76848f86ed6d4c4150893c95eb36cf044cf6f44c7a6f57506d72e7411` |

## 5. Bounded migration of existing source packages

1. Read only the three existing pinned archives listed above. Reject missing,
   changed, oversized or structurally unsafe input. An adjacent newly computed
   hash is not an acceptable replacement for the existing reviewed pin.
2. Use the existing bounded archive reader. Retain the inner unsigned package
   bytes, validate outer/inner configuration agreement and the complete payload
   structure. Do not execute or blindly extract archive entries.
3. Record the legacy archive digest and the new unsigned input digest in a
   versioned provenance manifest. Check deterministic output and exact payload
   equivalence, including all profile metadata and 7/15/23-path capability sets.
4. Perform migration through the existing Demo Control component path, not an
   external script or helper. Existing valid output is a no-op; conflicting
   output is a diagnostic, not an overwrite. A partial write is recoverable.
5. Switch source lookup and provenance validation to unsigned inputs together.
   The historical PEM setting becomes obsolete for normal Prepare. Existing
   configuration with that field must be handled explicitly during transition,
   not cause an unrelated configuration-loader failure.
6. Keep existing source archives until migration and comparison pass. Their
   later removal is a scoped housekeeping action, not an automatic destructive
   side effect of this audit or of a failed Prepare.

Trust changes explicitly: equality to the reviewed legacy digest bootstraps
the migration; reviewed unsigned digests protect later source use. This does
not establish authorship of arbitrary unsigned files and must not be described
as fresh verification of the old signature. New publication signatures remain
fully verified under the selected current credential.

## 6. Ordered implementation and documentation gates

| Step | Deliverable | Gate before proceeding |
| --- | --- | --- |
| 1 — Freeze the amendment | Accept this local trust/publication-context decision; update affected contract definitions and schemas | No contradictory claim that Prepare still requires the original PEM; preserve external OEM/SP authority and all unrelated demo flows |
| 2 — Unsigned VDP sources | Versioned source manifest, bounded idempotent migration and unsigned lookup/provenance | All three real pinned inputs match; deterministic unsigned outputs and payload equivalence; no old certificate use |
| 3 — VDP publication contexts | Existing Sign/Verify/Upload select a context-specific derived envelope and receipt | Same-context repeat, certificate rotation, other-domain re-sign and selection-change-before-upload tests pass |
| 4 — Service parity | Separate reusable prepared content from SP/service binding; identical context handling for Brake and Tire | No cross-Cloud owner/UUID reuse; payload unchanged; correct SP signer; version-collision and uncertain-publication tests pass |
| 5 — UI and persisted compatibility | Project the active context; read/migrate legacy records conservatively; preserve parked-run checkpoints | Browser and CLI use the same operations; no stale Signed/Published state; no lost receipt, replay, version rollback or automatic VM action |
| 6 — Handoff | Targeted verification receipt and exact manual Resume/Prepare/Publish sequence | Park remains intact; explain live gates not executed; operator can continue the same unprovisioned Test |

Documentation cascade: update the affected local-trust paragraph of HLA and
the certificate-selected Cloud amendment, Demo Control package/signing sections,
relevant requirement allocations, artifact/operation schemas, CLI README,
Presenter contract/traceability and delivery plan. Record no-impact review of
the scene layout, OEM/SP external authority, provisioning model and guest Safe
Stop behavior rather than changing their semantics or unnecessarily rebuilding
their implementations. Earlier qualification reports remain dated evidence.

Factory .33, CM/SM, VDP functional binaries, service binaries, KUKSA permissions,
Production rollout and Cloud backend code are outside this change. No VM image,
service Docker build or platform rebuild is needed for this package refactor.

## 7. Verification while the operator is away

| Check | Execution boundary | Expected evidence |
| --- | --- | --- |
| Archive migration | Local pinned source artifacts; no Cloud or VM | Positive V1/V2/V3 equality and negative digest/path/duplicate/tamper cases |
| Prepare | Isolated temporary fixture catalog and version ledger | Old PEM absent; unsigned content valid; same profile/version rules; user ledger not consumed by tests |
| Sign and rotate | Generated fixture OEM/SP credentials and the real installed signer | New signatures verify; same unsigned content across signers; repeated same-context signing is a no-op |
| Upload guards | Mocked API boundary, not the live staging account | Correct role/domain/owner; no unsigned upload, cross-context IDs, retry of uncertain outcomes or credential-switch race |
| Services | Existing product exports or isolated fixtures, no Docker build | Brake/Tire content unchanged; SP binding deferred to the correct destination context |
| UI state | Unit/browser fixtures through existing adapters | Prepared survives context change; Signed/Published refer only to current context; no layout/flow redesign |
| Restart/retirement | Isolated journal/receipt fixtures | Partial signing/migration recovers; parked checkpoints and version continuity survive; cleanup is ownership-scoped |
| Current session preservation | Read-only actual Presenter/journal | Test remains PARKED with the same local identity, disk and selected Cloud; no operator workflow replay |

Fixture checks can proceed with the real Test stopped. They do not establish
staging acceptance or installation on the VM. A real staging publication and
guest installation remain a separate live step and must not be performed under
the label of an offline test or while promising to leave this session parked.

## 8. Operator continuation

The operator has already parked successfully. Do not use Finish, delete the
overlay, reset version continuity or create a replacement Test for this change.
After implementation and targeted checks, an idle Presenter reload may be
needed to load the changed server code; ephemeral UI job history is not the
persisted lifecycle authority. Re-read the parked journal and selection.

Use **Session → Resume** (CLI: `democtl environment resume`) to restart the same
Test, backends and simulator. The existing lifecycle initializes the retained
connection in stationary Manual, not in its previous moving scene. Selected
staging guest configuration is reapplied by the ordinary VM-start path. No
automatic provisioning or software publication is part of Resume.

Then continue the accepted manual story with Prepare VDP V1 and Sign/Publish
against staging, followed by provisioning and Safe Stop as appropriate. The
operator does not enter a version. Report the allocator's actual release and
the real Cloud result; do not promise a specific next number in advance.

## 9. Audit sources and limits

Implementation follow-up: the accepted changes, offline tests and real pinned
source migration are recorded in the [verification receipt](../../qualification/unsigned-package-signing-2026-09-15.md).
The following paragraphs retain the boundary of the original pre-change audit,
not the result of the subsequent implementation.

Code reviewed: `components.py`, `component_build.py`, `component_worker.py`,
`component_publication.py`, `service_packages.py`, `cloud_connection.py`,
`status.py`, `releases.py`, `demo_lifecycle.py`, `test_environment.py` and the
Presenter operation bridge. Existing component identity/signing tests were
inspected; this audit did not execute the proposed regression suite.

The installed official `aos_signer/signer/signer.py` accepts `pkcs12_path`,
builds from unsigned configuration/payload, and signs hashes of the archive and
configuration with RS256. The installed configuration validator checks schema
and input paths. These source reads support using the existing signer rather
than inventing a new deployment envelope. The public
[Aos Quick Start](https://docs.aosedge.tech/docs/quick-start/) also separates
service packaging/signing/upload from Subject-based deployment. Two deeper
documentation URLs could not be fetched during this audit; no unobserved
platform behavior is inferred from that failure.

Evidence actually obtained: read-only source and configuration inspection,
the reproduced baseline signature failure from the preceding diagnosis, three
real `component inspect` results, version-ledger observation, and the completed
operator Park receipt. No runtime code, source artifact, signature, Cloud object,
VM state or version ledger was changed by this audit. Only this proposal and
documentation navigation/status links were written, including repair of an
existing Finish anchor and reachability of the preceding UI-run report. No
commit or push was performed.

Documentation validation passed: `scripts/docs-check` checked 194 Markdown
documents, 658 stable identifiers and 38 Mermaid diagrams; `git diff --check`
reported no whitespace errors. These are documentation gates, not execution
of the proposed package/signing tests.
