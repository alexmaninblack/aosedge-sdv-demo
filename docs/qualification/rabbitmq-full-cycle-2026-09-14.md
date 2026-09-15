<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Full Test cycle and RabbitMQ timeout observation — 14 September 2026

Status: **COMPLETED — the prior 30-minute connection-event timeout did not
recur in this run.**

The Test lifecycle completed at 16:15:44 UTC. Passive Grafana observation
continued through 16:46 UTC, more than 31 minutes after the final WebSocket
disconnect. The scoped RabbitMQ queue query returned zero matching entries;
UMH retained exactly the four original connection events with approximately
8–13 ms receipt delay and no late duplicate. This is a bounded non-reproduction,
not proof that the Cloud defect has been fixed globally.

## Scope

User-authorized clean Test-only run on selected `aoscloud.io`, using immutable
Factory `.33`. Production is preserved. All lifecycle/publication/assignment
actions use existing `democtl` commands; driving uses native CARLA controls.
No CM/SM patch or standalone manager restart, Cloud change, image rebuild or
timeout bypass is part of this test. Services use synthetic data; native
KUKSA permissions remain blocked.

The target signature is the previously observed connection-event consumer
acknowledgement timeout (`1800000 ms`), channel closure and delayed handling
of an older connect/disconnect event. Delayed Online/Offline alone does not
prove that RabbitMQ signature. Observe beyond 30 minutes, including final
whole-VM shutdown and authoritative Offline before deprovision/delete.

Source base: `52dd2c0bedbad43944ee05e2569e51d7306d9774` with existing local
changes. This is a development-tree live run, not clean-tree qualification.

## Execution (UTC)

| Time / command | Observation |
| --- | --- |
| Initial state | Previous Test retired; simulator stopped; Production retained. Regular `aoscloud.io`, not the earlier developer backend. |
| 15:36 `demo create` | Test `f5a9c93b-1704-4f8f-a70c-ec95fdeea72d` created from .33. Native access dialog unavailable; PARTIAL before VM boot/Cloud activity. Wall 187.96 s including dialog timeout. |
| `vm start test` | Same Test, terminal password enrollment. SSH/DNS and Test role confirmed. Guest 61.71 s; command wall 68.71 s. |
| 15:44:27 `demo create` continuation | COMPLETED, same Test and both backends; 14.93 s. No repeated image creation. |
| `component prepare --profile v1` | VDP49.0.0, seven paths; 2.24 s. |
| `simulation start --target test` | COMPLETED; CARLA/Controller/Gateway and native layout, 47.66 s. |
| `component sign 49.0.0` | Signature verified, 2.05 s. |
| 15:48:46 `component upload 49.0.0` | HTTP201, deployment `585817eb-08b3-4842-b2c6-ab2b2eff95a4`; 5.47 s. |
| `vehicle initialize test`; `unit provision test` | 4.69 / 29.34 s. Same Test Online, Test Vehicles membership confirmed. Unit `7c2a778e-6947-458b-bf04-a62781b3dec0`, system UID `f5a9c93b17044f8fa70cec95fdeea72d`. |
| 15:49:56.674 UMH | Initial `is_connected=true`, event timestamp `1789400996.661519`; approximately 12.5 ms handler receipt delay. No delayed initial connection. |
| 15:57:42 Autopilot | Native controller reports 19.47 km/h. Safe Stop then requested using the normal Space shortcut. |
| 15:57:53 VDP49/v1 | Installed and active, 7 paths, zero restarts. Cloud UMH records installation at 15:57:53.676. |
| `service runtime-prepare test` | Public service inputs prepared, no manager restart or container action. |
| 15:59:21 Brake30/v1 upload | HTTP201, deployment `38ff0018-8ea2-46b4-8f13-2bd7c050e23b`; READY subsequently observed. |
| 16:00:32 Brake assignment | Existing Brake Group Subject bound only to this Test; native service assignment. Autopilot enabled, no further Safe Stop. |
| 16:01:26 Cloud snapshot | Brake30 installed, one active instance. Unit Online; VDP49 installed. |
| 16:02:01 VDP50/v2 upload | HTTP201, deployment `e147df7a-5828-450f-ae21-69ceb4bdc88a`. VDP49 kept running with `waiting-for-safe-stop` until native Safe Stop. |
| 16:03:42 VDP50/v2 | Active, 15 paths, zero restarts, slot b. |
| 16:04:27 Brake31/v2 upload | Deployment `9cf65128-cc43-4a32-acd3-f63908495a20`. Cloud confirms installed/active at 16:05:08, without new assignment or Safe Stop. |
| 16:05:51 VDP51/v3 upload | Deployment `b568e490-ab38-4a2d-bf5e-7374ec42b162`. VDP50 remained active in `waiting-for-safe-stop`. |
| 16:06:51 VDP51/v3 | Native Safe Stop released update. Active, 23 paths, zero restarts, slot a. |
| 16:07:41 Brake32/v3 upload | Deployment `8758beaa-243a-4b79-80ac-72b91d83a725`. Installed/active by 16:08:48 while Autopilot; no new assignment. |
| 16:07:46 Tire21/v1 upload | Deployment `29ebaad0-80ce-4ba2-8390-a47b44afe82d`. READY; assigned at 16:08:33 using separate retained Tire Group Subject; active by 16:08:48. |
| 16:09:34 backend inspection | Brake32 assessment receipts and Tire21 assessment/function-status receipts match current Test UID. Synthetic data only; both backends ready. |
| 16:09:57 Tire22 replacement upload | Deployment `35db67c7-6035-42ac-86d4-c2b4e1b0e586`. Same content profile v1, next release. Installed/active at 16:10:23 without reassignment or Safe Stop. Autopilot 19.42 km/h at 16:10:04. |
| 16:10:43.379 `vehicle connectivity off --target test` | COMPLETED, 2.35 s. Owned guest packet filter; VM, managers, Production and in-vehicle link preserved. |
| 16:11:00 Cloud observation | Still Online before transport close detection. |
| 16:11:17.351 UMH | `is_connected=false`, event timestamp `1789402277.342117`; receipt delay about 8.9 ms. |
| 16:12:09 Cloud observation | Offline, `last_online_changed_at=16:11:17`. Roughly 34 s from packet-filter OFF to Cloud state change, not 30 minutes. |
| Offline guest/backend inspection | VDP51 stayed active, 23 paths, zero restarts and LIVE in-vehicle data. Last Tire22 backend receipt 16:10:38, before OFF. |
| 16:13:27.581 `vehicle connectivity on --target test` | COMPLETED, 2.26 s. Same VM/Unit, no restart. |
| 16:13:28.409 UMH reconnect | `is_connected=true`, event timestamp `1789402408.398532`; approximately 10.5 ms receipt delay. Cloud Online since 16:13:28. |
| 16:15:08 post-reconnect receipts | Brake32 and Tire22 backend receipts continued; Cloud had confirmed both active. |
| 16:15:19.670 final WS close | Whole-VM stop during `demo retire`, normal WebSocket close code 1000. Trace `c2e72cdbc69bd6e170a998e2c114929c`. |
| 16:15:19.681 final UMH disconnect | Event timestamp `1789402519.6732`, `is_connected=false`; approximately 7.8 ms receipt delay. No 30-minute wait before Offline. |
| 16:15:44.135 `demo retire` | COMPLETED, wall 44.67 s. Offline/deprovision/Delete confirmed; Unit and Node absent. Test overlay, Test SSH files and Test factory copy irreversibly removed. Production, shared factory/DNS, source and Cloud releases preserved. |

Initial combined publication command was rejected by execution review before
dispatch. Exact archive/configuration inspection established its baseline
VDP code/library payload and absence of credential files, Unit identity or
vehicle data. The same direct upload was subsequently allowed under the user's
standing publication permission; no alternate upload path was used.

Grafana access was recovered in a new tab of the same authenticated Chrome.
Initial RabbitMQ query from 15:35 UTC contained no matching queue entries;
this pre-provision observation does not qualify this Test's event delivery.

## Connection event correlation

All times below use UTC from the log body. Grafana's WS view can display local
UTC+2 timestamps; those display values are not mixed into the calculation.
Delays are approximate because the handler receipt log is millisecond precision.

| Event | Publisher timestamp | UMH receipt | Receipt delay |
| --- | --- | --- | --- |
| Initial connect | 15:49:56.661519 | 15:49:56.674 | 12.5 ms |
| Network OFF disconnect | 16:11:17.342117 | 16:11:17.351 | 8.9 ms |
| Network ON reconnect | 16:13:28.398532 | 16:13:28.409 | 10.5 ms |
| Finish whole-VM disconnect | 16:15:19.673200 | 16:15:19.681 | 7.8 ms |

The network-OFF transport close occurred at 16:11:17.339 (code 1006), trace
`4aeab670530fdc8efd6a357b5c62f2fa`. Packet filtering completed at 16:10:43.379;
the approximately 34-second interval is transport disconnect detection, not
a delayed UMH connection-event receipt.

## Scope and limitations

- Actual lifecycle, three VDP content profiles, three Brake profiles, Tire
  install/replacement, backend receipts, link OFF/ON and final cleanup passed.
- Component replacement waited for native Safe Stop. Service replacements did
  not require Safe Stop or a second Subject assignment.
- Service data was explicitly synthetic (`DEMO_MOCK`), not KUKSA telemetry;
  this does not close the platform permissions issue or qualify real advisory.
- This was a CLI-driven live test with native driving controls, not a new
  UI-only qualification. Initial native password-dialog unavailability required
  the existing terminal VM-access path; that separate UX issue is not cleared.
- Production was excluded. No Cloud code/configuration, CM/SM binary or runtime
  setting was changed, and neither manager was restarted independently.
- No RabbitMQ acknowledgement timeout or matching queue entry appeared in
  the scoped Grafana query through the final observation, beyond the last
  disconnect +31 minutes. No late duplicate appeared in the UMH event query.

## Remaining open issues

This requested run has no remaining execution step. The previously demonstrated
Cloud defect remains open until the platform team establishes and fixes its
cause; one successful run does not close it. Native KUKSA permissions and the
separate initial native-password-dialog UX limitation also remain outside the
successful functional scope above. No additional Test was created after cleanup.

## Passive post-cycle observation

| Observation time (UTC) | Result |
| --- | --- |
| 16:20:30 | Initial connection +30 minutes elapsed. RabbitMQ queue-name query still returned zero matching entries; UMH still showed exactly the four original connection events, without delayed duplicate initial connect. Final-disconnect window remained open. |
| 16:25 / 16:30 / 16:35 | Same scoped results: no matching RabbitMQ queue entry; exactly four UMH events, no duplicates. No system mutations. |
| After 16:41:17 | Network-OFF disconnect +30 minutes elapsed without timeout or delayed duplicate. |
| 16:44 | Reconnect +30 minutes elapsed; same result. |
| 16:46, final read | Last whole-VM disconnect +31 minutes elapsed. RabbitMQ query: zero matching entries; UMH query: exactly four original events, no late redelivery. |

## Reproducible Cloud evidence queries

- [RabbitMQ queue logs, run and passive observation window](https://grafana-prod01.aoscloud.io/a/grafana-lokiexplore-app/explore/service/rabbitmqcluster/logs?from=2026-09-14T15%3A35%3A00.000Z&to=2026-09-14T16%3A46%3A30.000Z&var-ds=loki&var-filters=service_name%7C%3D%7Crabbitmqcluster&timezone=utc&var-lineFilters=caseInsensitive,0%7C__gfp__%3D%7Caos_unit_connection_events&patterns=%5B%5D&sortOrder=%22Descending%22&wrapLogMessage=true).
- [UMH connection events for this Test](https://grafana-prod01.aoscloud.io/a/grafana-lokiexplore-app/explore/service/aos-prod01-umh/logs?from=2026-09-14T15%3A49%3A00.000Z&to=2026-09-14T16%3A46%3A30.000Z&var-ds=loki&var-filters=service_name%7C%3D%7Caos-prod01-umh&timezone=utc&var-lineFilters=caseInsensitive,0%7C__gfp__%3D%7Cf5a9c93b17044f8fa70cec95fdeea72d&var-lineFilters=caseInsensitive,1%7C__gfp__%3D%7Cis_connected&patterns=%5B%5D&sortOrder=%22Descending%22&wrapLogMessage=true).

The final live query used `to=now`; links freeze the approximately equivalent
observation interval for review. They require the existing Grafana access and
do not contain authentication material. No credentials or full message payloads
are retained in this report.
