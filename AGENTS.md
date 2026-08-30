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
- Test with the deployed service identity/capability model. Do not weaken the
  product to satisfy a non-production harness identity.
- Keep network-disabled/offline build guards and the work packet's disk guard;
  default minimum free space for image work is 60 GiB unless a stricter packet
  value applies.

## Security, Cloud and cleanup

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
