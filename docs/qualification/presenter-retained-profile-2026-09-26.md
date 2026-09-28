<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter profile binding for retained VDP releases

- Date: 26 September 2026.
- Scope: operator-authorized metadata correction for the preserved Test .39.
- Source: uncommitted working-tree increment on `0d13212`; unrelated distribution work retained.
- Contract: [Cloud-first installed-profile projection](../architecture/demo-control-cloud-observation.md).

## Cause and correction

Cloud reports VDP117 installed, but the current run has no component-publication
operation for that reused release. Its original domain/OEM-scoped publication
receipt and inspected V3 package are still retained. The Presenter previously
scheduled publication reconciliation and resolved the profile only from current-
run operations, so it displayed `Release · 117.0.0`. Brake and Tire use the
retained service-release catalogue and did not have this particular limitation.

The existing profile resolver now reads the exact retained publication receipt
selected by its preceding Cloud inventory. This is an in-memory projection,
not a journal repair or new state store. Existing independent Cloud publication
reconciliation, version UUID, owner/domain/Unit, upload, signing/preparation and
package digest/profile checks remain mandatory. No profile is inferred from
the numeric release, pending successor, latest preparation or saved READY field.
Only an exact installed-release hint is added; no catalogue-wide scan, guest
read, endpoint, timer, synchronous publication wait or mutation is introduced.

## Regression and read-only live proof

The new regression reproduces the old defect: four positive binding/retention
cases failed before the correction. All eleven new cases pass afterwards,
including unchanged journal, restart, wrong UUID/Unit/context, malformed/missing/
symlinked receipt, changed package, no absent-installation scan, slow single-
flight publication and Offline versus stale separation. The existing eight
resolver cases also pass. All 53 Presenter tests pass under the deployed private
Python 3.12. The first restricted run could not bind isolated test sockets;
that harness permission failure was rerun with permission, without weakening
product checks.

The corrected production reader independently queried the preserved staging
Test. Its first inventory established the exact installed release; subsequent
asynchronous publication reconciliation confirmed:

| Fact | Observed |
| --- | --- |
| Unit | `5395f7d6-2ff3-4d10-9e7f-efa85e7994eb` |
| Connectivity | `ONLINE` |
| Installed VDP | `117.0.0` |
| Cloud version UUID | `fae4b24a-190e-45f3-91c2-db322d10f409` |
| Profile | `CURRENT`, `v3`, `CLOUD_INSTALLATION_AND_PACKAGE` |
| Original deployment | `9f0e875e-2ca7-48cb-ae63-91213fe73b00` |
| Journal | Byte-for-byte unchanged by the proof |

The three reads took 1.421, 1.027 and 1.094 seconds. These are measured individual
read durations, not an E2E UI latency guarantee. Unknown remains visible until
the independent publication response is consumed. No package signing, upload,
VM/CARLA/controller operation or service reset occurred.

## Activation and remaining scope

The complete orchestrator regression passes **1,120 tests, 17 explicit skips**
in 120.427 seconds. The existing frontend installed-profile suite passes all
20 cases. Documentation validation passes 279 Markdown documents, 658 stable
identifiers and 38 Mermaid diagrams; whitespace checks pass. No new browser
automation or native UI rebuild was needed for this read-projection change.

The normal exact-owner/idle `ui stop` gate succeeded. The same private Python
entry then started the corrected server as PID14301. Native Presenter PID51041
remained unchanged; both main frames committed and finished their normal
session refresh at17:18:25CEST. This is load evidence, not a new visual
inspection: browser-tool access to the real page remains unavailable. The
independent production reader above proves the profile returned by the updated
read path; the unchanged UI formats it as `v3 · 117.0.0`.

CARLA PID26084, Driving Control PID26136 and Test QEMU PID37277 retain their
original process start times. No native/web payload, host-runtime manifest,
Factory image, Cloud identity, service/model or package was changed. No build
artifacts were created, and no cache was deleted; approximately102GiB remained
free at the final disk sample.

This closes the retained-release metadata defect, not unrelated advisory
readiness issues or
the [mixed-interpreter DNS ownership gate](standalone-host-handoff-2026-09-26.md#explicit-open-gates).
No commit, push, tag movement, disk cleanup or new E2E acceptance is claimed.
