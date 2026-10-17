<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0016: Unsigned Packages and Session-scoped Signing

- Status: Accepted and implemented; current selected-preview API/UI evidence follows the current baseline
- Version: 1.1
- Prepared: 2026-09-15
- Owner: Demo Solution Team
- Change class: C — local source-artifact trust and publication-context separation
- Architecture input: [High-Level Architecture 1.8](../high-level-architecture.md)
- Scenario input: [Demo Scenarios 2.1](../../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Existing contract: [Certificate-selected Test Cloud](../certificate-selected-cloud.md)
- Current proof: [baseline](../../qualification/current-baseline.md)
- Editorial consolidation: 2026-10-17; accepted behavior and stable IDs preserved

## Accepted decision

Keep reusable package content unsigned and independent of a destination Cloud.
Prepare an immutable release, then use the currently selected OEM certificate
for a VDP publication or the configured, matching SP certificate for a service
publication. A different destination or signer creates a separate signed
representation of the same prepared content; it does not mutate that content.

## Context and rationale

Using a destination certificate to verify historical source envelopes made
preparation fail when the destination signer changed. Reusable source trust
must therefore be digest/provenance-bound independently of current signing
credentials. The accepted correction is implemented. Exact source conversion
and former session observations remain in
[Git history](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/1a0d66f4b340bfc7b487062f7bb316623ad86af8/docs/architecture/decisions/0016-unsigned-packages-and-session-scoped-signing.md),
not parked-Test continuation instructions. Cloud/Subject selection, OEM/SP
authority, monotonic allocation and uncertainty guards are unchanged.

<a id="4-accepted-artifact-and-signing-contract"></a>
## Artifact and signing contract

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

Exact unsigned input bytes are selected by source-owned input locks and
producer declarations, not by a copied digest table in this decision. Keep
prepared content, destination-specific signatures and Cloud objects separate;
an old signature or receipt cannot authorize another domain/owner.

## Legacy-source compatibility

1. Read only the three legacy archives pinned by `component_build.PROFILE_BASES`. Reject missing,
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

## Verification and compatibility boundary

Use isolated fixtures for digest/path/duplicate/tamper rejection, deterministic
unsigned conversion and exact 7/15/23-path equivalence; no ledger allocation in
the operator instance. Signer tests cover same-context reuse, rotation,
other-domain signatures and selection changes before upload. Upload fixtures
cover wrong role/owner, cross-context IDs and uncertain results without replay.
Brake/Tire retain the same payload and native identity/permission semantics.

Legacy receipt decoding preserves original context and monotonic reservations.
Current UI facts refer to the active context only. Partial writes reconcile;
cleanup preserves required canonical inputs and release continuity, not an
unbounded archive. Stop/Start and retirement follow ADR 0017, not the removed
Park/Resume instructions.

This source-artifact refactor does not change Factory, CM/SM, KUKSA permissions,
functional binaries, production rollout or backend protocols. It requires no
image rebuild. Offline tests cannot establish live publication, installation or
full UI acceptance; actual scoped evidence is selected by the current baseline.
No retired session/ledger observations select the next release number.
