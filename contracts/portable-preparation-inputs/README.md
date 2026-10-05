<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Portable preparation inputs

- Status: Accepted Stage 2 integration slice; not installer/live qualification.
- Version: 1.0
- Prepared: 2026-09-26
- Owner: Demo Solution Team
- Parent: [accepted distribution plan, Stage 2](../../docs/planning/active/installable-distribution-and-reproducibility.md#stage-2-assemble-portable-demo-runtime-artifacts).
- Authority: [unsigned inputs and session-scoped signing](../../docs/architecture/decisions/0016-unsigned-packages-and-session-scoped-signing.md#4-accepted-artifact-and-signing-contract).

## Selection and integrity

The existing artifact catalogue may contain one `preparation-inputs` directory
under `$DEMO_ARTIFACT_ROOT/aosedge-sdv-demo`. This is an explicit packaged-input
selection, not a search path or an arbitrary archive import. If absent, the
existing developer path remains unchanged. If present but invalid, unreadable,
incomplete or linked elsewhere, preparation fails closed; it must not fall
back to Git, a historical signed VDP bundle or a developer product build.

The shipped integration contract [lock](vehicle-inputs.lock.json) independently
pins the complete `vehicle-input-manifest.json` by size and SHA-256. The lock
is release-source data, not an adjacent self-generated acceptance receipt.
Updating it requires a new reviewed artifact checkpoint; there is no runtime
adoption or automatic lock update. The manifest contains unique canonical
relative paths and bounded sizes/digests. Reject symlinks, hard links, special
files and group/world-writable payload files. Validate file presence/size when
selecting the bundle and each consumed file's SHA-256 at preparation. Do not
rehash the multi-gigabyte Factory merely to prepare a software release.
This local integrity contract is not publisher signature/notarization proof.

The offline producer may select an explicit reviewed Factory checkpoint from
the integration source tree. Its default remains the historical `demo-v1.1`
checkpoint; a successor uses a separate candidate file, never overwrites the
return point. The producer validates version, image name, source revision, size
and digest against the immutable Factory manifest, with no fallback on an
invalid explicit choice. This is build-time input only: runtime selection,
the independent release-source lock and installation authority are unchanged.

The bound source artifact supplies the three exact unsigned VDP profiles,
reviewed common/advisory modules, four prebuilt Linux/arm64 service profiles,
public notices, build receipts and six configuration contracts. The existing
VDP unsigned digest and reviewed runtime module pins are checked independently
as well. Existing product-reader checks for native executable format, hashes,
public-license-only rootfs and product configuration remain in force.

## Preparation and unchanged authority

1. Validate the selected inputs before contacting the release catalogue or
   reserving a version. Bad inputs consume no version and trigger no Cloud call.
2. VDP uses the selected profile's unsigned archive and current reviewed runtime:
   V1/V2 remain telemetry-only; V3 retains advisory. Service Prepare uses its
   exact prebuilt product export, without Git, Docker or a build fallback.
3. Use the existing selected Cloud release catalogue and persistent allocator.
   Write newly prepared unsigned outputs only to the existing writable release
   directories. Never write into `preparation-inputs` or reset the ledger.
4. Keep the existing CLI/API/UI actions, selected OEM/SP signing context, upload
   guards, publication reconciliation and Factory compatibility checks. Prepare
   is not Sign/Publish, installation or a claim of runtime readiness.

The explicit developer `service build` command remains separate; this contract
changes only its no-build input-selection path used by Service Prepare. Legacy
development-only VDP composition without a selected V1/V2/V3 profile is not a
packaged operation. No browser/caller-selected input path is added.

## Verification and scope

Required checks: all seven profile preparations, current VDP module identity,
no source/build subprocess, schema/product-reader success, independent signed
output absence, allocation continuity and repeat handling; corrupt/missing
manifest, profile, binary, contract and path failures before Cloud/allocation;
unchanged development behavior when no packaged directory exists. Use isolated
catalogues, journals and a clearly labelled release-catalogue fixture. Real
signing/upload, guest boot and the complete operator launch require their own
later acceptance. No current Test or Production switch is authorized by a test.

This class-B implementation of the accepted delivery plan changes an input
location, not component ownership, wire protocols, credential custody, Cloud
authority, vehicle safety gates or lifecycle state. Revalidate the existing
scenario/flows and requirement allocation without renumbering their stable IDs.
