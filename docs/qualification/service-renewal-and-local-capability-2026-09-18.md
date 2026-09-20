<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Service interruptions and the P2 local-capability boundary

Date: 18 September 2026. Status: diagnosis, bounded P2 host evidence and
fixture-verified Presenter compatibility; not a deployed fix or complete
P1/P2 acceptance.

The operator requested classification of remaining interruptions before P2.
The preserved Test still uses Factory .35, VDP V3 / 79.0.0, Brake V3 / 59.0.0
and Tire V1 / 34.0.0. No VM, service, source or Cloud lifecycle operation,
package publication, model reset or security-policy change was performed for
this investigation. Existing source and pending UI changes are preserved.

## 1. Recurring Brake interruption is credential renewal, not steering

The previous [moving-source proof](preserved-test-motion-and-results-2026-09-18.md)
covered 4,798 coherent frames without invalid steering pairs. The new bounded
inspection correlates service journal transitions with token-file modification
times only. No token contents, claims or credential hashes were inspected,
exported or retained by the diagnostic probe.

| UTC on 18 September | Token file replaced | Brake reports input unavailable | Input recovered; advisory unproved | Fully operational |
| --- | --- | --- | --- | --- |
| 19:19 | 19:19:43.128721 | 19:19:43.178290 | 19:19:44.308736 | 19:19:46.557719 |
| 19:22 | 19:22:43.322512 | 19:22:43.328281 | 19:22:44.491557 | 19:22:47.156522 |

Earlier captured transitions recur around 19:07:43, 19:10:43, 19:13:43 and
19:16:44. Recovery at 19:11:03 follows the 19:10:43 transition by about
20 seconds, but analytics had already recovered at 19:10:45. The longer
interval is not evidence of twenty seconds without telemetry.

This matches the accepted [authorization contract](../../contracts/kuksa-current-demo-authorization/README.md):
300-second TTL, renewal at 180 seconds, mandatory subscription recreation
with the new token. In `brake-health-service/src/runtime/grpc_main.cpp`:

1. Both telemetry and advisory watchers cancel their RPCs on token replacement.
2. Telemetry disconnect aborts an incomplete capture, retains model/outbox
   state and logs `KUKSA_DATA_UNAVAILABLE`.
3. Both outer loops add an unconditional one-second retry delay, even for
   successful planned renewal rather than a failed request.
4. The advisory loop clears its per-session attempted-request correlation.
   A cached Gateway result may be reconciled, but is deliberately not promoted
   to proof of a new request/reply in that session. Readiness can therefore
   remain `VISS_OR_GATEWAY_UNAVAILABLE` until the next legitimate request.

The 15-minute provider journal query returned 335 rows with none of the
selected source-stale, invalid-value or readiness-transition labels. This is
a bounded negative observation, not an all-history/no-error assertion. The
original query used the wrong systemd name and returned zero rows; it was
corrected to `aos-vehicle-data-provider.service` before drawing this conclusion.

The source control observation at 19:30:17 UTC remained Autopilot/ready with
17,852 heartbeats and zero command timeouts, ownership timeouts or disconnects
in this source generation. Earlier-generation control failures are not thereby
explained or qualified away.

### Correction boundary

Keep immediate credential invalidation, fresh IAM lookup, mandatory reconnect,
expiry and actual sample-gap handling. Do not lengthen leases, preserve an
unauthorized old stream, fabricate an advisory request or count a cached ACK
as a new one. The authorized service-observability work needs to separate
planned reauthentication, current input and unproved advisory delivery.
Removing unnecessary retry backoff on a classified successful replacement is
a targeted candidate; it still needs real TLS/gRPC renewal and negative tests.
It was not implemented or deployed by this diagnosis.

## 2. Tire has a separate diagnostic ambiguity

Tire's source has the same token-change cancellation and one-second reconnect
delay. Its logger deduplicates by event type: connection loss and input-ready
use different event keys. Identical subsequent renewals can therefore be
absent from its journal. Absence of repeated Tire log events cannot establish
absence of reconnects.

A separate host executable linked against the existing Tire runtime library
reproduced this sequence with synthetic fixtures and isolated temporary state:

1. Create a valid request and accept its correlated Gateway ACK.
2. Create the next legitimate lease request using the same producer epoch.
3. Receive the previous valid ACK again.
4. `advisory_fact` raises `UNCORRELATED_STATUS`; the live gRPC catch-all maps
   that exception to `READINESS_CHANGED / NOT_READY / GATEWAY_STATUS_INVALID`.

Discarding an uncorrelated result is correct; describing it as overall input
failure is misleading. Malformed/current-request errors, superseded ACKs,
analytics readiness and advisory application need independent treatment.
The historical 19:05:03 Tire event did not retain enough correlation detail
to establish that this exact sequence caused that individual event. The
reproduction proves the mechanism, not that historical attribution.

## 3. P2: existing inputs cannot identify the active local profile

New executable characterization covers distinct committed releases with V1,
V2 and V3 capability lists. The existing projector validates each artifact,
yet produces **byte-identical** five-field public metadata and reports a no-op
for the second and third projection. The shared family contract is `1.0.1`.
Neither a reread nor a more frequent refresh can recover information that
the input does not contain.

The Factory KUKSA catalog is built with all V1/V2/V3 telemetry and advisory
leaves independently of the active provider. Catalog existence is therefore
not sufficient either. Fresh valid values prove available inputs, but missing
values alone cannot distinguish a lower profile from an unavailable publisher.

The existing cold projector creates stable empty resource directories when
no first committed component exists; its startup stage is `DEFERRED` without
preventing native SM startup. Both current service bootstraps read metadata
and public trust before their long-running credential loop. A missing initial
file takes the outer failure exit; automatic recovery of an already-running
service does not prove early-install recovery. No live early-install failure
was induced on the retained Test.

Both service reader tests now use the real family dimension (`1.0.1`) and
explicitly reject proposed profile/release/capability fields in legacy input.
This prevents accidental schema widening; it does not add a local interface.

### Bounded decision — option A accepted

- **A, recommended minimal path:** Presenter uses native Cloud and exact
  package binding for installed profile/version compatibility. Services report
  observed input/capability readiness and automatically recover locally;
  absent data remains unknown/waiting rather than a guessed incompatible
  profile. This explicitly relaxes the earlier requirement that a service's
  own local evidence distinguish an unsuitable active profile from a suitable
  but silent publisher. No new local profile transport is introduced.
- **B:** retain that exact service-local distinction, then approve and freeze
  a versioned local capability contract and activation/invalidation boundary.
  Preserve old readers, offline operation and Cloud-only Presenter inventory.
  Do not silently revive the rejected timer/expiry proposal or choose an
  implementation hook before the contract review.

The operator answered **A** in this conversation. A is the accepted boundary;
B is not authorized. This closes the mechanism decision, not the early-start,
renewal or complete FOTA qualification. Contracts and the work packet have
been reconciled with A. Service recovery and new function observations follow
the existing consumer-first P3/P4 sequence.

## 4. Option-A Presenter implementation

The source adds a shared installation-evidence validator and the accepted
software compatibility matrix in the existing service detail dialog. The
validator rejects unknown profiles, wrong release strings and mismatching
Cloud artifact IDs. Pending releases are not compatibility inputs. The
service's installed release is mapped through the existing service release
records; an unresolved service profile remains unconfirmed.

Compatibility is explicitly separate from receiving input, computing an
assessment and applying advisory. Stale parent observations or stale profile
bindings are labelled last known. A stale binding cannot advance the guide
to completed software progress, even if the parent Cloud read is current.
The existing Cloud reader and dialog refresh are reused; there is no new
guest probe, API, timer, lifecycle action or publication dependency.

Browser fixtures cover an open dialog's VDP V2-to-V3 compatibility transition,
pending-versus-installed evidence, stale/unknown/mismatching artifacts, both
service teams and GET-only reads. Service dialogs fit without internal scroll
at 1280x720, 1728x1117 and native-panel 1118x1124. Screenshots at compact and
native-panel sizes were visually inspected. Fixture labels are not live
vehicle or backend evidence.

## Executed gates and exclusions

- Demo Control: **37** service-input tests, **8** installed-profile tests,
  **29** Cloud-observation tests passed.
- Platform: **6** catalog-schema and **14** provider tests passed.
- Brake: targeted native-reader rebuild and all **7 CTest groups** passed.
- Tire: targeted native-reader rebuild and all **4 CTest groups** passed.
- Tire superseded-ACK reproduction: compiled with warnings as errors and
  reproduced the exception path using synthetic host-only fixtures.
- Presenter: **176 unit tests across 19 files**, **103 browser tests**,
  TypeScript and isolated Vite production build passed. Build output is
  `/private/tmp/aos-presenter-p2.WdZ7lq`; the running Presenter assets were not
  replaced. Browser fixtures use port 18070, not the live demo's port 18080.

The non-UI gates total **94 Python tests**, **11 CTest groups**, and one
bounded host reproduction. The CTest builds do not include the real gRPC
product executable.
No revised service binary was built for the VM, no end-to-end token-rotation
fix was qualified, and no full version-transition/early-install matrix passed.

Transient read-only probe and reproduction source/binary are retained under
`/private/tmp/aos-input-interruptions.dBWqH8`; no guest debug state was created.
Existing warm build directories and immutable Factory/overlay remain intact.
No commit or push was made in this increment. Changes remain in the existing
working trees with unrelated pending changes preserved. Source correction of
service renewal, ACK classification and early bootstrap recovery is still
P3/P4 work, not claimed complete by the new Presenter display.
