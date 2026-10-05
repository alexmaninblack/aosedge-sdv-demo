<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Installed Clean-state E2E — 28 September 2026

## Scope and current verdict

The operator requested the complete E2E run on the newly installed application,
followed by a discoverable launch action in the installer. Continue from the
[clean-installation receipt](clean-installation-2026-09-28.md), not the retained
developer Test. `VDP-TIMEOUT-01` remains explicitly deferred. Factory, simulator
and service binaries are not rebuilt for this check.

**Verdict: functional sequence PASS after explicitly documented engineering
first-use corrections; complete installer qualification remains open.**
Gateway trust and the live transport proof passed. The same simulator/actor is
attached without scene recreation. Service preparation exposed a separate
installed-path defect; the four-profile transient proof and source regression
passed, and Brake 94/V1 was prepared through an explicit engineering continuation,
published, installed and functionally checked. VDP118/119/120, Brake94/95/96
and Tire50 were installed and checked in order. Both advisory paths and separate
resets, offline/online delivery and full ignition power-cycle recovery pass.
Native installer launch and irreversible Finish are not claimed complete; the
Test is deliberately retained for the next launch gate. This continuation does not qualify
automatic first use of unchanged Kit009 or an unrelated clean Mac.

## Exact installed target

- Kit 009 manifest: `f20b6d501ac5c0e257532a41507e68bbd8039d6d5e07b499b8dc53610dcd28e1`.
- Private instance: `~/SDV-Lab-Clean`, ID `191c70c8-6cb5-487d-9be0-3f06691c9812`.
- Installed CLI Presenter PID at observation: `96566`.
- Test VM: `8f380832-3eff-4fc3-94d8-a778dd33f492`, Factory `.39`, SSH port `10022`.
- Runtime owner: `ad878c0d-9d73-4d1f-99d9-bacace48e8d7`.
- Cloud Unit: `ee0a8607-5359-47ee-b5a6-4f50568d2b3a`.
- Cloud Node: `50d8b2c5-4e10-46c2-9335-b5b8598a2aff`.

Initial operator actions below used the installed Presenter. Its authenticated
workers retain Cloud API authority; no Cloud browser operation was used.
Read-only local process, journal and Docker inspections supplement UI receipts.
The subsequent trust initializer proof and controlled simulator stop used
explicit engineering paths documented below, not invisible package edits.

## Controller creation and old-resource collision

The first **Create controller** created and booted the new Test, presented the
native VM-access prompt and enrolled its SSH access. It then stopped at
`BACKEND_FOREIGN_VOLUME`. The exact VM was preserved; this was not a boot failure.

The old developer owner `ac995ea1-6fa9-4098-acfd-0ff37db07b23` had retained named
backend volumes/networks after its explicitly completed Test retirement because
its journal also retained Production. The new owner correctly refused to adopt
these resources. This is a same-Mac migration collision, not evidence that a
genuinely clean Mac has foreign resources or that ownership checks should relax.

Read-only preflight established completed old-Test retirement, stopped backend
owners, no referring containers and zero application rows for both the Test and
all nonmatching identities. Both product and isolated mock databases were
checked. Schema metadata was not mistaken for vehicle records. Only the exact
empty old volumes were deleted under the operator's cleanup authorization:

- `aosedge_demo_brake_cloud_v1`;
- `aosedge_demo_tire_cloud_v1`.

The SQLite files occupied approximately 116 MiB logically before removal.
Physical disk reclamation was not separately measured. Removal is irreversible,
but the removed volumes contained no application records. Production's local
VM and Factory `.31`, Factory `.39`, source, credentials and published releases
were not removed.

The first explicit **Continue preparation** then identified
`BACKEND_FOREIGN_NETWORK`. Exact owner/team labels and zero endpoints were
confirmed before removing only `aosedge-demo-brake-cloud-v1` and
`aosedge-demo-tire-cloud-v1`. No global prune, force removal, ownership adoption
or unrelated Docker change was used. The second explicit continuation completed
at **13:27:46 UTC**, reusing the same VM and completing `start-backends`.

Fresh inspection confirmed both containers **running/healthy**, both volumes
owned by the new runtime owner and both networks with that owner and exactly one
endpoint. The initial VM-start step was not repeated.

Evidence-harness corrections: a read-only SQLite source needs a disposable copy
for WAL metadata; the first RAM-copy allowance was too small. Neither failed
probe changed the source or removed resources. A bounded 160-MiB RAM filesystem
and network-disabled, read-only helper completed the row-count proof. Helpers
were automatically removed. An initial network-name filter used underscores;
the final exact-name inspection used the actual hyphenated network names.

## Reproduced first-use trust gap

**Start simulator** failed closed in approximately **3 seconds**, with UI receipt
at **13:31:06 UTC**: `SOURCE_OPERATOR_TLS_REQUIRED`. The fresh instance has no
`.local/demo-control/tls` directory, hence no `server-cert.pem` or `server-key.pem`.
No simulator/source run was created and no fallback credentials were adopted.

`SourceDriver.assets()` requires this server pair before native spawning. The
[installed-state contract](../../contracts/distribution-installation/installed-state.md)
deliberately treats absent operator TLS as a prerequisite and forbids importing
developer trust. The existing native wizard selects OEM/SP PKCS#12 references,
not local Gateway server trust. Existing `source_trust.prepare_local()` creates
client-CA/dashboard material, not this server pair. Therefore successful Cloud
authentication cannot satisfy the missing local transport prerequisite.

Classification: **unimplemented first-use dependency**, not a VDP timeout, Cloud
permission regression, CARLA crash or absent package binary. Silently copying
the developer key, generating a placeholder, disabling TLS, adding system trust
or changing the accepted local-trust lifecycle is not an authorized workaround.

The operator subsequently accepted a unique private Gateway server identity per
installed instance. The [accepted contract](../../contracts/distribution-installation/local-gateway-trust.md)
was added before implementation. Source and live transport qualification are in
the [Gateway trust receipt](installed-gateway-trust-2026-09-28.md). No old key was
copied, system trust installed or TLS/mTLS rule relaxed. Kit 009 consumed the
pair initialized by an explicitly recorded rapid-proof helper; it was not
silently patched and is not evidence of automatic packaged first-use.

## Simulator continuation and cold-start finding

The first start after initializing trust stopped at
`SOURCE_SIMULATOR_READY_TIMEOUT` at **14:04:38 UTC** (about 181 seconds overall).
The exact native process was preserved. CARLA launched at approximately
**14:02:38.587 UTC**, but a bounded sample at **14:05:30 UTC** showed `_dyld_start`
with approximately 112 KiB footprint and no application log or RPC listener.
The macOS security log reported the exact application's scan finished at
**14:06:29.729 UTC**; native execution and log output then progressed. Read-only
strict code-signature verification passed. The evidence supports delayed OS
first-execution scanning, not invalid package bytes or a Gateway TLS failure.
The precise division of scan, storage and scheduling time is not measured.

Record **CARLA-FIRST-START-01**: the installed cold launch can outlast the
readiness budget before CARLA reaches its main code. Do not disable Gatekeeper,
strip quarantine, resign the payload or fold this into `VDP-TIMEOUT-01`.
Improved first-launch progress/budget behavior and cold-Mac qualification remain
separate follow-up work; no timeout was changed in this continuation.

After localization, the normal installed CLI stopped only the owned simulator
group. The same VM, trust material and unprovisioned state were preserved. One
deliberate warm **Start simulator** from Presenter then completed in **43 s**
at **14:10:47.656 UTC**, with source run
`0f69e818-49da-4ef6-9a58-0f0b3fb7b92a`. Its timeline records vehicle ready,
first VSS frame, verified VISS and keyboard ready. The native dashboard shows
**LIVE**, **Safe Stop**, zero speed and **Not assigned**. Advisory unavailability
is expected before VDP/service installation and Unit selection.

## Independent preparation and regression evidence

**Prepare VDP V1** completed in approximately **4 seconds**, UI receipt at
**13:32:02 UTC**, producing unsigned candidate **118.0.0 / V1** from packaged
inputs. The existing release-continuity path observes Cloud release numbers;
fresh local state did not reset the sequence. The candidate was not signed or
published, and no VM component changed.

The targeted `test_host_runtime`, `test_runtime_paths` and `test_cloud_first_use`
suite passed **42 tests** with isolated, no-bytecode Cloud-runtime Python. An
earlier invocation with host-runtime Python passed the 31 host/path tests but
could not import the synthetic-certificate suite because that interpreter does
not include `cryptography`. Correcting the test interpreter required no product
change, dependency installation or modification of immutable runtime files.

Internal free space after creating the VM was about **91.6 GiB**; Work retained
about **561.6 GiB**. Keep the 90-GiB internal guard for subsequent large artifact
work. These observations do not authorize more cleanup or a Factory rebuild.

## Remaining ordered gates

1. Preserve the passed immutable Kit 010 installed-code proof and this Test;
   distinguish the explicit Kit 009 rapid helper from automatic UI first-use,
   which remains a later candidate gate. Track the cold-start finding above.
2. Preserve the completed VDP118/V1, Provision and stationary attachment below.
   The selected installed kit remains immutable; separately qualify the source
   service-preparation correction in a successor kit before claiming a fully
   automatic installed flow.
3. Publish VDP and Brake releases **one at a time**, verifying each installation
   before publishing its successor. VDP installation uses Safe Stop; retain the
   accepted service update behavior. Include Tire, live advisory, independent
   resets, offline/local processing and delivery recovery, and ignition checks.
4. Only after E2E completion, add and qualify the guarded native launch action
   through existing Demo Control. Do not confuse this CLI launch with that gate.

## Published VDP V1 and first attachment

The operator's continuation followed the exact VDP118/V1 publication and current
Test Provision request. The installed Presenter invoked the existing authenticated
workers; no Cloud website was used. Production was not changed.

| Observation (UTC) | Result |
| --- | --- |
| 14:48:02–14:48:12 | One Sign & publish operation, completed in about 10 s |
| 14:49:02.326 | Authoritative Cloud publication `READY`, VDP118/V1 |
| 14:49:42.413–14:50:28 | Provision completed in about 46 s; new Unit Online |
| About 14:51:17 | Explicit native Safe Stop, stationary vehicle |
| 14:51:19 | Guest VDP118 active; installation record and process slot agree |
| 14:53:59 | Presenter `Cloud installed · 118.0.0`; no pending successor |

The component ID is `77f85bd8-70ec-4683-9207-af8eaed20821`, deployment ID
`98699edf-5c59-4575-bd4a-978d5e151c5c` and version ID
`f86f5fd8-9ca7-437f-9451-610250b08dee`. Guest observation reports slot `a`,
seven read paths, `ADVISORY NOT_APPLICABLE`, process active, success and
`NRestarts=0`; provider status is `VDP data READY; source LIVE; reason NONE`.
This is provider-reported readiness, not yet independent Brake consumption.
The source run/actor remain `0f69e818-49da-4ef6-9a58-0f0b3fb7b92a` / `25`;
the new attachment is assignment generation 1. No scene or VM recreation.

**INSTALLED-RECOVERY-COPY-01:** immediately after initial Provision, the UI
briefly described connection restoration "after ignition on" and Safe Stop,
although this was a first attachment in stationary Manual and no ignition had
occurred. The boot observer records `OBSERVED` at 14:50:42, not a recovery
attempt. Its busy flag spans read-only observation as well as actual recovery.
Track this presentation inconsistency; do not infer a physical reboot from it.

## Installed service configuration routing

**INSTALLED-SERVICE-PREPARE-01:** native **Prepare Brake V1** blocked at
14:54:58.147 UTC after about two seconds with
`SERVICE_PACKAGE_PREPARATION_FAILED_VERSION_RETAINED`. Release **93.0.0** was
reserved; no prepared directory, signature or upload resulted. Its number is
not reclaimed or reused.

Read-only reproduction identified `INSTALLED_FOREIGN_STATE_ROOT`: Prepare
passes the selected, manifest-verified `preparation-inputs` root to the package
configuration reader, which incorrectly routed it through the private-state
root validator. The contracts exist and their integrity checks pass. All four
service profiles share this path; this is not a Brake-only model or VM failure.

A transient in-memory correction recognizes only the selected instance's exact
immutable input group, retaining rejection of foreign state and input roots.
All four real product configurations passed the official schema unchanged;
two negative root cases failed closed. The release ledger and installed bytes
remained unchanged. Source correction is limited to `service_packages.py`, an
installed full-Prepare regression and the standalone installed-state probe's
actual input-root coverage. No permission, model, protocol or timeout changed.

Targeted regression: **75 tests passed in 9.037 s**, with the explicit existing
signer runtime and no skipped tests. The first invocation omitted that optional
runtime and passed 74 with one skip; it is not the final gate. Tests use isolated
fixtures, no credentials, Cloud mutation or live VM changes.

One guarded engineering continuation used the installed code with only that
configuration function corrected in process. It prepared **Brake94/V1** at
**15:01:53.313 UTC**, using the normal Cloud catalogue read, persistent allocator,
schema validator and instance release directory. The Presenter observed the
new candidate and enabled Sign & publish. The installed Kit009 bytes and version
selection were not changed. This closes package formation, **not** the normal
UI Prepare regression on a corrected installed candidate. Repetition requires
a new deliberate operation; the helper has an exclusive intent receipt.

The exact follow-on publication request covers Brake94/V1 and fresh remaining
VDP/Brake/Tire profiles on this same Test, strictly one publication after each
previous installation and functional check. The operator subsequently directed
continuation of the agreed sequence without routine continue/stop questions.
Brake94/V1 publication completed; Cloud reported `READY` by 15:10:25 UTC.

## Existing-account Subject reconciliation

**INSTALLED-EXISTING-SUBJECT-01:** first Deploy at 15:11:45 UTC returned
`SERVICE_SUBJECT_UNRECORDED_LABEL_COLLISION` before a Cloud mutation. Public
runtime-input preparation completed, but assignment had empty step intents.
The fresh instance lacked the exact retained Subject references from the earlier
same-OEM demo. This is not a failed package, missing service permission or reason
to delete/recreate Cloud resources. Existing-access setup did not detect this
first-use gap.

Read-only reconciliation used exact previously recorded UUIDs, not a label-based
adoption: Brake Subject `78d05c9c-cdf6-45cc-ab28-df2a4d3ac0d7` with service
`cabba557-061d-4f44-9385-5b1b03e34186`, and Tire Subject
`ae69c0f8-28cc-4469-bb04-0f4fdd7db2eb` with service
`b845eef2-bf81-4035-895f-4a013d6b956f`. Fresh authoritative GETs confirmed the
selected OEM, exact creator/type/priority, one intended service per Subject,
zero desired/reported Unit recipients and no current runtime assignment.

A guarded explicit engineering reconciliation at **15:16:09.651 UTC** wrote
only those verified public references to the existing selected-Cloud
`demoSubjects` map, under the environment writer. It re-read Cloud before the
write, retained an exclusive intent/completion receipt and proved all other
journal fields unchanged. No credential, model, prior VM or historical run state
was copied; no Cloud POST or deletion occurred. This is not a completed automatic
existing-account installer flow; add an explicit exact-identity reconciliation
UX before claiming that qualification. Unknown create responses or matching
labels alone remain insufficient and blocked.

The subsequent normal Presenter Deploy at approximately **15:16:40 UTC** used
the now-recorded exact identity. By **15:17:00 UTC**, Cloud reported Brake94
installed with one active instance. Its backend had a current real function
report at 15:16:57 UTC, initially waiting for input. A dedicated native Brake
Maneuver produced a complete 75-sample recording with 8/8 chunks: event time
15:17:26 UTC and backend receipt 15:17:33 UTC. A fresh function report at
15:17:37.870 UTC arrived at 15:17:37.877 UTC, with input RECEIVING and an empty
delivery queue. V1 provides capture, not condition analysis or local advisory.

## Sequential V2 continuation

VDP119/V2 was prepared and published through Presenter at approximately
15:22 UTC. While native Autopilot was moving at 19.4 km/h, Presenter showed
the pending successor and guest observation still showed VDP118 active with
the transaction waiting for Safe Stop. Explicit native Safe Stop then allowed
installation at **15:23:23 UTC**. Guest slot `b`, exact version119, 15 read paths,
active process, provider READY and zero restarts agree with Cloud installed119.
Advisory remains NOT_APPLICABLE for VDP V2.

Brake95/V2 was prepared at 15:24:13.708 UTC by the same bounded, single-use
configuration-routing continuation. Immutable Kit009 bytes are unchanged.
Autopilot resumed after VDP installation; service publication was then started
once through Presenter without another Deploy or Safe Stop. Cloud showed one
active Brake95 instance by 15:25:13 UTC; native driving was independently
observed at 19.3 km/h. A real Brake Maneuver produced MONITOR, score40/100,
source/receipt at approximately 15:25:45 UTC. V2 correctly reports advisory
NOT SUPPORTED; earlier V1 recordings remain in the backend.

## V3 platform and Brake advisory

VDP120/V3 followed only after V2's result. Publication at approximately
15:26:47 UTC remained pending during Autopilot. Native Safe Stop allowed the
installation at **15:27:26 UTC**: slot `a`, 23 read paths, active/READY,
NRestarts0 and Cloud installed120. Enabled advisory configuration alone was
not counted as a functional advisory proof.

Brake96/V3 was prepared at 15:28:03.589 UTC using the same recorded transient
routing correction, then published once through the installed Presenter.
Cloud reported one active instance by 15:28:58 UTC. No repeated Deploy was used.
Native telemetry moved to Monitoring; Tire showed Waiting for service.
A dedicated Brake Maneuver generated assessment
`f3ff6a76-0ac4-5685-bc66-e19a3d3746a9` at 15:29:32.271 UTC, durably received
at 15:29:32.399 UTC: score34/100, INSPECTION_RECOMMENDED. The native dashboard
showed that recommendation, and a fresh backend advisory fact confirmed
Gateway APPLIED. Current function input is RECEIVING, delivery IDLE/0 queued.
The 15:30:53 read retained two assessments across V2/V3 and observed SM, CM
and VDP active/success with zero automatic restarts.

Tire50/V1 preparation completed15:30:32.742 UTC. Its publication completed and
normal Presenter Deploy started15:32:05 UTC, using the exact reconciled Subject.
Cloud reported one active instance50 by15:32:28. The real Tire Maneuver produced
INSPECTION_RECOMMENDED, score69/100 and confidence93%, source and receipt at
15:33:03 UTC. Gateway APPLIED/Service ACK CONFIRMED and the native recommendation
agree. Brake remains installed and functional; no peer assignment was replaced.

## Independent resets and Return to road

Brake reset was requested at approximately15:34:59 UTC and confirmed CLEAR
at15:35:04. Its native recommendation returned to Monitoring while Tire retained
INSPECTION_RECOMMENDED. Tire reset at15:35:31 completed at15:35:34; Tire then
returned to Monitoring and the Brake model was byte-for-byte unchanged in the
bounded projection. The three Brake assessments/one event and one Tire
assessment/one event are unchanged across both resets. Thus history is retained,
not deleted or mistaken for a new result. UI differentiates pending and confirmed
reset and does not claim that CLEAR alone proves telemetry readiness.

Return to road completed in stationary Manual with both models retained and
without automatically selecting Autopilot. Subsequent native external OFF was
authoritatively observed at **15:36:45.852 UTC**. Cloud transitioned Offline;
the backend cards eventually displayed Last known / Not confirmed and disabled
Reset while the native vehicle remained LIVE.

The settled-OFF,15:38:22 and15:41:42 snapshots have the same backend result and
function-observation receipts. Real Brake and Tire maneuvers nevertheless
advanced both local models and regenerated INSPECTION_RECOMMENDED, visible in
native telemetry. Queues contain six messages per service at that intermediate
read. SM/CM/IAM/KAC/VDP remain active with zero automatic restarts, unchanged
boot ID and Enforcing policy. Only the previously known SSH directory-search
AVC category appears; no SEGV appears in the bounded window. This is not a
claim of a clean all-domain AVC audit.

External ON was observed at **15:42:14.711 UTC**, after328.86s in the OFF state.
The final offline snapshot captured16 Brake and23 Tire queue messages. All39
identities matched exactly one durable backend receipt after ON: the last
captured Brake receipt is15:42:24.600 (9.89s after ON observation), Tire
15:42:44.508 (29.80s). The first post-ON snapshot was non-atomic: its backend
read preceded Tire delivery while its later guest read still showed a queue.
That early snapshot remains retained and is not rewritten as success. A later
15:44:17 snapshot confirms both queues empty and both current observations
restored, same boot/processes, Cloud ONLINE and versions120/96/50 unchanged.
The result comparison passes12 predicates including independent reset/history,
unchanged offline receipts, local recommendations and exact-once captured drain.
No service restart or manual replay was used to obtain recovery.

Ignition OFF was requested at15:44:43.852 UTC only after a fresh exact-identity,
Safe Stop and empty-outbox preflight. Graceful guest poweroff returned0 at
15:44:47.886. This engineering power-cycle gate retains the owned disk and
identity; it does not claim a native ignition control exists in Presenter.
QEMU absence was confirmed at15:45:40.575 UTC. Normal installed VM-start began
at15:46:04.412 and completed at15:46:40.652 (36.24s). The Presenter-owned recovery
ran15:46:54.319–15:47:07.956 (13.64s), about63.54s from the ON intent. It restored
the same Unit/Node, source run, actor25 and assignment1 without provisioning,
manual reattachment or automatic Autopilot. Boot ID changed as expected.

Post-cycle comparison passes: exact installed120/96/50, no pending/errors,
storage UID/inodes and local models retained, physical Safe Stop0km/h, queues
empty. Each manager and VDP reports active/success/NRestarts0. The controlled
CM endpoint-restoration restart remains separate from automatic crash counters.
Fresh post-boot evidence contains only the known SSH-search and getty
checkpoint_restore AVC categories and no SEGV; Enforcing is retained.

Post-ignition Brake and Tire maneuvers generated new results by15:48:56 UTC.
The final15:49:23.970 snapshot shows Brake assessments5→7 and Tire2→3, new local
model inputs, fresh APPLIED advisory facts and both outboxes empty. The final
comparison passes **24 predicates**. These checks do not cover cold offline
ignition, nonempty-outbox power loss, continuous frame-by-frame absence of
readiness flicker, new-account onboarding or a physically clean Mac.

Internal free space was about87GiB at15:46 UTC, below the90GiB guard for large
artifact work; Work retains561GiB. No large rebuild or cleanup was initiated.
Small source/native-target work is separate from that package gate.

When Vehicle was reopened after time on team screens, resource cards first
showed older samples as Last known, then refreshed to current samples. They did
not present those cached readings as current or block Reset. The exact refresh
latency was not continuously instrumented.

The read-only evidence adapter initially expected the developer journal's
`factory` object; installed journals omit it. It exited before guest reads or
mutations. The adapter now guards the exact retained VM/Unit/Node and uses the
installed runtime; this harness correction does not alter the product.

## Diagnostic consistency and final local checks

The modern read-only source observation reports `CONNECTED`, selected Test,
`perUnitMtls ACTIVE`, `serverTls true`, `mutualTls true`, VDP active/READY and
zero VDP restarts. Its evidence is the authenticated Gateway role combined with
provider-reported readiness, not a fabricated independent service result.

**COMPONENT-DIAGNOSE-MTLS-01:** the older `component diagnose` Safe Stop section
reports absent certificate/private-key files, mismatched profile/endpoint/path
fields and an SSL failure. Source inspection explains the contradiction: it
looks for credentials beside public platform inputs and assumes the old binding
schema. Current trust supplies private files through systemd `LoadCredential`
and uses the accepted role/identity/generation binding. The normal connection
probe and the completed FOTA are positive evidence; do not copy keys to public
inputs, relax TLS or infer a broken live connection from this obsolete probe.
The schema part did correctly observe all 23 telemetry and six typed advisory
leaves; that does not mean VDP V1 publishes all of them. The diagnostic correction
remains separate from the service-package routing fix.

An initial evidence summarizer mistakenly read the generic CLI `data` field;
status is under `status`, so its null summary was discarded. The corrected
read returned the explicit positive source observations above, without printing
certificates, keys, fingerprints or arbitrary state.

Documentation gate passed: 308 Markdown documents, 662 identifiers, 38 diagrams.
`git diff --check` passed. Compact ignored proof files are
`probe_installed_service_config_20260928.py` (read-only/transient four-profile
proof), `prepare_brake_installed_proof_20260928.py` and its exclusive completion
receipt (one real local preparation). These are engineering evidence, not new
operator instructions or modifications to immutable installed bytes. Source
regression includes the complete Prepare caller path with isolated fixtures;
the installed successor-kit/UI gate remains open.

## Evidence retained locally

Ignored evidence under `CarlaSim/Build-distribution-stage2-20260926/` includes
`clean_e2e_empty_volumes.py`, the single-use intent and completion receipt
`clean-e2e-old-empty-volumes*.json`, and
`clean-installed-e2e-tls-blocked.png`. The screenshot shows actual completed
controller creation, the explicit TLS blocker and completed local preparation.
It contains no certificate/key content. Later transport, candidate and screenshot
evidence is indexed in the Gateway receipt. No new commit or push is claimed.
