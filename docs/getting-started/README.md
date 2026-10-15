<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Getting started

Choose a route by what you want to do. You do not need the project's history,
old kit numbers or sibling repositories to choose a route.

1. **Run:** [Install and connect Cloud access](installed-preview-cloud-first-use.md).
   Use one matching DMG, with no compiler or Unreal Editor.
2. **Build:** [Developer build](reproduce-demo.md). Build project components
   and the installer, reusing the prebuilt CARLA simulator and ARM64 virtual
   controller image (**Factory image**, the clean Linux/AosEdge base).
3. **Prepare tools to rebuild the controller image or simulator:**
   [Specialist preparation and full-source scope](full-source-build.md).
   This prepares compatible host tools, not a complete build. Source/Builder
   prerequisites and full-source qualification remain separate.

All routes start with the [single launcher in README](../../README.md#start-here)
and its menu. [Release selection and access](release-status.md) explains the
matching inputs. Developers do not clone manually first: route B prepares tools,
checks capacity, selects sources and builds automatically. The
[launcher reference](unified-macos-launcher.md) explains handoff, repeats and the
explicit partial specialist route. The [current release evidence](release-status.md)
separates offline fixture coverage, actual M1 checks and remaining gates.
For the system overview, use the [product map](../architecture/product-map.md).
For changes, use [Contributing](../../CONTRIBUTING.md).

## When something stops

Use [troubleshooting](troubleshooting.md). Preserve the failed operation and
existing state; do not combine packages, erase a retained Test or disable
security checks to make progress.

## Specialist routes

- [Standalone AosVM](../operations/aosvm-apple-silicon.md) is a component-level
  engineering guide, not the installer workflow. Never run its launchers over
  an installed Demo Control-owned instance.
- [Design and requirements](../architecture/README.md) explain the system
  contract. [Qualification](../qualification/README.md) contains dated evidence.
- [Historical local setup preview](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/84056efdf73c518d14929d66a772673212e8a2d9/docs/getting-started/local-setup-preview.md) is retained for
  reference, not as a current installation procedure.
