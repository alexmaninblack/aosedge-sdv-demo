<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Presenter UI amendments — qualification

Date: 20 September 2026. Status: implemented, activated and scoped local/live
qualification passed. Ready for operator visual review.

Scope: [approved implementation packet](../planning/active/work-packets/presenter-ui-amendments-implementation.md).
The existing staging Test and factory .36 are preserved. No AosCore, VM image,
service package, authentication, Cloud deployment or Production changes were
made. No publication, retirement, record deletion or public push is included.

## Delivered behavior

- Separate one-click **Reset Driver Advisory** and detail actions on each service card.
  Only backend scenario Reset skips confirmation; it keeps request IDs,
  native authorization, serialization and uncertain-outcome protection.
- Card and popup share submitting/pending/uncertain/CLEAR evidence. A completed
  job alone is not CLEAR. Delayed old commands cannot revive an earlier state.
  Routine background reads do not flicker an otherwise available Reset action.
- One Disk navigation item resolves aliases by scope and partition. Zero,
  conflict, incomplete and unverified-unit states remain explicit.
- Five-minute controller CPU/RAM graphs on the Cloud card; separate Controller,
  Brake and Tire rows in Resources. CPU is DMIPS, verified RAM is bytes displayed
  as MiB. No node/service addition, invented percentage or host-Mac metric.
- Latest readings and dashboard history use independent, bounded 30-second
  readers. Slow history cannot block latest readings, backend evidence or Reset.
  Graphs use source instants, not read time, and retain real gaps/ages.
- Existing miniatures, team colors, architecture anchors/arrows and native-left
  layout remain. Compact views scroll internally when needed; text and actions
  remain reachable instead of clipping the lower rows.

## Source and contract proof

The fixed current-Test history read uses the selected OEM context and existing
Unit ownership checks, plus `units_monitoring_dashboard`. Both documented
service arrays and the observed keyed service object are validated. Counts,
payload and process duration are bounded; malformed/forbidden data is not zero.

The platform's deployed OEM frontend applies its IEC byte formatter directly
to both latest RAM and history RAM. See the authoritative source link and
provenance in the [observation contract](../architecture/demo-control-cloud-observation.md#monitoring-semantics).
The live read returned six CPU/RAM series, 150 points over about fourteen
minutes; this is observed coverage, not a retention promise. The implementation
keeps the proven parameter-free dashboard read rather than depending on an
additional query contract.

Live verification found an additional latest/history shape difference: latest
samples include `measurementType`, history does not. CPU/RAM identity now uses
the actual Node/service/Subject/allocation tuple; metadata cannot falsely create
two controllers. Disk preserves its separate partition/measurement identity.
A dedicated regression covers this difference.

## Automated qualification

- Presenter: typecheck, production build, unit and browser regression suites.
- Python: Cloud observation/authority suite; fixed reader dispatch; bounded
  history normalizer; Presenter HTTP and protected-operation suites.
- Documentation navigation/links and whitespace/diff checks.
- Fixtures cover array/keyed histories, zero/null/conflicts, unzoned/foreign/
  malformed input, count bounds, missing permission, old replies, changed scope,
  hidden views, hung history, retained latest data, Reset expiry/uncertainty,
  release/run changes, keyboard submission, duplicate guards and other mutation
  confirmations. Compact/native geometry and service-arrow endpoints are checked.

Final gates: **314 Presenter unit tests**, **135 browser tests**, **118 affected
Python tests** (77 Cloud/reader, 4 history, 37 Presenter/operations), typecheck,
production build and documentation quality gate all passed. The documentation
gate checked 246 Markdown documents, 658 stable identifiers and 38 diagrams.
Fixture tests are not represented as a full demo lifecycle qualification.

## Timing observations

Three isolated browser runs deliberately held the history request open. Each
performed exactly one Reset submission; opening details created no new observer.
The existing post-operation refresh performed one extra latest read while the
hung history remained coalesced.

| Fixture measurement | Minimum | Median | Maximum |
| --- | ---: | ---: | ---: |
| Keyboard Reset to visible submitting state | 18 ms | 20 ms | 26 ms |
| Details click to visible popup | 69 ms | 70 ms | 79 ms |
| Refresh of correlated CLEAR to visible acknowledgement | 70 ms | 91 ms | 99 ms |

These include local browser-driver overhead. They are not Cloud or vehicle
latency guarantees. Automatic backend visibility additionally depends on the
existing five-second observation phase. Resource visibility depends on native
Cloud delivery and the thirty-second reader phase; repeated identical source
timestamps do not create new chart points.

## Live checks (UTC)

- The pre-change Presenter build was
  `3fb66df26991ecb4c8a0e92f2e6e008a77c7645a0db029b774f806734bfaddcb`.
  The compatible compiled UI and host adapter sources were retained outside Git
  for rollback. Only the idle Presenter host was restarted for the new route.
- Brake Reset submitted at 10:49:22.912 and accepted/completed by Demo Control
  at 10:49:23.030; matching Gateway CLEAR was reported at 10:49:28.
  A UI click plus immediate state read took 226 ms and showed Resetting, not
  success. Tire remained unchanged.
- Tire Reset likewise showed immediate Resetting (236 ms including state read),
  with matching CLEAR at 10:50:13. Both native advisories showed Monitoring.
- An existing real CARLA brake maneuver produced a new Brake result after CLEAR.
  Earlier backend records remained available; no synthetic input was introduced.
- External Network OFF requested at 10:51:40.473. Cloud later reported Offline;
  this was read from Cloud, not inferred from request failure. Resources aged as
  last known. Tire's last backend function receipt stayed at 10:51:38.092 across
  later successful backend reads, including 10:54:02.816.
- An existing Tire maneuver completed while external network remained OFF.
  Native telemetry remained LIVE and local advisories advanced from Monitoring
  to Inspection recommended. This is independent local execution evidence,
  not an inference from Cloud's retained instance status.
- Live Resources showed separate controller/Brake/Tire graphs. Disk retained
  node partitions and both service scopes, including measured zero; there was
  no second Disk button or invented alias total.

- At 10:57:14 (334 seconds after OFF), all six current five-minute graphs were
  empty. Last nonzero CPU/RAM values remained outside the plot with six-minute
  source ages. No artificial zero or shifted historical timeline appeared.
- External Network ON requested at 10:57:29.647 (349 seconds OFF). The first
  retained Tire result was received at 10:57:39.993, preserving its original
  source time 10:53:06.607 from the offline maneuver. This is backlog delivery,
  not a fresh event at reconnection. A new function receipt at 10:57:54.809
  reported RECEIVING. Presenter subsequently showed Cloud Online and new
  Controller/Brake/Tire CPU/RAM points without a guest/service restart.
- Final served UI build:
  `6e7bbb9bf9114cc7214584db672af298476ebac7846946ccaa9702dfcc6a98b3`.
  Final regression also covers the live identity correction, independent
  history success/latest failure, and the inverse case where a successful but
  empty history must not revalidate a retained latest measurement. No timing
  deadline, service algorithm or data path was relaxed to obtain these passes.
- The original QEMU, Unreal/CARLA, Gateway runtime, native Driving Control,
  VISS client and desktop Presenter processes remained running. The Test is
  left stationary in Safe Stop with External Network ON and Cloud Online;
  VDP 97/V3, Brake 77/V3 and Tire 43/V1 remain installed.

## Handoff boundaries

No full reinstall/version-update/Finish run was repeated: this packet changes
the host UI/read path, not the images or services. Deferred checks from the
versioned-observability packet remain separate. Public push is not claimed.
Do not use UI freshness or successful Reset as proof of vehicle health.

## UIA7 — disk and traffic display follow-up

Implemented and activated on 20 September 2026 after the operator accepted
keeping the existing local backend network. This is a display/observation
metadata correction, not a traffic-accounting or vehicle-runtime change.

- Protocol/Core and deployed OEM formatting establish unscaled bytes for disk
  usage and network volume. The host projection now supplies verified unit
  metadata; numeric values, identities and source timestamps remain unchanged.
- Disk shows used partition space with adaptive B/KiB/MiB/GiB formatting.
  The four current controller partitions fit one resource page, with partition
  names in card headings. They are not represented as separate physical disks,
  free capacity or an additive controller total.
- Inbound/Outbound show received/sent daily totals, not transfer rates. Text
  ties the accounting day to the source sample, avoiding a false "today" label
  for retained older data. Local/private traffic exclusions are explained;
  measured 0 B does not claim missing backend delivery.
- Unknown unit, missing value, conflict and retained/incomplete states remain
  distinguishable. CPU/RAM formatting, graph sampling and API cadence are
  unchanged. No additional observer or Cloud endpoint was introduced.

Follow-up gates passed: 320 Presenter unit tests, 137 browser tests, 30 Cloud
observation tests and 4 monitoring-history tests, plus typecheck, production
build and documentation checks. After the final partition-heading polish,
all 320 unit tests and both affected browser cases (1100 and 640 px viewports)
were rerun successfully. Browser tests include previous-day samples, true zero,
unknown units, service scope, read-only interaction and compact layout.

Live inspection at 11:39 UTC showed controller `states` 135 KiB, `storages`
408 KiB, `var` 96.61 MiB and `workdirs` 592.46 MiB. Service storage inspection
showed Tire 52 KiB and Brake 100 KiB, with state usage 0 B. Both service network
directions showed 0 B with the private-network explanation; controller received
22.2 MiB and sent 2.03 MiB. These are source samples, not benchmark guarantees.
The Test remained Online, with VDP 97/V3, Brake 77/V3 and Tire 43/V1 installed.

Final served UI build:
`aae933dcb67b2b4a852ec15b82b25597b50e4c9aeb992ccfca587563ef837d52`.
The prior compatible build is retained at
`/private/tmp/presenter-resource-units.YplMAR/previous-dist`; the prior adapter
is available at source checkpoint `397e657`. Compiled files remain outside Git.
The local browser was reloaded and Disk/Inbound/Outbound were inspected.
The existing native Presenter window can load the same build using Reload UI;
its reload was not independently observed in this follow-up.

Presenter server session and the original desktop Presenter, QEMU, CARLA,
Gateway, Driving Control and VISS processes were preserved. No runtime restart,
network toggle, Reset, upload, service update or destructive action occurred.
A full lifecycle rerun and public push are not claimed for this follow-up.

## UIA8 — Driver Advisory wording

The operator approved a wording-only follow-up: both service-card buttons now
say **Reset Driver Advisory**; accessible names retain Brake/Tire context.
Submitting/waiting messages say **Resetting driver advisory…**, while the
existing correlated Gateway CLEAR is labelled **Driver advisory reset**.
Card, popup and operation-title wording are aligned. Native command names,
request payloads, availability guards, reset semantics and history retention
are unchanged.

Typecheck, all 322 Presenter unit tests, all 137 fixture browser tests and the
production build passed. Two new unit cases verify identical visible wording
but distinct unchanged Brake/Tire command targets. Existing browser cases
verify submission, pending CLEAR and confirmed feedback, duplicate protection,
independent details and unchanged peer-service results.

The tested static UI assets were activated at an idle operation boundary;
the Presenter server session was retained and no runtime was restarted.
Served build:
`68fea053d6447e5a5b8fb3340a39a30678645ebc74f68b9978577f5ad3339cf5`.
The previous assets are retained at
`/private/tmp/presenter-advisory-label.igNif1/previous-dist`; preceding source
checkpoint is `ff8931b`. No live advisory reset was needed or submitted for
this copy-only check; no Python/backend/guest behavior changed. No full
lifecycle rerun or public push is claimed.

Read-only live browser inspection at 11:54 UTC confirmed the exact visible
button text on both cards, the updated confirmation text and readable layout
at the existing right-pane width. Earlier confirmed reset timestamps and the
later Inspection recommended results remained intact; no new reset occurred.
The native desktop window may use Reload UI to load the same served build;
its reload was not independently observed.

## Subsequent audit and retention update

The operator then requested a full audit, obsolete-artifact cleanup and public
commit/push checkpoint. The [separate receipt](ui-amendments-checkpoint-cleanup-2026-09-20.md)
records the repeated regressions and publication boundary. It supersedes the
earlier artifact-retention statements: the older UIA7 resource-units rollback
directory was removed; the latest UIA8 `presenter-advisory-label` rollback pair
remains. Factory .35's binary was removed; .36 and its live overlay remain.
The no-push statements above describe the earlier individual follow-ups,
not the subsequent authorized publication. This audit does not rerun the live
Reset/network/lifecycle scenarios or promote the Factory qualification state.
