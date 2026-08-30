<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Rapid Development and Debugging Policy

- Status: Accepted operating policy
- Version: 1.0
- Prepared: 2026-08-30
- Owner: Demo Solution Team with repository and integration owners
- Applies to: implementation, integration, debugging, build, qualification,
  Cloud operations and artifact cleanup across the AosEdge SDV demo workspace

## Purpose

This policy minimizes elapsed engineering time and routine operator
involvement without weakening accepted design, security, evidence or external
mutation boundaries. The default is autonomous progress inside an exact
authorized scope. Formal package/image builds occur only after the smallest
reversible proof has closed all known blockers.

This policy changes no component, interface, lifecycle, authority or
acceptance requirement. Applicable requirements, D4 decisions, executable
contracts and authorized work packets remain authoritative.

## Human-Involvement Boundary

After an exact work packet or user-requested change is authorized, the agent
shall continue without intermediate approval through:

- read-only inspection and diagnosis;
- creation of isolated worktrees and ignored temporary evidence locations;
- reversible transient changes confined to the selected disposable target;
- targeted compile, static analysis, unit and contract tests;
- source correction inside the frozen writable boundary;
- local commits and the work packet's offline repository/package gates; and
- factual status reporting and non-mutating authoritative reconciliation.

The agent shall stop and request direction only when:

1. accepted design or contracts leave a real product choice unresolved;
2. a change must cross a repository owner or writable boundary;
3. architecture, authority, trust, lifecycle, data direction or an observable
   contract would change;
4. required secret/credential use is outside prior authorization;
5. signing, publication, live provisioning/deployment, Production mutation,
   destructive cleanup or another irreversible external action is not already
   authorized for exact targets and effects;
6. an execution safety control requires more explicit authorization; or
7. authoritative state is contradictory or cannot be observed safely.

Routine compiler errors, test failures and corrections inside the accepted
boundary are not new approval gates. An agent shall not ask for repeated
approval merely because an operation contains multiple internal checks.

## Mandatory Rapid-Debug Cycle

### 1. Preserve the failing state

- Keep the exact VM, overlay, checkpoint, Cloud Unit/Node identity, service
  state and bounded logs available.
- Stop unrelated writers but do not destroy, reprovision, reset, rebase or
  rebuild the failing target.
- Record the last confirmed state and whether any mutation command actually
  started. Absence of output is never reported as success.

### 2. Localize with read-only evidence

Collect only evidence needed to identify the next boundary:

- effective service configuration, identity, environment and sandbox;
- `ActiveState`, `Result`, `ExecMainStatus` and `NRestarts`;
- a bounded journal window and fixed diagnostic stages;
- exact file owner, group, mode, type and SELinux label;
- fresh scoped AVCs from a captured audit cursor;
- process, listener, mount, lock and open-handle ownership; and
- exact authoritative external object/status reads where relevant.

Classify the result before editing:

| Class | Required response |
| --- | --- |
| Product/source defect | Continue with the smallest transient product-equivalent proof. |
| Harness identity/environment mismatch | Correct the harness; do not weaken production behavior. |
| Evidence-command/tooling defect | Correct or relocate the evidence command; reuse the completed artifact/run. |
| Expected Factory/baseline condition | Record the accepted expectation; do not create a fake product dependency. |
| External/authoritative contradiction | Preserve state and stop mutation until reconciliation closes it. |

### 3. Prove one minimal reversible hypothesis

Preferred mechanisms, in order, are:

1. service restart or invocation with unchanged product bytes when safe;
2. exact transient systemd drop-in under `/run/systemd/system`;
3. one hash-verified target binary under `/run` with the production exec label;
4. one temporary configuration or credential copy from an already accepted
   authoritative source, never TOFU or invented material; and
5. one exact temporary SELinux module using a temporary policy root/store,
   with an armed stock-policy rollback and post-proof restoration.

Transient changes shall be explicitly inventoried and reversible. They shall
not enter immutable rootfs content, a Factory Image, Git, a reusable overlay or
an unrelated service. Unsafe whole-overlay rebase, rootfs remount, broad
permission grant, shared placeholder credential and product weakening are
forbidden shortcuts.

### 4. Use targeted compilation

When code is required to prove the hypothesis:

- compile only the affected target with the exact pinned inputs;
- do not run package, image or unrelated recipe tasks;
- verify architecture, interpreter, digest and size;
- install only in the transient proof location with exact owner/mode/label;
- redirect only the exact service `ExecStart`; and
- retain the original installed binary and immutable checkpoint unchanged.

If current diagnostics cannot locate a failure, add bounded non-secret stage
names and errno/result only. Paths, raw responses, PINs, tokens, certificate
contents, keys, telemetry and customer data shall not be printed.

### 5. Execute bounded proof, never blind retry

- Run exactly one attempt for the current hypothesis.
- A timeout or response loss triggers polling/reconciliation of that attempt,
  not another invocation.
- A retry is permitted only after proof that the previous operation did not
  apply, or when the test explicitly exercises an accepted idempotent path.
- Cloud/SDK/provisioning attempts retain their exact stronger no-blind-retry
  and authoritative-reconciliation rules.

The proof matrix shall include every applicable row:

| Proof | Required result |
| --- | --- |
| First-create/empty-state | The original failing path completes without partial or hidden failure. |
| Existing-state/idempotent repeat | Reuse completes cleanly and does not duplicate state. |
| Restart/reboot | Required state reconstructs or remains absent exactly by contract. |
| Functional operation | The real consumer path succeeds, not only process startup. |
| Negative/fail-closed | Wrong/missing/stale input has no unsafe side effect. |
| Service stability | Expected state, exit status and `NRestarts=0`; no restart storm. |
| Security | Fresh scoped AVC set is empty or contains only an accepted deny-and-dontaudit proof. |
| Secret hygiene | No secret or unrestricted payload entered logs, evidence or environment. |
| Rollback | Transient binary/config/policy can be removed and stock state restored. |

### 6. Consolidate source only after proof

Once the live or production-equivalent proof passes:

1. implement the smallest source delta inside the owning boundary;
2. add regression tests for the exact first-create and repeat paths;
3. add static validators for security and packaging invariants;
4. run targeted compile/tests before broad suites;
5. create one clean reviewable checkpoint with the proof and exclusions; and
6. do not copy diagnostic credentials, `/run` files, debug environments,
   temporary policy modules or disposable target state into source.

## Build and Qualification Economy

The build ladder is mandatory and monotonic:

```text
source/static gate
  -> affected target compile and tests
  -> affected package and package-QA
  -> one warm incremental image build
  -> immutable freeze and transfer
  -> clean offline smoke
  -> separately authorized live provisioning/deployment
  -> final functional, restart and security acceptance
```

- A failed early gate closes every later gate.
- Use the accepted warm Builder, download cache and shared-state cache with
  offline/network guards. Routine cleanup shall not remove them.
- Default free-space guard for image work is 60 GiB on the Builder and host,
  unless a work packet requires more.
- A missing evidence-only tool, quoting error or host-side metadata failure
  after successful image/assembly does not trigger a rebuild. Resume from the
  immutable candidate and obtain the evidence in a compatible environment.
- A multi-gigabyte immutable artifact is hashed at creation and at each copy or
  trust-boundary transfer. Its recorded manifest is reused while path, size and
  immutable identity remain unchanged; status reporting alone does not justify
  another full hash.
- Qualification uses the deployed service UID, groups, capabilities and
  sandbox. A non-production harness mismatch is corrected in the harness.
- Formal rebuild starts only after all currently known defects have passed the
  rapid proof. Several unproved guesses shall never be bundled into an hour-
  long build.

## Cloud, VM and API Operations

- Use the qualified API/CLI path rather than an interactive browser.
- Perform an exact read-only preflight: authenticated role, permission,
  target UUIDs, current state, non-target guard and expected request/response.
- Before a mutation, journal exact intent and whether an attempt has started.
- Execute an authorized mutation once, require the documented response, then
  perform an authoritative object and inventory re-read.
- Preserve partial/uncertain results; never hide them by local overlay removal
  or immediate reprovisioning.
- Guest-local debugging does not justify SDK reprovisioning or creation of a
  replacement Cloud Unit.
- Live provisioning, identity retirement, source handover and R0 are
  run-exclusive even when source development occurs in parallel.

## Security Closure

- Apply least privilege to the observed necessary operation, not to a library
  or directory category broadly.
- Optional probes that must remain denied use an exact deny/dontaudit decision;
  they do not receive access merely to produce a clean audit.
- Transient SELinux proof shall use an exact reviewed module, temporary store,
  pre-recorded active-policy hash, Enforcing mode, automatic stock-policy
  rollback, full functional-chain execution, fresh audit cursor and verified
  removal. No rootfs remount or canonical policy-store mutation is allowed.
- Systemd hardening is relaxed only when an accepted product invariant
  requires the blocked syscall, and only on the exact unit. Other hardening,
  identities, capabilities, paths and network restrictions remain unchanged.
- Native packaged trust anchors and configured authorities take precedence
  over handshake extraction, TOFU, shared demo certificates or generated
  placeholders.

## Disk and Artifact Hygiene

Disk cleanup is part of completion rather than an emergency response.

1. Inventory exact candidate paths and physical sizes; use no broad glob.
2. Map child overlays to backing images and active QEMU/Builder processes.
3. Stop only exact owned VMs, then prove zero PIDs, mounts, locks and open
   handles.
4. Delete child overlays before backing images.
5. Preserve the accepted baseline and active diagnostic generation until the
   successor passes its complete acceptance.
6. Preserve Builder/caches, Git objects, manifests, compact logs and accepted
   evidence. Reproducible scratch and superseded raw/overlay artifacts may be
   deleted after their source commits are proven available.
7. Report exact removed paths, physical space recovered and whether state is
   recoverable.

## Parallel Work and Status

- Parallelize disjoint repository-owned source, read-only analysis, targeted
  compile and fixture work according to the accepted implementation plan.
- Keep one writer per repository/worktree and one integration owner.
- Do not parallelize live run-exclusive mutations or use another lane's VM,
  credential, socket, port, build output or Cloud object.
- Prepare the next safe local step while a build or transfer runs, but never
  cross a gate early.
- Send concise factual heartbeats at least every 60 seconds during active work:
  current operation, completed milestone, whether an external attempt started,
  blocker and next gate. A heartbeat requests no approval unless a true human
  gate above has been reached.

## Completion Checklist

A completion statement shall include:

- exact source commit/tree and changed boundary;
- tests/builds actually run, including skipped or unavailable gates;
- artifact/version/digests when produced;
- first-create, repeat, functional, restart and security results as applicable;
- authoritative Cloud/Unit state when touched;
- remaining unimplemented or unqualified scope;
- confirmation that transient debug state was removed or deliberately
  preserved with its exact location; and
- disk cleanup disposition and preserved caches/evidence.
