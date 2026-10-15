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
| Contract synchronization | Versioned legacy executable-profile drift, without changing accepted wire bytes or weakening handlers |
| Deferred timing diagnostics | Load-sensitive readiness and VDP-TIMEOUT-01 remain deferred; do not restart them as documentation work |

A successful current engineering campaign is not blanket acceptance of every
normative requirement. The [distribution plan](active/installable-distribution-and-reproducibility.md),
[reproduction packet](active/work-packets/human-friendly-reproduction.md) and
[release-campaign contract](../development/release-campaign.md) own execution details.

## Canonical design chain

[HLA 1.8](../architecture/high-level-architecture.md) →
[Scenarios 2.1](../demo/staged-post-sop-brake-health-demo-scenarios.md) →
[Flows 2.2](../architecture/demo-scenario-architecture-flows.md) →
[System Requirements 2.2](../requirements/system-requirements-and-traceability.md) →
[Component Register 2.2](../requirements/component-decomposition-and-interface-register.md) →
[component packages](../requirements/components/README.md).

These accepted designs include expanded obligations beyond the implemented
Test-only demonstration. Amendments, scope and actual proof must be read together.
Closed historical milestone lists are in Git, not a second active roadmap.
