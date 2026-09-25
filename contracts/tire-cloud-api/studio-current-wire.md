<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Tire current-Test administrative wire — implemented v1.1 demo

Inspected 24 September 2026 at the Tire backend revision pinned by
`demo-v1.1`. This is an as-implemented description, not a new API version.
The legacy `cleanup-preview.schema.json` and profile's `exactSystemUidCount: 2`
do **not** fully describe the current response. Their historical fixtures and
digests remain unchanged. See [contract maintenance status](../implementation-status.md).

Sources: [context validation](../../../tire-health-cloud/src/context.mjs),
[private HTTP handler](../../../tire-health-cloud/src/main.mjs),
[store/cleanup transaction](../../../tire-health-cloud/src/store.mjs) and
[product/selector tests](../../../tire-health-cloud/test/product.test.mjs).

## Context and selectors

Context is a closed object with `schemaVersion: 1`, `contractVersion: "1.0.0"`,
`source: "CURRENT_RUN_PROVISIONING_JOURNAL"`, required `testUnit` and optional
`productionUnit`. Each Unit has exactly `systemUid`, `unitRole` and
`userFacingRole`. Internal roles are `VALIDATION` / `PRODUCTION`, display roles
`Test Vehicle` / `Production Vehicle`. Identities must be distinct; missing,
duplicate-key, malformed, oversized or unknown context is rejected.

Cleanup accepts exactly `[currentTestUid]` or all current context UIDs (one or
two). It rejects empty, duplicate, foreign and Production-only selectors.
The selector is checked against current context and sorted before use; a valid
UID grammar alone never grants cleanup authority.

## Transport and closed requests

Admin POSTs are on a private mode-0600 Unix socket, not the guest-ingestion or
browser TCP route. Requests are limited to 4096 bytes and use strict JSON.

| Operation | Path suffix under `/api/v1/tire/admin/` | Exact request fields |
| --- | --- | --- |
| Preview | `current-run/cleanup-preview` | `schemaVersion`, `contractVersion`, `systemUids` |
| Execute | `current-run/cleanup` | Previous fields plus `confirmationToken` |
| Storage proof | `storage/empty-proof` | `schemaVersion`, `contractVersion` |

All three requests require schema 1 and contract `1.0.0`; extra fields fail.
Demo Reset is a different endpoint/protocol and does not delete this history.

## Response and transaction

Preview returns `schemaVersion: 1`, sorted `systemUids`, `recordCounts`,
`recordSetSha256`, `nonmatchingRecordCounts`, `nonmatchingRecordSetSha256`,
`confirmationToken` and `expiresAt`. Unlike the request, it has no
`contractVersion` field. Tokens last 60 seconds and at most 16 previews are
retained. Token contents are private and must not be copied into audit evidence.

Both count objects cover these ten categories: `messages`, `assessments`,
`events`, `advisories`, `functionStatus`, `quarantine`, `resetProducers`,
`resetCommands`, `functionObservations`, `functionObservationConflicts`.

Execution revalidates context, exact selector/token/expiry and both matching
and nonmatching record-set digests. Changed data is `STALE_PREVIEW`; no blind
retry is valid. One SQLite transaction deletes selected rows (including reset
and observation records), proves zero selected rows and unchanged nonmatching
digest, then consumes the preview token.

Success returns schema 1, contract `1.0.0`, `state: "CLEANED"`, `systemUids`,
`deletedRecordCounts`, `remainingRecordCounts`, `nonmatchingRecordCounts`,
`nonmatchingRecordSetSha256` and `completedAt`. Storage proof separately
reports database schema 4 and `EMPTY` / `NONEMPTY`, counts and observation time.
Neither response retires Cloud identity, deletes VM files or touches Brake data.

The source tests cover Test-only/dual context, selector rejection, stale
preview, peer preservation and empty-store behavior. Passing the legacy
two-UID fixture alone does not cover this current handler.
