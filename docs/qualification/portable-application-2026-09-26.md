<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Portable application assembly and preserved-run handoff

- Date: 26 September 2026.
- Status: Corrected complete artifact/offline proof and scoped preserved-run
  live checks, including raw guest reboot recovery, passed; open gates below.
- Parent: [Stage 2 work packet](../planning/active/portable-runtime-artifacts.md).

## Assembly evidence

`scripts/distribution/application.py` exports 83 application files, including
69 Python modules, runtime contracts, independent input locks, public
launcher-path metadata and license. The six new selector/entry modules are
explicitly reviewed additions; arbitrary untracked Python files are rejected.
Relative imports are checked, including package-level version exports.
No `.local`, `.run`, credential, operator configuration, overlay, model state
or release ledger is included. Git HEAD alone is not presented as the source
identity: each exported working-source byte sequence is recorded.

Five existing locked input groups were APFS-cloned and their transferred
payload bytes verified: host, preparation, VM/DNS, Cloud SDK and backends.
They total 28,110,934,104 logical bytes. The unchanged Factory catalogue also
uses a read-only APFS clone of the preparation group's .39 image, sharing
blocks rather than allocating another full image. No Game cook, Factory build,
service compilation, native host compilation or package download occurred.
Free space remained above the 90 GiB reserve (about 101 GiB after assembly).

The assembled workspace was relocated to a short path containing spaces:
`/private/tmp/aosapp.dEU9Ge/Runtime Kit`. Its application manifest SHA-256 is
`bb8ee9e2b1d629cb2f1ea97d6261dce83dc823e478facb8a97a75e878104fb95`.
This is a local engineering artifact, not a signed/notarized installer or a
redistribution-approved release.

## Offline proof

The relocated private interpreter ran with `-I -B`, development/Homebrew/Xcode
and operator credential/Keychain reads denied, and all network access denied.
The proof's deliberate denied-file/network controls passed. Results:

- All 69 application modules import from the candidate.
- Existing `host_entry.py` supports CLI help/version without developer Python.
- All five selectors resolve through the relocated existing catalogue layout.
- Private QEMU, firmware, DNS command and fixed Cloud worker commands resolve.
- Backend archive verification and VDP common-runtime input validation pass.
- Factory .39 is discoverable without metadata conflicts or image problems.
- Brake V1/V2/V3 and Tire V1 configurations retain the accepted quotas.
- Missing operator TLS explicitly returns `SOURCE_OPERATOR_TLS_REQUIRED`.
- No runtime journal/state is created and no live service is operated.

Evidence: `/private/tmp/aosapp.dEU9Ge/probe.py` and `offline.sb`; tool result
`PASS_OFFLINE_RELOCATED_APPLICATION`. This is not a real guest boot or an
authenticated Cloud proof. TLS/credential first use belongs to the later setup
stage; it is not supplied by copying this machine's credentials.

Regression: 114 distribution tests pass. The complete orchestrator regression
passes 1,155 cases with 17 explicit skips (1,138 executed); native live cases
are not claimed by that test run. Documentation/whitespace gates pass before
the live continuation. Initial builder invocation with `-I` excluded its sibling
build-tool imports; no output existed. A subsequent closure check required
handling the package's `__version__` export; that build-tool false positive was
fixed and covered before assembly. Neither case rebuilt a product.

## Live continuation boundary

The operator authorized live checks after assembly. Keep the current state
root and exact Test .39 / Production .31 identities; do not migrate provisioned
state into the exported app. Handoff uses existing owners and independently
locked inputs. It can qualify those dependencies against the preserved run,
but cannot establish a fresh clean-Mac or first-install all-version cycle.

At the first checkpoint the old HTTP server was stopped through its idle
ownership gate. Normal Test-only simulation Stop confirmed Safe Stop and
detachment, then stopped Controller/Gateway and CARLA. Normal VM Stop completed
in 3.63 seconds, including the exact legacy DNS helper, without force or
deprovisioning. Both VM disks and Cloud identities remain retained. Docker
Desktop was started as the existing prerequisite: both owned backends and five
unrelated Watt containers restarted under their existing policies; their
configuration/data was not changed. Functional qualification is in progress.

Open gates include integrated guest/Cloud/backend/advisory behavior, serial
version transitions, offline/ignition and native/UI review, fresh-engine import,
first-use/installer design, clean-Mac execution and redistribution obligations.
No source commit, push, tag or external artifact publication is claimed.

## Corrective live findings and final assembled successor

The preceding candidate is historical; `Runtime Kit 004` is the corrected
complete workspace under the same private proof root. Its application manifest
SHA-256 is `c7f5b967ae08407b4f1ee09714a7a0cea5ba555e5076598761052b3b990187bd`.
It exports the same 83 application files / 69 modules and five groups totalling
28,111,240,862 logical bytes. Transfer hashes pass. The repeated source-,
Homebrew-, Keychain- and network-denied proof passes, including packaged NIC
data and both services' advisory paths. COW storage keeps free space around
101 GiB; there is no second physical Game/Factory rebuild.

Four narrowly scoped defects were closed:

1. The first private QEMU version probe needed 3.38 seconds; later identical
   observations needed about 0.017 seconds. The old three-second packaged
   budget caused a pre-spawn exception. Packaged probing now has a bounded
   15-second budget and a classified timeout; developer behavior is unchanged.
   No specific OS loader/cache cause is asserted.
2. The VM lacked `efi-virtio.rom`, required by its existing `virtio-net-pci`
   device. A paused, diskless QEMU fixture reproduced the exact missing-ROM
   error; the same fixture passed with the pinned file. The small VM bundle
   now includes that file and QEMU notices, and supplies its explicit data
   directory. Source-denied proof passes. QEMU, firmware, Factory and guest
   services were not rebuilt. Normal Test starts completed in 33.67/33.96s.
3. Strict source admission's anonymous negative probe still referenced a
   developer client. It now uses the selected packaged client; the required
   `TLS_CLIENT_CERTIFICATE_REQUIRED` result passes. No role or permission changed.
4. Historical native inventory selected a pre-advisory Gateway/client pair.
   Packaged Gateway had no QM paths/symbols, while the actual accepted warm
   build did. Reconciliation against clean Gateway source
   `4e384798c95298a706709775c6fb33367edd00c6` and all six QM/protocol/access/
   assignment/network/dashboard suites passed. Gateway was already current;
   its client required only a warm link. Corrected inputs replaced just the
   two binaries and native metadata. Other 14,167 host payload files retained
   their inode/size/mtime; shared libraries were byte-identical. A negative
   build gate rejects pre-advisory inputs. Path presence is not misrepresented
   as functional qualification: the live round trip below provides that proof.

The successor host manifest is
`15522032314610362d678e3ddbb464d204a18fd09085dbb3e4a1d5cf1f71d28e`;
its rebound small VM manifest is
`d9b06cfa14bc602059ce80a1311f79177bd3e6d058108f83c9a0db6dba25082d`.
Previous bytes and compact build/handoff receipts remain under the private
Stage 2 proof roots. No temporary guest policy, diagnostic client, permission,
model threshold or injected telemetry was used.

One harness issue was kept separate: the initial HTTP worker was launched
with a relative entry path, so canonical `ui stop` correctly refused ownership.
Its exact UID/command/cwd and all existing idle/recovery guards were verified
before normal SIGINT. The replacement uses the canonical absolute invocation;
the product ownership guard was not relaxed. Two optional retained-developer-
source tests also accidentally selected the newly active operator catalogue;
their fixture now explicitly owns the developer branch. No product selector
fallback was added to make these tests pass.

After ignition recovery, canonical `ui stop` also passed its real ownership and
idle guards, the HTTP worker exited normally, and the same canonical private
entry was reopened. VM, simulator and Cloud state were not stopped by this
Presenter lifecycle check. No browser visual claim follows from HTTP startup.

The last restart exposed one additional source defect: a client-cancelled
monitoring response raised BrokenPipe, which the read handler misclassified
and attempted to answer again with 503. Two disconnected-writer fixtures
reproduced the failure before correction. Response output now catches only
BrokenPipe/ConnectionReset and closes that connection; real observation errors
retain their existing sanitized failures. Tests cover cancellation in headers
and body, unrelated writer errors, and a real TCP-reset client followed by a
successful request. No Cloud query or protected action is retried. Only HTTP
was restarted; Test/CARLA/Gateway/backends remained running. `Runtime Kit 004`
supersedes 003 solely for this small application-source delta, with all five
input pins unchanged. Its isolated offline proof passes again.

Final regression: **1,163 orchestrator cases, 17 explicit skips**, OK in
132.123 seconds; **118 distribution tests**, OK; six native Gateway suites,
OK. The earlier full run's two fixture errors are not counted as a pass.

## Preserved-run functional proof — 26 September UTC

Test remains Unit `5395f7d6-2ff3-4d10-9e7f-efa85e7994eb`, VM
`48a0e19c-857f-44b8-9b68-38b585a8278f`, with VDP117/V3, Brake92/V3 and
Tire49/V1. Production .31 stays stopped and unchanged. Both backend containers
reuse their existing volumes; histories and model state are not reset.

- Restored strict attachment has one selected-Unit and one dashboard role,
  zero qualification clients; VDP is READY/LIVE, automatic restarts zero.
- Before correction, both advisory writes were rejected and last backend
  facts were dated 25 September. After correction, fresh Brake and Tire facts
  report `APPLIED`, retaining their inspection recommendations. No service
  update or restart was needed to change the advisory protocol behavior.
- Online Tire maneuver: 260 frames / 13.0s / maximum 35.108 km/h, physical
  stop confirmed. New Tire assessment arrived at 19:37:18.247; its braking
  phase also produced a separate Brake assessment at 19:37:19.992.
- External OFF completed at 19:38:40.242; ON at 19:42:01.813 (~202s).
  Cloud reported OFFLINE with transition time 19:39:06. Local CARLA frames,
  VDP readiness and accepted advisory requests continued. SM/CM/VDP each
  reported active/success and zero automatic restarts.
- During OFF, real Brake (267 frames, 13.35s, 30.588 km/h maximum) and Tire
  (260 frames, 13.0s, 35.094 km/h maximum) maneuvers completed with physical
  stop. Settled-OFF snapshots retained identical latest receipt timestamps for
  both services' assessments, advisory facts and function observations. Backend
  observations became stale as expected rather than receiving hidden traffic.
- After ON, Tire assessment delivery resumed at 19:42:26.930 and Brake at
  19:42:34.491; the latter has offline source time 19:40:42.476. Both fresh
  advisory facts again report APPLIED and function observations become fresh.
  This proves resumed/delayed delivery, not an exact outbox-ID bijection or
  total drain; that stronger assertion was not measured in this run.
- Repeated Start returned `noOp=true` without another CARLA/scene. Return to
  road completed in stationary Manual, Autopilot not started, models retained.
- Native startup geometry matched all requested rectangles and z-order was
  VERIFIED. Readability remains `OPERATOR_REVIEW_REQUIRED`: no browser/native
  visual acceptance is inferred from layout or API results.

Readiness still briefly changes NOT_READY→READY (~0.2–0.3s), including before
OFF and after ON. Startup also rejects old/stale advisory values before fresh
publication. These remain observations, not claims of uninterrupted readiness
or proof of a new network-related defect. The retained readiness-flap follow-up
from the [.39 offline qualification](factory-39-offline-2026-09-24.md#observations-do-not-call-this-uninterrupted-readiness)
is not silently closed by the Gateway packaging correction.

Receipts/scripts are in the CARLA workspace's
`Build-distribution-stage2-20260926`: `gateway-correction-*`,
`packaged-live-{connected,corrected,tire-completed,offline-before,offline-after,online-recovered}.json`
and the fixed public observation helper. Secrets and raw sensor streams are
excluded. The separate application export contains no live state.

Remaining scope: actual operator-UI review, fresh-engine backend import,
fresh serial all-version provisioning/update E2E, installer/first-use design,
redistribution/notarization and clean-Mac qualification. Preserved-run success
does not make the artifact a distributable installer or a clean installation.

## Final ignition and authoritative reconciliation

A single raw guest reboot was requested at 19:44:53.482 with the car already
stationary and external connectivity ON. SSH returned 255 when its connection
closed; this alone was not counted as reboot success. The subsequent boot-ID
change established the restart. Presenter, not the qualification script,
automatically restored the existing route from 19:45:24.591 to 19:45:35.577:
10.99s for recovery, about 42.10s from request to READY_SAFE_STOP.

The same QEMU process, simulator run/actor, assignment generation 34 and exact
Unit/Node/VM identities remained. No manual reattach, provisioning, scene reset
or Autopilot action followed reboot. VDP became READY/LIVE with zero automatic
restarts; current SM/CM/VDP observations are active/success/NRestarts=0. Existing
boot restoration may perform its canonical controlled configuration restart;
zero automatic counters do not imply every guest PID stayed unchanged.

Post-recovery facts for both services are APPLIED and freshly received, function
observations are fresh and previous assessments remain available. AosCloud's
final read at 19:48:23.077 reports ONLINE (transition 19:45:51), unchanged
117/92/49, both service instances active and no pending component/service update
or reported error. Car state is Safe Stop, 0 km/h, brake 1.0; external link is ON.

Compact evidence: `packaged-ignition-intent-001.json`,
`packaged-ignition-result-001.json`, `packaged-live-ignition-final.json` and
`packaged-cloud-final-001.json` in the same private build-proof directory.
This is raw guest reboot with external ON, not cold offline boot, abrupt
power loss with a nonempty queue or a complete new-installation version matrix.
No commit, push, tag, cleanup or external publication was performed. The final
disk observation is about 100 GiB free, above the retained 90 GiB reserve.
