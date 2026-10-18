<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current delivery roadmap

- Status: Current remaining-work map; no runtime mutation authorized
- Updated: 2026-10-15
- Owner: SDV Lab integration

## Implemented engineering-preview route

The selected package is resolved from the
[launcher catalog](../../workspace/launcher-catalog.json). The
[current baseline](../qualification/current-baseline.md) and release receipts
define its proof and limitations.

Implemented: a complete DMG; integrated native Setup; existing-pair connection
and new certificate issuance for existing accounts; installed Presenter entry;
ARM64 controller creation from the Factory image; serial VDP and service
delivery; real vehicle-derived Brake/Tire results; independent Reset/history;
offline delivery recovery; controller ignition; API/browser/native scenario
automation; main/tag publication and anonymous operator delivery.

The single launcher provides:

1. Install and run using the selected DMG and Setup.
2. Build project components/installer using pinned sources and prebuilt
   simulator/controller inputs.
3. Prepare specialist host tools for the controller image or simulator;
   this is not turnkey full-source reproduction.

<a id="future-implementation-workstreams"></a>

## Remaining gates

| Work | Required proof / boundary |
| --- | --- |
| Fresh developer reproduction (R4) | New declared environment, exact sources/inputs, complete build, measured time/space, no hidden maintainer paths |
| Full-source rebuilding | Fresh Linux Builder acquisition/guest preparation and complete licensed CARLA/Unreal recipe, inputs and measured capacity |
| General-public macOS distribution | Developer ID, notarization, supported consent paths and complete dependency/redistribution closure |
| New Cloud users | Official company/account registration and email path; issued certificates for existing accounts are not this proof |
| Native installation/return robustness | Candidate-bound interruption/repair/update/removal cases and full stopped-controller return journey |
| Formal product acceptance | Outstanding calibration, negative/security/resource matrices, nonempty-outbox power loss and expanded vehicle-role/provider cases |
| Host sleep/wake | Separate accepted recovery plan; controller ignition does not implement it |
| Contract maintenance | Keep current admin profiles/negative fixtures aligned with handlers while preserving explicitly selected legacy compatibility inputs; no runtime change is implied |
| Deferred timing diagnostics | Load-sensitive readiness and VDP-TIMEOUT-01 remain deferred; do not restart them as documentation work |

A successful current engineering campaign is not blanket acceptance of every
normative requirement. The [release campaign](../development/release-campaign.md)
owns promotion; [M1 scenarios](../../scripts/qualification/README.md) own execution.

## Fresh developer reproduction

R4 remains an independent proof, not another M1 operator installation. Declare
a fresh host/workspace, obtain only published inputs and authorized tools/keys,
and execute the documented [developer route](../getting-started/reproduce-demo.md).
Record exact source and artifact identities, binary/cache reuse, elapsed time
and peak disk demand. Exercise the resulting candidate's applicable installation
and runtime profiles; another DMG's passes do not transfer to it.

The [developer selection](../../workspace/current-developer-build.json) and
[operator catalog](../../workspace/launcher-catalog.json) are independent.
Normal developer assembly reuses source-locked simulator/controller inputs
from the [Dropbox dependency catalog](../../workspace/dependencies/catalog.json).
It does not promise turnkey fresh Yocto/CARLA/Unreal compilation.

No provisioned VM, credentials, release ledger or hidden maintainer directory is
a required build input. Preserve receipt, dependency, signing and promotion gates;
do not export private keys, relocate/restart Docker, bypass security or publish
automatically. Current builds permit internal or external writable local APFS;
frozen producer plans retain their own policies and byte identities.

## Execution priorities

1. Complete the independent developer reproduction above.
2. Close candidate-bound installation/recovery/permission and new-account
   paths through their explicit independent scenarios.
3. Close Developer ID/notarization and dependency/source/redistribution review
   before claiming general-public distribution.
4. Execute outstanding formal product matrices only within their authorized scope.

Install / Connect / Open belongs to the [Setup contract](../../contracts/distribution-installation/native-setup.md#integrated-user-journey),
not a pending implementation packet. Scenario execution, private test access,
serial publication, Safe Stop and final cleanup belong to the M1 scenario guide
and [execution policy](../governance/rapid-development-and-debugging.md).
Source, cache and scratch placement follow the [reproduction contract](../../contracts/release-reproduction/README.md).
Docker's actual backing disk is checked independently and is never moved as a
build side effect. M1 installation uses its internal storage.

## Canonical design chain

[HLA 1.8](../architecture/high-level-architecture.md) →
[Scenarios 2.3](../demo/staged-post-sop-brake-health-demo-scenarios.md) →
[Flows 2.4](../architecture/demo-scenario-architecture-flows.md) →
[System Requirements 2.4](../requirements/system-requirements-and-traceability.md) →
[Component Register 2.3](../requirements/component-decomposition-and-interface-register.md) →
[component packages](../requirements/components/README.md).

These accepted designs include expanded obligations beyond the implemented
Test-only demonstration. Amendments, scope and actual proof must be read together.
Closed historical milestone lists are in Git, not a second active roadmap.
