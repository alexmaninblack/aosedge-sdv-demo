<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Getting started

Choose a route by what you want to do. You do not need the project's history,
old kit numbers or sibling repositories to choose a route.

1. **Run:** [Install and connect Cloud access](installed-preview-cloud-first-use.md).
   Use one matching DMG, with no compiler or Unreal Editor.
2. **Build:** [Developer build](reproduce-demo.md). Build project components
   and the installer, reusing verified CARLA and Factory inputs.
3. **Rebuild heavy dependencies:** [Full source](full-source-build.md).
   This separate route lists its unresolved prerequisites and is not yet qualified.

All routes start from [release selection and access](release-status.md).
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
- [Historical local setup preview](local-setup-preview.md) is retained for
  reference, not as a current installation procedure.
