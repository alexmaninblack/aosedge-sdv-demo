<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# External SSD Package Transfer and Isolated Proof

- Date: 27 September 2026.
- Status: Transfer, isolated application/native smoke and negative-input checks PASS; not installer/live qualification.
- Parent: [External SSD deployment plan](../planning/active/external-ssd-deployment.md).
- Artifact: [Runtime Kit 004 checkpoint](portable-application-2026-09-26.md#corrective-live-findings-and-final-assembled-successor).

## Result

The exact current engineering candidate is preserved at
`/Volumes/SDV-Work/AosEdge-SDV/packages/runtime-kit-004-20260927`.
Its application manifest SHA-256 remains
`c7f5b967ae08407b4f1ee09714a7a0cea5ba555e5076598761052b3b990187bd`.
The internal original remains `/private/tmp/aosapp.dEU9Ge/Runtime Kit 004`.
This operation did not create an installer, sign or publish a release, change
the current runtime selection, or migrate an existing VM or any credentials.

Normal file ownership is enabled on Work. The operator created the exact
project directory after automated administrative creation was denied. Its
verified owner/group is the current operator, mode `0700`; the volume root
remains system-owned. Mount UUID, external status, capacity and the 90 GiB
reserve were checked before transfer and during progress checkpoints.

## Transfer proof

- **17,679 files; 35,114,325,564 logical bytes (32.7 GiB).** This includes the
  second Factory catalogue image path. This cross-device copy is not an APFS
  clone and does not claim to preserve source block sharing.
- **135.87 seconds** for source inventory/preflight, copying, per-file digest
  checks, final source/destination reconciliation and promotion. This is an
  end-to-end elapsed measurement, not a sustained/raw USB bandwidth benchmark.
- Source application manifest matches the independently recorded Kit 004 pin.
  Its five source locks bind the component manifests; their exact inventories
  and the existing Factory catalogue relationship close the allowed file set.
- All destination file sizes, SHA-256 values and modes match. Source inode,
  size, mode, link count and modification/change stamps remained unchanged.
  Unlisted files, links, special files and unsafe permissions are rejected.
- The temporary candidate was promoted to `packages` only after verification;
  its old staging path is absent. Both original and transferred package remain.
- Recorded external free space: 614,621,372,416 bytes, about **572.4 GiB**.
  The internal Data volume still reported approximately **97 GiB** free.

No operator configuration, `.run`, `.local`, ledger, backend history or
provisioned overlay was part of the manifest or copy. No existing artifact
was deleted and no recoverable-space gain on the internal disk is claimed.

## Isolated execution proof

The transferred private Python ran the complete-application probe with `-I -B`
under an additional test sandbox. Network access, developer/Homebrew/Xcode
inputs, the internal original kit and credential/Keychain reads were denied;
writes to the SSD package tree were denied. Explicit developer-file,
internal-manifest and network controls returned the required permission error.
The probe did not connect to the running simulator or operate any live service.

The successful corrected test took **11.16 seconds** including process launch,
on a just-copied/warmed package. This is not a cold-start or FPS measurement.
It established:

- all 69 application modules import from the SSD candidate;
- all five packaged input selectors resolve and validate their consumed inputs;
- private CLI help/version succeeds without developer tools;
- Factory .39 is discovered with no catalogue issues;
- Brake V1/V2/V3 and Tire V1 configurations retain the accepted file quota;
- the host Gateway/client bytes retain both services' required QM paths;
- the matching native CARLA Python API imports from the SSD;
- first-use TLS remains explicitly missing (`SOURCE_OPERATOR_TLS_REQUIRED`),
  rather than silently adopting development credentials;
- no `.local` or `.run` directory is created inside the package.

### Preserved initial failure and cause

The first proof terminated with `SIGSEGV` after 19 seconds. It added a direct
CARLA API import to the previous complete-app probe but passed a minimal
environment with neither `HOME` nor `CARLA_CACHE_DIR`. The native crash stack
entered `_GLOBAL__sub_I_FileTransfer.cpp` and `strlen` with a null address.
Source inspection of `LibCarla/source/carla/client/FileTransfer.cpp` confirmed
that its static cache-path initialization uses the override or constructs a
path directly from `getenv("HOME")` without a missing-value guard.

A single isolated import succeeded after supplying only an explicit test
`CARLA_CACHE_DIR`. The complete proof then passed with that same correction,
retaining every sandbox denial and the exact package bytes. No library was
rebuilt and no product protection was weakened. The actual packaged launch
retains normal OS environment variables while removing Python/DYLD overrides;
it was not the zero-environment harness used here.

Classification: qualification-harness environment mismatch, exposing an upstream
CARLA missing-environment robustness limitation. Future installer/launcher
tests must preserve the normal OS home context or supply the supported cache
input explicitly. This receipt does not claim the upstream null guard is fixed.
The initial failed receipt remains alongside the successful one.

## Native execution and negative-input follow-up

The same unchanged SSD candidate passed **27 native checks** using its private
Python and native tools. The execution sandbox denied developer sources,
Homebrew, Xcode, the internal kit, credentials and package writes. Networking
was denied except for the test's private Unix QMP sockets. No existing guest
disk, Cloud identity or simulator connection was used.

- Strict code-signature verification passed for QEMU, qemu-img, Gateway,
  VISS client, Presenter, Driving Control.app, Python, OpenSSL and the CARLA
  executable. This verifies existing signatures, **not** Developer ID,
  notarization, Gatekeeper acceptance or the complete CARLA app bundle.
- Packaged tools returned their expected help/version or invalid-argument
  result. The three Python UI helpers accepted `--help`. Presenter's `screen`
  command returned display geometry without opening or moving windows; this
  is not graphical/layout acceptance.
- The packaged qemu-img created, checked and inspected a separate 32 MiB
  virtual QCOW2 test disk with no backing file. Its physical file is about
  192 KiB and is retained with the native test records.
- Two separate paused, diskless QEMU processes initialized hardware
  virtualization, packaged firmware/QEMU data and the NIC ROM, answered QMP
  with `running: false`, and exited normally on `quit`. Their elapsed times
  were **0.057 / 0.061 seconds**. They had no network backend and did not boot
  an operating system; these are not guest-boot times.

The first observed QEMU `--version` call took **7.608 seconds**, inside the
existing 15-second launch-preflight limit. Three later measurements with the
same isolation policy took **0.404 / 0.155 / 0.024 seconds**. These are first
observed versus warmed preflight timings, not a cache-controlled cold-start
benchmark or proof of why the first call was slower. No timeout was changed.

### Corrupt/missing-input rejection

A disposable same-volume APFS copy-on-write clone was created exclusively for
these tests. Its 17,679 file paths, sizes and modes matched, with distinct
inodes and no hard links or symlinks. The actual packaged validators rejected
all **12** injected cases before any corrupted executable was launched:

| Input group | Injected condition | Observed rejection |
| --- | --- | --- |
| Host | Same-size Presenter byte change after validation cache | `HOST_RUNTIME_FILE_CHANGED` |
| Host | Group-writable file | `HOST_RUNTIME_FILE_CHANGED` |
| Host | Manifest byte change | `HOST_RUNTIME_MANIFEST_CHANGED` |
| Host | Additional importable file | `HOST_RUNTIME_UNDECLARED_FILE` |
| VM | Missing NIC ROM | `VM_RUNTIME_FILE_UNAVAILABLE` |
| VM | NIC ROM replaced by a link | `VM_RUNTIME_PATH_UNSAFE` |
| Cloud | Consumed SDK adapter byte change | `CLOUD_RUNTIME_FILE_CHANGED` |
| Cloud | Manifest byte change | `CLOUD_RUNTIME_MANIFEST_CHANGED` |
| Backend | Same-size archive change after validation cache | `BACKEND_INPUTS_ARCHIVE_CHANGED` |
| Backend | Unlisted file | `BACKEND_INPUTS_UNDECLARED_FILE` |
| Preparation | Manifest byte change | `PREPARATION_INPUTS_MANIFEST_DIGEST_MISMATCH` |
| Preparation | Brake V3 product-input byte change | `PREPARATION_INPUTS_FILE_DIGEST_MISMATCH` |

Mutations were restored, the five positive validators passed again, and all
eight touched original files retained their digests, modes and modification
times. Package writes remained denied throughout. No `.run` or `.local`
directory was created. Receipts and reproduction helpers were preserved before
removing only this owned clone after a conclusive zero-open-handle check.
Its 32.7 GiB logical size was shared storage, not an additional full physical
copy; cleanup recovered about 4.9 MiB, not 32.7 GiB. No original was deleted.

Separately, the five source regression modules (`test_host_runtime`,
`test_vm_runtime`, `test_cloud_runtime`, `test_backend_inputs`,
`test_preparation_inputs`) passed **62 tests in 0.496 seconds**. That is a
source-workspace regression result, not an additional SSD/clean-host proof.
No implementation or package bytes changed for this follow-up.

These cases establish rejection of invalid **present** input groups. They do
not establish whole-install completeness: the existing source/developer mode
still permits absent packaged groups to select developer inputs. A future
installer must close its complete-install/prelaunch contract explicitly; this
test did not change that compatibility behavior or implement such a guard.

## Evidence and preserved runtime

Small receipts under `/Volumes/SDV-Work/AosEdge-SDV/reports`:

- `kit-004-transfer-20260927.json`;
- `kit-004-offline-proof-20260927.json` (initial failure);
- `kit-004-offline-proof-002-20260927.json` (PASS);
- `kit-004-proof/` (transfer helper, qualification runner, probe and sandbox profile).
- `kit-004-native-negative-20260927/` (27 native checks, warmed preflight
  timings, 12 negative cases, scoped cleanup receipt and reproduction helpers).

Corresponding local engineering records remain in the ignored CARLA
`Build-distribution-stage2-20260926` directory. The scoped native crash report
is retained locally; it is not copied into the distributable package or Git.
The follow-up has a verified compact mirror in its
`ssd-native-negative-20260927` child. Only small native test records and the
192 KiB scratch disk remain under SSD `install-tests`; the negative clone is
absent. Work has approximately 572.3 GiB free after those tests.

The previously observed QEMU, CARLA, Driving Control and Presenter processes
remained present, using their internal packaged paths. No restart, control
command, Cloud action or runtime handoff was executed. This process-preservation
observation does not requalify live functional status.

## Remaining gates

The accepted Stage 3 installer format, first-use/state retention, update and
rollback decisions remain open before new lifecycle code. Fresh-engine import,
operator UI acceptance and native clean-Mac E2E are not established by these
artifact checks. Clean macOS is not installed; no reboot occurred. Heavy builds,
Docker's disk, active VM overlays, source repositories and caches remain internal.
Do not delete their inputs because a copied package passed an offline proof.
