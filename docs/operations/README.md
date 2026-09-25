<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Operations Documentation

This directory contains current operator procedures. Dated experiments,
phase-by-phase execution logs and accepted evidence live under
[`qualification`](../qualification/README.md), so an operator sees one
unambiguous path.

- [Current SDV Lab workflow](current-demo-workflow.md) — the implemented
  Studio lifecycle, sequential releases, status/monitoring interpretation,
  Reset, offline checks and separate ignition recovery.
- [Run AosVM on Apple Silicon](aosvm-apple-silicon.md) — standalone install,
  local lifecycle, network-change recovery and explicitly gated provisioning
  procedure.

All persistent Unit identities and secrets remain outside Git. Provisioning is
never implicit.

## Demo Control — shared CLI and Presenter implementation

The [Demo Control design](../architecture/demo-control.md) records the shared
CLI/UI contract and dated amendments. Lifecycle, preparation/publication,
assignment, observation and guarded Finish are implemented. See the
[package README](../../apps/demo-orchestrator/README.md) for commands and local
configuration. Do not run standalone legacy launchers over an active
Demo Control-owned environment. Historical read-only milestones are not the
current capability boundary.
