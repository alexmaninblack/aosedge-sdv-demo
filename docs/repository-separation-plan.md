# Repository Separation Plan

## Objective

Establish lifecycle-aligned public repositories for vehicle platform software
and the independently deployable telemetry service before implementing AOS-2.
Keep `carla-aosedge-integration` as the version-locking and end-to-end
qualification repository.

This plan is review-gated. Repository creation, code scaffolding, commits,
pushes, and feature implementation start only after the final review is
accepted.

## Fixed Decisions

- Platform repository: `alexmaninblack/aos-vehicle-platform`.
- Service repository: `alexmaninblack/vehicle-telemetry-service`.
- Both repositories are public and contain no restricted Unreal Engine code,
  AosEdge account material, private certificates, tokens, VM disks, or raw
  operational logs.
- License both new repositories under Apache-2.0 and use the exact original-file
  copyright holder text `maninblack`.
- Apply the SPDX, NOTICE, DCO, third-party, VSS, generated-file, and binary
  distribution rules from the licensing and copyright policy.
- Do not use Git submodules.
- Keep CARLA and Unreal Engine forks, `carla-ego-runtime`, and the integration
  repository in their existing repositories.

## R-0 — Approve Documentation and Scope

1. Review ADR 0005, ADR 0006, this plan, the roadmap, and README as one change.
2. Confirm the repository names, public visibility, Apache-2.0 license,
   `maninblack` copyright holder, ownership boundary, and update channels.
3. Confirm that the Authorization Adapter remains AOS-5 and belongs to the
   platform repository.
4. Commit and push the accepted documentation on the current integration
   feature branch; merge it according to the repository's normal review flow.

Exit criterion: the documented boundary is accepted and the integration work
tree contains no unexplained change.

## R-1 — Create the Public Repositories

1. Verify that neither repository name already exists under the GitHub owner.
2. Create both repositories with `main` as the default branch.
3. Add a concise English README, unmodified Apache-2.0 `LICENSE`, minimal
   project `NOTICE`, `THIRD_PARTY_NOTICES.md`, credential-safe `.gitignore`,
   `SECURITY.md`, and DCO-based contribution guidance.
4. Enable secret scanning and dependency/security alerts where GitHub supports
   them.
5. Do not add deployment credentials, signing keys, generated certificates, or
   copied upstream source.

Exit criterion: both clean public repositories exist, clone successfully, and
pass a credential and redistribution review.

## R-2 — Scaffold `aos-vehicle-platform`

1. Create the directory ownership described by ADR 0006.
2. Add an architecture document that marks the CARLA provider as
   development-only and the Authorization Adapter as a deferred AOS-5
   component.
3. Define the initial machine-readable vehicle telemetry profile for speed,
   acceleration, steering, accelerator, and brake.
4. Record VSS 5.0, CARLA-side VSS 6.0 compatibility, KUKSA 0.5.0, and
   `kuksa.val.v1` as pinned prototype inputs.
5. Add empty packaging and test boundaries without implementing provider or
   adapter behavior during the repository-organization step.
6. Add CI gates for formatting, unit-test discovery, SPDX/REUSE compliance,
   dependency licenses, secret patterns, and accidental binary or certificate
   additions.

Exit criterion: the repository publishes a reviewable version `0.x` contract
artifact and has an explicit platform-only ownership boundary; no feature is
claimed implemented.

## R-3 — Scaffold `vehicle-telemetry-service`

1. Create application, test, configuration, documentation, and Aos packaging
   boundaries.
2. Record that the service depends only on a compatible vehicle-data contract,
   KUKSA API, and declared Aos resources/layers.
3. Add a static boundary test that rejects CARLA imports, CARLA endpoints, and
   provider implementation dependencies.
4. Define service versioning, resource-limit ownership, rollback expectations,
   and English-only product output.
5. Add CI gates, including SPDX/REUSE and dependency-license checks, without
   implementing telemetry behavior during the repository-organization step.

Exit criterion: the repository can produce an empty or diagnostic ARM64 Aos
service package skeleton without depending on CARLA or platform source.

## R-4 — Add the Integration Version Lock

1. Add a tracked, non-secret component lock to
   `carla-aosedge-integration`.
2. Pin AosVM, KUKSA, VSS, `carla-ego-runtime`, platform repository, telemetry
   service, and vehicle-data-contract revisions or artifact digests.
3. Add a validation command that rejects missing fields, floating branches,
   unqualified architectures, and digest mismatches.
4. Keep local sibling checkout paths in ignored developer configuration, never
   in the shared lock.

Exit criterion: a clean integration checkout can identify the exact source and
artifact version of every component in a tested baseline without submodules.

## R-5 — Qualify Repository Boundaries

1. Run license, SPDX/REUSE, copyright-holder, credential, binary, private URL,
   and restricted-source scans on all three project-owned repositories.
2. Verify that the platform repository does not depend on service source.
3. Verify that the service repository does not depend on CARLA, VISS, provider,
   VM launcher, or provisioning source.
4. Verify that the integration repository consumes pinned component versions
   and contains no copied component implementation.
5. Clone all repositories into a fresh temporary workspace and run their
   static gates.

Exit criterion: repository ownership and dependency direction match ADR 0006,
and the separation can be reproduced from clean clones.

## R-6 — Begin Feature Implementation

Only after R-0 through R-5 pass:

1. Implement AOS-2 provider and platform integration in
   `aos-vehicle-platform`.
2. Qualify the CARLA-to-KUKSA path through the integration repository.
3. Implement AOS-3 consumer behavior in `vehicle-telemetry-service`.
4. Pin the accepted component releases in the integration lock.

Exit criterion: feature work begins in the repository that owns its lifecycle,
and each accepted end-to-end combination is reproducibly pinned.

## Final Review Checklist

- [ ] The two proposed GitHub repository names are accepted.
- [ ] Public visibility and Apache-2.0 licensing are accepted.
- [ ] Original project files use the exact copyright holder `maninblack`.
- [ ] SPDX, NOTICE, DCO, VSS/MPL-2.0, and third-party provenance rules are
      accepted.
- [ ] Provider and future Authorization Adapter ownership is platform-side.
- [ ] Consumer ownership and SOTA lifecycle are service-side.
- [ ] The vehicle-data contract is initially owned by the platform repository.
- [ ] The integration repository owns orchestration and exact version locks,
      not component source.
- [ ] No Git submodules are introduced.
- [ ] AOS-2 implementation remains blocked until R-0 through R-5 pass.
