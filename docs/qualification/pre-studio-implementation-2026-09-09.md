<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Pre-Studio implementation source checkpoint

- Status: accepted source checkpoint; Studio implementation not authorized
- Version: 1.0
- Prepared: 2026-09-09
- Owner: Demo Solution Team
- Reference: `pre-studio-implementation-2026-09-09`
- Plan: [Demo Studio delivery plan](../planning/active/demo-studio-delivery-plan.md)
- Contract: [Current Test Studio contract](../demo/mockups/aosedge-demo-interaction-specification.md#ui-studio-026--current-test-studio-contract)
- Audit: [Action and integration audit](../research/demo-studio-action-audit.md)

## Boundary and authorization

The operator authorized committing and pushing the already reviewed working
changes, recording repository revisions, and creating a named return point.
The operator explicitly prohibited starting Studio implementation. This
checkpoint introduces no new application behavior, VM/image build, component
publication, Cloud mutation, service deployment, or live demo operation.

The same annotated tag names the Solution checkpoint and the Runtime source
checkpoint in their respective repositories. The Solution tag includes this
record and the updated workspace source pins; the application/mockup source
was frozen by the exact preceding commit recorded below. There is no
self-referential commit hash inside this document: resolve the final Solution
checkpoint with `git rev-parse pre-studio-implementation-2026-09-09^{commit}`.

## Exact source revisions

| Repository | Branch | Frozen source revision |
|---|---|---|
| `aosedge-sdv-demo` | `main` | `4507beeb98820ae57f7e42843ce5371c220ed0d2` (application, tests, mockups and accepted design); the checkpoint tag additionally includes this record and the workspace pins |
| `carla-ego-runtime` | `main` | `f506e4b206725317c83346c4f46069235ca8f038` |
| `aos-vehicle-platform` | `main` | `0bed8b3769b09fbe685ed599ca8d10e6594fbe53` |
| `brake-health-service` | `main` | `63b0c5fd43572ff96c508abc5e35818218d3500a` |
| `brake-health-cloud` | `main` | `1320dde24ae0f72771ea9320c2bd2212c20726ba` |
| `CarlaSim` | `macos-apple-silicon` | `ac7d882cac496ccbf8b40aa543d6b38513e1173c` |
| `UnrealEngine5_carla` | `macos-xcode26-compat` | `2583a3fd4110bc430416d14820c6df2894ccc619` |

[Workspace repository pins](../../workspace/repositories.json) now match these
six dependency revisions. This is a development source baseline, not a claim
that every product is implemented or qualified. Launcher paths, executable
contracts and immutable artifact build provenance are unchanged. In particular,
the existing Gateway build may retain its documented `carla-tm-order` source
worktree; the updated main-source pin does not relabel that binary.

## Included work

- Runtime: five existing source/test/document changes for combined native
  Driving Control and telemetry, fixed telemetry pages, read-only JSON
  monitoring, and the Demo Control connectivity invocation.
- Solution: 36 existing changes covering the selected-vehicle external-link
  command, native workspace integration, Presenter header simplification,
  associated tests, mockups 2.5 and 2.6, English design documents, action
  matrix, gap register and reconciled delivery sequence. Earlier mockups are
  retained.
- Accepted design includes the retained dedicated Group Subject bound only
  to the current Test; both service packages specify
  `configuration.instances.minInstances: 1` and
  `configuration.offlineTTL: P7D`. Assignment sends only `service_ids`.
  These are accepted implementation inputs, not deployed service changes.

## Bounded checks at checkpoint creation

| Check | Result |
|---|---|
| Demo Control connectivity tests | 14 passed |
| Demo Control workspace tests | 13 passed |
| Presenter TypeScript type check | Passed |
| Presenter local UI unit tests | 17 passed |
| Runtime M6 tooling tests | 8 passed |
| Runtime product-language tests | 2 passed |
| Mockup 2.6 state-machine and browser tests | 27 passed; none skipped |
| Staged source/confidential-input checks | Passed for the 41 source/mockup/document files |
| Git whitespace and documentation checks | Passed; checkpoint documentation is checked again by the normal commit hook |

The browser test used an isolated headless browser and exercised the VDP,
Brake and Tire story, offline/reconnect, Park and Retire. It did not operate
the user's open mockup or call live Cloud/VM APIs. The confidentiality checks
included the repository guard and a bounded check for binary payloads,
private-key/certificate blocks and JWT-shaped credentials in staged files.
This is not a claim of an exhaustive security audit.

No Swift/C++ rebuild, new native live trial, full integration regression or
fresh-overlay qualification was performed. Previous live evidence remains
in the [native desktop plan](../planning/active/native-demo-desktop.md) and
[Factory .31 qualification record](democtl-release-checkpoint.md), with its
original limitations. Passing a simulated service flow does not establish
real service packaging, deployment or advisory readiness.

## Work deliberately outside the baseline

- Runtime branch `codex/ltvp-traffic-manager-order` retains local commit
  `d1838abfad2a69a8d05222bcaf79625a5ef1d502`; its remote branch still points to
  `c308c4195f8f9eebd7a5a59ff630d2b13237afb2` at the audit. Do not delete its
  worktree while the existing build depends on it.
- Brake Cloud branch `codex/imp-04-brake-cloud-window-detail` retains local
  commit `f66ff01cad67d12b386b1c0d994dd642f1d491d5`, outside `main` and not
  published by this checkpoint.
- Brake Service worktree `brake-health-service-imp-04-bhs-core-v3` retains six
  untracked v3 advisory/message/state-store source files. They are not covered
  by this checkpoint tag and are not silently integrated or deleted.
- Solution branch `codex/bhs-v2-packet-digest-correction` retains local commit
  `7f2f1935e1b8d9ad47bc206c1c863019762f7b79`. Git patch-equivalence inspection
  reports its change already represented in `main`; no duplicate integration
  or branch publication is required for this baseline.
- The `pre-integration-main-2026-08-30` stash and historical LTVP worktrees
  remain untouched. They are not part of the current source baseline.
- CARLA's untracked presentation scratch, platform source copy and two
  pinned-API scripts remain outside the checkpoint. No blanket `git add`,
  branch cleanup, worktree removal or stash application was performed.

## Return to this point

Use the Solution and Runtime tags above, plus the exact dependency revisions
in the table. Retrieve only the required normal branches/tags from each
repository's configured remote. Prefer a separate worktree or a new branch
from the checkpoint; do not reset a dirty working directory or overwrite
unrelated work. Restoring only Solution `main` is insufficient because the
native Runtime source is owned by another repository.

This is a source/documentation return point, not a snapshot of running
processes or Cloud state. Factory .31 and compiled executables, signed VDP
bundles, overlays, credentials, private journals and telemetry remain outside
Git in their existing locations. Their original manifests/provenance are
preserved. No backup copies are created. Cloud release numbers and published
history cannot be rolled back by checking out a Git tag.

Implementation must receive a separate authorization after this checkpoint.
