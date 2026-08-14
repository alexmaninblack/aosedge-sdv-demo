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
The next checkpoint is a successful unchanged-image build and disposable boot.
