#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Prove that the qualification reader token cannot write KUKSA values."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PYTHON_ROOT = Path(
    "/var/aos/workdirs/sm/runtimes/systemd-slot-component/active/python"
).resolve()
sys.path.insert(0, str(PYTHON_ROOT / "site-packages"))

from kuksa_client.grpc import (  # noqa: E402
    DataEntry,
    Datapoint,
    EntryUpdate,
    Field,
    VSSClient,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
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
        try:
            client.set(
                [
                    EntryUpdate(
                        DataEntry("Vehicle.Speed", value=Datapoint(99.0)),
                        (Field.VALUE,),
                    )
                ],
                try_v2=False,
                timeout=2.0,
            )
        except Exception:
            print("KUKSA_READER_WRITE=DENIED")
            return 0
    raise RuntimeError("read-only KUKSA token unexpectedly wrote a value")


if __name__ == "__main__":
    raise SystemExit(main())
