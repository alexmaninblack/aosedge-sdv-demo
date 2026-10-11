<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter branch DMG and M1 qualification — 11 October 2026

Status: Complete DMG built and verified; candidate M1 installation and live/native
acceptance NOT_RUN. Do not promote this record to release acceptance.

## Scope and candidate

Branch: `codex/presenter-human-friendly`. Presenter product source:
`d65c4f0af952253d64a65141fa4e25358c610000`. Main is unchanged at
`a4afa82e2dd2e6007102797cb785e5f004e46db6`.

Candidate output:
`/Volumes/SDV-Build/sdv/build/candidates/presenter-human-friendly-20261011-dmg`.
The complete DMG is named `AosEdge-SDV-Lab-Presenter-Review-20261011.dmg`.
Build only UI/native helpers and Setup; reuse reviewed Gateway, Factory `.41`,
CARLA, Python, QEMU and backend inputs. No simulator or Factory rebuild is
required for this Presenter change. Credentials and installed run state are
not part of the media. Existing Apple Development signing does not imply
Developer ID/notarization or public distribution approval.

## Build findings

Two local orchestration-input mistakes were corrected without weakening the
canonical checks or changing runtime behavior:

1. A previously repackaged host group cannot serve as the original SDK-origin
   input to the native assembler. The OpenSSL source-provenance guard rejected
   it. Reuse the original reviewed retained host input with manifest SHA-256
   `f6ae4b1222e55a0d15501176ca0ab91aaa29ce011817419c1e6b3443c5dacff2`.
2. The direct packaging orchestration omitted the existing workspace scratch
   root setting. Native signing left two empty-registry metadata files inside
   the host group. Exact inventory validation rejected those undeclared files.
   Use `SDV_SCRATCH_ROOT` on the selected SSD, as the ordinary reproduction
   worker environment already does. Remove only the owned, idle empty metadata
   directory; reuse completed verified UI/host/VM outputs. Do not add scratch
   files to the payload manifest or relax its equality check.

The native Setup protocol self-test passed. Final DMG image verification passed;
the build receipt records 14,160,513,657 bytes and SHA-256
`65cec3f47d3c5963843505d06de15b42e219a8124cf0ce51e732d53e04f17b26`.
The application manifest is
`6f9b0391d1c696c7bbe07c0b94ead485536b47956bb893c7b354d65bb15d10b5`;
the signed Setup executable is
`be5b586fb90858d45c4056a209211cf117446921b716cc34b04babd6bb2084a5`.
These pins bind the new M1 campaign and cannot inherit the old candidate's
passes. The media receipt explicitly reports `notarized: false` and no runtime
or Cloud launch during packaging. Owned full-size staging is cleaned on exit.
Compact private logs
are in `.local/presenter-human-friendly/`. Large outputs remain on the SSD.

## Fixed campaign and local evidence

The qualification harness suite passed 78 tests. The 117-step fixed journey
uses exact installed candidate/Test bindings, journaled request identities and
the existing signed Setup and product owners. It covers:

- Installation and backend preparation; current staging certificate pair.
- New Test, simulator, provisioning and attachment.
- Serial VDP V1→V2→V3 via Safe Stop and Brake V1→V2→V3, then Tire V1.
- Native maneuver commands, new product delivery and correlated advisories.
- Independent resets, return to road, 300-second offline operation/recovery.
- Ignition off/on, unchanged identity/models/history and new post-boot results.
- Stop demo/Start controller on the same Test, observed source/VM/backend stop,
  preserved Docker Engine, explicit simulator start/attachment and new results.
- Test-owned process/window shutdown with persistent state preserved.

Native window/layout and button acceptance remain separately observed; a
scripted operation is not a native click. New-account token entry, moving SOTA,
installation interruption/repair and external distribution are not silently
closed by this branch campaign. The deferred VDP timeout is not changed.

## M1 preparation boundary

The new DMG was delivered to
`SDV-Qualification/presenter-review-20261011/AosEdge-SDV-Lab-Presenter-Review-20261011.dmg`
under the authorized M1 test user's home directory.
The canonical media owner recorded transfer PASS (213.977 seconds, exact
consumer digest and unchanged file identity) and mount/signature/pin verification
PASS (71.485 seconds). Installation was deliberately not dispatched while the
existing-state gate is blocked. The private installation report correctly says
`installation: NOT_COMPLETE`, `nativeAcceptance: NOT_RUN` and
`fullE2E: NOT_COMPLETE`. Later continuation rechecks the same media identity;
it does not retransmit a verified large file merely for another status check.

M1 transport and unlocked Screen Sharing are available; the demo was quiescent
at preflight. The old default instance retains a provisioned Test. Installed
selection correctly blocks replacing that kit until normal retirement.

The exact old Test was `524ed2c5-23b6-4ec7-ab81-e8687f4be096`; its staging Unit
was `5c2e41b1-19cf-43c9-9428-89460015d243`. Tool review initially rejected the
retirement and scoped unused-copy deletion before execution and required exact
target approval. The operator then explicitly approved those objects. Normal
installed retirement confirmed `COMPLETED / RETIRED`, and the run journal is
absent. Retirement was not replayed during subsequent copy cleanup.

The two approved unused qualification DMGs and the unselected `1cb2628a…`
package were removed after exact target/usage checks. Approximately 159 GiB is
free on M1. The accepted `e296fd…` package, credentials, source and Production
are preserved. An overly broad local cleanup preflight checked preserved state
as well as the actual removed copies; it was narrowed to the deletion targets.
The separate product installation guard was not changed.

That installation guard still reports `INSTALLED_NATIVE_CONSUMER_ACTIVE`.
The only foreign holder of the retired instance is the Docker Virtualization
file-sharing cache; zero containers are running. A separate explicit request
was sent for one M1-only Docker Engine restart with images/data preserved.
This is exceptional host maintenance, never a routine Engine lifecycle test.
Candidate installation/live testing remain NOT_RUN pending release of that
holder. Do not bypass the guard, alter the journal or force version selection.
