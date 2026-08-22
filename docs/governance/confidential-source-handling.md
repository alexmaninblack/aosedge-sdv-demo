<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Confidential Source Handling

## Rule

Customer- or OEM-provided source material must never enter a Git repository,
including a private repository. This prohibition includes the original file,
renamed or reformatted copies, screenshots, extracted worksheets, direct
quotes, and archives containing any of them.

Only a separately authored, reviewed, customer-neutral derivative may be
committed. A derivative must contain our own wording, no customer identity,
no confidential internal detail, and no reference that enables retrieval of
the original material.

## Local storage

Canonical confidential inputs live under the developer's local
`OpenAI/PrivateInputs/` tree, outside every Git worktree. The containing
directories use owner-only permissions and each source file has a local
manifest recording its classification, digest, size, and publication rule.

The original download may remain temporarily as a second local copy. It is not
the canonical project input and must not be moved into a repository.

## Defense in depth

This repository uses four protections:

1. repository `.gitignore` rules reject confidential-input directories and
   known generic filename patterns;
2. the developer's global Git ignore applies the same patterns to every local
   repository;
3. `.githooks/pre-commit` scans staged paths and content before a commit;
4. `.githooks/pre-push` scans reachable Git history before a push.

The content guard recognizes the protected source by digest and workbook
structure, so simply renaming the file does not make it acceptable.

Enable the versioned hooks in a fresh checkout:

```sh
git config core.hooksPath .githooks
./scripts/guard-confidential-inputs --tracked
```

These controls protect the normal Git workflow. `git --no-verify`, manual web
uploads, email, chat attachments, cloud-sync folders, and arbitrary archive
creation can bypass Git hooks, so the handling rule remains mandatory even
when all automated checks pass.

## Sanitized derivative review

Before committing a derivative, confirm all of the following:

- the raw source is absent from the worktree and Git index;
- the customer is not identified;
- no cell, sentence, screenshot, or distinctive internal label was copied;
- each concern is paraphrased as a general automotive requirement;
- current evidence is labelled `UNKNOWN`, `PARTIAL`, `PLANNED`,
  `DOCUMENTARY_ONLY`, `ACCEPTED`, or `STALE` honestly, and `ACCEPTED` is bound
  to exact current evidence without exposing the confidential source;
- claim boundaries state what the demo cannot prove;
- the confidential-input guard passes for staged content and history.

## Incident response

If confidential material is ever committed, do not push it. Stop immediately,
record the affected repository and commit locally, and remove it from the
entire unpublished history before continuing. If it reaches any remote, treat
that as a disclosure incident; deleting the latest file is not sufficient
because the object remains in history and caches.
