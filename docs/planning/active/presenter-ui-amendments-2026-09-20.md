<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter UI amendments — 20 September 2026

Status: all three changes and the two presentation clarifications accepted;
final implementation plan accepted; implemented and live-qualified.
The operator deferred the remaining live qualification checks and requested
discussion and recording of further UI changes. Record each agreed change here;
the subsequent explicit start instruction closes that discussion-only boundary.

Execution order, technical gates and acceptance are consolidated in the
[final implementation plan](work-packets/presenter-ui-amendments-implementation.md).
The subsequent operator instruction authorized work through the plan's gates.
Results: [qualification report](../../qualification/presenter-ui-amendments-qualification-2026-09-20.md).

## Change 1 — Reset scenario on the backend summary card

Decision: accepted. Implementation and live qualification: passed.

- Move the existing per-service Reset action from the backend detail popup to
  the corresponding Brake or Tire backend summary card on the Vehicle screen.
- Label the secondary action **Reset scenario**. Keep it visually and
  interactively separate from opening backend details; clicking Reset must not
  also open the popup.
- Start the action with one explicit click, without an additional confirmation
  dialog. The card already identifies the selected service.
- Immediately display progress on that card and prevent duplicate submission
  while the operation is pending. Show success only after the existing
  correlated vehicle/Gateway CLEAR confirmation. Preserve explicit failed,
  expired and uncertain outcomes; do not retry a mutation blindly.
- Keep existing availability, connectivity and lifecycle guards, with a clear
  explanation when the action is disabled. Moving the action does not bypass
  server-side checks or alter the reset protocol, lifetime or authority.
- Reset only the selected service's demo scenario. Backend history and the
  other service are preserved; Reset is not a service restart or vehicle repair.
- Remove the action button from the detail popup. Retain last-reset information
  and history there.

This accepted target changes the earlier UI confirmation/placement behavior.
The implementation, interaction specification and affected tests are now
reconciled. Historical mockups are preserved, not silently overwritten.

## Change 2 — One Disk resource selector

Decision: accepted. Implementation and live qualification: passed.

- In Aos Cloud monitoring / Resources, retain one **Disk** selector and remove
  the separate **Disk (alternate)** selector.
- Keep selection between the supported `usedDisk` and `disk` parameters inside
  the observation/presentation logic, not as an operator choice. The current
  fallback can cause both existing selectors to display the same `disk` samples.
- Resolve alternatives per Node/service/Subject/instance/partition, not once
  for the whole response. A controller value must not hide a service or another
  partition reported only by the other parameter. Preserve source and quality;
  do not silently select a conflicting alternative.
- Show the reported partitions, such as `states`, `storages` and `var`, within
  the single Disk view, retaining their scope and source/sample identity. These
  are not two physical disks or separate used/free-space controls.
- Preserve explicit unknown, stale and unavailable states. Do not combine
  alternative parameters into a total, invent units or reinterpret their values
  as free space, capacity or percentages without a verified metric contract.
- Cover primary-parameter, fallback and missing-data paths in the affected UI
  tests when implementation begins; no Cloud API contract change is approved.

<a id="change-3-cloud-cpu-and-memory-history"></a>

## Change 3 — Cloud CPU and memory history

Decision: accepted. Implementation and UI/live qualification: passed.

- Add two compact graphs to the main Aos Cloud card: **Controller CPU ·
  DMIPS** and **Controller memory · MiB**, showing the last five minutes,
  latest measured value and sample age. Keep the existing detail-popup entry
  and connectivity/software/update facts; resource freshness must not refresh
  the age of those independent observations.
- In the Resources popup, show separate Domain Controller, Brake Health and
  Tire Health rows, each with CPU and memory graphs and current values, using
  the same time axis. Keep controller and service scales visibly identified;
  do not flatten service usage against the much larger controller range.
- Retain blue platform, purple Brake and teal Tire identity accents. Keep the
  main Brake/Tire backend cards focused on service results, not resource usage.
- Use native Aos Cloud monitoring only. Latest samples come from
  `GET /api/v11/units/{item_id}/monitoring/`; historical series come from
  `GET /api/v11/units/{item_id}/monitoring/dashboard/`. No new guest collector,
  SSH monitoring loop, VM rebuild or AosCore change is part of this amendment.
- Preserve Node, service, Subject and instance identity within the selected
  Cloud/tenant/current Test. The API measures service instances, not a generic
  installed-package total. Do not relabel another instance's historical data
  or assume every historical point belongs to the currently installed version.
- CPU stays in DMIPS. Format verified byte memory as MiB/GiB instead of long
  raw integers. Usage is not a package quota; controller usage is not the sum
  of Brake and Tire. Do not add controller and instance values or invent a
  percentage without a verified capacity/quota denominator.
- Plot Cloud sample timestamps, not UI refresh times. Deduplicate repeated
  observations of the same point. Keep missing/stale/offline intervals honest:
  retain last-known history and age, do not invent samples, zero load or
  continued live measurements when External Network is off. No fresh Cloud
  sample is not proof that a local service stopped.

### Accepted presentation and refresh clarifications

- Resources navigation is **CPU & Memory / Disk / Inbound / Outbound**.
  CPU & Memory contains the three controller/Brake/Tire rows. The other
  resource views preserve their existing scope and partition information;
  this change does not remove traffic monitoring.
- After more than five minutes without new measurements, the current
  five-minute graph may be empty. Keep the last value and its age separately.
  Retained historical graphs must show their actual dated time range; never
  shift old points toward the present to make the chart appear live.
- Use asynchronous resource polling with a nominal 30-second cadence and one
  shared read model for the card and popup. Do not overlap identical reads or
  block controls while awaiting Cloud. Keep current connectivity, software,
  operation and functional-backend refresh policies independent and unchanged.
  The documented Unit-to-Cloud WebSocket is not an OEM dashboard subscription.

The operator accepted both presentation choices after the compatibility audit.
The refresh approach follows the official
[Unit Dashboard documentation](https://docs.aosedge.tech/docs/how-to/tutorials/device/use-unit-dashboard),
which describes separate Unit-status and monitoring refresh intervals. Its
defaults are not evidence of the current VM's configured reporting period.

Read-only feasibility proof on 20 September 2026: the selected staging OEM
credential has `units_monitoring_dashboard`; the current Test returned CPU
and RAM history for its controller and both Brake/Tire instances. The
09:42 UTC observation contained 25 points per series over approximately
14 minutes. This proves current availability, not a guaranteed retention or
sampling interval. The existing Presenter reads only latest measurements and
collapses samples to the newest per identity; historical adaptation and chart
rendering remain to be implemented. Test the actual response shape as well as
the documented schema: staging returned `services` as a keyed object rather
than the array described by OpenAPI. Keep reads bounded and handle missing
history permission/data explicitly.

References: [Aos monitoring overview](https://docs.aosedge.tech/docs/aos-core/monitoring/),
[Cloud OpenAPI](https://api.aoscloud.io/api/v11/openapi.json),
[CPU units](https://docs.aosedge.tech/docs/aos-cloud/components-view/dmips-and-cpu-usage),
[Node RAM accounting](https://github.com/aosedge/aos_core_cpp/blob/main/src/sm/monitoring/nodemonitoringprovider.cpp),
[instance RAM accounting](https://github.com/aosedge/aos_core_cpp/blob/main/src/sm/launcher/runtimes/container/monitoring.cpp).

This accepted target supersedes the earlier “No CPU/RAM on the summary”
requirement in Presenter slice V. It does not change the running UI yet.
Reconcile the interaction specification and cover history, identity isolation,
units, repeated samples, stale/offline gaps and permission/error states in the
affected tests when implementation is explicitly started.

## Decision closure

No product decision remains open for these three changes. Implementation and
scoped automated/live qualification are complete; the
[qualification record](../../qualification/presenter-ui-amendments-qualification-2026-09-20.md)
states the evidence and remaining handoff boundaries. The subsequent disk and
traffic follow-up is explicitly recorded below; no other UI change is assumed.

## Follow-up — verified disk and traffic presentation

Accepted by the operator after read-only diagnosis on 20 September 2026.
Implement only the observation-unit metadata and Presenter presentation:

- Disk usage uses verified bytes, formatted as B/KiB/MiB/GiB; explain that
  rows are used space in Aos partitions, not physical disks or free capacity.
  Show the four current controller partitions together, preserving instance
  scope, aliases, missing values and conflicts.
- Network readings use the same verified byte formatting. Describe accumulated
  daily accounting volume, not transfer speed. Retained older samples must not
  be labelled today's measurements; use `Received/Sent · daily total` with
  source-day context instead.
- Explain the native private/local-network exclusion and that local backend
  traffic is not counted. Preserve real zero; it is not proof of no delivery.
- Defer any public/test backend network, forwarding or address changes.
  No AosCore, VM, service package, network, Cloud or lifecycle change.

Verification and provenance are in the
[Cloud observation contract](../../architecture/demo-control-cloud-observation.md#monitoring-semantics).
