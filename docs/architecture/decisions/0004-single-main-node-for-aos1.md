# ADR 0004: Start AOS-1 with One Main Node

- Status: Accepted for AOS-1; supersedes ADR 0003
- Date: 2026-08-13

## Context

AOS-0 qualified the official AosVM `v6.1.0` ARM64 Main Node on the Apple M5
Pro. ADR 0003 initially selected the release's Main + Secondary demonstration
topology because the official `unit-new` workflow and released Unit
Configuration use both images.

Further review separated the AosEdge architecture from that convenience
workflow:

- an AosEdge Unit contains one or more Nodes, and the documented simplest case
  is one Node running the complete core stack;
- the released Main Node identifies itself with the `MainNode` attribute and
  contains IAM, Service Manager, and Communication Manager;
- only the Secondary configuration names the Main IAM endpoints, so the
  dependency is Secondary-to-Main rather than Main-to-Secondary;
- the official device guide explicitly recommends
  `aos-prov provision --nodes 1` for a single Linux image derived from AosVM;
- the published `aos-prov` package accepts a single Node, an `IP:PORT` Unit
  address, and provisioning protocol v5 on IAM port `8089`.

The CARLA integration initially needs one cloud-managed telemetry service. It
does not yet need workload rebalance, heterogeneous compute Nodes, inter-Node
file distribution, or failure migration.

## Decision

AOS-1 will provision only the already qualified Main Node as a single-Node
Unit. It will continue to run as one QEMU/HVF VM on the M5 Pro.

Use the generic SDK provisioning command with an explicit Node count, not the
VirtualBox-owning `unit-new` workflow:

```text
aos-prov provision -u 127.0.0.1:<provision-host-port> --nodes 1
```

The tracked non-secret Unit Configuration must declare only `aos-vm-main`.
The QEMU launcher will expose guest IAM port `8089` through a temporary
loopback-only host forward during provisioning. Normal launches will not
contain that forward.

The AosEdge SDK remains responsible for the provisioning protocol,
certificate issuance, PKCS#11 key creation, and cloud registration. Repository
code must not reimplement those operations or store any credential.

## Consequences

### Positive

- Reuses the complete Main Node baseline already accepted by AOS-0.
- Removes the unqualified Secondary lifecycle and inter-Node network from the
  critical path to the first cloud-managed telemetry service.
- Uses roughly half the guest CPU and memory of the two-VM topology.
- Reduces boot, shutdown, networking, certificate, and failure-state
  complexity.
- Remains an officially documented AosEdge provisioning configuration.

### Costs and constraints

- Dynamic Rebalance and workload migration between Nodes are unavailable.
- The single Main Node is the only execution and cloud-coordination point.
- The official two-Node `unitconfig.json` cannot be used unchanged; cloud Unit
  Configuration must match the one-Node topology.
- Adding a Secondary to an already provisioned Unit is not part of AOS-1 and
  must not be assumed safe without a separate lifecycle test.

## Deferred multi-Node path

Keep the verified Secondary base image immutable and ignored. If a concrete
multi-Node use case appears, qualify it as a separate milestone and preferably
as a separate Unit first. That work must define Secondary ownership, a private
inter-Node network, unique identity and ports, placement policy, failure
behavior, and cloud topology migration.

## Security boundaries

- User tokens, `.p12` files, private keys, SDK secure state, Unit identifiers,
  and raw provisioning logs remain outside Git.
- The email token command is run by the user locally and is never pasted into
  this repository or chat.
- Provisioning IAM is forwarded only to `127.0.0.1` and only in an explicit
  provisioning launch mode.
- A failed or partial provisioning attempt is preserved for diagnosis; the
  overlay is not reset until cloud and local identity state are reconciled.

## References

- [AosEdge key concepts](https://docs.aosedge.tech/docs/aos-core/system-overview/key-concepts)
- [Build and provision an HPC device](https://docs.aosedge.tech/docs/how-to/register-your-device/with-your-HPC-device)
- [Provision a device](https://docs.aosedge.tech/docs/how-to/tutorials/device/provision-device)
- [AosVM v6.1.0 Main IAM configuration](https://github.com/AosEdge/meta-aos-vm/blob/v6.1.0/meta-aos-vm-main/recipes-aos/aos-iamanager/files/iam.cfg)
- [AosVM v6.1.0 Main Service Manager configuration](https://github.com/AosEdge/meta-aos-vm/blob/v6.1.0/meta-aos-vm-main/recipes-aos/aos-servicemanager/files/sm.cfg)
