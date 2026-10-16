<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0001: Repository and Artifact Boundaries

- Status: Superseded in part by [ADR 0006](0006-lifecycle-based-repository-ownership.md)
- Date: 2026-08-12

## Remaining decisions

CARLA and restricted Unreal changes stay in their upstream-oriented repositories;
never copy restricted engine source/assets into this public integration repo.
Platform and independently deployed services follow ADR 0006 rather than the
original monolithic prototype allocation. Use focused upstream forks for a
required platform correction and pin the exact revision until upstream adoption.

Large runtime/build artifacts, mutable VM overlays, provisioning state, SDK
caches, raw diagnostic data and all credentials remain untracked. Certificates
are external references, never copied into source. Record exact external source
versions and content digests; use no Git submodules or hidden monorepo copies.
Explicit checked-out paths or verified installed inputs connect repositories.

Current branch/release rules and source-publication gates are maintained in
[development workflow](../../governance/development-workflow.md) and
[licensing policy](../../governance/licensing-and-copyright-policy.md).
They replace the completed initial repository-creation checklist and prototype
branch/tag names. The [original decision](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/7691072c88de9558f6c9a88687d304462c759d34/docs/architecture/decisions/0001-repository-and-artifact-boundaries.md) retains that context.
