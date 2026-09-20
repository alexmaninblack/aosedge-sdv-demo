<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .36: separate guest-reboot engineering check

Date: 19 September 2026. Status: OBSERVED; same-Test engineering recovery
completed. Autonomous bare-guest reboot recovery remains unqualified.

The operator explicitly separated this check from the continuous demonstration.
Park/Resume remains absent from Demo Studio. No new boot behavior, AosCore patch,
Factory rebuild or repeated reboot is authorized by this record.

After the passing CM-only cleanup/storage check, one direct guest `systemctl
reboot` was issued against the owned .36 Test (Unit
`3df2d00e-62a4-4a52-85ef-179427becf65`). Both backend containers were already
stopped intentionally, with their databases preserved. CARLA was in Safe Stop;
the scene, VM disk, identities and installed releases were retained.

Boot identity changed from `0b188568-8d28-4f60-8376-2c03753d309a` to
`638c0168-d3aa-41d7-bf68-8f2820d7629b`. All fourteen original queued message
hashes were still present and unchanged (35 messages at the later snapshot).
Brake retained wear74/score26, generation3, its last assessment and producer
epoch. This is evidence against recurrence of the fixed shared-storage loss,
not proof of complete functional recovery after reboot.

The direct guest reboot did not run the existing host-side startup recovery.
VDP repeatedly failed with `VISS client certificate is unavailable`; SM was
still activating/restarting. CM and IAM were active and SELinux Enforcing.
At the bounded check VDP NRestarts=17 and SM NRestarts=2. No restart-stability
or automatic full-boot recovery pass is claimed.

Code inspection identifies the existing recovery path:
`VMManager._start` in `vm.py` supplies `source_restore` for the same enrolled
Unit/Node; `source_trust_guest.py` action `trust-restore` validates previously
stored identities/material and reconstructs the volatile systemd credential
drop-ins. It does not issue new credentials, rotate leaves, reset the model or
change Gateway assignment. The accepted next step is one idempotent
`democtl vm start test` invocation, not another reboot or a source change.

The idempotent startup completed in 3.62 seconds, with no provisioning, new VM,
current-vehicle change or CARLA action. SM/VDP credential snapshots were restored.
A second volatile dependency remained absent: the owned guest Gateway DNAT gate.
VDP reported connection refused to port6443; the Gateway continued listening on
16443 with the same authenticated assignment. Thus startup alone was not full
source recovery, and autonomous bare-guest reboot remains unqualified.

The operator authorized restoration of the current setup. A bounded engineering
invocation of the existing democtl guest `allow` helper restored only the original
gate after verifying exact Unit/source-run ownership, fresh Safe Stop, no pending
handover, the same selected Gateway identity/generation, and gate ABSENT. This
was an internal-helper recovery exception, not a public UI/CLI recovery pass.
It changed no credential, security scope, assignment generation, scene or source.
Both backends were restored with dataPreserved=true. By 17:01:20 both services
reported RECEIVING and zero queued messages; native warning displays returned.
No code or Factory Image change was made. Further reboot work is explicitly
separate from the main cycle in [the qualification record](factory-36-e2e-2026-09-19.md).
