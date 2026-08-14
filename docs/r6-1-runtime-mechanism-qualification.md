<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R6.1-1 Runtime-Mechanism Qualification

- Status: In progress
- Date started: 2026-08-14
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
pass. The lock remains `candidate` until the local mechanism, protocol,
storage, and identity gates below are complete.

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
- no Aos services, Unit identity, Cloud certificate, or signing credential.

The virtual disk is stored outside Git under the project's private macOS
application-support directory. Its nominal 220 GiB capacity is sparse, but
host free-space checks remain mandatory because a Yocto build may consume much
of that capacity.

## Service Manager Evidence

Inspection of the exact locked sources currently establishes:

- Service Manager implements `RuntimeItf` factories for `container`, `boot`,
  and `rootfs`; a vehicle-data-provider runtime is not present in the release;
- `SMClient::SendSMInfo()` sends the runtime inventory to CM;
- Service Manager protocol v5 `SMInfo` contains repeated `RuntimeInfo` records;
- `RuntimeInfo` carries runtime ID, type, architecture, OS, and resource data;
- `isComponent` participates in the Yocto runtime configuration but is not a
  field of the transmitted `RuntimeInfo` record.

Therefore local runtime reporting has a real protocol path, but source
inspection alone does not prove Cloud component classification. The harness
must determine which desired-state, item, Unit Model, or component metadata is
also required.

## Qualification Gates

| Gate | Evidence required | State |
| --- | --- | --- |
| Source lock | Exact commits and file digests validate | Pass |
| Builder isolation | ARM64 VM passes resource, network, and no-identity checks | Pending |
| Runtime factory | Minimal provider runtime is constructed by Service Manager | Pending |
| Lifecycle trace | Prepare/start/stop/status paths are captured locally | Pending |
| Node/CM report | Proposed type appears in captured local SMInfo | Pending |
| Component semantics | Required classification metadata is identified | Pending |
| Storage | Persistent root and A/B ownership rules are selected | Pending |
| Identity | Unit Model and Node Type impact is closed | Pending |
| Mechanism ADR | Runtime or Update Manager fallback is accepted | Pending |

## Current Decision

Continue with the custom Service Manager runtime as the primary candidate.
The Update Manager fallback remains conditional and must not be selected until
the runtime harness has either passed or exposed a concrete blocking property.

The next action is to create and qualify the isolated builder. The active
provisioned AosVM remains unchanged.
