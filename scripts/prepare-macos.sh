#!/bin/bash
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
# Standalone before Git/Python/Homebrew. Compatible with Apple's Bash 3.2.
# Sourceable by offline fixtures; execution always goes through main().

SDV_PREP_VERSION=4
SDV_CATALOG_RECORD=c4c5639edc09ddc363784b8fcf3c97fb5b5ff99b4815e8421bb2858b657d0da5
SDV_PUBLIC_CATALOG_URL=''
SDV_PUBLIC_CATALOG_RECORD=''
# Bootstrap projection of the source-owned requirements; parity is tested.
SDV_MACOS_MIN=26
SDV_PYTHON_MINOR=3.12
SDV_NODE_VERSION=26.0.0
SDV_NPM_VERSION=11.12.1
SDV_CMAKE_MIN=3.24
SDV_RESERVE_GIB=90

say() { printf '%s\n' "$*"; }
die() { printf '\nSTOP: %s\n' "$*" >&2; exit 1; }
ask() {
  local label=$1 current=$2 answer
  printf '%s' "$label" >&2
  [ -z "$current" ] || printf ' [%s]' "$current" >&2
  printf ': ' >&2
  IFS= read -r answer || die 'Input ended. Nothing further will be installed.'
  answer=${answer:-$current}
  case "$answer" in *$'\t'*|*$'\r'*|*$'\n'*) die 'Use a single-line value without tabs.' ;; esac
  printf '%s' "$answer"
}
help_text() {
  say 'AosEdge SDV Lab — macOS developer build launcher'
  say 'Usage: /bin/bash prepare-macos.sh [--prepare-only | --check] [--parent PATH] [--xcode PATH] [--configure-access]'
  say 'Default: one plan, one confirmation; prepare, clone pinned sources, acquire inputs, build and sign a DMG.'
  say '--prepare-only: stop after host/input-access preparation; no source clone or build.'
  say '--check: local diagnostics only; no writes, downloads, login or installation.'
  say '--parent PATH: existing internal/external APFS parent for the workspace.'
  say '--xcode PATH: Xcode.app or its Contents/Developer directory (session only).'
  say '--configure-access: review/change the signing selection (and account in private mode).'
  say '--private-inputs: maintainer-only authenticated catalog; never an automatic fallback.'
  say '--advanced-inputs: engineering-only manual input binding files; ordinary users do not need them.'
  say '--state-dir PATH: explicit private control directory (default: Library/Application Support/AosEdge SDV Lab/Developer).'
  say '--requirements: print machine-readable bootstrap requirements and exit.'
  say 'Repeat the same command to resume at the selected commit. No installation, demo launch, publication or Docker restart.'
}
requirements() {
  printf '{"schemaVersion":1,"macosMin":%s,"pythonMinor":"%s","node":"%s","npm":"%s","cmakeMin":"%s","reserveGiB":%s}\n' \
    "$SDV_MACOS_MIN" "$SDV_PYTHON_MINOR" "$SDV_NODE_VERSION" "$SDV_NPM_VERSION" "$SDV_CMAKE_MIN" "$SDV_RESERVE_GIB"
}
safe_path() {
  local path=$1 part
  case "$path" in /*) ;; *) return 1 ;; esac
  case "$path/" in *$'\n'*|*$'\r'*|*$'\t'*|*'/../'*|*'/./'*|*'//'*) return 1 ;; esac
  part=$path
  while [ "$part" != / ]; do
    [ ! -L "$part" ] || return 1
    part=$(dirname "$part")
  done
  return 0
}
private_file() {
  [ -f "$1" ] && [ ! -L "$1" ] && [ "$(stat -f %u "$1")" = "$(id -u)" ] &&
    [ "$(stat -f %l "$1")" = 1 ] && [ "$(stat -f %Lp "$1")" = 600 ]
}
state_get() {
  [ -f "$STATE/selections.tsv" ] || return 0
  private_file "$STATE/selections.tsv" || die 'Saved selections have unsafe ownership or permissions.'
  # Data, never sourced or evaluated as shell code.
  awk -F '\t' -v key="$1" '$1 == key { print $2; exit }' "$STATE/selections.tsv"
}
field() { printf '%s' "$VOLUME_INFO" | plutil -extract "$1" raw -o - - 2>/dev/null; }
inspect_volume() {
  local path=$1 device dfout mount
  safe_path "$path" && [ -d "$path" ] && [ -x "$path" ] && [ -w "$path" ] ||
    die 'Choose an existing, writable absolute directory without symbolic links.'
  dfout=$(LC_ALL=C df -kP "$path") || die 'Cannot read the selected filesystem.'
  device=$(printf '%s\n' "$dfout" | awk 'NR == 2 {print $1}')
  FREE_KIB=$(printf '%s\n' "$dfout" | awk 'NR == 2 {print $4}')
  case "$device" in /dev/disk*) ;; *) die 'Select a local APFS disk, not a network share.' ;; esac
  VOLUME_INFO=$(diskutil info -plist "$device" 2>/dev/null) || die 'Cannot inspect the selected disk.'
  [ "$(field FilesystemType)" = apfs ] && [ "$(field WritableVolume)" = true ] ||
    die 'Select a writable APFS volume. No disk has been changed.'
  mount=$(field MountPoint)
  [ -d "$mount" ] || die 'The selected volume is not mounted.'
  case "$path" in /Volumes|/Volumes/*)
    case "$path/" in "$mount/"*) ;; *) die 'External disk is missing. Reconnect it; do not create a replacement folder.' ;; esac ;;
  esac
  VOLUME_UUID=$(field VolumeUUID)
  VOLUME_NAME=$(field VolumeName)
  VOLUME_MOUNT=$mount
  [ -n "$VOLUME_UUID" ] && [ -n "$VOLUME_NAME" ] || die 'Cannot identify the selected volume.'
  printf '%s\n' "$FREE_KIB" | LC_ALL=C grep -Eq '^[0-9]+$' || die 'Cannot determine free space.'
}
check_capacity() {
  # A preparation reserve, NOT a measured complete-build peak.
  [ "$FREE_KIB" -ge "$((SDV_RESERVE_GIB * 1048576))" ] ||
    die "Less than ${SDV_RESERVE_GIB} GiB free on selected storage. Free space before preparation."
}
recheck_storage() {
  local expected=$SELECTED_UUID
  inspect_volume "$SDV_PARENT"
  [ "$VOLUME_UUID" = "$expected" ] || die 'Selected disk changed or disconnected; no fallback is allowed.'
  check_capacity
}
version_at_least() {
  awk -v actual="$1" -v minimum="$2" 'BEGIN {
    if (actual !~ /^[0-9]+(\.[0-9]+)+$/) exit 1;
    split(actual,a,"."); split(minimum,b,".");
    for(i=1;i<=3;i++) {if(a[i]+0>b[i]+0) exit 0; if(a[i]+0<b[i]+0) exit 1} exit 0
  }'
}
python_ok() {
  [ -x "$1" ] && "$1" -I -B -c 'import platform,sys; sys.exit(not (sys.version_info[:2] == tuple(map(int,sys.argv[1].split("."))) and platform.machine() == "arm64"))' "$SDV_PYTHON_MINOR" >/dev/null 2>&1
}
cmake_ok() {
  [ -x "$1" ] && [ -x "$(dirname "$1")/ctest" ] &&
    version_at_least "$("$1" --version 2>/dev/null | awk 'NR==1 {print $3}')" "$SDV_CMAKE_MIN"
}
node_ok() {
  [ -x "$1" ] && [ "$("$1" --version 2>/dev/null)" = "v$SDV_NODE_VERSION" ] &&
    [ "$("$1" -p process.arch 2>/dev/null)" = arm64 ]
}
npm_ok() {
  [ -x "$2" ] && [ "$(PATH="$(dirname "$1"):$PATH" "$2" --version 2>/dev/null)" = "$SDV_NPM_VERSION" ]
}
discover() {
  local candidate
  XCODE_OK=no
  [ -d "$DEVELOPER_DIR" ] && xcodebuild -checkFirstLaunchStatus >/dev/null 2>&1 &&
    xcrun --sdk macosx --show-sdk-path >/dev/null 2>&1 &&
    version_at_least "$(xcrun --sdk macosx --show-sdk-version 2>/dev/null)" "$SDV_MACOS_MIN.0" &&
    xcrun swift --version >/dev/null 2>&1 && xcrun git --version >/dev/null 2>&1 && XCODE_OK=yes
  BREW=
  [ ! -x /opt/homebrew/bin/brew ] || BREW=/opt/homebrew/bin/brew
  SDV_CMAKE=
  for candidate in "$(command -v cmake)" /opt/homebrew/bin/cmake; do
    if cmake_ok "$candidate"; then SDV_CMAKE=$candidate; break; fi
  done
  BASE_PYTHON=
  for candidate in "$(command -v python3.12)" /opt/homebrew/opt/python@3.12/bin/python3.12; do
    if python_ok "$candidate"; then BASE_PYTHON=$candidate; break; fi
  done
  SDV_PYTHON="$SDV_ROOT/tools/python/bin/python3.12"
  PYTHON_OK=no
  python_ok "$SDV_PYTHON" && "$SDV_PYTHON" -I -B -c 'import packaging' >/dev/null 2>&1 && PYTHON_OK=yes
  SDV_NODE= SDV_NPM=
  for candidate in "$SDV_ROOT/tools/node-v$SDV_NODE_VERSION-darwin-arm64/bin/node" "$(command -v node)"; do
    if node_ok "$candidate" && npm_ok "$candidate" "$(dirname "$candidate")/npm"; then
      SDV_NODE=$candidate; SDV_NPM="$(dirname "$candidate")/npm"; break
    fi
  done
  SDV_DOCKER=
  for candidate in "$(command -v docker)" /Applications/Docker.app/Contents/Resources/bin/docker "$HOME/.docker/bin/docker"; do
    if [ -x "$candidate" ] && "$candidate" --version >/dev/null 2>&1; then SDV_DOCKER=$candidate; break; fi
  done
  SDV_GCLOUD=
  if [ "${PRIVATE_INPUTS:-no}" = yes ]; then
    for candidate in "$(command -v gcloud)" /opt/homebrew/bin/gcloud /opt/homebrew/share/google-cloud-sdk/bin/gcloud; do
      if [ -x "$candidate" ] && "$candidate" version >/dev/null 2>&1; then SDV_GCLOUD=$candidate; break; fi
    done
  fi
}
choose_storage() {
  local choice path i=1 saved
  saved=$(state_get SDV_PARENT)
  if [ -z "$SDV_PARENT" ]; then
    if [ -n "$saved" ]; then
      SDV_PARENT=$saved
      say "Previously selected storage: $saved"
      say 'To choose another location, rerun with --parent PATH.'
    else
      local options=("$HOME")
      say 'Where would you like to build?'
      say "  1. Internal disk — $HOME"
      for path in /Volumes/*; do
        [ -d "$path" ] && [ ! -L "$path" ] || continue
        options+=("$path"); i=$((i+1)); say "  $i. $path"
      done
      say '  0. Enter another existing folder'
      choice=$(ask 'Your choice' '')
      case "$choice" in
        0) SDV_PARENT=$(ask 'Existing absolute folder path (no quotes)' '') ;;
        *) printf '%s\n' "$choice" | grep -Eq '^[1-9][0-9]*$' && [ "$choice" -le "${#options[@]}" ] || die 'Choose one of the listed numbers.'
           SDV_PARENT=${options[$((choice-1))]} ;;
      esac
    fi
  fi
  SDV_PARENT=${SDV_PARENT%/}
  [ -n "$SDV_PARENT" ] || die 'The filesystem root is not a build parent.'
  inspect_volume "$SDV_PARENT"
  SELECTED_UUID=$VOLUME_UUID
  if [ "$saved" = "$SDV_PARENT" ] && [ -n "$(state_get VOLUME_UUID)" ]; then
    [ "$(state_get VOLUME_UUID)" = "$SELECTED_UUID" ] || die 'A different disk is mounted at the saved path. Review the saved selection before reuse.'
  fi
  check_capacity
  SDV_ROOT="$SDV_PARENT/sdv"
  SDV_TMP="$VOLUME_MOUNT/tmp"
  [ "$VOLUME_MOUNT" != /System/Volumes/Data ] || SDV_TMP=/private/tmp/sdv
  if [ "$saved" = "$SDV_PARENT" ] && [ -n "$(state_get SDV_TMP)" ]; then SDV_TMP=$(state_get SDV_TMP); fi
  if [ "$(printf %s "$SDV_TMP" | wc -c | tr -d ' ')" -gt 29 ]; then
    SDV_TMP=$(ask 'Short scratch path on the SAME volume (maximum 29 UTF-8 bytes)' '')
  fi
  safe_path "$SDV_ROOT" && safe_path "$SDV_TMP" || die 'Workspace/scratch must be absolute paths without links or traversal.'
  for path in "$SDV_ROOT/tools" "$SDV_ROOT/cache" "$SDV_ROOT/.developer-preparation"; do
    safe_path "$path" || die 'Workspace tool/cache directories must not be symbolic links.'
  done
  [ ! -d "$SDV_ROOT" ] || [ "$(stat -f %u "$SDV_ROOT")" = "$(id -u)" ] || die 'Existing workspace belongs to another user.'
  [ "$(printf %s "$SDV_TMP" | wc -c | tr -d ' ')" -le 29 ] || die 'Scratch path is longer than 29 UTF-8 bytes.'
  [ -d "$(dirname "$SDV_TMP")" ] && [ "$(stat -f %d "$SDV_PARENT")" = "$(stat -f %d "$(dirname "$SDV_TMP")")" ] || die 'Scratch parent must already exist on the selected volume.'
  say "Selected: $SDV_PARENT"
  awk -v k="$FREE_KIB" 'BEGIN {printf "Available: %.1f GiB (full build capacity is checked after cloning)\n",k/1048576}'
}
load_choices() {
  SDV_DRIVE_ACCOUNT=$(state_get SDV_DRIVE_ACCOUNT)
  [ "${PRIVATE_INPUTS:-no}" = yes ] || SDV_DRIVE_ACCOUNT=
  SDV_BUILD_BINDING=$(state_get SDV_BUILD_BINDING)
  SDV_SIM_BINDING=$(state_get SDV_SIM_BINDING)
  SDV_SIGNING_IDENTITY=$(state_get SDV_SIGNING_IDENTITY)
  catalog_paths
  if [ -z "$DEVELOPER_DIR" ]; then
    DEVELOPER_DIR=$(state_get DEVELOPER_DIR)
    [ -n "$DEVELOPER_DIR" ] || DEVELOPER_DIR=$(xcode-select -p 2>/dev/null)
    case "$DEVELOPER_DIR" in */Xcode*.app/Contents/Developer) ;; *) DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer ;; esac
  fi
  case "$DEVELOPER_DIR" in *.app) DEVELOPER_DIR="$DEVELOPER_DIR/Contents/Developer" ;; esac
  export DEVELOPER_DIR
}
show_plan() {
  say ''; say 'Developer workflow plan — no changes yet'
  say "[1/6] Storage: checked; workspace $SDV_ROOT; scratch $SDV_TMP"
  if [ "$XCODE_OK" = yes ]; then say '[2/6] Apple tools: reuse selected Xcode, SDK, Swift and Git';
  else say '[2/6] Apple tools: ACTION — install/open Xcode, finish its license and components, then rerun'; fi
  if [ -n "$SDV_CMAKE" ] && [ "$PYTHON_OK" = yes ]; then say '[3/6] CMake / Python: reuse compatible tools';
  else say '[3/6] CMake / Python: prepare missing tools and project Python environment'; fi
  [ -n "$SDV_NODE" ] && say "[4/6] Node $SDV_NODE_VERSION / npm $SDV_NPM_VERSION: reuse" || say "[4/6] Node $SDV_NODE_VERSION / npm $SDV_NPM_VERSION: install inside the workspace"
  if [ "${PRIVATE_INPUTS:-no}" = yes ]; then
    say '[5/6] Docker / inputs: maintainer private catalog with explicit Google authorization'
  else
    say '[5/6] Docker / inputs: check local Engine and public input availability (no Google login)'
  fi
  say '[6/6] Signing / inputs: select existing identity; find compatible release inputs automatically'
  if [ -z "$BREW" ] && { [ -z "$SDV_CMAKE" ] || [ -z "$BASE_PYTHON" ] || [ -z "$SDV_DOCKER" ] || { [ "${PRIVATE_INPUTS:-no}" = yes ] && [ -z "$SDV_GCLOUD" ]; }; }; then
    say 'Homebrew is missing: its official installer will be offered (may require an administrator password).'
  fi
  say 'Host tools use their standard macOS locations; project tools/caches use the selected disk.'
  say 'Package managers may install required dependencies. No upgrade, cleanup or Docker restart is requested.'
  if [ "${PREPARE_ONLY:-no}" = yes ]; then
    say 'Preparation only: no source clone, heavy input download, build or signing operation.'
  else
    say 'Then: fix the root main revision, prepare component sources, check capacity and download/reuse release inputs.'
    say 'Build the developer DMG and sign Setup using the selected existing Apple Development identity.'
    say 'CARLA and Factory are reused, not rebuilt. Exact download/storage totals are shown before acquisition.'
    say 'Existing checkouts/receipts and verified inputs are reused; no automatic pull, reset or deletion.'
  fi
  say 'Nothing will be installed as a demo, launched, provisioned or published. Shared Docker is not restarted or moved.'
}
owned_dir() {
  local path=$1
  safe_path "$path" || die 'Unsafe preparation directory.'
  if [ -e "$path" ]; then
    [ -d "$path" ] && [ -f "$path/.aosedge-preparation" ] && [ ! -L "$path/.aosedge-preparation" ] &&
      [ "$(<"$path/.aosedge-preparation")" = 'aosedge-developer-preparation-v1' ] &&
      [ "$(stat -f %u "$path")" = "$(id -u)" ] || die "Unowned directory preserved: $path"
  else
    mkdir -m 700 "$path" || die "Cannot create $path"
    printf '%s\n' aosedge-developer-preparation-v1 > "$path/.aosedge-preparation"
  fi
}
save_choices() {
  local key value tmp
  tmp=$(mktemp "$STATE/selections.XXXXXX") || die 'Cannot save preparation selections.'
  for key in SDV_PARENT SDV_TMP SDV_DRIVE_ACCOUNT SDV_BUILD_BINDING SDV_SIM_BINDING SDV_PREPARED_SOURCE SDV_SIGNING_IDENTITY DEVELOPER_DIR; do
    value=${!key}; printf '%s\t%s\n' "$key" "$value" >> "$tmp"
  done
  printf 'VOLUME_UUID\t%s\n' "$SELECTED_UUID" >> "$tmp"
  mv "$tmp" "$STATE/selections.tsv" || die 'Cannot save preparation selections.'
}
setup_state() {
  local stale_pid
  umask 077
  safe_path "$STATE" || die 'Unsafe preparation state location.'
  mkdir -p "$(dirname "$STATE")" || die 'Cannot create preparation state parent.'
  owned_dir "$STATE"
  [ "$(stat -f %Lp "$STATE")" = 700 ] || die 'Preparation state directory must have mode 700.'
  if [ -e "$STATE/active" ]; then
    safe_path "$STATE/active" && private_file "$STATE/active/pid" || die 'Unrecognized preparation lock; preserved for inspection.'
    stale_pid=$(<"$STATE/active/pid")
    printf '%s\n' "$stale_pid" | grep -Eq '^[1-9][0-9]*$' || die 'Invalid preparation lock; preserved.'
    kill -0 "$stale_pid" 2>/dev/null && die 'Another preparation process is still running. Let it finish first.'
    rm "$STATE/active/pid" && rmdir "$STATE/active" || die 'Unexpected interrupted lock contents; preserved.'
  fi
  mkdir "$STATE/active" 2>/dev/null || die 'Another preparation is running.'
  LOCKED=yes
  printf '%s\n' "$$" > "$STATE/active/pid"
  trap 'cleanup' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  # Invalidate a previous success before any change. Never source stale readiness.
  write_environment no
  save_choices
  recheck_storage
  [ -d "$SDV_ROOT" ] || mkdir -m 700 "$SDV_ROOT" || die 'Cannot create workspace.'
  owned_dir "$SDV_TMP"
  mkdir -p "$SDV_ROOT/tools" "$SDV_ROOT/cache" || die 'Cannot create workspace directories.'
  owned_dir "$SDV_ROOT/.developer-preparation"
  LOG=$(mktemp "$SDV_ROOT/.developer-preparation/run.XXXXXX") || die 'Cannot create diagnostic log.'
  export TMPDIR="$SDV_TMP" HOMEBREW_TEMP="$SDV_TMP"
  export HOMEBREW_CACHE="$SDV_ROOT/cache/homebrew" PIP_CACHE_DIR="$SDV_ROOT/cache/pip" npm_config_cache="$SDV_ROOT/cache/npm"
  export HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_UPGRADE=1 HOMEBREW_NO_INSTALL_CLEANUP=1 HOMEBREW_NO_ANALYTICS=1
}
cleanup() {
  stop_child
  if [ "${LOCKED:-no}" = yes ]; then
    [ ! -f "$STATE/active/pid" ] || rm "$STATE/active/pid"
    rmdir "$STATE/active" 2>/dev/null
  fi
}
stop_child() {
  if [ -n "${CHILD_PID:-}" ]; then
    # run_install enables job control for its own process group only.
    # Drop Bash 3.2's job notification before termination (it can emit a
    # corrupted job description during an EXIT trap). Keep the explicit PID.
    disown "$CHILD_PID" 2>/dev/null
    if [ "${WORKFLOW_CHILD:-no}" = yes ]; then
      # Let the Python continuation unwind its canonical child owners first.
      kill -INT -- "-$CHILD_PID" 2>/dev/null
      local grace=0
      while kill -0 "$CHILD_PID" 2>/dev/null && [ "$grace" -lt 15 ]; do sleep 1; grace=$((grace+1)); done
    fi
    kill -TERM -- "-$CHILD_PID" 2>/dev/null
    sleep 1
    kill -KILL -- "-$CHILD_PID" 2>/dev/null
    wait "$CHILD_PID" 2>/dev/null
    CHILD_PID=
  fi
}
run_install() {
  local title=$1 result elapsed=0
  shift
  recheck_storage
  say "  $title… (details: $LOG)"
  set -m
  "$@" >> "$LOG" 2>&1 & CHILD_PID=$!
  set +m
  while kill -0 "$CHILD_PID" 2>/dev/null; do
    sleep 2; elapsed=$((elapsed+2))
    [ "$((elapsed % 10))" -ne 0 ] || printf '  Still working: %s (%ss)\n' "$title" "$elapsed"
    [ "$elapsed" -lt 1800 ] || { stop_child; die "$title exceeded 30 minutes. Owned processes stopped; partial work preserved."; }
  done
  wait "$CHILD_PID"; result=$?; CHILD_PID=
  [ "$result" = 0 ] || die "$title failed (exit $result). Partial work is preserved; see $LOG and rerun after resolving the cause."
}
download() {
  local url=$1 destination=$2
  # Official HTTPS only; incomplete files never replace a completed download.
  curl --fail --location --proto '=https' --proto-redir '=https' --tlsv1.2 --connect-timeout 15 --max-time 900 \
    --silent --show-error --output "$destination.part" "$url" && mv "$destination.part" "$destination"
}
need_brew() {
  check_host_capacity
  [ -z "$BREW" ] || return 0
  local installer="$SDV_ROOT/.developer-preparation/homebrew-install.sh"
  run_install 'Download official Homebrew installer' download https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh "$installer"
  say 'Homebrew will now show its own installation plan and permission prompts.'
  /bin/bash "$installer" || die 'Homebrew installation was not completed. Rerun when ready.'
  [ -x /opt/homebrew/bin/brew ] || die 'Native Homebrew was not installed at /opt/homebrew.'
  BREW=/opt/homebrew/bin/brew
}
check_host_capacity() {
  local path available
  # Host applications and Homebrew do not move to the selected build disk.
  # Check both actual host locations; never sum shared APFS free capacity.
  for path in /Applications /opt; do
    [ -d "$path" ] || path=/
    available=$(LC_ALL=C df -kP "$path" | awk 'NR==2 {print $4}')
    printf '%s\n' "$available" | grep -Eq '^[0-9]+$' || die 'Cannot check host-tool disk capacity.'
    [ "$available" -ge "$((SDV_RESERVE_GIB * 1048576))" ] || die "Host tool storage at $path has less than $SDV_RESERVE_GIB GiB free. An external workspace does not move Xcode, Docker or Homebrew."
  done
}
install_formula() {
  need_brew
  if "$BREW" list --versions "$1" >/dev/null 2>&1; then
    die "Homebrew already has $1, but it did not pass the required checks. Existing tools are preserved; inspect or repair them before retrying."
  fi
  # Bottle only: host preparation must not unexpectedly compile a dependency.
  run_install "Install $1" "$BREW" install --force-bottle "$1"
}
prepare_python_cmake() {
  if [ -z "$SDV_CMAKE" ]; then install_formula cmake; SDV_CMAKE=/opt/homebrew/bin/cmake; fi
  cmake_ok "$SDV_CMAKE" || die 'CMake/CTest did not pass the version check.'
  if [ "$PYTHON_OK" != yes ]; then
    owned_dir "$SDV_ROOT/tools/python"
    if ! python_ok "$SDV_PYTHON"; then
      if [ -z "$BASE_PYTHON" ]; then install_formula python@3.12; BASE_PYTHON=/opt/homebrew/opt/python@3.12/bin/python3.12; fi
      python_ok "$BASE_PYTHON" || die 'A native Python 3.12 interpreter is required.'
      run_install 'Prepare isolated Python' "$BASE_PYTHON" -m venv "$SDV_ROOT/tools/python"
    fi
    run_install 'Install Python packaging support' "$SDV_PYTHON" -I -m pip install --only-binary=:all: packaging
  fi
  python_ok "$SDV_PYTHON" && "$SDV_PYTHON" -I -B -c 'import packaging' >/dev/null 2>&1 || die 'Project Python is not ready.'
  say '[3/6] CMake / Python ready'
}
prepare_node() {
  local base="$SDV_ROOT/tools/node-v$SDV_NODE_VERSION-darwin-arm64" work archive actual expected
  if [ -z "$SDV_NODE" ]; then
    work="$SDV_ROOT/.developer-preparation/node"
    owned_dir "$work"
    archive="node-v$SDV_NODE_VERSION-darwin-arm64.tar.gz"
    [ -f "$work/SHASUMS256.txt" ] || run_install 'Download Node checksums' download "https://nodejs.org/dist/v$SDV_NODE_VERSION/SHASUMS256.txt" "$work/SHASUMS256.txt"
    expected=$(awk -v name="$archive" '$2==name {print $1}' "$work/SHASUMS256.txt")
    printf '%s\n' "$expected" | grep -Eq '^[a-f0-9]{64}$' || die 'Node checksum list is incomplete.'
    [ -f "$work/$archive" ] || run_install 'Download Node' download "https://nodejs.org/dist/v$SDV_NODE_VERSION/$archive" "$work/$archive"
    actual=$(shasum -a 256 "$work/$archive" | awk '{print $1}')
    [ "$actual" = "$expected" ] || die 'Node archive checksum mismatch. The archive is preserved, not executed.'
    if [ ! -e "$base" ]; then
      owned_dir "$work/unpacked"
      run_install 'Unpack verified Node' extract_node "$work/$archive" "$work/unpacked"
      printf '%s\n' aosedge-developer-preparation-v1 > "$work/unpacked/node-v$SDV_NODE_VERSION-darwin-arm64/.aosedge-preparation"
      mv "$work/unpacked/node-v$SDV_NODE_VERSION-darwin-arm64" "$base" || die 'Cannot place Node tools.'
      rm "$work/unpacked/.aosedge-preparation"
      rmdir "$work/unpacked" || die 'Unexpected archive contents preserved.'
    fi
    node_ok "$base/bin/node" || die 'Existing project Node is incompatible or incomplete; preserved.'
    if ! npm_ok "$base/bin/node" "$base/bin/npm"; then
      owned_dir "$base"
      run_install 'Install pinned npm inside project tools' env PATH="$base/bin:$PATH" "$base/bin/npm" install --global --prefix "$base" "npm@$SDV_NPM_VERSION" --ignore-scripts --no-audit --no-fund
    fi
    SDV_NODE="$base/bin/node"; SDV_NPM="$base/bin/npm"
  fi
  node_ok "$SDV_NODE" && npm_ok "$SDV_NODE" "$SDV_NPM" || die 'Node/npm did not pass exact-version checks.'
  say '[4/6] Node / npm ready'
}
extract_node() {
  "$SDV_PYTHON" -I -B - "$1" "$2" "node-v$SDV_NODE_VERSION-darwin-arm64" <<'PY'
import pathlib, sys, tarfile
with tarfile.open(sys.argv[1]) as archive:
    for member in archive.getmembers():
        path = pathlib.PurePosixPath(member.name)
        if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != sys.argv[3]:
            raise SystemExit('Unexpected archive path')
    archive.extractall(sys.argv[2], filter='data')
PY
}
prepare_access_tools() {
  if [ -z "$SDV_DOCKER" ]; then
    [ ! -d /Applications/Docker.app ] || die 'Docker is installed but its CLI is unavailable. Complete Docker first-run setup, then rerun.'
    need_brew
    # Cask prompts remain visible (including any macOS administrator dialog).
    "$BREW" install --cask docker || die 'Docker installation was not completed.'
    SDV_DOCKER=/Applications/Docker.app/Contents/Resources/bin/docker
  fi
  [ "${PRIVATE_INPUTS:-no}" = yes ] || return 0
  if [ -z "$SDV_GCLOUD" ]; then
    need_brew
    "$BREW" list --cask gcloud-cli >/dev/null 2>&1 && die 'Google CLI is installed but unavailable; repair its CLI path, then rerun.'
    "$BREW" install --cask gcloud-cli || die 'Google CLI installation was not completed.'
    SDV_GCLOUD=/opt/homebrew/share/google-cloud-sdk/bin/gcloud
    [ -x "$SDV_GCLOUD" ] || SDV_GCLOUD=/opt/homebrew/bin/gcloud
  fi
  "$SDV_GCLOUD" version >/dev/null 2>&1 || die 'Google CLI is unavailable.'
}
docker_ready() {
  "$SDV_PYTHON" -I -B - "$SDV_DOCKER" <<'PY'
import json, subprocess, sys
try:
    cmd = sys.argv[1]
    context = subprocess.run([cmd, 'context', 'inspect', 'desktop-linux'], capture_output=True, text=True, timeout=15)
    host = json.loads(context.stdout)[0]['Endpoints']['docker']['Host']
    assert host.startswith('unix://'), 'remote engine'
    result = subprocess.run([cmd, '--context', 'desktop-linux', 'info', '--format', '{{.OSType}}/{{.Architecture}}'], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0 and result.stdout.strip() in ('linux/arm64', 'linux/aarch64')
except Exception:
    sys.exit(1)
PY
}
choose_access() {
  local identities chosen index=0 fingerprint label
  say ''; say 'Build signing and inputs — saved selections are reused.'
  if [ "${CONFIGURE_ACCESS:-no}" = yes ]; then
    [ "${PRIVATE_INPUTS:-no}" != yes ] || SDV_DRIVE_ACCOUNT=$(ask 'Google account with access to the build inputs' "$SDV_DRIVE_ACCOUNT")
    SDV_SIGNING_IDENTITY=
  fi
  if [ "${PRIVATE_INPUTS:-no}" = yes ]; then
    [ -n "$SDV_DRIVE_ACCOUNT" ] || SDV_DRIVE_ACCOUNT=$(ask 'Google account with access to the build inputs' '')
  else
    SDV_DRIVE_ACCOUNT=
    say 'Public inputs: no Google account, credentials or JSON path needed.'
  fi
  if [ "${ADVANCED_INPUTS:-no}" = yes ]; then
    say 'Advanced engineering mode: use owner-supplied bindings for this exact release.'
    if [ "${CONFIGURE_ACCESS:-no}" = yes ] || [ ! -r "$SDV_BUILD_BINDING" ]; then
      SDV_BUILD_BINDING=$(ask 'Full path to developer-inputs.drive.json (no quotes)' "$SDV_BUILD_BINDING")
    fi
    if [ "${CONFIGURE_ACCESS:-no}" = yes ] || [ ! -r "$SDV_SIM_BINDING" ]; then
      SDV_SIM_BINDING=$(ask 'Full path to simulation-inputs.drive.json (no quotes)' "$SDV_SIM_BINDING")
    fi
  else
    say 'Release inputs will be selected automatically from the SDV Lab catalog.'
  fi
  if identity_ready; then save_choices; return; fi
  identities=$(security find-identity -v -p codesigning 2>/dev/null | grep '"Apple Development:' || true)
  local fingerprints=()
  say 'Available Apple Development signing identities:'
  while IFS= read -r label; do
    [ -n "$label" ] || continue
    fingerprint=$(printf '%s\n' "$label" | awk '{print $2}')
    printf '%s\n' "$fingerprint" | grep -Eq '^[A-Fa-f0-9]{40}$' || continue
    fingerprints+=("$fingerprint"); index=$((index+1))
    printf '  %s. %s\n' "$index" "${label#*\"}"
  done <<< "$identities"
  SDV_SIGNING_IDENTITY=
  if [ "$index" = 0 ]; then
    say '  None. Obtain your identity in Xcode Settings > Accounts > Manage Certificates.'
  else
    chosen=$(ask 'Choose an identity number (or 0 to complete later)' 1)
    if [ "$chosen" != 0 ]; then
      printf '%s\n' "$chosen" | grep -Eq '^[1-9][0-9]*$' && [ "$chosen" -le "$index" ] || die 'Choose a listed identity number.'
      SDV_SIGNING_IDENTITY=$(printf %s "${fingerprints[$((chosen-1))]}" | tr '[:lower:]' '[:upper:]')
    fi
  fi
  save_choices
}
identity_ready() {
  printf '%s\n' "$SDV_SIGNING_IDENTITY" | grep -Eq '^[A-F0-9]{40}$' &&
    security find-identity -v -p codesigning 2>/dev/null | grep '"Apple Development:' | grep -Fq " $SDV_SIGNING_IDENTITY "
}
catalog_paths() {
  local selection=automatic key=$SDV_CATALOG_RECORD
  if [ "${PRIVATE_INPUTS:-no}" != yes ]; then
    selection=public; key=${SDV_PUBLIC_CATALOG_RECORD:-unpublished}
  fi
  [ "${ADVANCED_INPUTS:-no}" != yes ] || selection=manual
  SDV_PREPARED_SOURCE="$STATE/catalog/$key/$selection/source-requirements.json"
  if [ "$selection" != manual ]; then
    SDV_BUILD_BINDING="$STATE/catalog/$key/$selection/developer-inputs.drive.json"
    SDV_SIM_BINDING="$STATE/catalog/$key/$selection/simulation-inputs.drive.json"
  fi
}
drive_probe() {
  local transport=public
  [ "${PRIVATE_INPUTS:-no}" != yes ] || transport=private
  # Public mode never reads credentials; private tokens stay in the helper.
  "$SDV_PYTHON" -I -B - "$SDV_GCLOUD" "$SDV_DRIVE_ACCOUNT" "$SDV_BUILD_BINDING" "$SDV_SIM_BINDING" "$1" "$STATE" "${ADVANCED_INPUTS:-no}" "$transport" <<'PY'
# Canonical anonymous transport, embedded for pre-clone use.
import sys, types
_transport = types.ModuleType("public_drive")
exec('# SPDX-FileCopyrightText: 2026 maninblack\n# SPDX-License-Identifier: MIT\n"""Anonymous, bounded Drive downloads; no OAuth, API keys, cookies or publication.\n\nThe caller authenticates catalog records against a source pin and archive bytes\nagainst a lock. A public URL is a locator, never an integrity authority.\n"""\nfrom html.parser import HTMLParser\nimport http.client\nimport re\nimport urllib.error\nimport urllib.parse\nimport urllib.request\n\nHOSTS = {\'drive.google.com\', \'drive.usercontent.google.com\'}\nHTML_LIMIT = 65536\n\n\nclass PublicDriveError(Exception):\n    pass\n\n\ndef require(condition, message):\n    if not condition:\n        raise PublicDriveError(message)\n\n\ndef bounded_read(response, limit):\n    try:\n        return response.read(limit)\n    except (OSError, urllib.error.URLError, http.client.HTTPException):\n        raise PublicDriveError(\'Public download response was interrupted; no new selection was accepted.\') from None\n\n\ndef link(url, confirmation=False):\n    """Only persistent download links (including Google\'s resource key)."""\n    require(isinstance(url, str) and len(url) <= 4096 and not any(c.isspace() for c in url),\n            \'Invalid public download link.\')\n    p = urllib.parse.urlsplit(url)\n    require(p.scheme == \'https\' and p.netloc in HOSTS and not p.fragment\n            and ((p.netloc == \'drive.google.com\' and p.path == \'/uc\')\n                 or (p.netloc == \'drive.usercontent.google.com\' and p.path == \'/download\')),\n            \'Unsupported public download endpoint; no request was sent.\')\n    try:\n        pairs = urllib.parse.parse_qsl(p.query, keep_blank_values=True, strict_parsing=True)\n    except ValueError:\n        raise PublicDriveError(\'Invalid public download query.\') from None\n    fields = dict(pairs)\n    allowed = {\'id\', \'export\', \'resourcekey\'} | ({\'confirm\', \'uuid\', \'at\'} if confirmation else set())\n    require(len(fields) == len(pairs) and set(fields) <= allowed\n            and fields.get(\'export\') == \'download\'\n            and re.fullmatch(r\'[A-Za-z0-9_-]{10,200}\', fields.get(\'id\', \'\'))\n            and all(re.fullmatch(r\'[A-Za-z0-9_.:-]{1,2048}\', v) for v in fields.values()),\n            \'Invalid public download parameters.\')\n    return fields\n\n\ndef binding(value, lock_digest, roles):\n    require(isinstance(value, dict) and set(value) == {\'schemaVersion\', \'transport\', \'lockDigest\', \'files\'}\n            and type(value[\'schemaVersion\']) is int and value[\'schemaVersion\'] == 2\n            and value[\'transport\'] == \'google-drive-public\' and value[\'lockDigest\'] == lock_digest\n            and isinstance(value[\'files\'], dict) and set(value[\'files\']) == set(roles),\n            \'Public input selection differs from the source lock.\')\n    for url in value[\'files\'].values():\n        link(url)\n    return value\n\n\nclass NoRedirect(urllib.request.HTTPRedirectHandler):\n    def redirect_request(self, *args, **kwargs):\n        return None\n\n\nclass DownloadForm(HTMLParser):\n    def __init__(self):\n        super().__init__()\n        self.active = False\n        self.forms = []\n        self.fields = {}\n        self.duplicate = False\n        self.text = []\n\n    def handle_starttag(self, tag, attrs):\n        a = dict(attrs)\n        if tag == \'form\':\n            self.active = a.get(\'id\') == \'download-form\'\n            if self.active:\n                self.forms.append(a)\n        if tag == \'input\' and self.active:\n            name = a.get(\'name\')\n            if name:\n                self.duplicate |= name in self.fields or a.get(\'type\') != \'hidden\'\n                self.fields[name] = a.get(\'value\', \'\')\n\n    def handle_endtag(self, tag):\n        if tag == \'form\':\n            self.active = False\n\n    def handle_data(self, data):\n        self.text.append(data)\n\n\ndef confirmation_url(raw, original):\n    form = DownloadForm()\n    try:\n        form.feed(raw.decode(\'utf-8\'))\n    except UnicodeError:\n        raise PublicDriveError(\'Unexpected download page; no file was saved.\') from None\n    text = \' \'.join(form.text).lower()\n    if \'too many users\' in text or \'download quota\' in text:\n        raise PublicDriveError(\'Google Drive temporarily limited downloads. Retry later; no login or duplicate copy is needed.\')\n    require("can\'t scan this file for viruses" in text\n            and not any(word in text for word in (\'infected\', \'malware\', \'violates\', \'abusive\'))\n            and len(form.forms) == 1 and not form.duplicate,\n            \'The public file is unavailable or needs sign-in, or Google returned an unsupported warning. Contact the release owner; no file was saved.\')\n    a = form.forms[0]\n    require(a.get(\'action\') == \'https://drive.usercontent.google.com/download\'\n            and a.get(\'method\', \'get\').lower() == \'get\', \'Unsupported download confirmation form.\')\n    fields = form.fields\n    require(fields.get(\'id\') == original[\'id\'] and fields.get(\'export\') == \'download\'\n            and fields.get(\'confirm\') == \'t\', \'Download confirmation does not match the requested file.\')\n    if original.get(\'resourcekey\'):\n        require(fields.get(\'resourcekey\', original[\'resourcekey\']) == original[\'resourcekey\'], \'Download resource key changed.\')\n        fields[\'resourcekey\'] = original[\'resourcekey\']\n    url = a[\'action\'] + \'?\' + urllib.parse.urlencode(fields)\n    link(url, confirmation=True)\n    return url\n\n\nclass Client:\n    def __init__(self):\n        # No ambient proxy authentication, browser cookie jar, .netrc or CLI.\n        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())\n\n    def open(self, url, start=None, end=None):\n        original = link(url)\n        confirmed = False\n        for _ in range(5):\n            fields = link(url, confirmation=confirmed)\n            require(fields[\'id\'] == original[\'id\'], \'Public redirect changed the requested file.\')\n            require(fields.get(\'resourcekey\') == original.get(\'resourcekey\'), \'Public redirect changed the resource key.\')\n            headers = {\'Accept-Encoding\': \'identity\', \'Accept-Language\': \'en\', \'User-Agent\': \'AosEdge-SDV-Lab/3\'}\n            if start is not None:\n                require(type(start) is int and start >= 0 and (end is None or type(end) is int and end >= start), \'Invalid download range.\')\n                headers[\'Range\'] = f\'bytes={start}-\' + (str(end) if end is not None else \'\')\n            req = urllib.request.Request(url, headers=headers)\n            try:\n                response = self.opener.open(req, timeout=30)\n            except urllib.error.HTTPError as error:\n                response = error\n            except (OSError, urllib.error.URLError, http.client.HTTPException):\n                raise PublicDriveError(\'Public Drive connection interrupted; rerun to resume verified input acquisition.\') from None\n            if response.status in (301, 302, 303, 307, 308):\n                with response:\n                    next_url = urllib.parse.urljoin(url, response.headers.get(\'Location\', \'\'))\n                if urllib.parse.urlsplit(next_url).hostname == \'accounts.google.com\':\n                    raise PublicDriveError(\'This release is not publicly downloadable. Contact the release owner; Google login is not required by this workflow.\')\n                link(next_url, confirmation=confirmed)\n                url = next_url\n                continue\n            if response.status not in (200, 206):\n                with response:\n                    code = response.status\n                raise PublicDriveError(f\'Public Drive download failed (HTTP {code}). Check access/connectivity or retry later for a quota limit; no login was started.\')\n            if response.headers.get(\'Content-Encoding\', \'identity\') != \'identity\':\n                response.close()\n                raise PublicDriveError(\'Unexpected download content encoding.\')\n            content_type = response.headers.get(\'Content-Type\', \'\').split(\';\')[0].strip().lower()\n            if content_type in (\'text/html\', \'application/xhtml+xml\'):\n                with response:\n                    raw = bounded_read(response, HTML_LIMIT + 1)\n                require(len(raw) <= HTML_LIMIT and not confirmed, \'Unexpected or repeated download page; no file was saved.\')\n                url = confirmation_url(raw, original)\n                confirmed = True\n                continue\n            if content_type not in (\'application/octet-stream\', \'application/json\', \'application/gzip\',\n                                     \'application/x-gzip\', \'application/x-apple-diskimage\', \'application/zip\'):\n                response.close()\n                raise PublicDriveError(\'Unexpected public file type; no file was saved.\')\n            return response\n        raise PublicDriveError(\'Too many public download redirects; no file was saved.\')\n\n    def catalog(self, url, limit=1024 * 1024):\n        with self.open(url) as response:\n            require(response.status == 200, \'Unexpected catalog range response.\')\n            raw = bounded_read(response, limit + 1)\n        require(0 < len(raw) <= limit, \'Public catalog is empty or exceeds its size limit.\')\n        return raw\n\n    def probe(self, url, expected):\n        # Availability/length only. Full integrity belongs to the later consumer.\n        with self.open(url, 0, 0) as response:\n            require(response.status == 206 and response.headers.get(\'Content-Range\') == f\'bytes 0-0/{expected["bytes"]}\',\n                    \'Public input size/range differs; no archive was downloaded.\')\n            require(len(bounded_read(response, 2)) == 1, \'Public input availability check failed.\')\n', _transport.__dict__)
sys.modules["public_drive"] = _transport
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Bounded developer catalog reader; embedded verbatim in prepare-macos.sh.

Standard library only. The public pin authenticates one immutable catalog record,
not a mutable filename, owner-supplied checksum or Google account name.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import public_drive

PIN = {
    'releaseId': '1.2.0-rc.1-source-factory-r1',
    'recordSha256': 'c4c5639edc09ddc363784b8fcf3c97fb5b5ff99b4815e8421bb2858b657d0da5',
    'lockDigests': {
        'buildInputs': 'f69665e4218111c3f13f35a8ecd6fe2ecdbc7dd3c6c36c46f650f31c479a77b0',
        'simulation': '18769de4641b3b7e2955123094ba7ac983a6af1a734a8fe25c8fd100f3d24e5e'},
    'sourceFiles': {
        'workspace/dependencies/carla-macos-arm64-r1.lock.json': '37311be6f3c1a18893bd61a112e42eddb7c457041168845e39a98c7b67ce151f',
        'workspace/dependencies/developer-factory41-r1.lock.json': '734927ac6c1f8efaf464884773fca37f117ef8ec96f5107ff17a254e6251fe0f',
        'workspace/releases/1.2.0-rc.1-source-factory-build-chain.json': '8ef497219dcbd11d06201330b6f429e07cdb6d672c66bbaad6ede8731334cfd6',
        'workspace/releases/1.2.0-rc.1-source-factory-delivery.json': '33cc8b296bfe76be301b33a170789539a3154dec7a8ad62a3333fff8e9a3ebdc',
        'workspace/releases/kit028-setup042.json': '5951852da7158a63802c1045fe0f37719f90d549b2e70f5f7ab63c5c9841ad13'},
}
# Populated only after release-owner review/publication of a separate public
# catalog and its dependencies. Never expose the current private IDs as defaults.
PUBLIC_PIN = {'url': '', 'releaseId': '1.2.0-rc.1-source-factory-r1-public', 'recordSha256': ''}
ROLES = {'buildInputs': {'vehicle-bases', 'factory-image'},
         'simulation': {'carla-runtime', 'host-support', 'gateway-sdk'}}
LIMIT = 1024 * 1024
FOLDER = 'AosEdge SDV Lab Artifacts'
NAME = 'release-index.json'
FIELDS = 'id,name,mimeType,size,sha256Checksum,version,trashed,parents,capabilities(canDownload)'


class CatalogError(Exception):
    def __init__(self, message, code=12):
        super().__init__(message)
        self.code = code


def require(condition, message):
    if not condition:
        raise CatalogError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def json_bytes(raw):
    require(len(raw) <= LIMIT, 'Catalog metadata exceeds the supported size.')
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'Duplicate JSON fields are not supported.')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def identifier(value):
    require(isinstance(value, str) and re.fullmatch('[A-Za-z0-9_-]{10,200}', value), 'Invalid catalog object identity.')
    return value


def safe_path(value):
    path = Path(value)
    require(path.is_absolute() and '..' not in path.parts
            and not any(p.is_symlink() for p in (path, *path.parents)), 'Unsafe preparation file location.')
    return path


def read_local(value):
    path = safe_path(value)
    require(path.is_file() and path.stat().st_size <= LIMIT, 'Prepared release metadata is missing. Run the preparation wizard first.')
    return json_bytes(path.read_bytes())


def validate_binding(value, group, public=False):
    if public:
        return public_drive.binding(value, PIN['lockDigests'][group], ROLES[group])
    require(isinstance(value, dict) and set(value) == {'schemaVersion', 'lockDigest', 'folderId', 'files'}
            and type(value['schemaVersion']) is int and value['schemaVersion'] == 1
            and value['lockDigest'] == PIN['lockDigests'][group]
            and isinstance(value['files'], dict) and set(value['files']) == ROLES[group],
            'Input selection is incompatible with this preparation script. Obtain the matching release inputs.')
    identifier(value['folderId'])
    for file_id in value['files'].values():
        identifier(file_id)
    return value


def validate_record(entry, public=False):
    pin = PUBLIC_PIN if public else PIN
    require(isinstance(entry, dict) and entry.get('id') == pin['releaseId']
            and digest(entry) == pin['recordSha256'],
            'The selected release record differs from the trusted source pin. No input selection was saved.')
    require(entry['sourceFiles'] == PIN['sourceFiles'] and set(entry['dependencyGroups']) == set(ROLES),
            'Release source requirements differ.')
    for group, row in entry['dependencyGroups'].items():
        validate_binding(row['binding'], group, public)
        require(set(row['packages']) == ROLES[group], 'Release input list is incomplete.')
        for package in row['packages'].values():
            require(set(package) == {'file', 'bytes', 'sha256'} and type(package['bytes']) is int
                    and package['bytes'] > 0 and re.fullmatch('[a-f0-9]{64}', package['sha256']),
                    'Invalid pinned package identity.')
    return entry


def select_record(catalog, public=False):
    pin = PUBLIC_PIN if public else PIN
    require(isinstance(catalog, dict) and set(catalog) == {'schemaVersion', 'product', 'catalogRevision', 'releases'}
            and type(catalog['schemaVersion']) is int and catalog['schemaVersion'] == 1,
            'Unsupported release catalog format. Download the current preparation script from README B1.')
    require(catalog['product'] == 'aosedge-sdv-lab'
            and type(catalog['catalogRevision']) is int and catalog['catalogRevision'] >= 1
            and isinstance(catalog['releases'], list) and 0 < len(catalog['releases']) <= 1000,
            'Invalid release catalog.')
    ids = []
    for entry in catalog['releases']:
        require(isinstance(entry, dict) and isinstance(entry.get('id'), str), 'Invalid release record.')
        ids.append(entry['id'])
    require(len(set(ids)) == len(ids), 'Duplicate release IDs require release-owner reconciliation.')
    require(pin['releaseId'] in ids,
            'No compatible release is available for this preparation script. Contact the release owner; no newer release was substituted.')
    return validate_record(catalog['releases'][ids.index(pin['releaseId'])], public)


def public_ready():
    require(PUBLIC_PIN['url'] and re.fullmatch('[a-f0-9]{64}', PUBLIC_PIN['recordSha256']),
            'Public release inputs have not been published yet. The release owner must publish the reviewed catalog and enable its source pin. No Google account or JSON path is required from you.')
    public_drive.link(PUBLIC_PIN['url'])


def public_discover():
    public_ready()
    client = public_drive.Client()
    record = select_record(json_bytes(client.catalog(PUBLIC_PIN['url'], LIMIT)), public=True)
    for row in record['dependencyGroups'].values():
        for role, url in row['binding']['files'].items():
            client.probe(url, row['packages'][role])
    return record


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Client:
    def __init__(self, gcloud, account):
        require(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', account or ''), 'Google account is missing or invalid.')
        try:
            result = subprocess.run([gcloud, 'auth', 'print-access-token', '--account=' + account],
                                    capture_output=True, text=True, timeout=60,
                                    env={**os.environ, 'CLOUDSDK_CORE_DISABLE_FILE_LOGGING': 'true'})
        except (OSError, subprocess.TimeoutExpired):
            raise CatalogError('Google CLI did not respond. Check connectivity; no new login was started.') from None
        if result.returncode:
            if any(word in result.stderr.lower() for word in ('auth login', 'invalid_grant', 'reauthentication', 'credentials have been revoked')):
                raise CatalogError('Google authorization is missing or expired.', 10)
            raise CatalogError('Google token refresh failed. Check connectivity/CLI; existing authorization was preserved.')
        self.token = result.stdout.strip()
        require(0 < len(self.token) <= 4096 and not any(c.isspace() for c in self.token), 'Google CLI returned an invalid authorization response.')
        self.opener = urllib.request.build_opener(NoRedirect())
        require(self.get('about?fields=user(emailAddress)')['user']['emailAddress'].lower() == account.lower(),
                'Google account differs from the selected account.')

    def raw(self, relative, limit=65536):
        # All paths are assembled here from fixed strings and validated IDs.
        request = urllib.request.Request('https://www.googleapis.com/drive/v3/' + relative,
            headers={'Authorization': 'Bearer ' + self.token, 'Accept-Encoding': 'identity'})
        try:
            with self.opener.open(request, timeout=20) as response:
                raw = response.read(limit + 1)
            require(len(raw) <= limit, 'Drive metadata exceeds the supported size.')
            return raw
        except urllib.error.HTTPError as error:
            if error.code == 401:
                raise CatalogError('Google authorization needs renewal.', 10) from None
            reason = ''
            try:
                reason = json_bytes(error.read(65536))['error']['errors'][0]['reason']
            except (ValueError, KeyError, TypeError, IndexError, CatalogError):
                pass
            if error.code == 403 and reason == 'insufficientPermissions':
                raise CatalogError('Existing Google authorization does not include Drive access.', 11) from None
            raise CatalogError('Drive access check failed (HTTP %s). Ask the release owner to grant this Google account access to the SDV Lab catalog and inputs. No archive was downloaded.' % error.code) from None
        except (OSError, urllib.error.URLError):
            raise CatalogError('Drive could not be reached. Check connectivity and rerun; existing authorization was preserved.') from None

    def get(self, relative):
        return json_bytes(self.raw(relative))

    def metadata(self, file_id):
        return self.get('files/' + identifier(file_id) + '?supportsAllDrives=true&fields=' + FIELDS)

    def unique(self, query, label):
        result = self.get('files?' + urllib.parse.urlencode({
            'q': query, 'pageSize': 2, 'includeItemsFromAllDrives': 'true', 'supportsAllDrives': 'true',
            'fields': 'nextPageToken,incompleteSearch,files(' + FIELDS + ')'}))
        require(not result.get('nextPageToken') and not result.get('incompleteSearch')
                and len(result['files']) <= 1, 'Ambiguous ' + label + '. Ask the release owner to reconcile duplicates; none was selected.')
        require(len(result['files']) == 1, 'The SDV Lab ' + label + ' is not available to this account. Ask the release owner for access; no JSON file is required from you.')
        row = result['files'][0]
        identifier(row['id'])
        return row

    def discover(self):
        folder = self.unique("name = '" + FOLDER + "' and mimeType = 'application/vnd.google-apps.folder' and trashed = false", 'artifact folder')
        row = self.unique("'" + folder['id'] + "' in parents and name = '" + NAME + "' and trashed = false", 'release catalog')
        require(row['name'] == NAME and row['mimeType'] == 'application/json'
                and not row.get('trashed', True) and folder['id'] in row.get('parents', [])
                and row.get('capabilities', {}).get('canDownload') is True
                and 0 < int(row['size']) <= LIMIT and re.fullmatch('[a-f0-9]{64}', row['sha256Checksum']),
                'The release catalog is not a readable bounded JSON file.')
        raw = self.raw('files/' + identifier(row['id']) + '?alt=media&supportsAllDrives=true', LIMIT)
        require(len(raw) == int(row['size']) and hashlib.sha256(raw).hexdigest() == row['sha256Checksum'], 'Release catalog transfer checksum differs.')
        after = self.metadata(row['id'])
        require(all(after.get(k) == row.get(k) for k in ('id', 'name', 'mimeType', 'size', 'sha256Checksum', 'version', 'parents', 'trashed')),
                'Release catalog changed during discovery. Rerun the wizard; no selection was saved.')
        return select_record(json_bytes(raw))

    def check_inputs(self, bindings, record=None):
        for group, binding in bindings.items():
            folder = self.metadata(binding['folderId'])
            require(folder['mimeType'] == 'application/vnd.google-apps.folder' and not folder.get('trashed', True), 'Input folder is unavailable.')
            for role, file_id in binding['files'].items():
                row = self.metadata(file_id)
                require(row['id'] == file_id and not row.get('trashed', True)
                        and binding['folderId'] in row.get('parents', [])
                        and row.get('capabilities', {}).get('canDownload') is True, 'An input is not downloadable from its declared folder. Ask the release owner for access.')
                if record:
                    expected = record['dependencyGroups'][group]['packages'][role]
                    require(row['name'] == expected['file'] and int(row['size']) == expected['bytes']
                            and row['sha256Checksum'] == expected['sha256'], 'An input no longer matches its release. Contact the release owner; no archive was downloaded.')


def private_directory(path, create=False):
    path = safe_path(path)
    if create:
        path.mkdir(mode=0o700, exist_ok=True)
    info = path.stat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700, 'Unsafe catalog state directory.')
    return path


def save_generation(state, record, public=False):
    parent = private_directory(state)
    for part in ('catalog', (PUBLIC_PIN if public else PIN)['recordSha256']):
        parent = private_directory(parent / part, create=True)
    target = safe_path(parent / ('public' if public else 'automatic' if record else 'manual'))
    files = {'source-requirements.json': PIN}
    if record:
        files.update({'release.json': record,
                      'developer-inputs.drive.json': record['dependencyGroups']['buildInputs']['binding'],
                      'simulation-inputs.drive.json': record['dependencyGroups']['simulation']['binding']})
    if target.exists():
        private_directory(target)
        require({p.name for p in target.iterdir()} == set(files), 'Prepared catalog files are incomplete or unexpected; preserved for inspection.')
        for name, value in files.items():
            path = safe_path(target/name)
            info = path.stat()
            require(info.st_uid == os.getuid() and info.st_nlink == 1 and stat.S_IMODE(info.st_mode) == 0o600
                    and read_local(path) == value, 'Prepared catalog files changed; preserved for inspection.')
        return
    temporary = Path(tempfile.mkdtemp(prefix='.pending-', dir=parent))
    try:
        for name, value in files.items():
            fd = os.open(temporary/name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(canonical(value) + b'\n')
        os.rename(temporary, target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)  # This invocation's small generated directory only.


def source_check(receipt, root):
    require(read_local(receipt) == PIN, 'Prepared source selection differs. Rerun the current preparation script before building.')
    for name, expected in PIN['sourceFiles'].items():
        path = safe_path(Path(root)/name)
        require(path.is_file() and path.stat().st_size <= LIMIT and hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                'Cloned source requirements differ from the prepared release. Stop here and rerun preparation for matching sources; do not download or build inputs.')
    print('Source compatibility: PASS — cloned dependency records and producer plan match the prepared release.')


def main(args):
    if len(args) == 2 and args[0] == '--check-source':
        source_check(args[1], Path(__file__).resolve().parents[1])
        return 0
    if args == ['--requirements']:
        print(json.dumps(PIN, sort_keys=True))
        return 0
    # Seven arguments retain the historical private helper interface; the
    # current wizard always supplies the explicit eighth transport argument.
    require(len(args) in (7, 8), 'Invalid catalog helper invocation.')
    gcloud, account, build, simulation, mode, state, advanced = args[:7]
    transport = args[7] if len(args) == 8 else 'private'
    require(transport in ('public', 'private'), 'Invalid catalog transport.')
    public = transport == 'public'
    require(mode in ('local', 'remote') and advanced in ('yes', 'no'), 'Invalid catalog check mode.')
    require(not (public and advanced == 'yes'), 'Manual bindings require explicit private-inputs mode.')
    record = None
    if advanced == 'yes':
        bindings = {g: validate_binding(read_local(p), g) for g, p in (('buildInputs', build), ('simulation', simulation))}
    elif mode == 'local':
        if public:
            public_ready()
        generation = safe_path(Path(state)/'catalog'/(PUBLIC_PIN if public else PIN)['recordSha256']/('public' if public else 'automatic'))
        record = validate_record(read_local(generation/'release.json'), public)
        bindings = {g: validate_binding(read_local(p), g, public) for g, p in (('buildInputs', build), ('simulation', simulation))}
        require(all(v == record['dependencyGroups'][g]['binding'] for g, v in bindings.items()), 'Prepared bindings differ from the trusted release.')
    if mode == 'local':
        print('Input file structure checked; Drive access is not checked in --check mode.')
        return 0
    if public:
        print('Checking the compatible public SDV Lab release (no Google login)…')
        record = public_discover()
        save_generation(state, record, public=True)
        print('Selected release: ' + record['productVersion'] + ' — engineering candidate (not qualified).')
        print('Public catalog pin verified; all five input links/lengths checked. No archives downloaded; complete SHA-256 verification happens during acquisition.')
        return 0
    client = Client(gcloud, account)
    if advanced == 'no':
        print('Finding compatible SDV Lab release…')
        record = client.discover()
        bindings = {g: row['binding'] for g, row in record['dependencyGroups'].items()}
    client.check_inputs(bindings, record)
    save_generation(state, record)
    if record:
        print('Selected release: ' + record['productVersion'] + ' — source-Factory engineering candidate (not qualified).')
        print('CARLA, controller base and supporting inputs: available. Input files prepared automatically.')
    print('Drive account and access to all five inputs checked (metadata only; no archives downloaded).')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except public_drive.PublicDriveError as error:
        print(str(error))
        sys.exit(12)
    except CatalogError as error:
        print(str(error))
        sys.exit(error.code)
    except (ValueError, KeyError, TypeError, IndexError, OSError, RecursionError):
        print('Catalog preparation failed: malformed metadata or unavailable local state. No archive was downloaded; existing files were preserved.')
        sys.exit(12)
PY
}
write_environment() {
  local ready=$1 key tmp
  tmp=$(mktemp "$STATE/environment.XXXXXX") || die 'Cannot write environment handoff.'
  {
    say '# Generated by AosEdge developer preparation. No credentials are stored here.'
    say 'unset SDV_PARENT SDV_ROOT SDV_TMP SDV_PYTHON SDV_CMAKE SDV_NODE SDV_NPM SDV_DOCKER SDV_GCLOUD SDV_DRIVE_ACCOUNT SDV_BUILD_BINDING SDV_SIM_BINDING SDV_PREPARED_SOURCE SDV_SIGNING_IDENTITY'
    if [ "$ready" != yes ]; then
      say "printf '%s\n' 'STOP: Developer preparation is incomplete. Rerun the preparation script.' >&2"
      say 'return 1'
    else
      printf 'SDV_PARENT=%q\n' "$SDV_PARENT"
      printf 'SDV_EXPECTED_VOLUME=%q\n' "$SELECTED_UUID"
      # Fail on disconnect/replacement, including a stale /Volumes directory.
      say 'SDV_CURRENT_DEVICE=$(LC_ALL=C df -kP "$SDV_PARENT" 2>/dev/null | awk '\''NR==2 {print $1}'\'')'
      say 'SDV_CURRENT_VOLUME=$(diskutil info -plist "$SDV_CURRENT_DEVICE" 2>/dev/null | plutil -extract VolumeUUID raw -o - - 2>/dev/null)'
      say '[ "$SDV_CURRENT_VOLUME" = "$SDV_EXPECTED_VOLUME" ] || { printf "%s\n" "STOP: Prepared disk is missing or changed." >&2; return 1; }'
      for key in SDV_ROOT SDV_TMP SDV_PYTHON SDV_CMAKE SDV_NODE SDV_NPM SDV_DOCKER SDV_GCLOUD SDV_DRIVE_ACCOUNT SDV_BUILD_BINDING SDV_SIM_BINDING SDV_PREPARED_SOURCE SDV_SIGNING_IDENTITY DEVELOPER_DIR; do
        printf 'export %s=%q\n' "$key" "${!key}"
      done
      printf 'export TMPDIR=%q HOMEBREW_TEMP=%q\n' "$SDV_TMP" "$SDV_TMP"
      printf 'export HOMEBREW_CACHE=%q PIP_CACHE_DIR=%q npm_config_cache=%q\n' "$SDV_ROOT/cache/homebrew" "$SDV_ROOT/cache/pip" "$SDV_ROOT/cache/npm"
      printf 'export PATH=%q:"$PATH"\n' "$(dirname "$SDV_PYTHON"):$(dirname "$SDV_NODE"):/opt/homebrew/bin"
      say 'unset SDV_EXPECTED_VOLUME SDV_CURRENT_DEVICE SDV_CURRENT_VOLUME'
      say "printf '%s\n' 'Developer environment loaded.'"
    fi
  } > "$tmp"
  mv "$tmp" "$STATE/environment.sh" || die 'Cannot publish environment handoff.'
}
bootstrap_checkout() {
  "$SDV_PYTHON" -B - "$SDV_ROOT" "$SELECTED_UUID" "$SDV_PREPARED_SOURCE" <<'BOOTSTRAP_PY'
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Small pre-clone owner. Embedded in the downloadable macOS launcher."""
import hashlib
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile

REMOTE = 'https://github.com/alexmaninblack/aosedge-sdv-demo.git'


class WorkflowError(RuntimeError):
    pass


def require(ok, message):
    if not ok:
        raise WorkflowError(message)


def safe(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts
            and not any(p.is_symlink() for p in (path, *path.parents)),
            'Unsafe or linked workflow path; existing files were preserved.')
    return path


def read(path):
    path = safe(path)
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
            and info.st_nlink == 1 and info.st_size <= 1024 * 1024,
            'Unsafe workflow metadata; existing files were preserved.')
    return json.loads(path.read_text())


def save(path, value):
    path = safe(path)
    fd, temporary = tempfile.mkstemp(prefix='.workflow-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, sort_keys=True)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def git(directory, *args, timeout=60, optional=False):
    # No interactive credentials, inherited repository overrides or local hooks.
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_TERMINAL_PROMPT='0', GIT_CONFIG_NOSYSTEM='1',
               GIT_CONFIG_GLOBAL='/dev/null', GIT_LFS_SKIP_SMUDGE='1')
    process = subprocess.Popen(['git', '-c', 'core.hooksPath=/dev/null',
                                '-c', 'protocol.file.allow=never', *args],
                               cwd=directory, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        output, _ = process.communicate(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(process.pid, sig)
            except ProcessLookupError:
                pass
            try:
                process.communicate(timeout=3)
                break
            except subprocess.TimeoutExpired:
                continue
        if isinstance(error, KeyboardInterrupt):
            raise
        raise WorkflowError('Source operation timed out. The selected commit and partial checkout were preserved; rerun after checking connectivity.') from None
    if optional and process.returncode != 0:
        return ''
    require(process.returncode == 0,
            'Source operation failed. Check connectivity/repository access; existing sources and the selected commit were preserved.')
    return output.strip()


def validate_checkout(path, revision=None):
    safe(path)
    require((path/'.git').is_dir() and not (path/'.git').is_symlink(),
            'Expected an independent source checkout, not a linked worktree.')
    require(git(path, 'rev-parse', '--show-toplevel') == str(path)
            and git(path, 'remote') == 'origin'
            and git(path, 'remote', 'get-url', '--all', 'origin') == REMOTE,
            'Existing source belongs to a different repository; it was not changed.')
    require(not git(path, 'status', '--porcelain', '--untracked-files=all'),
            'Existing source has local changes. Preserve/review them before continuing; no reset or overwrite was performed.')
    actual = git(path, 'rev-parse', 'HEAD')
    require(re.fullmatch('[a-f0-9]{40}', actual) and (revision is None or actual == revision),
            'Source revision changed since this build was selected; no update was adopted.')
    return actual


def source_matches(source, requirements):
    pins = requirements.get('sourceFiles')
    require(isinstance(pins, dict) and pins, 'Prepared source requirements are missing.')
    for name, expected in pins.items():
        require(isinstance(name, str) and not Path(name).is_absolute()
                and '..' not in Path(name).parts and re.fullmatch('[a-f0-9]{64}', expected),
                'Invalid prepared source requirement.')
        path = safe(source/name)
        require(path.is_file() and path.stat().st_size <= 1024*1024
                and hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                'Cloned source requirements differ from the prepared release. Obtain matching preparation/source; no inputs were downloaded or built.')
    require((source/'scripts/developer_build.py').is_file(),
            'The selected repository revision does not yet contain the one-run workflow. Publish the reviewed source before the joint walkthrough.')


def checkout(root, volume, requirements_path):
    lock = safe(Path(root)/'.developer-preparation/workflow.lock')
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise WorkflowError('Another source/build workflow is using this workspace.') from None
        return _checkout(root, volume, requirements_path)


def _checkout(root, volume, requirements_path):
    root = safe(root)
    control = safe(root/'.developer-preparation')
    require(control.is_dir() and (control/'.aosedge-preparation').read_text().strip()
            == 'aosedge-developer-preparation-v1', 'Prepared workspace ownership is missing.')
    requirements = read(requirements_path)
    requirements_key = hashlib.sha256(json.dumps(requirements, sort_keys=True,
                                                separators=(',', ':')).encode()).hexdigest()
    source = safe(root/'source')
    partial = safe(control/'source.partial')
    receipt = safe(control/'root-source.json')
    binding = dict(schemaVersion=1, remote=REMOTE, root=str(root), volumeUUID=volume,
                   requirementsSha256=requirements_key)
    if receipt.exists():
        selected = read(receipt)
        require(set(selected) == set(binding) | {'revision'}
                and all(selected[k] == v for k, v in binding.items())
                and re.fullmatch('[a-f0-9]{40}', selected['revision']),
                'Saved source selection belongs to another volume/release. Use a separate workspace; nothing was replaced.')
    else:
        require(not partial.exists(), 'Unowned partial checkout preserved; inspect it before continuing.')
        if source.exists():
            revision = validate_checkout(source)
            source_matches(source, requirements)
        else:
            print('Selecting the current main revision…', flush=True)
            rows = git(root, 'ls-remote', '--exit-code', REMOTE, 'refs/heads/main').splitlines()
            require(len(rows) == 1 and re.fullmatch('[a-f0-9]{40}\trefs/heads/main', rows[0]),
                    'Cannot resolve one main revision; no source was selected.')
            revision = rows[0].split()[0]
        selected = {**binding, 'revision': revision}
        # Persist before fetching: a resumed run never follows a moving main.
        save(receipt, selected)
    revision = selected['revision']
    if not source.exists():
        partial.mkdir(exist_ok=True, mode=0o700)
        if not (partial/'.git').exists():
            require(not any(partial.iterdir()), 'Unexpected partial checkout contents preserved.')
            git(partial, 'init', '--quiet')
        require((partial/'.git').is_dir() and not (partial/'.git').is_symlink(), 'Unsafe partial Git directory.')
        remotes = git(partial, 'remote')
        if not remotes:
            git(partial, 'remote', 'add', 'origin', REMOTE)
        require(git(partial, 'remote') == 'origin'
                and git(partial, 'remote', 'get-url', '--all', 'origin') == REMOTE,
                'Partial checkout remote changed; preserved without fetching.')
        # A checkout interrupted after materialization is reused only if clean.
        probe = git(partial, 'rev-parse', '--verify', '--quiet', '--end-of-options', revision+'^{commit}', optional=True)
        if not probe:
            print('Downloading root source (large binary inputs are not included)…', flush=True)
            git(partial, 'fetch', '--quiet', '--no-tags', 'origin', revision, timeout=900)
        # Do not force/reset an interrupted or modified worktree.
        require(not git(partial, 'status', '--porcelain', '--untracked-files=all'),
                'Partial source checkout has changes; inspect it before resuming.')
        git(partial, 'checkout', '--quiet', '--detach', revision)
        validate_checkout(partial, revision)
        source_matches(partial, requirements)
        require(not source.exists(), 'Source destination appeared during preparation; both copies preserved.')
        os.rename(partial, source)
    validate_checkout(source, revision)
    source_matches(source, requirements)
    print('Root source ready at ' + revision + ' (fixed for repeats).', flush=True)
    return selected


if __name__ == '__main__':
    def cancel(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, cancel)
    signal.signal(signal.SIGINT, cancel)
    try:
        require(len(sys.argv) == 4, 'Invalid bootstrap invocation.')
        checkout(*sys.argv[1:])
    except KeyboardInterrupt:
        print('Source preparation stopped; selection and partial work preserved.', file=sys.stderr)
        sys.exit(130)
    except (WorkflowError, OSError, ValueError, KeyError, TypeError) as error:
        print('STOP: ' + (str(error) if isinstance(error, WorkflowError) else
                         'Source preparation metadata is unavailable or malformed; existing files preserved.'), file=sys.stderr)
        sys.exit(1)
BOOTSTRAP_PY
}
continue_workflow() {
  local result
  recheck_storage
  WORKFLOW_CHILD=yes
  set -m
  bootstrap_checkout & CHILD_PID=$!
  set +m
  wait "$CHILD_PID"; result=$?; CHILD_PID=; WORKFLOW_CHILD=no
  [ "$result" = 0 ] || return "$result"
  recheck_storage
  private_file "$STATE/environment.sh" || die 'Unsafe environment handoff.'
  source "$STATE/environment.sh" || return $?
  export SDV_WORKFLOW_VOLUME="$SELECTED_UUID"
  # The host-preparation lock remains held until the repository continuation exits.
  WORKFLOW_CHILD=yes
  set -m
  "$SDV_PYTHON" -B "$SDV_ROOT/source/scripts/developer_build.py" & CHILD_PID=$!
  set +m
  wait "$CHILD_PID"; result=$?; CHILD_PID=; WORKFLOW_CHILD=no
  return "$result"
}
main() {
  local mode=prepare arg confirm drive_status blocked=no
  set -o pipefail
  export CLOUDSDK_CORE_DISABLE_FILE_LOGGING=true
  SDV_PARENT= DEVELOPER_DIR= LOG= CHILD_PID= LOCKED=no CONFIGURE_ACCESS=no ADVANCED_INPUTS=no PRIVATE_INPUTS=no PREPARE_ONLY=no WORKFLOW_CHILD=no
  STATE="$HOME/Library/Application Support/AosEdge SDV Lab/Developer"
  while [ "$#" -gt 0 ]; do
    arg=$1; shift
    case "$arg" in
      --help|-h) help_text; return 0 ;;
      --requirements) requirements; return 0 ;;
      --check) mode=check ;;
      --prepare-only) PREPARE_ONLY=yes ;;
      --configure-access) CONFIGURE_ACCESS=yes ;;
      --private-inputs) PRIVATE_INPUTS=yes ;;
      --advanced-inputs) ADVANCED_INPUTS=yes; PRIVATE_INPUTS=yes ;;
      --parent|--xcode|--state-dir) [ "$#" -gt 0 ] || die "$arg needs a value."
        case "$arg" in --parent) SDV_PARENT=$1 ;; --xcode) DEVELOPER_DIR=$1 ;; --state-dir) STATE=$1 ;; esac; shift ;;
      *) die "Unknown option: $arg" ;;
    esac
  done
  [ "$(uname -s)" = Darwin ] && [ "$(uname -m)" = arm64 ] || die 'Use a native Terminal on an Apple Silicon Mac, not Rosetta.'
  [ "$(id -u)" != 0 ] || die 'Run as your ordinary user, not with sudo.'
  version_at_least "$(sw_vers -productVersion)" "$SDV_MACOS_MIN.0" || die "macOS $SDV_MACOS_MIN or later is required."
  safe_path "$STATE" || die 'Unsafe preparation state location.'
  [ "$STATE" != / ] && [ "$STATE" != "$HOME" ] || die 'Use a dedicated preparation state directory.'
  [ ! -e "$STATE/selections.tsv" ] || private_file "$STATE/selections.tsv" || die 'Saved selections have unsafe ownership or permissions.'
  say "AosEdge SDV Lab — Developer build launcher v$SDV_PREP_VERSION"
  say 'Preparation → source checkout → verified inputs → developer DMG'; say ''
  if [ "$mode" != check ] && [ "$PRIVATE_INPUTS" != yes ] && { [ -z "$SDV_PUBLIC_CATALOG_URL" ] || [ -z "$SDV_PUBLIC_CATALOG_RECORD" ]; }; then
    say 'PUBLIC RELEASE NOT YET AVAILABLE — the release owner must publish reviewed inputs and enable their source pin.'
    say 'No Google account or JSON path is required from you. Nothing was installed or changed.'
    return 2
  fi
  choose_storage; load_choices; discover; show_plan
  if [ "$mode" = check ]; then
    say ''; say 'CHECK ONLY — no changes or network access.'
    [ "$XCODE_OK" = yes ] && [ -n "$SDV_CMAKE" ] && [ "$PYTHON_OK" = yes ] && [ -n "$SDV_NODE" ] && [ -n "$SDV_DOCKER" ] || blocked=yes
    [ "$PRIVATE_INPUTS" != yes ] || [ -n "$SDV_GCLOUD" ] || blocked=yes
    if [ "$PYTHON_OK" = yes ]; then
      docker_ready || { say 'Docker: complete first-run setup and start the local Engine; no restart was attempted.'; blocked=yes; }
      drive_probe local || blocked=yes
    fi
    identity_ready || { say 'Signing identity: select an available Apple Development identity during preparation.'; blocked=yes; }
    say 'Remote input availability and complete build capacity remain separate checks; this is not a READY result.'
    [ "$blocked" = no ] && return 0 || return 2
  fi
  if [ "$XCODE_OK" != yes ]; then
    say ''; say 'ACTION REQUIRED: Install/open Xcode, finish its license and components, then rerun.'
    say 'For a nonstandard Xcode location, use --xcode /path/to/Xcode.app. No system-wide selection is changed.'
    return 2
  fi
  if [ "$PREPARE_ONLY" = yes ]; then
    confirm=$(ask 'Prepare this environment only? (yes/no)' no)
  else
    confirm=$(ask 'Proceed with preparation and the developer DMG build? (yes/no)' no)
  fi
  [ "$confirm" = yes ] || { say 'Cancelled. No changes made.'; return 2; }
  setup_state
  say '[1/6] Workspace ready'; say '[2/6] Apple tools ready'
  prepare_python_cmake; prepare_node; prepare_access_tools
  docker_ready || { say 'ACTION: Open Docker once, finish its first-run prompts and start the Engine. Then rerun; existing work is preserved.'; blocked=yes; }
  choose_access
  drive_probe remote; drive_status=$?
  if [ "$PRIVATE_INPUTS" = yes ] && { [ "$drive_status" = 10 ] || [ "$drive_status" = 11 ]; }; then
    say 'Google will ask for Drive/Cloud consent. Review its permissions; the script reads only the small release catalog and input metadata.'
    # Do not redirect, tee or persist OAuth login output/capabilities.
    "$SDV_GCLOUD" auth login "$SDV_DRIVE_ACCOUNT" --enable-gdrive-access --no-activate && drive_probe remote
    drive_status=$?
  fi
  [ "$drive_status" = 0 ] || blocked=yes
  [ "$blocked" != no ] || say '[5/6] Docker / input access ready'
  identity_ready || { say 'ACTION: A usable Apple Development identity is required. No certificate or private key was created, exported or used to sign.'; blocked=yes; }
  save_choices
  recheck_storage
  if [ "$blocked" = yes ]; then
    say ''; say 'PREPARATION INCOMPLETE — selections saved. Resolve the actions above and rerun the same script.'
    return 2
  fi
  say '[6/6] Signing / inputs ready'
  write_environment yes
  say ''; say 'READY FOR SOURCE PREPARATION'
  say 'This is not a completed build or a guarantee of full-build capacity.'
  say "Diagnostic log: $LOG"
  if [ "$PREPARE_ONLY" = yes ]; then
    say 'Preparation-only complete. Rerun without --prepare-only to continue automatically.'
    say "Optional manual handoff: $STATE/environment.sh"
    return 0
  fi
  say 'Continuing automatically; no more commands need to be copied.'
  continue_workflow
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then main "$@"; fi
