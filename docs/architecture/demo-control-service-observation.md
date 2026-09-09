<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Control: service catalog and ownership inspection

Read-only P5 tooling increment. It supports the
[accepted SOTA work package](../planning/active/demo-studio-delivery-plan.md#p5-implement-sota-and-backend-plumbing-with-brake-v1)
without creating an SP, Service, Subject, assignment, version or credential.

## Shared CLI/API contract

```bash
democtl service list
democtl service list --profile service-provider
democtl service status SERVICE_UUID --profile service-provider
```

The optional profile is an existing `cloudProfiles` name. With no selector each
configured profile is observed independently. `SERVICE_UUID` comes from the
observed catalog; a title, version UUID, team name, path or endpoint is not an
identity substitute. No implicit Brake/Tire identity is invented.

The transport-neutral API accepts only:

```json
{"domain":"service","action":"list","profile":"service-provider"}
```

or `action=status` with `service_id` equal to a catalog UUID. `profile` is
optional in both. Credential paths, owner overrides, team/vehicle selectors,
arbitrary URLs and mutations are rejected. These are engineering inspection
commands, not a grant allowing team-facing UI panels to choose peer identities.

## Authority and observations

Every profile uses its configured role and optional expected owner when the
existing Aos SDK worker reads `/users/me/`. The credential, raw user response
and reusable token never leave the worker. Only observed role/owner,
expected-owner binding state and seven fixed permission booleans are exposed.
`teamBinding=NOT_CONFIGURED` is deliberate: existing credentials or an SP display
name do not establish the accepted independent Brake/Tire publication mapping.
Mutation authority is `NOT_EVALUATED`; these commands perform no write.

OEM-visible services are labelled `VISIBLE_TO_OEM_NOT_OEM_OWNED`. Every row read
with an SP profile must belong to that authenticated SP, otherwise the section
is unavailable with an ownership error. OEM access is never a fallback that
silently lends publication authority to an SP.

`OperationResult.data` contains:

```text
schemaVersion: 1
source: AOS_CLOUD_ONLY
action: list | status
serviceId: UUID | null
readCompletedAt
profiles: {profile name: profile observations}
problems: [{profile, section, reason}]
```

Profile observations use the existing `{value, source, sourceTimestamp,
readCompletedAt, state, transport, reason}` envelope. List returns `authority`,
`services`, and an OEM-only `providers` directory observation. Status returns
`authority`, exact `service`, `versions`, and `units`. A service detail ownership
or identity failure prevents its downstream reads. Empty lists require complete
successful coverage; missing/forbidden/malformed responses remain unavailable.
Partial pagination retains `INCOMPLETE`, not a false empty catalog.

Collection values have `items` and `coverage: {total, returned, complete}`.
Service projections expose identity, title/codename, SP ID/title and actual
version labels. Version projections preserve exact version ID, raw
`container_state`, creation time and the reported resource-limit flag. Legacy
empty version labels stay empty. Assigned Unit projections expose Unit UUID,
system UID, OEM UUID and Subject UUIDs. Catalog Ready is not instance Running;
the service-to-Unit list is not a runtime or functional-health report.

Descriptions, contacts/email, tokens, environment variables, full service
configuration/default quotas and unrestricted metadata are excluded. Text is
bounded/redacted using the same public Cloud projection policy as Unit reads.
No local VM state, guest SSH or lifecycle journal write occurs.

## Official endpoints and bounds

The implementation uses the [public v11 OpenAPI](https://api.aoscloud.io/api/v11/openapi.json),
observed version 6.1.53. Relevant schemas are `ServiceItemShortSchema`,
`ServiceItemDetailedSchema`, `ServiceVersionItemShortSchema`,
`ServiceUnitListSchema`, and `SpInfoShort`.

- `GET /services/`: accessible catalog. List ownership is `service_provider`.
- `GET /service-providers/`: OEM-visible directory, only with the existing
  `service_providers_list` permission. It is not queried using SP authority.
- `GET /services/{service_id}/`: exact detail; `service_provider_id` and the
  read-only `service_provider` must agree when both are supplied.
- `GET /services/{service_id}/service-versions/`: actual version IDs/states.
- `GET /services/{service_id}/units/`: current service-to-Unit/Subject records.

The live SP endpoint rejected the documented optional `service_provider` list
filter with HTTP 422. The implementation therefore uses the ordinary list route
and verifies ownership on every returned row. There is no automatic failing-call
retry or credential-role switch.

Collections use limit 100, at most eight pages, validated offsets/totals and
duplicate rejection. Changing totals are reported incomplete. Each profile has
one authentication read; list then has at most 16 collection reads, status one
detail and at most 16 collection reads. Each worker has a 60-second overall
budget and 256-KiB sanitized-output limit; the shared HTTP client retains its
12-second/2-MiB bounds. At most four profile workers run concurrently. There is
no timer loop, process control, publication, provisioning or assignment.

The initial live inspection exercised separate OEM/SP catalogs and all three
existing service details, including a two-page 103-version legacy history.
All observed service-to-Unit lists were empty. No existing Brake/Tire service
identity or independent team-SP binding was established. These scoped catalog
facts are not a claim about providers hidden from the configured OEM.
