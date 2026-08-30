<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Consolidated Implementation Execution Trains

- State: `PLATFORM TRAIN COMPLETED IN ACCEPTED .21 — DEMO INTERFACE TRAIN AUTHORIZED / NOT STARTED`
- Version: 1.2
- Prepared: 2026-08-29
- Owner: Demo Solution Team with Platform, Gateway and UI owners
- Factory Gate 1 source implementation: completed under its accepted bounded
  packet and integrated into `.21`
- Product edits, package/image build, local commits, fan-in and disposable
  Test-Vehicle qualification in the Platform Train: completed; this record
  grants no residual execution authority
- Network, provisioned Unit and AosCloud activity: completed only for the
  separately authorized canonical disposable Test Vehicle qualification
- Live CARLA, Production Vehicle/Unit Set, unrelated Cloud/backend mutation,
  signing, publication, FOTA/SOTA, push and merge authorized: no

## Purpose and operating model

This is the single orchestration view for the accepted streamlined execution
model. It replaces the former three-lane, packet-by-packet approval sequence
with two reviewable trains. Existing detailed packets remain the exact source
for writable boundaries and deterministic tests; no new per-gate planning
document is required.

Each train receives one explicit consolidated authorization. The Platform
Train received that authorization on 2026-08-29. The operator accepted the
Demo Interface Train and its exact bundled safe defaults on 2026-08-30, but
product implementation remained held until the synchronized entry bases and
digests were committed and rechecked. The operator accepted the bounded
cross-platform controller-handoff correction on 2026-08-30; after this
contract checkpoint is committed, the clean entry gates may start. After authorization,
read-only evidence checks, bounded source edits, offline builds, deterministic
tests, forced-clean repeats and local checkpoint commits proceed without a
new operator review at every internal Gate 0/1/2. Those gates remain mandatory
agent stop checks. Work returns for review only on an automatic stop condition
below or before an action explicitly excluded from the train.

The two trains may run in parallel and do not absorb the concurrent Brake
Health or Brake Cloud work. Tire Health and every new feature lane remain
paused. Shared solution-document changes are reconciled only after both trains
produce reviewable evidence; no worker overwrites the current BHS or Factory
cascade.

## Train 1 — Platform

### Entry lock

| Input | Exact identity or rule |
| --- | --- |
| Product repository | `aos-vehicle-platform` |
| Clean common ancestry | `bdc72aba97a83c9868d454588189ef139710a6d7` |
| Runtime checkpoint | `4d8800636ded58386e2872a7e415dc1cc322c92c` |
| VDP-family checkpoint | `67123333775a696a1143d0281013651b3736f0fd` |
| KAC/Row2 checkpoint | `405546b9efa6d5acf6ced4bc14a5249860d448de` |
| Factory input | Result of the already authorized Gate 1 work defined by [the KAC Factory packet](work-packets/p1-platform-kac-factory-integration.md), with `405546b9` as its exact parent |
| Builder/source lock | Existing qualified R6.1 `qemuarm64` Builder and pinned offline cache only |

The completed [KAC compile packet](work-packets/p1-platform-kac-compile-integration.md)
and [KUKSA Row2 packet](work-packets/p1-platform-kuksa-row2-scope-parser.md)
remain immutable evidence. The current Factory Gate 1 authorization remains
valid and is incorporated as the first stage of this Platform Train
authorization.

### Continuous execution sequence

1. Complete Factory source implementation and its product-local/contract
   tests inside the frozen packet boundary.
2. Run the exact affected offline compile, package, package-QA, installed-file,
   dependency, systemd, SELinux and forced-clean repeat checks; create one
   local Factory checkpoint only after all pass.
3. Create a clean isolated fan-in branch from `bdc72aba`. Import the complete
   Runtime range ending at `4d880063`, then VDP `6712333`, then KAC/Row2 ending
   at `405546b`, then the Factory checkpoint. Resolve only predeclared
   ownership collisions. In particular, the IAM/Permission Handler and
   Factory transformation must preserve both accepted semantics; a
   last-writer-wins copy is forbidden.
4. Repeat every owning branch suite plus dependency inventory, recipe/package,
   IAM/resource, Runtime Safe Stop, VDP family/slot, KUKSA Row2 and KAC gates.
   Create one local fan-in checkpoint only after the effective configuration
   and changed-path audit pass.
5. From that exact checkpoint, build the successor Factory Image offline with
   the pinned R6.1 Builder. Record manifest, package inventory, hashes,
   effective configuration, SBOM/dependency evidence and reproducibility
   result. Do not sign, publish, assign or install it on a current Unit.
6. Qualify the exact image in one newly created disposable Test Vehicle
   VM/COW. Before any VM or provisioning mutation, freeze and independently
   verify the exact new target, creation harness, image input, existing-OEM
   provisioning harness and cleanup exclusion. If those identities are not
   already exact and reviewable, stop automatically; the authorization is not
   permission to guess or select a pre-existing target. Prove boot;
   IAM/Permission Handler; KUKSA verifier and Row2 scopes;
   KAC Service-only and Provider-one-shot separation; VDP v1-v3 family/slot;
   Runtime Safe Stop waiting/recovery; restart persistence; bounded failures;
   and deprovision behavior without executing destructive cleanup. Preserve
   the disposable overlay, VM and all sanitized evidence; this authorization
   grants no overlay, VM, artifact or evidence cleanup.
7. Using only the frozen canonical existing-OEM path, provision that exact new
   disposable VM as a Test Vehicle and confirm that the resulting exact Unit
   becomes online in AosCloud. Record the Unit/Node/provisioning identities in
   redacted evidence. Do not touch a Production Vehicle, Production Unit Set,
   pre-existing VM/Unit/artifact or any unrelated Cloud resource.

### Exit evidence

- exact Factory and fan-in commits with parents and changed-path inventories;
- first/repeat offline build and package results for every affected recipe;
- successor image/package manifests, hashes, SBOM/dependency and effective
  IAM/resource/systemd/SELinux configuration proof;
- disposable-VM test matrix with redacted logs, restart and failure-closure
  results;
- exact new disposable Test Vehicle and canonical existing-OEM provisioning
  evidence, plus read-only confirmation that its Unit became online in
  AosCloud; and
- explicit confirmation that no Production Vehicle/Unit Set, pre-existing
  VM/Unit/artifact, unrelated Cloud resource, signing, publication, cleanup,
  push or merge action occurred.

Passing this exit qualifies a local successor-image candidate and proves one
new disposable Test Vehicle can be provisioned and observed online. It does
not make the image an accepted Factory baseline or authorize production
deployment.

## Train 2 — Demo Interface

### Entry lock

| Input | Exact identity or rule |
| --- | --- |
| Gateway repository/base | `carla-ego-runtime@d4a20c85196ef7df81c78f992f6237c5eca8ff6c`; clean isolated worktree |
| Completed controller handoff | Same commit above; the completed 14-file implementation remains immutable |
| Presenter repository/base | `aosedge-sdv-demo@107031a353308fc670d4a477e302e7a6bd278e55`; Presenter shell `106d340a6fe2e945de055642f2e016355ea6cf91` is an ancestor |
| Detailed execution contracts | [Selected-Unit mTLS](work-packets/p1-vehicle-gateway-selected-unit-mtls.md) and [fixture-first AosCloud read adapters](work-packets/p1-ui-aoscloud-readonly-adapters.md) |

### Bundled safe defaults

One authorization of this train accepts the recommended `MTLS-01` through
`MTLS-05` bundle exactly as written in the mTLS packet and the
`UI-RO-RD-01` through `UI-RO-RD-06` fixture-only closures exactly as written
in the UI packet. These defaults do not create certificates, introduce a live
read proxy, contact a source or claim production PKI/freshness behavior.

### Continuous execution sequence

1. Implement the selected-Unit mTLS Gateway core in its exact twenty-file
   boundary: strict client authentication, fixed URI identities/fingerprints,
   private same-UID assignment CAS, per-role path policy, generation handover
   and no cached-frame reuse. Generate test credentials only ephemerally.
2. Run unit, loopback mTLS, assignment, role-policy, no-stale-generation,
   regression, static-analysis and sanitizer gates; create one local Gateway
   checkpoint after all pass.
3. Implement only the UI packet's fixture-first typed read projections inside
   its exact twenty-three-file boundary and existing lockfile. Use contract
   synthetic fixtures, injected time, metadata-only native logs and
   notification-followed-by-full-reread semantics. No HTTP transport or
   credential enters browser code.
4. Run offline typecheck, unit, browser and architecture tests plus
   credential/mutation/storage/network negative scans; create one local UI
   checkpoint after all pass.
5. Run host-only integration tests that compose the two outputs through
   existing fixture/test seams. Prove selected Test/Production identity
   switching, source/error/redaction display, assignment-generation behavior
   and independent Dashboard continuity. No live CARLA, VM, Unit, AosCloud or
   Brake Backend is contacted.

### Exit evidence

- exact Gateway and UI commits, parents and boundary inventories;
- ephemeral certificate/role matrix and selected-assignment traces with
  fingerprint redaction;
- UI fixture provenance, GET-only route matrix, freshness/error/redaction
  matrix and unchanged dependency-lock digests;
- all component and host-integration test counts; and
- explicit confirmation that no external source, credential, live system,
  push or merge was used.

Passing this exit proves the local interface behavior only. Per-Unit client
onboarding, VDP/Runtime guest client wiring, the browser-safe live read proxy,
protected lifecycle actions and live end-to-end qualification remain later
work.

## Automatic stop conditions

An agent stops the affected train and returns one consolidated blocker when:

- a frozen base, parent, tree, digest, dependency lock or pinned source differs;
- an edit is needed outside an exact packet boundary or in another owner's
  concurrent dirty path;
- a dependency, authority, identity, data direction, demo behavior or security
  boundary would change;
- a predeclared fan-in collision cannot preserve both accepted semantics;
- a test/build repeat differs, a secret/private identity is encountered, or a
  fail-closed behavior cannot be proved;
- external network, live CARLA, a provisioned/current Unit, AosCloud/backend,
  real credential/signing, publication, FOTA/SOTA, push or merge is needed,
  except for the Platform Train's exact canonical provisioning and online
  observation of its one newly created disposable Test Vehicle; or
- the exact disposable-VM creation/preservation boundary cannot be proven
  before the protected action.

Ordinary compiler errors, source-local test failures and bounded implementation
corrections inside the accepted contract are handled within the train and do
not create a new operator gate.

## Exact one-time authorization scopes

### Platform Train — authorized 2026-08-29

The operator authorized the sequence under **Train 1** from the current
Factory Gate 1 checkpoint through offline package proof, one local Factory
commit, isolated fan-in in the exact Runtime -> VDP -> KAC/Row2 -> Factory
order, combined gates and one local fan-in commit, successor-image build, one
new disposable Test Vehicle, canonical existing-OEM provisioning and online
confirmation in AosCloud. Authorization is limited to the frozen
repositories, inputs, detailed Factory boundary, isolated worktrees, verified
offline Builder/cache and that exact newly created disposable target.

The authorization preserves every overlay and evidence artifact and grants no
cleanup. It excludes Production Vehicles and Unit Sets, overwrite or deletion
of any pre-existing VM/artifact, dependency or unpinned network acquisition,
unrelated Cloud access or mutation, architecture/security widening, signing,
publication, FOTA/SOTA, push and merge. If the exact disposable target or
canonical harness is not yet frozen, the train stops before mutation and
reports the missing identity; it does not guess.

### Demo Interface Train — authorized 2026-08-30; ready after contract checkpoint

The operator authorized the sequence under **Train 2**, including the bundled safe defaults,
the exact mTLS twenty-file and UI twenty-three-file boundaries, ephemeral test
credentials, offline/local builds and tests, host-only fixture integration and
one local checkpoint per repository. It excludes onboarding or retention of
real certificates, live CARLA/VM/Unit/Cloud/backend access, a live proxy,
protected mutations, dependency changes, push and merge.

These authorizations are independent. Both trains have now received their
bounded authorization. The Demo Interface Train may begin product edits only
after this synchronized contract checkpoint is committed and its clean entry
gate passes. The controller correction executes before selected-Unit mTLS in
the Gateway repository. Its authorization grants only the
offline/local source, ephemeral-certificate and test boundaries above; it
grants no live source, credential retention, external mutation, push or merge.
The Platform authorization ended after the exact new disposable Test Vehicle
was confirmed online; all later integrated-live behavior remains separately
gated.
