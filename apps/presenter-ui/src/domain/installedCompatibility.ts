// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import type { InstalledProfile } from "./platformObservation";

/** Cloud/package installation evidence only. Never a telemetry health check. */
export function confirmedInstalledProfile(evidence: InstalledProfile | null | undefined,
  version: string | null | undefined, versionId?: string | null): InstalledProfile | null {
  if (!evidence || !version || evidence.releaseVersion !== version || !evidence.cloudVersionId
      || (versionId !== undefined && evidence.cloudVersionId !== versionId)
      || evidence.source !== "CLOUD_INSTALLATION_AND_PACKAGE"
      || !["CURRENT", "STALE"].includes(evidence.state)
      || !["v1", "v2", "v3"].includes(evidence.profile ?? "")) return null;
  return evidence;
}

export function installedCompatibility(evidence: InstalledProfile | null,
  team: "brake" | "tire" | undefined, serviceProfile: string | undefined, current: boolean) {
  const required = team === "brake" && ["v1", "v2", "v3"].includes(serviceProfile ?? "")
    ? serviceProfile! : team === "tire" && serviceProfile === "v1" ? "v3" : null;
  if (!required || !evidence || !confirmedInstalledProfile(evidence, evidence.releaseVersion))
    return { state: "UNKNOWN" as const, required, actual: null, compatible: null };
  return { state: current && evidence.state === "CURRENT" ? "CURRENT" as const : "STALE" as const,
    required, actual: evidence.profile,
    compatible: Number(evidence.profile!.slice(1)) >= Number(required.slice(1)) };
}
