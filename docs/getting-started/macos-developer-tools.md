<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Prepare macOS for a developer build

This is tool preparation, not the operator installation route. These commands
are written for a future supervised walkthrough; they have not been executed
as part of the README revision. Use one native Terminal session and stop at
any error. Do not paste the whole page as a script.

## 1 Select the Mac and storage

```sh
uname -m
sw_vers -productVersion
printf 'Existing build parent directory (absolute path, internal or external disk): '
read -r SDV_PARENT
test -d "$SDV_PARENT"
SDV_DEVICE=$(df -P "$SDV_PARENT" | awk 'NR == 2 { print $1 }')
diskutil info "$SDV_DEVICE"
df -h "$SDV_PARENT"
```

Expect `arm64`, macOS 26 or later and a writable **local APFS volume**. For
example, select your existing home directory for internal storage or an already
mounted `/Volumes/BUILD` for external storage. Do not create a missing
`/Volumes/...` directory: it could put the build on the internal disk. If the
checks disagree, stop here. Check the selected release's space requirements
before acquisition; the DMG size is not the required build capacity.

The storage-aware scripts are a source update awaiting regression execution.
The currently frozen candidate's complete chain still requires the external
layout. Follow the [README storage/release boundary](../../README.md#b1-prepare-tools-storage-and-access)
before choosing a candidate; do not reinterpret its old producers as supporting
an internal or split-Docker build.

```sh
SDV_ROOT="$SDV_PARENT/sdv"
printf 'Short scratch directory on the same volume (for example /private/tmp/sdv on the internal Data volume): '
read -r SDV_TMP
test -n "$SDV_TMP"
test -d "$(dirname "$SDV_TMP")"
test "$(stat -f '%d' "$SDV_PARENT")" = "$(stat -f '%d' "$(dirname "$SDV_TMP")")"
mkdir -p "$SDV_ROOT" "$SDV_TMP"
export TMPDIR="$SDV_TMP"
export HOMEBREW_CACHE="$SDV_ROOT/cache/homebrew"
export PIP_CACHE_DIR="$SDV_ROOT/cache/pip"
export npm_config_cache="$SDV_ROOT/cache/npm"
```

The native test scratch path `SDV_TMP` must be at most **29 UTF-8 bytes**.
Use a short path on the same volume: for example `/Volumes/BUILD/tmp` for that
external disk or `/private/tmp/sdv` for the internal Data volume. The tools
reject scratch on a different volume; there is no automatic fallback. Host
tools/Xcode and account credentials still have their ordinary macOS locations.
Project sources, build outputs and large caches belong in the selected workspace.

## 2 Install Apple developer tools

Install Xcode from Apple's App Store, open it once, complete its license and
first-run components, then select that installation. For the standard path:

```sh
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
xcodebuild -version
xcrun --sdk macosx --show-sdk-path
xcrun swift --version
git --version
```

If Xcode is elsewhere, replace only the selected path. The complete installer
build needs the macOS SDK/Swift, not just Git. Follow Apple's
[command-line tools guidance](https://developer.apple.com/documentation/xcode/selecting-your-xcode-version-for-command-line-tools).
Component-only C++ checks can use Command Line Tools (`xcode-select --install`)
instead; that smaller route is not a complete packaging toolchain.

## 3 Install CMake and Python

If Homebrew is absent, use its [official installer](https://docs.brew.sh/Installation)
and review/confirm its prompts:

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Skip that block if Homebrew already exists. For Apple Silicon, its ordinary
prefix is `/opt/homebrew`. Do not use a Rosetta Homebrew installation. Once
installed:

```sh
eval "$(/opt/homebrew/bin/brew shellenv)"
brew install cmake python@3.12
"$(brew --prefix python@3.12)/bin/python3.12" -m venv "$SDV_ROOT/tools/python"
SDV_PYTHON="$SDV_ROOT/tools/python/bin/python3.12"
"$SDV_PYTHON" -m pip install packaging
export PATH="$SDV_ROOT/tools/python/bin:$PATH"
SDV_CMAKE="$(command -v cmake)"
"$SDV_PYTHON" -c 'import platform, sys, packaging; print(sys.version.split()[0], platform.machine(), packaging.__version__)'
"$SDV_CMAKE" --version
```

Expect Python **3.12.x / arm64** and CMake **3.24 or newer**. The `packaging`
module belongs in this isolated build environment, not system Python or an
installed demo's private interpreter. The dependency owners check their exact
pins during the build; installing host tools does not qualify their versions.

## 4 Select the exact Node and npm

The project requires **Node 26.0.0 and npm 11.12.1**, not whatever `brew install
node` currently provides. An existing installation with both exact versions is
acceptable: skip download/extraction and go directly to the common tool-path
check below. Otherwise download the macOS ARM64 archive and checksum list from
the [official Node 26.0.0 archive](https://nodejs.org/en/download/archive/v26.0.0):

```sh
mkdir -p "$SDV_ROOT/tools/node-download"
cd "$SDV_ROOT/tools/node-download"
curl --fail --location --remote-name https://nodejs.org/dist/v26.0.0/node-v26.0.0-darwin-arm64.tar.gz
curl --fail --location --remote-name https://nodejs.org/dist/v26.0.0/SHASUMS256.txt
test "$(shasum -a 256 node-v26.0.0-darwin-arm64.tar.gz | cut -d ' ' -f 1)" = "$(awk '$2 == "node-v26.0.0-darwin-arm64.tar.gz" {print $1}' SHASUMS256.txt)" && printf 'Checksum matches\n'
```

Continue only after `Checksum matches`. Extract once into an unused destination:

```sh
test ! -e "$SDV_ROOT/tools/node-v26.0.0-darwin-arm64" && tar -xzf node-v26.0.0-darwin-arm64.tar.gz -C "$SDV_ROOT/tools"
export PATH="$SDV_ROOT/tools/node-v26.0.0-darwin-arm64/bin:$PATH"
```

For both an existing and a newly extracted installation, record/check the tools:

```sh
SDV_NODE="$(command -v node)"
SDV_NPM="$(command -v npm)"
"$SDV_NODE" --version
"$SDV_NODE" -p 'process.arch'
"$SDV_NPM" --version
```

Expect `v26.0.0`, `arm64`, `11.12.1`. If the destination already exists, inspect
and reuse the verified installation rather than extracting over it. Do not
silently upgrade dependencies or substitute another Node release.

## 5 Prepare Docker and Drive access

Install Docker Desktop using [Docker's Mac instructions](https://docs.docker.com/desktop/setup/install/mac-install/),
complete its first-run dialogs, and retain its existing storage configuration.
The new preflight checks Docker's active disk and its capacity separately from
the workspace; no relocation is needed for the storage-aware adapters. The
frozen candidate's older producers still require their original same-external-
volume layout. Do not relocate shared Docker just to bypass that limitation;
use a reviewed successor chain when available. Leave an existing
engine running; do not cycle its dashboard or stop unrelated containers.

```sh
SDV_DOCKER="$(command -v docker)"
"$SDV_DOCKER" --context desktop-linux info --format '{{.OSType}}/{{.Architecture}}'
brew install --cask gcloud-cli
SDV_GCLOUD="$(command -v gcloud)"
"$SDV_GCLOUD" version
printf 'Google account granted access to the input folder: '
read -r SDV_DRIVE_ACCOUNT
"$SDV_GCLOUD" auth login "$SDV_DRIVE_ACCOUNT" --enable-gdrive-access --no-activate
```

The engine must report Linux/ARM64. Google CLI installation is documented by
[Homebrew](https://formulae.brew.sh/cask/gcloud-cli); its
[login command](https://cloud.google.com/sdk/gcloud/reference/auth/login) opens
Google consent. Review the requested Drive/Cloud permissions. This is separate
from Aos Cloud, and may need organization approval. Existing authorization is
reused where valid. Do not print access tokens, save them in variables or paste
them into reports. `lab` obtains them privately from the Google credential store.

## 6 Select signing and input files

In Xcode **Settings → Accounts → Manage Certificates**, obtain your authorized
Apple Development identity, including its private key in Keychain. List usable
identities, then copy only the chosen certificate's fingerprint:

```sh
security find-identity -v -p codesigning
printf 'Authorized Apple Development certificate fingerprint: '
read -r SDV_SIGNING_IDENTITY
printf 'Absolute path to developer-inputs.drive.json: '
read -r SDV_BUILD_BINDING
printf 'Absolute path to simulation-inputs.drive.json: '
read -r SDV_SIM_BINDING
test -r "$SDV_BUILD_BINDING" && test -r "$SDV_SIM_BINDING"
"$SDV_PYTHON" -c 'import os; assert len(os.environ["TMPDIR"].encode()) <= 29, "Choose a shorter same-volume scratch path"'
```

The release owner supplies both binding files; do not invent file IDs or put
bindings/credentials in Git. No OEM/SP certificate is needed to build. Local
Apple Development signing is not Developer ID notarization or permission for
public redistribution. If there is no usable signing identity, stop before the
complete installer build; unsigned output is not an equivalent result.

Keep this terminal open and return to [README B2](../../README.md#b2-clone-the-one-entry-repository)
or [developer guide step 2](reproduce-demo.md#2-select-the-root-revision-and-storage).
After a terminal restart, restore these explicit values before continuing;
the guide deliberately does not write shell profiles or shared credentials.
