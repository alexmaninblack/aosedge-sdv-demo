<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Automotive Orchestration Coverage Matrix

Version: **0.1 — review draft**

Status: **sanitized derivative; dashboard input; no implementation authorized**

## Purpose

This matrix translates a confidential OEM assessment of general-purpose
container orchestration in an automotive environment into customer-neutral
demo proof obligations. It is the requirements and evidence catalogue for the
Software Delivery Dashboard; it is not a claim that every concern is already
closed.

The confidential source workbook is deliberately absent from this repository.
This document contains no source attachment, customer identity, direct quote,
or customer-specific internal detail. Only reviewed paraphrases and our own
acceptance criteria are allowed in Git.

`Current status` describes evidence available in this demo repository today;
it does not reproduce or adopt the historical coverage ratings from the
confidential assessment.

## Dashboard interpretation

Each row becomes a dashboard evidence card. A card must show:

- the automotive concern in neutral language;
- the relevant `G0–G4` demo stages;
- the proof mode: live demonstration, controlled qualification, documentary
  evidence, or explicit scope boundary;
- current coverage without turning `PARTIAL` or `PLANNED` into success;
- audience-visible evidence and its original timestamp;
- a concise claim boundary explaining what the demo does not prove.

The machine-readable input is
[`contracts/software-delivery-dashboard/coverage-matrix.v1.json`](../../../contracts/software-delivery-dashboard/coverage-matrix.v1.json).

## Status vocabulary

| Status | Meaning |
| --- | --- |
| `PARTIAL` | Reusable evidence exists, but the complete dashboard proof or end-to-end capability is not accepted. |
| `PLANNED` | The demo or qualification work is defined but no accepted proof exists yet. |
| `DOCUMENTARY_ONLY` | The concern cannot be proven by a short live demo and requires policy, compatibility, or support evidence. |

## Coverage matrix

| ID | Automotive concern | Demo stages | Proof mode | Software Delivery Dashboard evidence | Current status |
| --- | --- | --- | --- | --- | --- |
| AO-01 | Deterministic software lifecycle with explicit download, install, activation, stop, update, and single-active-instance state | G1–G4 | Live + qualification | Artifact and Unit state timeline, active instance count, transition duration, failure reason | PARTIAL |
| AO-02 | Per-service persistent storage with declared ownership, quota, isolation, update survival, and removal policy | G2–G4 | Qualification | Storage declaration, owner, quota, persistence test, cross-service denial result | PLANNED |
| AO-03 | Predictable recovery after ignition-like power loss, restart, and interrupted update without identity or accepted state loss | G0, G2–G4 | Live + qualification | Before/after desired state, restart recovery result, state checksum, Unit identity continuity | PARTIAL |
| AO-04 | Bounded platform and service startup/readiness suitable for an automotive boot sequence | G0–G2 | Qualification | Boot-to-platform-ready and service-ready timings with accepted threshold and sample count | PARTIAL |
| AO-05 | Artifact authenticity and integrity verification before activation | G1–G3 | Live + qualification | Signer/trust policy, immutable digest, verification verdict, rejected-tamper evidence | PARTIAL |
| AO-06 | Explicit CPU, memory, storage, and network budgets with observed use against limits | G0–G4 | Live + qualification | Requested limits, measured peak/steady state, threshold result, resource-related restart count | PARTIAL |
| AO-07 | Efficient fleet delivery, including measured payload and transfer savings for an update | G1–G3 | Qualification | Full artifact size, bytes transferred, cache/reuse result, measured saving; no unproven “delta” label | PLANNED |
| AO-08 | Dependency-aware installation and activation across platform FOTA capabilities and SOTA services | G1–G4 | Live + qualification | Desired-state graph, dependency constraint, required/actual version, native Cloud rejection, zero Unit transfer, activation order, readiness result | PLANNED — blocked on roadmap release |
| AO-09 | Defined long-term support, vulnerability response, and maintenance ownership | Cross-stage | Documentary | Version support record, maintenance owner, support window, unresolved policy gaps | DOCUMENTARY_ONLY |
| AO-10 | Versioned and backward-compatible APIs between vehicle platform capabilities and post-SOP services | G1–G3 | Qualification + documentary | Contract version, compatibility range, consumer/provider test result, migration note | PLANNED |
| AO-11 | Trusted, immutable artifact sources without reliance on mutable tags or uncontrolled public registries | G1–G3 | Qualification | Registry/source policy, digest-pinned identity, provenance result, mutable-tag rejection | PLANNED |
| AO-12 | Visibility of transitive dependencies, software bill of materials, and known vulnerability findings | G1–G3 | Qualification | SBOM identity, scanner timestamp, severity counts, policy verdict, exception owner | PLANNED |
| AO-13 | Least-privilege device and vehicle-interface access without broad host privilege | G0–G2, G4 | Qualification | Linux capabilities, device/interface allowlist, SELinux result, denied-access evidence | PARTIAL |
| AO-14 | Safe vehicle/cohort targeting with a guard against intended-versus-effective recipient mismatch | G1–G4 | Live + qualification | Intended Unit Set, effective pending recipients, mismatch banner, promotion block/decision | PARTIAL |
| AO-15 | Continued local function during connectivity loss plus bounded reconnect, queue, and replay behavior | G2–G4 | Live + qualification | Connectivity state, local-service health, buffered sample count, replay result, data age | PARTIAL |
| AO-16 | Bounded idle CPU, memory, network activity, and battery-impact proxy | G0–G1 | Qualification | Idle resource baseline, observation window, wakeups/traffic proxy, accepted threshold | PLANNED |
| AO-17 | Detection and safe handling of unhealthy OS, driver, runtime, or dependency state | G0–G4 | Qualification | Layered health status, injected failure, containment result, recovery action and duration | PARTIAL |
| AO-18 | Coordinated release view spanning base system/FOTA capabilities and SOTA services, with firmware scope stated separately | G1, G3 | Live + documentary | Release graph across rootfs, platform components, and services; firmware boundary and owner | PARTIAL |
| AO-19 | Per-vehicle identity, certificate lifecycle, secret isolation, and key-rotation readiness | G0–G4 | Qualification + documentary | Identity continuity, certificate health, secret-exclusion result, rotation generation, hardware-root status | PARTIAL |
| AO-20 | Integrated operational workflow that avoids presenting a collection of unrelated tools as one platform capability | Cross-stage | Live + documentary | One release/evidence timeline, capability ownership map, external dependency inventory | PARTIAL |
| AO-21 | Measured end-to-end local event latency and serialization/network-hop cost | G4 | Live + qualification | Event timestamps from VISS input through KUKSA to local advisory, percentile latency, Cloud independence | PLANNED |

## Demo alignment

The five accepted stages provide the narrative spine rather than twenty-one
separate demos:

1. **G0 — integrated post-SOP platform baseline:** establishes identity,
   startup, resource, health, and idle baselines before a demo provider or
   service is desired.
2. **G1 — platform data capability:** shows signed FOTA delivery, targeting,
   dependency and activation evidence for the initial Vehicle Data Provider.
3. **G2 — first functional service:** shows independent SOTA delivery,
   least-privilege data access, service storage, resource limits, and
   operational logs.
4. **G3 — independent capability evolution:** shows contract and dependency
   evolution, efficient transfer evidence, validation, and promotion.
5. **G4 — local Brake Health intelligence:** shows edge processing, offline
   continuity, bounded local latency, and bidirectional advisory evidence.

The dashboard should support a **coverage view** across all rows and a
**release view** that shows only the evidence relevant to the current G-stage.

## Claim boundaries

- The matrix records OEM automotive fit concerns; it is not a universal
  statement that a Kubernetes distribution can never address them. Ecosystem
  components may address some concerns at additional integration and
  maintenance cost.
- Local processing still has IPC, serialization, and network-hop cost. The
  accepted claim is measured bounded latency without a Cloud round trip, not
  zero overhead.
- A QEMU demo cannot prove hardware TPM behavior, real ECU firmware update, or
  physical battery consumption. Those remain documentary or hardware-lab
  evidence.
- Install state is not readiness. Application health and qualification
  evidence remain separate fields.
- Long-term support and API lifecycle are governance commitments, not visual
  effects that a short live demonstration can prove.

## Review exit

Before this becomes version 1.0:

1. confirm the twenty-one neutral concern statements;
2. accept the status and proof mode of every row;
3. select the minimum evidence cards for the first dashboard increment;
4. assign each acceptance criterion to an owner and an evidence source;
5. verify again that no confidential source wording or customer identity is
   present.
