# ADR 0001: Repository and Artifact Boundaries

- Status: Superseded in part by ADR 0006
- Date: 2026-08-12

## Supersession

ADR 0006 supersedes the temporary decision to keep the platform provider,
authorization adapter, and cloud-managed consumer in this integration
repository. Those components now have distinct vehicle-program platform and
independently deployed service ownership and release lifecycles. Platform
updates can still occur after SOP, but remain under the vehicle-program
qualification path.

The remaining decisions in this ADR still apply: CARLA and restricted Unreal
Engine changes stay in their own upstream-oriented repositories; large runtime
artifacts and all credentials remain untracked; exact external versions and
digests are recorded without Git submodules.

## Context

The working system spans four independently licensed and independently
releasable areas: upstream CARLA changes, restricted Unreal Engine changes, the
project-owned CARLA/VISS runtime, and the new AosEdge integration. Combining
them in one repository would make upstreaming difficult and could accidentally
mix public code with restricted source, credentials, or multi-gigabyte VM
artifacts.

## Decision

Maintain these repository boundaries:

| Repository | Visibility | Ownership |
| --- | --- | --- |
| `alexmaninblack/carla` | Public fork | CARLA changes that may later be proposed upstream |
| `alexmaninblack/UnrealEngine` | Private/restricted | Epic/CarlaUnreal engine compatibility changes only |
| `alexmaninblack/carla-ego-runtime` | Public | Ego vehicle lifecycle, control, VSS 6.0 projection, and VISS 3.1 server |
| `alexmaninblack/aosedge-sdv-demo` | Public | AosVM macOS lifecycle, orchestration, tests, qualification, and solution documentation |

Use one integration repository rather than separate launcher, consumer, and
adapter repositories during the proof of concept. Split a component only when
it has an independent release cadence or a reusable public API.

Do not use Git submodules initially. Record upstream versions, URLs, and
cryptographic digests in configuration and documentation. Build and runtime
scripts consume checked-out sibling repositories or installed packages through
explicit paths.

## Branch and release strategy

- `main` contains reviewed, reproducible milestone baselines.
- Work occurs on one branch per bounded milestone or feature, beginning with
  `feature/aos-0-arm64-vm`.
- Merge only after the milestone's acceptance checks pass.
- Tag accepted integration baselines using semantic versions, beginning with
  `v0.1.0` for AOS-0.
- Keep CARLA and Unreal Engine changes on branches in their own forks; never
  carry their source as patches in this integration repository unless an
  upstream review explicitly requires a small, license-safe patch artifact.

## Tracked content

- launch and lifecycle scripts;
- non-secret configuration examples;
- OCI service source and package metadata;
- automated tests;
- VSS/VISS-to-AOS mapping definitions owned by this project;
- architecture decisions, runbooks, and sanitized acceptance results;
- upstream release identifiers and SHA-256 values.

## Untracked content

- downloaded AosVM archives, disks, firmware, and mutable overlays;
- local VM lifecycle metadata and pre-/post-provision recovery checkpoints;
- SDK virtual environments and caches;
- provisioning state;
- OEM, Service Provider, Fleet Owner, Unit, or TLS private keys;
- `.p12`, `.pfx`, tokens, passwords, or account-specific configuration;
- raw logs, run manifests, packet captures, and crash dumps;
- CARLA, Unreal Engine, or AosCore build output;
- restricted Unreal Engine source, binaries, headers, assets, and content.

The AosEdge SDK stores user certificates outside the repository, normally under
the user's AOS configuration directory. Integration scripts accept paths to
those resources at runtime and never copy them into the project tree.

## Upstream changes

Prefer a project-owned wrapper around the released AosVM image. If a defect
requires changing `AosEdge/meta-aos-vm` or `AosEdge/aos_vis`, create a focused
fork branch and keep the source modification there. The integration repository
records the fork commit temporarily and returns to an upstream release after
the fix is accepted.

## Public-release gate

Before creating or pushing the GitHub repository:

1. choose and add the project license;
2. review all tracked files for redistribution rights;
3. scan for credentials, private URLs, certificates, archives, binaries, and
   user-specific paths;
4. confirm a clean checkout can run documentation and static tests without
   CARLA, Unreal Engine, or an AosCloud account;
5. ensure every downloaded dependency is pinned by version and digest;
6. confirm all product-facing text, logs, comments, examples, and documents are
   in English.

## Consequences

The repositories can be released and upstreamed independently, and large or
sensitive artifacts stay out of Git. The cost is that a top-level integration
run must know the paths or installed versions of multiple sibling projects.
That relationship will be captured in explicit local configuration rather than
hidden in a monorepo or submodule graph.
