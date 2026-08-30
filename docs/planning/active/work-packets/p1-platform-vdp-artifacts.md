<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# P1 Vehicle Data Platform Deployable Artifact Preparation Work Packet

- ID: `WP-P1-PLATFORM-VDP-ARTIFACTS-001`
- Lane: `L-PLATFORM`
- Increment: `IMP-03-VDP-ARTIFACTS`
- State: `AUTHORIZED — READY / NOT STARTED`
- Version: 0.1
- Prepared and authorized: 2026-08-30
- Repository: `aos-vehicle-platform`
- Exact source revision: `667afb1512cf43ff27f1ab5327293208bf73045b`
- Exact source tree: `164f907bf041dbc99df24d2ebe7b0e5d2bbaeab0`
- Required relationship: clean `main == origin/main` at the exact source
  revision above
- Parent source packet:
  [`WP-P1-PLATFORM-VDP-001`](p1-platform-vdp-family.md)
- Accepted Factory binding: `6.1.1-maninblack.21`, raw image SHA-256
  `80e0c0dc4f7f9c51a25d3461047e2e3d85bf540059c7052af3944ce8650e19e1`

## Outcome

Complete the already integrated VDP v1-v3 packaging boundary and prepare three
deployable, unsigned, immutable `linux/arm64` Platform FOTA candidates for
semantic versions `1.0.0`, `2.0.0` and `3.0.0`. The work converts the existing
reviewed `notDeployable` source-prebuild path into a deterministic candidate
builder without changing the accepted release capabilities or Factory Image.

This phase proves prepared artifact identity only. It does not sign, publish,
install, deploy or qualify a candidate on a VM or in AosCloud.

## Entry Gate

Before any edit or build, require all of the following:

1. the product repository and isolated worktree are clean at exact commit
   `667afb1512cf43ff27f1ab5327293208bf73045b`;
2. `main` and `origin/main` both resolve to that commit after a fresh fetch;
3. the accepted VDP v1-v3 profiles and capability manifests are unchanged;
4. the five-file ARM64 wheelhouse is available locally and every digest equals
   the checked-in dependency allowlist;
5. network-disabled and offline dependency guards are active;
6. the historical Provider `0.2.0` candidate path and accepted bytes remain an
   immutable regression input; and
7. the selected work filesystem has at least 55 GiB free before candidate
   generation. This component-only phase performs no image/rootfs build; the
   repository-wide 60-GiB image-build guard remains unchanged. If the
   component guard is not met, stop for an exact disk-hygiene reconciliation; do not
   delete the Builder, caches, current `.21` baseline or evidence.

## Exact Writable Boundary

Only these product-repository paths may change:

- `packaging/fota/**` for the deployable v1-v3 builder, validator, canonical
  metadata and package-owned documentation;
- `manifests/release-candidates/**` for exactly three producer-owned canonical
  manifests;
- `tests/test_fota_packaging.py`, `tests/test_vdp_family.py`,
  `tests/test_provider.py`, and new packaging-owner tests when required for the
  frozen artifact boundary; and
- `DEPENDENCIES.json`, `THIRD_PARTY_NOTICES.md` and license/SBOM inputs only if
  an already pinned runtime input proves the update necessary.

Provider runtime behavior, Factory/Yocto/KAC/IAM/SELinux source, Gateway,
Brake/Tire products and the Demo repository are read-only. A need to edit any
other path stops the packet and returns a bounded change request.

## Frozen Candidate Identity

The builder produces exactly these candidates and no alias or mutable `latest`
identity:

| Candidate ID | Semantic version | Prepared filename |
| --- | --- | --- |
| `aosedge-vdp-component-1.0.0` | `1.0.0` | `aosedge-vdp-component-1.0.0-linux-arm64.unsigned.tar.gz` |
| `aosedge-vdp-component-2.0.0` | `2.0.0` | `aosedge-vdp-component-2.0.0-linux-arm64.unsigned.tar.gz` |
| `aosedge-vdp-component-3.0.0` | `3.0.0` | `aosedge-vdp-component-3.0.0-linux-arm64.unsigned.tar.gz` |

Each producer manifest is UTF-8 JSON canonicalized with RFC 8785 before
SHA-256 and contains no self-digest. It records the exact fields required by
D4-013, including prepared filename/length/SHA-256, product/version/kind,
`linux/arm64`, source revision, all byte-affecting input digests, Factory
Image/runtime compatibility, contract delta, permissions/resource envelope,
SBOM/licenses/provenance and qualification references. It contains no
credential, private Cloud identifier, mutable tag or machine-local path.

The prepared candidate and a verified manifest copy are staged only in the
Git-excluded content-addressed path
`.local/release-candidates/sha256/<prepared-sha256>/`. The canonical producer
manifest remains version-controlled in the product repository. Creation of
`manifests/demo-release-set.v1.json` belongs to the later Demo Integration
packet and is excluded here.

## Build and Verification Sequence

1. Run all source, contract, dependency, quality and secret-negative gates
   before candidate generation.
2. Complete the deployable v1-v3 envelope builder and validator while keeping
   the historical Provider `0.2.0` path byte-stable.
3. Build each version twice from fresh temporary output roots using only the
   verified local ARM64 wheelhouse.
4. Require byte-identical prepared artifacts, component layers, metadata,
   SBOM, provenance and canonical producer manifests for both runs.
5. Validate exact strict-superset behavior: v1 exposes no v2/v3 capability and
   v2 exposes no v3 capability.
6. Validate architecture, runtime interface, Factory `.21` binding, package
   inventory, modes, licenses, notices and absence of secrets, Unit identity,
   certificates, keys, tokens and Cloud configuration.
7. Copy only the accepted bytes and verified manifest into the exact
   content-addressed store and record their size and SHA-256 in sanitized
   evidence.

Minimum owned gates include all `UT-VDP-001` through `UT-VDP-008`, existing
provider/packaging tests, `tools/quality_gate.py`, `git diff --check`, changed-
path verification and a clean final worktree. Any nondeterministic repeat,
wheel/cache mismatch, network attempt, changed dependency, Provider `0.2.0`
regression or secret-positive result stops the packet before staging.

## Explicit Exclusions

- no source change to the accepted v1-v3 functional behavior;
- no dependency download, registry access or unpinned input;
- no Factory Image or rootfs rebuild;
- no signing key, PKCS#12, signing operation or signed envelope;
- no AosCloud upload, Component UUID, Verification Batch, Fleet Validation or
  Campaign operation;
- no VM, provisioning, VISS/KUKSA/A-B, CARLA, Test or Production deployment;
- no Demo Release Set edit; and
- no merge or push by the implementation worker.

Disposable-VM/real VISS-KUKSA/A-B qualification, signing/publication, Test
Vehicle FOTA and identical-byte Production promotion remain separately
authorized later phases.

## Completion Evidence

The worker returns the exact branch/worktree, commit and parent; changed-path
inventory; all commands and test counts; two-build comparison for each
version; artifact, layer, metadata and canonical-manifest digests/sizes;
package/SBOM/license/provenance inventories; historical Provider regression;
secret/network negative results; content-store locations; free-space result;
and confirmation that every excluded operation was absent.

Passing this packet means only `PREPARED / OFFLINE VALIDATED`. It does not mean
`SIGNED`, `PUBLISHED`, `DEPLOYED`, `VALIDATED` or `PRODUCTION ACCEPTED`.

## Authorization Gate

The operator accepted this exact Phase-A boundary on 2026-08-30. Product work
may begin only after the synchronized readiness documents are committed and
the entry gate above passes. Any expansion, external action or later lifecycle
phase requires a separate authorization.
