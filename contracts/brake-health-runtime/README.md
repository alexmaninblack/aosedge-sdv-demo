<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Brake Health Runtime and Evidence Profile

- Decision: D4-016.5 accepted 2026-08-23
- Contract version: 1.1.0
- Accepted profile SHA-256:
  `bc93334ed7af4e5d4238b5720cbe1e4ea184c4c04aeeb5ad60d1ee926ce70820`

This profile freezes the proposed capability-oriented readiness, requested Aos
quota envelope, cross-version state rules and bounded native-log vocabulary
for Brake Health v1-v3. AosCore remains the process/resource authority and
AosCloud remains the native log source; the Service introduces neither a
resource manager nor a separate log archive.

The quota values match the current scaffold and remain subject to live
measurement and the independent D4-023 AosCore isolation qualification. A
declared value is not evidence that enforcement or headroom has passed.

On 16 September 2026 the operator approved increasing Brake `pidsLimit`
from 16 to 24, with measured headroom required. Brake V3 had exhausted the
16-task envelope (one bootstrap plus 15 product threads), with a thread
creation failure. Only immutable Service package metadata changes; other
quotas, model thresholds and native AosCore enforcement remain unchanged.

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

Ordinary process, container and VM restarts preserve the producer epoch and
continue from the persisted next advisory sequence without reuse. Only an
explicit producer replacement or new producer lifecycle rotates the epoch,
exactly once, and starts its sequence at `1`. R0 destroys that producer state.
Late evidence from an old epoch may remain historical evidence but never
changes the current state or advisory.

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
