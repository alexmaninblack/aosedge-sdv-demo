#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Serve deterministic seven-path VISS telemetry inside a disposable VM."""

from __future__ import annotations

import datetime as dt
import json
import ssl
import sys
import time
from pathlib import Path


PYTHON_ROOT = Path(
    "/var/aos/workdirs/sm/runtimes/systemd-slot-component/active/python"
).resolve()
sys.path.insert(0, str(PYTHON_ROOT / "site-packages"))

from websockets.sync.server import serve  # noqa: E402


VALUES = {
    "Vehicle.Speed": "42.5",
    "Vehicle.Acceleration.Longitudinal": "1.25",
    "Vehicle.Acceleration.Lateral": "-0.5",
    "Vehicle.Acceleration.Vertical": "0.0",
    "Vehicle.Chassis.Accelerator.PedalPosition": "23",
    "Vehicle.Chassis.Brake.PedalPosition": "0",
    "Vehicle.Chassis.Axle.Row1.SteeringAngle": "-4.75",
}


def handler(websocket) -> None:
    request = json.loads(websocket.recv(timeout=5))
    if request.get("action") != "subscribe" or request.get("path") != "Vehicle":
        raise RuntimeError("fixture received an unexpected VISS request")
    request_id = request.get("requestId")
    websocket.send(
        json.dumps(
            {
                "action": "subscribe",
                "requestId": request_id,
                "subscriptionId": "r61-fixture-1",
            }
        )
    )
    while True:
        timestamp = (
            dt.datetime.now(dt.timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )
        websocket.send(
            json.dumps(
                {
                    "action": "subscription",
                    "subscriptionId": "r61-fixture-1",
                    "data": [
                        {"path": path, "dp": {"value": value, "ts": timestamp}}
                        for path, value in VALUES.items()
                    ],
                    "ts": timestamp,
                }
            )
        )
        time.sleep(0.05)


def main() -> int:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(
        "/etc/kuksa-val/Server.pem", "/etc/kuksa-val/Server.key"
    )
    with serve(
        handler,
        "127.0.0.1",
        6443,
        ssl=context,
        subprotocols=["VISSv3"],
    ) as server:
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
