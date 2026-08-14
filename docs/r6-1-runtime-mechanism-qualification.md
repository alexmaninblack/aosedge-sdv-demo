<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R6.1-1 Runtime-Mechanism Qualification

- Status: Complete; mechanism accepted
- Date started: 2026-08-14
- Date completed: 2026-08-14
- Authorized scope: R6.1-1 only
- Source baseline: `components/r6-1-source.lock.json`

## Objective

Prove, without changing AosCloud or the active demonstration Unit, whether a
dedicated vehicle-data-provider component can use the Aos Service Manager
runtime boundary and report its component type through the local Node/CM path.

This record distinguishes inspected facts from hypotheses. It must not be used
as evidence that Cloud catalog acceptance, deployment, update, or rollback has
already passed.

## Safety Boundary

R6.1-1 may create an isolated, non-provisioned Linux ARM64 build VM and local
runtime harnesses. It must not:

- deprovision or reprovision the existing Unit;
- modify the active AosVM disk, Unit Model, Node Type, certificates, or Cloud
  registration;
- publish a component, alter a Cloud catalog, or assign a deployment;
- copy an Aos Unit identity, user certificate, OEM signing key, one-time token,
  or other persistent credential into the builder;
- replace the released AosVM image or claim a bootstrap image is qualified.

## Exact Source Baseline

The machine-readable candidate lock resolves the released AosVM 6.1.0 manifest
to exact commits for `poky`, OpenEmbedded, virtualization, security, SELinux,
`meta-aos`, `meta-aos-vm`, the relevant AosCore repositories, and Moulin 0.21.
It also records the exact Service Manager recipe `SRCREV` instead of assuming
that the public `aos-core-cpp` v9.1.0 tag describes the released recipe.

Run:

```text
./scripts/validate-r6-1-source-lock
python3 -m unittest tests.test_r6_1_source_lock
```

Current result: the validator passes for 12 sources and all negative tests
pass. The lock is `accepted` for the R6.1-1 mechanism boundary. It does not
accept a production runtime, bootstrap image, FOTA artifact, or Cloud
deployment.

## Recorded Upstream Gaps

1. The released `aos-vm.yaml` selects the floating `meta-arm` `scarthgap`
   branch. The project candidate pins the latest commit on that branch before
   the AosVM 6.1.0 release timestamp. This is an explicit audited resolution,
   not proof of the exact upstream release checkout.
2. The `aos-core-cpp` v9.1.0 public tag does not identify the revision selected
   by the `meta-aos` v9.1.0 Service Manager recipe. The candidate therefore
   pins the recipe `SRCREV`.

Neither gap permits a floating source in a project build.

## Builder Baseline

The isolated builder candidate is:

- Ubuntu Server 22.04 LTS ARM64 cloud image, release `20260722`, verified by
  the SHA-256 digest in the source lock;
- QEMU 11.0.3 with Apple Hypervisor Framework acceleration;
- 10 virtual CPUs, 24 GiB memory, and a 220 GiB sparse virtual disk;
- SSH bound only to host loopback port 10023;
- a dynamic macOS resolver bridge bound only to loopback port 18054, with the
  guest using the QEMU host alias and an explicit non-default DNS port;
- no Aos services, Unit identity, Cloud certificate, or signing credential.

The virtual disk is stored outside Git under the project's private macOS
application-support directory. Its nominal 220 GiB capacity is sparse, but
host free-space checks remain mandatory because a Yocto build may consume much
of that capacity.

The builder lifecycle passed on 2026-08-14. The pinned image download and
firmware digests matched, preparation produced a verified sparse overlay, and
the dry-run exposed only loopback SSH and DNS listeners. The first boot passed
cloud-init and the smoke gate. A clean stop, restart with the same disk and SSH
host key, repeated smoke gate, and final clean stop also passed. The observed
guest evidence was ARM64, 10 CPUs, ext4 root storage larger than 200 GB, and no
Aos services or standard Aos identity paths. Qualification tools were pinned
to GCC 11.4.0, Conan 2.31.2, CMake 3.31.10, clang-format 15.0.7, and SoftHSM
2.6.1. The idempotent tool bootstrap passed. The builder and DNS bridge are
stopped after the qualification run.

Standard QEMU DNS was not accepted as sufficient: on the active Mac network,
the guest's `10.0.2.3` resolver timed out. The builder now reuses the tracked
loopback-only, resolver-refreshing macOS bridge already qualified for AosVM.
The guest uses systemd-resolved's supported `address:port` syntax to reach
`10.0.2.2:18054`. The final DNS probe and restart gate passed without TAP,
administrator privilege, packet-filter changes, or LAN exposure.

## Service Manager Evidence

Inspection of the exact locked sources currently establishes:

- Service Manager implements `RuntimeItf` factories for `container`, `boot`,
  and `rootfs`; a vehicle-data-provider runtime is not present in the release;
- `SMClient::SendSMInfo()` sends the runtime inventory to CM;
- Service Manager protocol v5 `SMInfo` contains repeated `RuntimeInfo` records;
- `RuntimeInfo` carries runtime ID, type, architecture, OS, and resource data;
- `isComponent` participates in the Yocto runtime configuration but is not a
  field of the transmitted `RuntimeInfo` record.

The exact-source ARM64 harness then passed all three runtime probe cases,
`RuntimesTest.InitRuntimes`,
`SMClientTest.SendSMInfoWithMultipleRuntimesAndResources`, and
`SMControllerTest.SMClientConnected`. It constructed the fourth runtime,
traced one non-rebooting in-memory instance lifecycle, serialized the exact
provider type through Service Manager protocol v5, and preserved the type and
`arm64` architecture at the Communication Manager receiver.

The accepted platform evidence is pinned to
`alexmaninblack/aos-vehicle-platform` commit
`34faf4b1637dd418a8b9a80476e243f5cd81c6d3`. The probe is qualification-only
and deliberately has no systemd, archive, persistence, health, slot, apply,
rollback, or recovery implementation.

## Cloud and Identity Evidence

A read-only OEM mTLS inspection of `/api/v11/openapi.json` identified
AosCloud API v11 implementation 6.1.26, OpenAPI 3.0.3, with the exact digest
recorded in the source lock. No POST, PATCH, DELETE, upload, assignment, Unit
Model, Node Type, or Unit mutation was performed.

The existing `aos-vm;1.0.0` Unit Configuration contains only one
`aos-vm-main` Node and has an empty desired-component list. The provisioned
Unit nevertheless reports the released boot and rootfs types as independent
installed components. The Node Type schema contains resource ratios and no
component declarations. Therefore the proposed runtime type does not require
a Unit Model or Node Type revision.

Future catalog metadata comes from uploading a FOTA bundle whose `type`
exactly equals
`aos-vm-1.0.0-main-qemuarm64-vehicle-data-provider`; an assignment then
creates desired update state. Those mutations and visual Cloud acceptance
remain R6.1-6 gates.

## Persistent Storage Evidence

The exact `meta-aos` release mounts the dedicated
`/dev/aosvg/workdirs` ext4 logical volume at `/var/aos/workdirs`; the Main Node
allocates 30 percent of its encrypted Aos volume to it. Service Manager already
owns `/var/aos/workdirs/sm`, including its rootfs runtime and migration state.

The accepted provider component root is:

```text
/var/aos/workdirs/sm/runtimes/systemd-slot-component
```

The production runtime will own its A/B payloads, transaction metadata, and
recovery state below this root. Exact slot layout and atomic switching remain
R6.1-3 implementation work. Downloads remain in the existing Aos downloads
volume and are not treated as installed component state.

## Qualification Gates

| Gate | Evidence required | State |
| --- | --- | --- |
| Source lock | Exact commits and file digests validate | Pass |
| Builder isolation | ARM64 VM passes resource, network, and no-identity checks | Pass |
| Runtime factory | Minimal provider runtime is constructed by Service Manager | Pass |
| Lifecycle trace | Start/stop/status seam is captured locally without reboot | Pass |
| Node/CM report | Proposed type appears in captured local SMInfo and CM | Pass |
| Component semantics | Matching runtime type and FOTA bundle type identified | Pass |
| Storage | Persistent root and future A/B ownership boundary selected | Pass |
| Identity | Existing Unit Model and Node Type remain unchanged | Pass |
| Mechanism ADR | Custom Service Manager runtime accepted | Pass |

## Current Decision

Use the custom Service Manager runtime. The local factory, lifecycle,
protocol, and CM gates passed, so the Update Manager fallback is not selected.
It can be reconsidered only if a new production blocker is discovered.

The accepted ADR is
`aos-vehicle-platform/docs/decisions/0001-service-manager-component-runtime.md`.
R6.1-1 is complete. R6.1-2 is the next work package but is not implicitly
authorized by this record. The active provisioned AosVM remains unchanged and
does not require deprovisioning or reprovisioning.
