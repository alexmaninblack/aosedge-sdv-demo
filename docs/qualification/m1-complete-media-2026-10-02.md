<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Complete DMG installation qualification on M1

- Date: 2026-10-02
- Status: Complete media built, transferred and installed; engineering preparation passed, native UI acceptance pending
- Candidate: Runtime Kit 025 with signed Setup 039
- Scope: First accepted single-media milestone, not the complete simplified wizard
- Plan: [Installable distribution](../planning/active/installable-distribution-and-reproducibility.md)
- Prior results: [M1 functional qualification](m1-installation-2026-10-01.md)

## Delivery and qualification boundary

The user accepted the operator-experience direction and explicitly chose a
complete DMG plus M1 installation as its first milestone. The development disk
[cleanup and relocation](../research/development-disk-cleanup-2026-10-02.md)
was completed before media assembly. All large packaging staging stays on the
Work SSD. Factory, CARLA and service binaries are not rebuilt for this change.

The image contains the signed Setup app, its matching `Runtime Kit`, and a short
`Start Here.txt`. Setup discovers this exact sibling without a separate download
or a folder search. Discovery does not execute anything from the payload;
independent release pin, inventory and digest checks remain in force. Existing
explicit Check installation, Install package and Prepare local data actions are
retained in this first slice. The persistent Applications launcher and simplified
first-use journey are later implementation work, not demonstrated capabilities.

This is an Apple Development-signed engineering candidate, not a notarized
public distribution. Docker remains a declared separately installed dependency.
Cloud account/access prerequisites remain separate. No development credentials,
certificates, previous run state or VM instance are added to the media.

The target is the existing dedicated M1 Pro (MacBookPro18,3, 16 GiB RAM), internal
disk, macOS 27.0.1 build 26A434. A new empty package store and private-data path
distinguish a genuine media installation from selecting the already installed
Kit 025. Existing installation, credentials and rollback are preserved.
This does not mean macOS was erased again or that dependency/permission consent
is being qualified from a virgin operating system.

## Source verification

- Seven complete-media tests pass, including corrupt/extra payload rejection,
  independent pin preservation, path overlap and no-overwrite boundaries.
- 106 existing Setup tests pass with the documented source Python import paths.
- The native Setup protocol self-test passes (`SETUP_NATIVE_PROTOCOL_PASS`).
- `git diff --check` passes; pre-existing uncommitted work is preserved.

Kit manifest SHA-256:
`cdc976a372b5294984769c4dbb1dbbe1c527baeeb6883c36a12469933641380c`.
Setup 039 keeps the established bundle identifier and signing requirement.
The native executable SHA-256 is
`d36152dc7ac97912a711a85c845b26ad2b9282b053209726f6368b074deae6f3`.

## Live evidence

The image was built on the Work SSD as
`AosEdge-SDV-Lab-Kit025-Setup039.dmg`, containing 17,686 runtime files totaling
35,456,326,771 logical bytes. Compressed image size is **14,161,819,662 bytes**
(14.16 GB, approximately 13.19 GiB). Every staged file was checked against its
manifest digest, the copied app signature was verified, and `hdiutil verify`
reported a valid image. Successful assembly removed its own temporary staging.
Image SHA-256:
`c46233c3eb484e3ca32f420a89d66f1e836e3623ab546df181dbfdc1d84a54bb`.

The image and sibling build receipt are retained on the Work SSD, outside the
source repository. The single DMG was transferred over pinned SSH; its M1
digest matched and the read-only attachment passed image verification. The
mounted app passed strict signature verification and executable identity checks.

The user then requested script-first functional qualification, with UI work
reserved for final acceptance. The remote adapter invoked the exact signed
Setup's embedded Python and `setup_bridge.py` over JSON stdin. It adds transport,
timing and evidence only, not a separate installation implementation. M1 used
no source checkout, system Python, Homebrew or developer toolchain for these
steps. Native Setup buttons were not used and are not counted as passed.

| Operation | Elapsed time | Observed result |
| --- | --- | --- |
| Single DMG transfer | 121.54 seconds | Destination digest matched |
| Setup preflight | 5.24 seconds | Compatible payload, volume and space guard passed |
| Setup install | 121.98 seconds | 17,686 files installed and verified into a new store; no prior package reuse |
| Setup prepare | 34.90 seconds | New private instance selected Kit 025 at revision 1, not started |

The three Setup operations took **162.12 seconds** combined, excluding transfer,
media attachment, prior UI navigation and subsequent evidence checks. Preflight
alone is not a content-integrity proof; installation and selection performed the
required content verification.

The new store is `~/AosEdge SDV Full Media`; private state is
`~/SDV-Full-Media`. Cloud remains unconfigured, `demoReady` is false, Docker
presence was observed but its engine was not tested. No vehicle, simulator,
backend or Cloud operation was started. The older `~/AosEdge SDV Packages` and
`~/SDV-Lab-Data` were not targeted. Runtime and Cloud E2E results from earlier
candidates are not relabelled as new results.

Post-read reconciliation confirmed the installation receipt, selected pin and
revision, no automotive run journal, and the presence of the prior installation.
No owned Setup/demo/VM/simulator process or listener on the demo ports remained.
The exact qualification image was ejected after checking its mounted identity
and absence of open users. Its DMG file and both installations remain on M1;
no runtime or Cloud identity was removed. Final native UI acceptance is deferred
until the functional sequence is ready, as requested by the user.

Compact timing and transaction evidence is retained in
`CarlaSim/Build-distribution-stage2-20260926/full-media-m1-20261002-receipt.json`
on the development Mac. The native newcomer journey and the remaining wizard,
persistent-launcher and release gates remain open.

## Subsequent scripted preparation

Later on 2 October the [journey runner](scripted-journey-2026-10-02.md) verified
this same installed candidate, prepared the packaged backend images, saved
references to the already authorized M1 OEM/SP credentials and passed the
read-only staging access check. This supersedes the earlier unconfigured-Cloud
observation above; no new credentials, automotive journal or Cloud Unit were
created. The private-key files were neither copied nor replaced.

The corrected installed-host smoke subsequently passed. Presenter exited and
its demo listeners were released. As explicitly clarified by the user, Docker
Engine remains background infrastructure: it was available after demo shutdown,
with zero running containers, and its subsequent readiness check started
nothing. The runner no longer quits Docker at the end of a test. Full serial
runtime qualification and the final native UI pass remain separate open gates.
