<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Operations Documentation

This directory contains current operator procedures. Dated experiments,
phase-by-phase execution logs and accepted evidence live under
[`qualification`](../qualification/README.md), so an operator sees one
unambiguous path.

- [Run AosVM on Apple Silicon](aosvm-apple-silicon.md) — canonical install,
  local lifecycle, network-change recovery and explicitly gated provisioning
  procedure.

All persistent Unit identities and secrets remain outside Git. Provisioning is
never implicit.

## Demo Control — Read-only Status

The [Demo Control design](../architecture/demo-control.md) describes the shared
CLI/UI direction. Its first read-only status slice is implemented; lifecycle
mutations remain disabled. See the [package README](../../apps/demo-orchestrator/README.md)
for executable status commands, local configuration and limitations. It does
not replace the working VM lifecycle procedure above.
