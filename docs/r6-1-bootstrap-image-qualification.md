<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R6.1-2 Bootstrap-Image Qualification

- Status: Completed
- Date started: 2026-08-14
- Date completed: 2026-08-14
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
./scripts/r6-1-guest upstream \
  artifacts/r6-1/upstream/main-qemuarm64.img SHA256 enroll-key
./scripts/r6-1-guest upstream \
  artifacts/r6-1/upstream/main-qemuarm64.img SHA256 \
  copy scripts/guest/r6-1-bootstrap-check /tmp/r6-1-bootstrap-check
./scripts/r6-1-guest upstream \
  artifacts/r6-1/upstream/main-qemuarm64.img SHA256 \
  run sh /tmp/r6-1-bootstrap-check upstream
```

The actual digest is taken from the successful guarded fetch output and is
recorded in this qualification file; `SHA256` above is deliberately not a
floating or inferred value.

Guest access reuses the accepted per-VM Ed25519 enrollment and strict
known-host verification. The official development-image password is consumed
only by the existing bounded helper during first key enrollment and is not
stored in a new file or log. The guest gate verifies AArch64, AosCore 6.1.0,
read-only root, writable persistent partitions, cgroups v2, namespaces,
seccomp, network shape, enforcing SELinux, pre-provision state, and absence of
credential-like files. The upstream variant must contain no project runtime;
the project variant must contain exactly one fixed runtime and a disabled,
inactive, empty provider store whose health and launcher interfaces fail safe.

The guarded build controller exposes the unsigned `fota` target only after the
project image result is `PASS`, and it refuses to run the image and FOTA builds
concurrently. `scripts/validate-r6-1-fota-output` then requires exactly the
ARM64 boot and full-rootfs components, version 6.1.0, publisher `maninblack`,
regular non-empty artifacts below the canonical output root, and fixed runtime
identities. Incremental or extra items, path traversal, symlinks, publication
metadata, TLS key references, and credential-like content are rejected.

## Qualification Gates

| Gate | Evidence required | State |
| --- | --- | --- |
| Authorization | Scope and prohibited mutations recorded | Pass |
| Capacity | Host and guest free-space guards pass | Pass |
| Cache | Persistent ext4 download and shared-state paths pass restart check | Pass |
| Manifest | Moulin input resolves only locked sources | Pass |
| Upstream build | Unchanged AosVM 6.1.0 Main Node image builds | Pass |
| Upstream boot | Disposable unchanged image passes the AOS-0 boot baseline | Pass |
| Project layer | Runtime, launcher, policy, storage, and health inputs validate | Pass |
| Custom build | Bootstrap image and unsigned full rootfs FOTA bundle build | Pass |
| Custom boot | Disposable project image passes all required AOS-0 gates | Pass |
| Secret exclusion | No identity, certificate, key, or token enters artifacts | Pass |
| Reproducibility | Exact inputs, commands, delta, and artifact digests recorded | Pass |

## Current Checkpoint

Execution is authorized. The active provisioned AosVM and AosCloud remain
outside scope. The Mac had 343 GiB free and the builder had 198 GiB free after
installing the required Yocto host packages. The download and shared-state
directories were created on ext4, survived a clean builder shutdown and boot,
and passed the guarded ownership, symlink, marker, and capacity checks.

The tracked Apache-2.0 manifest passed the local validator and Moulin 0.21.
Because Moulin 0.21 leaves `gpt-image` unbounded, the builder additionally
pins `gpt-image` 0.8.1 by the SHA-256 of its official PyPI wheel.
It selected `qemuarm64`, one Main Node, no message proxy, exact Git revisions,
and the persistent cache paths. Its SHA-256 is
`77f25a49c439035ab0dc2d8d496048043b1258bb230996428ca730de364bb4fe`;
the generated Ninja graph SHA-256 is
`af224c74f932dab23d8ca736e3b36c4c403df3ba5d219010f87f175ac472f0c6`.
The Apache-2.0 project layer is fixed at
`ad850e8bad7585cbdf589915a64fee061a0bd405`. Its production runtime and
Service Manager factory compile against the exact AosCore source pins; all
three empty-store runtime tests pass. The layer's local contract, policy,
license, launcher, health-adapter, and 14 unit-test gates also pass.

The credential-free project manifest SHA-256 is
`8d1814540e1c6b6291a6b4b8af3bcb66e2d118e9650af5002dc9847b62115445`.
It pins the separately versioned platform repository and generates the stable
Moulin graph SHA-256
`528b09ca750576a2ab8520802d6f9ed015e7e57cab72d5aae4bbcdb55e2cf4a5`.

The first unchanged-upstream execution completed all 7,493 BitBake tasks
successfully, including the VM root filesystem, initramfs, kernel deployment,
license deployment, KUKSA Databroker, and VSS 5.0 packaging. Final raw-image
assembly then stopped at Ninja step 20 of 21 because the non-interactive SSH
environment omitted `/home/yocto/.local/bin` from `PATH`; the generated graph
therefore could not resolve the `rouge` entry point already installed by the
pinned Moulin 0.21 environment. No source, BitBake output, download cache, or
shared-state cache failed or was discarded.

The tracked guest controller now exports the fixed pipx application directory
before graph generation or execution and verifies that `moulin` and `rouge`
resolve from the same pinned environment. The first incremental retry reached
Rouge without rerunning BitBake, but exposed a second reproducibility issue:
Moulin 0.21 had resolved its unbounded `gpt-image` dependency to 0.9.1. The
0.9.x staged partition-entry API is incompatible with Moulin 0.21's layout
calculation, so every partition appeared to start at LBA zero and Rouge sized
the disk for only the largest partition. The later writes therefore overflowed
the generated GPT image. R6.1 now pins the last compatible release,
`gpt-image` 0.8.1, and verifies both its package version and wheel digest. The
next incremental retry confirmed the corrected GPT layout and began creating
the EFI/FAT partition, then exposed one missing Ubuntu host utility: Rouge
requires `mmd` from `mtools`. The builder bootstrap now includes and verifies
Ubuntu Jammy's mtools 4.0.32. The next incremental execution completed the
final image assembly without rerunning the 7,493 successful BitBake tasks.

The guarded fetch published the unchanged upstream image read-only with:

- size: 6,997,147,648 bytes;
- SHA-256: `cc5a14f3ed60bdaa9ad16017d0006ced66aa2670b8f3b9aa498608570fb9e3ee`.

Its isolated disposable overlay reached the AosCore 6.1.0 `main login:` prompt
with external networking disabled. The full upstream guest gate passed for
AArch64, storage mounts, cgroups v2, overlayfs, seccomp, OCI namespaces,
network shape, SELinux enforcing mode, pre-provision state, secret exclusion,
and absence of all project-owned runtime files. The qualification VM was then
stopped cleanly while its overlay and evidence were retained. The pinned
project graph was regenerated with its expected digest and the project image
build completed successfully against the same persistent caches. During that
build, three project-layer integration defects were corrected without changing
the accepted architecture: the shell patch fragment was moved out of a Python
BitBake task, the SELinux policy now uses the interface exported by the pinned
refpolicy revision, and its required `service` policy class is declared. The
resulting read-only project image is retained inside the persistent builder
with:

- size: 6,997,147,648 bytes;
- SHA-256: `fbd424dd20a472ed99fb15d1394e89d12b443fc3a280fa4b63f45d661190ccd6`.

The guarded fetch copied that image to the Mac as a read-only artifact and
verified the same size and SHA-256. Its offline disposable overlay reached the
login prompt and passed the full project guest gate: ARM64, read-only rootfs,
writable persistent partitions, cgroups v2, overlayfs, seccomp, production OCI
namespaces, fixed network shape, SELinux enforcing mode, pre-provision state,
secret exclusion, one inactive project runtime, an empty provider store, and
fail-safe launcher and health behavior. The VM was stopped cleanly and its
overlay and boot evidence were retained.

The first project gate used the unprefixed Yocto input type
`vehicle-data-provider`; the running Service Manager correctly reported the
released prefixed type
`aos-vm-1.0.0-main-qemuarm64-vehicle-data-provider`. The gate now tests that
accepted runtime contract and has a regression test.

The released FOTA custom-script paths were relative to a working directory
that Moulin 0.21 does not enter when executing the generated Ninja rule. The
credential-free project manifest now normalizes only the FOTA script, output,
Yocto, OSTree, and boot-input paths against the actual graph root. It also
invokes the released `fota_builder.py` with the same pinned Moulin Python.
The builder tool lock supplies the script's previously undeclared Pydantic 2
runtime as four exact, hash-verified ARM64-compatible wheels: Pydantic 2.10.6,
Pydantic Core 2.27.2, Annotated Types 0.8.0, and Typing Extensions 4.16.0.

The guarded unsigned FOTA build completed all 1,174 overlay tasks and emitted
exactly two enabled components. Independent structural validation passed with:

- metadata SHA-256:
  `76b83af66775b99527e5a2a41ef25490a28897bc740e8f70a5ad3270cbed555b`;
- boot component: 65,191,559 bytes, SHA-256
  `bb79e0a9b75ac6429da630da24bcb67dd84a7bb173a8035881e8df558fcacabf`;
- full rootfs component: 128,319,488 bytes, SHA-256
  `2bcb778352b59b0b6c5644a8481a672269341822c85d320d8d4751da39c62812`.

The validator confirmed schema version 2, publisher `maninblack`, AosVM 6.1.0
boot and full-rootfs identities, ARM64/Linux metadata, safe `sourceFolder` and
image paths, regular non-empty files, and the absence of publish, TLS-key, or
credential metadata. The disabled incremental component was not emitted.

The upstream and project rootfs package manifests contain 440 and 441 entries,
respectively. Their only delta is
`aos-vehicle-data-provider-platform cortexa57 0.1.0`; the upstream and project
initramfs package manifests are byte-identical. The rootfs manifest SHA-256
values are, respectively,
`5e03679eaa002f3aa9e13cdbb06bcd8b01cd48e99289fa9ef8c9dd55c53a5b90`
and
`f69d8f84fa1159af5537f817f2e12e66ebd8ebe505bd7443c91874525e36fa34`.

The first disposable guest-gate run also corrected a qualification-only test:
the minimal upstream image intentionally does not ship the `unshare` command,
so command absence had been misreported as a kernel namespace failure. The
gate now uses the image's production OCI runtime, crun 1.14.3, to create a
read-only probe container and verifies distinct mount, PID, IPC, UTS, and
network namespace inodes. This tests the actual vehicle-service execution path
without adding a package to the upstream image. The same correction removed a
legacy `eth0` assumption: the gate now derives the qualified interface from
the fixed default route and accepts the upstream image's predictable
`enp0s2` name while still requiring `10.0.0.100/24` and gateway `10.0.0.1`.
