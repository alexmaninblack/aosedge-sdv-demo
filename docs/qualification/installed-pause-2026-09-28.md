<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installed Demo — Laptop Travel Pause, 28 September 2026

## Preserved checkpoint

The operator explicitly requested pausing qualification, closing the laptop and
safely disconnecting the external SSD. This is a data-preserving shutdown, not
Finish demo, legacy Park/Resume, a new ignition qualification, or a cleanup.

- Installed instance: `~/SDV-Lab-Clean`.
- Selected immutable Kit 009:
  `f20b6d501ac5c0e257532a41507e68bbd8039d6d5e07b499b8dc53610dcd28e1`.
- Store: `SDV-Work/AosEdge-SDV/install-tests/stage3-clean-store-001`.
- Work volume UUID: `591578E3-8196-4B44-A575-CEC76B406789`.
- Test VM: `8f380832-3eff-4fc3-94d8-a778dd33f492`, Factory `.39`.
- Cloud Unit: `ee0a8607-5359-47ee-b5a6-4f50568d2b3a`.
- Installed releases: VDP `120.0.0/V3`, Brake `96.0.0/V3`, Tire `50.0.0/V1`.
- [Functional E2E evidence](installed-clean-e2e-2026-09-28.md): 24 final
  predicates passed, including serial upgrades, independent resets/history,
  external OFF/ON, exact-once backlog delivery and full ignition recovery.
  Explicit engineering first-use corrections remain disclosed, not automatic
  clean-Mac qualification.

Safe Stop was freshly confirmed at 0 km/h before stopping the exact idle
Presenter server. The normal installed CLI is used to stop Test's simulation,
gracefully stop Test VM, close its Presenter windows and stop the two owned
backend containers while retaining their volumes. No Cloud deletion,
deprovisioning, model Reset, Factory removal or Production mutation is intended.
Final shutdown/eject results are recorded below only after observation.

## Interrupted implementation — not deployed or qualified

Native launch work started only after the functional E2E completed. The contract,
ADR/requirement refinement and plan were updated. Source now contains an initial
`setup_launch.py` implementation, fixed bridge/build registration and an
`Open demo` button/protocol in `Setup.swift`. These edits have **not yet been
compiled, tested, built into a native app, installed or exercised live**. The
running native setup preview remains the previous immutable preview 009.

Resume with code review and focused negative/ownership/protocol tests before any
native build or execution. In particular, review strict required session fields,
first-start readiness/partial-port races, response-loss reconciliation and
first-use Presenter-only versus complete simulator layout. Run Swift protocol
tests and inspect the actual window/button fit. Qualify first/repeat/reopened
launch separately, preserving this exact retained Test; do not switch its kit
or bypass retained-run version guards. No commit or push was requested here.

`VDP-TIMEOUT-01` remains explicitly deferred. Do not restart that investigation.
Large-artifact work remains subject to the 90 GiB reserve; internal free space
was approximately 87 GiB at pause. Do not delete preserved data to bypass it.

## Resume order

1. Reconnect the same SSD and verify volume UUID and selected installed version.
2. Check exact owners and existing journals before starting anything. Start the
   preserved backends/controller/simulator through existing Demo Control as
   required, restoring the same Unit and stationary vehicle, not a new Test.
3. Finish and qualify the separate native launch increment above.
4. Carry forward the first-use preparation, existing-account reconciliation,
   cold CARLA start and diagnostic follow-ups documented in the E2E receipt.

## Shutdown and ejection observation

Confirmed around 16:04 UTC / 18:04 local:

- Exact idle Presenter HTTP server stopped normally.
- `simulation stop --target test`: COMPLETED, physical stop confirmed,
  current vehicle detached, CARLA/Controller/Gateway stopped.
- `vm stop test`: COMPLETED, graceful shutdown in 4.32 seconds; no forced kill.
- `workspace close`: CLOSED, no problems and no pending retry.
- Brake and Tire `backend stop`: both STOPPED, `dataPreserved: true`.
- Exact native setup preview 009 accepted normal Quit.
- No current-user file handles remained under either SSD volume. No listeners
  remained on the five checked demo TCP ports (18080, 18600, 2000, 16443, 10022).
- macOS reported `Disk /dev/disk12 ejected`; neither `SDV-Work` nor `SDV-Clean`
  remained mounted. The physical device may still enumerate until unplugged.
- The internal Test overlay, instance marker and selection record remained
  present. No Finish, deletion, deprovisioning or package selection occurred.

The external SSD is safe to unplug. Qualification is paused at the operator's
request; no test/build is intentionally left running against it.

## Subsequent resumption

The pause/ejection statements above describe the 16:04 UTC checkpoint, not the
current desktop. After the operator reconnected the disk and authorized
completion, its UUID and Kit 009 selection were verified. The
[native launch report](native-presenter-launch-2026-09-28.md) supersedes the
unbuilt/untested implementation status: preview 010 was built and exercised;
warm/reopened launch passed, while cold file-open delay remains unqualified.
Presenter is now open. The retained controller, simulator and backends were
not started by that launch action. The disk is mounted and in use again; it
must be stopped/ejected before another physical disconnection.

## Second travel pause — 29 September 2026

The operator requested a data-preserving stop and SSD ejection again. Before
shutdown, the retained source was already STOPPED, current vehicle was null,
and no QEMU/CARLA/control process or demo backend container was running.
Presenter reported no active, uncertain, workspace or source-recovery operation.
No compiler or setup helper was running. Unrelated Docker containers were left
unchanged.

The exact idle Presenter server (PID 47891) received normal SIGTERM. The installed
`workspace close` completed at **05:21:49 UTC**, closing host PID 47978 with no
problems or pending retry. Native setup preview 015 was closed with normal Quit.
Both external volumes had zero current-user open handles. Volume UUIDs and their
APFS physical-store mappings were revalidated before normal, non-forced ejection
of the 1-TB Portable SSD T5. macOS confirmed `Disk /dev/disk12 ejected`; neither
SDV-Work nor SDV-Clean remained mounted. No demo process or listener remained on
18080, 18600, 2000, 16443 or 10022. The disk is safe to disconnect.

No Finish, deletion, Cloud mutation, model reset, package selection or source
cleanup occurred. Test identity/data, Factory inputs and all candidates are
preserved. Two evidence-command schema/path errors were corrected before
ejection: `plistlib.load` cannot seek this pipe, and this macOS plist uses
MountPoint rather than the assumed Mounted field. Neither attempted a stop or
ejection; the subsequent exact UUID/physical-store preflight passed.

Resume from the [native launch checkpoint](native-presenter-launch-2026-09-28.md),
not another E2E or rebuild. Source regression: 245 distribution tests pass;
preview 015 successful/repeated native Open remains unqualified. The operator's
subsequent question localized repeated consent to changing ad-hoc code-signing
identities. Stable development/distribution signing is the next proposed step;
no certificate setup or signing-policy change has been performed. Preserve
`VDP-TIMEOUT-01` as deferred. Reconnect and verify the same SSD before any use;
do not automatically start driving or create another Test.
