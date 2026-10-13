#!/bin/bash
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
# One downloadable Apple Bash 3.2 entry; no Git/Python/Homebrew required.

SDV_LAB_VERSION=1
# BEGIN VERIFIED MODULE PINS — maintained by scripts/sync-launcher-pins
lab_spec() {
  case "$1" in
    developer) printf '%s\n' '0577cb8bac914f07648325b6370eb5cefbcad423 9a9b7c8fd95eb1a3e83558ada660260df9a4b4073a7fd8f08d2899f986735560 80942' ;;
    install) printf '%s\n' 'a8ad575e89457651bbc31a1079f9ba2e683786b1 6a12c9e2d342de89f87f38eeb655dc9dc26ea17c9ca75999388ec826ae257b87 11279' ;;
    heavy) printf '%s\n' '3bbac8fd4939dc0c129e1e3affe5c2d199918912 d028e2ce7c476b76951be97a126508e357880b6729623b77bb09b6daf8797de9 7864' ;;
    common) printf '%s\n' '9b5c35aa3b9c1f3f7d849368601d862ca4674fd6 a9b3f24c4f8acaa7f86b777e149980ad8138fef976598165fa336aca03986f89 5401' ;;
    catalog) printf '%s\n' 'd1fe4c42894eb0e30575fcdec9e27c0eeb3e12e3 40947e86c4e2a9210fa79bdff3ffe1a5804fae12dc997a27d0d4c88ceed41447 1043' ;;
    drive-parser) printf '%s\n' 'adf78cc74e1f13230c96c057a71d82f9d8af34b8 3377608f34350c2f2bfd40ab99653eace743f1a0972ee8aa62860a86ae7eba62 4269' ;;
    *) return 1 ;;
  esac
}
# END VERIFIED MODULE PINS

lab_say() { printf '%s\n' "$*"; }
lab_die() { printf '\nSTOP: %s\n' "$*" >&2; exit 1; }
lab_help() {
  lab_say 'AosEdge SDV Lab — install, build or prepare specialist tools'
  lab_say 'Usage: /bin/bash aosedge-sdv-lab.sh [--route A|B|C] [--parent PATH] [--check | --plan]'
  lab_say 'A: approved DMG → signed Setup. Optional: --dmg /absolute/file.dmg'
  lab_say 'B: existing developer workflow → signed engineering DMG. Optional: --prepare-only'
  lab_say 'C: host tools only. Optional: --component factory|simulator and --xcode PATH'
  lab_say '--check: cached/local checks only; no download, installation or state write.'
  lab_say '--plan: describe the selected route only; no host probes, downloads or changes.'
  lab_say '--parent: existing APFS folder on an internal or external disk; no disk formatting.'
  lab_say '--state-dir: explicit private launcher control directory, not bulk build storage.'
  lab_say 'Rerun this same file to resume. No automatic source update, Cloud publication or Docker restart.'
}
lab_path() {
  local path=$1
  case "$path" in /*) ;; *) return 1 ;; esac
  case "$path/" in *$'\n'*|*$'\r'*|*$'\t'*|*'/../'*|*'/./'*|*'//'*) return 1 ;; esac
  while [ "$path" != / ]; do [ ! -L "$path" ] || return 1; path=$(dirname "$path"); done
}
lab_file() {
  lab_path "$1" && [ -f "$1" ] && [ "$(stat -f %u "$1")" = "$(id -u)" ] &&
    [ "$(stat -f %l "$1")" = 1 ] && [ "$(stat -f %Lp "$1")" = 600 ]
}
lab_directory() {
  local path=$1
  lab_path "$path" || lab_die 'Linked or unsafe launcher directory; preserved.'
  if [ -e "$path" ]; then
    [ -d "$path" ] && [ "$(stat -f %u "$path")" = "$(id -u)" ] &&
      [ "$(stat -f %Lp "$path")" = 700 ] && lab_file "$path/.owner" &&
      [ "$(<"$path/.owner")" = aosedge-lab-launcher-v1 ] || lab_die 'Unowned launcher directory; preserved.'
  else
    mkdir -m 700 "$path" || lab_die 'Cannot create launcher directory.'
    printf '%s\n' aosedge-lab-launcher-v1 > "$path/.owner"
  fi
}
lab_state() {
  umask 077
  lab_path "$LAB_STATE" && [ "$LAB_STATE" != / ] && [ "$LAB_STATE" != "$HOME" ] || lab_die 'Unsafe state directory.'
  mkdir -p "$(dirname "$LAB_STATE")" || lab_die 'Cannot create launcher state parent.'
  lab_directory "$LAB_STATE"; lab_directory "$LAB_STATE/modules"; lab_directory "$LAB_STATE/.tmp"
}
lab_lock() {
  local previous
  if [ -e "$LAB_STATE/active" ]; then
    lab_path "$LAB_STATE/active" && lab_file "$LAB_STATE/active/pid" || lab_die 'Unknown launcher lease; preserved.'
    previous=$(<"$LAB_STATE/active/pid")
    printf '%s\n' "$previous" | grep -Eq '^[1-9][0-9]*$' || lab_die 'Invalid launcher lease.'
    kill -0 "$previous" 2>/dev/null && lab_die 'Another launcher is preparing its helpers.'
    rm "$LAB_STATE/active/pid" && rmdir "$LAB_STATE/active" || lab_die 'Unexpected lease contents; preserved.'
  fi
  mkdir -m 700 "$LAB_STATE/active" || lab_die 'Cannot acquire launcher lease.'
  printf '%s\n' "$$" > "$LAB_STATE/active/pid"; LAB_LOCKED=yes
}
lab_last() {
  local last=
  if [ -e "$LAB_STATE/last-route" ] || [ -L "$LAB_STATE/last-route" ]; then
    lab_file "$LAB_STATE/last-route" || lab_die 'Unsafe saved choice; preserved.'
    last=$(<"$LAB_STATE/last-route")
    case "$last" in A|B|C:factory|C:simulator) ;; *) lab_die 'Invalid saved route; preserved.' ;; esac
  fi
  printf '%s' "$last"
}
lab_route() {
  case "$1" in A|a|1) printf A ;; B|b|2) printf B ;; C|c|3) printf C ;; *) return 1 ;; esac
}
lab_menu() {
  local answer last
  last=$(lab_last)
  lab_say ''; lab_say 'What would you like to do?'
  lab_say '  1. Install and run the demo'
  lab_say '  2. Build the demo and installer'
  lab_say '  3. Prepare Factory or simulator build tools'
  [ -z "$last" ] || lab_say "Last choice: $last. Press Return to resume that route."
  printf 'Your choice: ' >&2
  IFS= read -r answer || lab_die 'Input ended; no action started.'
  [ -n "$answer" ] || answer=${last%%:*}
  LAB_ROUTE=$(lab_route "$answer") || lab_die 'Choose 1, 2 or 3.'
  if [ "$LAB_ROUTE" = C ] && [ -z "$LAB_COMPONENT" ] && [ "$last" = "C:${last#C:}" ]; then
    LAB_COMPONENT=${last#C:}
  fi
}
lab_component() {
  local answer
  if [ -z "$LAB_COMPONENT" ]; then
    lab_say '  1. Factory — ARM64 controller image'; lab_say '  2. CARLA / Unreal — simulation engine'
    printf 'Your choice: ' >&2; IFS= read -r answer || lab_die 'Input ended; no action started.'
    case "$answer" in 1|factory) LAB_COMPONENT=factory ;; 2|simulator) LAB_COMPONENT=simulator ;; *) lab_die 'Choose Factory or simulator.' ;; esac
  fi
}
lab_fetch() {
  local role=$1 blob digest size target work actual result
  read -r blob digest size <<< "$(lab_spec "$role")"
  printf '%s %s %s\n' "$blob" "$digest" "$size" | grep -Eq '^[a-f0-9]{40} [a-f0-9]{64} [1-9][0-9]*$' || lab_die 'Invalid compiled helper pin.'
  target="$LAB_STATE/modules/$role-$digest"
  if [ -e "$target" ]; then
    lab_file "$target" && [ "$(stat -f %z "$target")" = "$size" ] &&
      [ "$(shasum -a 256 "$target" | awk '{print $1}')" = "$digest" ] || lab_die 'Changed helper cache; preserved, not executed.'
  else
    [ "$LAB_MODE" != check ] || { lab_say "Local check unavailable: verified $role helper is not cached. Run normally once to obtain it." >&2; return 2; }
    work=$(mktemp -d "$LAB_STATE/.tmp/fetch.XXXXXX") || lab_die 'Cannot create owned helper scratch.'
    LAB_FETCH_TMP=$work
    lab_say "Preparing $role helper…" >&2
    # Immutable public blob locator; SHA-256 is the independent execution guard.
    set -m
    curl --disable --fail --proto '=https' --tlsv1.2 --connect-timeout 15 --max-time 120 \
      --max-filesize "$size" --silent --show-error -H 'Accept: application/vnd.github.raw+json' \
      --output "$work/body" "https://api.github.com/repos/alexmaninblack/aosedge-sdv-demo/git/blobs/$blob" & LAB_FETCH_PID=$!
    set +m
    wait "$LAB_FETCH_PID"; result=$?; LAB_FETCH_PID=
    [ "$result" = 0 ] ||
      { rm -f "$work/body"; rmdir "$work"; LAB_FETCH_TMP=; lab_die 'Helper download stopped. No login or retry was started.'; }
    actual=$(shasum -a 256 "$work/body" | awk '{print $1}')
    [ "$(stat -f %z "$work/body")" = "$size" ] && [ "$actual" = "$digest" ] ||
      { rm -f "$work/body"; rmdir "$work"; LAB_FETCH_TMP=; lab_die 'Helper checksum or size differs; nothing executed.'; }
    chmod 600 "$work/body" && mv "$work/body" "$target" && rmdir "$work" || lab_die 'Cannot promote verified helper.'
    LAB_FETCH_TMP=
  fi
  LAB_FETCHED=$target
}
lab_cleanup() {
  local grace=0
  if [ -n "${LAB_ROUTE_PID:-}" ]; then
    kill -TERM "$LAB_ROUTE_PID" 2>/dev/null
    while kill -0 "$LAB_ROUTE_PID" 2>/dev/null && [ "$grace" -lt 20 ]; do sleep 1; grace=$((grace+1)); done
    if kill -0 "$LAB_ROUTE_PID" 2>/dev/null; then
      lab_say 'Route cancellation did not settle; stopping the exact delegate. Preserve its diagnostics and reconcile before another run.' >&2
      kill -KILL "$LAB_ROUTE_PID" 2>/dev/null
    fi
    wait "$LAB_ROUTE_PID" 2>/dev/null; LAB_ROUTE_PID=
  fi
  if [ -n "${LAB_FETCH_PID:-}" ]; then
    disown "$LAB_FETCH_PID" 2>/dev/null
    kill -TERM -- "-$LAB_FETCH_PID" 2>/dev/null
    wait "$LAB_FETCH_PID" 2>/dev/null; LAB_FETCH_PID=
  fi
  # Only this operation's newly created, private, exact scratch child.
  if [ -n "${LAB_FETCH_TMP:-}" ] && lab_path "$LAB_FETCH_TMP"; then
    case "$LAB_FETCH_TMP" in "$LAB_STATE/.tmp/"fetch.*) rm -f "$LAB_FETCH_TMP/body"; rmdir "$LAB_FETCH_TMP" ;; esac
  fi
  LAB_FETCH_TMP=
  if [ "${LAB_LOCKED:-no}" = yes ] && lab_file "$LAB_STATE/active/pid" && [ "$(<"$LAB_STATE/active/pid")" = "$$" ]; then
    rm "$LAB_STATE/active/pid" && rmdir "$LAB_STATE/active"
  fi
  LAB_LOCKED=no
}
lab_execute() {
  local module=$1 result
  shift
  # No new process group: interactive input stays in the foreground terminal.
  # Each existing route owns/cleans its own tool process groups.
  exec 3<&0
  /bin/bash "$module" "$@" <&3 3<&- & LAB_ROUTE_PID=$!
  exec 3<&-
  wait "$LAB_ROUTE_PID"; result=$?; LAB_ROUTE_PID=
  return "$result"
}
lab_dispatch() {
  local module selected extra=()
  lab_fetch developer || return $?; export SDV_LAB_HELPER=$LAB_FETCHED
  if [ "$LAB_ROUTE" = B ]; then
    module=$SDV_LAB_HELPER
    [ "$LAB_PREPARE_ONLY" != yes ] || extra+=(--prepare-only)
  else
    lab_fetch catalog || return $?; export SDV_LAB_CATALOG=$LAB_FETCHED
    lab_fetch common || return $?; export SDV_LAB_COMMON=$LAB_FETCHED
    if [ "$LAB_ROUTE" = A ]; then
      lab_fetch drive-parser || return $?; export SDV_LAB_DRIVE_PARSER=$LAB_FETCHED
      lab_fetch install || return $?; module=$LAB_FETCHED
      [ -z "$LAB_DMG" ] || extra+=(--dmg "$LAB_DMG")
    else
      lab_fetch heavy || return $?; module=$LAB_FETCHED; extra+=(--component "$LAB_COMPONENT")
    fi
    export SDV_LAB_STATE="$LAB_STATE"
  fi
  [ -z "$LAB_PARENT" ] || extra+=(--parent "$LAB_PARENT")
  [ -z "$LAB_XCODE" ] || extra+=(--xcode "$LAB_XCODE")
  [ "$LAB_MODE" != check ] || extra+=(--check)
  if [ "$LAB_MODE" != check ]; then
    selected=$LAB_ROUTE; [ "$LAB_ROUTE" != C ] || selected="C:$LAB_COMPONENT"
    [ ! -e "$LAB_STATE/last-route.new" ] && [ ! -L "$LAB_STATE/last-route.new" ] || lab_die 'Unexpected saved-choice temporary file; preserved.'
    printf '%s\n' "$selected" > "$LAB_STATE/last-route.new"
    chmod 600 "$LAB_STATE/last-route.new" && mv "$LAB_STATE/last-route.new" "$LAB_STATE/last-route" || lab_die 'Cannot save choice.'
  fi
  # Hold the launcher lease through execution, not only helper acquisition.
  lab_execute "$module" "${extra[@]}"
}
lab_main() {
  local arg
  LAB_ROUTE= LAB_COMPONENT= LAB_DMG= LAB_PARENT= LAB_XCODE= LAB_FETCH_TMP= LAB_FETCH_PID= LAB_ROUTE_PID=
  LAB_LOCKED=no
  LAB_MODE=run LAB_PREPARE_ONLY=no
  LAB_STATE="$HOME/Library/Application Support/AosEdge SDV Lab/Launcher"
  while [ "$#" -gt 0 ]; do
    arg=$1; shift
    case "$arg" in
      --help|-h) lab_help; return 0 ;;
      --check|--plan) [ "$LAB_MODE" = run ] || lab_die 'Choose only one check/plan mode.'; LAB_MODE=${arg#--} ;;
      --prepare-only) LAB_PREPARE_ONLY=yes ;;
      --route|--component|--dmg|--parent|--xcode|--state-dir)
        [ "$#" -gt 0 ] || lab_die "$arg needs a value."
        case "$arg" in
          --route) LAB_ROUTE=$(lab_route "$1") || lab_die 'Unknown route.' ;;
          --component) LAB_COMPONENT=$1 ;; --dmg) LAB_DMG=$1 ;; --parent) LAB_PARENT=$1 ;;
          --xcode) LAB_XCODE=$1 ;; --state-dir) LAB_STATE=$1 ;;
        esac; shift ;;
      *) lab_die "Unknown option: $arg" ;;
    esac
  done
  lab_path "$LAB_STATE" && [ "$LAB_STATE" != / ] && [ "$LAB_STATE" != "$HOME" ] || lab_die 'Unsafe state directory.'
  [ -n "$LAB_ROUTE" ] || lab_menu
  [ "$LAB_ROUTE" != C ] || lab_component
  [ -z "$LAB_COMPONENT" ] || { [ "$LAB_ROUTE" = C ] && { [ "$LAB_COMPONENT" = factory ] || [ "$LAB_COMPONENT" = simulator ]; }; } || lab_die '--component belongs to C.'
  [ -z "$LAB_DMG" ] || [ "$LAB_ROUTE" = A ] || lab_die '--dmg belongs to A.'
  [ -z "$LAB_XCODE" ] || [ "$LAB_ROUTE" != A ] || lab_die 'A does not need Xcode.'
  [ "$LAB_PREPARE_ONLY" != yes ] || [ "$LAB_ROUTE" = B ] || lab_die '--prepare-only belongs to B.'
  lab_say "AosEdge SDV Lab launcher v$SDV_LAB_VERSION — route $LAB_ROUTE ${LAB_COMPONENT:-}"
  if [ "$LAB_MODE" = plan ]; then
    case "$LAB_ROUTE" in
      A) lab_say 'Approved DMG verification → signed Setup; no compiler, source checkout or Cloud action in this script.' ;;
      B) lab_say 'Existing developer preparation → pinned sources/inputs → engineering DMG; no installation or publication.' ;;
      C) lab_say "Prepare $LAB_COMPONENT host tools only. Fresh Builder/source/assets and full-source qualification remain separate." ;;
    esac; return 0
  fi
  [ "$(uname -s)" = Darwin ] && [ "$(uname -m)" = arm64 ] && [ "$(id -u)" != 0 ] || lab_die 'Use a native Apple Silicon Terminal as your ordinary user.'
  trap lab_cleanup EXIT; trap 'exit 130' INT; trap 'exit 143' TERM
  if [ "$LAB_MODE" != check ]; then
    lab_state; lab_lock
  fi
  lab_dispatch
}
if [ "${BASH_SOURCE[0]}" = "$0" ]; then lab_main "$@"; fi
