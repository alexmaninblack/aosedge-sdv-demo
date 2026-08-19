<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory Substrate Component Requirements

- Status: D3 design-reviewed
- Package: [`CR-FACTORY`](../component-decomposition-and-interface-register.md#cr-factory)
- Version: 0.2
- Prepared: 2026-08-19
- Owner: Platform Team / pre-SOP OEM Factory Baseline Assembly
- Architecture input: [High-Level Architecture 1.4](../../architecture/high-level-architecture.md)
- Scenario input: [Demo Scenarios 1.7](../../demo/staged-post-sop-brake-health-demo-scenarios.md)
- Flow input: [Architecture Flows 1.6](../../architecture/demo-scenario-architecture-flows.md)
- System-requirements input: [System Requirements 0.9](../system-requirements-and-traceability.md)
- Component-register input: [Component Register 1.0](../component-decomposition-and-interface-register.md)
- Implementation evidence: `aos-vehicle-platform@15b6abb`, with local
  candidate `.11` pinned to `a12c0aa`

## Purpose

This package defines the pre-SOP OEM assembly that produces a clean,
unprovisioned and immutable Domain Controller image and the provider-specific
empty-slot runtime contained in that image. It also distinguishes that
manufacturing artifact from two later delivery artifacts:

1. an optional rootfs FOTA envelope used to retrofit or update an already
   manufactured and provisioned Unit; and
2. the independently versioned Vehicle Data Platform Component delivered into
   the empty slot after SOP.

The normal demo manufacturing path shall not install the initial empty-slot
runtime through post-provision rootfs FOTA. A fresh Unit receives that runtime
from the accepted OEM Demo Factory Image before provisioning.

## Reader Summary

| Question | Answer |
| --- | --- |
| What this package owns | Reproducible pre-SOP composition, the full bootable Factory Image, its immutable evidence, clean identity/key-free content, enabled stock Aos IAM permission handling, the non-secret IAM/PKCS#11 broker-key seam, and the provider-specific empty-slot runtime |
| What this package does not own | Cloud provisioning transactions, per-Unit key creation, Credential Broker behavior, provider-identity binding, Vehicle Data Platform payload behavior, functional SOTA services, demo-stage orchestration or production storage selection |
| Intended result | Two fresh unprovisioned Domain Controller deployments can be created from one accepted image and later receive the Vehicle Data Platform Component without another rootfs update |
| Accountable lifecycle owner | Platform Team; pre-SOP factory/build lifecycle and later platform/rootfs FOTA lifecycle when explicitly required |
| Primary repository | `aos-vehicle-platform`; release metadata and qualification orchestration in `aosedge-sdv-demo`; image bytes remain outside Git |

## Artifact and Lifecycle Model

One pinned Yocto assembly may produce more than one artifact, but those
artifacts have different purposes and must never be presented as the same
lifecycle object.

| Artifact | Contents | Normal lifecycle | Installed through | Role in this demo |
| --- | --- | --- | --- | --- |
| OEM Demo Factory Image | Complete bootable, unprovisioned VM disk with AosCore, enabled stock IAM permission handling, KUKSA, non-secret IAM/PKCS#11 integration seam and the empty-slot runtime; no per-Unit key or token | Pre-SOP manufacturing | Fresh read-only base plus a new copy-on-write overlay | Required source for M0 |
| Rootfs platform-update envelope | Complete rootfs payload containing a selected platform revision | Post-SOP platform/rootfs FOTA | The factory-installed AosVM rootfs A/B runtime | Optional retrofit or later platform maintenance; not used to add the initial runtime in the normal M0-M1 flow |
| Vehicle Data Platform Component | Independently versioned provider payload and its component metadata | Post-SOP component FOTA | The provider-specific `systemd-slot-component` A/B runtime | Required at G1 and later |

The `.11` Yocto build produced both a full raw VM image and an unsigned rootfs
FOTA candidate from the same rootfs content. The full raw image is engineering
evidence for the future Factory Image acceptance. The rootfs envelope is an
upgrade artifact for an older Unit; it is not the Vehicle Data Platform
Component and it is not required when manufacturing a fresh Unit from the
accepted Factory Image.

## Component Boundary

### In scope

- [OEM Factory Baseline Assembly (`CMP-FACTORY`)](../component-decomposition-and-interface-register.md#cmp-factory), including pinned upstream and OEM integration inputs, build, qualification and freeze;
- the complete bootable OEM Demo Factory Image and its manifest/digest;
- [Provider-Specific Empty-Slot Runtime (`CMP-RUNTIME`)](../component-decomposition-and-interface-register.md#cmp-runtime), including Service Manager registration, A/B state, launcher, health, systemd, storage and SELinux integration;
- stock Aos IAM permission-handler enablement and the non-secret
  IAM/certificate-module and PKCS#11 configuration seam required by the future
  Credential Broker;
- proof that the factory image contains no provisioned identity, reusable
  vehicle secret, provider payload or functional service;
- the factory-side contract required for distinct first-boot identities in
  fresh overlays;
- preservation of the immutable Factory Image across retirement and reset.

### Out of scope

- the AosCloud provisioning transaction and Cloud-side Unit/Node lifecycle,
  owned by `CR-AOS` and invoked by `CR-DEMO`;
- the Vehicle Data Platform executable, signal contract, thin Credential
  Broker, provider platform-identity binding and KUKSA token issuance, owned by
  `CR-VDP`;
- per-Unit broker signing-key generation or provisioning, which is a later
  identity/security lifecycle and must not be baked into the Factory Image;
- a generic runtime for arbitrary future component types;
- production vehicle storage architecture;
- signing, publishing or assigning a rootfs update during normal M0-M1.

### Dependencies and assumptions

| Dependency or assumption | Owner | Required state | Failure consequence |
| --- | --- | --- | --- |
| Identified AosEdge/AosVM release | AosEdge platform | Immutable revision, build graph and license inputs | Factory assembly fails before producing an accepted artifact |
| OEM Yocto integration layer | Platform Team | Pinned revision and passing repository/build gates | No Factory Image may be frozen |
| Host overlay lifecycle | Demo Orchestration | Creates only fresh overlays from the verified read-only base | M0 fails without modifying the Factory Image |
| First-boot identity generation | AosVM plus OEM integration | No baked reusable identity; fresh instances generate distinct local identities | Provisioning is blocked and the candidate is rejected |
| Aos provisioning | `CR-AOS` | Exactly one unique Unit/Main Node identity per fresh overlay | The deployment is quarantined; the Factory Image is not modified |
| Aos IAM permission handling | AosCore plus OEM factory integration | Stock permission handler enabled and reachable; no project-owned service secret store | SOTA services cannot obtain KUKSA credentials and the factory candidate is rejected |
| Signing-key facility | Aos IAM/certificate module plus PKCS#11 integration | Non-secret module/configuration seam in the image; per-Unit key established later | Broker readiness fails closed; no file-key fallback or baked key is permitted |

## Current Implementation Baseline

| Capability | Evidence | State |
| --- | --- | --- |
| Full bootable `.11` raw image | `main-qemuarm64.img`, 6,997,147,648 bytes, SHA-256 `946a296b7200644bc529080f3512712d8b7ec97dedad520146a4f503cf4006a2`; clean AArch64 boot through a disposable qcow2 overlay | `EVIDENCE`; not yet the accepted Factory Image |
| Separate `.11` rootfs FOTA candidate | Full rootfs payload, 128,528,384 bytes, SHA-256 `e30406f600ada77568d21178e656a34f444973bf121f5a0b537e24efde8ab9d7`; unsigned and uninstalled | `EVIDENCE`; optional retrofit artifact only |
| Provider-specific runtime | `systemd-slot-component`, reported provider type, one active instance, A/B implementation and persistent recovery | `CURRENT / QUALIFY` |
| Empty-slot behavior | Provider service inactive, launcher and health fail safely, no active slot or payload | `CURRENT / QUALIFY` |
| Security boundary | Fixed `aos-vdp` identity, empty capabilities, SELinux transition, systemd credentials and bounded access | `CURRENT / QUALIFY` |
| Demonstration store | 512 MiB nested ext4 inside encrypted Aos workdirs | `CURRENT` for demo; production backend intentionally undecided |
| Clean unprovisioned checks | No provisioning marker, Aos user PIN, credential-like file, provider payload or functional service in disposable candidate boot | `EVIDENCE`; repeat on the accepted Factory Image |
| Stock Aos IAM permission handler | The deployed AosCore build contains the handler, but live `.1`/`.2` `/etc/aos/iam.cfg` does not enable it and the parser default is disabled | `GAP`; Factory Image configuration and boot qualification required |
| IAM/PKCS#11 broker signing seam | AosCore supplies generic IAM certificate-module and PKCS#11 facilities; no accepted broker module/key binding is configured in the current candidate | `PARTIAL EXTERNAL CAPABILITY`; non-secret integration and per-Unit key lifecycle qualification required |
| Source lock and repository gates | `.11` pinned to `a12c0aa`; build-affecting Yocto-layer files are unchanged at current `main`; 35 Python tests and the 81-file quality gate pass | `CURRENT`; output reproducibility proof remains open |
| Distinct fresh overlays | Existing `.1` and `.2` Units have different provisioned identities but are not derived acceptance evidence for the unprovisioned `.11` raw image | `TARGET` |

The installed `.1` and `.2` rootfs versions prove that an earlier form of the
runtime can exist with an empty provider slot. They are already provisioned and
must never be used as a Factory Image source. Candidate `.11` adds the accepted
hardening but remains engineering evidence until this package's factory gates
pass.

## Testability Boundary

Source-lock validation, artifact classification, manifest/digest verification,
forbidden-content policy, runtime configuration, archive checks, A/B state
transitions, security policy and reset guards are deterministic owned logic and
shall be tested without AosCloud or a live provisioned Unit.

Bootability, first-boot identity generation, empty-slot health, SELinux state,
two-overlay uniqueness and provisioning identity separation require disposable
VM integration. Unit tests must not fabricate acceptance for those properties.
No test may print identity or credential values; uniqueness evidence uses
redacted comparison or digests.

## Interface Summary

| Interface | Direction | Data or command | Contract/version | Failure behavior | Authority |
| --- | --- | --- | --- | --- | --- |
| [Cloud-to-Unit lifecycle (`IF-LC-004`)](../component-decomposition-and-interface-register.md#if-lc-004) | Later inbound | Rootfs or component desired state after provisioning | AosCloud/AosCore lifecycle | Not used to add the initial runtime in M0-M1; later update failures retain the previous accepted slot | AosCloud desired state and Unit actual state |
| [Runtime enforcement (`IF-LC-006`)](../component-decomposition-and-interface-register.md#if-lc-006) | In/Out | Prepare, apply, start, stop, revert, health and inventory | Fixed provider-specific runtime contract | Reject unsupported type, unsafe payload or invalid state without changing the active release | AosCore Service Manager actual state |
| [Broker IAM/PKCS#11 substrate (`IF-AUTH-005`)](../component-decomposition-and-interface-register.md#if-auth-005) | Later outbound | Enabled permission lookup and protected signing operation without exporting key bytes | Aos IAM/certificate-module and PKCS#11 integration | Broker remains unready; no local file-key fallback | AosCore IAM and per-Unit platform key lifecycle |
| [Orchestrated VM lifecycle (`IF-DEMO-001`)](../component-decomposition-and-interface-register.md#if-demo-001) | Out | Verified image digest, fresh-overlay creation and role handoff | M0/R0 lifecycle contract | Reject missing/mutable base, reused overlay or unresolved identity | Factory manifest plus orchestrator session evidence |

## Verification Strategy

| Level | Purpose | Dependency boundary | Required | Planned evidence |
| --- | --- | --- | --- | --- |
| Unit | Prove validators, state transitions, archive policy and reset guards | Filesystem, process, clock and platform commands replaced by fixtures/fakes | Yes | `UT-FACTORY-*` obligations in normal repository/build gates |
| Component | Prove the built runtime and complete Factory Image contents | Disposable image/overlay without Cloud identity | Yes | Runtime suite, image manifest and guest qualification report |
| Contract | Prove artifact types, component type and runtime/FOTA boundaries | Versioned manifests and release fixtures | Yes | Factory manifest, rootfs-envelope metadata and provider-runtime conformance |
| Integration | Prove clean boot, empty slot, security and two fresh overlays | QEMU/HVF and later controlled provisioning | Yes | Redacted two-overlay qualification and exact image digest |
| End-to-end | Prove M0, M1, G0 and R0 preserve the lifecycle model | Full Validation and Demonstration lanes | Yes | Software Delivery Dashboard and retained lifecycle evidence |

## Requirement Summary

| Requirement | Plain-language obligation | Implementation | Verification levels |
| --- | --- | --- | --- |
| [Pinned factory assembly (`REQ-FACTORY-001`)](#req-factory-001) | Rebuild from identified upstream and OEM inputs | `PARTIAL` | Unit, Contract, Component |
| [Distinct build artifacts (`REQ-FACTORY-002`)](#req-factory-002) | Never confuse Factory Image, rootfs FOTA and provider component FOTA | `PARTIAL` | Unit, Contract, Inspection |
| [Clean SOP substrate (`REQ-FACTORY-003`)](#req-factory-003) | Ship runtime and security seams but no payload, service, reusable identity or signing key | `EVIDENCE / EXTEND` | Unit, Component, Integration |
| [Immutable bootable Factory Image (`REQ-FACTORY-004`)](#req-factory-004) | Freeze a complete bootable image by digest | `EVIDENCE` | Unit, Component, Integration |
| [Healthy provider-specific empty slot (`REQ-FACTORY-005`)](#req-factory-005) | Report one safe empty capability slot at G0 | `CURRENT / QUALIFY` | Unit, Component, Integration |
| [Atomic component lifecycle (`REQ-FACTORY-006`)](#req-factory-006) | Install and recover provider payloads without corrupting the active slot | `CURRENT / QUALIFY` | Unit, Component, Integration |
| [Bounded security and storage (`REQ-FACTORY-007`)](#req-factory-007) | Enforce fixed identity, policy and bounded demo storage | `CURRENT / QUALIFY` | Unit, Component, Integration |
| [Identity-safe fresh deployments (`REQ-FACTORY-008`)](#req-factory-008) | Create two overlays without duplicating local or Cloud identity | `TARGET` | Unit, Integration, End-to-end |
| [Pre-provision runtime availability (`REQ-FACTORY-009`)](#req-factory-009) | Start M1 with runtime already in the manufactured image | `TARGET acceptance` | Inspection, Integration, End-to-end |
| [Factory artifact preservation (`REQ-FACTORY-010`)](#req-factory-010) | R0 discards overlays but retains the exact Factory Image | `TARGET` | Unit, Integration, End-to-end |
| [Native IAM credential substrate (`REQ-FACTORY-011`)](#req-factory-011) | Enable stock service-instance permission handling and a non-secret protected-key integration seam before provisioning | `GAP / PARTIAL` | Unit, Component, Integration |

## Detailed Requirements

### Pinned factory assembly

<a id="req-factory-001"></a>

- ID: `REQ-FACTORY-001`
- Statement: The OEM Factory Baseline Assembly shall use an immutable source
  lock identifying the AosEdge release, OEM integration revision, build graph,
  configuration and toolchain inputs and shall produce a replayable build
  record for every Factory Image candidate.
- Parent system requirement: [Reproducible factory image (`SYS-MFG-001`)](../system-requirements-and-traceability.md#sys-mfg-001)
- Architecture flow: [Factory-image and overlay creation (`AF-M0-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-m0-lc)
- Components: [Factory Assembly (`CMP-FACTORY`)](../component-decomposition-and-interface-register.md#cmp-factory)
- Required evidence: validated source lock, build manifest, tool versions and output manifest
- Requirement state: D3 design-reviewed
- Implementation state: `PARTIAL`; `.11` has a source lock and one accepted output digest, while independent rebuild equivalence is not yet accepted

Acceptance rejects an ambient branch, uncommitted build input, mutable external
download, personal absolute path in release metadata or a candidate whose
record cannot identify every effective integration input.

### Distinct build artifacts

<a id="req-factory-002"></a>

- ID: `REQ-FACTORY-002`
- Statement: The assembly and release metadata shall identify the complete OEM
  Demo Factory Image, any optional rootfs platform-update envelope and every
  independently delivered Vehicle Data Platform Component as different
  artifact types with separate versions, digests, target runtimes and lifecycle
  purpose.
- Parent system requirements: [Reproducible factory image (`SYS-MFG-001`)](../system-requirements-and-traceability.md#sys-mfg-001) and [clean SOP substrate (`SYS-MFG-002`)](../system-requirements-and-traceability.md#sys-mfg-002)
- Architecture flow: [Factory-image and overlay creation (`AF-M0-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-m0-lc)
- Components: [Factory Assembly (`CMP-FACTORY`)](../component-decomposition-and-interface-register.md#cmp-factory) and [Empty-Slot Runtime (`CMP-RUNTIME`)](../component-decomposition-and-interface-register.md#cmp-runtime)
- Interfaces: [Cloud-to-Unit lifecycle (`IF-LC-004`)](../component-decomposition-and-interface-register.md#if-lc-004) and [runtime enforcement (`IF-LC-006`)](../component-decomposition-and-interface-register.md#if-lc-006)
- Required evidence: machine-readable artifact manifest and negative cross-type installation tests
- Requirement state: D3 design-reviewed
- Implementation state: `PARTIAL`; the bytes and component types exist, while one normative factory artifact manifest is not yet accepted

Acceptance requires the rootfs envelope to target the factory-installed rootfs
A/B runtime and the Vehicle Data Platform Component to target only the
provider-specific runtime. Neither may be labelled as the Factory Image.

### Clean SOP substrate

<a id="req-factory-003"></a>

- ID: `REQ-FACTORY-003`
- Statement: The Factory Image shall contain AosCore, KUKSA, security/update
  support, enabled stock IAM permission handling, a non-secret IAM/PKCS#11
  integration seam and the provider-specific empty-slot runtime but no active
  provider payload, functional service, Cloud registration, provisioned
  identity, signing key, static token, reusable credential or vehicle-specific
  mutable state.
- Parent system requirement: [Clean SOP substrate (`SYS-MFG-002`)](../system-requirements-and-traceability.md#sys-mfg-002)
- Architecture flows: [Factory-image and overlay creation (`AF-M0-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-m0-lc) and [Manufacturing evidence (`AF-M0-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-m0-ob)
- Components: [Factory Assembly (`CMP-FACTORY`)](../component-decomposition-and-interface-register.md#cmp-factory), [AosCore (`CMP-AOS-CORE`)](../component-decomposition-and-interface-register.md#cmp-aos-core), [KUKSA (`CMP-KUKSA`)](../component-decomposition-and-interface-register.md#cmp-kuksa) and [Empty-Slot Runtime (`CMP-RUNTIME`)](../component-decomposition-and-interface-register.md#cmp-runtime)
- Required evidence: image-content manifest, forbidden-content scan and clean guest-state qualification
- Requirement state: D3 design-reviewed
- Implementation state: `EVIDENCE`; the `.11` disposable bootstrap gate proved the intended absence set and must be repeated on the accepted Factory Image

### Immutable bootable Factory Image

<a id="req-factory-004"></a>

- ID: `REQ-FACTORY-004`
- Statement: The accepted Factory Image shall be a complete bootable,
  unprovisioned artifact frozen read-only with size and cryptographic digest;
  every M0 overlay shall reference that exact verified base without writing to
  it.
- Parent system requirements: [Reproducible factory image (`SYS-MFG-001`)](../system-requirements-and-traceability.md#sys-mfg-001) and [preserve immutable factory artifact (`SYS-RET-005`)](../system-requirements-and-traceability.md#sys-ret-005)
- Architecture flows: [Factory-image and overlay creation (`AF-M0-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-m0-lc) and [Retirement evidence (`AF-R0-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-r0-ob)
- Components: [Factory Assembly (`CMP-FACTORY`)](../component-decomposition-and-interface-register.md#cmp-factory)
- Interface: [Orchestrated VM lifecycle (`IF-DEMO-001`)](../component-decomposition-and-interface-register.md#if-demo-001)
- Required evidence: raw-image format, partition/boot proof, size, digest, read-only state and qcow2 backing-chain validation
- Requirement state: D3 design-reviewed
- Implementation state: `EVIDENCE`; `.11` provides a matching full raw image but has not completed factory acceptance

### Healthy provider-specific empty slot

<a id="req-factory-005"></a>

- ID: `REQ-FACTORY-005`
- Statement: At clean G0 the Service Manager shall report exactly the accepted
  provider component type and one bounded runtime instance while the provider
  service remains inactive, no payload or active link exists and the health
  adapter reports the defined empty state without presenting a fault as an
  installed capability.
- Parent system requirements: [Clean SOP substrate (`SYS-MFG-002`)](../system-requirements-and-traceability.md#sys-mfg-002) and [healthy empty capability slot (`SYS-VDP-001`)](../system-requirements-and-traceability.md#sys-vdp-001)
- Architecture flow: [Working vehicle, empty feature graph (`AF-G0-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g0-rt)
- Components: [Empty-Slot Runtime (`CMP-RUNTIME`)](../component-decomposition-and-interface-register.md#cmp-runtime)
- Interface: [Runtime enforcement (`IF-LC-006`)](../component-decomposition-and-interface-register.md#if-lc-006)
- Required evidence: runtime inventory, empty filesystem/state checks, inactive systemd state and health result
- Requirement state: D3 design-reviewed
- Implementation state: `CURRENT / QUALIFY`

### Atomic component lifecycle

<a id="req-factory-006"></a>

- ID: `REQ-FACTORY-006`
- Statement: The provider-specific runtime shall validate an accepted component
  artifact before activation, install it into the inactive A/B slot, switch
  atomically, preserve the previous accepted release until commit and recover
  deterministically from interruption, failed health, repeated digest,
  downgrade and rollback conditions.
- Parent system requirements: [Healthy empty capability slot (`SYS-VDP-001`)](../system-requirements-and-traceability.md#sys-vdp-001), [immutable release candidates (`SYS-REL-001`)](../system-requirements-and-traceability.md#sys-rel-001) and [dependent-first rollback (`SYS-REL-005`)](../system-requirements-and-traceability.md#sys-rel-005)
- Architecture flow: [G1 platform component lifecycle](../../architecture/demo-scenario-architecture-flows.md#af-g1-lc)
- Components: [Empty-Slot Runtime (`CMP-RUNTIME`)](../component-decomposition-and-interface-register.md#cmp-runtime)
- Interface: [Runtime enforcement (`IF-LC-006`)](../component-decomposition-and-interface-register.md#if-lc-006)
- Required evidence: blocking runtime C++ suite plus disposable guest apply/revert/recovery qualification
- Requirement state: D3 design-reviewed
- Implementation state: `CURRENT / QUALIFY`; the implementation and test sources exist, while final Factory Image evidence remains open

### Bounded security and storage

<a id="req-factory-007"></a>

- ID: `REQ-FACTORY-007`
- Statement: The runtime shall execute provider payloads under the fixed
  non-login platform identity, empty Linux capability set, accepted SELinux
  domain, bounded credential interface and bounded persistent store, and shall
  fail closed when identity, mount, label, capacity, payload layout or policy is
  unexpected.
- Parent system requirements: [Clean SOP substrate (`SYS-MFG-002`)](../system-requirements-and-traceability.md#sys-mfg-002) and [healthy empty capability slot (`SYS-VDP-001`)](../system-requirements-and-traceability.md#sys-vdp-001)
- Architecture flow: [G0 failure boundaries (`AF-G0-FR`)](../../architecture/demo-scenario-architecture-flows.md#af-g0-fr)
- Components: [Empty-Slot Runtime (`CMP-RUNTIME`)](../component-decomposition-and-interface-register.md#cmp-runtime)
- Interface: [Runtime enforcement (`IF-LC-006`)](../component-decomposition-and-interface-register.md#if-lc-006)
- Required evidence: source gate, policy build, guest identity/capability/SELinux checks and negative store qualification
- Requirement state: D3 design-reviewed
- Implementation state: `CURRENT / QUALIFY`; the 512 MiB nested ext4 store is accepted only as a demonstration backend

### Identity-safe fresh deployments

<a id="req-factory-008"></a>

- ID: `REQ-FACTORY-008`
- Statement: Two fresh copy-on-write deployments created from one Factory
  Image shall contain no inherited provisioned identity, shall establish
  distinct local machine, SSH and network identity before provisioning and
  shall be eligible for exactly one distinct Unit/Main Node identity each.
- Parent system requirements: [Unique fresh overlays (`SYS-MFG-003`)](../system-requirements-and-traceability.md#sys-mfg-003), [one identity per overlay (`SYS-ID-001`)](../system-requirements-and-traceability.md#sys-id-001) and [reconcile partial provisioning (`SYS-ID-002`)](../system-requirements-and-traceability.md#sys-id-002)
- Architecture flows: [Factory-image and overlay creation (`AF-M0-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-m0-lc) and [Manufacturing evidence (`AF-M0-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-m0-ob)
- Components: [Factory Assembly (`CMP-FACTORY`)](../component-decomposition-and-interface-register.md#cmp-factory), jointly with `CR-AOS` and `CR-DEMO`
- Interface: [Orchestrated VM lifecycle (`IF-DEMO-001`)](../component-decomposition-and-interface-register.md#if-demo-001)
- Required evidence: redacted two-overlay identity comparison, no provisioning material before M1 and later distinct Cloud Unit/Node evidence
- Requirement state: D3 design-reviewed
- Implementation state: `TARGET`; existing provisioned `.1/.2` overlays are not valid proof for this requirement

### Pre-provision runtime availability

<a id="req-factory-009"></a>

- ID: `REQ-FACTORY-009`
- Statement: Every fresh Validation and Demonstration deployment shall contain
  the accepted empty-slot runtime before M1 provisioning; the normal M0-M1 flow
  shall not use rootfs FOTA to introduce that initial runtime.
- Parent system requirements: [Clean SOP substrate (`SYS-MFG-002`)](../system-requirements-and-traceability.md#sys-mfg-002) and [healthy empty capability slot (`SYS-VDP-001`)](../system-requirements-and-traceability.md#sys-vdp-001)
- Architecture flows: [Factory-image and overlay creation (`AF-M0-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-m0-lc) and [Working vehicle, empty feature graph (`AF-G0-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g0-rt)
- Components: [Factory Assembly (`CMP-FACTORY`)](../component-decomposition-and-interface-register.md#cmp-factory) and [Empty-Slot Runtime (`CMP-RUNTIME`)](../component-decomposition-and-interface-register.md#cmp-runtime)
- Required evidence: M0 image manifest, pre-provision runtime inventory and absence of a rootfs-update action in M0-M1 evidence
- Requirement state: D3 design-reviewed
- Implementation state: `TARGET acceptance`; `.11` proves the intended content, while the final Factory Image has not been accepted

A later post-SOP rootfs FOTA remains permitted for a platform/runtime fix or
retrofit. Such an update is a separate Platform Team lifecycle and must not be
presented as installation of the Vehicle Data Platform Component.

### Factory artifact preservation

<a id="req-factory-010"></a>

- ID: `REQ-FACTORY-010`
- Statement: R0 shall retire and discard only run-specific provisioned
  deployments and shall verify that the same accepted Factory Image size,
  digest and read-only base remain available for the next M0 run.
- Parent system requirement: [Preserve immutable factory artifact (`SYS-RET-005`)](../system-requirements-and-traceability.md#sys-ret-005)
- Architecture flows: [Controlled retirement (`AF-R0-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-r0-lc) and [Retirement evidence (`AF-R0-OB`)](../../architecture/demo-scenario-architecture-flows.md#af-r0-ob)
- Components: [Factory Assembly (`CMP-FACTORY`)](../component-decomposition-and-interface-register.md#cmp-factory), jointly with `CR-DEMO`
- Interface: [Orchestrated VM lifecycle (`IF-DEMO-001`)](../component-decomposition-and-interface-register.md#if-demo-001)
- Required evidence: pre/post-reset base digest, exact retired-overlay inventory and next-run overlay backing-chain proof
- Requirement state: D3 design-reviewed
- Implementation state: `TARGET`

### Native IAM credential substrate

<a id="req-factory-011"></a>

- ID: `REQ-FACTORY-011`
- Statement: Before provisioning, the Factory Image shall enable the stock Aos
  IAM permission handler used by Service Manager for per-instance service
  secrets and shall contain the accepted non-secret IAM/certificate-module and
  PKCS#11 integration required for broker signing operations. It shall not
  contain a broker signing key, static provider/service token, project-owned
  service-secret database or a fallback file-key path.
- Parent system requirements: [Clean SOP substrate (`SYS-MFG-002`)](../system-requirements-and-traceability.md#sys-mfg-002), [KUKSA verifier and token lifetime (`SYS-SEC-004`)](../system-requirements-and-traceability.md#sys-sec-004), and [native-IAM-derived SOTA KUKSA credentials (`SYS-SEC-006`)](../system-requirements-and-traceability.md#sys-sec-006)
- Architecture flows: [Factory-image and overlay creation (`AF-M0-LC`)](../../architecture/demo-scenario-architecture-flows.md#af-m0-lc), [working vehicle, empty feature graph (`AF-G0-RT`)](../../architecture/demo-scenario-architecture-flows.md#af-g0-rt), and [cross-cutting credential flow (`AF-X-AUTH`)](../../architecture/demo-scenario-architecture-flows.md#af-x-auth)
- Components: [Factory Assembly (`CMP-FACTORY`)](../component-decomposition-and-interface-register.md#cmp-factory) and [AosCore (`CMP-AOS-CORE`)](../component-decomposition-and-interface-register.md#cmp-aos-core)
- Interface: [Broker IAM/PKCS#11 substrate (`IF-AUTH-005`)](../component-decomposition-and-interface-register.md#if-auth-005)
- Required evidence: effective IAM configuration, boot/readiness proof,
  permission-handler positive/negative contract test, PKCS#11 module discovery,
  protected-sign operation using a disposable per-Unit test key, and forbidden
  key/token/content scan
- Requirement state: D3 design-reviewed
- Implementation state: `GAP / PARTIAL`; the stock handler and generic key
  facilities exist in AosCore, but the live demo IAM configuration does not
  enable the handler and no accepted broker signing-key binding is configured

This requirement qualifies native platform facilities; it does not authorize
the Factory package to mint service identities or to own the broker's runtime
translation rules. Per-Unit signing material is created only after a fresh
deployment exists and must be retired with that deployment.

## Unit-Test Obligations

| Unit-test obligation | Requirements proved | Behavior and branches | Isolation / doubles | Required assertions | Repository / suite | State |
| --- | --- | --- | --- | --- | --- | --- |
| <a id="ut-factory-001"></a>`UT-FACTORY-001` — Source-lock validation | [`REQ-FACTORY-001`](#req-factory-001) | Exact pins, dirty/missing/wrong inputs, unsafe paths and manifest mismatch | Temporary repositories and build-manifest fixtures | Only the complete accepted lock passes; no ambient input is silently accepted | `aosedge-sdv-demo` manifest/build validators | D3 design-reviewed |
| <a id="ut-factory-002"></a>`UT-FACTORY-002` — Artifact-type separation | [`REQ-FACTORY-002`](#req-factory-002), [`REQ-FACTORY-004`](#req-factory-004) | Factory raw image, rootfs envelope and provider component positive/negative type combinations | Synthetic release metadata and small image fixtures | Wrong target runtime/type/digest or cross-type label is rejected | `aosedge-sdv-demo` release validators | D3 design-reviewed |
| <a id="ut-factory-003"></a>`UT-FACTORY-003` — Clean-content policy | [`REQ-FACTORY-003`](#req-factory-003) | Allowed platform files and forbidden identity, credential, provider and service content | Synthetic filesystem manifests | Every forbidden class fails without printing content; accepted empty graph passes | `aosedge-sdv-demo` factory image validator | D3 design-reviewed |
| <a id="ut-factory-004"></a>`UT-FACTORY-004` — Empty runtime contract | [`REQ-FACTORY-005`](#req-factory-005), [`REQ-FACTORY-009`](#req-factory-009) | Exact runtime type/count/configuration; empty, malformed and unexpected active states | Service Manager configuration and state fixtures | One accepted empty runtime passes; duplicate/generic/wrong type or active payload fails | `aos-vehicle-platform` layer tests | D3 design-reviewed |
| <a id="ut-factory-005"></a>`UT-FACTORY-005` — Atomic A/B lifecycle | [`REQ-FACTORY-006`](#req-factory-006) | First install, A-to-B update, idempotence, interruption, unsafe archive, downgrade, digest mismatch, stop and recovery | Filesystem sandbox, fake profile/health and archive fixtures | Previous accepted slot remains recoverable; unsafe candidate never becomes active | `systemdslotcomponent_test` C++ suite | D3 design-reviewed |
| <a id="ut-factory-006"></a>`UT-FACTORY-006` — Security/store source gate | [`REQ-FACTORY-007`](#req-factory-007) | Identity, capabilities, systemd, SELinux, store size/mount/path and fail-closed rules | Recipe, policy and configuration fixtures | Missing or weakened boundary blocks the normal repository gate | `aos-vehicle-platform` `test_r6_1_layer.py` | D3 design-reviewed |
| <a id="ut-factory-007"></a>`UT-FACTORY-007` — Fresh-overlay guard | [`REQ-FACTORY-008`](#req-factory-008) | New overlay, reused/provisioned/locked overlay, wrong backing file and duplicate redacted identity | Temporary qcow2 metadata and identity-digest fixtures | Only a fresh overlay backed by the accepted digest is eligible for M1 | `aosedge-sdv-demo` lifecycle tests | D3 design-reviewed |
| <a id="ut-factory-008"></a>`UT-FACTORY-008` — Immutable reset guard | [`REQ-FACTORY-010`](#req-factory-010) | Exact run overlays, missing reconciliation, unexpected target and changed base digest | Temporary lifecycle manifest and fake image metadata | Reset never targets the base and fails on unresolved identity or changed digest | `aosedge-sdv-demo` lifecycle tests | D3 design-reviewed |
| <a id="ut-factory-009"></a>`UT-FACTORY-009` — IAM substrate configuration | [`REQ-FACTORY-003`](#req-factory-003), [`REQ-FACTORY-011`](#req-factory-011) | Permission handler enabled/disabled/absent, accepted PKCS#11 module references, forbidden file-key fallback and key/token content | IAM and certificate-module configuration fixtures plus filesystem manifests | Only the enabled native handler and non-secret protected-key seam pass; any baked key/token or fallback file path fails without printing content | `aos-vehicle-platform` layer and image-policy tests | D3 design-reviewed |

All runtime C++ cases required by `UT-FACTORY-005` shall be executed as a
blocking build/qualification gate. Merely compiling those tests into the Yocto
build tree is not acceptance evidence.

## Verification Traceability

| Requirement | Unit obligations | Component proof | Contract proof | Integration proof | End-to-end proof |
| --- | --- | --- | --- | --- | --- |
| [`REQ-FACTORY-001`](#req-factory-001) | [`UT-FACTORY-001`](#ut-factory-001) | Build output manifest | Source-lock schema | Rebuild/equivalence gate | N/A; build-time property |
| [`REQ-FACTORY-002`](#req-factory-002) | [`UT-FACTORY-002`](#ut-factory-002) | Three artifact inspections | Runtime/type compatibility | Negative cross-install proof | M0/G1 lifecycle labels |
| [`REQ-FACTORY-003`](#req-factory-003) | [`UT-FACTORY-003`](#ut-factory-003) | Guest content gate | Forbidden-content policy | Clean unprovisioned boot | M0/G0 absence evidence |
| [`REQ-FACTORY-004`](#req-factory-004) | [`UT-FACTORY-002`](#ut-factory-002) | Full-image boot | Factory manifest | Verified qcow2 backing chain | M0 and R0 digest |
| [`REQ-FACTORY-005`](#req-factory-005) | [`UT-FACTORY-004`](#ut-factory-004) | Runtime/health gate | Exact component type | Disposable empty-slot boot | G0 inventory |
| [`REQ-FACTORY-006`](#req-factory-006) | [`UT-FACTORY-005`](#ut-factory-005) | Runtime suite | Component metadata/archive | Apply/revert/recovery | Validation then Demonstration evidence |
| [`REQ-FACTORY-007`](#req-factory-007) | [`UT-FACTORY-006`](#ut-factory-006) | Policy/image gate | Security/store contract | Guest negative qualification | G0/G1 health evidence |
| [`REQ-FACTORY-008`](#req-factory-008) | [`UT-FACTORY-007`](#ut-factory-007) | N/A; cross-deployment property | Overlay handoff contract | Two fresh overlays/identities | M0-M1 VU/DU evidence |
| [`REQ-FACTORY-009`](#req-factory-009) | [`UT-FACTORY-004`](#ut-factory-004) | Pre-provision inventory | Manufacturing stage contract | Fresh image boot | No M0-M1 rootfs update |
| [`REQ-FACTORY-010`](#req-factory-010) | [`UT-FACTORY-008`](#ut-factory-008) | Base metadata gate | Retirement contract | Overlay-only discard proof | R0 then next M0 |
| [`REQ-FACTORY-011`](#req-factory-011) | [`UT-FACTORY-009`](#ut-factory-009) | Effective IAM and module configuration | `IF-AUTH-005` conformance | Disposable protected-key and service-secret lifecycle qualification | G0 security-readiness evidence |

## Cross-Cutting Constraints

| Concern | Applicable obligation | Component response | Verification |
| --- | --- | --- | --- |
| Security and least privilege | [`REQ-FACTORY-003`](#req-factory-003), [`REQ-FACTORY-007`](#req-factory-007), [`REQ-FACTORY-011`](#req-factory-011) | No reusable identity/key; enabled native IAM permission lifecycle; fixed non-root runtime and fail-closed policy | Source, component and guest gates |
| Privacy and redaction | [`REQ-FACTORY-008`](#req-factory-008) | Compare identity uniqueness without retaining or printing secret values | Redacted integration evidence |
| Resource bounds | [`REQ-FACTORY-007`](#req-factory-007) | Fixed payload/free-space limits and bounded demo store | Runtime and store negative tests |
| Timing | [`REQ-FACTORY-006`](#req-factory-006) | Bounded start/stop/health operations | D4 runtime timing cases |
| Offline and recovery | [`REQ-FACTORY-006`](#req-factory-006), [`REQ-FACTORY-010`](#req-factory-010) | Persistent A/B recovery and immutable reset source | Unit, integration and R0 proof |
| Observability | [`REQ-FACTORY-002`](#req-factory-002), [`REQ-FACTORY-004`](#req-factory-004) | Factual artifact type, version, digest and runtime inventory | Factory manifest and Software Delivery Dashboard |

## Open Issues

| Issue | Impact | Owner | Decision gate |
| --- | --- | --- | --- |
| Define whether reproducibility requires byte-identical full raw output or accepted filesystem/partition equivalence under a pinned build | Final acceptance criteria for `REQ-FACTORY-001` | Platform Team / System Architecture | D4 before the final factory build |
| Decide whether the existing `.11` full raw image can pass Factory Image acceptance unchanged or a newly versioned candidate is required | Build time and final artifact version | Platform Team | After no-build content, identity and runtime gates |
| Production provider-store backend remains undecided | No impact on demo acceptance if nested ext4 remains explicitly demo-only | OEM platform architecture | Outside current demo |

## D3 Review Closure and Product Acceptance

The artifact/lifecycle model, eleven requirement obligations, interface
ownership, verification levels and stable `UT-FACTORY-*` obligations were
design-reviewed on 2026-08-19 and are accepted as input to D4. This closes the
`CR-FACTORY` D3 package. The recorded `CURRENT`, `EVIDENCE`, `PARTIAL`, `GAP`
and `TARGET` labels remain authoritative and prevent design review from being
misread as implementation or image acceptance.

Product acceptance remains open until D4 defines measurable cases, the
effective Factory Image contents and current implementation states are
qualified, and no provisioned `.1` or `.2` image is presented as a
manufacturing source. This closure does not authorize a Yocto build, signing,
Cloud upload, VM restart, provisioning or Unit mutation.
