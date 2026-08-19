# AosEdge SDV Demo

This is the solution-integration repository for the Apple Silicon AosEdge
software-defined vehicle demonstration. It owns the system architecture,
audience-visible scenarios, macOS AosVM lifecycle, cross-project contracts,
workspace locks, orchestration, qualification and operator documentation. It
does not vendor CARLA, Unreal Engine, AosCore, AosVM images, platform-component
source or functional-service source.

The standalone AosVM path and the CARLA engineering demonstration are
repeatable on the qualified workspace. The complete staged FOTA/SOTA story is
the current design and implementation target, not yet a one-command
fresh-checkout demo. See the
[reproduction readiness matrix](docs/getting-started/reproduce-demo.md).

## Current Baseline

| Area | Accepted state |
| --- | --- |
| macOS VM | Official AosVM 6.1.0 `qemuarm64` runs with QEMU/HVF on Apple Silicon |
| Cloud identity | One persistent, provisioned Main Node; no Secondary Node |
| Simulation bridge | CARLA VISS 3.1 telemetry reaches the in-VM KUKSA Databroker |
| Provider | `0.2.0` is signed and locally verified; not published or assigned |
| Platform runtime | Service Manager A/B runtime, fixed `aos-vdp` identity, SELinux policy, and bounded demo store are implemented |
| Rootfs candidate | `6.1.1-maninblack.11` is frozen locally, unsigned, and not uploaded or installed |
| Installed Units | validation Unit: `.2`; demonstration Unit: `.1`, accepted as the current operational baseline after end-to-end verification |

Candidate `.11` closes the qualified provider runtime dependency chain under
SELinux Enforcing and remains accepted local evidence. It is not the accepted
clean factory artifact or selected for Cloud promotion. Signing, Cloud upload,
assignment, and provisioned-Unit mutation remain separate approval gates. See the
[exact current baseline](docs/qualification/current-baseline.md).
The acceptance records the already running `.1` state without approving its
stale Verification Batch or selecting it for a new rollout.

## Architecture

```text
Virtual vehicle and Gateway                  AosVM Domain Controller

CARLA -> Vehicle Gateway -> VISS 3.1 -> Vehicle Data Platform Component
                                           provider + contract +
                                         thin Credential Broker
                                                    |
AosCore Service Manager/IAM ------------------------+  (instance permissions)
                                                    v
                                      unmodified KUKSA Databroker
                                              /             \
                                             v               v
                                  Brake Health service   Tire Health service
```

The Vehicle Data Platform Component follows the OEM Platform Team/FOTA
lifecycle. Brake Health and Tire Health are peer Function Team products
with independent Service Provider/SOTA lifecycles. The Gateway-to-KUKSA
contract separates simulated vehicle hardware from service-facing data. A
production vehicle replaces the CARLA side with real vehicle networks while
preserving the service contract.

Service Manager and Aos IAM own each SOTA instance identity, secret and
registered permissions. Services use that identity to obtain short-lived,
path-scoped KUKSA JWTs from the component-owned thin broker. They do not carry
reusable KUKSA tokens, create a parallel identity/policy store, or modify
Eclipse KUKSA.

Read [architecture and repository ownership](docs/architecture/repository-boundaries.md) for the
complete boundary.

## Start Here

Choose the path that matches your goal in [Getting Started](docs/getting-started/README.md):

- run AosVM on an Apple Silicon Mac;
- reproduce the currently available engineering demonstration;
- understand the architecture;
- modify an existing component;
- add a demo scenario.

For AosVM itself, follow the canonical
[Apple Silicon guide](docs/operations/aosvm-apple-silicon.md):

```sh
./scripts/aosvm-macos-onboard doctor
./scripts/aosvm-macos-onboard bootstrap
./scripts/aosvm-macos-onboard setup
```

Provisioning is never implicit. It requires an existing OEM certificate, a
read-only preflight, and explicit confirmation.

For the existing persistent VM:

```sh
./scripts/aosvm status
./scripts/aosvm start
./scripts/aosvm smoke-test
./scripts/aosvm stop
```

Do not reset or copy a provisioned overlay. Its disk contains a unique Cloud
identity and must remain persistent across stops, Mac sleep, and network
changes.

For the complete sibling-repository workspace, run the read-only doctor before
a demo or migration:

```sh
./scripts/workspace-doctor
```

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
- [High-Level Architecture 1.4 — accepted architecture baseline](docs/architecture/high-level-architecture.md)
- [System Requirements and Traceability 0.9 — accepted system-requirements baseline](docs/requirements/system-requirements-and-traceability.md)
- [Component Decomposition and Interface Register 0.9 — accepted component baseline](docs/requirements/component-decomposition-and-interface-register.md)
- [R9 Demo Foundation Research](docs/research/demo-foundation/README.md)
- [Current accepted baseline](docs/qualification/current-baseline.md)
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
