<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R6.1 Offline Provider Qualification

- Status: R6.1-5 complete; accepted provider signed and verified locally
- Date: 2026-08-15
- Scope: local and offline only
- Provider version: `0.2.0`
- Platform revision: `e972d2bd7f14e27646bb5d7c10c7186ecdecfa9f`
- Integration implementation revision:
  `c1666615fb37a8bb251011797d698d8056840c98`
- Signing-gate revision:
  `0adfb0db30c055307582a0a0dc1fe3f11cb6d3fc`

## Qualification Boundary

This record completes R6.1-3.1 through R6.1-5. The approved OEM signing
identity was accessed locally only to sign and verify the accepted provider
candidate. No item was uploaded, published, assigned, or installed through
AosCloud. The provisioned demonstration VM, Unit identity, Cloud catalog,
Unit Model, Node Type, and assignments were not accessed or changed.

The accepted candidate ran only in a fresh, disposable, non-provisioned ARM64
VM with QEMU user networking restricted from external access. The persistent
Yocto builder VM, download cache, shared-state cache, build tree, and source
checkouts were retained for future incremental work. The builder contains no
Unit identity or signing material. The private qualification JWT key remained
on the Mac and was never copied into the disposable guest.

## Pinned Build Inputs

| Input | Accepted value |
| --- | --- |
| Platform source | `e972d2bd7f14e27646bb5d7c10c7186ecdecfa9f` |
| Project manifest | `e50045fe22588bfe882584fd35d4ee0439eb36712e4bb07a4fb5aed15e0b2748` |
| Generated Ninja graph | `1b1633cf3074054a6f23f5e86c4da93276fbc123d59ebd10ffbbbba532389d9c` |
| Local disposable VM raw disk; not an OTA/FOTA payload | `2316627cb452c779683001f02cfdc14fccaff40137c797ffc94def94d5c4d32a` |
| ARM64 runtime qualifier | `f95b051bcbd18bdf1095bc0e373ac9193209b32fb29424d07c552628524a97c0` |

The 6,997,147,648-byte image is a complete local raw VM disk containing the
partition layout and persistent-disk capacity required to boot AosVM under
QEMU. It is not a deployment bundle, is never signed as the provider, and is
not transferred through FOTA or uploaded to AosCloud. The runtime qualifier is
25,734,904 bytes. The guarded fetch verified both guest and host digests and
made the local image read-only before boot.

The 6,616,114-byte unsigned envelope recorded below is the deterministic
compressed input witness for the OEM-to-Cloud bundle, not the payload size
downloaded by a Unit. The accepted provider layer is 17,756,160 bytes. After
Cloud ingestion a Unit downloads that layer plus small OCI and cryptographic
metadata; the exact encrypted transfer size is supplied by Cloud per blob.
Signing never includes the 6,997,147,648-byte raw VM disk. A separate,
one-time bootstrap system update is recorded later in this document and
currently contains 193,559,688 bytes of boot and compressed rootfs payloads in
total.

## Accepted Unsigned Candidate

Two builds from separate staging roots produced byte-identical files. The
strict project validator and the official `aos-signer validate` command both
accepted the configuration and image paths.

| File | Size | SHA-256 |
| --- | ---: | --- |
| Restricted ARM64 provider layer | 17,756,160 | `baf1c29c9264b8f2422dc155540c3b22716bb43d5f80c1cfeb3cc9529f0bf3cb` |
| Unsigned envelope | 6,616,114 | `1f634839e5678efa2ec9677c1342c9b4c4b7ede929ff0fd166d25de84103f051` |
| Unsigned `config.yaml` | 827 | `cb636649e253510cd1c06d8888a0254fc1bd4b7642de79a9601bb9d5979f0d9a` |

The candidate contains the real CARLA VISS-to-KUKSA provider, five exact
hash-locked ARM64 dependencies, component metadata, SPDX SBOM, provenance,
dependency inventory, licenses, and notices. It contains no installer,
virtual environment, systemd unit, rootfs mutation, credential, private key,
Unit identity, Cloud token, or user-specific path.

## Signing And Encryption Boundary

The official `aos-signer` does not encrypt the local deployment bundle and
does not attach a signature to the deterministic unsigned envelope as an
opaque file. It copies the accepted configuration and layer into a newly
composed inner `batch.tar.gz`, signs the SHA3-512 hash and size of that inner
archive together with `config.yaml` using RS256, and creates a readable outer
`batch.tar.gz` containing the inner archive, configuration, and `package.sign`.

The immutable accepted signing inputs are therefore the provider layer digest,
size, and configuration digest. The unsigned-envelope digest remains a
reproducibility witness. The guarded post-signing verifier must read the outer
and inner archives without extracting them to the repository, prove that the
embedded layer and configuration are byte-identical to the accepted inputs,
validate the signed hashes, and verify RS256 with the public certificate from
the approved OEM PKCS#12 identity. It then records the final signed-bundle
digest and size.

Content encryption is a later Cloud-to-Unit boundary. Upload uses HTTPS/mTLS.
After Cloud ingestion, Communication Manager may receive encrypted OCI blobs
and per-blob decryption information; it validates the downloaded ciphertext,
decrypts inside the Unit, and then validates the content signature and digest.
The local R6.1-5 verifier never attempts to unpack a Cloud-encrypted blob.

## Accepted Signed Candidate

The accepted inputs were revalidated immediately before signing. The official
`aos-signer` composed and signed only provider `0.2.0`. The guarded verifier
then read both archive levels without extracting them into either repository,
proved that the embedded layer and both embedded configuration copies were
byte-identical to the accepted inputs, validated both signed SHA3-512 records,
and verified the RS256 signature using only the public certificate extracted
from the approved OEM PKCS#12 identity.

| Evidence | Accepted value |
| --- | --- |
| Signed deployment bundle size | 6,599,930 bytes |
| Signed deployment bundle SHA-256 | `30802d1bcb88a5954cf1e9c6c17573b527efe4f2a62ca3c0c83459f8a2fe35db` |
| Embedded provider layer SHA-256 | `baf1c29c9264b8f2422dc155540c3b22716bb43d5f80c1cfeb3cc9529f0bf3cb` |
| Embedded configuration SHA-256 | `cb636649e253510cd1c06d8888a0254fc1bd4b7642de79a9601bb9d5979f0d9a` |
| Signature algorithm | RS256 |
| Verification result | `R6_1_SIGNED_PROVIDER=PASS` |

The signed bundle remains a local, ignored build artifact under the accepted
candidate directory. It is not stored in Git. No private key, certificate,
password, subject, key identifier, token, or Cloud response is recorded in
this evidence.

## Offline Matrix Result

| Gate | Result |
| --- | --- |
| Platform repository tests and validators | Pass; 27 tests |
| Integration repository tests and pinned-input validators | Pass; 59 tests |
| Restricted archive, Image Manager, lifecycle, and recovery matrix | Pass; 40 ARM64 tests |
| Real provider first install through the production profile | Pass |
| No-source start and seven-path unavailable state | Pass |
| Live VISS fixture to seven KUKSA paths | Pass |
| Source loss, explicit reload, and restart without stale values | Pass |
| Read-only KUKSA role denied provider write access | Pass |
| Real `0.2.0` to synthetic `0.3.0` update | Pass |
| Downgrade rejection without active-slot change | Pass |
| Post-preflight `0.4.0` start failure and automatic rollback | Pass |
| Failure evidence and restored `0.3.0` state | Pass |
| DynamicUser SOTA boundary, read-only root, and SELinux | Pass |
| Provider non-root identity and memory below 256 MiB | Pass; 49,348 KiB RSS |
| Payload and guest secret-exclusion checks | Pass |

The guest ran CPython 3.12.12. The live provider reported readiness through
systemd, ran under a dynamic non-root UID, and did not require CARLA to remain
locally healthy. CARLA loss made all owned values unavailable instead of
retaining or fabricating data.

Generic negative and recovery coverage includes unsafe archive paths, links,
duplicates, modes, special files, whiteouts, wrong architecture, excessive
size, insufficient storage reserve, same-version digest changes, corrupted
state, failed previous health, and recovery from every durable transaction
phase. These deterministic runtime gates cover the disk-full, interrupted
transaction, and corrupted-state portions of R6.1-5 without modifying the
host or provisioned VM.

## Bootstrap FOTA Regression

The final unsigned bootstrap output contains exactly the full boot and rootfs
components and no incremental or provider item:

| File | Size | SHA-256 |
| --- | ---: | --- |
| `config.yaml` | 1,065 | `76b83af66775b99527e5a2a41ef25490a28897bc740e8f70a5ad3270cbed555b` |
| Boot 6.1.0 | 65,186,952 | `1a17720e88a2ded3684d8fff10efee1c1d6313bc43349a9ec752130dd14c1b09` |
| Full rootfs 6.1.0 | 128,372,736 | `88f41e9ec9aaa180d66fd84b3ef2cc4c372c1c6659f8be957874c151c72916a1` |

The structural, identity, canonical-path, and secret-exclusion validator
passed. This output is an offline regression artifact only; it was not signed
or submitted to the Cloud.

The regression output reuses upstream version `6.1.0` and is not a publishable
custom bootstrap release. R6.1-6 selected a rootfs-only full-image release
`6.1.1-maninblack.1`; boot remains at `6.1.0` and is omitted from the update.
The new output must be rebuilt, qualified, and frozen before signing or upload.
Its expected unsigned payload is approximately 128,372,736 bytes instead of
the 193,559,688-byte boot-plus-rootfs regression output. Different bytes must
never be published under an existing component version.

## Defects Closed During Qualification

The disposable acceptance work found and closed five production-path gaps:

1. first installation no longer tries to stop a nonexistent previous
   provider;
2. the Service Manager completes its systemd D-Bus authentication preflight
   before invoking the external health adapter;
3. first start accepts the expected not-yet-loaded static systemd unit while
   preserving all other reset failures;
4. bounded health calls cancel their watchdog sleep after early success;
5. a failed candidate that cannot be marked unavailable because its unit is
   already inactive no longer causes a successfully restored previous release
   to be discarded.

The fifth issue was reproduced only after correcting the qualification fixture
so that the bad candidate passes offline preflight and fails after the active
slot switch. A dedicated ARM64 regression test now protects this exact case.

## Completed Signing Gate

The accepted layer, configuration, and unsigned reproducibility witness remain
frozen at the digests recorded above. Explicit approval to access the OEM
signing identity was granted on 2026-08-15. It covered local signing and
verification of only this accepted provider candidate; it did not cover Cloud
upload or mutation.

The completed local signing gate:

1. reverified the accepted layer, configuration, and unsigned-envelope digests
   before accessing the identity;
2. signed without copying key material into Git, the builder, or the disposable
   VM;
3. verified that the signed bundle contains the exact accepted layer and
   configuration, validated its signed SHA3-512 records, and verified its RS256
   signature with the approved public certificate;
4. recorded only the final bundle size, digest, signature algorithm, and accepted
   input digests; and
5. stopped without uploading, publishing, assigning, provisioning, or
   changing the active Unit.

R6.1-5 is complete. R6.1-6 remains a separate gate requiring explicit approval
for bootstrap signing or deployment and every Cloud or active-Unit mutation.
