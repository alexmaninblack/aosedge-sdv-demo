<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Continuous M1 UI campaign results

- Date: 12 October 2026
- Status: Step 3 PASS; full installer E2E remains separate
- Branch: `codex/presenter-human-friendly`
- Target: Dedicated M1, internal storage, Aos Cloud staging

One uninterrupted scenario passed all 42 browser stages and 14 native mouse
actions in 1,210.107 seconds (20:10), including final cleanup. It covered serial
VDP/Brake releases, Tire V1, installed views, independent Reset, moving QM
updates and an explicit same-Test Stop/Start. No agent scheduled individual
clicks. Healthy owners remained running between sections; only the declared
lifecycle check and final Stop restarted or closed the vehicle environment.

This closes Step 3 of the
[ordered optimization plan](ui-qualification-timing-2026-10-12.md).
It does not replace first-use Setup/WKWebView, permissions/token entry,
installation repair, offline soak or complete installer E2E acceptance.
Asynchronous independent query transport was qualified separately in
[Step 4](asynchronous-ui-reads-2026-10-12.md), followed by the
[Step 5 comparison](ui-campaign-comparison-2026-10-12.md). Main, Production,
the video repository and the deferred VDP timeout are unchanged.

## Execution and release results

The [single campaign entry](../../scripts/qualification/continuous_ui_campaign.py)
owns preflight, VM access, visible UI execution and cleanup. Playwright clicks
the installed Presenter controls on M1; the signed Native UI Runner resolves
the actual Driving Control buttons by semantic ID and delivers mouse input.
Fresh read-only owner observations independently establish installation,
movement, source-bound completed maneuvers and matching backend products.
Input receipts alone are not vehicle-result evidence.

| Section | Passed evidence |
| --- | --- |
| Serial release story | VDP V1/V2/V3 installed after physical Safe Stop; Brake V1/V2/V3 and Tire V1 installed and exercised before advancing |
| Installed views | Installed cards, all three team views, Cloud/resources, backend/record views, Activity and Stop cancellation |
| Independent Reset | Brake and Tire reset separately; peer model and both backend histories preserved |
| Moving QM updates | Brake V3 and Tire V1 installed during fresh Autopilot motion; Test, boot and VDP unchanged; new completed maneuvers and version-matched products |
| Same-Test Stop/Start | Boot changed; identity, models, histories and installed releases preserved; healthy services, stationary Manual attachment and restored window layout |
| Final closure | Zero owned demo processes/listeners and qualification clients; owned media detached and temporary display assertion closed |

All nine publications occurred through real UI, serially, with installation
confirmed before the next publication. Existing Subject assignments were reused;
there was no new assignment, Test creation, retirement or backend-history deletion.

| Component | Serial story versions | Moving update | Final installed version |
| --- | --- | --- | --- |
| VDP | V1 159.0.0; V2 160.0.0; V3 161.0.0 | Not changed | 161.0.0 |
| Brake | V1 138.0.0; V2 139.0.0; V3 140.0.0 | V3 141.0.0 | 141.0.0 |
| Tire | V1 70.0.0 | V1 71.0.0 | 71.0.0 |

## Measured time

These groups sum successful browser-stage timers. Complete campaign time also
includes preflight, VM access, bootstrap, client/transport work between stages
and final cleanup; the remainder is not all browser or cleanup overhead.

| Group | Seconds |
| --- | ---: |
| Initial visible startup and exact installed baseline | 158.986 |
| Serial release story and Return to road | 476.491 |
| Installed views, independent Reset and Stop cancellation | 38.153 |
| Moving updates, maneuvers and final release checks | 250.072 |
| Explicit Stop/Start and preservation checks | 149.661 |
| Final confirmed Stop | 21.590 |
| Work outside those browser-stage timers | 115.154 |
| Complete campaign | 1,210.107 |

The 14 local native input receipts totalled 1.257 seconds: median 78.5 ms,
range 66.7–230.3 ms. These measure the executor's resolution/input processing,
not physical maneuvers, installation settlement or independently observed
results. No conversational native-input waiting occurred. The original 42:22
baseline combined six attempts with different coverage and failures; it is not
an equivalent denominator for a full-E2E speedup claim.

## Guard and recovery evidence

Three earlier attempts remain preserved. The first stopped before browser input
because reused `ui` basenames collided in remote record storage. The adapter now
binds a stable remote namespace to the complete local campaign path, preserving
at-most-once behavior while isolating separate campaigns. The second stopped on
its initial Presenter read, before vehicle actions, publication or native input.
Subsequent HTTP-only diagnosis observed successful reads, but did not establish
that attempt's exact HTTP failure cause. The third stopped at LOCKED desktop
preflight; the operator unlocked M1 before the passing campaign.

Each earlier attempt confirmed cleanup. Their measured campaign durations were
112.119, 108.974 and 10.437 seconds, outside the passing run's 20:10. The passing
campaign had no refused Presenter reads and did not use the new bounded,
read-only startup-503 retry. That retry permits only the two recognized
temporary observation codes; it never retries a permission refusal, publication
or mouse input. No failed attempt is relabelled PASS.

The continuous runner uses its own fixed stage allowlist. Control-pilot profiles
cannot issue campaign stages, and campaign profiles cannot issue arbitrary or
pilot stages. Native input remains bound to the original exact PID, executable,
candidate, Test and Presenter session. No native input occurs after the explicit
restart, so lifecycle coverage does not rebind the input client silently.

Final source gates passed 58 targeted Python tests, 18 JavaScript scenario tests
and the signed helper's pure Swift request-parser test. All live checks ran on
M1. The development Mac ran only unit tests and compiled the small qualification
helper on SSD; no product/DMG, Factory or CARLA rebuild was required.

## Evidence and preserved state

- Private campaign: `.local/remote-qualification/m1-continuous-ui-20261012-r4/`.
- Retained Test: `3bb88ede-8c78-4c1a-80b6-41264982aeaa`.
- Unchanged installed package: `31f135fae8b547358495d5a046c73840a22dac3fbfebbf4e3ddc8d8b137d462c`.
- Campaign source pin: `328779c4642d099d9ae539ac447b398b07a78c19913671adb7db30c05d2e3d89`.
- Signed native executor: `35e5f9cf6548e42ee44cc1fed7ef2eecf4f295400257c510d5098def8f48372b`.

The campaign report, browser stages/actions, native intents/receipts, cleanup
result and independent final closure remain private. Persistent Test data and
the same Docker Engine are preserved. Credentials, browser profiles and raw
network traces are not included in this Git receipt.
