# CARLA–AosEdge Integration

This repository makes the Apple Silicon CARLA-to-AosEdge demonstration
reproducible. It owns macOS AosVM lifecycle, single-Node provisioning,
component locks, end-to-end qualification, and operational documentation. It
does not vendor CARLA, Unreal Engine, AosCore, AosVM images, provider source,
or telemetry-service source.

## Current Baseline

| Area | Accepted state |
| --- | --- |
| macOS VM | Official AosVM 6.1.0 `qemuarm64` runs with QEMU/HVF on Apple Silicon |
| Cloud identity | One persistent, provisioned Main Node; no Secondary Node |
| Simulation bridge | CARLA VISS 3.1 telemetry reaches the in-VM KUKSA Databroker |
| Provider | `0.2.0` is signed and locally verified; not published or assigned |
| Platform runtime | Service Manager A/B runtime, fixed `aos-vdp` identity, SELinux policy, and bounded demo store are implemented |
| Rootfs candidate | `6.1.1-maninblack.11` is frozen locally, unsigned, and not uploaded or installed |
| Installed Units | validation Unit: `.2`; demonstration Unit: `6.1.0` |

Candidate `.11` closes the complete provider runtime dependency chain under
SELinux Enforcing. Signing, Cloud upload, assignment, and provisioned-Unit
mutation are intentionally separate approval gates. See the
[exact current baseline](docs/current-baseline.md).

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

Read [architecture and repository ownership](docs/architecture.md) for the
complete boundary.

## Start Here

For a new Apple Silicon Mac, follow the
[colleague setup guide](docs/aosvm-macos-colleague-setup.md):

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

- [Current accepted baseline](docs/current-baseline.md)
- [Architecture and ownership](docs/architecture.md)
- [Roadmap and next gates](docs/roadmap.md)
- [Run AosVM on Apple Silicon](docs/aos-0-arm64-vm.md)
- [Provision one Main Node](docs/aos-1-single-node-provisioning.md)
- [CARLA VISS-to-KUKSA qualification](docs/aos-2-carla-kuksa-qualification.md)
- [Current R6.1 demo-store design](docs/r6-1-demo-isolated-provider-store.md)
- [Validation-set scope defect](docs/r6-1-validation-set-scope-defect.md)
- [Exact component lock](docs/component-lock.md)
- [Licensing and copyright policy](docs/licensing-and-copyright-policy.md)
- [Architecture decisions](docs/decisions/0001-repository-and-artifact-boundaries.md)

Completed experimental plans, rejected rootfs iterations, and one-shot
diagnostic helpers are intentionally absent from the current tree. Git history
retains them when forensic detail is needed.

## Security and License

Never commit private keys, certificates, tokens, provisioned identities, VM
overlays, signing output, or raw operational logs. Public evidence must remain
sanitized and reproducible.

Original integration work is MIT-licensed under the exact copyright name
`maninblack`. Platform and service repositories use Apache-2.0. Third-party
material retains its own terms; see [LICENSE](LICENSE) and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
