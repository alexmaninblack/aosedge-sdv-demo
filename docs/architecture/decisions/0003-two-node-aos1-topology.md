# ADR 0003: Use the Official Two-Node AosVM Topology in AOS-1

- Status: Superseded by ADR 0004
- Date: 2026-08-13

This decision was superseded after the official generic provisioning path was
confirmed to support `aos-prov provision --nodes 1` for an AosVM-derived image.
[ADR 0004](0004-single-main-node-for-aos1.md) records the current single-Node
decision. This file remains as the history of why the initial two-Node baseline
was considered.

## Context

AOS-0 qualified the official AosVM `v6.1.0` ARM64 Main Node on one Apple M5
Pro. The release archive also contains a Secondary Node disk, but AOS-0 kept it
immutable and unused so that host virtualization, the Main Node guest kernel,
local OCI runtime, networking, and lifecycle could be proven independently of
multi-Node behavior.

AOS-1 will register and provision a Unit through the tools supplied by the
AosEdge SDK. We therefore need to decide whether that Unit contains only the
qualified Main Node or follows the official AosVM demonstration topology.

The official `v6.1.0` Unit Configuration contains two entries:

- `aos-vm-main`, labelled `main`, priority 100;
- `aos-vm-secondary`, labelled `secondary`, priority 50.

The official AosVM registration guide also says that the SDK `unit-new` flow
creates two VMs and waits until the Secondary Node connects. A Secondary Node
registers with the Main Node IAM, while the Main Node maintains the Unit's Node
registry and forwards provisioning operations. Provisioning only one released
disk would therefore diverge from the documented AosVM configuration before we
have a concrete requirement to do so.

Two Nodes do not imply two physical computers. The M5 Pro has enough qualified
host memory for two 2 GiB guests, and both can run as separate QEMU/HVF system
VMs on the same Mac.

## Decision

Use one Main Node VM and one Secondary Node VM on the same Apple Silicon host
for AOS-1.

Before supplying any SDK credential or starting provisioning, AOS-1 must:

1. create a disposable overlay for the verified Secondary Node base;
2. give each VM a unique name, MAC address, runtime state, serial/QMP sockets,
   loopback host forwards, and owned lifecycle;
3. provide deterministic private Main-to-Secondary connectivity without an
   external LAN listener or administrator-owned host networking;
4. qualify the Secondary Node's ARM64 boot, required compatibility state,
   restart, reset, and cleanup behavior;
5. prove that both Nodes can be started and stopped independently and as one
   Unit without targeting unrelated processes;
6. use the official SDK and `v6.1.0` Unit Configuration for registration,
   certificates, and provisioning.

No repository script will reimplement the AosEdge provisioning protocol or
store SDK credentials, certificates, tokens, private keys, or account-specific
configuration.

## Consequences

### Positive

- Matches the released images, official Unit Configuration, and documented SDK
  demonstration flow.
- Exercises the multi-Node feature that the AosVM package is intended to show.
- Avoids treating the unused Secondary disk as release baggage without testing
  that assumption.
- Keeps all work on the existing Mac and requires no second physical computer.

### Costs and constraints

- AOS-1 needs a two-VM network and lifecycle layer before cloud provisioning.
- Loopback ports, MAC addresses, IP addresses, overlays, and runtime files must
  be unique per Node.
- The Secondary Node is not covered by the AOS-0 acceptance result and must
  pass its own local gates.
- The host will reserve approximately 4 GiB of RAM and four vCPUs while both
  default-sized VMs are running.

## Alternatives considered

### Provision only the Main Node

Deferred. This is simpler locally but diverges from the official AosVM Unit
Configuration and automated registration flow. Revisit it only if the SDK
explicitly supports a single-Node Unit and the telemetry demonstration gains a
clear reason to avoid the Secondary Node.

### Use a second physical computer

Rejected for the current demonstration. AosEdge Nodes are logical systems;
QEMU/HVF already gives each Node its own full Linux kernel and isolated system
environment on the same host.

## References

- [Register a device with AosVM](https://docs.aosedge.tech/docs/how-to/register-your-device/with-aos-vm/)
- [AosVM v6.1.0 Unit Configuration](https://github.com/AosEdge/meta-aos-vm/releases/download/v6.1.0/unitconfig.json)
- [AosVM v6.1.0 release](https://github.com/AosEdge/meta-aos-vm/releases/tag/v6.1.0)
- [AosEdge Node identity](https://docs.aosedge.tech/docs/aos-core/architecture/identity-access-manager/node-identity)
