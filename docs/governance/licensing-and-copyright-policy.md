# Licensing and Copyright Policy

## Scope

This policy applies to the planned public
`alexmaninblack/aos-vehicle-platform` and
`alexmaninblack/brake-health-service` repositories and to artifacts
published from them. Existing repositories retain their current licenses and
notices unless a separate reviewed decision changes them.

## Project License and Copyright Holder

- License both new repositories under the Apache License, Version 2.0.
- Use the SPDX identifier `Apache-2.0`.
- Use the exact copyright holder text `maninblack` for original project files.
- Do not name an employer, customer, GitHub organization, AosEdge, the Apache
  Software Foundation, Eclipse Foundation, COVESA, or another third party as a
  copyright holder for original project work.

The standard original-file header is:

```text
SPDX-FileCopyrightText: 2026 maninblack
SPDX-License-Identifier: Apache-2.0
```

Apply the appropriate comment syntax for each source or configuration format:

```python
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: Apache-2.0
```

```cpp
// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: Apache-2.0
```

Do not modify the holder string's spelling, capitalization, or spacing without
a new explicit decision.

## Repository-Level Files

Each new repository must contain:

- `LICENSE` with the unmodified Apache-2.0 license text;
- a minimal project-specific `NOTICE`;
- `THIRD_PARTY_NOTICES.md` describing only material actually copied, modified,
  generated from, or bundled into the repository or its distributions;
- `CONTRIBUTING.md` documenting Apache-2.0 submission terms and Developer
  Certificate of Origin sign-off;
- machine-readable license metadata and a CI license-compliance gate.

The initial platform `NOTICE` is:

```text
Aos Vehicle Platform
Copyright 2026 maninblack
```

The initial service `NOTICE` is:

```text
Brake Health Service
Copyright 2026 maninblack
```

Do not include Apache Software Foundation attribution boilerplate: these are
Apache-licensed projects, not Apache Software Foundation projects.

## File Stages and Provenance Rules

### Original files

Add the project SPDX copyright and license tags when the file is created.
Use the first publication year for a new file. Do not update copyright years
mechanically on every edit or every calendar year.

### Files with multiple original copyright holders

Preserve every valid holder statement. Add an additional
`SPDX-FileCopyrightText` line only when a contributor or organization owns a
copyrightable contribution and requests or requires that notice. Git authorship
alone does not require changing every file header.

### External contributions

Contributors retain copyright in their contributions and submit them under
Apache-2.0. Do not require copyright assignment initially. Require a
`Signed-off-by` line under the Developer Certificate of Origin for commits
accepted from external contributors.

### Third-party and upstream files

- Preserve all upstream copyright, license, patent, trademark, attribution,
  and NOTICE content required by the upstream license.
- Never replace an upstream header with the project header.
- Never add an Apache-2.0 header to a file governed by MIT, MPL-2.0, or another
  license.
- Mark modifications to Apache-2.0-derived files prominently and preserve the
  original Apache license and relevant NOTICE content.
- Do not copy code from a repository that does not provide an applicable
  license or other explicit permission.

The AosEdge `demo-services/kuksa-test-client` is an architectural reference
only until its source license is confirmed. Do not copy its implementation into
either project repository merely because the repository is public.

### VSS-derived material

COVESA Vehicle Signal Specification source material is MPL-2.0. Keep copied or
derived VSS files clearly separated and under their applicable upstream
license. The project's original vehicle telemetry profile may reference VSS
paths and a pinned VSS release, but it must not silently relicense a copied VSS
tree as Apache-2.0.

### Generated files and formats without comments

Where a valid header would break the format or generated output, record the
file's copyright and license through repository-level REUSE metadata or an
equivalent machine-readable mechanism. Generated files must identify their
generator and source license; do not assume the generated output becomes
Apache-2.0.

### Binary distributions and service packages

Every distributed source archive, platform artifact, OCI image, layer, and Aos
service package must carry license and notice material that accurately reflects
its bundled contents. A binary distribution may require more third-party
notices than the source repository because it can bundle additional runtime
dependencies.

## Compliance Gate

Before a release or public artifact is accepted:

1. verify all original eligible files have the approved SPDX tags;
2. verify no private key, token, certificate, account identifier, or restricted
   source is tracked;
3. produce and review the dependency license inventory;
4. verify all copied or modified third-party files retain their original
   notices;
5. verify `LICENSE`, `NOTICE`, and `THIRD_PARTY_NOTICES.md` describe the exact
   contents of the distribution;
6. reject unknown, missing, or incompatible licenses;
7. record the accepted compliance result with the release.

## References

- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
- [Applying the Apache License 2.0](https://www.apache.org/legal/apply-license)
- [REUSE specification tutorial](https://reuse.software/tutorial/)
- [Developer Certificate of Origin](https://developercertificate.org/)
- [COVESA Vehicle Signal Specification](https://github.com/COVESA/vehicle_signal_specification)
