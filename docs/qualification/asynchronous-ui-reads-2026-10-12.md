<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Asynchronous M1 UI read results

- Date: 12 October 2026
- Status: Step 4 PASS; overall runtime speedup not established
- Branch: `codex/presenter-human-friendly`

The unchanged 42-stage continuous UI scenario passed on M1 with 166 fresh
independent reads over one pinned SSH connection. All reads succeeded, no
automatic reconnect occurred, and all owned clients, processes, listeners,
media and temporary display assertions closed. Test data and shared Docker
were preserved. The passing campaign took 1,220.281 seconds (20:20).

This closes Step 4 of the [ordered plan](ui-qualification-timing-2026-10-12.md),
not complete installer E2E or main integration. The development Mac ran only
unit tests and orchestrated M1; product, DMG, Factory, CARLA, credentials,
permissions, Production, video and the deferred VDP timeout were unchanged.

## Implemented boundary

[The reply broker](../../scripts/qualification/ui_read_broker.mjs) keeps browser
routing and timers responsive while an independent read runs. Every scenario
read is awaited. It rejects concurrent requests, wrong IDs, malformed, oversized
or failed replies, EOF, timeout and cancellation without replaying input.
Buffered reply parsing replaces per-byte blocking reads. Timing-write failures
also reject instead of leaving an unresolved promise.

[The read transport](../../scripts/qualification/ui_read_transport.py) reuses
only the authenticated SSH connection. Every request still starts a fresh Python
Worker and validates installed selection, candidate, Test and current owners.
No mutable product context or success response is cached. A lost master fails
closed; clients prohibit fallback connections. The private control socket lives
in owned SSD scratch and is removed after the exact master exits. Native input,
publication and lifecycle retain their existing owners and guards.

## Verification

Source gates passed 64 Python tests and 25 JavaScript tests. Coverage includes
fresh repeated replies, a live event-loop timer while waiting, all call sites
being awaited, no mutation queries, lost transport, reply failures, timeout,
cancellation, exact-client closure and stream-listener removal.

A separate M1 read-only transport proof passed in 16.173 seconds: repeated fresh
reads, an intentionally timed-out three-second fixture, absence of that remote
fixture afterward, successful subsequent reads and closed clients/master.
It performed no UI input or vehicle/Cloud mutation. Its one expected failed
request is separate from the positive full campaign's zero failed reads.

The full campaign passed all 42 stages, 14 native inputs and nine serial UI
publications. VDP V1/V2/V3 used physical Safe Stop; Brake V1/V2/V3 and Tire V1
produced correlated results. Independent Reset preserved peer models/history;
moving QM updates preserved Test, boot and VDP. Explicit Stop/Start established
a changed boot with preserved identity, models, history and releases, healthy
services and stationary Manual attachment. Final versions are VDP 164.0.0,
Brake 145.0.0 and Tire 73.0.0.

## Time and remaining optimization

| Measurement | Result |
| --- | ---: |
| SSH connections for independent scenario reads | 1 |
| Fresh reads / failed reads | 166 / 0 |
| Aggregate transport read time | 311.551 s |
| Browser-observed read wait, including broker handling | 313.413 s |
| Median browser-observed read wait | 0.866 s |
| Complete passing campaign, including cleanup | 1,220.281 s |
| Previous Step 3 campaign | 1,210.107 s |

The new campaign was 10.174 seconds longer overall. Successful browser-stage
timers totalled 1,092.224 seconds versus 1,094.953 previously; the small difference
does not establish a speedup. Async waiting and connection reuse are verified,
but read execution and real startup, publication and maneuver work still take
time. These counters do not isolate Python, guest SSH, Cloud or backend costs.
The subsequent [Step 5 comparison](ui-campaign-comparison-2026-10-12.md)
closes comparative acceptance; do not present this implementation as a proven
reduction in full runtime.

Work-session time is separate from campaign time. This implementation session
started at 21:02:20 Europe/Berlin; the passing campaign ran from 21:20:13 to
21:40:33. Development, unit gates, diagnosis and reporting are not included in
its 20:20. An earlier 11.684-second attempt stopped at LOCKED desktop before any
vehicle action, publication or native input; cleanup passed, and the operator
unlocked M1 before the fresh positive attempt. No failed attempt was rewritten.

## Evidence

Private records are under `.local/remote-qualification/m1-async-reads-20261012-r2/`
and `m1-read-transport-proof-20261012/`. They retain campaign, browser, transport,
input and independent final-closure reports. The unchanged package is
`31f135fae8b547358495d5a046c73840a22dac3fbfebbf4e3ddc8d8b137d462c`;
Test is `3bb88ede-8c78-4c1a-80b6-41264982aeaa`. Campaign source pin is
`72e6b9221b9e263ff701b6eb7c6ac39e39aeef09dee53a718b26c417bdef6ae3`.
Credentials, browser profiles and raw network traces remain outside Git.
