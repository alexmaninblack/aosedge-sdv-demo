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
