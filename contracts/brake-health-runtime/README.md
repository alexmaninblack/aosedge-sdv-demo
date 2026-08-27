<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Brake Health Runtime and Evidence Profile

- Decision: D4-016.5 accepted 2026-08-23
- Contract version: 1.0.0
- Accepted profile SHA-256:
  `d16bbfe4f1672c0d9935826f2d79b6cc3331a050f72d30d0e9365332c09c0064`

This profile freezes the proposed capability-oriented readiness, requested Aos
quota envelope, cross-version state rules and bounded native-log vocabulary
for Brake Health v1-v3. AosCore remains the process/resource authority and
AosCloud remains the native log source; the Service introduces neither a
resource manager nor a separate log archive.

The quota values match the current scaffold and remain subject to live
measurement and the independent D4-023 AosCore isolation qualification. A
declared value is not evidence that enforcement or headroom has passed.

Process health and product capability are separate. AosCore owns only the
process lifecycle. The Service reports `OPERATIONAL`, `DEGRADED` or
`NOT_READY` from separate analytics, backend-sync and version-dependent
advisory axes. Backend or AosCloud loss never gates local analytics. A running
v3 Service with working analytics but a temporarily unavailable advisory chain
is `DEGRADED`, not process-failed; initial v3 deployment acceptance still
requires the advisory chain to prove `READY` at least once.

Absence of an eligible braking episode and an individual insufficient-input
episode are outcomes, not readiness failures. Likewise, an individual Gateway
`REJECTED`, `EXPIRED` or `FAILED` result remains factual command evidence and
does not by itself redefine capability readiness.

On v1-to-v2 update, v2 analytics starts from its preconditioned model state
without waiting for the bounded v1 spool. The legacy spool drains in the
background and is deleted only after durable backend acknowledgement or R0.
On v2-to-v3 update, exact model state is reused and the accepted D4-016.4
persisted-active-condition behavior applies. Unknown state or model digest is
quarantined explicitly; it is never silently reset.

Structured Service logs report owned state, queue and capability facts.
Repeated records are rate-limited and aggregated. CPU/RAM quota enforcement
and evidence come from AosCore, not from a Service-side resource monitor.

The first demo intentionally saturates CPU only inside Tire Health. AosCore
caps that instance by throttling without stopping, restarting or redeploying
it; Brake Health is the healthy control tenant and must continue processing the
deterministic event while VDP, KUKSA and Gateway remain healthy. Stopping the
load returns the same Tire instance to normal. RAM, storage, state, tmp, PID
and file-limit overruns are not intentionally demonstrated and no common
throttling behavior is claimed for them. Restart for an unrelated failure must
recover or explicitly quarantine persistent Brake state.
