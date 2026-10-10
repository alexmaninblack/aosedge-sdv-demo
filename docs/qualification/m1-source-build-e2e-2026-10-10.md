<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# M1 installation and E2E verification on 10 October 2026

The newly built `1.2.0-rc.1` DMG has passed transfer verification and a fresh
installation on the separate M1. The Factory VM password was accepted and the
VM started. The installed staging journey then exposed a backend build-file
permission defect and is **not complete**. Earlier Kit028 results do
not qualify this candidate.

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
A corrected immutable package and its complete M1 journey remain required;
the transient proof does not qualify the failing DMG.

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

At 11:10 UTC, ordinary shutdown passed with zero owned demo processes and
listeners. Docker Engine and persistent installation/Test state were preserved;
Finish was not executed. The scripted summary is eight passes (including
shutdown), one unresolved Create and 89 steps not run. No components or services
were published during this run.

Do not blindly resume the failing image or request another password: VM access
is already enrolled. Preserve this Test and its fault evidence while building
the corrected candidate. A new candidate needs new bindings and qualification
records; no pass is inherited merely from the former installation. The Keychain
save failure and the harness's handling of partial Create remain separate findings.
