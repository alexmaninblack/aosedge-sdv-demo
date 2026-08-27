<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# R8 — AosEdge Native Logging

Status: **research pass complete; implementation not authorized**.

## Decision scope

This workstream determines what AosEdge logging provides today, how the demo
uses it through AosCloud, and which evidence belongs in operational logs rather
than the Engineering or Function dashboards.

## Evidence summary

| Finding | Classification |
| --- | --- |
| Aos service instances run as systemd-managed `crun` containers and their stdout/stderr is available in the system journal. | **PROVEN** |
| The Service Manager supports Cloud-requested instance, crash, and system logs with time filtering, compression, splitting, and Cloud transmission. | **PROVEN** |
| AosCore sends resource monitoring and journal-derived error alerts to AosCloud through the Communication Manager. | **PROVEN** |
| AosCloud UI supports requesting and downloading service and Unit logs. | **PROVEN** |
| AosCloud UI supports explicit Unit, service-instance and crash-log requests and downloadable results. | **PROVEN** |
| AosCloud persists downloaded Unit logs as encrypted BLOB objects; the current API exposes separate Unit- and Service-log request list, create, detail, download and delete operations. | **PROVEN** |
| The current API contract states that deleting a log request also deletes its related files. | **PROVEN** |
| Live role enforcement, request progress/failure behavior, exact Cloud retention duration, deletion effect and offline behavior in the qualified demo tenant require qualification. | **REQUIRES EXPERIMENT** |

## Product-native logging path

```text
provider/service stdout and stderr
  -> systemd journal on the AosVM
  -> Aos Service Manager log provider
  -> on-demand Cloud log request
  -> compressed log parts over Communication Manager
  -> Cloud-retained AosCloud request record and downloadable archive
```

This path is different from two related paths:

- resource monitoring periodically reports CPU, RAM, disk, and network usage;
- journal alerts continuously forward selected error-priority entries as
  structured Aos alerts.

An informational `provider ready` line is therefore available in a requested
log archive but is not automatically a real-time Cloud alert.

## Accepted demo boundary

The demo uses only the native AosEdge logging path. No demo-owned collector,
export bridge, secondary log store, or separate log dashboard is introduced.
The later D4-014 allocation refines this research boundary. Role-scoped
dashboard adapters use supported AosCloud APIs to:

1. create an explicitly confirmed OEM Unit system/VDP request or matching
   SP1/SP2-owned service-instance/crash-log request;
2. poll the authoritative Cloud request state;
3. present or download the completed Cloud-retained result without retaining
   an independent dashboard archive.

The OEM Software Delivery Dashboard owns Unit-log presentation; each Function
Dashboard owns only its Service Provider's Service-log presentation. Private
client credentials remain behind fixed backend/helper allowlists and never
enter browser code. If a requested operation is unavailable through the
qualified API, the original AosCloud UI remains the technical drill-down.

## Required operational events

Provider and service logs should be English, structured as one compact record
per event, and include stable correlation fields where available:

```text
timestamp
level
event_name
unit_pseudonym
run_id
component_or_service_id
component_or_service_version
contract_version
event_id
result
reason_code
```

The minimum event catalogue is:

| Component | Events |
| --- | --- |
| Inbound provider | start, configuration accepted, KUKSA connected, VISS connected, ready, source stale/lost, recovery, contract rejection, stop |
| Outbound provider | start, target received, policy accepted/rejected, VISS Set result, Gateway status timeout, reconnect, stop |
| Brake Health service | start, KUKSA subscribed, model loaded, event detected, inference completed, advisory requested, queue pending/acknowledged/overflow, backend disconnected/reconnected, stop |
| Demo orchestration | run start/end, stage selected, expected artifact graph, acceptance result, reset result |

Routine 30 Hz samples do not belong in operational logs. Function telemetry
and prediction records go to the Function Backend; Gateway signals go to the
Engineering Dashboard; software lifecycle state remains in AosCloud.

## Privacy, security, and retention

Never log private keys, bearer tokens, `AOS_SECRET`, PKCS#12 paths, certificate
subjects, unrestricted request bodies, public VINs, or raw high-rate telemetry.
Use pseudonymous Unit and run identifiers suitable for the demonstration.

The native-log dashboard and any bounded temporary download handling must:

- enforce an event and field allowlist;
- redact before presentation;
- cap record and archive sizes;
- preserve explicit validation/demonstration Unit identity;
- treat the Cloud request record and related archive as authoritative while
  retained by AosCloud;
- never describe the Cloud-retained result as an indefinite archive unless the
  deployed Cloud retention policy is separately qualified;
- remove any temporary Mac-local copy after bounded presentation/download use;
- record the source log request ID and source time range;
- expose data age so a downloaded archive is not presented as a live stream.

## Dashboard role

The role-matching dashboard's native-log view is supporting troubleshooting
evidence, not the main narrative. For a demo stage it should answer only:

1. Did the expected provider or service start and report ready?
2. Did source loss, policy rejection, offline queueing, or reconnect occur?
3. Which exact component/service/run produced the event?

The primary visible proof remains CARLA, the Engineering Dashboard, the
Software Delivery Dashboard, and the Function Dashboard.

## Required experiments

1. Exercise the proven Unit- and Service-log API operations end to end: create,
   poll, download and delete the request with its related files.
2. Confirm live permissions for a dedicated read/log-request identity and separate
   read-only dashboard identity.
3. Confirm eventual availability and factual progress/failure state from an
   informational service log line to a downloadable Cloud archive; do not use
   retrieval duration as a vehicle-performance KPI.
4. Repeat across temporary Unit/Cloud disconnection and establish whether the
   journal and requested time window preserve the record.
5. Verify archive format, compression, ordering, timestamps, duplication, and
   maximum part size.
6. Determine whether the deployed Cloud retention policy can be exposed; the
   current API cannot, so display that limitation. Prove explicit deletion and
   verify no independent archive plus bounded temporary removal.
7. Prove that high log volume cannot exhaust the Unit, AosCloud request path,
   dashboard backend, or demo laptop.

## Current architecture decision

The scenario's wording that AosEdge provides system/service log collection,
Cloud transmission and Cloud-retained downloadable results is supported. The
accepted architecture uses the AosCloud request record and related stored
archive as authoritative while retained. D4-014 allocates Unit system/VDP logs
to the OEM Software Delivery Dashboard and Service-owned logs to the matching
Function Dashboard. A separate pipeline or store is not part of the demo.
`Permanent` in the storage architecture is a persistence class, not a claim
of unlimited retention.

## Sources

- [AosEdge Monitor a Service](https://docs.aosedge.tech/docs/how-to/advanced-service-operation/monitor-service)
- [AosEdge getting logs and service instance status](https://docs.aosedge.tech/docs/how-to/troubleshooting/getting-logs)
- [AosCore Monitoring and Observability](https://docs.aosedge.tech/docs/aos-core/monitoring/)
- [AosCore Common Infrastructure](https://docs.aosedge.tech/docs/aos-core/architecture/common-infrastructure/)
- [AosCore alerts and thresholds](https://docs.aosedge.tech/docs/aos-core/monitoring/alerts-and-thresholds)
- [AosCloud storage components](https://docs.aosedge.tech/docs/aos-cloud/components-view/storage-components)
- [AosCloud API v11](https://api.aoscloud.io/api/v11/docs#/)
- [AosCloud audit actions](https://docs.aosedge.tech/docs/reference/misc/audit-actions)
- [Current Demo Scenario 2.0](../../demo/staged-post-sop-brake-health-demo-scenarios.md)
