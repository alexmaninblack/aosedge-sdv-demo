<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# AosEdge SDV Development Instructions

These instructions are mandatory for every implementation, integration,
debugging and qualification task in this repository and its worktrees.

## Accepted design is authoritative

- Read the applicable accepted requirements, D4 decisions, executable
  contracts, implementation plan and authorized work packet before editing.
- Do not invent a new interface, lifecycle, authority, state store, fallback or
  product behavior. Stop and report a bounded change request when accepted
  inputs conflict or do not close the required behavior.
- Preserve repository ownership, writable boundaries, one-writer-per-repository
  isolation and the exact fan-in order recorded by the work packet.

## Autonomous execution inside an authorized boundary

- Once an exact work packet or user-requested change is authorized, continue
  through read-only diagnosis, reversible transient proof, targeted compile,
  owned tests, source correction and the packet's local gates without asking
  for routine intermediate approval.
- Ask for human input only when a design/product choice is genuinely open, the
  requested scope must expand, a required secret or credential use was not
  authorized, or a signing/publication/live external/destructive action lacks
  exact authorization. Never bypass an execution safety review.
- Send concise factual progress while work is active; do not leave a command or
  investigation without a user-visible heartbeat for more than 60 seconds.

## Standing staging test authorization

On 30 September 2026 the user explicitly authorized the complete ongoing
installer/demo qualification cycle in `aws-stage.epmp-aos.projects.epam.com`:
retire previous owned Test runs (including their Cloud Units, working VMs and
backend run data), create replacement Tests, build and sign test packages with
the already selected authorized identities, publish test releases and install
and verify them. Do not ask again for routine steps inside this scope.

Resolve exact targets and ownership before each mutation and retain compact
evidence. Preserve Production even on staging, source/Git, current Factory and
required rollback/build inputs, credentials and unrelated resources. Publish
VDP/Brake versions serially, verifying each before the next. This authorization
does not bypass tool safety controls, permit credential disclosure, change the
accepted architecture or authorize public distribution. Ask only at an actual
boundary outside this scope or when a mandatory tool control requires it.

## Finish checks and follow the accepted delivery stages

- At the end of a check or a paused test session, gracefully close all windows,
  servers, helpers, simulators, VMs and containers started for that check and no
  longer needed by the active sequence. Do not leave them running for convenience.
- Keep a test environment running after handoff only when the user explicitly
  requests it. Preserve persistent Test/Cloud identities, disks, journals, models,
  release ledgers and evidence: stopping is not Finish, retirement or deletion.
- Verify that owned processes and listeners have exited; a successful stop
  request alone is insufficient. Do not stop unrelated user applications or
  shared infrastructure. Reconcile an active or uncertain operation before
  shutdown; report any concrete shutdown blocker rather than killing blindly.
- Docker Engine is background infrastructure, not a test-owned runtime. Reuse
  it without opening Dashboard; start it only if confirmed stopped and needed.
  End-of-test cleanup stops the demo containers, never Docker Engine/Desktop.
  Do not add Engine restart tests or automatic quit cycles to this qualification.
- Execute the accepted delivery stages without turning each fix, test or build
  into a new plan or approval checkpoint. Report stage completion against its
  original acceptance criteria; partial tests and new kit numbers are not a
  completed stage. Continue authorized in-scope work until those criteria or a
  concrete external blocker are reached.

## Rapid-debug before formal build

1. Preserve the failing VM, overlay, checkpoint, Cloud identity and evidence.
   Do not rebuild, reprovision, retry or clean up before classifying the fault.
2. Collect the smallest read-only evidence set: effective configuration,
   service result/restarts, bounded journal, ownership/modes/labels, fresh AVCs
   and exact external state. Separate product defects from harness,
   evidence-command and expected-baseline conditions.
3. Prove one hypothesis with the smallest reversible transient change. Prefer
   `/run`, a temporary directory, a systemd drop-in, an exact replacement
   binary or a temporary policy store. Do not modify immutable rootfs content,
   remount it writable, perform an unsafe overlay rebase or widen security to
   make a test pass.
4. Compile only the affected target when a binary is required. Verify its
   architecture, digest, owner, mode and label before one bounded execution.
5. Never issue a blind retry. Poll an existing command; after response loss,
   reconcile authoritative state before deciding whether another attempt is
   permitted.
6. Require the applicable first-create, idempotent-repeat, restart, functional,
   negative, restart-count, secret-redaction and fresh-AVC proofs. Add only
   fixed non-secret stage diagnostics when existing output cannot locate the
   boundary.
7. Move a fix into source only after the transient proof passes. Run targeted
   compile/tests first; perform one warm incremental package/image build only
   after all known rapid-debug blockers are closed.

## Efficient build and evidence rules

- All new build, packaging, publication-preparation and diagnostic scratch
  belongs under the selected workspace's `.tmp`, not a new directory in the
  home or volume root. Use the owned build-scratch helper/context and cleanup
  traps; completion includes scratch removal and retained compact evidence.
  Keep verified caches, resumable downloads, final outputs and runtime state
  separate. Never repurpose scratch cleanup to remove them. Recover abandoned
  marked runs only after proving their owner and open handles are gone.
- Gateway socket fixtures may require an explicitly selected shorter `.tmp`
  on the same volume (29-byte parent limit); this is not bulk-build storage.
  Preserve existing transactional/credential/guest temporary-file boundaries.
- Use the accepted warm Builder, download cache and shared-state cache. Never
  delete them as routine cleanup.
- Put mandatory compile/unit/policy gates before image construction. Stop the
  image gate on failure.
- An evidence-only tool or quoting failure does not invalidate a completed
  artifact. Resume from the exact immutable candidate instead of rebuilding.
- Hash a large immutable artifact at creation and transfer/trust boundaries.
  Reuse the recorded manifest while path, size and immutable identity remain
  unchanged; do not repeatedly hash an unchanged multi-gigabyte image merely
  for status reporting.
- Routine artifact delivery uploads once and verifies remote identity, size,
  checksum, parent and access metadata. Do not download the payload back merely
  to recheck the provider. Verify bytes on the actual installation/build
  consumer; reserve separate round-trip tests for changed transfer/recovery
  code or a concrete integrity incident. Reuse verified caches and receipts.
- Test with the deployed service identity/capability model. Do not weaken the
  product to satisfy a non-production harness identity.
- Keep network-disabled/offline build guards and the work packet's disk guard;
  default minimum free space for image work is 60 GiB unless a stricter packet
  value applies.

## Security, Cloud and cleanup

- New repositories created for this project must be public, as explicitly
  required by the user on 10 September 2026. Do not default them to private.
  Public visibility does not permit committing credentials, runtime data or
  build artifacts; retain the existing source-publication and secret gates.
- Never print, hash for display, persist in evidence or place in Git any PIN,
  private key, JWT, reusable certificate content or one-time token.
- Grant no broad SELinux/systemd/filesystem/network permission from a symptom.
  Prove exact permissions transiently, verify the full functional chain and
  restore stock policy before committing the minimal source delta.
- Use authenticated APIs/CLIs rather than a browser for AosCloud operations.
  Resolve exact UUIDs with read-only preflight, mutate only explicitly
  authorized targets once, then perform authoritative post-read reconciliation.
- Before cleanup, prove exact paths, dependency order, stopped owners, zero
  open handles and preserved source/evidence. Delete child overlays before
  backing images; use no broad globs. Preserve the current accepted baseline,
  active diagnostic state, Builder/caches, Git, manifests and compact logs.

The complete normative procedure and acceptance checklist are in
[`docs/governance/rapid-development-and-debugging.md`](docs/governance/rapid-development-and-debugging.md).
