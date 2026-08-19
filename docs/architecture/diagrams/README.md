<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Architecture Diagrams

Store accepted, editable architecture sources here together with their
reviewable SVG or PNG exports. Use stable names and keep the version and status
in the owning architecture document.

The accepted HLA 1.3 architecture baseline is maintained as Mermaid source
inside [`high-level-architecture.md`](../high-level-architecture.md).

The editable visual model is the primary visual architecture source:

- [`aosedge-demo-hla-authoring-reference.drawio`](aosedge-demo-hla-authoring-reference.drawio) — editable Draw.io source;
- [`aosedge-demo-hla-authoring-reference.png`](aosedge-demo-hla-authoring-reference.png) — matching review export.

The Draw.io file is authoritative for diagram layout and visual relationships;
the PNG must be regenerated from it after every accepted visual change. The
accepted HLA 1.3 baseline reflects two peer OEM Service Providers, independent
SOTA lifecycles, the shared FOTA-owned Vehicle Data Platform Component, the
Tire Health service, the Factory Baseline Assembly-to-Factory Image and
factory-installed runtime boundaries, the Software Delivery Dashboard's
AosCloud lifecycle and native-log views, and the KUKSA-mediated advisory
return. It keeps Eclipse KUKSA unchanged and shows the thin Aos–KUKSA
Credential Broker translating native Aos IAM permissions inside the FOTA-owned
Vehicle Data Platform Component, with IAM/PKCS#11 support in the Factory
substrate and no duplicate per-service policy store.
It also distinguishes Service Provider artifact publication, team-owned
engineering release decisions, OEM-authorized deployment approval, and
AosCloud lifecycle state/execution as defined by ADR 0009.
The credential boundary follows ADR 0010.
Both files are original project material, copyright 2026 maninblack, and
distributed under the repository MIT license.

Customer or partner presentation screenshots and other external reference
images are not architecture baselines and must not be copied into this public
directory.
