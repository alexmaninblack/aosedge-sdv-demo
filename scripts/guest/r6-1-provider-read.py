#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Check all provider-owned KUKSA paths in a disposable qualification VM."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PYTHON_ROOT = Path(
    "/var/aos/workdirs/sm/runtimes/systemd-slot-component/active/python"
).resolve()
sys.path.insert(0, str(PYTHON_ROOT / "site-packages"))

from kuksa_client.grpc import VSSClient  # noqa: E402


PATHS = (
    "Vehicle.Speed",
    "Vehicle.Acceleration.Longitudinal",
    "Vehicle.Acceleration.Lateral",
    "Vehicle.Acceleration.Vertical",
    "Vehicle.Chassis.Accelerator.PedalPosition",
    "Vehicle.Chassis.Brake.PedalPosition",
    "Vehicle.Chassis.Axle.Row1.SteeringAngle",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("expectation", choices=("available", "unavailable"))
    parser.add_argument("--token", required=True, type=Path)
    options = parser.parse_args()
    token = options.token.read_text(encoding="ascii").strip()
    if not token or "\n" in token:
        raise ValueError("qualification token must contain exactly one JWT")
    with VSSClient(
        "127.0.0.1",
        55555,
        token=token,
        root_certificates=Path("/etc/kuksa-val/CA.pem"),
        tls_server_name="127.0.0.1",
    ) as client:
        values = client.get_current_values(PATHS, timeout=3.0)
    available = {path for path in PATHS if values.get(path) is not None}
    if options.expectation == "available" and available != set(PATHS):
        raise RuntimeError("one or more provider-owned paths are unavailable")
    if options.expectation == "unavailable" and available:
        raise RuntimeError("one or more provider-owned paths retain stale data")
    print(f"KUKSA_PATHS={len(PATHS)} STATE={options.expectation.upper()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
