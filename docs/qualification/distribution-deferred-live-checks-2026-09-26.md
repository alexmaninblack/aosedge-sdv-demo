<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Distribution assembly: deferred live checks

- Date: 2026-09-26.
- Status: Historical deferral; post-assembly continuation now qualified below.
- Parent: [portable runtime work packet](../planning/active/portable-runtime-artifacts.md).

The operator initially requested completing package assembly before further checks of
the current screen. No Docker/VM/service/Gateway/native-panel restart is part
of this continuation. Unit/static/artifact-integrity gates remain necessary
build checks, not live qualification.

## Evidence retained from the preceding read-only diagnosis

1. Both backend inspections returned `BACKEND_DOCKER_ENGINE_UNAVAILABLE`.
   Docker's engine socket and backend listeners were absent. The earlier
   [backend export checkpoint](../planning/active/portable-runtime-artifacts.md#backend-export-and-vehicle-input-checkpoint)
   records deliberately restoring Docker Desktop to its initial stopped state;
   this current observation is not evidence of a backend crash. Starting Docker
   can also start unrelated containers under their saved restart policies.
2. Same Test .39 was Cloud Online; VDP 117.0.0/V3 was active, with live input
   and zero restarts. Brake/Tire processes were independently present in the
   guest. Brake recorded a completed assessment around 15:49 UTC and backend
   synchronization entered `BACKLOG`. This is local-processing evidence, not
   backend receipt or advisory success.
3. VDP reported `FORWARDED_TO_GATEWAY` followed by `VISS_SET_REJECTED` for both
   advisory endpoints. The generic transport log omits the exact error reason.
   A read-only guest KUKSA observation found both saved GatewayStatus values
   `EXPIRED/NONE`, dated 25 September 05:30:28 UTC. Those stale values do not
   establish the reason for today's rejection. The cause remains unresolved.
4. A second native client using the already-occupied dashboard role was
   rejected. The one-connection-per-role policy explains why that diagnostic
   harness cannot run alongside the dashboard; do not weaken admission or
   count this probe failure as another product outage.
5. The older container inspector reported no process from its runtime PID-file
   lookup, while `/proc` showed both bootstraps and both services running.
   Treat that helper result as incomplete observation, not service-crash proof.

## Post-assembly disposition

The operator subsequently authorized assembly followed by a live run. The
[complete application report](portable-application-2026-09-26.md) records the
bounded corrections and measurements. All five packaged dependency groups are
now selected through existing owners; retained Test .39 has booted and attached.
Docker and the existing backend volumes are available. Backend receipts and
local advisory round trips have been verified online and during external OFF/ON.

The advisory rejection was a packaging input regression, not a .39 Factory or
model defect: the selected native Gateway/client pair predated QM support.
Current warm inputs and six protocol/security suites passed; replacing only
that pair changed the observed result from rejected writes/stale facts to fresh
accepted/APPLIED facts for both services. No role limit or security check was
relaxed. The rejected extra diagnostic dashboard client remains a harness issue.

The generic older container PID helper remains an incomplete observation; this
run instead verifies service work through fresh assessments/function observations
and advisory facts. Do not claim the PID helper was repaired. Native layout and
ordering pass; browser/native visual acceptance and fresh serial-version E2E
remain open. Brief readiness transitions are retained as a separate follow-up.

## Original revisit checklist

- Perform the authorized preserved-owner handoff and declared backend startup.
- Prove backend receipt separately from local service processing and queued
  delivery, including the externalOFF/ON case.
- Obtain the precise bounded Gateway rejection reason and correct only a
  reproduced cause; do not guess time skew, authorization or schema failure.
- Verify local advisory independently of backend/Cloud availability.
- Reconcile container-process observation with the actual Aos runtime.
- Complete the pending VM/DNS, packaged guest/UI and serial-version E2E gates.

No claim of a fully working distribution, a failed .39 Factory, lost model
data or a causal link to the Presenter metadata correction follows from these
interim observations. Preserve the active Test and Production .31, identities,
overlays, histories and release ledgers until their explicit lifecycle handoff.
