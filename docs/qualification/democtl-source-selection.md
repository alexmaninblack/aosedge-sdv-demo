<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# democtl Local Source Selection

- Status: review candidate
- Version: 0.2.0
- Prepared: 2026-09-05
- Owner: Demo Solution

Scope: the operator-authorized local server-TLS amendment in
[Demo Control](../architecture/demo-control.md#local-demo-amendment-defer-per-unit-viss-mtls).
This record does not qualify per-Unit mTLS, new FOTA payloads, a new VM image,
or an independent functional-service/KUKSA consumer.

## Live CLI Results

Commands ran from `apps/demo-orchestrator` using its editable `democtl`.
Both fresh local VMs were created, started and provisioned through that CLI.
The source preparation checks then reused those Online Units.

| Check | Observed result |
| --- | --- |
| Image | `6.1.1-maninblack.28/main-qemuarm64`, unchanged SHA `5154a312598e3712666e27573adee149a730c1816d712f6cdb77bddb3f54da01` |
| `environment prepare --target all --current test` | Both role Units retained; one local source attached to Test |
| `vehicle select production` | Safe Stop, both paths blocked, physical reset, Production-only VISS read |
| `vehicle select test` | Reverse handover completed with the same simulator run and VM processes |
| Repeated `vehicle select test` | `noOp=true`; no new reset or assignment generation |
| Repeated `environment prepare --target all --current test` | `noOp=true`; reset and assignment generation remained 5 |
| `status --guest --cloud` | Test connected; Production read timed out behind its BLOCKED gate; both Units Online |
| VDP on Test | Active, `VDP data READY; source LIVE; reason NONE`, `NRestarts=0` |
| VDP on Production | Inactive baseline; no claim of a running VDP data chain |

Final read at approximately 13:03 UTC:

- Test Unit: `4279840f-d81f-410b-abf3-376e69719fc2`, Test Vehicles membership confirmed.
- Production Unit: `766f8fcc-e733-4d1c-a928-fb25176a2f4f`, Production Vehicles membership confirmed.
- QEMU PIDs remained Test 40986 and Production 40993, the original started processes.
- Simulator run `21ed7ae4-cc29-4e55-9487-5d40b3791abe`; ego actor 26.
- Final physical reset generation 5; applied control generation 10.
- Final handover waited for brake 1.0, SAFE_STOP and speed approximately
  0.026 km/h; subsequent status observed 0 km/h and no held orchestration.
- The independent Test guest read observed advancing VISS frames 29989 → 29991.
- The independent Production guest read returned a transport timeout while
  its exact incoming/outgoing VISS gate was BLOCKED.

Raw private runtime logs remain under the existing current-run source
directory. They are not committed build artifacts or backups.

## Corrections Proven During Integration

- The interactive runner now passes the shared simulator run ID and private
  frame-facts socket already required by Controller/Gateway.
- The caller explicitly selects the authorized local server-TLS development
  profile. No implicit strict-to-development fallback was added.
- A transient SSH-forward attempt was rejected by the existing SELinux
  `sshd_t` port-binding restriction. It was removed; no policy permission was
  added. The implemented route uses only the owned guest nftables table.
- The independent guest probe uses the standard library and the Gateway's
  required `VISSv3` WebSocket subprotocol. It does not depend on a VDP payload
  being installed or on that payload's private Python packages.
- The reset-completed phase alone is insufficient while physics is settling.
  The host wait also checks the current completed frame's speed, brake and mode.
- Interrupted attachment was reconciled with the same Controller operation
  ID; a completed reset was not repeated.

## Automated Gates and Boundaries

- 121 orchestrator regression tests passed.
- 37 Controller/protocol tests and 44 launcher/tool tests passed.
- Fixtures cover invalid/plural selection, stop/reset failure before attach,
  contradictory live gates, same-role no-op, TLS failure closing the selected
  gate, same-operation recovery, stale/non-advancing frame rejection and
  composite writer exclusion.
- The live vehicle remained in Safe Stop for automated handover checks.
  A user-driven visual/autopilot handover has not been claimed by this record.
- Park/resume, source teardown and extending an already attached environment
  with an unprepared role remain separate lifecycle increments. A VM reboot
  loses its transient redirect and fails closed; it is not reported as resumed.
- There was no VM rebuild, broad firewall change, SELinux relaxation, client
  mTLS issuance, Cloud rights change or new VDP upload in this increment.

## Simulation Lifecycle and Performance Increment — 2026-09-05

This later CLI acceptance supersedes the earlier source-teardown and expensive
default-status limitations only. Park/resume, full retirement and full E2E
qualification remain outside this increment. Changes are in the current dirty
Solution orchestrator/documentation tree and Gateway runner stop policy; no
commit, push, image build or Cloud mutation was performed for this increment.
Base commits are Solution `fe35641917033c83e778f80c4402941379b08941` and
Gateway `4f6da4c3c82448e98f12c55e7c6f728a50ee7f90`; current uncommitted changes,
including prior work, are not represented as those commits' contents.

All live operations used the editable `democtl` from `apps/demo-orchestrator`.
The assistant used only `simulation start/stop` to launch/shut down simulation.
Measured elapsed times include CLI startup, not tool invocation overhead:

| Command/check | Result | Elapsed |
| --- | --- | --- |
| `vehicle select test`, simulator stopped | `SIMULATION_NOT_RUNNING`; no startup/guest/Cloud work | 0.10 s |
| Fresh `simulation start` | CARLA, Controller, Gateway, keyboard UI ready; no VM selected | 37.28 s |
| Test → Production → Test | Exclusive handover, physical stop/reset and TLS/VISS proof | 3.14–3.22 s each |
| Repeat selection of Test | Confirmed no-op, no reset | 2.83 s |
| Repeat `simulation start` | No-op, Test preserved | 0.21 s |
| Ordinary `status` | Selected Test and dated last confirmation; no SSH/Cloud | 0.22 s |
| `status --guest --cloud` | Test CONNECTED/VDP READY, peer BLOCKED, both Units Online | 6.04 s |
| Live `simulation stop` | Physical Safe Stop CONFIRMED; detach; runner and CARLA exit | 3.62 s |
| Repeat stop | No-op | 0.15 s |
| Start again from stopped | New simulator session; same VMs/Cloud identities; no selection | 34.30 s |
| Select Test after restart | Connected, car remains in Safe Stop | 3.51 s |
| Final `status --guest` at 13:56 UTC | Test VDP REPORTED_READY; both Aos cores active, restarts 0 | 5.25 s |

The final simulator run is `1d21f2c9-7884-47c4-8ee6-c6f59d7eeb3c`, with Test
selected and assignment generation 1. Both original QEMU PIDs and Unit/Node
identities above remain unchanged. The new run's private logs remain under
`.run/demo-current/source/`; no cleanup or backup was part of this change.

The pre-change ordinary status measurement was 5.050 s. Pre-change selection
overhead was an estimated 20–25 s, derived from separately measured Cloud and
SSH reads, not a measured complete handover. Do not present it as a measured
before/after switching benchmark.

The preceding long-running Controller session had exited before the first
live test (`external controller stopped during live handover`). The explicit
stop correctly reported physical stop NOT_OBSERVED for that expired session,
confirmed detachment and removed only owned running processes. It was not
reported as a successful physical-stop proof. A later live stop provided that
proof. No VM was rebooted/reprovisioned to recover the simulator session.

Gates: 137 orchestrator tests, 51 launcher/tool tests and 9 targeted Controller
orchestration tests PASS; documentation gate and both diff whitespace checks
PASS. Fixtures additionally cover no guest/Cloud work in ordinary status or
early select failure, SSH reuse/expiry/cleanup, read deadlines, partial-start
cleanup, uncertain stop reconciliation and no forced child kill. Full composite
prepare was not rerun against Cloud in this increment; the existing VM/Unit
primitives are reused under the same writer.

Known visible-UI gap found by the operator: the live terminal telemetry
dashboard is started by the runner, but detached launch redirects its terminal
output to `runner.log`. No separate dashboard window is opened. The old native
launcher opened Terminal for that output; that presentation step has not yet
been integrated into `simulation start`. This is not a telemetry-delivery
failure and is not claimed as complete visual dashboard acceptance.
