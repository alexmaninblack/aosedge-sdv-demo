<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Development Workflow

## Mandatory Execution Policy

Every implementation, integration, debugging, build and qualification task
shall follow the
[Rapid Development and Debugging Policy](rapid-development-and-debugging.md).
Inside an exact authorized boundary the implementation agent proceeds
autonomously through reversible diagnosis and local gates. Full builds and
external mutations remain behind the policy's explicit evidence and human
authorization boundaries.

## Current Branching Decision

The maintained AosEdge SDV demonstration repositories use a lightweight
trunk-based workflow while the project has one active developer and one active
implementation agent:

- accepted changes are committed directly to `main`;
- routine work does not create feature branches;
- each commit is small, coherent, and independently reviewable;
- relevant local tests and repository gates pass before a commit is pushed;
- the working tree is checked before staging so unrelated files are not swept
  into a commit;
- a checkpoint tag or other recoverable baseline is created before a risky
  migration, release operation, or destructive cleanup.

This decision applies to:

- `aosedge-sdv-demo`;
- `aos-vehicle-platform`;
- `brake-health-service`;
- `brake-health-cloud`;
- `tire-health-service`;
- `tire-health-cloud`;
- `carla-ego-runtime`;
- the maintained `alexmaninblack/carla` fork;
- the restricted `alexmaninblack/UnrealEngine` fork.

On 9 October 2026 the owner selected `main` as the current development and
GitHub default branch for all nine repositories. This supersedes the earlier
CARLA/Unreal compatibility-branch exception. Their maintained Apple Silicon
baselines now live on `main` in our forks; upstream repositories are unchanged
and Unreal remains private. Existing compatibility and integration branches
remain as historical references, without force-push, deletion or retagging.

The root integration and Factory build-tool histories are consolidated in
`main`. A contributor does not select another maintenance branch for current
work. Reproducing an existing candidate still selects its exact recorded
commits: frozen release locks and producer pins are not rewritten merely to
follow `main`. A current default branch is not a new qualified binary release.

The current `workspace/repository-map.json` records maintenance owners and
optional heavy-source dependencies without release pins or launcher paths.
The default read-only workspace doctor checks current main, remote identity and
dirty state against locally recorded remote-tracking refs; it does not fetch
or claim server freshness. CARLA/Unreal sources are optional unless explicitly
requested. The hash-bound `workspace/repositories.json` remains an unchanged
selected-build compatibility input. Inspect it only with an explicit
`--manifest workspace/repositories.json`; do not reseal frozen definitions to
make current source inspection pass.

## When to Reconsider

Reintroduce pull requests or short-lived feature branches when any of the
following becomes true:

- multiple developers or implementation agents can modify the same repository
  concurrently;
- an external contributor needs review before integration;
- protected-branch or release-governance rules require approval;
- a long-running experiment cannot remain continuously releasable;
- a change requires an isolated security, safety, or architecture review.

Until then, branch creation adds coordination overhead without improving the
current single-writer workflow.

## Architecture Change Exception

A level-C change that modifies an authority, trust boundary, component,
interface, lifecycle or data direction uses a short-lived architecture branch
even during the single-writer phase. The complete impacted documentation
cascade is reviewed and passes `docs-check` before merge, so `main` never
contains a partially migrated architecture baseline. See
[Documentation and Requirements Management](documentation-and-requirements-management.md).
