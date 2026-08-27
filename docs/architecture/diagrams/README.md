<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Architecture Diagrams

Store accepted, editable architecture sources here together with their
reviewable SVG or PNG exports. Use stable names and keep the version and status
in the owning architecture document.

The accepted HLA 1.5 architecture is maintained as Mermaid source inside
[`high-level-architecture.md`](../high-level-architecture.md), with the Draw.io
source below as the primary visual-authoring artifact.

The editable visual model is the primary visual architecture source:

- [`aosedge-demo-hla-authoring-reference.drawio`](aosedge-demo-hla-authoring-reference.drawio) — editable Draw.io source;
- [`aosedge-demo-hla-authoring-reference.png`](aosedge-demo-hla-authoring-reference.png) — matching review export.

The Draw.io file is authoritative for diagram layout and visual relationships;
the PNG must be regenerated from it after every accepted visual change. The
accepted HLA 1.5 visual reflects two peer OEM Service Providers, independent
SOTA lifecycles, the shared FOTA-owned Vehicle Data Platform Component, the
Tire Health service, the Factory Baseline Assembly-to-Factory Image and
factory-installed runtime boundaries, the Software Delivery Dashboard's
AosCloud lifecycle and native-log views, and the KUKSA-mediated advisory
return. It keeps Eclipse KUKSA unchanged and factory-installed outside the VDP
FOTA payload. It shows an implementation-neutral platform Service-credential
boundary and a visually subordinate current-release overlay: a removable
helper outside the VDP and both SOTA artifacts that translates active native
Aos IAM permissions into Service-private short-lived JWTs without a duplicate
per-Service policy store.
It also distinguishes Service Provider artifact publication, producer-owned
engineering acceptance, independent OEM Release Authority authorization, and
AosCloud lifecycle state/execution as defined by ADR 0009. The accepted
credential correction follows ADR 0013 and supersedes ADR 0010. QM-service
containment and evidence-backed Release Authority authorization follow ADR
0011, while OEM-runtime Platform FOTA Safe Stop enforcement follows ADR 0014.
Both files are original project material, copyright 2026 maninblack, and
distributed under the repository MIT license.

Customer or partner presentation screenshots and other external reference
images are not architecture baselines and must not be copied into this public
directory.
