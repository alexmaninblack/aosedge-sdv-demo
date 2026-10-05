<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Native Setup Permission Continuity — 29 September 2026

- Status: Local signed-build permission continuity passed after explicit Accessibility migration; clean-host qualification remains separate
- Version: 1.2
- Prepared: 2026-09-29
- Owner: Demo Solution Team
- Source base: `22ee79e0e21709de34803c6db20047847138eba0`, with existing uncommitted work preserved
- Contract: [native setup v1.5](../../contracts/distribution-installation/native-setup.md)
- Previous evidence: [native launch](native-presenter-launch-2026-09-28.md),
  [travel pause](installed-pause-2026-09-28.md)

## Resume and preservation

Both SSD volumes were reconnected with their recorded UUIDs: Work
`591578E3-8196-4B44-A575-CEC76B406789`, Clean
`870130E1-51A1-4ED8-841E-DB84B7941376`. Device numbers changed and were not reused
as identity. Internal free space was approximately 89 GiB, Work 561 GiB.
No large package/image work was started below the 90 GiB reserve.

Installed instance `191c70c8-6cb5-487d-9be0-3f06691c9812` still selected Kit 009
`f20b6d501ac5c0e257532a41507e68bbd8039d6d5e07b499b8dc53610dcd28e1`, revision 1,
previous null. No Setup, Presenter, CARLA or QEMU owner/listener was observed
at resume. No Test lifecycle, Cloud operation, package selection, credential
copy, service/Factory rebuild or model reset was performed. `VDP-TIMEOUT-01`
remains deferred.

## Cause and scope

Preview 015 still has `Signature=adhoc`, no TeamIdentifier and a designated
requirement bound to its executable's code hash. Earlier previews have different
code hashes. The previous store-open trace aligned with macOS removable-volume
consent, not a package-copy or VM operation. Changing this identity explains
why accepting access for an earlier preview does not qualify the next preview.
Historical untraced long opens are not retroactively classified as this fault.

Apple documents that a designated requirement identifies successive versions
of code: [TN3127](https://developer.apple.com/documentation/technotes/tn3127-inside-code-signing-requirements).
The source fix uses a normal Apple Development signature and verifies its
generated requirement; it does not bypass macOS privacy controls.

An initial sandboxed `security find-identity` incorrectly appeared to show zero
identities, and sandboxed disk/process checks were unavailable. Repeating these
read-only checks with normal system visibility found one valid Apple Development
identity for Alex Agizim and confirmed the mounted UUIDs/stopped owners. The
premature user-facing conclusion that a certificate was missing was corrected.
No private key or certificate content was read/exported. The user subsequently
authorized that identity for local Setup signing. All signing below used that
existing Keychain identity; no certificates were created or exported.

## Source correction and tests

The build now requires exactly one of `--signing-identity <exact identity>` or
the explicit engineering-only `--ad-hoc`. Discovery, identity type and exact
match checks run before package copying/compilation. Failed signing never retries
with a weaker identity. Signature checks verify bundle ID, authority, Team ID
and a non-code-hash designated requirement. The receipt records signing mode
and requirement digest, but always leaves actual consent qualification false.
There is no custom requirement, added entitlement, TCC reset, trust change or
network timestamp request.

Before source consolidation, 11 temporary signing fixtures passed. Targeted
Setup suites then passed 72 tests. The subsequent full distribution suite passed
256 tests, including explicitly enabled process-ownership checks, with no skips.
Two additional build-boundary tests cover failure before artifact creation and
the single bundle-ID authority. Their first combined invocation exposed a test
harness import-path omission, not a signing attempt or failed artifact. With
the normal builder import path restored in that fixture, the final suite passed
**258 tests, no skips**, in 6.740 seconds. Documentation validation passed for
311 Markdown documents, 662 stable identifiers and 38 Mermaid diagrams;
`git diff --check` passed. These fixtures do not prove that macOS reuses consent.

## Authorized signed build and native continuation

Built preview 016 against unchanged Kit 009, with 2,430 verified bootstrap
files, native protocol self-test, signature verification and embedded helper
probe all passing. Signing mode is `apple-development-local-only`, Team ID
`3NF57VKB3V`. Native executable SHA-256:
`540cffb63cf6e809718ba80f2ad9f34264a69bc47e47529c975a1be57cef61b9`.
No network timestamp request or notarization was performed.

First Open was clicked at **06:46:53.731 UTC**. The accepted workspace operation
ran 06:47:07.301–06:47:08.873. Presenter server PID 34127 and host PID 34214
started and were retained. The UI correctly reported **Presenter needs
attention**, not success: no removable-disk prompt was observed, but window
geometry was unavailable to the Setup-launched observation. A separate CLI
observation saw exact geometry and verified ordering; that is not native success.

Both Accessibility and System Events switches displayed On in macOS settings.
Nevertheless, an isolated diagnostic copy 017, opened explicitly at
**06:53:47.569 UTC**, recorded only fixed error fields and proved macOS rejected
window observation with **-25211 / assistive access**. No raw scripts, stderr,
window contents or credentials were recorded. This establishes a real permission
denial rather than inferring trust from an old settings checkbox. The user later
authorized rebinding Accessibility to the signed Setup; no Full Disk Access,
screen recording or other new permission is included.

The changed 017 code signature had a different CDHash from 016, while both had
the same designated-requirement SHA-256:
`2cd6abe5ddd0ce9733dbcd1762af34ba64136679033c1cabd22d4482e16dd11c`.
Both read the selected SSD package without another visible removable-volume
prompt. This is same-host access evidence, not a fresh-account consent grant,
reconnect qualification, or proof that all permission categories are shared.

After a temporary native compile/protocol proof, the source now checks its own
Accessibility trust **before** starting any launch helper. Preview 018 includes
this correction, the same stable requirement, no diagnostic instrumentation,
and native executable SHA-256
`ad479c955197fbebb011e5825f06024df410a41c4407f2663eabb97cbc987bc0`.
Build/signature/bootstrap/protocol checks passed. At **06:58:04.380 UTC**, Open
immediately showed **Accessibility permission needed** (UI tool response under
one second). Job count remained exactly two; server/host PIDs and instance
selection were unchanged. The permission check neither requested nor granted
OS access. The final distribution regression again passed **258 tests, no skips**,
in 9.415 seconds.

The diagnostic copy was closed, not left running. Preview 018 remains open.
Adding the exact signed app through System Settings reached the normal **Touch
ID or Mac password** authentication sheet. That system-owned authentication
subsequently completed and exposed the file chooser. The exact preview 018 app
was selected, but macOS left Add/Open disabled for the existing bundle entry.
The selected Setup-only Accessibility switch was turned off/on under the user's
authorization. Actual trust remained false, including after quitting/reopening
018. Both negative checks returned before creating a helper/restore; job count
stayed two. No other app's switch was changed.

The stale row could not be selected for removal through the available UI.
A separately bounded request was sent to revoke only the old Setup bundle's
Accessibility entry with the supported system reset, then explicitly add 018.
At that checkpoint, the reset had not been executed. It required explicit
authorization as a one-time migration exception; the installer must never reset
permissions itself. The authorized continuation is recorded below.
No password was guessed/entered, no grant bypass or TCC database editing was
attempted. Positive native acceptance was pending at that checkpoint.

Evidence under the ignored CarlaSim qualification directory includes
`setup018-accessibility-attention.png` and `setup-accessibility-touchid.png`.
The fixed-code diagnostic is `/private/tmp/sdv-setup017-window-proof.jsonl`.
Prior ad-hoc/native candidates and the retained Test are preserved.

## Explicitly authorized Accessibility migration and live results

The operator explicitly approved resetting only the old Setup Accessibility
entry and adding the signed version. Setup was closed first. One supported
`tccutil reset Accessibility org.aosedge.sdvlab.setup.preview` invocation
succeeded; only the Setup row disappeared from System Settings. No other
permission category or app was reset, and no TCC database was accessed.

The exact preview 018 app was then added through the ordinary System Settings
file chooser. Its Accessibility switch became On. This was a one-time migration
from previous ad-hoc previews, not an installer feature or a new implicit grant.
No additional Full Disk Access, recording, Automation or SSD permission was
requested. Native Open subsequently passed the actual trust check and verified
the owned Presenter windows, rather than relying on the checkbox alone.

| Native test | Explicit Open (UTC) | Success observed by (UTC) | Result |
| --- | --- | --- | --- |
| 018 after exact permission migration | 08:15:41.615 | 08:16:02.371 | Presenter opened; original server/host reused |
| 018 explicit same-process repeat | 08:16:26.852 | 08:16:52.747 | Presenter opened; no duplicate owners or new prompt |
| 018 after Setup quit/reopen | 08:17:24.497 | 08:17:45.022 | Presenter opened; grant retained |
| Different signed binary 016 after the 018 grant | 08:17:58.736 | 08:18:31.204 | Presenter opened; grant reused across different code |
| Return to 018 after Work remount and stopped server | 08:21:03.210 | 08:22:04.202 | Presenter opened; no new permission prompt |

These observation times are upper bounds, not exact UI completion latency.
For the first row, the single restore ran 08:15:49.128–08:15:50.224 UTC.
The server/host remained 34127/34214 with session
`dd1214dc-dc55-4ec2-9391-c349c44cf699`; no vehicle runtime started. The restore
jobs were PARTIAL because CARLA/control were deliberately parked; the native
result correctly distinguished verified Presenter geometry/order from full
demo readiness. Cross-build testing reused the existing immutable 016, whose
executable differs from 018 but has the same designated requirement. No new
large package or artificial source change was needed for this proof.

After those checks, the ordinary installed `workspace close` and idle `ui stop`
completed. All observed Work-volume file holders exited. The exact Work UUID
was checked before a normal, non-forced unmount and again after remount. Clean
was not unmounted. This is a logical volume reconnect test, not a physical cable
disconnect, OS reboot, or fresh-user qualification.

After remount, preview 018 passed actual Accessibility trust and SSD reads
without another visible permission prompt. It started exactly one new server
(64251) and native host (64434); previous owners were absent. The new session
`339ffe1c-ddae-4515-ab60-d59a0c598ca1` contained exactly one restore, running
08:21:13.640–08:21:15.131 UTC. Final native output was **Presenter opened** with
verified geometry/order and the expected simulator/controller-not-ready note.
No operation was active, uncertain, or workspace-busy at the final check.

Selection still had the exact Kit 009 pin, revision 1, previous null and instance
UUID recorded above. Current Vehicle remained null. Retained Test VM
`8f380832-3eff-4fc3-94d8-a778dd33f492`, Unit
`ee0a8607-5359-47ee-b5a6-4f50568d2b3a` and Node
`50d8b2c5-4e10-46c2-9335-b5b8598a2aff` were unchanged. No provisioning,
publication, reset, VM/simulator start or Production mutation occurred. The
unchanged build receipts retain `consentPersistenceQualified: false`; live
qualification is this dated report, not an edited artifact receipt.

Evidence includes `setup018-accessibility-restored.jpg` and
`setup018-presenter-opened.jpg` in the ignored qualification directory. No
production source or immutable kit was changed by this continuation.

## Qualified boundary and remaining gates

The local native slice now passes actual permission migration, first/repeat
Open, Setup quit/reopen, different signed executables (018 → 016 → 018), and
logical Work-volume remount with a stopped-server start. The first permission
grant remains an operator-controlled OS prerequisite; it is not bypassed.

Physical disconnect/reconnect, OS restart, certificate renewal and a genuinely
clean OS account/Mac remain distinct from these same-host proofs. No universal
one-prompt guarantee or permission sharing with other apps is claimed.

Developer ID/notarization, a genuinely clean Mac, secure new-account enrollment,
Subject first-use UX, service-Prepare packaging and CARLA cold-first-start remain
separate gates. This signing slice does not close the whole installer.

No source commit/push or cleanup of retained artifacts was performed. Small
transient signing fixtures, native proof source and diagnostic app are retained
until the live gate finishes. After successful compilation and zero-open-handle
verification, the disposable compiler directory
`/private/tmp/sdv-setup-accessibility-compile.rqn3tQ` was removed; it can be
regenerated from the preserved proof source. No generated certificate/key is
present there. No VM, CARLA or backend was started.
