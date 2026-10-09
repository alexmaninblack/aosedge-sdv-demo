<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# macOS developer preparation reference

The normal route is now the standalone preparation wizard in
[README B1](../../README.md#b1-prepare-tools-storage-and-access).
Download it, review it, run it, and load its generated environment as shown
there. No Git checkout, Python or Homebrew is required to start the wizard.
This page is a reference, not another six-block copy/paste prerequisite.

The wizard is implemented in [prepare-macos.sh](../../scripts/prepare-macos.sh).
Its offline fixtures cover control flow and failures; the owner's actual
first-use walkthrough remains pending. No live installation or build was run
to publish this implementation.

<a id="1-select-the-mac-and-storage"></a>

## What the six stages do

| Stage | Reuse/check | Missing or incompatible prerequisite |
| --- | --- | --- |
| 1. Mac and storage | Native Apple Silicon, macOS 26+, existing writable local APFS, volume identity, available GiB | Explain the problem; never format a disk or fall back after disconnect |
| 2. Apple tools | Selected Xcode, completed first-run setup, macOS SDK 26+, Swift and Git | Ask the user to install/open Xcode and complete Apple's prompts; preserve the global Xcode selection |
| 3. CMake and Python | CMake/CTest >=3.24; native Python 3.12; project virtual environment with packaging | Install missing Homebrew bottles and create/reconcile the owned project environment; do not upgrade an incompatible existing formula automatically |
| 4. Node and npm | Exact versions from the current source requirement projection | Install a checksum-verified ARM64 Node distribution and the required npm inside the workspace, not over a global installation |
| 5. Docker and Drive | Existing Docker CLI/Engine, local Linux ARM64 context, Google CLI and selected account access | Install missing casks; leave Docker first-run/start to the user; request Google login only if credentials/scope need it |
| 6. Signing and inputs | Available Apple Development identity and both private Drive bindings | Select an identity by number; explain missing files/access; never create/export a key or sign a package |

The screen shows a plan before changes and asks for one preparation confirmation.
Xcode, Homebrew, Docker and Google can still require their own system/account
prompts. Preparation does not bypass those controls or constitute entitlement
to private inputs.

Host tools retain their standard locations (Xcode/Docker under Applications,
Homebrew under /opt/homebrew, credentials in their existing stores). The project
workspace, isolated Python/Node, downloads and caches use the selected volume.
Package managers can install required dependencies; the wizard does not request
global upgrades, cleanup, Engine restarts, shared storage moves or shell-profile
edits. Homebrew's [installation](https://docs.brew.sh/Installation) and
[command reference](https://docs.brew.sh/Manpage) describe its own behavior.
Google's [login reference](https://docs.cloud.google.com/sdk/gcloud/reference/auth/login)
describes the consent flow.

## Result and next step

Only `READY FOR SOURCE PREPARATION` makes the environment handoff usable.
It means the six preparation checks passed, including read-only Drive metadata
access. It does **not** mean a complete build fits, a candidate is qualified,
the signing key has been exercised, or private archives have been verified.

The 90 GiB selected-volume reserve is a preparation floor, not an estimate of
the complete build. The same conservative free-space floor is checked at
Applications/Homebrew locations before installing host packages; an external
workspace does not provide space for those host tools. After cloning, use the existing build-space planner to
check workspace and Docker capacity and compatibility with exact build owners.
The frozen candidate retains its older external-only producer policy;
preparation does not rewrite source pins or make that policy disappear.

`PREPARATION INCOMPLETE` or `ACTION REQUIRED` means resolve the listed action
and rerun the same downloaded script. The script never clones source,
downloads CARLA/Factory archives, compiles code, signs outputs, provisions a
Cloud Unit, or launches the demo.

## Repeats, saved choices and diagnostics

Small private control files are kept in
`~/Library/Application Support/AosEdge SDV Lab/Developer` (directory 0700,
files 0600). Selections are data, not executed shell input. They contain paths,
a volume UUID, the account name and a public signing fingerprint, never a token,
certificate body or private key. No changes are written to .zshrc or .zprofile.

Each run rediscovers installed tools and rechecks their versions. It does not
trust an earlier success flag. Compatible tools and verified downloads are
reused. A failed/interrupted preparation cannot leave a newly usable success
handoff. Normal cancellation releases the owned lock; a later run recognizes
a dead lock owner. Unexpected lock contents and active owners are preserved.

The generated `environment.sh` supplies the explicit `SDV_*` variables and
session paths used by the build guide. Load it using the short README block,
including after opening a new Terminal. It rejects a disconnected/replaced
selected volume. Rerun preparation when tools, credentials or inputs change;
the environment file is not perpetual readiness evidence.

Install diagnostics live under `<workspace>/.developer-preparation`; ordinary
progress stays short. Google authorization is never captured in these logs.
Interrupted owned Python/Node setup can be completed on repeat. A bad archive,
unowned directory or incompatible existing package is preserved and reported,
not silently overwritten or deleted.

Optional diagnostics (not another mandatory preparation sequence):

```sh
/bin/bash "$HOME/Downloads/aosedge-prepare-macos.sh" --check
```

This mode does not install, download, log in, create state or contact Drive.
It checks local tools, Docker and input-file structure where available. Exit 0
means local checks passed, **not** full access readiness; exit 2 lists missing
prerequisites. Fatal host/storage or unsafe-state errors exit 1.

To review/change the saved account, binding files and signing selection:

```sh
/bin/bash "$HOME/Downloads/aosedge-prepare-macos.sh" --configure-access
```

Use `--parent /absolute/existing/folder` to explicitly choose a different
workspace parent, or `--xcode /path/to/Xcode.app` for a nonstandard Xcode.
Paths with spaces are supported when quoted as command arguments. Interactive
path answers are literal: do not add shell quotes. Scratch must stay on the
selected volume and fit the existing 29-byte limit.

The two private input files still come from the release owner. Metadata checks
verify access and declared roles without downloading payloads; authoritative
lock-digest/content checks remain with `lab inputs prepare` after cloning.
No OEM/SP certificate is needed for this developer preparation.
