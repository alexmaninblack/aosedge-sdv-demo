#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Bounded native lock probes. Failing concurrency cases stay FAIL, not XFAIL."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


def run_case(binary, output, module, action, schedule, attempt):
    name = f"{module}_{action}_{schedule}_{attempt}"
    started = time.monotonic()
    child = subprocess.Popen([str(binary), module, action, schedule],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    stack = ""
    timed_out = False
    try:
        stdout, _ = child.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            dump = subprocess.run([
                "gdb", "--batch", "-nx", "-ex", "set auto-load off",
                "-ex", "set pagination off", "-ex", "set print frame-arguments none",
                "-ex", "thread apply all bt 14", "-ex", "detach", "-p", str(child.pid)
            ], capture_output=True, text=True, timeout=5)
            stack = dump.stdout + dump.stderr
        except subprocess.TimeoutExpired:
            stack = "STACK_CAPTURE_TIMEOUT\n"
        finally:
            child.kill()
            stdout, _ = child.communicate(timeout=3)
    (output / f"{name}.log").write_text(stdout)
    if stack:
        (output / f"{name}.stack.txt").write_text(stack)
    subscriber = "Monitoring" if module == "monitoring" else "Alerts"
    sender = "SendMonitoringData" if module == "monitoring" else "SendAlerts"
    markers = all(marker in stdout for marker in ["SEND_PASSED_RUNNING_CHECK",
        "DISCONNECT_CALLBACK_ENTERED", "SEND_GATE_RELEASED", "RENDEZVOUS_COMPLETE"])
    stack_matches = (f"{subscriber}::OnDisconnect" in stack and
                     f"{subscriber}::{sender}" in stack and
                     "Communication::EnqueueMessage" in stack and
                     "Communication::CloseConnection" in stack and
                     "pthread_mutex_lock" in stack)
    passed = child.returncode == 0 and "PASS_COMPLETED_AND_RECONNECTED" in stdout
    result = {
        "case": name, "result": "PASS" if passed else "FAIL",
        "exitCode": child.returncode, "timedOut": timed_out,
        "rendezvousConfirmed": markers,
        "transportMutexHeldAtCallback": ("TRANSPORT_MUTEX_HELD=1" in stdout)
            if "TRANSPORT_MUTEX_HELD=" in stdout else None,
        "nativeWaitCycleStackConfirmed": stack_matches,
        "seconds": round(time.monotonic() - started, 3),
    }
    print(json.dumps(result), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error("--repeat must be at least 1")
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    for attempt in range(1, args.repeat + 1):
        for schedule in ("serial", "overlap"):
            for module in ("monitoring", "alerts"):
                for action in ("disconnect", "stop"):
                    results.append(run_case(args.binary, args.output, module, action, schedule, attempt))
    summary = {"binarySHA256": hashlib.sha256(args.binary.read_bytes()).hexdigest(),
               "results": results}
    (args.output / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
    return 0 if all(row["result"] == "PASS" for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
