<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# AosCore review deltas

Small source-only review patches for the
[13 September idle full-status proof](../../docs/qualification/cm-idle-full-status-recovery-2026-09-13.md).
These are not compiled artifacts, a second runtime implementation, an installed
override or evidence of upstream acceptance. Their contents are preserved
unchanged from the experiment. Factory .33 applies its owned recipe patches
in `aos-vehicle-platform`; do not apply these review copies to a running Unit.

- `cm-idle-full-status-library.patch`: optional idle worker refresh, disabled
  by default, and focused tests.
- `cm-idle-full-status-app.patch`: CM configuration parsing and wiring.

Upstream review and removal after a qualified Cloud-side repair remain open;
see the [consolidation register](../../docs/qualification/factory-33-consolidation-audit-2026-09-13.md).
