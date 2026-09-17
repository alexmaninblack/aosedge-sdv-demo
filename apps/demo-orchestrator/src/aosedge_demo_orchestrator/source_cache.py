# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Explicit, map-scoped Unreal DDC preparation; never runs on a UI status read."""

import os
import re
import shutil
import subprocess
import time
from uuid import uuid4

from .environment import EnvironmentError, JOURNAL
from .status import read_json


MAP = "/Game/Carla/Maps/Town10HD_Opt"


def progress_detail(log):
    if not log.exists():
        return ""
    with log.open("rb") as stream:
        stream.seek(max(0, log.stat().st_size - 16384))
        tail = stream.read().decode(errors="replace")
    waiting = re.findall(r"Waiting for (\d+) Shaders to finish", tail)
    return "; latest shader queue: " + waiting[-1] if waiting else ""


def command(paths, log):
    # This native commandlet follows map dependencies and fills the same DDC
    # used by UnrealEditor -game. No cooking, project save or engine rebuild.
    # Unlike the game launcher, this commandlet's NormalizePackageNames takes
    # a filesystem filename (without .umap), not a /Game package identifier.
    map_file = paths["project"].parent / "Content/Carla/Maps/Town10HD_Opt"
    return [str(paths["unreal-editor"]), str(paths["project"]),
            "-run=DerivedDataCache", "-fill", "-Map=" + str(map_file),
            "-TargetPlatform=Mac", "-unattended", "-nop4", "-nosound",
            "-NullRHI", "-abslog=" + str(log)]


def prepare(service):
    try:
        state = read_json(service.root / JOURNAL)
    except FileNotFoundError:
        state = {}  # Host setup is also valid before the first environment.
    source = state.get("source") or {}
    if (state.get("currentVehicle") or source.get("operation")
            or source.get("state") not in (None, "STOPPED")):
        raise EnvironmentError("SIMULATION_CACHE_REQUIRES_STOPPED_SIMULATOR")
    for key in ("runnerCommand", "simulatorCommand"):
        if source.get(key) and service.driver.live_process(source[key]):
            raise EnvironmentError("SIMULATION_CACHE_REQUIRES_STOPPED_SIMULATOR")
    service.vm._free_port(2000)
    if shutil.disk_usage(service.root).free < 60 * 1024 ** 3:
        raise EnvironmentError("SIMULATION_CACHE_DISK_GUARD_60_GIB")
    paths = service.driver.assets()
    directory = service.root / ".local/simulator-cache" / str(uuid4())
    service.environment._directory(str(directory.relative_to(service.root)))
    log = directory / "unreal.log"
    output = directory / "commandlet.log"
    started = time.monotonic()
    service.progress("CARLA: preparing Town10HD texture cache; first preparation may take several minutes")
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as handle:
        process = subprocess.Popen(command(paths, log), stdout=handle, stderr=subprocess.STDOUT)
        try:
            while True:
                try:
                    result = process.wait(timeout=30)
                    break
                except subprocess.TimeoutExpired:
                    elapsed = time.monotonic() - started
                    # Some macOS Unreal fatal paths wait indefinitely for a
                    # missing crash reporter. Treat the explicit fatal as a
                    # failure and reap this commandlet, never the live demo.
                    with output.open("rb") as stream:
                        stream.seek(max(0, output.stat().st_size - 16384))
                        fatal = b"Fatal error:" in stream.read()
                    if fatal:
                        raise EnvironmentError("SIMULATION_CACHE_PREPARATION_FAILED:" + str(output.relative_to(service.root)))
                    service.progress(("CARLA: map cache preparation running (%d s); VM unchanged" % elapsed)
                                     + progress_detail(log))
                    if elapsed >= 3600:
                        raise EnvironmentError("SIMULATION_CACHE_PREPARATION_TIMEOUT:" + str(output.relative_to(service.root)))
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
    if result != 0:
        raise EnvironmentError("SIMULATION_CACHE_PREPARATION_FAILED:" + str(output.relative_to(service.root)))
    # The native commandlet can exit successfully with a map that matched no
    # packages. Require proof that the requested map was actually processed.
    with log.open(errors="replace") as stream:
        map_loaded = any("LogDerivedDataCacheCommandlet:" in line and "Loading (" in line
                         and "/Carla/Maps/Town10HD_Opt.umap" in line for line in stream)
    if not map_loaded:
        raise EnvironmentError("SIMULATION_CACHE_MAP_NOT_PROCESSED:" + str(output.relative_to(service.root)))
    return dict(state="PREPARED", map=MAP, elapsedSeconds=round(time.monotonic() - started, 2),
                log=str(log.relative_to(service.root)), scope="MAP_DERIVED_DATA",
                cachePreserved=True, drivingVerification="NOT_PERFORMED")
