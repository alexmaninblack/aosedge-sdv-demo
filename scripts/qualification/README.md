<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# M1 qualification scenarios

Run a complete scenario, not a conversation-driven sequence of commands.
The development Mac orchestrates; installation, browser/native UI, simulator
and live runtime checks execute on the dedicated M1 using its internal storage.
Only offline unit/fixture checks run on the development Mac.

This tooling is not an installer or another runtime/Cloud authority. Signed
Setup and Demo Control perform product operations. Tests use semantic controls
and independently observed effects; an SSH launch receipt is not UI acceptance.
See the [execution policy](../../docs/governance/rapid-development-and-debugging.md#scenario-execution-policy)
and [current baseline](../../docs/qualification/current-baseline.md).

## Choose one scenario

| Entry | Purpose |
| --- | --- |
| `campaign.py` | Deliver the pinned DMG, install/prepare through Setup, run the ordered API journey and close owned runtime resources |
| `native_controls_campaign.py` | Complete visible M1 browser/native-control campaign with independent effects, timings and cleanup |
| `setup_first_use_campaign.py` | Separate signed native Setup first-use profile, including certificate issuance for existing authorized accounts |
| `ui_pilot.py` | Bounded diagnosis or explicitly selected visible M1 UI scenario on an existing Test; not a substitute for the complete campaign |

Prepare the exact private target/candidate selection before starting. A private
plan binds the M1, immutable media/manifest, Cloud domain and owners, Test policy,
applicable scenario and record directory. The plan grants no new signing,
publication, deletion or Cloud authority. Do not copy identities or completed
receipts from a different candidate or domain.

The fixed native first-use profile derives its M1 paths from the validated SSH
user and the journey's `instanceRoot` / `storeRoot`, not a developer's account
name. Its existing producer certificates are read locally under the invoking
user's `~/.aos/security prod/`; they are not the newly issued M1 certificates
and are never copied to the target. This path portability does not change the
profile's fixed Test/Unit, candidate, Cloud-owner or at-most-once issuance guards.

For the API installation/journey campaign:

```sh
python3 -B scripts/qualification/campaign.py \
  --config PRIVATE_SSH_CONFIG --journey PRIVATE_JOURNEY_CONFIG \
  --dmg /absolute/path/to/Lab.dmg \
  --remote-dmg /Users/tester/SDV-Qualification/candidate/Lab.dmg
```

For the complete native-controls campaign:

```sh
python3 -B scripts/qualification/native_controls_campaign.py --plan PRIVATE_CAMPAIGN_JSON
```

These are maintainer scenario entries, not operator installation instructions.
Use the [normal installation route](../../docs/getting-started/installed-preview-cloud-first-use.md)
to install and use the lab.

## Preconditions and immutable binding

Check the selected M1, unlocked desktop, required native Accessibility grants,
network access, matching signed package, existing installation and account-level
Cloud compatibility before costly preparation or a live mutation. Freeze whether
the scenario retains an existing compatible Test or prepares a new one.
Local directory separation does not isolate Cloud resources.

For a retained-Test package-update campaign, the private journey may explicitly
bind `retainedTest` to its existing UUID. The API profile then validates that
binding and runs the complete publication, product/advisory, Reset, offline,
ignition and Stop/Start matrix without Create, provisioning or credential/
Subject replacement. Its backend prerequisite is a read-only check of the exact
stopped image bindings and current package inputs, not another image import or
backend activation. Record those fresh-first-use gates as outside this profile,
not inherited passes. A changed Test fails closed. Use the new candidate's own
media/installation records; never rebind a predecessor's campaign receipt.
The retained Cloud prerequisite authenticates the already selected pair and
checks its domain, pinned owners and publication permissions without repeating
the fresh-Setup certificate-selection operation.
The retained profile uses ordinary Start demo to restore both VM and backend
owners, then starts the simulator and connects the existing Test before FOTA.
It must not reuse the fresh-Provision ordering or publish before reconnecting
the authenticated source. Interrupted FOTA recovery remains the native runtime's
responsibility; this profile never deletes its transaction or bypasses trust
restoration guards to continue.

Use the existing OEM/SP account topology. Production Cloud requires an explicit
`cloudDomain: aoscloud.io` plus authenticated OEM/SP owner IDs in the private
selection. A Test vehicle in Production Cloud is not a Production-role vehicle.
Unselected domains, changed owners and retained Production-role resources remain
outside the campaign.

Media is verified against its receipt at the actual consumer boundary. Reuse an
unchanged verified file and healthy tool cache; do not copy or hash a multi-GB
DMG again merely for a status update. The persistent launcher must match the
selected installed package; runtime installation alone is not that proof.
For media built on M1, `--dmg` and the UI plan's `dmg` may explicitly name its
small `.receipt.json` on the orchestrating host. The payload must already exist
at `remoteDmg`; the normal consumer checksum, signature, mount and installation
checks still run. Missing media fails closed without a transfer fallback. This
avoids copying an M1-built DMG to the development Mac merely to copy it back.

Capacity preflight counts the 90 GiB reserve, unpacked runtime and any missing
DMG copy separately. A capacity refusal may use `--resume-capacity-preflight`
only after proving the new version, staging transaction and receipt are absent
and normal owners are quiescent. A mount-induced ctime-only change requires
checksum verification of the existing file, not another transfer.

Presenter browser identities are process-scoped opaque references, not native
Cloud UUIDs. Keep the exact Test/Unit binding in the private M1 observer and
use the public reference when checking browser responses or selecting an
allowed browser operation. Validate the native journal and real backend effects
independently; never restore full IDs to the browser to satisfy an older test.
The API outbox/delivery checks use the private backend observation, while UI
Reset/history checks use the same opaque projection as the displayed product.
Native session/request IDs retain their separate public at-most-once protocol.

## Visible M1 execution

The current browser scenario uses `--display m1`. It shows the real Presenter
web build in its signed Chrome app-mode window on M1. CARLA and Driving Control
start through their normal owners and use the canonical settled layout. A locked,
missing, minimized, displaced or obscured required surface stops the relevant
check instead of silently switching to background execution.

Native mouse input uses the separately signed semantic runner and current
Accessibility identifiers, not recorded coordinates. A fixture-only pilot
checks mechanics; connected vehicle acceptance also requires the ordinary
product handler and independent vehicle/service effects.

The Chrome web surface, native WKWebView shell and signed Setup are different
acceptance surfaces. Do not present one as proof of another. Visual readability
and human review are separate from a geometry receipt.

The old development-side background-browser walkthrough is retired. Its presence
in an older Git revision is not permission to run live tests on the development
Mac. Low-level adapters remain implementation/diagnostic details, not a second
recommended campaign.

## Ordered actions, results and recovery

Publish and verify each VDP/Brake version before publishing the next. VDP FOTA
installation uses Safe Stop; QM service SOTA may run while moving when the
selected scenario calls for it. Switch to Platform for the independent
publication-card checks. Reset, return-to-road, offline and ignition checks
retain their ordinary product guards and declared scope.

Moving SOTA waits up to 120 wall-clock seconds for actual fresh, unheld
Autopilot motion above 3 km/h before publishing. Traffic Manager road stops and
below-real-time simulation do not authorize stationary publication, weakened
freshness checks, forced traffic lights or another control input. This bounded
wait is a test scheduling budget, not a service/provider timeout change.

Persist intent before mutation. On timeout or response loss, observe and
reconcile the exact operation rather than replaying input. A terminal failed or
uncertain mutation does not authorize Finish, another installation, another
publication or a replacement Test. Use only the existing explicit continuation
or reconciliation mode after its preconditions have been established.

A run records its actual scenario definition, correlated effects, timed phases,
bounded redacted diagnostics, PASS/FAIL/BLOCKED/NOT_RUN gates and cleanup.
Historical step counts or a mechanical fixture pass cannot establish current
API, native Setup, browser UI or full-product acceptance. The
[current proof map](../../docs/qualification/current-baseline.md) owns those claims.

Private access inputs and expiring credentials stay outside packages and public
reports. Explicit unattended VM access uses the existing owner-private profile;
ordinary installation still uses native secure input/Keychain. Automation does
not satisfy the separate secure-input UI gate by itself.

## Unattended test access

The operator also authorized reuse of the development Factory password for
automated Test enrollment. A locally supplied test credential may be provisioned
once into an owner-private installed-instance qualification profile, bound to
the instance UUID, explicitly authorized Cloud domain and exact Factory SHA-256. The value is not
shipped in the DMG, committed, displayed, passed in argv/environment or copied
into qualification reports. This is an explicit test configuration, never an
implicit developer-Keychain fallback or permission to operate a Production-role
vehicle. The current approved campaign uses Production Aos Cloud with a Test
vehicle; environment and vehicle role are independent. An invalid profile
fails closed instead of opening a dialog. An absent profile preserves ordinary
native first-use behavior; the unattended runner requires it before Create.
The ordinary console login, per-VM SSH key and pinned host-key exchange remain
mandatory. Known-host reuse after enrollment does not require the password.

This accepted test-only exception refines the interactive first-SSH rule in
[Demo Control](../../docs/architecture/demo-control.md). It does not test native
password entry and must be reported as engineering access preparation.

A partial Create can bind the same unprovisioned Test for diagnosis/shutdown
only after its terminal job and validated vehicle journal agree; this is never
a passed Create. Before cleanup, retain fixed reason codes and bounded job and
lifecycle projections, not raw logs or exception text. Candidate changes require
new evidence bindings. Ordinary secure input and native consent remain separate.

## Cleanup and retained evidence

Close only scenario-owned browser/native clients, helpers, simulator, VMs and
demo containers through their normal owners. Verify process/listener exit.
Stopping preserves Unit identity, VM disks, models, history and release ledgers;
it is not Finish or retirement. Reuse shared Docker Engine without opening its
Dashboard or restarting it as a routine test step.

Keep current release/campaign receipts and the private configuration needed to
resume. Remove obsolete fixture packages, screenshots and one-off scripts after
ownership, dependencies and open handles are checked. Do not restore entire
ignored directories into a clean checkout. Keep source, reusable tool caches,
runtime data and compact evidence distinct.

## Offline checks

The qualification tooling's unit fixtures do not start the demo:

```sh
python3 -B -m unittest discover -s scripts/qualification -p 'test_*.py'
```

The integration source suite is documented in
[Contributing](../../CONTRIBUTING.md). A green source test does not qualify a new
DMG, mutate the selected option A or replace the M1 campaign.

Earlier pilot instructions, intermediate failure narratives and dated command
walkthroughs remain recoverable in Git history, not as competing current guides.
