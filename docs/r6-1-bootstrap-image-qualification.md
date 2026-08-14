<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R6.1-2 Bootstrap-Image Qualification

- Status: In progress
- Date started: 2026-08-14
- Authorized scope: R6.1-2 only
- Source baseline: `components/r6-1-source.lock.json`

## Objective

Produce and qualify a reproducible AosVM 6.1.0 `qemuarm64` bootstrap image
that contains the production vehicle-data-provider runtime boundary while an
empty provider component store remains safe. First build and boot the unchanged
upstream image, then apply only the tracked project Yocto layer and quantify
the resulting delta.

R6.1-2 establishes the platform bootstrap. It does not implement or claim the
atomic component lifecycle assigned to R6.1-3.

## Safety Boundary

R6.1-2 may:

- use the isolated, non-provisioned ARM64 Yocto builder;
- create persistent download and shared-state caches on its ext4 disk;
- build unchanged upstream and project bootstrap images;
- boot disposable, unprovisioned image copies for local qualification;
- produce an unsigned full rootfs FOTA bundle for structural qualification.

R6.1-2 must not:

- modify, replace, boot from, or attach the active provisioned AosVM disk;
- deprovision or reprovision the existing Unit;
- copy any Unit identity, user certificate, OEM key, signing key, token, or
  Cloud credential into the builder or any build artifact;
- upload a component, modify a Cloud catalog, or create an assignment;
- install the qualification-only R6.1-1 runtime probe in a production image;
- claim A/B apply, rollback, recovery, or provider payload acceptance before
  R6.1-3.

## Locked Inputs and Outputs

All upstream Git revisions and the Ubuntu builder image are resolved by the
accepted source lock. The project-owned Moulin input and Yocto layer are kept
in Git. Build directories, downloads, shared state, images, and bundles remain
outside Git; only their non-secret manifests and digests may be recorded.

The builder cache boundary is:

```text
/home/yocto/yocto-cache/downloads
/home/yocto/yocto-cache/sstate-cache
```

Both directories reside on the builder's persistent ext4 root disk and remain
independent of disposable build directories.

Completed images leave the builder only through the guarded `fetch` command.
It accepts regular image artifacts below `/home/yocto/r61-build`, writes below
the ignored `artifacts/r6-1` host directory, refuses overwrites, and compares
the guest and host SHA-256 digests. A fetched read-only raw image is booted
through `scripts/r6-1-disposable-vm` with a dedicated qcow2 overlay, PID, QMP,
serial, log, MAC address, and loopback SSH port. Its QEMU user network uses
`restrict=on`: local qualification remains possible, but the disposable,
unprovisioned guest cannot contact AosCloud or any external service.

The expected invocation shape is:

```sh
./scripts/r6-1-builder fetch \
  /home/yocto/r61-build/upstream/main-qemuarm64.img \
  artifacts/r6-1/upstream/main-qemuarm64.img
./scripts/r6-1-disposable-vm upstream \
  artifacts/r6-1/upstream/main-qemuarm64.img SHA256 prepare
./scripts/r6-1-disposable-vm upstream \
  artifacts/r6-1/upstream/main-qemuarm64.img SHA256 start
./scripts/r6-1-disposable-vm upstream \
  artifacts/r6-1/upstream/main-qemuarm64.img SHA256 wait-ready
```

The actual digest is taken from the successful guarded fetch output and is
recorded in this qualification file; `SHA256` above is deliberately not a
floating or inferred value.

## Qualification Gates

| Gate | Evidence required | State |
| --- | --- | --- |
| Authorization | Scope and prohibited mutations recorded | Pass |
| Capacity | Host and guest free-space guards pass | Pass |
| Cache | Persistent ext4 download and shared-state paths pass restart check | Pass |
| Manifest | Moulin input resolves only locked sources | Pass |
| Upstream build | Unchanged AosVM 6.1.0 Main Node image builds | Pending |
| Upstream boot | Disposable unchanged image passes the AOS-0 boot baseline | Pending |
| Project layer | Runtime, launcher, policy, storage, and health inputs validate | Pending |
| Custom build | Bootstrap image and unsigned full rootfs FOTA bundle build | Pending |
| Custom boot | Disposable project image passes all required AOS-0 gates | Pending |
| Secret exclusion | No identity, certificate, key, or token enters artifacts | Pending |
| Reproducibility | Exact inputs, commands, delta, and artifact digests recorded | Pending |

## Current Checkpoint

Execution is authorized. The active provisioned AosVM and AosCloud remain
outside scope. The Mac had 343 GiB free and the builder had 198 GiB free after
installing the required Yocto host packages. The download and shared-state
directories were created on ext4, survived a clean builder shutdown and boot,
and passed the guarded ownership, symlink, marker, and capacity checks.

The tracked Apache-2.0 manifest passed the local validator and Moulin 0.21.
It selected `qemuarm64`, one Main Node, no message proxy, exact Git revisions,
and the persistent cache paths. Its SHA-256 is
`77f25a49c439035ab0dc2d8d496048043b1258bb230996428ca730de364bb4fe`;
the generated Ninja graph SHA-256 is
`af224c74f932dab23d8ca736e3b36c4c403df3ba5d219010f87f175ac472f0c6`.
The unchanged upstream image build is now running in the isolated builder.
The Apache-2.0 project layer is fixed at
`aba8c2be9845e3a19d12014bb2aeb17c20906de7`. Its production runtime and
Service Manager factory compile against the exact AosCore source pins; all
three empty-store runtime tests pass. The layer's local contract, policy,
license, launcher, health-adapter, and 14 unit-test gates also pass. This is
not yet the complete project-layer gate because BitBake and disposable-image
qualification remain pending.

The credential-free project manifest SHA-256 is
`354a80d04e3ada9a855af8eaadb4551d9f33535d19bb55b0b7d69056c5f4ac92`.
It pins the separately versioned platform repository and generates the stable
Moulin graph SHA-256
`fb373f865844aa3c68c1c7c53a79a286b2a0ae3c50563d5ccb4f4e76744cfea7`.
The unchanged upstream image build continues in the isolated builder. The
next checkpoint is its successful build and disposable boot; only then may
the project image build start.
