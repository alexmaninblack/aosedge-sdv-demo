<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Advisory readiness and independent Reset — preserved Test

Status: partial qualification, 16 September 2026. Functional CLI and targeted
UI proofs passed on the preserved staging Test; no clean Factory acceptance,
full fresh UI lifecycle or final cleanup is claimed by this report.

## Scope

Staging `aws-stage.epmp-aos.projects.epam.com`, Test Unit
`42c0bf43-4eb7-44e6-8c74-f60f9959da66`, original Factory .33.
Production was not changed. Runtime/build/package actions used Demo Control;
backend Reset actions were also exercised through Presenter and observed in
the native Driving Control telemetry. The dashboard reads only Gateway/VISS.
The backend results use real vehicle signals and explicitly labelled demo
synthetic estimators, not production diagnoses.

| Artifact | Functional profile | Confirmed runtime |
| --- | --- | --- |
| VDP 70.0.0 | V3 | Installed and running from 17:49:06 UTC; 23 telemetry paths |
| Brake 49.0.0 | V3 | Native instance active, real KUKSA, backend poll connected |
| Tire 30.0.0 | V1 | Native instance active, real KUKSA, backend poll connected |

Tire's accepted first functional profile includes advisory. Release numbers
are provenance and are not used as a substitute for functional capability.

## Exact functional evidence

1. Brake warning -> CLI Reset `da889d3c-9f16-4652-af41-dbf38d55924d`
   at 17:44:44.433 UTC -> correlated Gateway CLEARED at 17:44:47.099.
   CLEAR request `6646743c-f995-5730-9b2c-38c60575e611`, sequence 594,
   unchanged producer epoch `803f6948-17ee-4bdd-912d-b8ae1ea2bdda`.
   Tire was unchanged.
2. New real Brake maneuvers yielded MONITOR and then INSPECTION_RECOMMENDED.
   The 17:46:49.789 assessment `4d83a0d3-d5d2-55c6-bda4-c4a66ad771b9`
   had score 34, 25 active braking and 12 straight qualified samples. Gateway
   applied the renewed warning with a higher sequence. No threshold change.
3. Tire CLI Reset `b5594904-3d71-472c-a63e-145430c00083` at 17:49:28.185
   was CLEARED at 17:49:30.526; sequence 405, unchanged epoch
   `80e393f6-2c89-4000-9093-7b29889eda58`.
4. Presenter Brake Reset cancellation did nothing. Confirmed Brake Reset
   completed and cleared only its native warning. Retained historical
   assessments were excluded from the new current result, not deleted.
5. Presenter Tire Reset `5277e069-2fbd-49fd-bc3b-1ed9d15767a9` at
   18:10:40.384 was Gateway CLEARED at 18:10:42.512, request
   `a8664bdc-3c03-51c7-b67a-533f69154295`, sequence 453. The native screen
   subsequently showed Brake Inspection recommended / Tire Monitoring.
6. The final real Tire maneuver completed collision-free in 13 seconds,
   260 frames, maximum 35.105 km/h. New assessment at 18:12:54.359,
   `fd2965e4-865f-5415-a00d-a468ffc2d6c1`, moved NOT_EVALUATED to
   INSPECTION_RECOMMENDED, score 69, confidence 98%, 39 samples. Gateway
   APPLIED request `7ae026ac-d5e0-5db1-8bdd-b40b89f7e400`, sequence 455,
   at 18:13:14.441. Both native advisory warnings and the corresponding
   Tire backend result were visually observed again at 18:20 UTC.

Earlier long Tire maneuvers collided at a junction and are explicitly **not**
qualified. The test maneuver was shortened to stop before the junction; its
steering amplitude is 0.3. It uses real CARLA physics, no substituted signals
and no model-threshold changes. An intermediate 0.15 run completed but did
not establish a new warning after a clean estimator reset; it is not used as
the final warning proof.

## Corrections proven during this cycle

- A valid unexpired Gateway warning takes precedence over an absent/stale
  availability heartbeat. Invalid readiness can never hide that warning.
- Availability heartbeats initially failed because the VM timestamp led the
  host by 9–10 ms. The already agreed five-second demo skew tolerance now
  applies only to that display heartbeat. Expiry remains the Gateway's own
  15-second wall/monotonic deadline; older-than-15-second and non-increasing
  observations remain rejected. No Safe Stop or warning-request window changed.
- The transient credential proof restarted its oneshot preparer; the native
  Requires dependency stopped VDP69. The proof harness omitted resuming it,
  producing PROVIDER_MARK_UNAVAILABLE_FAILED. The exact committed VDP69 was
  resumed without selector/database/manager changes. Native retry installed
  VDP70 at 17:49:06, with no new upload. This was a proof-harness fault, not a
  change to Cloud delivery or component Safe Stop semantics.
- Presenter now labels a newly submitted Reset as in progress instead of
  briefly displaying the previous command's CLEARED result as its completion.
- Bounded diagnostic output includes readiness transport and only allowlisted
  update/mount labels; secret-redaction regression cases pass.
- Final status reconciliation exposed the owned run journal's old 64 KiB
  input limit (the preserved long-run journal reached 65,723 bytes). Only
  `.run/demo-current/journal.json` now has a bounded 1 MiB read budget.
  Other JSON inputs retain 64 KiB; explicit caller limits still take priority.
  No history was deleted. After correction, VDP70 was independently observed
  active, LIVE/REPORTED_READY, with zero restarts. Presenter alone was restarted
  to load the correction; VM, CARLA and Driving Control were preserved.

## Security and transient disposition

The exact KAC time-marker read/search proof policy was restored to the saved
stock policy through `service runtime-activate test --kac-only
--kac-recovery-remove`. A second invocation was a verified no-op. The canonical
policy store was not changed, the owned recovery drop-in was removed, and no
VM/CM/SM/IAM/container was restarted by this rollback.

The same approved policy was then reactivated under its six-hour rollback
lease to preserve the working Test while the successor is built. This is
explicitly transient, not clean-image acceptance.

Current Test also retains previously inventoried transient manager capacity
binaries, VSS supplement and Provider preparer/29-scope credential proof.
The Provider executable runs from a private root-owned read-only filesystem;
global /run flags, NoNewPrivileges, rootfs and SELinux enforcement are unchanged.
Do not reboot .33 with its migrated token and old preparer without an owned
rollback. None of these live inputs may be copied into Factory .34.

## Local gates and remaining work

- Demo Control final full suite: 936 run, 16 skipped, no failures (69 seconds).
  The first rerun exposed five journal fixture call-count mismatches and a
  status test coupled to live workstation state. Fixtures were corrected and
  status collection isolated; no runtime behavior was weakened to pass.
  After the journal-budget correction, the full suite passed again. Presenter
  was reloaded and visibly confirmed current Test Online, Brake49/V3,
  Tire30/V1 and VDP70/V3; .34 appeared in the firmware catalog while the
  running Test remained on .33.
- Latest targeted gates: 34 service-input, 46 component-runtime, 8 Factory
  compatibility and 13 permission-capacity tests; Presenter backend UI 9 tests,
  typecheck and production build; full Presenter suite 135 passed;
  CARLA scenario 5 + qualification maneuver 3.
- Platform: permission storage 3 (including actual C++ 32/256 boundary proof),
  advisory transport 13, KAC Factory integration 14, VSS schema 6 passed.
- Gateway warning-precedence and heartbeat skew/expiry native suites passed.

Factory .34 completed from pinned source
`81e7e1fda991c133a7dc83188c1dcf0f966fd62e`. Three-manager 256 flag parity,
five native Factory regressions, ten KAC tests and Provider/verifier test
executables passed before image construction. Manager package QA and image
QA completed; package QA retained build-path warnings (not zero-warning QA).
No source rebuild or image retry was needed. Builder stopped cleanly.

Immutable raw image: 6,997,147,648 bytes, mode 0444, SHA-256
`fac0cccfd5c4ededaf068bbd574b0f0a83b9af1b94f1df94022fa0ca5893eeeb`.
The remote assembly and host-transfer digests matched. Artifact location is
`demo-artifacts/aosedge-sdv-demo/factory-images/6.1.1-maninblack.34/`,
outside Git. `democtl image list` discovers it without issues as selector
`6.1.1-maninblack.34/main-qemuarm64`. Manifest state is deliberately
`BUILT_NOT_LIVE_QUALIFIED`; metadata availability is not boot or E2E evidence.
Original .33 and the live staging Test remain preserved.

Open UI integration decision: first-time strict Gateway authentication is
currently a CLI operation, not part of the Provision button. Automatically
including it would restart the local simulator group and must preserve
stationary Manual before reopening the VM's source link. The operator's
Safe Stop remains the component installation gate. Approval was requested;
the existing UI flow has not been silently changed. Until closed, a clean
UI-only advisory lifecycle cannot be declared passed.
