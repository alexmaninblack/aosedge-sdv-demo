<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# democtl Local VM Lifecycle — Terminal Acceptance

- Date: 2026-09-05
- Scope: local Test/Production VM lifecycle, no Cloud or CARLA operation
- Source: main working tree based on fe35641; this record is not a commit/push receipt
- Design: [Demo Control](../architecture/demo-control.md), Local VM Start/Stop — Agreed Increment
- Operator instructions: [Demo Orchestrator](../../apps/demo-orchestrator/README.md)

## Execution Boundary

The operator explicitly authorized full create/start/stop/retire cycles and
interactive guest authentication. Every live check used democtl from
apps/demo-orchestrator with its virtual environment activated, exactly as a
terminal user would. No direct SSH/QMP/QEMU invocation or old lifecycle wrapper
was used as an alternative acceptance path. A password was entered only at
getpass prompts; it was not added to source, argv, configuration or this record.
Fixture-test success was not used as proof that these live commands worked.

The selected factory artifact was 6.1.1-maninblack.27/main-qemuarm64:

- format raw, size 6,997,147,648 bytes;
- SHA-256 dbc018cf31dc83accbca82cf26df0b3ca69c66d1135100db8d05552fd2744c56;
- original artifact and published manifests unchanged;
- independent local factory copy and fresh role overlays created by democtl;
- macOS ARM64/HVF and the existing aos-main-qemuarm64-v1 profile.

## Defects Found and Corrected

1. DNS process ownership compared Python argv literally. macOS framework
   Python re-execs Python.app. Ownership now accepts this interpreter's native
   executable while still matching the exact script, arguments and owner ID.
2. First serial setup had one pre-boot Enter and an opaque common timeout.
   Before login only, the console prompt is requested again after boot. Fixed
   progress states distinguish console, password, shell and key-install stages.
   Login and password are not blindly resubmitted.
3. The host key was read from a guessed /etc/ssh path. This image's SSHD_OPTS
   selects /etc/ssh/sshd_config_readonly. The client now reads that -f setting,
   obtains sshd's effective HostKey and pins its public half over owned serial.
4. DNS checks invoked getent, absent from this image (exit 127). Both the guest
   dnsmasq and host bridge actually answered DNS queries. Readiness now uses
   the installed BusyBox nslookup with a bounded query; guest DNS was not patched.
5. A TCP bind probe could reject immediate restart after a closed SSH session.
   The TCP probe now matches QEMU's SO_REUSEADDR behavior. UDP remains exclusive.
   The immediate stop/start cycle subsequently passed for both roles.
6. Fresh first boot plus SSH enrollment exceeded the original 60-second ceiling.
   The ceiling is now 90 seconds, with readiness-driven completion. Both selected
   VM processes launch before readiness waits, allowing their boots to overlap.

Guest systemd observations showed userspace beginning around 5–6 seconds and
serial-getty/boot completion around 35–36 seconds on the guest monotonic clock.
Those values exclude early firmware time and do not prove which boot unit
accounts for the interval. No firmware, rootfs, Aos service or VM hardware
change was made to conceal this measured first-boot cost.

## Observed Command Results

| Command / condition | Observed result |
| --- | --- |
| image list | Published .27 selector available |
| environment create --image 6.1.1-maninblack.27/main-qemuarm64 --target all | COMPLETED; fresh Test/Production overlays; measured example 3.31 s |
| vm start all, fresh factory-derived overlays | One invocation COMPLETED for both; SSH=True and DNS=True; Test 58.72 s, both reported ready by 73.52 s, excluding password entry |
| vm start all, already running | COMPLETED without re-enrollment; both results by 4.60 s |
| vm stop all followed immediately by vm start all | COMPLETED without password; Test ready by 23.97 s, both by 26.10 s |
| status all --guest | Both authenticated; DNS resolved; provisioning IAM active; normal IAM/SM/CM inactive; observed service restart counts zero |
| vm stop test; status production --guest | Test stopped; Production and shared DNS remained operational |
| vm stop production; status test --guest | Production stopped; Test and shared DNS remained operational |
| vm stop all | Graceful shutdown completed; typical running-role result 2.4–3.4 s; owned shared DNS shut down after the last VM |
| vm stop all, already stopped | Successful no-op; about 0.2 s per role |
| environment retire, while running | BLOCKED CURRENT_RUN_RECOVERY_REQUIRED; no deletion; subsequent VM operations still worked |
| environment retire, stopped/proven unprovisioned | COMPLETED; exact overlays, generated host-access files, local factory copy/manifest and journal removed without backup |
| environment retire, already absent | Successful no-op |
| retire followed by create | Fresh local copy/overlays recreated from the same original .27; no rebuild |

Commands were exercised across diagnostic and fresh acceptance cycles. Times
are observations on this host, not a latency guarantee for other images or
machines. Role duration runs from its launch attempt to its reported result;
with all, those intervals overlap and readiness is observed in role order.

VM start completion proves QMP/SSH/DNS readiness, not that every Aos service
has finished booting. Immediately after a restart, status briefly observed
inactive Aos services; a later read confirmed provisioning mode and zero
restarts. Provisioning remains a separate, currently unimplemented operation.

## Final State and Exclusions

At the final status read (2026-09-05 05:10:36 UTC), the current journal was
LOCAL_STOPPED and both managed VMs were STOPPED. The last stop operation
completed shared DNS shutdown. Current overlays, local factory copy and
enrolled SSH access were retained for the operator's next start. Earlier
diagnostic environments were permanently removed by explicit retire; the
original factory artifact was retained throughout. No backup was created.

This qualifies only the exercised local CLI slice on .27. It does not qualify
Cloud provisioning/deprovisioning, FOTA, Production Cloud deployment, CARLA,
Current Vehicle handover, full scenario R0, Mac crash/sleep recovery or arbitrary
image versions. No Builder, compilation, Cloud API mutation, service restart
inside a guest, rootfs patch, security relaxation, commit or push was performed.
