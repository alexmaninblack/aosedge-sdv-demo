# AosEdge SDV Demo

This solution repository makes the Apple Silicon AosEdge software-defined
vehicle demonstration reproducible. It owns macOS AosVM lifecycle, single-Node
provisioning, cross-project orchestration, component locks, end-to-end
qualification, demo architecture, and operational documentation. It does not
vendor CARLA, Unreal Engine, AosCore, AosVM images, provider source, or
functional-service source.

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
SELinux Enforcing and remains accepted local evidence. The revised deployment
plan does not select `.11` or provider `0.2.0` for Cloud promotion: it first
adds a separate public vehicle-integration FOTA component and a dependent
provider successor. Signing, Cloud upload, assignment, and provisioned-Unit
mutation remain separate approval gates. See the
[exact current baseline](docs/qualification/current-baseline.md).
The acceptance records the already running `.1` state without approving its
stale Verification Batch or selecting it for a new rollout.

## Architecture

```text
macOS development host                         AosVM vehicle computer

CARLA -> VISS 3.1 -- private VM route --> vehicle-data provider
                                             |
                                             v
                                      KUKSA Databroker
                                             |
                                             v
                                      Aos service container
```

The vehicle-data provider and KUKSA integration follow the OEM platform/FOTA
lifecycle. The telemetry consumer follows the independent Aos service/SOTA
lifecycle. A production vehicle replaces the CARLA/VISS input with its real
vehicle-network provider while preserving the KUKSA/VSS contract.

Read [architecture and repository ownership](docs/architecture/repository-boundaries.md) for the
complete boundary.

## Start Here

For a new Apple Silicon Mac, follow the
[colleague setup guide](docs/operations/macos-colleague-setup.md):

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
./scripts/validate-component-lock
./scripts/validate-r6-1-source-lock
./scripts/validate-r6-1-manifest
python3 -m unittest discover -s tests -p 'test_*.py'
```

The isolated Yocto builder and disposable qualification VM are managed by
`scripts/r6-1-builder` and `scripts/r6-1-disposable-vm`. Their disks and build
caches live outside Git and are deliberately preserved for incremental builds.

## Documentation

- [Documentation map](docs/README.md)
- [High-Level Architecture 1.1 — review candidate](docs/architecture/high-level-architecture.md)
- [System Requirements and Traceability 0.1 — review candidate](docs/requirements/system-requirements-and-traceability.md)
- [Component Decomposition and Interface Register 0.1 — review candidate](docs/requirements/component-decomposition-and-interface-register.md)
- [R9 Demo Foundation Research](docs/research/demo-foundation/README.md)
- [Current accepted baseline](docs/qualification/current-baseline.md)
- [Roadmap and next gates](docs/planning/roadmap.md)
- [Run AosVM on Apple Silicon](docs/operations/aosvm-arm64-macos.md)
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
