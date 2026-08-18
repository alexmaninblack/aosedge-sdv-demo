<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Architecture and Repository Ownership

The accepted end-to-end architecture baseline, including shared platform FOTA,
independent SOTA lifecycles for two peer OEM functional teams, bidirectional
KUKSA/VISS flows, local analytics, Cloud reporting, and engineering-dashboard
boundaries, is defined in
[High-Level Architecture 1.2](high-level-architecture.md).

## Runtime Boundary

```mermaid
flowchart LR
    subgraph macOS["macOS development host"]
        CARLA["CARLA simulator"]
        VISS["carla-ego-runtime / VISS 3.1"]
        CARLA --> VISS
    end

    subgraph AosVM["AosVM vehicle computer"]
        PROVIDER["vehicle-data provider / OEM FOTA"]
        BROKER["Aos–KUKSA Credential Broker<br/>OEM policy / FOTA"]
        KUKSA["unmodified Eclipse KUKSA Databroker"]
        SERVICE1["Brake Health service / SOTA 1"]
        SERVICE2["Tire Health service / SOTA 2"]
        PROVIDER -->|"kuksa.val.v1"| KUKSA
        KUKSA -->|"versioned VSS contract"| SERVICE1
        KUKSA -->|"versioned VSS contract"| SERVICE2
        SERVICE1 -. "AOS_SECRET to short-lived JWT" .-> BROKER
        SERVICE2 -. "AOS_SECRET to short-lived JWT" .-> BROKER
        BROKER -. "public verifier" .-> KUKSA
    end

    VISS -->|"private verified VISS 3.1 route"| PROVIDER
```

CARLA and VISS run on macOS. The provider, KUKSA Databroker, Service Manager
runtime, SELinux boundary, and independently deployed functional services run
in AosVM. The provider is not part of CARLA and neither service connects to
VISS directly.

In a production vehicle, CAN, SOME/IP, DDS, or another OEM provider replaces
the simulation-specific VISS provider. KUKSA and the versioned VSS contract
remain the stable service boundary.

## Lifecycle Boundary

| Repository | Owns | Lifecycle |
| --- | --- | --- |
| `carla-ego-runtime` | ego control and VISS projection | simulation tooling |
| `aos-vehicle-platform` | Vehicle Data Platform Component: providers, contract/configuration, Aos–KUKSA Credential Broker and OEM access policy; plus Service Manager runtime and KUKSA integration | OEM platform/FOTA |
| `brake-health-service` | Function Team 1 Brake Health consumer and local analytics | Service Provider 1/SOTA 1 |
| `tire-health-service` | Function Team 2 local tire-condition estimation, bounded reporting, offline state and typed inspection advisory | Service Provider 2/SOTA 2; accepted boundary, repository not yet created |
| `brake-health-cloud` | Function Team 1 backend and Brake Health Function Dashboard | Function Team 1 Cloud product; accepted boundary, repository not yet created |
| `tire-health-cloud` | Function Team 2 backend and Tire Health Function Dashboard | Function Team 2 Cloud product; accepted boundary, repository not yet created |
| `aosedge-sdv-demo` | macOS VM lifecycle, provisioning, locks, orchestration, system documentation, and end-to-end qualification | solution/demo baseline |

The integration repository may pin and qualify every component, but it does
not become the source repository for those components. No Git submodule or
private local checkout path is part of a public baseline.

The planned Function Team 2 repository is intentionally not present in the
machine-readable workspace contract until its license, initial scaffold and
accepted revision are reviewed. Its name and in-vehicle SOTA ownership
boundary are already accepted. Functional backends and dashboards are
separate products: each Function Team owns one planned Cloud-product
repository, distinct from its in-vehicle SOTA repository.

## Trust and Network Boundary

- VISS listens only on the macOS loopback path used by the VM bridge.
- The provider verifies TLS and receives credentials through systemd, not its
  payload or command line.
- Upstream Eclipse KUKSA remains unchanged as the in-vehicle data interface
  exposed to services and verifies only the Platform Team's configured public
  key.
- The Vehicle Data Platform Component owns the Aos–KUKSA Credential Broker and
  FOTA-managed OEM access policy. It derives short-lived, path-scoped JWTs from
  an authenticated Aos service instance's `AOS_SECRET`; prototype tokens are
  historical qualification fixtures, not the target architecture.
- VM provisioning identity, OEM signing identity, user certificates, private
  keys, Cloud tokens, and raw operational evidence remain outside Git.

## Update Boundary

The rootfs supplies the provider runtime, A/B store, launcher, systemd units,
health contract, and SELinux policy. The provider bundle supplies only its
immutable application payload and runtime libraries. Therefore provider
updates can follow their own FOTA lifecycle after a compatible rootfs is
installed.

The demonstration nested ext4 store preserves isolation on the fixed-context
AosVM workdirs mount. Production storage remains a separate OEM architecture
decision. Rootfs rollback from `.11` to `.2` is not provider-transparent; the
provider assignment must first be suspended or removed.

See [ADR 0006](decisions/0006-lifecycle-based-repository-ownership.md) for the
accepted repository decision,
[ADR 0010](decisions/0010-aos-kuksa-credential-broker.md) for the credential
boundary, and
[the current baseline](../qualification/current-baseline.md)
for exact versions and digests.
