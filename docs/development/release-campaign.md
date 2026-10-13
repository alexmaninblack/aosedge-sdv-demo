<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Automated demo release campaign

The accepted [release packet](../planning/active/work-packets/consolidated-release-automation.md)
coordinates source acceptance and operator delivery through one maintainer entry.
The campaign is distinct from the A/B/C operator/developer launcher and from a
vehicle lifecycle journal. Its ordered adapters retain their normal ownership,
staging, signature and no-replay boundaries.

## Single entry and receipts

Integration tooling prepares one private JSON selection with source expectations,
the selected SSD UUID, exact media/manifest identities, M1 connection references,
applicable evidence and the publisher's approved folder/account. It contains no
password, private key or token. No command or arbitrary executable URL can be
supplied by that selection.

```sh
python3 -B scripts/release-campaign plan --config /absolute/private-selection.json
python3 -B scripts/release-campaign run --config /absolute/private-selection.json
```

After resolving a concrete prerequisite, use the same selection with `resume`.
Successful stages are independently revalidated. An uncertain mutation cannot
be submitted again until its authoritative effects are reconciled. `--until`
stops at an explicit diagnostic boundary and reports PARTIAL, never a completed
release. One global lease serializes release work; per-candidate records also
reject concurrent writers and changed bindings.

After a source-only campaign-tool correction, `run --restart-readonly` may
archive a BLOCKED attempt and restart all gates with the same configuration.
It refuses any attempt that reached a mutation intent; those must be reconciled
and resumed, not restarted. Existing evidence is retained in a numbered attempt
directory rather than rebound to different source.

Records are private and versioned under the selected workspace's
`build/release-campaign`. They include stage results, timings and one report.
For the approved Dropbox delivery successor, records use `<version>-dropbox`;
the product version is unchanged and the original Drive campaign is preserved.
This does not adopt or change the developer workflow's `output` result alias.
Temporary fixture/build data stays under the workspace's owned `.tmp`; persistent
artifacts, caches, Test data and shared Docker are not cleanup targets.

## Current UI source selection

Historical binary-input locks and build plans remain immutable. A successor
schema 3 build chain explicitly declares two `nativeSources`: integration and
vehicle-gateway. Each carries the existing repository URL and an exact commit.
It changes neither the retained C++/Factory/CARLA dependency selection nor the
platform/service algorithm contracts.

The Presenter owner obtains those exact current UI/native sources without
resetting existing checkouts. Its receipt binds them into the build key. Host
assembly uses the same source trees as the selected UI receipt; it cannot combine
a current binary with old helper source by accident. Missing, dirty, foreign or
mutable source selections stop before compilation.

An optional committed `workspace/current-developer-build.json` selects one
immutable successor plan by repository-relative path and SHA-256. Fresh B runs
resolve that source-owned selection; older checkouts without it retain their
historical plan. Saved root checkouts never silently update. The public binary
input catalog remains independently pinned and unchanged by a UI-only source
successor.

## Source and artifact promotion

Both source main branches advance only after the applicable frozen product and
source gates pass. Fan-in is Gateway first, then integration; interrupted pushes
are reconciled, not force-reset or blindly repeated. Public preview delivery is
explicit and checks the already approved folder's anonymous reader permission.
It does not create or widen sharing permissions.

Option A promotion additionally requires the exact public consumer proof. Its
source catalog, selected immutable descriptor and regenerated helper graph move
together in one commit after acceptance. The preceding package remains available
for explicit rollback. Apple Development preview status, lack of notarization
and remaining first-use/native acceptance limits are retained rather than
removed by a green unit test or an upload.

The current consumer adapter downloads the frozen public launcher generation
on M1 without Google credentials or developer tools, verifies the DMG and signed
Setup, then uses Setup's ordinary install/prepare/open owners. It preserves the
existing installed Test and checks visible Presenter surfaces and final closure.
This is an engineering consumer-path proof, not native Setup button-input or
clean-first-user acceptance. Those limitations remain explicit in its report.
An uncertain graphical handoff is not replayed automatically.

### Existing Dropbox publication

A maintainer selection can specify `delivery` as `{"provider": "dropbox",
"downloadURL": "https://www.dropbox.com/scl/…?rlkey=…&dl=1"}`. This adopts an
operator-published DMG; it does not upload, sign in or change sharing rights.
Anonymous HEAD requests check the approved full byte count and bounded Dropbox
CDN redirects. Some folder-member CDN responses label the attachment as JSON
with an unspecified filename. The downloader accepts that observed combination
only on the reviewed CDN with the exact approved length; a complete consumer
SHA-256 and signed Setup identity remain mandatory before use. HTML, foreign
redirects, wrong lengths and cross-provider fallbacks are rejected.

The old Drive selection remains supported for developer inputs and existing
campaigns. A storage move updates active paths and UUIDs explicitly; it does
not rewrite frozen build manifests or resume a differently bound campaign.

For a consumer-tool defect before any media bytes were downloaded, an explicit
`resume --amend-operator-tooling` correction may re-gate a strictly allowlisted
operator-only source delta. It requires the same selection and Gateway, unchanged
packaged product and verified publication, preserved prior receipts, confirmed
closure and affirmative M1 proof of no media/partial file or mounted image.
Any existing payload or uncertain handoff refuses this path. The new consumer
attempt uses a fresh named namespace; confirmed publication is not replayed.
