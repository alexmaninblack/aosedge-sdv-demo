#!/bin/bash
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

# BEGIN VERIFIED DEPENDENCY PINS — maintained by scripts/sync-launcher-pins
HEAVY_COMMON_SHA256=dc46cb50707edd8399e3aa180a05bba0563e1ea4f08c08826b959dc42feff13f
# END VERIFIED DEPENDENCY PINS

heavy_import() {
  [ -f "${SDV_LAB_COMMON:-}" ] && [ ! -L "$SDV_LAB_COMMON" ] &&
    [ "$(shasum -a 256 "$SDV_LAB_COMMON" | awk '{print $1}')" = "$HEAVY_COMMON_SHA256" ] ||
    { printf 'STOP: Verified common helper missing or changed.\n' >&2; return 1; }
  source "$SDV_LAB_COMMON"; route_import
}
heavy_qemu() {
  local candidate actual wanted=$(route_field specialist.factory.qemuVersion)
  SDV_QEMU= SDV_QEMU_IMG=
  for candidate in "$(command -v qemu-system-aarch64)" /opt/homebrew/bin/qemu-system-aarch64; do
    [ -x "$candidate" ] || continue
    actual=$("$candidate" --version 2>/dev/null | awk 'NR==1 && $1=="QEMU" && $2=="emulator" && $3=="version" {print $4}')
    if [ "$actual" = "$wanted" ] && file -b "$candidate" | grep -q arm64 && [ -x "$(dirname "$candidate")/qemu-img" ]; then
      SDV_QEMU=$candidate; SDV_QEMU_IMG="$(dirname "$candidate")/qemu-img"; break
    fi
  done
  [ -n "$SDV_QEMU" ] && [ -f /opt/homebrew/share/qemu/edk2-aarch64-code.fd ] &&
    [ "$(shasum -a 256 /opt/homebrew/share/qemu/edk2-aarch64-code.fd | awk '{print $1}')" = "$(route_field specialist.factory.firmwareSha256)" ]
}
heavy_ninja() {
  local candidate
  SDV_NINJA=
  for candidate in "$(command -v ninja)" /opt/homebrew/bin/ninja; do
    if [ -x "$candidate" ] && "$candidate" --version 2>/dev/null | grep -Eq '^[0-9]+\.[0-9]+(\.[0-9]+)?$'; then SDV_NINJA=$candidate; break; fi
  done
  [ -n "$SDV_NINJA" ]
}
heavy_discover() {
  # Reuse validators, but never probe Node, Docker, signing or input accounts.
  local candidate
  BREW= SDV_CMAKE= BASE_PYTHON= XCODE_OK=no PYTHON_OK=no
  [ ! -x /opt/homebrew/bin/brew ] || BREW=/opt/homebrew/bin/brew
  if [ -d "$DEVELOPER_DIR" ] && xcodebuild -checkFirstLaunchStatus >/dev/null 2>&1 &&
    xcrun --sdk macosx --show-sdk-path >/dev/null 2>&1 &&
    version_at_least "$(xcrun --sdk macosx --show-sdk-version 2>/dev/null)" "$SDV_MACOS_MIN.0" &&
    xcrun swift --version >/dev/null 2>&1 && xcrun git --version >/dev/null 2>&1; then XCODE_OK=yes; fi
  for candidate in "$(command -v cmake)" /opt/homebrew/bin/cmake; do
    if cmake_ok "$candidate"; then SDV_CMAKE=$candidate; break; fi
  done
  for candidate in "$(command -v python3.12)" /opt/homebrew/opt/python@3.12/bin/python3.12; do
    if python_ok "$candidate"; then BASE_PYTHON=$candidate; break; fi
  done
  python_ok "$SDV_PYTHON" && "$SDV_PYTHON" -I -B -c 'import packaging' >/dev/null 2>&1 && PYTHON_OK=yes
  return 0
}
heavy_parent() {
  local parent=$1 selection="$SDV_LAB_STATE/Heavy-$2/selections.tsv" previous= previous_uuid=
  if [ -e "$selection" ] || [ -L "$selection" ]; then
    private_file "$selection" || die 'Unsafe specialist selection; preserved.'
    previous=$(awk -F '\t' '$1=="parent" {print $2}' "$selection")
    previous_uuid=$(awk -F '\t' '$1=="volume" {print $2}' "$selection")
    safe_path "$previous" && [ -n "$previous_uuid" ] || die 'Invalid specialist selection.'
  fi
  if [ -z "$parent" ]; then
    if [ -n "$previous" ]; then parent=$previous; say "Previously selected workspace: $parent";
    else parent=$(ask 'Existing build workspace parent folder' "$HOME"); fi
  fi
  route_storage "$parent"
  [ "$parent" != "$previous" ] || [ "$SELECTED_UUID" = "$previous_uuid" ] || die 'A different disk replaced the saved workspace. No fallback.'
}
heavy_save_parent() {
  { [ ! -e "$STATE/selections.tsv" ] && [ ! -L "$STATE/selections.tsv" ]; } || private_file "$STATE/selections.tsv" || die 'Unsafe specialist selection; preserved.'
  printf 'parent\t%s\nvolume\t%s\n' "$SDV_PARENT" "$SELECTED_UUID" > "$ROUTE_WORK/selections.tsv"
  mv "$ROUTE_WORK/selections.tsv" "$STATE/selections.tsv" || die 'Cannot save specialist workspace.'
}
heavy_install_qemu() {
  local advertised
  need_brew
  "$BREW" info --json=v2 qemu > "$ROUTE_WORK/qemu.json" || die 'Cannot inspect the QEMU bottle.'
  advertised=$(/usr/bin/plutil -extract formulae.0.versions.stable raw -o - "$ROUTE_WORK/qemu.json")
  [ "$advertised" = "$(route_field specialist.factory.qemuVersion)" ] || die 'Homebrew QEMU does not match the pinned Builder version. No alternate version installed; obtain the reviewed compatible tool.'
  install_formula qemu
  heavy_qemu || die 'QEMU/native firmware does not match the existing Builder recipe; full-source remains blocked.'
}
heavy_main() {
  local arg component= component_label= mode=run parent= xcode= confirm missing=no
  while [ "$#" -gt 0 ]; do
    arg=$1; shift
    case "$arg" in
      --check) mode=check ;;
      --component|--parent|--xcode) [ "$#" -gt 0 ] || { printf 'STOP: Missing argument.\n' >&2; return 1; }
        case "$arg" in --component) component=$1 ;; --parent) parent=$1 ;; --xcode) xcode=$1 ;; esac; shift ;;
      *) printf 'STOP: Unknown specialist option.\n' >&2; return 1 ;;
    esac
  done
  case "$component" in
    factory) component_label='ARM64 virtual controller image (Factory)' ;;
    simulator) component_label='Vehicle simulator (CARLA / Unreal)' ;;
    *) printf 'STOP: Select the controller image (--component factory) or vehicle simulator (--component simulator).\n' >&2; return 1 ;;
  esac
  heavy_import || return $?; route_host
  heavy_parent "$parent" "$component"
  SDV_PYTHON="$SDV_ROOT/tools/python/bin/python3.12"
  DEVELOPER_DIR=${xcode:-$(xcode-select -p 2>/dev/null)}
  case "$DEVELOPER_DIR" in *.app) DEVELOPER_DIR="$DEVELOPER_DIR/Contents/Developer" ;; esac
  export DEVELOPER_DIR; PRIVATE_INPUTS=no
  [ "$component" != simulator ] || SDV_CMAKE_MIN=$(route_field specialist.simulator.cmakeMin)
  heavy_discover
  say "Specialist route: $component_label — host tools only, no build or VM boot."
  say 'No Cloud access, Node, Docker or signing key is required by this preparation.'
  if [ "$component" = simulator ]; then
    [ "$XCODE_OK" = yes ] || { say 'ACTION: Install/open compatible Xcode and finish its license/components, then rerun. No global selection changed.'; return 2; }
    heavy_ninja || missing=yes
  else
    heavy_qemu || missing=yes
    say 'The Builder is a separate ARM64 Linux build VM, not the demo controller.'
    say "The controller-image Builder also requires $(route_field specialist.factory.builderMemoryGiB) GiB RAM, $(route_field specialist.factory.builderInitialHostFreeGiB) GiB initial host space and $(route_field specialist.factory.builderGuestFreeGiB) GiB free in the guest. These are not tool-installation checks."
  fi
  [ -n "$SDV_CMAKE" ] && [ "$PYTHON_OK" = yes ] || missing=yes
  if [ "$mode" = check ]; then
    [ "$missing" != yes ] || { say 'LOCAL TOOLS INCOMPLETE — run this route normally to prepare missing compatible tools.'; return 2; }
    say 'HOST TOOLS OBSERVED — full-source inputs/build capacity not verified.'; return 0
  fi
  say "Plan: reuse compatible Python/CMake and prepare missing host tools for $component_label on the selected workspace."
  say 'Xcode/Homebrew use normal host locations and may require system prompts; caches/scratch stay on the chosen disk.'
  confirm=$(ask 'Prepare these host tools? (yes/no)' no)
  [ "$confirm" = yes ] || { say 'Cancelled. No tools installed.'; return 2; }
  route_context "Heavy-$component"
  heavy_save_parent
  prepare_python_cmake
  if [ "$component" = simulator ]; then
    if ! heavy_ninja; then install_formula ninja; heavy_ninja || die 'Ninja version check failed.'; fi
  else
    heavy_qemu || heavy_install_qemu
  fi
  route_recheck
  say ''; say 'HOST TOOLS PREPARED — FULL SOURCE NOT READY.'
  if [ "$component" = factory ]; then
    say 'Remaining: exact ARM64 Linux Builder/base, guest tool/cache preparation and controller-image (Factory) owner gates.'
  else
    say 'Remaining: licensed Unreal access, pinned CARLA/Unreal source/assets and a closed macOS build recipe.'
  fi
  say 'No Builder or simulator was started. No controller image, simulator or DMG was built.'
  say 'Specialist procedure: docs/getting-started/full-source-build.md'
  return 2
}
if [ "${BASH_SOURCE[0]}" = "$0" ]; then heavy_main "$@"; fi
