<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Getting started

Start with the [single launcher in README](../../README.md#start-here) and
choose what you want to do:

1. **Run:** [Install and connect Cloud access](installed-preview-cloud-first-use.md).
   Use one complete DMG, with no compiler or Unreal Editor.
2. **Build:** [Build the demo and installer](reproduce-demo.md). Build project
   components while reusing the prebuilt CARLA simulator and ARM64 virtual
   controller image (**Factory image**, the clean Linux/AosEdge base).
3. **Prepare tools to rebuild the controller image or simulator:**
   [Specialist scope and prerequisites](full-source-build.md). This prepares
   host tools; source, licensed assets and the separate Linux Builder are
   additional requirements.

[Release and access information](release-status.md) explains package selection
and Cloud credentials. The [launcher reference](unified-macos-launcher.md)
covers saved choices, repeats and optional controls.
For a system overview, use the [component map](../architecture/product-map.md).

For first-time access, use [Cloud registration and token steps](installed-preview-cloud-first-use.md#new-cloud-access).
For a B result, [install that exact DMG](reproduce-demo.md#install-your-build),
not the published A package. Editing components is a separate
[contributor workflow](../../CONTRIBUTING.md#from-a-source-change-to-your-own-installer).

## When something stops

Use [troubleshooting](troubleshooting.md). Keep the failed operation's message
and existing state. Do not combine packages, erase a retained Test or disable
security checks to make progress.

## Component development

Use [Contributing](../../CONTRIBUTING.md) and the
[development map](../development/README.md) for source changes.
[Standalone AosVM](../operations/aosvm-apple-silicon.md) is a component-level
guide, not the installer workflow. Do not run its launchers over an installed
Demo Control-owned instance.
