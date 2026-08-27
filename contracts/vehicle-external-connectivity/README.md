<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Vehicle External Connectivity — Design Reviewed

- Decision: `D4-022`
- Lifecycle state: `DESIGN_REVIEWED`
- Contract version: `1.0.0`
- Accepted subdecisions: D4-022.1 dual-network mechanism, D4-022.2 probe/UI
  state machine, D4-022.3 transition/recovery behavior and D4-022.4
  qualification plan, 2026-08-23

The current single-NIC AosVM launcher cannot model the accepted fault: taking
that link down would remove both external connectivity and the in-vehicle
VDP-to-VISS/Gateway path. The successor OEM Demo Factory Image and QEMU
launcher therefore provide two explicit network planes per VM.

`vehicle-net`/`vehicle0` carries only the VDP-to-VISS/Gateway route, has no
default route or Cloud DNS and remains up. `external-net`/`external0` owns the
default route, DNS, AosCloud and Brake/Tire backend routes. Both concurrently
running VMs have independent instances of these planes.

The protected native helper resolves the currently selected Validation or
Production role from the current-run journal and issues one fixed QMP
`set_link` operation to that VM's exact `external-net`. The other VM is not
affected. QMP and serial remain out of band; the browser receives neither a
QMP socket nor an arbitrary-command surface. No macOS or guest firewall
mutation is required.

This is an OEM pre-SOP Factory Image network configuration and demo QEMU
launcher change, not an upstream AosCore source change.

The single control exposes `ONLINE`, `TRANSITIONING`, `OFFLINE`, `RECOVERING`
or `FAILED/PARTIAL` and is disabled during transitions. No individual Cloud or
backend switch exists, and no single probe may establish success. `OFFLINE`
requires the selected external link down, authoritative selected-Unit Cloud
offline, no post-disconnect Brake/Tire backend receipt, continued local
VISS/KUKSA analytics/advisory and telemetry, continued presenter Cloud access
and an unchanged other VM. Function Dashboards keep the last actual result and
show external connectivity unavailable without fabricating current data.

Recovered `ONLINE` requires the same Unit UUID/`system_uid` online, no
reprovision/reinstall/service restart, idempotent bounded outbox
synchronization with original event time distinct from receipt/sync time, and
unchanged other-VM/in-vehicle paths. Any mismatch is `FAILED/PARTIAL`. The
normative presentation selects PU, although the mechanism supports the current
VU role during qualification.

The helper always sets an exact desired state and never implements a blind
toggle. It journals the exact role, Unit identity, QEMU process/socket,
external netdev, last confirmed state and desired state before QMP mutation.
A request for an already achieved state probes and returns an idempotent
no-op. A missing QMP response is not success and is never retried blindly:
all accepted probes are reconciled first, after which an explicit idempotent
reissue may be made. Mixed or ambiguous evidence is `FAILED/PARTIAL`.

A forbidden side effect or partial transition attempts compensation to the
last confirmed state through the same exact selector. Compensation itself
must pass the full probe set; otherwise the state remains `FAILED/PARTIAL`.
After a Dashboard/helper restart, the journal and probes are reconciled before
any mutation. Recovery preserves the same Unit and installed graph and does
not reprovision, reinstall or restart a service. Queued functional messages
synchronize idempotently and retain original event time separately from later
receipt/synchronization time.

The local QMP acknowledgement bound is five seconds. Cloud convergence and
functional-backend synchronization bounds must be frozen by D4-022.4 live
qualification rather than invented as audience-facing performance KPIs.
No wait is unbounded. QEMU 11.0.3 exposes the required `set_link` command but
no dedicated `query-netdev`, while `query-rx-filter` does not expose link
state; therefore no single QEMU query is accepted as transition truth.

Live acceptance starts with both VU and PU concurrently running, uniquely
identified, in their correct disjoint Unit Sets and online with the expected
software graph and local dashboard stack. It runs two complete disconnect/
restore cycles for each role. Every offline cycle creates a new deterministic
CARLA event and proves selected-Unit Cloud/backend loss, continued local
analysis/advisory/telemetry and an unchanged online peer VM. Every restore
cycle proves the same Unit/Node identities and software graph, no reprovision,
reinstall or Service restart, duplicate-safe queued-message synchronization
and distinct source/receipt/synchronization times.

Controlled qualification covers lost QMP response, Dashboard/helper restart,
duplicate achieved-state request, stale/contradictory probes, forbidden peer
or vehicle-path effects and failed compensation. Live evidence freezes the
Cloud/backend operational bounds before acceptance. One sanitized engineering
qualification record is retained; ordinary demo-run history is not. The
design is reviewed, while implementation and live evidence remain an explicit
acceptance gate.

This contract authorizes no VM, network, Factory Image or Cloud mutation.
