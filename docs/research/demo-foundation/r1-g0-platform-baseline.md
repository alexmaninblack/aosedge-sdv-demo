<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R1 — G0 Platform Baseline and Generic Runtime

Status: **research pass complete; implementation not authorized**.

## Accepted disposition — 2026-08-21

The generic-runtime recommendation below is retained as historical research
but is superseded by HLA 1.4, Component Register 1.1, `CR-FACTORY` 0.2 and
[`D4-001`](../../requirements/d4-decision-register.md#d4-001). The accepted
demo architecture deliberately uses one provider-specific empty-slot runtime
for the single Vehicle Data Platform Component. It does not require a generic
multi-provider runtime in the OEM Demo Factory Image.

Candidate `.11` is not rejected because its runtime is provider-specific. It
remains engineering evidence and requires a successor Factory Image only
because the later accepted stock-IAM, protected-signing, normative-manifest,
reproducibility and fresh-overlay qualification obligations are incomplete.
No implementation or build is authorized by this disposition.

## Decision scope

This workstream answers three questions:

1. What is installed on the Validation and Demonstration Units today?
2. What exists only as a local candidate?
3. Does the current platform satisfy Scenario 1.0's claim that produced
   vehicles already contain a generic post-SOP extension substrate at G0?

## Current evidence

Read-only inspection of the two current Units and repository evidence produced
this baseline:

| Unit role | Installed rootfs | Reported extra runtime | Runtime store | Provider state |
| --- | --- | --- | --- | --- |
| Demonstration | `6.1.1-maninblack.1` | `systemd-slot-component` / `vehicle-data-provider` | Present but empty | Inactive |
| Validation | `6.1.1-maninblack.2` | `systemd-slot-component` / `vehicle-data-provider` | Present but empty | Inactive |

Both Units retain their provisioned identities. No identity or credential
value was read.

The later `6.1.1-maninblack.11` rootfs contains the same runtime plus the
accepted storage, SELinux, launcher-identity, and dependency hardening. It is a
qualified local candidate but remains unsigned and uninstalled. Provider
`0.2.0` is signed and independently verified locally but remains unpublished
and unassigned.

## Findings

| Finding | Classification |
| --- | --- |
| Both installed Units already register the provider-specific component runtime; it does not exist only in `.11`. | **PROVEN** |
| Neither Unit currently has a provider payload installed or active. | **PROVEN** |
| The installed runtime is statically bound to one reported type, one systemd Unit, one executable/configuration layout, one provider store, one health adapter, and `maxInstances = 1`. | **PROVEN** |
| `.11` closes the current provider-specific security and storage chain but does not make that runtime generic. | **PROVEN** |
| The empty `.1/.2` stores demonstrate an empty feature state, but not an accepted secure and reusable G0 substrate. | **INFERRED** |
| Adding another hard-coded runtime for every later provider would require another rootfs release and contradict the post-SOP extensibility narrative. | **INFERRED** |
| Architecture documents should distinguish the existing provider-specific runtime from the generic substrate required by G0. | **PROPOSED** |

## The terminology correction

The current `SM-EXT` label overloads two different concepts. Split it into:

- **`SM-VPD`** — the existing Vehicle Data Provider-specific runtime
  mechanism;
- **`SM-GEN`** — the reusable platform substrate that can host later OEM
  provider extensions without introducing another feature-specific rootfs
  runtime.

An empty provider store does not make `SM-VPD` generic. G0 is accepted only
when the platform has a healthy empty state and a prequalified extension
contract without containing feature payloads, credentials, or live Brake
Health signals.

## Extension mapping options

| Option | Benefit | Limitation |
| --- | --- | --- |
| Treat installed `.1/.2` as final G0 | No new rootfs deployment | Provider-specific and not fully hardened |
| Promote `.11` as G0 | Completes the current provider security/store chain | Still provider-specific and not installed |
| Add a second hard-coded runtime | Fits the older R6.1 material/provider split | Repeats rootfs work for each new provider type |
| Reusable multi-type provider host/runtime | Closest match to independent post-SOP FOTA extensions | Requires AosCore/Cloud routing and isolation qualification |
| One predeclared `vehicle-data-platform` component with internal plugins | Conservative fallback using a single known runtime type | Individual providers are not independently visible as Cloud components |

## Recommendation

Do not label `.1`, `.2`, or `.11` as the final generic G0 substrate.

First choose the physical extension mapping:

1. Prefer independently visible provider components if the pinned AosCore and
   AosCloud can route multiple new component types through one safely isolated
   runtime contract.
2. Otherwise adopt one predeclared `vehicle-data-platform` FOTA component with
   independently versioned and validated plugins as the practical demo
   fallback.

Then create one common accepted G0 rootfs for both Units. It must:

- boot and report healthy with no provider or Brake Health service installed;
- expose a stable runtime inventory and capability registry;
- isolate multiple extension payloads, stores, transactions, identities, and
  health results;
- keep feature-specific configuration, credentials, and payloads out of the
  rootfs;
- fail closed when a component type, dependency, signature, or security
  profile is not accepted;
- support a visible installed-component lifecycle without requiring another
  Yocto change for the next supported provider.

## Required experiments

1. Parameterize the current runtime in a repository-only disposable test
   harness and prove two isolated synthetic component types, stores,
   transactions, and health adapters without a Yocto build.
2. Against the pinned AosCore source, prove whether one runtime plugin can
   register or route multiple Cloud component types and how inventory is
   reported.
3. In an unprovisioned disposable VM, prove the proposed G0 empty state,
   install/remove two non-secret components, failure isolation, reboot, and
   recovery.
4. Confirm whether AosCloud requires every type to be present in runtime
   inventory before assignment.
5. Decide whether independent Cloud visibility is mandatory for every
   provider or whether provider-host inventory is acceptable for this demo.
6. Only after those gates, build one rootfs candidate and test it on the
   Validation Unit under a separately authorized change window.

## Documentation contradictions found

- The current demo and validation Units already contain `SM-VPD`; the flow
  document incorrectly says the runtime exists only in uninstalled `.11`.
- The scenario describes a generic SOP substrate, while the lower-level
  platform architecture correctly acknowledges that the current runtime is
  provider-specific.
- The older R6.1 plan proposes two feature-specific runtimes, while the newer
  architecture requires the next baseline to create a reusable substrate.
- Platform README text saying the Demonstration Unit remains on `6.1.0` is
  stale; the accepted and observed version is `.1`.

These are recorded for later documentation correction. This research pass did
not edit the accepted HLA, scenario, or implementation plan.

## Sources

- [Current accepted baseline](../../qualification/current-baseline.md)
- [High-Level Architecture 1.4](../../architecture/high-level-architecture.md)
- [Component Decomposition and Interface Register 1.1](../../requirements/component-decomposition-and-interface-register.md)
- [`aos-vehicle-platform` Service Manager configuration](../../../../aos-vehicle-platform/meta-aos-vehicle-platform/recipes-aos/aos-servicemanager/files/sm.cfg)
- [AosCore architecture](https://docs.aosedge.tech/docs/aos-core/architecture/)
