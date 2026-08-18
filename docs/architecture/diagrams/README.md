<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Architecture Diagrams

Store accepted, editable architecture sources here together with their
reviewable SVG or PNG exports. Use stable names and keep the version and status
in the owning architecture document.

The HLA 1.2 review candidate is maintained as Mermaid source inside
[`high-level-architecture.md`](../high-level-architecture.md). HLA 1.0 remains
the previous accepted checkpoint until the 1.1 review is complete.

The editable visual model is the primary visual architecture source:

- [`aosedge-demo-hla-authoring-reference.drawio`](aosedge-demo-hla-authoring-reference.drawio) — editable Draw.io source;
- [`aosedge-demo-hla-authoring-reference.png`](aosedge-demo-hla-authoring-reference.png) — matching review export.

The Draw.io file is authoritative for diagram layout and visual relationships;
the PNG must be regenerated from it after every accepted visual change. The
HLA 1.2 review candidate reflects two peer OEM Service Providers, independent
SOTA lifecycles, the shared FOTA-owned Vehicle Data Platform Capability, the
Tire Health service, the Factory Baseline Assembly-to-Factory Image and
factory-installed runtime boundaries, the Software Delivery and ELK
observation surfaces, and the KUKSA-mediated advisory return.
Both files are original project material, copyright 2026 maninblack, and
distributed under the repository MIT license.

Customer or partner presentation screenshots and other external reference
images are not architecture baselines and must not be copied into this public
directory.
