<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# LTVP `.27` repeatable VDP update work packet

- ID: `WP-LTVP-27-REPEATABLE-VDP-001`
- State: completed and visually accepted by the operator on 2026-09-04
- Audience: `Test Vehicles` only
- Factory target: `6.1.1-maninblack.27`
- Update targets: VDP `1.0.15`, then version-only successor VDP `1.0.16`
- Production and Campaign mutation: forbidden

## Objective

Turn the successful `.26` engineering proof into a source-controlled,
repeatable `.27` Factory and update flow. The final result must have no source,
binary, configuration or release dependency on `/private/tmp`, no post-boot
DNS repair and no transient replacement of `aos-sm`.

The same immutable `.27` image is qualified twice. The first clean VM receives
VDP `1.0.15`; it is then deprovisioned and deleted and its disposable overlay
is removed without backup. A new overlay from the same image SHA receives the
version-only successor VDP `1.0.16` through the same complete
Cloud-to-vehicle flow. This executed pair supersedes the initially planned
`1.0.14`/`1.0.15` pair after the final Factory digest and accepted source were
repinned before qualification.

## Source boundaries

### `aos-vehicle-platform`

Only the final forms of these changes are admitted:

- VDP server-authenticated TEST_ONLY input parsing and readiness;
- Safe Stop binding using the Aos node/system UID supplied by AosCore;
- one frame-coherent multi-path VISS snapshot and bounded connection close;
- full-gzip component layer handling and provider-archive validation;
- idempotent missing-component `StopInstance` semantics;
- Factory integration of the corrected component runtime;
- deterministic VDP `1.0.15` and `1.0.16` release profiles and packaging; and
- owned tests, manifests, SBOM and provenance required by those changes.

Intermediate `1.0.0`/`1.0.3`/`1.0.13` candidate pins and temporary artifact
bookkeeping are not carried into the clean branch.

### `aosedge-sdv-demo`

Admit only:

- this contract, packet, as-built record and their indexes/tests;
- one direct, documented provision/deprovision/delete sequence;
- one direct sign, deployment-bundle upload, status and approval sequence;
- the fixed per-instance DNS route required by the VM launcher; and
- exact `.27`/VDP release manifests and compact qualification evidence.

Do not add `formatVersion` or `vendorVersion` to the Unit Model payload. The
descriptive schema is authoritative over the stale example that previously
introduced those fields. Do not retain helpers pinned to VDP `1.0.0` or the
component-upload endpoint; VDP publication uses the Deployment Bundle API.

### `carla-ego-runtime`

Gateway product source remains at the accepted clean revision unless a source
defect is independently proven. A dedicated Test-only launch configuration may
set the controller period to 50 ms, matching the accepted Safe Stop profile.
Global 30-Hz configurations are not silently changed.

## Commit and integration order

1. documentation and executable contract;
2. component archive/runtime lifecycle;
3. coherent VISS Safe Stop and Test-only input;
4. Factory network/runtime integration;
5. deterministic VDP `1.0.15`/`1.0.16` release packaging;
6. direct Cloud and VM operating procedure;
7. qualification evidence and final source pins.

Each repository uses a clean branch from current `origin/main`. Experimental
branches are not pushed or merged. They are deleted locally and remotely only
after both E2E cycles pass, the final branches are pushed and immutable tags
and evidence identify all retained results.

## Pre-build gates

- focused Python and C++ tests pass from clean source;
- target `aos-sm` compile passes offline with pinned AosCore sources;
- component full-gzip install, replacement, absent-stop and reboot recovery
  pass;
- one VISS snapshot contains all ten paths, one timestamp and a monotonic frame;
- 50-ms Safe Stop timing, stale data and close-handshake negatives pass;
- Unit Model payload contains only current schema fields; and
- no candidate or signed bundle contains private credentials or machine-local
  paths.

No Factory image is built when a pre-build gate fails. The image build uses the
accepted warm Builder/cache, an exact source revision and the normal free-space
gate. Exactly one `.27` image is retained for both E2E cycles.

## Factory and artifact outputs

The Factory output records exact source commit/tree, image version, size,
SHA-256, partition identity and immutable path. A clean first boot must have
working DNS, synchronized time and native IAM/SM/CM Online behavior without a
guest patch.

VDP `1.0.15` and `1.0.16` use the same accepted functional payload. All
version-owned metadata is internally coherent. `1.0.16` is the declared
version-only successor of `1.0.15`; its packaging-source change only admits the
new release identity and does not change runtime behavior.
Each signed deployment bundle is unpacked once to verify its OCI schema,
component identity, runtime selector, exactly one nonempty full-gzip layer and
digests before upload.

## E2E cycle A — VDP `1.0.15`

1. Create a new disposable overlay from the immutable `.27` image.
2. Provision once, add the Unit to `Test Vehicles`, and require Unit/Node Online.
3. Start CARLA, controller and loopback Gateway; show that the vehicle moves.
4. Sign and upload VDP `1.0.15` through the Deployment Bundle API.
5. Approve its Validation Batch for `Test Vehicles`.
6. While moving, require Cloud delivery and runtime waiting without activation.
7. Apply explicit Safe Stop and require activation only after the complete gate.
8. Require Cloud installed `1.0.15`, active slot `1.0.15`, VDP active/running,
   `READY/source LIVE`, zero unexpected restarts and updating vehicle data.
9. Reboot the VM and require the same installed/active/readiness result without
   Factory placeholder `0.0.0` reassertion.

After evidence is recorded, deprovision and delete the Unit, stop the VM and
delete only its used overlay, access material and provisioning state. Preserve
the immutable `.27` image; create no overlay backup.

## E2E cycle B — VDP `1.0.16`

Repeat every cycle-A step using a new overlay from the exact same `.27` image
SHA and new provisioning state. Join `Test Vehicles` before uploading and
approving `1.0.16`. Require the same moving/waiting/Safe Stop/activation/live
evidence for `1.0.16`. Cycle B retained the live VM after visual acceptance so
the operator could inspect the qualified state; shutdown/reboot persistence is
recorded separately from the two-update delivery proof.

## Completion and cleanup

Completion requires both cycles, clean repositories, pushed final branches,
reviewable commits, immutable artifact manifests and updated documentation.
Only then remove obsolete local and remote experiment branches, `.21`–`.26`
overlays and images, temporary signed/unsigned bundles, old Builder outputs,
orphan runtime directories and stale Cloud Units. Preserve source history,
tags, `.27`, final signed bundles, compact evidence and required build caches.

Any Production/Campaign change, mTLS claim, different Factory image between
cycles, post-boot DNS correction, second image build or unreviewed product
boundary stops this packet.
