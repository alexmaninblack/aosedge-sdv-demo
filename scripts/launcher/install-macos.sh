#!/bin/bash
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

# BEGIN VERIFIED DEPENDENCY PINS — maintained by scripts/sync-launcher-pins
INSTALL_COMMON_SHA256=ff1c3e2472fb6314dc5d27cace39d961467248364fae09c2d529cfb13e814e02
INSTALL_DRIVE_SHA256=b43c73e9e4256bae5bdd045bd0769f0e083298d75866bc13f5540fd8acb24bd3
# END VERIFIED DEPENDENCY PINS

install_import() {
  [ -f "${SDV_LAB_COMMON:-}" ] && [ ! -L "$SDV_LAB_COMMON" ] &&
    [ "$(shasum -a 256 "$SDV_LAB_COMMON" | awk '{print $1}')" = "$INSTALL_COMMON_SHA256" ] ||
    { printf 'STOP: Verified common helper missing or changed.\n' >&2; return 1; }
  source "$SDV_LAB_COMMON"; route_import
}
install_docker() {
  local candidate docker= endpoint observed
  for candidate in "$(command -v docker)" /Applications/Docker.app/Contents/Resources/bin/docker "$HOME/.docker/bin/docker"; do
    [ ! -x "$candidate" ] || { docker=$candidate; break; }
  done
  [ -n "$docker" ] || { say 'ACTION: Install Docker Desktop for Apple Silicon and complete first-run setup.'; say 'https://docs.docker.com/desktop/setup/install/mac-install/'; return 2; }
  # Alarm bounds a read-only CLI probe without Python or a new dependency.
  endpoint=$(/usr/bin/perl -e 'alarm 20; exec @ARGV' "$docker" context inspect desktop-linux --format '{{.Endpoints.docker.Host}}' 2>/dev/null) || { say 'ACTION: Finish Docker first-run setup; no restart attempted.'; return 2; }
  case "$endpoint" in unix:///*) ;; *) say 'STOP: A local Docker Engine is required; no remote context was used.'; return 2 ;; esac
  observed=$(/usr/bin/perl -e 'alarm 20; exec @ARGV' "$docker" --context desktop-linux info --format '{{.OSType}}/{{.Architecture}}' 2>/dev/null) || { say 'ACTION: Start the existing Docker Engine; do not restart a running one.'; return 2; }
  case "$observed" in linux/arm64|linux/aarch64) say 'Docker: existing local ARM64 Engine ready.' ;; *) say 'STOP: Docker must run Linux ARM64 containers.'; return 2 ;; esac
}
install_partial() {
  local destination=$1 size=$2 binding identity receipt="$1.part.receipt"
  safe_path "$destination" && safe_path "$receipt" || { say 'STOP: Unsafe download path; preserved.' >&2; return 1; }
  binding=$(printf '%s\n' "$destination" "$size" "$(route_field operator.sha256)" \
    "${SELECTED_UUID:-}" "$(route_field operator.downloadURL)" | shasum -a 256 | awk '{print $1}') || return 1
  if [ ! -e "$destination.part" ] && [ ! -L "$destination.part" ]; then
    [ ! -e "$receipt" ] && [ ! -L "$receipt" ] || { say 'STOP: Partial-download receipt has no payload; preserved for inspection.' >&2; return 1; }
    (umask 077; set -C; : > "$destination.part") || return 1
    identity=$(stat -f '%d:%i' "$destination.part") || return 1
    (umask 077; set -C; printf 'sdv-dmg-part-v1\t%s\t%s\n' "$binding" "$identity" > "$receipt") || return 1
  fi
  private_file "$destination.part" && private_file "$receipt" && [ "$(stat -f %z "$receipt")" -le 512 ] &&
    [ "$(wc -l < "$receipt" | tr -d ' ')" = 1 ] || { say 'STOP: Unowned or unsafe partial download; preserved.' >&2; return 1; }
  identity=$(stat -f '%d:%i' "$destination.part") || return 1
  [ "$(<"$receipt")" = "$(printf 'sdv-dmg-part-v1\t%s\t%s' "$binding" "$identity")" ] || {
    say 'STOP: Partial download belongs to another package, file or volume; preserved.' >&2; return 1;
  }
  INSTALL_PART_BYTES=$(stat -f %z "$destination.part") || return 1
  [ "$INSTALL_PART_BYTES" -le "$size" ] || { say 'STOP: Partial download exceeds the approved size; preserved.' >&2; return 1; }
  INSTALL_PART_ID=$identity
}
install_rollback_append() {
  # Remove only this request's untrusted suffix, through an exact private fd.
  /usr/bin/perl -MFcntl=O_WRONLY,O_NOFOLLOW -e '
    my ($path,$id,$offset)=@ARGV;
    sysopen(my $f,$path,O_WRONLY|O_NOFOLLOW) or die "Cannot reconcile partial download.\n";
    my @s=stat($f); die "Partial identity changed.\n" unless -f $f && $s[4]==$< &&
      $s[3]==1 && ($s[2]&0777)==0600 && "$s[0]:$s[1]" eq $id && $s[7]>=$offset;
    truncate($f,$offset) or die "Cannot preserve previous prefix.\n";
  ' "$1" "$2" "$3"
}
install_promote_partial() {
  local destination=$1
  [ ! -e "$destination" ] && [ ! -L "$destination" ] || { say 'STOP: Completed destination appeared; both files preserved.' >&2; return 1; }
  mv -n "$destination.part" "$destination" && [ ! -e "$destination.part" ] &&
    private_file "$destination" && [ "$(stat -f '%d:%i' "$destination")" = "$INSTALL_PART_ID" ] || return 1
  rm "$destination.part.receipt"
}
install_public_download() {
  local url=$1 destination=$2 mode next round=0 parser=${SDV_LAB_DRIVE_PARSER:-} size offset result actual status
  local resume=() progress=(--silent --show-error)
  size=$(route_field operator.bytes) || return 1
  safe_path "$parser" && [ -f "$parser" ] &&
    [ "$(shasum -a 256 "$parser" | awk '{print $1}')" = "$INSTALL_DRIVE_SHA256" ] || return 1
  install_partial "$destination" "$size" || return 1
  offset=$INSTALL_PART_BYTES
  if [ "$offset" = "$size" ]; then
    install_promote_partial "$destination"; return $?
  fi
  while [ "$round" -lt 5 ]; do
    round=$((round+1))
    curl --disable --fail --proto '=https' --tlsv1.2 --connect-timeout 15 --max-time 30 \
      --silent --show-error --head --output "$ROUTE_WORK/drive-head" "$url" || return 1
    /usr/bin/perl "$parser" headers "$ROUTE_WORK/drive-head" "$url" "$size" > "$ROUTE_WORK/drive-next" || return 1
    IFS=$'\t' read -r mode next < "$ROUTE_WORK/drive-next" || return 1
    case "$mode" in
      redirect) url=$next ;;
      html)
        curl --disable --fail --proto '=https' --tlsv1.2 --connect-timeout 15 --max-time 30 \
          --silent --show-error --max-filesize 65536 --output "$ROUTE_WORK/drive-form" "$url" || return 1
        /usr/bin/perl "$parser" form "$ROUTE_WORK/drive-form" "$url" > "$ROUTE_WORK/drive-next" || return 1
        IFS=$'\t' read -r mode next < "$ROUTE_WORK/drive-next" || return 1
        [ "$mode" = confirm ] || return 1; url=$next ;;
      binary)
        [ "$offset" = 0 ] || resume=(--continue-at "$offset")
        if [ -t 9 ] && [ "${TERM:-}" != dumb ]; then
          printf '  %s\n' "${destination##*/}" >&9
          progress=(--progress-bar --show-error)
        fi
        # No total deadline: a slow but advancing download may take hours.
        # curl owns range-start checks; the parser additionally binds total/end.
        curl --disable --fail --proto '=https' --tlsv1.2 --connect-timeout 15 --speed-limit 1 --speed-time 90 \
          --dump-header "$ROUTE_WORK/drive-get-head" --max-filesize "$size" "${resume[@]}" \
          "${progress[@]}" --output "$destination.part" "$url" 2>&9
        result=$?
        status=unsupported
        if ! /usr/bin/perl "$parser" transfer-headers "$ROUTE_WORK/drive-get-head" "$url" "$size" "$offset" > "$ROUTE_WORK/drive-next"; then
          if [ "$offset" = 0 ] && [ "$(stat -f %z "$destination.part")" -le 65536 ]; then
            status=$(/usr/bin/perl "$parser" payload-status "$destination.part" "$url") || status=unsupported
          fi
          install_rollback_append "$destination.part" "$INSTALL_PART_ID" "$offset" || return 1
          if [ "$status" = quota ]; then
            printf 'STOP: The artifact provider blocks this anonymous download (quota exceeded). No installer was opened. Wait for provider availability; no automatic retry.\n' >&2
          else printf 'STOP: Download response/range was not confirmed. The previous prefix is preserved; no installer opened or automatic retry.\n' >&2; fi
          return 2
        fi
        private_file "$destination.part" && [ "$(stat -f '%d:%i' "$destination.part")" = "$INSTALL_PART_ID" ] || return 1
        actual=$(stat -f %z "$destination.part") || return 1
        if [ "$actual" -gt "$size" ]; then
          install_rollback_append "$destination.part" "$INSTALL_PART_ID" "$offset" || return 1
          say 'STOP: Transfer exceeded the approved total size; previous prefix preserved.' >&2; return 2
        fi
        install_partial "$destination" "$size" || return 1
        actual=$INSTALL_PART_BYTES
        [ "$actual" -ge "$offset" ] || return 1
        if [ "$actual" != "$size" ]; then
          printf 'Download paused at %s of %s bytes (transport exit %s). Rerun the same launcher to resume.\n' "$actual" "$size" "$result" >&2
          return 2
        fi
        # This is still unverified media. The full SHA-256 gate runs next.
        install_promote_partial "$destination"; return $? ;;
      *) return 1 ;;
    esac
  done
  return 1
}
install_verify_dmg() {
  local file=$1 size=$2 expected=$3 before after
  safe_path "$file" && [ -f "$file" ] && [ "$(stat -f %z "$file")" = "$size" ] || die 'DMG path or size differs from the selected approved package.'
  before=$(stat -f '%d:%i:%z:%.9Fm:%.9Fc:%.9FB' "$file")
  if private_file "$STATE/verified-dmg" && [ "$(<"$STATE/verified-dmg")" = "$expected $before $file" ]; then
    say 'DMG: reusing unchanged consumer verification.'
  else
    run_install 'Verifying the complete DMG checksum' /bin/bash -c 'shasum -a 256 "$1" | awk '\''{print $1}'\'' > "$2"' _ "$file" "$ROUTE_WORK/digest"
    [ "$(<"$ROUTE_WORK/digest")" = "$expected" ] || die 'DMG checksum differs. The file is preserved and not opened.'
  fi
  after=$(stat -f '%d:%i:%z:%.9Fm:%.9Fc:%.9FB' "$file")
  [ "$before" = "$after" ] || die 'DMG changed during verification; not opened.'
  { [ ! -e "$STATE/verified-dmg" ] && [ ! -L "$STATE/verified-dmg" ]; } || private_file "$STATE/verified-dmg" || die 'Unsafe verification receipt; preserved.'
  printf '%s\n' "$expected $after $file" > "$ROUTE_WORK/verified-dmg"
  mv "$ROUTE_WORK/verified-dmg" "$STATE/verified-dmg" || die 'Cannot record consumer verification.'
}
install_mount() {
  local file=$1 index=0 mount= dev= path= borrowed=no
  hdiutil info -plist > "$ROUTE_WORK/before-mount.plist" || die 'Cannot inspect existing media; no attachment started.'
  while /usr/bin/plutil -extract "images.$index" xml1 -o - "$ROUTE_WORK/before-mount.plist" >/dev/null 2>&1; do
    path=$(/usr/bin/plutil -extract "images.$index.image-path" raw -o - "$ROUTE_WORK/before-mount.plist" 2>/dev/null)
    [ "$path" != "$file" ] || borrowed=yes
    index=$((index+1)); [ "$index" -lt 128 ] || die 'Too many existing media objects; no attachment started.'
  done
  index=0
  hdiutil attach -readonly -nobrowse -plist "$file" > "$ROUTE_WORK/mount.plist" || die 'DMG mount failed; no retry.'
  while /usr/bin/plutil -extract "system-entities.$index" xml1 -o - "$ROUTE_WORK/mount.plist" >/dev/null 2>&1; do
    mount=$(/usr/bin/plutil -extract "system-entities.$index.mount-point" raw -o - "$ROUTE_WORK/mount.plist" 2>/dev/null)
    dev=$(/usr/bin/plutil -extract "system-entities.$index.dev-entry" raw -o - "$ROUTE_WORK/mount.plist" 2>/dev/null)
    if [ -n "$mount" ]; then
      [ -z "$ROUTE_MEDIA" ] || die 'Ambiguous DMG mounts; retain evidence.'
      ROUTE_MEDIA=$dev; INSTALL_MOUNT=$mount
    fi
    index=$((index+1)); [ "$index" -lt 16 ] || die 'Unexpected DMG entity count.'
  done
  case "$ROUTE_MEDIA" in /dev/disk*) ;; *) die 'Cannot identify the mounted installer.' ;; esac
  [ "$borrowed" = yes ] || ROUTE_MEDIA_NEW=yes
}
install_setup() {
  local app="$INSTALL_MOUNT/$(route_field operator.setupBundle)" details pin
  [ -d "$app" ] && [ ! -L "$app" ] && [ -d "$INSTALL_MOUNT/$(route_field operator.kitDirectory)" ] || die 'Complete Setup/Runtime Kit pair missing.'
  /usr/bin/codesign --verify --deep --strict "$app" >/dev/null 2>&1 || die 'Setup signature verification failed.'
  details=$(/usr/bin/codesign -dvv "$app" 2>&1) || die 'Cannot inspect Setup signature.'
  printf '%s\n' "$details" | grep -Fx "Identifier=$(route_field operator.setupIdentifier)" >/dev/null &&
    printf '%s\n' "$details" | grep -Fx "TeamIdentifier=$(route_field operator.setupTeam)" >/dev/null &&
    ! printf '%s\n' "$details" | grep -F 'Signature=adhoc' >/dev/null || die 'Setup identity differs.'
  pin=$(/usr/bin/plutil -extract manifestSha256 raw -o - "$app/Contents/Resources/tooling/scripts/distribution/setup_release.json") || die 'Setup release pin missing.'
  [ "$pin" = "$(route_field operator.manifestSha256)" ] || die 'Setup and selected DMG release differ.'
  /usr/bin/open "$app" || die 'macOS did not open Setup. Retain the security message; do not bypass Gatekeeper.'
  ROUTE_HANDOFF=yes
  say ''; say 'SETUP HANDOFF REQUESTED — installation continues in the signed app; not yet verified installed.'
  say 'In Setup: Continue installation → Cloud access → Open SDV Lab.'
  say 'Keep this DMG mounted until Setup quits, then eject it in Finder.'
  say 'This script does not create a Controller, provision a Unit or publish a release.'
}
install_main() {
  local arg mode=run file= parent= url name size digest confirm saved record kind volume recorded_size recorded_digest recorded_parent recorded_file extra automatic=no explicit_parent=no
  while [ "$#" -gt 0 ]; do
    arg=$1; shift
    case "$arg" in
      --check) mode=check ;;
      --dmg|--parent) [ "$#" -gt 0 ] || { printf 'STOP: Missing argument.\n' >&2; return 1; }
        case "$arg" in --dmg) file=$1 ;; --parent) parent=$1; explicit_parent=yes ;; esac; shift ;;
      *) printf 'STOP: Unknown install option.\n' >&2; return 1 ;;
    esac
  done
  install_import || return $?; route_host; install_docker || return $?
  name=$(route_field operator.file); size=$(route_field operator.bytes); digest=$(route_field operator.sha256)
  url=$(route_field operator.downloadURL)
  say "Selected package: $(route_field operator.productVersion) — $(route_field operator.status)"
  say 'No source checkout, Xcode, Python, Node or signing key is needed.'
  if [ "$mode" = check ]; then
    say 'LOCAL HOST CHECKS PASS — DMG/install/Cloud access remain unchecked.'; return 0
  fi
  saved="$SDV_LAB_STATE/Install/selected-dmg"
  record="$SDV_LAB_STATE/Install/download-selection"
  if [ -z "$file" ] && [ "$explicit_parent" = no ] && { [ -e "$saved" ] || [ -L "$saved" ]; }; then
    private_file "$saved" && [ "$(stat -f %z "$saved")" -le 4096 ] || die 'Unsafe saved DMG selection; preserved.'
    file=$(<"$saved")
    if [ -e "$record" ] || [ -L "$record" ]; then
      private_file "$record" && [ "$(stat -f %z "$record")" -le 16384 ] &&
        [ "$(wc -l < "$record" | tr -d ' ')" = 1 ] || die 'Unsafe saved download selection; preserved.'
      IFS=$'\t' read -r kind volume recorded_size recorded_digest recorded_parent recorded_file extra < "$record" || return 1
      [ "$kind" = sdv-dmg-download-v1 ] && [ -n "$volume" ] && [ -z "$extra" ] &&
        [ "$recorded_size" = "$size" ] && [ "$recorded_digest" = "$digest" ] &&
        [ "$recorded_file" = "$file" ] && [ "$file" = "$recorded_parent/sdv/cache/$name" ] || die 'Saved download selection differs from this package; preserved. Select a new parent explicitly.'
      route_storage "$recorded_parent"
      [ "$SELECTED_UUID" = "$volume" ] || die 'Saved download volume was replaced; reconnect the original disk. No fallback.'
      parent=$recorded_parent; automatic=yes
      safe_path "$file" && [ ! -L "$file" ] || die 'Unsafe saved download path; preserved.'
    else
      safe_path "$file" && [ -f "$file" ] || { say 'ACTION: Saved DMG is unavailable. Reconnect its disk, select a complete file with --dmg, or select a new download parent with --parent; no fallback.'; return 2; }
    fi
    say "Previously selected DMG: $file"
  fi
  if [ -z "$file" ] && [ -z "$url" ]; then
    say 'The approved operator DMG has no public download yet. Select the complete file supplied by the release owner.'
    file=$(/usr/bin/osascript -e 'POSIX path of (choose file with prompt "Choose the approved AosEdge SDV Lab DMG" of type {"com.apple.disk-image-udif"})') || return 2
  fi
  if [ -n "$file" ] && [ "$automatic" = no ]; then
    safe_path "$file" && [ -f "$file" ] || die 'Choose an existing absolute DMG path without links.'
    SDV_PARENT=
  elif [ "$automatic" = no ]; then
    # Locator is reviewed catalog data, never an arbitrary user executable URL.
    case "$url" in https://drive.google.com/*|https://drive.usercontent.google.com/*|https://www.dropbox.com/scl/*) ;; *) die 'Unsupported operator download locator.' ;; esac
    [ -n "$parent" ] || parent=$(ask 'Existing download workspace parent folder' "$HOME")
    route_storage "$parent"; file="$SDV_ROOT/cache/$name"
    automatic=yes
  fi
  [ "$automatic" = no ] || say "Download cache: $SDV_ROOT/cache (not the installation or private-data folder)."
  say 'Plan: verify approved DMG and Setup identity, then open its signed installer.'
  [ "$(route_field operator.notarized)" = true ] || say 'Engineering preview: not notarized. Respect any macOS security refusal.'
  confirm=$(ask 'Proceed? (yes/no)' no)
  [ "$confirm" = yes ] || { say 'Cancelled. No installer was opened.'; return 2; }
  route_context Install
  if [ "$automatic" = yes ]; then
    { [ ! -e "$record" ] && [ ! -L "$record" ]; } || private_file "$record" || die 'Unsafe download selection; preserved.'
    printf 'sdv-dmg-download-v1\t%s\t%s\t%s\t%s\t%s\n' "$SELECTED_UUID" "$size" "$digest" "$SDV_PARENT" "$file" > "$ROUTE_WORK/download-selection"
    mv "$ROUTE_WORK/download-selection" "$record" || die 'Cannot save download selection.'
  elif [ -e "$record" ] || [ -L "$record" ]; then
    private_file "$record" && rm "$record" || die 'Unsafe previous download selection; preserved.'
  fi
  { [ ! -e "$STATE/selected-dmg" ] && [ ! -L "$STATE/selected-dmg" ]; } || private_file "$STATE/selected-dmg" || die 'Unsafe saved DMG selection; preserved.'
  printf '%s\n' "$file" > "$ROUTE_WORK/selected-dmg"
  mv "$ROUTE_WORK/selected-dmg" "$STATE/selected-dmg" || die 'Cannot save DMG selection.'
  if [ ! -f "$file" ]; then
    [ ! -e "$file" ] && [ ! -L "$file" ] || die 'Existing download destination preserved.'
    install_partial "$file" "$size" || die 'Partial download requires inspection; no transfer started.'
    say "Downloading ${file##*/}: $INSTALL_PART_BYTES of $size bytes retained."
    run_install "Downloading $name" install_public_download "$url" "$file"
  fi
  install_verify_dmg "$file" "$size" "$digest"; install_mount "$file"; install_setup
}
if [ "${BASH_SOURCE[0]}" = "$0" ]; then install_main "$@"; fi
