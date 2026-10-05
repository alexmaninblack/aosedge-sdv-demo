#!/bin/sh
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
# Read-only, allowlisted facts. No environment, command arguments or app logs.
set -eu
field() { printf '%s\t%s\n' "$1" "$2"; }
field arch "$(/usr/bin/uname -m)"
field model "$(/usr/sbin/sysctl -n hw.model)"
field os "$(/usr/bin/sw_vers -productVersion)"
field build "$(/usr/bin/sw_vers -buildVersion)"
field user "$(/usr/bin/id -un)"
field console "$(/usr/bin/stat -f %Su /dev/console)"
field memoryBytes "$(/usr/sbin/sysctl -n hw.memsize)"
field freeKiB "$(/bin/df -k "$HOME" | /usr/bin/awk 'NR==2 {print $4}')"
device=$(/bin/df -P "$HOME" | /usr/bin/awk 'NR==2 {print $1}')
internal=$(/usr/sbin/diskutil info -plist "$device" | /usr/bin/plutil -extract Internal raw -o - -)
field internal "$internal"
docker=0; [ ! -d /Applications/Docker.app ] || docker=1
field dockerPresent "$docker"
brew=0; [ ! -e /opt/homebrew/bin/brew ] || brew=1
field homebrewPresent "$brew"
code=0; [ ! -d /Applications/Xcode.app ] || code=1
field xcodePresent "$code"
field demoProcesses "$(/bin/ps -A -o comm= | /usr/bin/awk '
 /CarlaUnreal|UnrealEditor|qemu-system|aosedge|AosEdge|driving_control|carla_gateway/ {n++}
 END {print n+0}')"
ports=0
for port in 18080 2000 2001 2002; do
  if /usr/sbin/lsof -nP -iTCP:"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then ports=$((ports+1)); fi
done
field busyPorts "$ports"
field swapUsedMiB "$(/usr/sbin/sysctl -n vm.swapusage | /usr/bin/awk '{print $6}' | /usr/bin/sed 's/[^0-9.]//g')"
field stagingHttp "$(/usr/bin/curl --silent --output /dev/null --write-out '%{http_code}' --connect-timeout 8 --max-time 15 https://aws-stage.epmp-aos.projects.epam.com/ || true)"
