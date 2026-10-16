<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Current M1 runtime and native Setup acceptance

Recorded on 15 October 2026, on the dedicated M1 internal disk with Production
Aos Cloud and a Test vehicle. These exact profiles do not qualify different bytes.
The [current baseline](current-baseline.md) records remaining acceptance limits.

## Corrected immutable candidate: complete production API and visible UI PASS

The source-preserving VDP successor was built from integration
`ab9d9deec9b3c786d4558b0857fb87f4211b20b1` and the reviewed Platform runtime
`fade0de2412efa71d739cf6e5d7e41308838f0b8`. These are isolated correction
branches, not a main merge or public release promotion. The complete local
media is `AosEdge-SDV-Lab-Production-Clock-20261015.dmg` (14,160,043,197 bytes):

- application manifest: `0f6216c8f300d5106e5ad80cc5ebe25682e397b7ae4174977055018477ffedb8`;
- DMG SHA-256: `f863a732f8d9f22ef0b922182bd8f2a6117960b9f13af93563ea187c8b80a84d`;
- signing: Apple Development, local engineering preview; not notarized.

The prior classified Test `6a1fae4b-1a53-4d8f-9d39-ac0c30abc94a` / Cloud
Unit `63c38d7e-23c0-411a-813b-5487314d571b` was normally retired with exact
absence checks. Fresh Test `79adbc10-3f37-40f7-8642-b03968791734` then completed
new installation, production credential reuse, the complete API journey and
the separate visible M1 continuous UI journey. Existing Production Unit
`d87ba9cb-b21f-45db-8773-553e52d0353e` was preserved. Staging was not touched.

| Phase | Result | Measured time |
| --- | --- | --- |
| Transfer, mount, installation and preparation | PASS | 426.554 s |
| Complete API journey | 118/118 PASS; zero fail/blocked/uncertain/not-run within this journey | 1682.705 s |
| Visible UI campaign, including its preflight and cleanup | 42/42 browser stages PASS; required native-input stages passed | 1197.271 s |
| Whole campaign, including retirement and final closure | PASS | 3405.590 s |

API acceptance includes sequential VDP V1/V2/V3 and Brake V1/V2/V3, Tire,
real maneuver products/advisories, independent resets with retained history,
300.689-second offline soak/local progress, durable recovery, ignition off/on,
identity/model/history preservation and new post-restart products.

UI acceptance uses visible M1 Presenter, CARLA and Driving Control, semantic
browser controls and signed native input receipts. It passed initial layout,
sequential publication and Platform-view version checks, new V1/V2/V3 Brake
and Tire results, details/team/resource/backend/activity views, independent
resets, cancel-stop, both QM updates while moving, post-update real maneuver
products, Stop/Start preservation, restored layout and confirmed final stop.
The earlier Brake V3 failure did not recur in these checked maneuvers.

The single entry owned ordinary actions and checks; the agent did not schedule
individual clicks. Cleanup independently confirmed zero owned demo processes
and listeners, closed browser/native runner/tunnel and detached media. Shared
Docker Engine was preserved. The new Test, models, history and release ledger
remain stopped for the next session; stopping did not retire the successful Test.

Scope exclusions remain explicit: `VDP-TIMEOUT-01` is still deferred by the
operator; standalone native Setup first-use acceptance, notarization, public
distribution and main promotion are not claimed by this API/Presenter/Driving
Control campaign. Scoped subreports retain their own `fullE2E=NOT_COMPLETE` /
`nativeAcceptance=NOT_RUN` labels; only the combined campaign certifies the
specific installed API plus continuous visible-UI profile above.

Two supplementary post-campaign journal projections failed at the evidence
command boundary (`QUALITY_LOG_PROJECTION_FAILED`). Both normal diagnostic
boots were stopped and independently reconciled to zero owners/listeners.
They performed no new maneuver, publication, reset or Cloud mutation. No
complete zero-future-rejection log count is claimed; the isolated clock proof
and actual API/UI functional results are the available correction evidence.
This supplemental collection failure is not silently converted to a pass or a
reason to rebuild/replay the already successful campaign.

Private immutable campaign, timing, API/UI receipts/screenshots and closure
records: `.local/remote-qualification/m1-production-clock-full-20261015`.
The earlier failed candidate and proof evidence remain separately identified;
their results are not substituted for this candidate's acceptance.

## Native Setup with no ready certificates: PASS on 15 October

The remaining first-use profile ran on M1 internal storage with the same
authorized production OEM/SP accounts, but no certificate files/references in
the fresh instance. The previous successful Test was normally retired to free
the account's single Test slot; its reports and parked installation were retained.
An idle-Docker maintenance restart released stale retired-Test file-sharing
handles. It was not an Engine lifecycle test or routine shutdown policy.

The first native installation completed in 170.705 seconds. This exposed a real
Setup defect: choosing Production changed the menu but did not initialize the
hidden enrollment domain, so the paired request stopped locally with
`SETUP_ENROLLMENT_ENVIRONMENT_INVALID`, before any certificate request. Setup
now derives the paired request domain directly from the selection and resets
both token fields when changing environment. Offline state proof and compiled
native Staging/Production assertions passed before successor media creation.

The corrected Setup was checked against the same installed, still-unenrolled
Runtime Kit. The earlier install evidence is reused because the installation
helpers and all runtime/UI bytes are unchanged; it is not represented as a
second empty-disk installation with the corrected binary.

| Corrected media identity | Value |
| --- | --- |
| Filename | `AosEdge-SDV-Lab-1.2.0-rc.2.dmg` |
| Bytes | 14,159,474,231 |
| SHA-256 | `71063a5d05ce9287feb0964d661b8408343aa85a58b4c3baaed8c0fd14664270` |
| Runtime application manifest | `0f6216c8f300d5106e5ad80cc5ebe25682e397b7ae4174977055018477ffedb8` |
| Setup executable SHA-256 | `95dbe894f0046c1709795525e0a4b9cf547a9aec8cac2f6955918f20bc582fa3` |

The fixed native scenario found both certificate fields empty, selected the
Production menu item, typed fresh one-time tokens into native secure fields,
clicked Get certificates, observed Connected to Production and opened Presenter.
New private keys were generated on M1; working developer keys were not copied.
Tokens passed in memory over pinned SSH stdin and a private FIFO, never through
argv, environment, clipboard, files or screenshots. No new Test was created.

The final native sequence took 67.139 seconds. Separate packaged-SDK Cloud
observation confirmed the matching authenticated pair and READY in 4.871 seconds;
final reconciled closure took 5.999 seconds. Corrected media transfer/mount took
247.376 seconds. These are individual phase times, not total elapsed time for
diagnosis, earlier failed harness attempts, installation and packaging.

Two evidence-tool corrections did not replay successful UI/enrollment actions:
popup input now selects a semantic menu item rather than assuming keyboard
position; certificate observation uses the packaged SDK helper rather than
importing cryptography into host Python. Presenter opening is retained from the
successful native action and its trusted helper's actual window/server checks,
before its confirmed shutdown. The final observation does not claim the already
closed Presenter was still running. Zero owned demo processes/listeners, native
client/Setup closure, media detachment and preserved shared Docker were checked.

This closes new-certificate native first use for this exact Setup/runtime pair.
It does not certify a new macOS user's permission prompts, new Cloud company
registration, notarization or the deferred VDP timeout. The preceding 118 API
and 42 visible-UI results apply to the unchanged Runtime Kit. Source fan-in and
anonymous public option A delivery are separate subsequent release gates.

Private first-use receipts and preserved failed-attempt evidence:
`.local/remote-qualification/native-first-use-production-20261015`.

The [original investigation and preceding failures](https://github.com/alexmaninblack/aosedge-sdv-demo/blob/cc75541f255f3d2fb0fd670053687ebe406c37ee/docs/qualification/m1-clean-install-e2e-2026-10-14.md)
remain in Git. This maintained record keeps the exact completed profiles and
reuse boundaries; it does not rewrite FAIL/PARTIAL receipts as passed.
