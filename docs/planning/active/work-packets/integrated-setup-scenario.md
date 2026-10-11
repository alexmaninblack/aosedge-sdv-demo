<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Integrated Setup user scenario

- Status: Implemented scenario; existing-access native acceptance passed; new-access gates open
- Date: 2026-10-11
- Parent: [Integrated Setup work packet](integrated-setup.md)
- Live qualification: Aos Cloud staging only

The operator receives one complete DMG, installs SDV Lab, connects one OEM and
one associated Service Provider, then opens Presenter. Setup hides packaging
and storage mechanics while preserving their independent verification. A
complete installation is not a manufactured or provisioned vehicle.

## First opening

The mounted DMG contains **AosEdge SDV Lab Setup**, **Runtime Kit** and **Start
Here**. Opening Setup displays the product name, a short purpose statement,
three numbered steps and one primary action. The default store is
`~/AosEdge SDV Packages`, private state is `~/SDV-Lab-Data`, and the persistent
launcher is `~/Applications/AosEdge SDV Lab.app`. Do not ask for those paths.
Advanced settings may change the package store before installation. Private
state remains internal; existing instances are never moved implicitly.

Read only the fixed sibling kit. Do not search mounted volumes, downloads,
developer checkouts or old kits. If no validated installed selection exists and
media is missing, say **Open Setup from the complete SDV Lab DMG**. If the media
does not match the independent pin, say **This installer and Runtime Kit do not
match**. Preserve existing files in both cases.

## Step 1 Install SDV Lab

The primary button is **Install SDV Lab**. It checks Apple silicon and supported
macOS, writable storage and required capacity, then checks the existing local
Linux arm64 Docker Engine before copying. Missing Docker displays **Install
Docker Desktop**, opens only the official installation page on explicit intent,
and offers **Check again**. An unavailable Engine asks the operator to start
Docker; Setup neither restarts it nor opens Dashboard when it is already running.

Run the existing preflight, verified installation, private-instance preparation,
version selection and backend-image preparation sequentially. Copying shows a
real byte progress bar. Other phases show a named indeterminate progress state;
do not fabricate percentages or time estimates. Finish by installing the small,
signed persistent launcher, without copying the Runtime Kit again. Replace only
an existing same-identifier, same-team signed launcher. A foreign application,
active selection lease, pending transaction or incompatible state blocks safely.

The completed screen says **Installed** and advances to Cloud access. It does
not say the vehicle is ready, does not create a vehicle journal, and does not
start Presenter, CARLA, a VM or backend containers. Backend images remain
Docker's independently observed state, not a stored boolean.

## Step 2 Connect to Aos Cloud

Offer **Use existing certificates** and **Get new certificates**. The first
route has exactly two file inputs: OEM certificate and Service Provider
certificate, then **Connect**. A native file picker saves no key contents. The
certificate Organization determines the domain; filenames and issuer names
do not. Show **Staging** or **Production** with the actual domain after inspection.
For other valid domains show the domain, not a guessed environment.

Connect inspects both private RSA PKCS#12 files, authenticates both roles and
their association, and checks component/service delivery permissions before
saving the pair. File/configuration/selection changes invalidate the result.
One atomic write stores references and authenticated public owner IDs through
the existing writer. Connect may prepare only the fixed absent Factory model
and empty Test verification set, using the existing durable attempt receipts.
It creates no Unit and publishes no package. Occupied or conflicting objects
are errors, not an invitation to delete or adopt them.

Show specific outcomes: incompatible domains, invalid certificate, wrong role,
unassociated SP, insufficient permission, missing prerequisite, occupied Test
set, lost response requiring reconciliation. Keep raw diagnostic codes under
Details. An unsuccessful operation must not leave a green connected indicator.

### New certificates

Ask **Staging** or **Production** first. Use the fixed reviewed mappings
`aws-stage.epmp-aos.projects.epam.com` and `aoscloud.io`. Offer the official
registration page for that environment and explain that Cloud may require
account confirmation or email. Do not claim anonymous registration is an
available API or embed privileged credentials.

Collect the OEM and SP issuance tokens in secure native fields. One **Get
certificates** action reconciles existing per-role receipts first, enrolls OEM
and then SP at most once each, and connects the returned pair through the same
validation path. A received OEM is retained when SP issuance fails. Never
repeat an uncertain issuance automatically; Details provides the existing
explicit inspection/recovery path. Clear secure fields when consumed and never
put tokens in arguments, environment, logs, preferences or evidence.

### Repair a missing Service Provider on a retained Test

The same Connect action can add the absent SP to a stable retained Test. Keep
the same selected OEM file, domain and authenticated OEM owner. Reject a changed
OEM, domain, established SP owner, pending journal/configuration write, or
incompatible/uncertain run. Authenticate the proposed SP and its OEM association
before saving. Reconcile under the existing writer and compare the run and pair
again before the atomic configuration write.

Preserve journal bytes, Unit identity, VM, installed VDP, release ledger, service
history and Subject references. This route makes no Cloud mutation and never
calls the fresh-instance preparation path. It is not a general replacement of
credentials or a weakening of the first-use guard.

## Step 3 Open SDV Lab

After independent installation, backend and Cloud checks, display **Ready to
open** and **Open SDV Lab**. Opening uses the existing Presenter launch owner,
port checks, selected package lease and workspace restore. Accessibility consent
remains a macOS action when needed. Explain that **Create Controller** in
Presenter starts the vehicle journey; CARLA and Driver Control are not expected
just from opening Presenter.

The demo proceeds through controller creation, simulator connection, provisioning
and serial VDP and service releases. VDP platform updates use Safe Stop; QM
service delivery does not replace that rule. Do not publish all versions before
the demonstration or preinstall the latest versions.

## Repeat opening and interruption

The installed launcher works after DMG ejection, without source or development
tools. Inspect the existing selected instance on opening; never trust cached UI
readiness. Resume the next incomplete setup phase. If local installation is
incomplete, require the original matching media. If certificates are missing or
expired, return to Cloud access. If Docker is stopped, request its start without
restarting shared infrastructure. Preserve a retained run and permit only the
bounded missing-SP repair described above. Reopening must not recopy verified
programs or replay uncertain enrollment, imports or Cloud writes.

Opening Presenter is not proof that a stopped controller has powered on. That
returning-runtime gate remains explicitly separate. **Stop** preserves a Test;
**Finish demo** is the separately confirmed irreversible retirement operation.
Setup itself never performs Finish. At the end of qualification, gracefully
stop owned consumers and verify exit, keeping shared Docker Engine and durable
run data.

## Implementation and acceptance order

1. Amend requirements, ADR 0018, native and Cloud first-use contracts with this
   scenario; retain old low-level actions for compatibility and diagnostics.
2. Implement the one-action local worker, read-only installed status, simplified
   native step presentation and persistent signed launcher.
3. Implement authenticated one-action Cloud connection, exact prerequisite
   preparation, bounded retained-Test SP repair and paired token onboarding.
4. Implement repeat launch and accurate error/continuation presentation.
5. Run automated positive, negative, interruption, idempotent, owner-conflict,
   redaction and protocol tests; compile native self-tests before packaging.
6. Build one matching signed candidate on SSD using retained Factory/CARLA.
   Test fresh and returning user paths on M1; record scripted and native results
   separately. Update guide and qualification record, then commit/push source.

Completion requires actual results for default install, existing pair, paired
token recovery, retained-Test SP repair, media ejection and repeat opening.
Unmeasured new-account signup, distribution notarization and cold controller
resume must remain explicit open gates, not implied by a Setup success banner.
