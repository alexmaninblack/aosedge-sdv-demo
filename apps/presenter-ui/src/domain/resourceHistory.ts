// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import type { CloudSection } from "./platformObservation";
import { groupedMetrics, metricScope, type MetricSample } from "./studioModel";

export type Metric = CloudSection<MetricSample[]> & { unit?: string | null };
export type HistorySeries = Pick<MetricSample, "nodeId" | "serviceId" | "subjectId" | "instance"> & {
  metric: "cpu" | "ram"; unit: string | null; state: string; reason?: string | null;
  points: [string, number | null][];
};
export type ResourceRead = { unitId?: string; readCompletedAt?: string;
  monitoring?: CloudSection<Record<string, Metric>>;
  history?: CloudSection<{ series: HistorySeries[]; coverage: { fromTime?: string | null; toTime?: string | null; points: number; retention: string; conflicts: number } }> };
export const resourceIdentity = (sample: Pick<MetricSample, "nodeId" | "serviceId" | "subjectId" | "instance" | "partition" | "measurementType">) => JSON.stringify([
  sample.nodeId ?? null, sample.serviceId ?? null, sample.subjectId ?? null, sample.instance ?? null, sample.partition ?? null, sample.measurementType ?? null]);

/** Aliases are resolved per scope and partition, never as a response-wide fallback.
 * A disagreement is retained explicitly, not silently chosen or added. */
export function diskRows(metrics?: Record<string, Metric>) {
  const rows = new Map<string, { key: string; scope: string; sample: MetricSample; unit?: string | null; state: string; conflict: boolean; sources: string[] }>();
  for (const name of ["usedDisk", "disk"]) for (const { sample } of groupedMetrics(metrics?.[name]?.value ?? [])) {
    const key = resourceIdentity(sample), prior = rows.get(key), metric = metrics![name];
    if (!prior) rows.set(key, { key, scope: metricScope(sample), sample, unit: metric.unit, state: metric.state, conflict: false, sources: [name] });
    else {
      prior.sources.push(name);
      const same = prior.sample.value === sample.value && Date.parse(prior.sample.time ?? "") === Date.parse(sample.time ?? "") && prior.unit === metric.unit;
      if (!same) { prior.conflict = true; prior.state = "INCOMPLETE"; }
      else if (metric.state !== "CURRENT") prior.state = metric.state;
    }
  }
  return [...rows.values()];
}

/** Keep true sample instants; no interpolation, synthetic zero or refresh-time points. */
export function windowPoints(points: [string, number | null][], now: number, windowMs = 300000) {
  const unique = new Map<number, number | null>();
  for (const [time, value] of points) {
    const instant = Date.parse(time);
    if (!Number.isFinite(instant) || instant < now - windowMs || instant > now) continue;
    if (value !== null && (!Number.isFinite(value) || value < 0)) continue;
    unique.set(instant, unique.has(instant) && unique.get(instant) !== value ? null : value);
  }
  return [...unique].sort((a, b) => a[0] - b[0]);
}
