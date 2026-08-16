<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# ADR 0007: Solution Documentation Home

- Status: Accepted and implemented
- Date: 2026-08-16
- Implemented: 2026-08-16

## Context

The demonstration spans CARLA, a Vehicle Gateway ECU, an AosVM Domain
Controller, platform FOTA components, SOTA services, AosCloud, functional
backends, and engineering tools. Storing the common architecture and demo
narrative in any one component repository would incorrectly make that
component the owner of the whole solution. A separate documentation-only
repository would split documentation from the orchestration and qualification
evidence that it describes.

The repository formerly named `carla-aosedge-integration` already owned VM
lifecycle, provisioning, cross-project locks, orchestration, and end-to-end
qualification, but that name understated its system-level role.

## Decision

1. The solution/integration repository is the source of truth for cross-system
   architecture, demo scenarios and storyboards, cross-project planning,
   operations, and end-to-end qualification.
2. The canonical repository name is `aosedge-sdv-demo`.
3. The GitHub repository and local checkout are renamed only after an audit of
   Git remotes, links, launchers, local paths, and collaborator instructions.
4. Documentation uses the following top-level taxonomy:
   `architecture`, `demo`, `planning`, `operations`, `qualification`, and
   `governance`.
5. Component-specific documentation remains in the repository that owns the
   component:
   - `carla-ego-runtime` owns Vehicle Gateway, VISS, and simulation-control
     details;
   - `aos-vehicle-platform` owns providers, KUKSA integration, VSS contracts,
     policies, and platform FOTA details;
   - the functional-service repository owns Brake Health state, APIs, tests,
     and SOTA details;
   - CARLA and Unreal forks own only their fork-specific material.
6. Accepted architecture diagrams are stored as editable sources plus
   reviewable exports. External and proprietary reference material remains
   outside the public repository.
7. Git history, rather than a live `archive` directory, retains obsolete and
   rejected documentation.

## Consequences

- Readers have one predictable entry point for the complete demonstration.
- HLA, scenario, planning, operations, and qualification remain connected
  without duplicating component documentation.
- The GitHub repository and local checkout now use `aosedge-sdv-demo`; the old
  GitHub URL is retained only as a platform-managed redirect.
- The documentation reorganization does not move source code, alter a runtime,
  mutate AosCloud, or change a provisioned Unit.
