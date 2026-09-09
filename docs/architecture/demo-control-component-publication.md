<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Demo Control: verification-Test component publication

P2 source increment, 10 September 2026. Implements the publication portion of
the [accepted delivery plan](../planning/active/demo-studio-delivery-plan.md#p2-make-cloud-observations-and-publication-results-truthful).
No live upload, delivery, runtime start or P3 qualification is claimed here.

## Commands and stages

Existing commands/API are retained: `component upload VERSION` and
`component cloud-status VERSION`. No new upload endpoint, wrapper, request flag,
caller-supplied Unit UUID or credential selector is exposed. The current journal
selects the owned Test and recorded response ID; the configured OEM profile
supplies credentials. Approval/addressed-send remain explicit engineering
commands, not automatic fallback steps in the verification-Test flow.

| Action/observation | Result | Mutation/next step |
| --- | --- | --- |
| Upload preflight | Factory/profile, exact OEM component identity, version order and eligible recipients proven | One official multipart `file` POST to `/deployment-bundles/upload/` |
| HTTP 201 with known ID | `publication.stage=ACCEPTED`; journal `upload.state=RESPONDED` | Return immediately; no post-upload wait, no approve, no send |
| Known bundle processing | `PROCESSING`, raw bundle state retained | Observe again explicitly; no mutation |
| Exact bundle `done`, one matching component item, unique real catalog version `Ready` | `READY` | Published, not proof of installation or process startup |
| Bundle/catalog Error or content mismatch | `ERROR`, safe build information and `problems` | Never successful noOp; no blind retry or automatic new version |
| Missing/unknown/ambiguous source evidence | `UNKNOWN` or bounded read failure | Not empty, Ready or successful publication |
| Repeat upload with known response ID | Exact read-only reconciliation; `noOp=true` only when Ready | No archive/guest reread or second upload |
| Lost upload response without exact ID | Reconciliation required | No guessed bundle adoption or resubmission |

`OperationResult.data.publication` contains `stage`, `deploymentId`,
`bundleState`, `versionState`, `versionId`, `buildInfo`, `observedAt` and optional
`reason`. The immediate acceptance response has only the fields known at that
boundary. `observedAt` is read/response time, not an invented Unit event time.
Version status also contains whitelisted `versions`, `deploymentBundles`,
`test` when provisioned, `latestPublishedVersion`, `ownerId`, `source` and
`problems`. Missing Unit component inventory stays null, not an empty list.
Errors produce `PARTIAL`; successful command acceptance does not mean Published.

## Scope and compatibility

The only allowed eligible recipient is the current owned Test. Before Provision
the verification recipient population must be empty. All verification sets are
enumerated because membership in another verification set can affect delivery.
A second set containing the same Test is allowed; a different member blocks
publication conservatively, without guessing model compatibility. Ordinary
Production sets and Units are neither required nor changed. The Test may be
Offline: host publication authority and guest connectivity are different facts.

Before Provision v1, v2 and v3 profile releases are allowed, including connected,
running initial-Manual preparation and the warehouse scenario. A previous owned
publication must be Ready before the next release. After Provision its version
must also be reported installed on Test, with no pending update/error. The UI
still must not infer a running VDP process from Cloud installation state.

The small `.local/factory` manifest is checked against its owned journal digest,
image SHA/version/path/format and the package provenance. Its `sourceSelector`
feeds `ImageCatalog.component_support(selector, sha256, component_type,
required_paths)`. The catalog must supply the validated producer declaration.
No image bytes or guest schema are read during publication. Missing/conflicting
declarations block publication; there is no hardcoded .31 exception. The source
producer/retained-artifact declaration migration remains a separate integration
gate. Tests use an explicit declared fixture, not an invented compatibility claim.

## Documented API and read bounds

Source: [OpenAPI v11 / 6.1.53](https://api.aoscloud.io/api/v11/openapi.json).
The [verification-set documentation](https://docs.aosedge.tech/docs/quick-start/create-unit-set)
states that a provisioned member receives updates without additional approval.
The [deployable item types](https://docs.aosedge.tech/docs/aos-core/deployment-flows/sota-vs-fota)
distinguish `component` FOTA content from service/layer content.

- `GET /components/{fixed-component-id}/` proves component codename and OEM.
- `GET /components/{id}/versions/` supplies real version identity/readiness/order.
- `GET /deployment-bundles/` finds the exact known upload ID. The detail route
  supports DELETE, not GET. Without a response ID, collection content is used
  only to reject an existing conflicting release, never to adopt one.
- Upload preflight adds `GET /unit-sets/?is_validation_set=true` and each
  returned set's `/units/` membership list. Schema/filter mismatch blocks.
- With a provisioned Test, `GET /units/{owned-id}/` checks exact UID, membership,
  lifecycle and installed/pending component/error state; Online is not required.

Pages use limit 100, up to eight pages per collection, with offset/total and
duplicate checks. Exact ID lookup stops once that primary key is observed.
Recipient discovery permits up to 16 sets, and the whole snapshot has at most
24 HTTP reads beyond the existing worker authentication. Limits or incomplete
coverage block; they do not silently authorize. Existing per-read 12-second,
2-MiB and worker 90-second/256-KiB bounds remain. No long polling, fake timer
completion, campaign scan or verification-batch read occurs in this path.

The current-run journal stores the upload intent before POST, exact accepted
ID, digest, OEM and recipient coverage. New receipts are marked
`publicationPath=VERIFICATION_TEST`. Retirement can confirm their exact Ready
publication without an approve record; historical engineering receipts retain
their existing batch proof. Processing/error/unknown outcomes stay unresolved;
failed-update recovery is not invented by this increment.
