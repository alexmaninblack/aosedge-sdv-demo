<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Consolidated demo integration and release automation plan

- Status: Accepted for implementation
- Version: 0.2
- Prepared: 2026-10-13
- Owner: Demo Solution Team with integration and component maintainers
- Scope: Current Presenter integration, operator DMG delivery and subsequent automated releases

The next delivery combines the reviewed Presenter and Driving Control changes
with the published A/B/C launcher. One release campaign will coordinate source
checks, selective assembly, M1 qualification, main integration, public artifact
delivery and operator catalog promotion. A failed candidate must not replace
the last successfully checked operator package.

Source acceptance and binary recommendation are separate gates. Product changes
enter main after their applicable source and M1 checks; option A switches only
after the exact DMG is published and its anonymous consumer path passes. This
plan neither changes runtime contracts nor treats an engineering preview as a
notarized, fully qualified external release. Implementation and external actions
follow the operator's 13 October approval and their existing authorized boundaries.

## Dropbox delivery amendment on 13 October 2026

The operator copied the unchanged engineering DMG into the approved public
Dropbox folder and authorized continuing the delivery check from the new
`SDV-Dev` workspace. Deliver the operator DMG through that reviewed Dropbox
file link; retain reusable developer inputs on Google Drive. No new product
version, CARLA/Factory build, upload, account permission or Cloud deployment
is needed for this transport change.

The maintainer selection may use `delivery` with `provider: "dropbox"` and
`downloadURL`. The publication stage adopts the already published file through
anonymous HEAD requests with bounded, HTTPS-only Dropbox CDN redirects and
the exact approved byte count. This does not claim a provider-reported checksum:
the actual M1 consumer must still check the complete SHA-256, Setup signature
and manifest before opening the installer. There is no automatic fallback
between Dropbox and Drive, nor a maintainer loopback payload download.

Use a separate `<version>-dropbox` campaign record directory. Preserve the
old Drive campaign, failed consumer receipts and historical storage identities.
Source gates precede normal main integration; the new operator catalog and
tag are promoted only after the M1 consumer check and final cleanup pass.
The existing engineering-preview and first-use limitations remain unchanged.

## Checkpoint at plan acceptance

### Authorized 15 October successor

The operator authorized the remaining native Setup first-use profile on M1,
then main fan-in, version tags and publication of a new option A DMG. Use
`1.2.0-rc.2` for changed media; do not replace the published rc.1 bytes. The
production migration's exact Test-only authority applies, preserving the
retained Production-role Unit and unrelated resources. Platform's reviewed
VDP runtime enters main before integration pins it; Gateway is already in main.

Native first use passed with new M1-generated certificates after correcting
Setup's menu/domain binding. The [qualification report](../../../qualification/m1-clean-install-e2e-2026-10-14.md)
identifies changed Setup bytes, unchanged qualified runtime, reused installation
evidence and remaining exclusions. Public option A still requires its separate
anonymous consumer check. The active B plan uses current frozen producer/native
sources over the unchanged rc.1 binary-input definition; historical locks and
plans are not rewritten.

The following heads were remotely verified on 13 October. Reconcile them before
execution rather than treating these dated values as moving release authority.

| Repository or input | Checkpoint | Remaining work |
| --- | --- | --- |
| Integration main | `3dc1c780a2a92eca1d79bb40c24f256d88e727da` | Already contains the new README and A/B/C launcher |
| Integration Presenter branch | `5f559a78a1f14797698060401088c8fc86f41a75` | Combine with current main and qualify the resulting composition |
| Gateway Driving Control branch | `b4c505561f9d2bcdf75ee322f973c85d4b18380d` | Integrate into Gateway main before integration main pins that revision |
| Current A descriptor | Engineering candidate `1.2.0-rc.1`; empty download locator | Replace the selected release through reviewed metadata, not by rewriting its historical descriptor |
| Retained M1 UI evidence | Two passing 42-stage campaigns on one immutable installed package | Reuse only the exact applicable results; they are not complete installer first-use acceptance |

The UI campaigns took 20:10 and 20:20 including cleanup. These are not total
release durations or proof of an overall speed improvement. The launcher has
offline fixture acceptance; its real public option A first-use remains open.

On 13 October the authorized Dropbox continuation completed source/delivery
gates, anonymous M1 download, installed/open reconciliation, verified closure
and catalog/tag promotion. The published engineering source checkpoint is
`sdv-lab-v1.2.0-rc.1`; [release results](../../../qualification/release-automation-2026-10-13.md)
record exact identities, recovery and timings. Native Setup button-input and
clean-first-user acceptance remain open; this does not turn the preview into a
fully qualified external release.

## Release rules

- Freeze exact commits, product build inputs, tool versions and artifact
  identities at campaign start. Do not pull new source during execution.
- Use the accepted product numbering and `sdv-lab-v<version>` tag policy.
  Reserve a new candidate identity when product bytes change; never replace a
  previously published version with different bytes.
- Run build and packaging work on the selected external SSD. Run actual
  installation, API, UI and live acceptance on M1 internal storage. The
  development Mac performs unit tests and M1 orchestration, not local live tests.
- Reuse verified Factory, CARLA and tool caches when their complete input
  identities match. Rebuild only affected components. Missing dependencies
  stop explicitly rather than falling back to internal bulk storage.
- Preserve staging-only Cloud scope, serial version publication, VDP Safe Stop,
  moving QM-service behavior and normal lifecycle owners. Preserve Production,
  credentials, unrelated resources and the video repository.
- One accepted scenario owns the sequence, bounded waits, effect checks,
  timings and final cleanup. The agent investigates failures rather than
  scheduling routine clicks or asking whether to continue.
- Existing signatures and OS protections remain authoritative. Keep preview,
  signing and qualification limitations visible; a successful upload cannot
  remove them.

## Ordered implementation and current release

Execute these stages in order under one agreed packet. Stage completion means
its stated result, not another kit number or a collection of partial attempts.

### 1 Freeze the integration candidate and acceptance matrix

Prepare one integration branch containing current main and the reviewed
Presenter changes, together with the intended Gateway revision. Preserve the
published launcher and original B behavior. Reconcile source cleanliness,
existing candidate receipts and current M1 state before any mutation.

Write the campaign's change classification and required gates once. Bind old
results to their exact product inputs, package, target and scenario version.
Retain unresolved first-use, native, repair and other acceptance boundaries
explicitly; do not expand this packet to close unrelated historical research
gates or the deferred VDP timeout.

Result: a fixed source composition, version identity and finite acceptance
matrix identifying reused evidence and checks that genuinely remain.

### 2 Implement the single release campaign

Add one maintainer entry, `scripts/release-campaign`, composing existing
build, packaging, qualification, transfer and pin-projection owners. It is not
a replacement installer, driver interface or product lifecycle journal. Keep
its orchestration receipts separate from authoritative vehicle/Test state.

The entry supports a plan, execution and reconciled continuation. Persist
non-secret stage intents, exact input identities, results and durations. Hold
one release lease across the campaign and use existing resource leases for
the SSD, M1 and live owners. Never cancel an active external mutation merely
because another release was requested.

Before costly work, check selected storage/capacity, M1 connection, desktop
availability, shared Docker and required authorized signing/Cloud/Drive access.
Report a concrete unavailable prerequisite without indefinite waiting. Known
downloads show artifact names and byte progress; other stages show activity,
elapsed time and the current operation without invented percentages.

Result: a unit-tested campaign that can own the whole accepted sequence without
conversational scheduling. Correctness and cancellation fixtures precede any
new real release campaign.

### 3 Verify source and assemble only what changed

Run unit, type, contract, documentation, secret and launcher-pin gates before
assembly. Verify the cross-repository source composition and immutable product
input hashes. A failure closes all later stages.

Reuse the retained tested DMG only if every packaged input and required artifact
identity matches the proposed release. A different Git merge commit alone does
not require rebuilding identical product bytes; matching filenames or an old
green report do not prove equivalence. Otherwise assemble one successor with
the affected binaries/assets, using retained Factory and CARLA inputs.

Result: an immutable DMG and provenance receipt mapping exact product inputs,
signature, payload manifest, size and checksum to the integration candidate.

### 4 Complete the applicable M1 qualification

One outer campaign invokes the existing M1 installation/API/UI scenarios in
their required order. Keep engineering API results separate from actual browser
and native input acceptance. Include exact package checks, the normal install
path, serial release behavior, required vehicle results, lifecycle preservation
and independent final closure according to the stage 1 matrix.

If the current packaged product is unchanged, retain its passed campaign
evidence and run only newly required composition/launcher/delivery checks.
Changed product inputs require the applicable new tests. Reused evidence never
fills a previously missing acceptance gate.

Result: source integration gates passed, exact newly passed/reused evidence
recorded, remaining preview limitations stated and test-owned runtime closed.

### 5 Integrate verified source into main

Integrate Gateway first, then integration source with the verified Gateway pin.
Update active dependency/build definitions so a fresh B run from main uses the
new source composition. Preserve historical source locks and release receipts.
Check expected remote heads immediately before publishing each main update.

Two repositories cannot be committed atomically together. Record each confirmed
fan-in result; if interrupted after Gateway integration, reconcile and resume
the root integration rather than repeating or force-resetting either repository.
Concurrent product changes invalidate the frozen composition and require the
affected gates again. Documentation-only merge differences may reuse evidence
only after explicit input-equivalence checks.

Result: the reviewed source is committed and pushed to both main branches, with
consistent active dependency pins. Option A still points to its previous package.
Main integration does not wait for the large Drive upload to finish.

### 6 Publish the exact operator DMG

Use the agreed public artifacts folder and an immutable, readable versioned
DMG name. Upload once or reuse the already verified matching object. Confirm
file identity, parent, size, provider checksum, version and anonymous reader
access through metadata. Reconcile interrupted uploads before sending bytes
again; do not create duplicates or perform a maintainer loopback download.

Extend the existing delivery owner's currently private-folder/candidate-only
contract explicitly for the reviewed public preview path. Do not silently
disable its sharing or qualification guards. Keep publisher authorization local;
option A must require neither Google credentials nor developer tools.

Result: an exact published DMG with a retained delivery receipt. Publication
alone does not make it the recommended operator package.

### 7 Prove option A and promote its catalog

Prepare the new release descriptor and candidate launcher/catalog generation.
Use one real anonymous M1 consumer download to test the selected provider's
redirects, progress, size/checksum, signature and normal Setup handoff. Complete
the required install/open checks under the ordinary owners. Respect Gatekeeper;
an OS refusal is a real blocker, not a reason to clear protections.

Only after this result passes, atomically commit the selected release reference,
catalog, regenerated helper pins and matching launcher to integration main.
Validate them against the new immutable descriptor, not the hard-coded old
delivery record. Retain old descriptors and the preceding recommended package.
Tag the final source composition under the accepted version policy and record
the Gateway/source mapping in its release provenance.

Result: a newly downloaded README launcher selects the published checked
package through A. Previously downloaded launchers retain their verified
generation; obtain the new launcher deliberately to select a newer release.
No silent self-update or mutable unsigned remote catalog is introduced.

## Subsequent release operation

After the first complete campaign passes, reuse this entry for later releases.
Initially one maintainer launch starts the whole campaign; no per-stage human
approval is added inside its accepted scope. Offline GitHub checks remain
automatic. A later trusted-source trigger may start the same local coordinator;
do not expose the credential-bearing Macs to arbitrary public pull requests.
No scheduled service, CI credential migration or general remote runner is
created by this packet.

| Change | Checks and delivery |
| --- | --- |
| Documentation only | Documentation/navigation and applicable source gates; no DMG or live campaign |
| Preparation or release tooling | Unit/contract gates plus the affected M1 consumer scenario; no unrelated heavy compilation |
| Product/runtime/installer | Affected source gates, selective candidate assembly and applicable M1 acceptance before main integration |
| Recommended operator release | All required release gates, exact publication, anonymous A proof and final catalog promotion |

A installs the last checked recommended preview/release and exposes its actual
qualification status. B uses current main on a fresh run and pins that selection
for continuation; its result is a build, not automatic release acceptance.
C retains specialist host preparation and its explicit full-source limitations.

## Failure recovery and cleanup

Stop at a failed, blocked or uncertain gate with a bounded report. Resume only
after checking current input identity and authoritative effects; never replay
uncertain publications, provisioning or UI actions. A failure before catalog
promotion leaves the previous recommended package selected. A later discovered
regression uses an explicit catalog rollback commit to the retained known-good
package, not overwritten artifacts or rewritten Git history.

Cleanup uses existing owned shutdown paths and verifies closed processes,
listeners, qualification clients and owned media. Preserve shared Docker Engine,
persistent Test state, credentials and diagnostic evidence. Retire an exact old
disposable Test only when the agreed clean-install scenario requires it.

Put scratch below the selected workspace's `.tmp`; final artifacts and reports
use readable versioned output paths. Keep the recommended and preceding package,
required rollback inputs and reusable caches. Delete other superseded bulk
outputs only after exact dependency/ownership checks and confirmed remote
availability where needed. Cleanup is not blanket deletion of Factory/Builder
caches or failed-state evidence.

## Completion criteria

The first consolidated delivery is complete when both source main branches and
active dependency pins are consistent, the selected DMG has the required M1
evidence, its public DMG delivery is verified, and a fresh README option A
consumer reaches the accepted installed/open state. Source, catalog/helper
generation, release tag and artifact provenance must agree. Preview or other
remaining qualification limitations remain visible.

Automation acceptance additionally requires a complete campaign without routine
agent scheduling, bounded negative/interruption/continuation proofs, no unsafe
promotion after a failure and confirmed cleanup. Record total campaign time,
per-stage times and development/investigation time separately. Do not promise a
release duration from the historical 20-minute UI segment alone.

## Related controls and evidence

- [Release campaign operating contract](../../../development/release-campaign.md)
- [13 October release results and provider blocker](../../../qualification/release-automation-2026-10-13.md)
- [Human friendly reproduction](human-friendly-reproduction.md)
- [Unified launcher packet](unified-macos-launcher.md)
- [Launcher behavior and maintenance](../../../getting-started/unified-macos-launcher.md)
- [Launcher offline results](../../../qualification/unified-macos-launcher-2026-10-13.md)
- [Build and publication operating policy](../../../governance/rapid-development-and-debugging.md)
- [Retained comparative UI results on the review branch](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/5f559a78a1f14797698060401088c8fc86f41a75/docs/qualification/ui-campaign-comparison-2026-10-12.md)
- [GitHub guidance for access to local runners](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/manage-access)
