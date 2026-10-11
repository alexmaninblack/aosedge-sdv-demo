<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Integrated Setup qualification — 11 October 2026

- Status: Native existing-access first/returning use and scripted vehicle journey passed on M1; new-access gates open
- Scope: [Integrated Setup scenario](../planning/active/work-packets/integrated-setup-scenario.md)
- Implementation revision: `ba99d3f`
- Live environment: Aos Cloud staging only

## Implemented boundary

The ordinary route is Install SDV Lab, Connect to Aos Cloud, then Open SDV Lab.
Setup discovers only its fixed sibling Runtime Kit, supplies default program
and private-state locations, prepares the two exact backend images and installs
a persistent signed launcher. The user selects only the OEM and associated SP
certificate files. One Connect action authenticates the pair before saving
references and may prepare the exact absent model and empty Test set.

New access offers a fixed Staging/Production choice, official account pages and
paired secure-token enrollment. This is not a claim that anonymous first-account
signup, email confirmation or terms acceptance is available as an unattended
API. Paired receipt recovery never automatically replays uncertain issuance.

## Automated evidence

- Distribution suite: 330 tests passed, one skipped.
- Focused Cloud suites: 123 tests passed.
- Native arm64 compilation and protocol self-test: passed.
- Documentation checks: 347 Markdown files, 662 specification IDs and 38 Mermaid
  blocks passed at the implementation commit.
- Staged confidential-input guard and whitespace checks: passed.

The broader orchestrator invocation ran 1,393 tests with 97 errors and two
skips; it is **not** a passing regression result. Errors included sandbox-denied
socket/process observations and a source-catalog manifest mismatch against
retained local inputs. These conditions were not hidden by changing runtime
contracts. Focused Setup results do not qualify all vehicle runtime gates.

## Retained-Test SP repair

The reviewed source worker connected the missing SP on the existing Kit 028
Test using its original OEM and staging domain. All ten fixed Cloud checks
returned READY. The journal remained byte-for-byte unchanged, including the
Unit and release identities; installed VDP V1 release 140.0.0 was preserved.
This is actual worker evidence, not a native UI acceptance result. See the
[detailed repair record](sp-configuration-after-create-2026-10-11.md).

The Test was subsequently retired through its normal lifecycle owner for the
fresh-install qualification. Before retirement, its already submitted VDP
publication was reconciled to READY without another upload. The exact Test Unit
was `35c9a273-e5c6-4186-82fe-ca1043aa55d6`. Presenter and owned workspace consumers
were stopped; shared Docker Engine and Production were preserved.

The quiescent retired default instance was moved to an owned qualification
archive, preserving its remaining configuration and reports. This is explicit
test preparation, not an installer feature for silently replacing retained
instances. Existing credential files outside that instance were retained.
Three old, unmounted qualification DMGs were removed after open-handle checks;
their source artifacts remain on the build SSD. Both old mounted installers
were ejected after their applications exited. M1 free space was approximately
146 GiB before transferring the candidate.

## Candidate and native acceptance

Candidate manifest:
`e296fd3360f8b98c6693df8e4213477d49848affe3c7a6c8a1d27c81ebab90b0`.

Complete DMG: `AosEdge-SDV-Lab-Integrated-Setup-20261011.dmg`, 14,151,944,711
bytes. SHA-256:
`d327accdaecfb91da9c73c6b254babf720cc125682327edcc8c5bcf15d93d9c1`.
The media builder completed its image verification and retained its receipt;
temporary full-size staging was cleaned by the existing scratch owner.

The complete DMG is assembled on the external build SSD from retained validated
Factory, CARLA and other developer inputs. No Factory or CARLA compilation is
part of this change. Setup uses the existing Apple Development signing identity
and team; this is a local engineering preview, not Developer ID/notarization.

### Native existing-certificate journey

The following actions used the actual signed candidate on the M1, with native
buttons and file pickers controlled through Screen Sharing. SSH performed only
the verified media transfer/mount, ordinary application opening, passive
process observations and product-owned shutdown between the two launch cases.
It did not replace Install, Connect or Open with scripted acceptance.

- **Install:** clicked Install SDV Lab at approximately 09:59 local time.
  Real copy progress was visible; at 10:06 the application reported Installed.
  Both exact backend images were checked and the persistent launcher was
  installed. No normal kit/store/private-state question or new OS permission
  prompt appeared. Presenter, VM and CARLA were not started by installation.
- **Connect:** selected the retained OEM and SP PKCS#12 files in native file
  pickers and clicked Connect once. At approximately 10:13 the application
  reported Connected to Staging, naming `aws-stage.epmp-aos.projects.epam.com`.
  Closing the sheet displayed Ready to open SDV Lab. There was no separate
  Inspect, save-reference or prerequisite-preparation action.
- **Open:** clicked Open SDV Lab. At approximately 10:15 the native Presenter
  was visible with No controller created, No Cloud Unit yet, Factory firmware
  `6.1.1-maninblack.41` and an enabled Create controller action. Setup reported
  Presenter opened. No controller, simulator or latest release was created
  automatically; this is the intended start of the vehicle journey.
- **Returning use without media:** closed the owned workspace and idle
  Presenter through their normal product owners, quit Setup, and normally
  ejected the complete DMG. Opened `~/Applications/AosEdge SDV Lab.app` with
  media absent. At approximately 10:17 it reported Ready to open SDV Lab after
  installed/backend and fresh Cloud checks, without certificate entry or a
  second installation. Clicking Open displayed the same initial Presenter
  at approximately 10:18.

The installed program and state are on the M1 internal APFS volume; free space
after installation was approximately 100 GiB. No VM password or token entry
was required for this existing-certificate journey. Screen Sharing keyboard
layout/clipboard limitations affected qualification navigation only; the file
choices were completed in the native picker without modifying the product or
credential files. Existing macOS Accessibility consent was reused. This does
not qualify first-time OS permission prompts on a new user account.

These results qualify default installation and existing-access first/returning
use, not native new-certificate issuance or a complete vehicle release run.

### Qualification shutdown

After returning-use acceptance, `workspace.close` completed and the existing
idle Presenter stop owner returned success. Setup exited through its Quit menu.
Final observations confirmed no listener on port 18080, no Setup, QEMU or CARLA
process and no mounted candidate media. The shared Docker Engine remained
running as Linux/aarch64. Installed programs, instance configuration, retained
credentials and qualification evidence were preserved. No test consumer was
left running for a future session.

## New account registration on staging

The operator submitted the official staging signup for the authorized Google
Workspace account on 11 October 2026. The portal displayed **Your account has
been created**. The OEM and associated Service Provider welcome emails both
arrived at 08:42:58 UTC (10:42:58 Europe/Berlin). This confirms the staging
signup and email-delivery path, not authenticated roles or certificate issuance.

The emails name `api.aws-stage.epmp-aos.projects.epam.com`; Setup selects
`aws-stage.epmp-aos.projects.epam.com`. Read-only HTTPS checks using the
packaged Aos CA succeeded against both names on port 10000, without redirects.
Both returned the same v11 schema, version 6.1.97 with 151 paths. The issued
certificate's Organization and authenticated account association still require
the ordinary product checks; matching endpoint observations do not waive them.

Both enrollment receipts on the installed M1 candidate were NOT_STARTED.
The execution safety review rejected transmitting live tokens as tool-call
arguments, including hidden terminal input, before any issuance dispatch.
The waiting transport was closed and temporary in-memory token copies cleared.
No certificate was requested, no token was consumed by this attempt, and the
prior certificate references were unchanged. Continue by pasting the two email
tokens directly into the native secure fields and submitting Get certificates;
never paste them into chat, commands or qualification evidence. Registration
must not be repeated to recover from this input boundary.

## Scripted vehicle journey on M1

The installed candidate completed the fixed staging journey from 09:23:22 to
09:52:02 UTC (11:23:22 to 11:52:02 Europe/Berlin), approximately 28 minutes
40 seconds including a preserved stop and continuation. The matching verified
DMG was remounted for the signed Setup workers; installation, media transfer
and Factory/CARLA compilation were not repeated. Existing authorized OEM/SP
certificates were used. This run does not qualify the newly registered account.

All 100 primary steps and six restoration checks finished PASS. The runner
reported `scriptedSequence: PASS`, no unresolved operations and no source-review
warning. Private append-only evidence retains all 110 attempts, including the
initial blocked step and both shutdowns; a later pass did not erase that history.

The exact Test run is `524ed2c5-23b6-4ec7-ab81-e8687f4be096`, Cloud Unit
`5c2e41b1-19cf-43c9-9428-89460015d243`. Releases were signed and published
sequentially, with installation and functional checks before the next version:

| Component or service | Logical profiles | Published releases |
| --- | --- | --- |
| VDP | V1, V2, V3 | 141.0.0, 142.0.0, 143.0.0 |
| Brake Health | V1, V2, V3 | 118.0.0, 119.0.0, 120.0.0 |
| Tire Health | V1 | 62.0.0 |

The journey passed controller creation/start, simulator startup, provisioning
and connection; physical Safe Stop before each VDP update; exact Cloud service
publication/readiness; new assessments from real Brake/Tire maneuvers; Brake V3
and Tire advisory correlation; independent Reset with peer-state and history
preservation; and Return to road.

Both services processed maneuvers with external connectivity OFF and queued
results locally. The offline invariant was observed through the full 300-second
interval (303.346 seconds including the final read). After ON, exact queued
assessment IDs appeared in backend history, local queues emptied and Cloud
returned ONLINE. IAM, CM, SM and VDP remained active with successful results
and zero restarts during the observed offline interval.

### Preserved continuation before ignition

The first `ignition-safe` attempt stopped with CURRENT_RUN_BUSY before the
driver command was dispatched. The diagnostic showed no active Presenter
operation, a completed lifecycle and no uncertain effect. Normal shutdown
passed. This was local writer contention, not a controller crash or a failed
ignition attempt; the competing writer was not identified.

Continuation used the same immutable binding and Test, freshly observed the
installation, restored stopped owners through their product paths and resumed
at ignition. It did not recreate/provision a Unit or replay publications,
assignments, Reset or the completed offline experiment. No product or harness
source was changed. Bounded waiting for this pre-dispatch lock contention
remains an automation improvement, not evidence that the contention is fixed.

The resumed ignition off/on changed the boot ID while preserving Unit/Node
identity, service models and backend history, with the vehicle stationary in
Safe Stop. VDP V3 readiness passed. Each service independently reported fresh
CONNECTED/RECEIVING inputs with a producer generation greater than before
ignition, and each produced a new assessment after its post-boot maneuver.

### Final shutdown and acceptance boundary

Normal shutdown confirmed zero owned demo processes/listeners, stopped backend
containers and preserved durable Test state. The idle Setup had no active
helper and was closed; the exact candidate DMG was normally ejected. Port 18080
was absent and shared Docker Engine remained Linux/arm64. The stopped Test,
VM disk, credentials, releases, models and history are retained; Finish was not
executed and Production was untouched.

The runner correctly retains `fullE2E: NOT_COMPLETE` and native acceptance
NOT_RUN: its scripted result does not replace the separately recorded native
existing-access proof or qualify secure token entry, moving SOTA, installation
interruption/repair, new-account connection or distribution notarization.

## Open gates

- Paired certificate issuance and authenticated connection for the new staging
  account; production registration feasibility remains unqualified.
- Native secure-field token entry and paired enrollment on this candidate.
- Distribution notarization and unrestricted third-party installation.
- Moving SOTA, installation interruption/repair and native cold-controller
  resume; scripted stationary ignition and the serial release journey passed.

Production resource mutation, private-key transfer from the development Mac and
unrelated Docker restart are outside this qualification.
