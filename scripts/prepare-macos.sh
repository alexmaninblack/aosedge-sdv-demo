#!/bin/bash
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
# Standalone before Git/Python/Homebrew. Compatible with Apple's Bash 3.2.
# Sourceable by offline fixtures; execution always goes through main().

SDV_PREP_VERSION=1
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
  say 'AosEdge SDV Lab — macOS developer preparation'
  say 'Usage: /bin/bash prepare-macos.sh [--check] [--parent PATH] [--xcode PATH] [--configure-access]'
  say 'Default: inspect, show one plan, ask once, prepare missing prerequisites.'
  say '--check: local diagnostics only; no writes, downloads, login or installation.'
  say '--parent PATH: existing internal/external APFS parent for the workspace.'
  say '--xcode PATH: Xcode.app or its Contents/Developer directory (session only).'
  say '--configure-access: review/change saved account, input paths and signing selection.'
  say '--state-dir PATH: explicit private control directory (default: Library/Application Support/AosEdge SDV Lab/Developer).'
  say '--requirements: print machine-readable bootstrap requirements and exit.'
  say 'Repeat the same command to resume. No clone, build, demo or Docker restart.'
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
  for candidate in "$(command -v gcloud)" /opt/homebrew/bin/gcloud /opt/homebrew/share/google-cloud-sdk/bin/gcloud; do
    if [ -x "$candidate" ] && "$candidate" version >/dev/null 2>&1; then SDV_GCLOUD=$candidate; break; fi
  done
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
  SDV_BUILD_BINDING=$(state_get SDV_BUILD_BINDING)
  SDV_SIM_BINDING=$(state_get SDV_SIM_BINDING)
  SDV_SIGNING_IDENTITY=$(state_get SDV_SIGNING_IDENTITY)
  if [ -z "$DEVELOPER_DIR" ]; then
    DEVELOPER_DIR=$(state_get DEVELOPER_DIR)
    [ -n "$DEVELOPER_DIR" ] || DEVELOPER_DIR=$(xcode-select -p 2>/dev/null)
    case "$DEVELOPER_DIR" in */Xcode*.app/Contents/Developer) ;; *) DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer ;; esac
  fi
  case "$DEVELOPER_DIR" in *.app) DEVELOPER_DIR="$DEVELOPER_DIR/Contents/Developer" ;; esac
  export DEVELOPER_DIR
}
show_plan() {
  say ''; say 'Preparation plan — no changes yet'
  say "[1/6] Storage: checked; workspace $SDV_ROOT; scratch $SDV_TMP"
  if [ "$XCODE_OK" = yes ]; then say '[2/6] Apple tools: reuse selected Xcode, SDK, Swift and Git';
  else say '[2/6] Apple tools: ACTION — install/open Xcode, finish its license and components, then rerun'; fi
  if [ -n "$SDV_CMAKE" ] && [ "$PYTHON_OK" = yes ]; then say '[3/6] CMake / Python: reuse compatible tools';
  else say '[3/6] CMake / Python: prepare missing tools and project Python environment'; fi
  [ -n "$SDV_NODE" ] && say "[4/6] Node $SDV_NODE_VERSION / npm $SDV_NPM_VERSION: reuse" || say "[4/6] Node $SDV_NODE_VERSION / npm $SDV_NPM_VERSION: install inside the workspace"
  say '[5/6] Docker / Drive: reuse tools, install missing ones; check Engine and authorized access'
  say '[6/6] Signing / inputs: select existing identity and two private input files; verify metadata'
  if [ -z "$BREW" ] && { [ -z "$SDV_CMAKE" ] || [ -z "$BASE_PYTHON" ] || [ -z "$SDV_DOCKER" ] || [ -z "$SDV_GCLOUD" ]; }; then
    say 'Homebrew is missing: its official installer will be offered (may require an administrator password).'
  fi
  say 'Host tools use their standard macOS locations; project tools/caches use the selected disk.'
  say 'Package managers may install required dependencies. No upgrade, cleanup or Docker restart is requested.'
  say 'No source clone, heavy input download, build, signing operation or demo launch.'
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
  for key in SDV_PARENT SDV_TMP SDV_DRIVE_ACCOUNT SDV_BUILD_BINDING SDV_SIM_BINDING SDV_SIGNING_IDENTITY DEVELOPER_DIR; do
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
  say ''; say 'Private build access — saved selections are reused. Missing items can be left empty for now.'
  if [ "${CONFIGURE_ACCESS:-no}" = yes ]; then
    SDV_DRIVE_ACCOUNT=$(ask 'Google account with access to the build inputs' "$SDV_DRIVE_ACCOUNT")
    SDV_BUILD_BINDING=$(ask 'Full path to developer-inputs.drive.json (no quotes)' "$SDV_BUILD_BINDING")
    SDV_SIM_BINDING=$(ask 'Full path to simulation-inputs.drive.json (no quotes)' "$SDV_SIM_BINDING")
    SDV_SIGNING_IDENTITY=
  fi
  [ -n "$SDV_DRIVE_ACCOUNT" ] || SDV_DRIVE_ACCOUNT=$(ask 'Google account with access to the build inputs' '')
  [ -r "$SDV_BUILD_BINDING" ] || SDV_BUILD_BINDING=$(ask 'Full path to developer-inputs.drive.json (no quotes)' '')
  [ -r "$SDV_SIM_BINDING" ] || SDV_SIM_BINDING=$(ask 'Full path to simulation-inputs.drive.json (no quotes)' '')
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
drive_probe() {
  # OAuth tokens live only in this bounded process, never shell variables/files/logs.
  "$SDV_PYTHON" -I -B - "$SDV_GCLOUD" "$SDV_DRIVE_ACCOUNT" "$SDV_BUILD_BINDING" "$SDV_SIM_BINDING" "$1" <<'PY'
import json, os, re, subprocess, sys, urllib.request, urllib.error
gcloud, account, build, simulation, mode = sys.argv[1:]
def stop(code, message):
    print(message); raise SystemExit(code)
if not account or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', account):
    stop(12, 'Google account is missing or invalid.')
bindings = []
try:
    for path, roles in ((build, {'vehicle-bases','factory-image'}), (simulation, {'carla-runtime','host-support','gateway-sdk'})):
        if not os.path.isabs(path) or not os.path.isfile(path) or os.path.islink(path) or os.path.getsize(path) > 65536:
            raise ValueError()
        with open(path) as f: value = json.load(f)
        assert set(value) == {'schemaVersion','lockDigest','folderId','files'} and value['schemaVersion'] == 1
        assert re.fullmatch('[a-f0-9]{64}', value['lockDigest']) and set(value['files']) == roles
        assert all(re.fullmatch('[A-Za-z0-9_-]{10,200}', v) for v in (value['folderId'], *value['files'].values()))
        bindings.append(value)
except Exception:
    stop(12, 'Two valid private Drive binding files are required. Their content is not printed.')
if mode == 'local':
    stop(0, 'Input file structure checked; Drive access is not checked in --check mode.')
try:
    result = subprocess.run([gcloud,'auth','print-access-token','--account='+account], capture_output=True, text=True, timeout=60)
    token = result.stdout.strip()
    if result.returncode:
        # A transport/tool error is not evidence that consent must be repeated.
        if any(word in result.stderr.lower() for word in ('auth login', 'invalid_grant', 'reauthentication', 'credentials have been revoked')):
            stop(10, 'Google authorization is missing or expired.')
        stop(12, 'Google token refresh failed. Check connectivity/CLI; existing authorization was preserved.')
    if not token or len(token)>4096 or any(c.isspace() for c in token):
        stop(12, 'Google CLI returned an invalid authorization response; nothing was sent to Drive.')
except (OSError, subprocess.TimeoutExpired):
    stop(12, 'Google CLI did not respond. Check connectivity/CLI and rerun; no new login was started.')
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None
opener = urllib.request.build_opener(NoRedirect())
def get(relative):
    request = urllib.request.Request('https://www.googleapis.com/drive/v3/'+relative, headers={'Authorization':'Bearer '+token})
    try:
        with opener.open(request, timeout=20) as response:
            raw = response.read(65537)
        assert len(raw)<=65536
        return json.loads(raw)
    except urllib.error.HTTPError as error:
        if error.code == 401: stop(10, 'Google authorization needs renewal.')
        reason = ''
        try:
            reason = json.loads(error.read(65536))['error']['errors'][0]['reason']
        except Exception: pass
        if error.code == 403 and reason == 'insufficientPermissions':
            stop(11, 'Existing Google authorization does not include Drive access.')
        stop(12, 'Drive metadata request failed (HTTP %s). Check input access; no files were downloaded.' % error.code)
    except Exception:
        stop(12, 'Drive metadata could not be checked. Check connectivity and rerun; no files were downloaded.')
try:
    assert get('about?fields=user(emailAddress)')['user']['emailAddress'].lower() == account.lower()
    for binding in bindings:
        folder = get('files/'+binding['folderId']+'?fields=id,mimeType,trashed')
        assert folder['mimeType'] == 'application/vnd.google-apps.folder' and not folder.get('trashed', True)
        for file_id in binding['files'].values():
            row = get('files/'+file_id+'?fields=id,trashed,parents,capabilities(canDownload)')
            assert row['id'] == file_id and not row.get('trashed',True)
            assert binding['folderId'] in row.get('parents',[]) and row.get('capabilities',{}).get('canDownload') is True
except (AssertionError, KeyError, TypeError):
    stop(12, 'Selected account or input metadata does not match. Request matching input access from the release owner.')
print('Drive account and access to all five inputs checked (metadata only).')
PY
}
write_environment() {
  local ready=$1 key tmp
  tmp=$(mktemp "$STATE/environment.XXXXXX") || die 'Cannot write environment handoff.'
  {
    say '# Generated by AosEdge developer preparation. No credentials are stored here.'
    say 'unset SDV_PARENT SDV_ROOT SDV_TMP SDV_PYTHON SDV_CMAKE SDV_NODE SDV_NPM SDV_DOCKER SDV_GCLOUD SDV_DRIVE_ACCOUNT SDV_BUILD_BINDING SDV_SIM_BINDING SDV_SIGNING_IDENTITY'
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
      for key in SDV_ROOT SDV_TMP SDV_PYTHON SDV_CMAKE SDV_NODE SDV_NPM SDV_DOCKER SDV_GCLOUD SDV_DRIVE_ACCOUNT SDV_BUILD_BINDING SDV_SIM_BINDING SDV_SIGNING_IDENTITY DEVELOPER_DIR; do
        printf 'export %s=%q\n' "$key" "${!key}"
      done
      printf 'export TMPDIR=%q HOMEBREW_TEMP=%q\n' "$SDV_TMP" "$SDV_TMP"
      printf 'export HOMEBREW_CACHE=%q PIP_CACHE_DIR=%q npm_config_cache=%q\n' "$SDV_ROOT/cache/homebrew" "$SDV_ROOT/cache/pip" "$SDV_ROOT/cache/npm"
      printf 'export PATH=%q:"$PATH"\n' "$(dirname "$SDV_PYTHON"):$(dirname "$SDV_NODE"):/opt/homebrew/bin"
      say 'unset SDV_EXPECTED_VOLUME SDV_CURRENT_DEVICE SDV_CURRENT_VOLUME'
      say "printf '%s\n' 'Developer environment loaded. Continue with README B2.'"
    fi
  } > "$tmp"
  mv "$tmp" "$STATE/environment.sh" || die 'Cannot publish environment handoff.'
}
main() {
  local mode=prepare arg confirm drive_status blocked=no
  set -o pipefail
  export CLOUDSDK_CORE_DISABLE_FILE_LOGGING=true
  SDV_PARENT= DEVELOPER_DIR= LOG= CHILD_PID= LOCKED=no CONFIGURE_ACCESS=no
  STATE="$HOME/Library/Application Support/AosEdge SDV Lab/Developer"
  while [ "$#" -gt 0 ]; do
    arg=$1; shift
    case "$arg" in
      --help|-h) help_text; return 0 ;;
      --requirements) requirements; return 0 ;;
      --check) mode=check ;;
      --configure-access) CONFIGURE_ACCESS=yes ;;
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
  say "AosEdge SDV Lab — Developer preparation v$SDV_PREP_VERSION"
  say 'No clone or build is performed by this script.'; say ''
  choose_storage; load_choices; discover; show_plan
  if [ "$mode" = check ]; then
    say ''; say 'CHECK ONLY — no changes or network access.'
    [ "$XCODE_OK" = yes ] && [ -n "$SDV_CMAKE" ] && [ "$PYTHON_OK" = yes ] && [ -n "$SDV_NODE" ] && [ -n "$SDV_DOCKER" ] && [ -n "$SDV_GCLOUD" ] || blocked=yes
    if [ "$PYTHON_OK" = yes ]; then
      docker_ready || { say 'Docker: complete first-run setup and start the local Engine; no restart was attempted.'; blocked=yes; }
      drive_probe local || blocked=yes
    fi
    identity_ready || { say 'Signing identity: select an available Apple Development identity during preparation.'; blocked=yes; }
    say 'Drive authorization and complete build capacity remain separate checks; this is not a READY result.'
    [ "$blocked" = no ] && return 0 || return 2
  fi
  if [ "$XCODE_OK" != yes ]; then
    say ''; say 'ACTION REQUIRED: Install/open Xcode, finish its license and components, then rerun.'
    say 'For a nonstandard Xcode location, use --xcode /path/to/Xcode.app. No system-wide selection is changed.'
    return 2
  fi
  confirm=$(ask 'Prepare this environment? (yes/no)' no)
  [ "$confirm" = yes ] || { say 'Cancelled. No changes made.'; return 2; }
  setup_state
  say '[1/6] Workspace ready'; say '[2/6] Apple tools ready'
  prepare_python_cmake; prepare_node; prepare_access_tools
  docker_ready || { say 'ACTION: Open Docker once, finish its first-run prompts and start the Engine. Then rerun; existing work is preserved.'; blocked=yes; }
  choose_access
  drive_probe remote; drive_status=$?
  if [ "$drive_status" = 10 ] || [ "$drive_status" = 11 ]; then
    say 'Google will ask for Drive/Cloud consent. Review its permissions; the script reads input metadata only.'
    # Do not redirect, tee or persist OAuth login output/capabilities.
    "$SDV_GCLOUD" auth login "$SDV_DRIVE_ACCOUNT" --enable-gdrive-access --no-activate && drive_probe remote
    drive_status=$?
  fi
  [ "$drive_status" = 0 ] || blocked=yes
  [ "$blocked" != no ] || say '[5/6] Docker / Drive ready'
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
  say 'Return to README B1: load the saved environment, then continue to B2.'
  say "Environment: $STATE/environment.sh"
  say "Diagnostic log: $LOG"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then main "$@"; fi
