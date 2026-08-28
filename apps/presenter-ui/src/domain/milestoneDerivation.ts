import type { TeamView } from "./model";

export function deriveMilestone(platform: TeamView, brake: TeamView): string {
  const vdpReady = platform.releases.filter((release) => release.status.includes("Production ready")).length;
  const brakeReady = brake.releases.filter((release) => release.status.includes("Production ready")).length;
  const ready = Math.min(vdpReady, 1) + Math.min(brakeReady, 1);
  return `Platform and Brake release progress · ${ready} of 2 releases ready`;
}
