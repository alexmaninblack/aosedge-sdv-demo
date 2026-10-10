<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# M1 installation and E2E verification on 10 October 2026

The original source-built `1.2.0-rc.1` DMG exposed a backend build-file permission
defect after successful M1 installation and VM password enrollment. The defect
is corrected in source; rebuilt r5 media has now passed a separate fresh M1
installation and backend-image preparation. Its live staging journey is paused
at first VM-password enrollment and **not complete**. Earlier Kit028 results do not qualify either
candidate. Candidate identities and recovery evidence are separated below.

## Candidate and target

| Item | Observed value |
| --- | --- |
| Launcher checkout revision | `61a9e3aa9eb67bf6124855cd118b1cecf510cf52` |
| Media | `AosEdge-SDV-Lab-1.2.0-rc.1.dmg` |
| Media bytes | 14,149,387,680 |
| Media SHA-256 | `2c254a636f5db22bbcf59f0d68823ee60e3b861ede32b3c3d7373a834daad149` |
| Kit manifest SHA-256 | `affc73fa1e9e2188ad00062a67cccf3ccab9c7e00e2a01d82ec60dd557d0d10e` |
| Setup executable SHA-256 | `da81027db7ac1104193a3f58870fca67b15f287a84ecea9703713343363e0455` |
| Factory selector | `6.1.1-maninblack.41/main-qemuarm64` |
| Mac | M1 Pro, MacBookPro18,3, 16 GiB RAM |
| macOS | 27.0.1, build 26A434 |
| Storage | M1 internal disk, approximately 335 GiB available before transfer |
| Cloud | `aws-stage.epmp-aos.projects.epam.com` only |
| Signing | Local Apple Development, not notarized |

The launcher revision identifies the checkout that produced the chain. Payload
owners remain bound by the chain's frozen source locks, not by an assumption
that every component uses the latest main branch.

## Installation results

| Check | Result | Duration |
| --- | --- | --- |
| Transfer through pinned direct Ethernet SSH and verify destination SHA-256 | PASS | 169.70 s |
| Read-only media mount, strict Setup signature and embedded pin | PASS | 82.09 s |
| Shipped Setup preflight | PASS | 5.43 s |
| Shipped Setup installation with complete payload verification | PASS | 122.31 s |
| Fresh private instance preparation and selection | PASS | 35.19 s |

Installation copied 17,697 files with 35,456,497,135 logical bytes. It ended at
`INSTALLED_NOT_ACTIVATED`; preparation separately ended at
`SELECTED_NOT_STARTED`. Neither operation accessed Cloud or started the demo.
No developer state or credentials were copied into the installation.

The new store and instance are separate from the previous manual installation.
Only its unused mounted media was detached; the previous installation, media
file and preserved credentials were not deleted. Existing OEM/SP certificates
are consumed through explicit private file references on M1.

## Installed journey

The fixed [scripted journey](../../scripts/qualification/README.md) uses the
installed product owners and private interpreter. Docker Engine is reused
without opening its Dashboard or restarting it. Each VDP/Brake version must be
installed and checked before the next is published.

Installation binding, Docker readiness, backend images, existing Cloud access,
exact Brake/Tire Subject references and Presenter server startup have passed.
Create Controller manufactured one unprovisioned Test and reached the ordinary
secure Factory VM password dialog. The first prompt expired without input.
An operator-requested continuation then failed on the optional Save in Keychain
path with `VM_KEYCHAIN_SAVE_FAILED`, before SSH enrollment. A further explicit
continuation reopened the native Use once path, but that prompt also expired
after 180 seconds. No duplicate controller or Cloud Unit was created by these resumptions.
After the operator supplied the password, continuation completed `start-test`,
enrolled VM access and reached `start-backends`. Brake returned
`BACKEND_COMMAND_FAILED`; the lifecycle remained partial. Subsequent deployment,
maneuver, offline and ignition checks are not yet passed.

### Backend permission defect

The installed Brake image starts its HTTP server, but `/health/ready` returns
503 with `DATABASE_UNAVAILABLE`. All five public SQL migration files are owned
by root with mode 0600. The process runs correctly as UID 1000 and cannot read
them. The source checkout on the build SSD has the same private modes, inherited
from the launcher's umask; Docker COPY preserved them. Tire has the same defect:
UID 1000 receives `EACCES` for its main module and package metadata.

A network-disabled, read-only disposable container using the exact Brake image
reproduced `EACCES`. Copying only the same public SQL bytes into its temporary
memory-backed directory with readable modes allowed fresh schema 5 creation
and a second startup of that database: both returned HTTP 200 / `ready: true`
under UID 1000. Original images, Test volumes and package bytes were unchanged.
The disposable containers exited and were removed.

The build adapter now exports a bounded pinned Git tree into private owned
scratch with explicit public file modes, excluding Git metadata and untracked
inputs. Its versioned context policy invalidates the affected image keys.
Four context regression tests and 91 existing reproduction tests passed.
Twenty chain tests, eight build-result tests and 29 cache/capacity tests also
passed (152 targeted tests in total). The source correction is committed as
`82dc1cca93645e0e5d4597dc41c32d5010fc7c81`. The r5 qualification plan pins that
revision only for component production; unaffected producer roles remain
unchanged. The public launcher is not yet promoted to this qualification plan.

Both corrected images were then tested directly, without permission patches,
as UID 1000 in disposable network-disabled, read-only containers with a
memory-backed database directory. Fresh and repeated database startup returned
HTTP 200 / `ready: true` for Brake schema 5 and Tire schema 4. Context readiness
correctly stayed unavailable without a provisioned vehicle. Image identities:

- Brake: `sha256:7a76fa8a9f100a2d8d5a98575554b91857bc958144e78954883f85c916f604f9`.
- Tire: `sha256:c6c90b66ee33ae5f11e19957d579317dfc5f10c7cc770e43fb22317275c6e64f`.

These image checks do not qualify the full DMG. Corrected media assembly and
its fresh M1 installation/journey are tracked separately from the failed
candidate; CARLA and Factory are reused rather than rebuilt.

### Corrected media

All 17 steps of the r5 source-build chain completed on the selected build SSD.
The resulting media remains `CHAIN_BUILT_NOT_QUALIFIED`, not a promoted release.

| Item | Corrected candidate |
| --- | --- |
| Build chain | `81bcdb5e30d3e2004d054d82b3d92949464d595863b3b97d92e05358a352072b` |
| Media bytes | 14,160,792,575 |
| Media SHA-256 | `e4fdebfe11762f6aaeba519fbc158df40151f866f62028160524d6b70bbf3ed3` |
| Kit manifest SHA-256 | `57c61087778b31a0c50bc513ea44f53a2d2d5461287ae8cc88962585eeb81fc0` |
| Setup executable SHA-256 | `52fd323896a7d9ba586b7e5f749e9d17fa4f48a1d0d629d0bb2ed012e388f870` |
| Installation instance | Fresh `SDV-E2E-R5` on the M1 internal disk |

Corrected-candidate private records use `m1-e2e-r5-20261010-install` and
`m1-e2e-r5-20261010-journey` under the same qualification-record parent.

Transfer/checksum (171.16 s), mount/signature (79.65 s), preflight (5.28 s),
installation (122.34 s), preparation (35.28 s) and backend image preparation
(7.63 s) all passed on M1.

The attempted selection of the corrected package for the old instance was
blocked by the intentional `CURRENT_RUN_RETAINED` rule. Read-only reconciliation
confirmed the old selection and Test were unchanged. No selection guard,
package file or journal was altered to bypass that rule.

For disposal only, the known public-file permission correction was applied to
the writable layers of the old exact-owned containers, preserving file bytes,
image identities and the non-root service identity. The temporary helper first
rejected Tire TypeScript/schema files; it stopped the containers and restored
the original modes. After reconciling the saved retirement phase, the corrected
helper normalized only the observed public source/schema files. Normal Finish
then completed its backend checks and removed the unprovisioned Test, its
overlay, owned containers and empty storage. No Cloud object existed or was
deleted. Temporary changes disappeared with the retired containers. This is
cleanup recovery evidence, not a passing installation or product acceptance
test for either candidate.

The corrected candidate's fresh full scripted journey started after that
retirement. Its separate records, not the cleanup recovery, establish results.
Installation binding, Docker readiness, prepared backend images, existing Cloud
pair/access, exact Subject references and Presenter startup passed. Create
manufactured one new Test, then the native VM-access dialog expired after its
180-second input budget. No VM access was enrolled, no Cloud Unit was created
and no component/service was published for this new Test.

Read-only reconciliation confirmed the completed local manufacture, partial
`start-test` phase with `VM_ACCESS_CANCELLED_OR_DIALOG_UNAVAILABLE`, and an idle
Presenter with no uncertain external operation. The harness again lacked the
new Test binding for its automatic shutdown; after exact-identity reconciliation,
normal shutdown passed in 12.56 seconds. Its explicit process/listener checks
passed, while Docker Engine and persistent Test/installation data remained.
The Screen Sharing connection used for the check was closed. Current scripted
results are eight passes (including shutdown), one incomplete Create and 89
steps not run. Resume this same retained Test after native password entry; do
not manufacture another Test, reuse the old candidate's enrollment or treat
this paused sequence as full E2E acceptance.

The runner classified the incomplete Create as uncertain and its automatic
cleanup could not bind the partially created Test (`TEST_IDENTITY_CHANGED`).
Read-only reconciliation established a completed local manufacture, no Cloud
Unit, an idle Presenter with no uncertain operation, and the exact failed
lifecycle phase. The ordinary product Create supports continuing that partial
record without manufacturing again. Historical attempts are retained; none was
rewritten into a pass. This recovery is separate engineering evidence, not a
claim that first-use password cancellation or Keychain saving passed.

## Evidence and remaining acceptance

Private development-side records are under
`.local/remote-qualification/m1-e2e-20261010-install` and
`.local/remote-qualification/m1-e2e-20261010-journey`. They retain the exact
candidate, attempt outcomes and timings without secrets. The latter is the
authority for individual scripted steps and uncertain-operation reconciliation.

Native operator interaction, moving SOTA, native secure-token entry and target
installation interruption/repair remain separately assessed gates. This run
uses existing Cloud accounts and credentials, not new account enrollment.
Host sleep/wake and external-SSD operation are excluded from the M1 internal
storage campaign. Deferred readiness and VDP timeout investigations are not
silently reopened or declared fixed by this run.

For the original candidate, at 11:10 UTC, ordinary shutdown passed with zero owned demo processes and
listeners. Docker Engine and persistent installation/Test state were preserved;
Finish was not executed. The scripted summary is eight passes (including
shutdown), one unresolved Create and 89 steps not run. No components or services
were published during this run.

The original Test is now retired through the recovery described above; its fault
evidence is retained. A new candidate has new bindings and qualification records;
no pass is inherited merely from the former installation. The Keychain save
failure and the harness's handling of partial Create remain separate findings.
A fresh Test has its own VM-access enrollment.
