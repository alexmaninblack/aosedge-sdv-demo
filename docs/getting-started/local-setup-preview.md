<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Local Setup Preview

**Historical instructions — 27 September 2026.** For the current operator path,
use [Installed Preview: Cloud First Use](installed-preview-cloud-first-use.md).
The matching candidate and actual qualification results are in the
[current installed-package receipt](../qualification/installed-serial-e2e-2026-09-29.md).
Do not choose Kit 007 or an old ad-hoc Setup because this retained page mentions
them. This page preserves the original local-slice evidence and link targets;
its "not yet wired" statements below are historical, not current capability claims.

The original engineering **local installation/selection and existing-access preview** was not the finished
installer for external users. That preview accepted complete Kit 007 only
on Apple silicon with macOS 26 or later. It is locally ad-hoc signed, not
notarized; do not disable Gatekeeper or other OS security to run it.

## What the window does

1. Open **AosEdge SDV Lab Setup** and choose the complete offline Kit 007 folder.
   Do not select a component subfolder. The expected release digest is built
   into the setup application, not read as a trusted value from that folder.
2. Choose **Package storage**. This can be a recognized existing SDV store or
   a new folder beneath an existing parent, including an ownership-enabled
   external volume. The original volume must remain connected. Setup never
   adopts an unrelated directory or makes a missing mount path.
3. Keep **Private demo data** at a short internal path, such as the suggested
   `SDV-Lab-Data` folder in your home directory. This is separate from immutable
   program storage. A recognized existing instance may be inspected; an active
   owner or retained current run blocks switching. Do not delete run data to
   bypass that guard. For isolated testing, choose a separate fresh folder.
4. Click **Check installation**. This checks release metadata, ownership,
   platform, paths and available space. It does not yet hash every large file.
   Editing any folder invalidates the check. The current engineering disk guard
   reserves 90 GiB beyond a required full copy; it is not a final published
   end-user storage requirement.
5. Click **Install package**. The operation verifies contents; a repeated
   installation verifies the existing version and reuses it. Large-file checks
   can take minutes. During verification the progress indicator can remain
   indeterminate; it is not a readiness indicator. The window stays responsive,
   but changing inputs, duplicate operations and closing are blocked until the
   result is known.
6. After **Package installed — demo not started**, click **Prepare local data**.
   This explicitly creates/recognizes a private instance, verifies the installed
   package and selects it with revision/ownership guards. No service starts.

If an operation fails, review its fixed diagnostic and check again. Source,
unrelated data and completed transactions are preserved. After an interruption,
an explicit repeat reconciles the existing transaction rather than trusting the
old progress percentage. This preview has no destructive repair/uninstall UI.

## Existing Cloud access

After local preparation, open **Set up Cloud access**. On a later launch, select
the same private-data folder to resume this step without reinstalling the kit.
This path is limited to a fresh installed instance; a retained run must use its
normal Demo Control workflow instead.

1. Choose your own OEM and SP certificate files. Both must be distinct,
   owner-private, unencrypted PKCS#12 files belonging to the same Cloud domain.
   Do not paste certificate contents or tokens. Setup stores references only;
   keep the files at their selected locations.
2. **Inspect locally** checks file safety, validity and certificate-derived
   domain using the verified installed SDK. It does not authenticate roles.
3. Review the domain and validity dates, then **Use this pair**. Both references
   are saved together in the private Demo Control configuration. A file,
   configuration or version change invalidates the preview.
4. **Check Cloud access** explicitly authenticates the pair and reads access,
   OEM/SP association, architecture, model/set and delivery prerequisites.
   Missing model/set objects are not created. Node-type registration is checked
   after provisioning, not treated as a prerequisite that blocks provisioning.
   The result is an observation, not a Ready/Running flag.

Each Cloud step has a two-minute helper deadline, including local verification.
On timeout, completed local saves are preserved and the prior result is cleared.
No automatic retry is performed; inspect again explicitly after diagnosis.
Interrupted local writes require reconciliation, not automatic overwriting.
The [existing-access receipt](../qualification/native-cloud-access-2026-09-27.md)
separates fixture tests, native UI qualification and outstanding live checks.

## What still follows

**Local setup complete — Cloud setup remains** is not Ready, Online or Running.
Docker application presence is only a presence check, not an engine check.
Docker installation/licensing and OS permissions remain explicit operator steps.
Secure enrollment, dependency/Cloud preparation and the guarded first launch
are not yet wired into this preview. Do not enter
secrets into path fields or copy developer credentials. One OEM and one
associated SP are sufficient for both independent Brake and Tire services.

See the [qualification receipt](../qualification/native-setup-2026-09-27.md)
for exact candidate identity and evidence, and the
[distribution plan](../planning/active/installable-distribution-and-reproducibility.md)
for remaining DMG, signing, retention, onboarding and clean-Mac gates.
