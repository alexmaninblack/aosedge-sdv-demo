<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Select a release and obtain access

The SDV Lab is an engineering preview. Use the
[single launcher in README](../../README.md#start-here) to select a route:
it obtains the matching package or developer inputs automatically.
You do not need to choose an old kit number or find a release JSON file.

## Install the selected demo

Route **A / 1** downloads the complete DMG from its public link, or reuses a
matching local copy. No Dropbox or Google account is required.

The [launcher catalog](../../workspace/launcher-catalog.json) identifies the
selected version, download and immutable delivery descriptor. The launcher
checks file size, SHA-256 and Setup identity before requesting macOS to open
it; Setup then checks its matching Runtime Kit. Do not substitute another
DMG just because its filename or product version looks the same.

Keep a verified local copy for another installation. The app is Apple
Development signed, not notarized. Do not disable macOS security controls to
open it. Continue with [installation and Cloud access](installed-preview-cloud-first-use.md).

## Build the installer

Route **B / 2** prepares the host, checks out the source and builds using its
selected component revisions and prebuilt dependencies. Start from the
current README and launcher on `main`; you do not need to collect component
repositories manually.

The [developer build selection](../../workspace/current-developer-build.json)
is separate from route A's downloadable DMG. It determines the producer plan
and compatible inputs. Public inputs need no Google login. Have Xcode and an
authorized Apple Development signing identity available.

This route reuses the vehicle simulator and **Factory image**, the clean
Linux/AosEdge base for the ARM64 virtual controller. To prepare tools for
rebuilding those heavy dependencies, choose **C / 3** instead.
See the [developer guide](reproduce-demo.md) and
[specialist prerequisites](full-source-build.md).

## Connect to Aos Cloud

Public downloads do not provide Cloud credentials or publication rights.
For the first demo, use one **OEM** and one associated **Service Provider**
account; Brake and Tire are separate services under that SP.

Setup accepts existing certificate files or requests new ones using OEM/SP
issuance tokens from the official Cloud flow. Existing certificates determine
the environment. For new certificates, choose **Production** or **Staging**.
Register accounts and obtain invitations through the official Cloud process.
No credentials, account sessions or provisioned controller are included in
the DMG or a source clone.

Restricted Unreal source access is separate and needed only when rebuilding
the simulator, not when installing the demo or using route B. Public download
access does not grant redistribution rights to restricted content.

If a download or prerequisite is unavailable, use
[troubleshooting](troubleshooting.md). Do not substitute an older package or
another person's private keys.
