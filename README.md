# AosEdge SDV Demo

This is the solution-integration repository for the Apple Silicon AosEdge
software-defined vehicle demonstration. It owns the system architecture,
audience-visible scenarios, macOS AosVM lifecycle, cross-project contracts,
workspace locks, orchestration, qualification and operator documentation. It
does not vendor CARLA, Unreal Engine, AosCore, AosVM images, platform-component
source or functional-service source.

The current engineering candidate is **Kit028 / Setup042 / Factory .41**,
published as source checkpoint `candidate/kit028-setup042`. Operators use a
complete prebuilt DMG; Unreal Editor and source compilation are not required
on the demo Mac. This is not yet a notarized public release or a completed
native end-to-end acceptance.

## Current baseline — 7 October 2026

The audience-facing name is **AosEdge Platform - SDV Lab**. One Test controller
uses real AosCore, KUKSA and local service authorization; CARLA simulates the
vehicle. VDP V1/V2/V3 arrives through Safe Stop-gated FOTA. Independent Brake
V1/V2/V3 and Tire V1 containers arrive through SOTA. One associated SP owns
both services in the first-install topology.

The installed M1 campaign passed 98 scripted steps, including serial updates,
real products, resets, offline backlog recovery and same-identity ignition.
The complete native journey, moving SOTA, secure UI token entry and installation
interruption/repair remain open. See the
[current baseline](docs/qualification/current-baseline.md) for exact pins and
limits, the [operator workflow](docs/operations/current-demo-workflow.md) for
actions, and the [documentation reconciliation](docs/qualification/documentation-reconciliation-2026-10-07.md)
for remaining inconsistencies. Old tags, including
[demo-v1.1](docs/qualification/demo-v1.1-return-point.md), keep their historical
evidence; they do not select the current installer.

## Architecture

```text
Virtual vehicle and Gateway                  AosVM Domain Controller

CARLA -> Vehicle Gateway -> VISS 3.1 -> Vehicle Data Platform Component
                                           provider + contract
                                                    |
                                                    v
                                         KUKSA Databroker
                                              /             \
                                             v               v
                                  Brake Health service   Tire Health service

AosCore Service Manager/IAM -> platform credential boundary -> Service-private JWT
                               current release: removable helper
```

The Vehicle Data Platform Component follows the OEM Platform Team/FOTA
lifecycle. Brake Health and Tire Health are peer Function Team products
with independent Service Provider/SOTA lifecycles. The Gateway-to-KUKSA
contract separates simulated vehicle hardware from service-facing data. A
production vehicle replaces the CARLA side with real vehicle networks while
preserving the service contract.

Service Manager and Aos IAM own each SOTA instance identity, secret and
registered permissions. The permanent target keeps credential preparation
platform-controlled and implementation-neutral. The current release uses a
separately packaged removable helper outside the VDP and both SOTA artifacts
to derive short-lived, Service-private, path-scoped KUKSA JWTs. Services do not
carry reusable KUKSA tokens, select their own authority, create a parallel
identity/policy store. The current platform includes a bounded KUKSA scope-path
compatibility patch; this is platform-owned, not service-owned authority.

Read [architecture and repository ownership](docs/architecture/repository-boundaries.md) for the
complete boundary.

## Start Here

- **Run the prebuilt demo:** [installation and Cloud first use](docs/getting-started/installed-preview-cloud-first-use.md).
- **Build or modify it:** [source reproduction](docs/getting-started/reproduce-demo.md).
- **Understand it:** [implemented architecture](docs/architecture/current-implementation.md),
  then the canonical requirements/design chain.
- **Run AosVM alone:** [standalone engineering guide](docs/operations/aosvm-apple-silicon.md).
  Do not layer standalone launchers over an installed Demo Control instance.

The installer, Presenter and CLI use the same Demo Control owners. Installation,
Cloud access, controller creation, provisioning and software installation are
separate steps. Never copy a provisioned overlay or roll back a release ledger.
Keep credentials and mutable demo data separate from immutable program inputs.

The machine-readable contract is
[`workspace/repositories.json`](workspace/repositories.json). It pins each
sibling checkout, its role, visibility, branch, and accepted revision without
vendoring repositories or using Git submodules.

## Local Validation

The safe repository-only gates do not sign, call mutating Cloud APIs, or alter
a provisioned VM:

```sh
./scripts/docs-check
./scripts/validate-component-lock
./scripts/validate-r6-1-source-lock
./scripts/validate-r6-1-manifest
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Documentation

- [Documentation map](docs/README.md)
- [Getting started](docs/getting-started/README.md)
- [Reproduction guide and readiness matrix](docs/getting-started/reproduce-demo.md)
- [High-Level Architecture 1.8 — accepted](docs/architecture/high-level-architecture.md)
- [System Requirements and Traceability 2.2 — accepted](docs/requirements/system-requirements-and-traceability.md)
- [Component Decomposition and Interface Register 2.2 — accepted](docs/requirements/component-decomposition-and-interface-register.md)
- [R9 Demo Foundation Research](docs/research/demo-foundation/README.md)
- [Current candidate and qualification limits](docs/qualification/current-baseline.md)
- [Roadmap and next gates](docs/planning/roadmap.md)
- [Run AosVM on Apple Silicon](docs/operations/aosvm-apple-silicon.md)
- [Development map](docs/development/README.md)
- [Architecture decisions](docs/architecture/decisions/0001-repository-and-artifact-boundaries.md)

Completed experimental plans, rejected rootfs iterations, and one-shot
diagnostic helpers are intentionally absent from the current tree. Git history
retains them when forensic detail is needed.

## Security and License

Never commit private keys, certificates, tokens, provisioned identities, VM
overlays, signing output, raw operational logs, or customer/OEM source
material. The prohibition on confidential source material also applies to
private repositories. Public evidence must remain sanitized and reproducible;
see [confidential source handling](docs/governance/confidential-source-handling.md).

Original integration work is MIT-licensed under the exact copyright name
`maninblack`. Platform and service repositories use Apache-2.0. Third-party
material retains its own terms; see [LICENSE](LICENSE) and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
