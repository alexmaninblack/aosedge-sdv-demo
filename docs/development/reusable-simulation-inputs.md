<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Reusable CARLA build inputs

- Status: Private dependency delivery under verification
- Version: 0.1
- Prepared: 2026-10-08
- Owner: Demo Solution Team
- Contract: [Release reproduction](../../contracts/release-reproduction/README.md#reusable-simulation-inputs)

Normal developer builds reuse the existing standalone CARLA. They compile
project components and assemble a demo, but do not compile Unreal, start an
Editor, or recook unchanged simulation content. The independent dependency
identity is `carla-macos-arm64-r1`; it is not a new CARLA upstream version or
a new demo release.

## Contents and compatibility

| Archive role | Contents | Build use |
| --- | --- | --- |
| `carla-runtime` | Exact retained standalone simulator, cooked content, compatible Python API and isolated Python 3.12 | Host assembly and Python base for Cloud SDK assembly |
| `host-support` | Exact retained native closure, QEMU, OpenSSL, notices and original host manifest | Native host assembly; original Gateway ancestry remains available, while the owner selects newly compiled Gateway outputs |
| `gateway-sdk` | Existing hash-bound LibCarla/OpenSSL headers, libraries, notices and SDK manifest | Offline Gateway compilation |

The [dependency lock](../../workspace/dependencies/carla-macos-arm64-r1.lock.json)
selects this set. It preserves Kit028's macOS ARM64/Town10HD_Opt configuration, including the
retained road-material corrections. The Git lock binds the existing CARLA and
Unreal source correspondence, original host manifest, SDK manifest, archive
digests and package inventories. This is an extraction of retained binaries,
not proof of a new clean source build. Existing native compatibility restrictions
still apply; the package does not extend supported macOS versions or hardware.

Editor/source trees, intermediate objects, derived-data caches, Factory images,
application UI, credentials, runtime logs and live Test data are excluded.
Some original provenance manifests retain historical build paths; they are
kept byte-for-byte inside private artifacts, not copied into public source.
Mixed dependency licenses/notices still apply. Private storage does not approve
redistribution of Unreal, assets or other bundled dependencies to new recipients.

## Acquire and use

Artifacts live under the separate `dependencies` folder in the existing private
Drive artifact root, outside demo release folders. The archive lock lives in Git;
the matching Drive binding (folder/file IDs and lock digest) is supplied privately.
No embedded credentials, login flow or automatic permission change is involved.
Use an already authorized Google CLI account for the initial download.

```sh
./lab dependencies prepare \
  --storage /Volumes/BUILD/simulation-inputs \
  --binding /Volumes/BUILD/private-dependency-binding.json \
  --account YOUR_AUTHORIZED_GOOGLE_ACCOUNT
./lab dependencies verify --storage /Volumes/BUILD/simulation-inputs
```

The command returns `kitInputs` and `gatewaySdk` paths. Supply those exact paths
to existing builds as `--kit-inputs` and `--gateway-sdk`. Host and Cloud SDK
assembly accept the sparse retained-host layout; Gateway accepts the unchanged
SDK manifest. There is no need to download a complete installer to get these
inputs. The directory is **not a complete kit**: preparation/Factory inputs are
not included, so it cannot alone satisfy `build --target all`.

The explicit workspace must be on the selected external SSD; no internal-disk
fallback is allowed. Downloads use SHA-256 cache keys and resumable partial
files. Complete repeat preparation validates the extracted file identities
without downloading or compiling again. A complete cache also allows offline
preparation without an account. Modified extracted files fail verification;
the tool does not overwrite them or silently adopt local changes.

Extraction rejects links, devices, escaping paths, extra/missing/duplicate
members and changed contents or modes. A failed extraction remains in its exact
owned `.partial` directory for diagnosis and is not a usable build input.
After inspection, a maintainer may remove only that failed extraction and rerun
with the intact verified cache; downloads need not be repeated. The final
directory is promoted only after the whole set verifies. Export/extraction
retain a 90 GiB reserve in addition to their declared byte demand; this is not
a measurement of the full cold build's peak disk consumption.

## Maintain a dependency version

Export only from explicitly selected retained inputs on the same SSD:

```sh
./lab dependencies export \
  --storage /Volumes/BUILD/simulation-publication \
  --kit-inputs /Volumes/BUILD/retained-kit \
  --gateway-sdk /Volumes/BUILD/retained-gateway-sdk
```

The export validates every selected file against existing manifests, preserves
payload bytes/modes, and creates three compressed archives plus a proposed lock.
Review the lock before selecting it for upload. `dependencies upload` is an
explicit maintainer publication operation requiring that lock, an authorized
account and the exact private destination folder. Ordinary preparation/build
never uploads. Non-secret upload intents reconcile existing file IDs, and a
same-name mismatch fails instead of replacing files or creating duplicates.

Keep immutable supported versions in Drive and a working digest cache on SSD.
Future dependency updates need a new identity, reviewed pins and affected
qualification. Do not overwrite `r1` when changing maps, assets, engine patches,
client ABI or native dependencies. Rebuilding unrelated services, Presenter,
Factory or packaging does not itself require a new CARLA package.

## Verification boundary

Transfer, payload integrity and existing consumer-input checks are separate
from native runtime and full-source build qualification. This work changes
neither the accepted 17-step producer plan nor historical release definitions,
application manifests, Factory images, signatures or the published demo DMG.
The next discussion selects the scope and capacity of a clean developer build;
a full-source Unreal/CARLA build remains a separate maintenance route.
