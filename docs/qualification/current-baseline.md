<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current demo baseline

- Status: engineering preview; scoped qualification, not general-public release acceptance
- Version: 3.4
- Prepared: 2026-10-22
- Owner: SDV Lab integration

## Current selection

The [launcher catalog](../../workspace/launcher-catalog.json) and its immutable
operator descriptor select option A's exact DMG, identity, download and status.
The [developer selection](../../workspace/current-developer-build.json) separately
binds option B's producer plan. Product version, functional profile, Cloud build
number and document version are different namespaces.

The [rc.4 record](current-rc4.md) binds the delivered bytes, supported
retained-Test update, pending-FOTA recovery, M1 API/UI results and option A
consumer. Its delivery rename preserves the original build and qualification
receipts. The [earlier M1 record](m1-clean-install-e2e-2026-10-14.md) and
[independent B record](developer-reproduction.md) describe different candidates,
not current rc.4 passes. Documentation changes do not advance artifact pins or
inherit another candidate's qualification.

## Qualified current profiles

| Profile | Recorded result and scope |
| --- | --- |
| Installed runtime API | rc.4 retained Test: 115/115 checks passed on M1 internal storage using Production Aos Cloud and a Test vehicle |
| Visible product UI | rc.4: 42/42 stages passed with actual native Driving Control input and visible demo surfaces |
| Supported package update and pending FOTA | rc.4: retained Test/data preserved; unchanged-boot/same-enrollment recovery passed without deleting the transaction or changing security policy |
| Native Setup without ready certificates | NOT_RUN for rc.4. The earlier rc.2 existing-account issuance proof is candidate-specific, not inherited |
| Public option A consumer | rc.4: exact already transferred media checksum/signature, signed Setup handoff, unchanged retained selection and closure passed. No redundant payload download, fresh installation or enrollment |
| Independent developer workspace | Current B selects rc.4-compatible product sources; its new complete build and exact-package qualification are NOT_RUN. The earlier independently rebuilt rc.3 has [separate evidence](developer-reproduction.md), not an rc.4 B pass |

The recorded retained-Test scenario covers runtime updates, products/advisories,
Reset/history, offline recovery, ignition, Stop/Start and closure within its
exact declared profile. It is not a fresh sequential bootstrap or the separate
moving-SOTA/native acceptance matrix. Earlier failures remain explicit in the
receipts; a later pass does not erase them.

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
- Supported retained-Test package update passed for rc.4; installation interruption/repair/removal and broader recovery/negative matrices remain separate. Ordinary tested Stop/Start is not host sleep/wake.
- Native first use without ready certificates, moving-SOTA acceptance and the full native operator journey remain unqualified for rc.4.
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

The rc.4 candidate retains the accepted fingerprint-only Presenter boundary:
private identities are projected server-side before browser JSON, with bounded
opaque selectors and isolated regression coverage. Its new exact-DMG API/UI
proof is recorded above; a source/documentation commit alone never advances
the operator delivery or qualifies different bytes. CARLA and Factory were
reused without rebuilding.

The [controller image lock](../../workspace/inputs/controller-images.lock.json)
preserves immutable Factory provenance. It does not select operator media or
inherit another artifact's qualification. This page summarizes source/evidence,
not a fresh observation of running hosts.
