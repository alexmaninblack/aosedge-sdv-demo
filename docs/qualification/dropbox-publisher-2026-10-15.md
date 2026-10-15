<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Automatic Dropbox publisher acceptance on 15 October 2026

## Scope and isolation

The operator authorized automatic publication of future DMGs and catalog-link
projection, with the active M1 final acceptance kept separate. Implementation
uses an isolated integration worktree and feature branch. No current release
selection, active campaign, M1 runtime, main branch or release tag was changed
by this acceptance.

## Completed evidence

- The dedicated `AosEdge SDV Lab Release Publisher` application uses Dropbox
  **App folder** access. The operator created the app and explicitly approved
  the reviewed upload, metadata, sharing and account-info scopes.
- PKCE/offline authorization completed through the loopback callback. The
  authorization code was removed from the visible callback URL. The listener
  closed, and new processes obtained fresh access using the private refresh
  credential without another browser login.
- Credentials are mode `0600` in an owner-only directory outside Git. A separate
  private delivery profile supplies future campaigns through
  `--delivery-profile`; neither credentials nor account identifiers are included
  in this source report.
- The offline publisher scenario passed 71 tests covering transport recovery,
  first publication, repeat, credential/privacy checks, token refresh, file and
  revision conflicts, public-link validation, catalog projection and the failed
  publication promotion gate. Documentation, reader routes, launcher pins and
  the confidential-input guard passed.
- The sender transport scenario created a separate valid **20,020-byte** DMG
  containing only a text explanation that it is a transport fixture. It uploaded
  into the app's `/transport-checks` folder and obtained a public download link.
  This `0.0.0-rc.0` fixture is not an application or release candidate and never
  enters the product catalog.
- Remote file revision, size and Dropbox content hash matched. Anonymous HEAD
  passed. Repeating publication through a fresh client sent **zero** payload
  bytes and performed no upload or link-creation mutation. A complete new
  process then repeated the same scenario, preserving the original receipt and
  again reusing the file without a payload upload.

Fixture SHA-256:
`9b62fe4124bd9d54e35df96df231a7f93d83b7e0513477049044ff2bc779428c`.

Fixture Dropbox content hash:
`a6e415117e34f5b7041ff1dac729d4f3d22785aee82245ec01c90f303b13e050`.

The first sender scenario took 27.453 seconds including small-image preparation,
OAuth refresh, publication, metadata/share checks and the no-upload repeat.
It is not a measurement of large-DMG throughput or an actual consumer download.
Private immutable-image, upload-session and numbered reports remain under the
selected workspace's `build/dropbox-publisher-transport`. Disposable build
scratch was removed; the tiny fixture and compact evidence were retained for
repeat/restart reconciliation. No existing product image or cache was removed.

## Remaining release boundary

The automatic adapter is ready for integration after the concurrent acceptance
owner finishes. Its profile must be selected for the next frozen release
campaign; an existing campaign cannot be rebound. Product qualification and
anonymous M1 download/signature/Setup acceptance remain owned by that campaign.
A successful sender upload does not promote a new product version or change its
engineering-preview/signing limitations. Catalog and launcher projection take
the generated URL automatically, while final main/tag promotion retains the
existing consumer and cleanup gates.

[Publisher operation and recovery](../development/release-campaign.md#automatic-dropbox-publication)
records the accepted procedure and reusable scenario entries.
