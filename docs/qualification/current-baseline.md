<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current demo baseline

- Status: engineering preview; scoped qualification, not general-public release acceptance
- Version: 3.2
- Prepared: 2026-10-19
- Owner: SDV Lab integration

## Current selection

The [launcher catalog](../../workspace/launcher-catalog.json) and its immutable
operator descriptor select option A's exact DMG, identity, download and status.
The [developer selection](../../workspace/current-developer-build.json) separately
binds option B's producer plan. Product version, functional profile, Cloud build
number and document version are different namespaces.

The [release report](release-automation-2026-10-13.md#published-release-120-rc3)
records the published successor, main/tag identities and anonymous M1 consumer.
The [M1 report](m1-clean-install-e2e-2026-10-14.md#mainline-candidate-120-rc3-api-and-visible-ui-pass)
records rc.3 runtime qualification separately from its now-published
operator delivery. Its earlier
[native Setup continuation](m1-clean-install-e2e-2026-10-14.md#native-setup-with-no-ready-certificates-pass-on-15-october)
binds the corrected Setup separately. Documentation changes do not advance
artifact pins or inherit another candidate's passes.

## Qualified current profiles

| Profile | Recorded result and scope |
| --- | --- |
| Installed runtime API | rc.3: 118/118 checks passed on M1 internal storage using Production Aos Cloud and a Test vehicle |
| Visible product UI | rc.3: 42/42 browser stages and required actual native driving input passed, with Presenter/CARLA/Driving Control visible |
| Native Setup without ready certificates | rc.2 only: empty fields, fresh M1-generated OEM/SP keys, issuance using existing accounts, Production connection and Presenter opening passed; not rerun or inherited by rc.3 |
| Public option A consumer | rc.3: anonymous Dropbox download, full checksum/signature, signed Setup handoff, read-only retained selection, Presenter opening and verified closure passed; no fresh enrollment or launcher replay |

Runtime proofs include serial VDP V1/V2/V3 Safe Stop FOTA, Brake V1/V2/V3,
Tire V1, real products/advisories, moving QM updates, independent Reset/history,
five-minute offline local operation and delivery recovery, ignition,
Stop/Start preservation, layout and final closure. Earlier failures remain
explicit in the report; a later pass does not erase their original receipts.

## Implemented system and ordinary return

The [architecture map](../architecture/current-implementation.md) and
[protocol status](../../contracts/implementation-status.md) describe the real
platform, simulated vehicle and accepted amendments. The Factory image is a
clean ARM64 Linux/AosEdge base; VDP and services are delivered afterward.
Aos Cloud environment selection is independent of Test/Production vehicle roles.

Open SDV Lab opens Presenter. For a stopped retained Test, use **Start
controller**, then follow simulator/connection readiness. **Stop demo and keep
data** preserves its identity, installed software, VM disk, models and history.
Closing Presenter alone keeps the demo running. **Delete Test & start over**
is a separate destructive operation. Shared Docker Engine is not a demo owner.

## Remaining acceptance limits

- Apple Development signing is not Developer ID/notarized general-public distribution.
- New-company/account registration and every clean-macOS consent path are not qualified.
- Target-host installation interruption/repair/update/removal and broader recovery/negative matrices remain candidate-specific gates; ordinary tested Stop/Start is not host sleep/wake.
- Full-source fresh Builder/CARLA/Unreal closure and R4 fresh-host developer reproduction remain separate.
- Formal stimulus/model calibration, fixed Tire CPU-load isolation, expanded dual-role/provider proof and a full acceptance dossier are not supplied by sampled functional results.
- Cold externalOFF ignition, nonempty-outbox power loss and laptop sleep/wake remain unqualified.
- Load-sensitive readiness and VDP-TIMEOUT-01 remain deferred.
- The short reported false-Offline fluctuation was not reproduced/classified by bounded observation; a passing campaign alone is not its root-cause analysis.

<a id="immutable-factory"></a>
<a id="current-qualification-limitation"></a>

## Input provenance

Current Brake/Tire private admin schemas and negative fixtures describe the
implemented handlers separately from retained legacy compatibility inputs.
Their source conformance is not a new live result or a change to this DMG.

The rc.3 candidate includes the accepted fingerprint-only Presenter boundary:
private identities are projected server-side before browser JSON, with bounded
opaque selectors and isolated regression coverage. Its new exact-DMG API/UI
proof is recorded above; a source/documentation commit alone never advances
the operator delivery or qualifies different bytes. CARLA and Factory were
reused without rebuilding.

The [controller image lock](../../workspace/inputs/controller-images.lock.json)
preserves immutable Factory provenance. It does not select operator media or
inherit another artifact's qualification. This page summarizes source/evidence,
not a fresh observation of running hosts.
