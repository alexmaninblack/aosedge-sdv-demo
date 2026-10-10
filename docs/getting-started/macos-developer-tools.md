<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# macOS developer preparation reference

The normal route is now the single developer build launcher in
[README B1](../../README.md#b1-prepare-tools-storage-and-access).
Download it, review it and run it. It passes its environment and continues
through checkout, verified inputs and the developer DMG build automatically.
No Git checkout, Python or Homebrew is required to start the wizard.
This page is a reference, not another six-block copy/paste prerequisite.

The wizard is implemented in [prepare-macos.sh](../../scripts/prepare-macos.sh).
Its offline fixtures cover control flow and failures; the owner's actual
first-use walkthrough remains pending. No live installation or build was run
to publish this implementation.

The default route needs no Google account or Google CLI. The owner-authorized
public test inputs and pinned catalog are available through the current launcher
in README B1. Download it again if an older copy reports
`PUBLIC RELEASE NOT YET AVAILABLE`. Public access does not complete the
[redistribution review](../development/public-artifact-preparation.md) or qualify
a build. An access failure never silently falls back to private access.

<a id="1-select-the-mac-and-storage"></a>

## What the six stages do

| Stage | Reuse/check | Missing or incompatible prerequisite |
| --- | --- | --- |
| 1. Mac and storage | Native Apple Silicon, macOS 26+, existing writable local APFS, volume identity, available GiB | Explain the problem; never format a disk or fall back after disconnect |
| 2. Apple tools | Selected Xcode, completed first-run setup, macOS SDK 26+, Swift and Git | Ask the user to install/open Xcode and complete Apple's prompts; preserve the global Xcode selection |
| 3. CMake and Python | CMake/CTest >=3.24; native Python 3.12; project virtual environment with packaging | Install missing Homebrew bottles and create/reconcile the owned project environment; do not upgrade an incompatible existing formula automatically |
| 4. Node and npm | Exact versions from the current source requirement projection | Install a checksum-verified ARM64 Node distribution and the required npm inside the workspace, not over a global installation |
| 5. Docker and public inputs | Existing Docker CLI/Engine, local Linux ARM64 context, anonymous input availability | Install Docker only if missing; leave first-run/start to the user; no Google CLI installation or login |
| 6. Signing and inputs | Available Apple Development identity; compatible release selected automatically from the pinned public catalog | Select an identity by number; explain unavailable/incompatible releases; never ask ordinary users for JSON paths or create/export a key |

The screen shows a plan before changes and asks for one workflow confirmation,
including the build/signing continuation unless `--prepare-only` was selected.
Xcode, Homebrew and Docker can still require their own system/account prompts.
Preparation does not bypass those controls or constitute redistribution approval.

Host tools retain their standard locations (Xcode/Docker under Applications,
Homebrew under /opt/homebrew, credentials in their existing stores). The project
workspace, isolated Python/Node, downloads and caches use the selected volume.
Package managers can install required dependencies; the wizard does not request
global upgrades, cleanup, Engine restarts, shared storage moves or shell-profile
edits. Homebrew's [installation](https://docs.brew.sh/Installation) and
[command reference](https://docs.brew.sh/Manpage) describe its own behavior.

## Result and next step

Only `READY FOR SOURCE PREPARATION` makes the environment handoff usable.
It means the six preparation checks passed, including the source-pinned public
catalog record and anonymous input availability/length checks. It does **not**
mean a complete build fits, a candidate is qualified, the signing key has been
exercised, or full archive checksums have been verified.

The 90 GiB selected-volume reserve is a preparation floor, not an estimate of
the complete build. The same conservative free-space floor is checked at
Applications/Homebrew locations before installing host packages; an external
workspace does not provide space for those host tools. After cloning, the launcher calls the existing build-space planner to
check workspace and Docker capacity and compatibility with exact build owners.
The public launcher selects the reviewed storage-aware successor owners;
historical candidate plans retain their original policy and source pins.
Project and Docker storage may be separate local volumes. Neither preparation
nor the build moves shared Docker data or restarts its Engine.

`PREPARATION INCOMPLETE` or `ACTION REQUIRED` means resolve the listed action
and rerun the same downloaded script. Default mode continues by cloning the
root and pinned component sources, acquiring verified inputs and invoking the
existing compiler/packaging/signing owners. It never provisions a Cloud Unit,
installs the resulting DMG, publishes services or launches the demo.

Use `--prepare-only` to stop at the original preparation boundary. `--check`
remains non-mutating and never enters checkout/acquisition/build. The complete
route ends with `BUILD COMPLETE` and the exact DMG/receipt paths, explicitly
labelled as an engineering candidate, not a qualified release.
The result stays on the selected disk; the launcher does not upload it or
publish a release automatically.

## Repeats, saved choices and diagnostics

Small private control files are kept in
`~/Library/Application Support/AosEdge SDV Lab/Developer` (directory 0700,
files 0600). Selections are data, not executed shell input. They contain paths,
a volume UUID and a public signing fingerprint (plus the account name only in
explicit private mode), never a token,
certificate body or private key. No changes are written to .zshrc or .zprofile.

Each run rediscovers installed tools and rechecks their versions. It does not
trust an earlier success flag. Compatible tools and verified downloads are
reused. A failed/interrupted preparation cannot leave a newly usable success
handoff. Normal cancellation releases the owned lock; a later run recognizes
a dead lock owner. Unexpected lock contents and active owners are preserved.

The generated `environment.sh` supplies the explicit `SDV_*` variables and
session paths. The launcher loads it itself; manual loading is only for the
optional engineering reference. It rejects a disconnected/replaced
selected volume. Rerun preparation when tools, credentials or inputs change;
the environment file is not perpetual readiness evidence.

Install diagnostics live under `<workspace>/.developer-preparation`; ordinary
progress stays short. Google authorization is never captured in these logs.
Interrupted owned Python/Node setup can be completed on repeat. A bad archive,
unowned directory or incompatible existing package is preserved and reported,
not silently overwritten or deleted.

The workspace's `root-source.json` under `.developer-preparation` binds the root
commit, prepared requirements and volume before source acquisition. A restart
does not follow an updated `main`. Existing clean matching checkouts can be
adopted, but local edits, changed commits and foreign repositories are preserved
and rejected. The preparation lock spans the continuation; an additional
workspace lock prevents two continuations. `workflow.json` records diagnostic
progress, not readiness: repeats ask each canonical owner to verify/reuse its
results. Neither failed stages nor incomplete native outputs are blindly retried
within a run. Partial clone/download state is retained for a deliberate rerun.

Optional diagnostics (not another mandatory preparation sequence):

```sh
/bin/bash "$HOME/Downloads/aosedge-prepare-macos.sh" --check
```

This mode does not install, download, log in, create state or contact Drive.
It checks local tools, Docker and input-file structure where available. Exit 0
means local checks passed, **not** full access readiness; exit 2 lists missing
prerequisites. Fatal host/storage or unsafe-state errors exit 1.

To review/change the saved signing selection:

```sh
/bin/bash "$HOME/Downloads/aosedge-prepare-macos.sh" --prepare-only --configure-access
```

Use `--parent /absolute/existing/folder` to explicitly choose a different
workspace parent, or `--xcode /path/to/Xcode.app` for a nonstandard Xcode.
Paths with spaces are supported when quoted as command arguments. Interactive
path answers are literal: do not add shell quotes. Scratch must stay on the
selected volume and fit the existing 29-byte limit.

## Automatic release selection

The wizard reads `release-index.json` through a source-reviewed public download
link; it does not search a user's Drive. The link and public-record SHA-256 are
compiled into the standalone script. The link is a locator, not an authority:
the selected record must match its independently reviewed source checksum.
No OAuth, API key, browser session, cookies or publisher credentials are used.

The index keeps `schemaVersion`, `catalogRevision`, product versions and
dependency identities inside JSON, not in its filename. Adding a release keeps
older records intact. The script selects its compatible record, never the
newest filename, timestamp or version. No match, unsupported schema, duplicates,
changed checksums or denied access produce an actionable failure, not a manual
JSON question or an implicit fallback. A missing/private catalog asks the
release owner to correct publication; login is not the remedy.

Only the bounded catalog is downloaded (maximum 1 MiB). Each of the five archive
checks reads one byte and requires a matching total length in `Content-Range`;
these checks do not claim complete content verification. Public schema-2 input
selections are generated in the existing private preparation state, atomically
and with mode 0600, for `lab inputs prepare`. Repeats
reuse matching local files but still check remote access. Unexpected or edited
files are preserved and reported. This does not grant new readers or alter
sharing. No OEM/SP certificate is needed.

After cloning, the launcher checks the saved selection against the checkout's
dependency records, release definition and producer plan. A moving `main` cannot
silently combine a previously prepared selection with changed requirements.
Authoritative archive-content checks remain with `lab inputs prepare`.
It uses the same anonymous transport, preserves interrupted partial downloads,
checks the full size/SHA-256 against the Git lock before promotion/extraction,
and reuses the existing verified cache without contacting Google. Public access
cannot inspect private Drive parent/version metadata; it does not fabricate it
or relax the content pins to compensate.

For a large file Google can return a standard "cannot scan for viruses" page.
The downloader recognizes only its bounded expected form for the same file and
follows the normal download confirmation, without a browser or cookies. It
does not bypass malware/abuse denials. Unexpected HTML, sign-in redirects,
wrong ranges, changed bytes and quota errors fail explicitly without login
loops or alternate copies. Google documents temporary download limits and
recommends [dedicated hosting for large distributions](https://support.google.com/drive/answer/2423534?hl=en).

## Private maintainer route

This is an explicit compatibility route, not a fallback for ordinary users:

```sh
/bin/bash "$HOME/Downloads/aosedge-prepare-macos.sh" --private-inputs
```

Only this mode discovers/installs Google CLI, requests the reader's own granted
Google account and, when needed, offers consent. It retains the authenticated
name discovery and private metadata checks. It never asks for the publisher's
credentials. [Google's login reference](https://docs.cloud.google.com/sdk/gcloud/reference/auth/login)
describes that consent flow. At acquisition, maintainers add
`--account "$SDV_DRIVE_ACCOUNT" --gcloud "$SDV_GCLOUD"` to the guide's
`lab inputs prepare` command. Existing private bindings, caches and historical
catalog records remain usable.

Only release engineers needing the old explicit binding workflow use
`--advanced-inputs` (which explicitly selects private mode); both binding paths are then requested and their lock
digests are checked. This option is never entered automatically after a catalog
failure. Ordinary reruns ignore legacy manual binding selections and use the
catalog route. Historical `release-index-v1.json` receipts remain unchanged.

### Release-owner activation

After redistribution/content review, publish only the intended dependencies to
a separate public read-only distribution folder, not the historical artifact
root. Use the offline `scripts/preparation-catalog --public-links` option with
the existing historical receipt and a mapping of `buildInputs`/`simulation`
roles to approved persistent public download URLs. This replaces private
bindings with public ones, preserves byte/source pins and creates a distinct
immutable `-public` record; it does not change permissions or upload anything.
Publish the small `release-index.json` once and update that object in place
for later additions. Review its stable URL and generated record SHA-256 into
`PUBLIC_PIN` in `scripts/developer_catalog.py`, then run
`scripts/sync-preparation-catalog` to refresh the standalone wizard.

Offline fixtures and the prior synthetic 1 MiB/128 MiB transport proof do not
qualify actual large-archive delivery or grant redistribution rights. The
joint first-use walkthrough remains a separate check after activation.
