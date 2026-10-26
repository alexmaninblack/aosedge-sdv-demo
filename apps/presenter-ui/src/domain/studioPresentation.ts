// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import type { PlatformCloudObservation } from "./platformObservation";

/** Presentation only: retained connection evidence never becomes current authority. */
export function cloudPresentation(observation: PlatformCloudObservation | null | undefined, loading: boolean, emptyLabel: string) {
  const value = observation?.value;
  const current = observation?.state === "CURRENT";
  const connection = value?.online;
  const readable = connection ? connection[0].toUpperCase() + connection.slice(1).toLowerCase() : emptyLabel;
  const routine = ["ACTION_COMPLETED_REFRESH_REQUIRED", "OBSERVER_HIDDEN"].includes(observation?.reason ?? "");
  return {
    connection: readable,
    current: Boolean(current && connection),
    freshness: loading ? "Updating Cloud report" : current ? "Cloud report current" : value ? "Last known Cloud report" : "Cloud report not confirmed",
    lastKnown: Boolean(value && !current),
    attention: Boolean(!current && observation && !routine && !loading),
    reason: observation?.reason ?? undefined,
    observedAt: observation?.observedAt,
  };
}

export function capabilityLabel(profile: string | null | undefined) {
  return /^v[123]$/i.test(profile ?? "") ? `Capability ${profile!.toUpperCase()}` : profile ?? "Profile not confirmed";
}

export function publicationLabel(stage?: string | null) {
  return stage === "READY" ? "Published" : stage === "ACCEPTED" ? "Submitted · awaiting Cloud processing"
    : stage === "PROCESSING" ? "Processing in Cloud" : stage ? `Publication ${stage.toLowerCase()}` : "Awaiting publication report";
}

/** Describe this package, not a guessed delivery of whichever profile is selected. */
export function selectedPackageStatus(value: {
  prepared: boolean; submitted: boolean; stage?: string | null; installed: boolean;
  selectedVersion?: string; installedVersion?: string | null; installedCurrent: boolean;
  pendingVersion?: string | null; activePublication: boolean; assignmentAbsent: boolean;
}) {
  if (value.activePublication) return { title: "Publication in progress", detail: "Submitted once. Await the owning Cloud report; do not repeat publication." };
  if (value.installed) return { title: "Installed release confirmed by Cloud", detail: "This selected package is installed on the current Test." };
  if (!value.prepared) return { title: "Prepare a release to begin", detail: "Profile selection alone changes no installed software." };
  if (!value.submitted) return { title: "Ready to sign and publish", detail: "Prepared locally; not published or installed." };
  if (value.stage !== "READY") return { title: publicationLabel(value.stage), detail: "Installation is observed separately from publication." };
  if (value.assignmentAbsent) return { title: "Published", detail: "Not assigned to this Test. First assignment is a separate OEM action." };
  if (value.selectedVersion && value.pendingVersion === value.selectedVersion) return { title: "Published · delivery pending", detail: "Cloud reports this exact package as the pending target. Keep the last installed release visible." };
  return { title: "Published", detail: value.installedVersion
    ? `This Test ${value.installedCurrent ? "currently runs" : "last reported"} release ${value.installedVersion}. This selection is not an installation request.`
    : "No installation of this selected package has been confirmed. Refresh the installed inventory separately." };
}
