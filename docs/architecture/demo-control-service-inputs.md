<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Temporary Test service inputs

Status: bounded interface authorized on 10 September 2026; not implemented
or guest-qualified. This closes the interface choice in the
[Studio plan](../planning/active/demo-studio-delivery-plan.md), not its P5 gate.
Factory `.31`, Production and native Aos service authorization remain unchanged.

## Read-only payload

Demo Control owns the projection. A dedicated resource for each service maps
only that service's runtime-input directory into the container read-only with
`nosuid,nodev,noexec`. It contains `metadata.json` and `kuksa-ca.pem`; no keys,
tokens, arbitrary host directories or other service metadata are included.
Directory binding permits an atomic replacement to remain visible to the
service. Brake uses the existing `--metadata-file` and `--ca-file` arguments.
The existing `kuksa` and `kuksa-auth-client` resources are still required.

| Metadata field | Authoritative binding |
| --- | --- |
| `schemaVersion` | Integer `1` |
| `unitSystemUid` | Native IAM `GetSystemInfo.system_id`, matching the current successful provisioning journal; not Cloud Unit UUID |
| `unitRole` | Demo Control's initialized guest role under `systemd-slot-component/demo-inputs/role`; Test maps to `validation` |
| `serviceVersion` | Selected signed candidate's exact release, subsequently reconciled with the actual SM instance version |
| `serviceArtifactSha256` | SHA-256 of the selected ARM64 OCI image manifest, matching native SM `manifestDigest`; not binary, signed bundle or layer digest |
| `vdpContractVersion` | Literal `contracts.vdpCompatibility.contractVersion` in the verified committed active capability manifest |
| `vdpContractSha256` | Its `contracts.vdpCompatibility.sha256`; not the entire capability-manifest hash |

The current VDP compatibility pair is version `1.0.1` and digest
`8e58e18e9d99a13409af6813e573cbe1c690e439ad746224426801f6b080c871`.
Functional profile v1/v2/v3 and monotonic Cloud release numbers are separate.
The public TLS source is only `/var/lib/aos-kuksa-tls/server.pem`, whose SAN
supports `Server`; its sibling private key is never projected.

## Ordering and temporary application

1. Resolve the current IAM identity, initialized role, exact signed candidate
   and committed active VDP contract. Prepare the read-only inputs before
   service assignment: bootstrap needs them before process launch.
2. Preserve all effective SM configuration/resources, adding only the dedicated
   resource in a temporary `/run` copy. The pinned SM key is
   `resourcesConfigFile`, not a guessed alternative.
3. Use a narrow systemd read-only config binding and one SM restart on Test;
   the resource manager loads the file at Init and has no evidenced hot reload.
   No rootfs remount, SM binary replacement or Factory rebuild is implied.
4. After assignment, reconcile actual native instance version/manifest digest
   against the selected tuple. A mismatch is not a successful integration.
5. Project VDP changes only after committed slot/process agreement, not when
   the active symlink first changes during an unfinished transaction. Refresh
   the actual compatibility pair atomically. Queued messages retain their old
   provenance. The existing Brake watcher reconnects on metadata/trust change.
6. Prove exact SELinux/systemd access, KAC renewal and TLS subscription with the
   service identity. Remove the temporary override after the bounded proof or
   explicitly record its retained state. No broad permissions or TOFU fallback.

Source evidence: pinned AosCore
[`config.cpp`](https://github.com/aosedge/aos_core_cpp/blob/9eecb80c4994937b5c8cbe0464970f81e8ad4c2d/src/sm/config/config.cpp#L126),
[`resourcemanager.cpp`](https://github.com/aosedge/aos_core_cpp/blob/9eecb80c4994937b5c8cbe0464970f81e8ad4c2d/src/sm/resourcemanager/resourcemanager.cpp#L92)
and [`instance.cpp`](https://github.com/aosedge/aos_core_cpp/blob/9eecb80c4994937b5c8cbe0464970f81e8ad4c2d/src/sm/launcher/runtimes/container/instance.cpp#L198).
This projection does not give analytics new IAM/network authority; KUKSA
credentials continue through the existing accepted KAC exchange.
