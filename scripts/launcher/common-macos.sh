#!/bin/bash
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
# Shared host primitives, never a replacement installation/build owner.

# BEGIN VERIFIED DEPENDENCY PINS — maintained by scripts/sync-launcher-pins
ROUTE_HELPER_SHA256=9a7eabaacd7d459963b657884da000b8851e26afa1d393d4204a3f3317a7683d
ROUTE_CATALOG_SHA256=e908a2f83597de9af8c6b93bab765b4c901a8d945e14f308533e50b15b94b698
# END VERIFIED DEPENDENCY PINS

route_import() {
  local actual
  [ -f "${SDV_LAB_HELPER:-}" ] && [ ! -L "$SDV_LAB_HELPER" ] || { printf 'STOP: Verified helper missing.\n' >&2; return 1; }
  actual=$(shasum -a 256 "$SDV_LAB_HELPER" | awk '{print $1}')
  [ "$actual" = "$ROUTE_HELPER_SHA256" ] || { printf 'STOP: Helper changed.\n' >&2; return 1; }
  source "$SDV_LAB_HELPER"
  recheck_storage() { route_recheck; }
  safe_path "${SDV_LAB_CATALOG:-}" && [ -f "$SDV_LAB_CATALOG" ] &&
    [ "$(shasum -a 256 "$SDV_LAB_CATALOG" | awk '{print $1}')" = "$ROUTE_CATALOG_SHA256" ] || die 'Catalog changed.'
  [ "$(route_field schemaVersion)" = 1 ] && [ "$(route_field product)" = aosedge-sdv-lab ] || die 'Unsupported launcher catalog.'
}
route_field() { /usr/bin/plutil -extract "$1" raw -o - "$SDV_LAB_CATALOG"; }
route_host() {
  [ "$(uname -s)" = Darwin ] && [ "$(uname -m)" = arm64 ] && [ "$(id -u)" != 0 ] || die 'Use a native Apple Silicon Terminal as your ordinary user.'
  version_at_least "$(sw_vers -productVersion)" "$SDV_MACOS_MIN.0" || die "macOS $SDV_MACOS_MIN or later is required."
}
route_storage() {
  SDV_PARENT=${1%/}
  safe_path "$SDV_PARENT" && [ -n "$SDV_PARENT" ] && [ "$SDV_PARENT" != / ] || die 'Choose an existing local folder, not the filesystem root.'
  inspect_volume "$SDV_PARENT"; SELECTED_UUID=$VOLUME_UUID; check_capacity
  SDV_ROOT="$SDV_PARENT/sdv"; SDV_TMP="$SDV_ROOT/.tmp"
  safe_path "$SDV_ROOT" || die 'Unsafe workspace.'
  [ ! -e "$SDV_ROOT" ] || { [ -d "$SDV_ROOT" ] && [ "$(stat -f %u "$SDV_ROOT")" = "$(id -u)" ]; } || die 'Workspace belongs to another owner.'
}
route_recheck() {
  if [ -n "${SDV_PARENT:-}" ]; then
    inspect_volume "$SDV_PARENT"
    [ "$VOLUME_UUID" = "$SELECTED_UUID" ] || die 'Selected disk changed or disconnected; no fallback.'
    check_capacity
  fi
}
# run_install/finish_scratch call this common guard; developer main is never run.
recheck_storage() { route_recheck; }
route_context() {
  local name=$1 previous
  umask 077
  safe_path "${SDV_LAB_STATE:-}" || die 'Launcher state is missing or unsafe.'
  STATE="$SDV_LAB_STATE/$name"; owned_dir "$STATE"
  if [ -e "$STATE/active" ]; then
    safe_path "$STATE/active" && private_file "$STATE/active/pid" || die 'Unknown route lease; preserved.'
    previous=$(<"$STATE/active/pid")
    printf '%s\n' "$previous" | grep -Eq '^[1-9][0-9]*$' || die 'Invalid lease owner.'
    kill -0 "$previous" 2>/dev/null && die 'This route is already active.'
    rm "$STATE/active/pid" && rmdir "$STATE/active" || die 'Unexpected interrupted lease contents; preserved.'
  fi
  mkdir -m 700 "$STATE/active" || die 'Cannot acquire route lease.'
  printf '%s\n' "$$" > "$STATE/active/pid"; LOCKED=yes
  WORKFLOW_CHILD=no CHILD_PID= SCRATCH_OWNED=no ROUTE_MEDIA= ROUTE_MEDIA_NEW=no ROUTE_HANDOFF=no
  ROUTE_WORK=
  trap route_cleanup EXIT; trap 'exit 130' INT; trap 'exit 143' TERM
  if [ -n "${SDV_PARENT:-}" ]; then
    route_recheck
    [ -d "$SDV_ROOT" ] || mkdir -m 700 "$SDV_ROOT" || die 'Cannot create workspace.'
    owned_dir "$SDV_ROOT/.heavy-preparation"
    LOG=$(mktemp "$SDV_ROOT/.heavy-preparation/$name.XXXXXX") || die 'Cannot create diagnostic log.'
    SDV_SCRATCH_ROOT="$SDV_ROOT/.tmp"; scratch_root "$SDV_SCRATCH_ROOT"
  else
    # Small installer/verification metadata uses its private security boundary.
    SDV_SCRATCH_ROOT="$STATE/.tmp"; scratch_root "$SDV_SCRATCH_ROOT"
    LOG=$(mktemp "$STATE/run.XXXXXX") || die 'Cannot create diagnostic log.'
  fi
  ROUTE_WORK=$(mktemp -d "$SDV_SCRATCH_ROOT/route.XXXXXX") || die 'Cannot create owned scratch.'
  printf '%s\n' "$$" > "$ROUTE_WORK/.pid"
  export TMPDIR="$ROUTE_WORK" HOMEBREW_TEMP="$ROUTE_WORK"
  if [ -n "${SDV_PARENT:-}" ]; then
    mkdir -p "$SDV_ROOT/tools" "$SDV_ROOT/cache" || die 'Cannot create tool/cache directories.'
    export HOMEBREW_CACHE="$SDV_ROOT/cache/homebrew" PIP_CACHE_DIR="$SDV_ROOT/cache/pip"
  fi
  export HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_UPGRADE=1 HOMEBREW_NO_INSTALL_CLEANUP=1 HOMEBREW_NO_ANALYTICS=1
}
route_cleanup() {
  local status=$?
  stop_child; clear_activity; exec 9>&-
  if [ -n "${ROUTE_MEDIA:-}" ] && [ "${ROUTE_MEDIA_NEW:-no}" = yes ] && [ "${ROUTE_HANDOFF:-no}" != yes ]; then
    hdiutil detach "$ROUTE_MEDIA" >/dev/null 2>&1 || { say "Installer media remains mounted: $ROUTE_MEDIA" >&2; status=1; }
  fi
  if [ -n "${ROUTE_WORK:-}" ]; then
    if route_recheck && safe_path "$ROUTE_WORK" && private_file "$ROUTE_WORK/.pid" &&
      [ "$(<"$ROUTE_WORK/.pid")" = "$$" ] && bootstrap_idle "$ROUTE_WORK"; then
      case "$ROUTE_WORK" in "$SDV_SCRATCH_ROOT/"route.*) rm -rf -- "$ROUTE_WORK" || status=1 ;; *) status=1 ;; esac
    else
      say 'Owned scratch preserved because its storage/owner/handles could not be verified.' >&2; status=1
    fi
  fi
  if [ "${LOCKED:-no}" = yes ] && private_file "$STATE/active/pid" && [ "$(<"$STATE/active/pid")" = "$$" ]; then
    rm "$STATE/active/pid" && rmdir "$STATE/active" || status=1
  fi
  trap - EXIT; exit "$status"
}
