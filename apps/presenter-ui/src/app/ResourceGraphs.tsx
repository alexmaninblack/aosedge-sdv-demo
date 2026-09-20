// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { useEffect, useState } from "react";
import type { CloudInventory } from "../domain/platformObservation";
import { windowPoints, type HistorySeries } from "../domain/resourceHistory";
import { groupedMetrics, metricScope, type MetricSample } from "../domain/studioModel";
import { formatResource } from "../domain/resourceFormatting";
import type { CloudResourcesModel } from "./state/useCloudResources";
import { ObservationTime } from "./StudioReadViews";

type Scope = "controller" | "brake" | "tire";
function belongs(sample: Partial<MetricSample>, scope: Scope, inventory?: CloudInventory) {
  if (scope === "controller") return !sample.serviceId && !sample.subjectId && sample.instance == null && Boolean(sample.nodeId)
    && !!inventory?.nodes.value?.some(node => node.node_id === sample.nodeId);
  const id = inventory?.teamServiceIds?.[scope];
  if (!id || sample.serviceId !== id) return false;
  return !!inventory?.services.value?.some(row => row.service?.id === id && row.subject === sample.subjectId
    && row.instances.value?.some(instance => instance.instance_id === sample.instance));
}

export function selectGraph(model: CloudResourcesModel, inventory: CloudInventory | undefined, scope: Scope, metric: "cpu" | "ram") {
  const latest = model.data?.monitoring?.value?.[metric];
  const history = model.history?.data?.history;
  const allHistory = history?.value?.series?.filter(row => row.metric === metric) ?? [];
  const series = allHistory.filter(row => belongs(row, scope, inventory));
  const samples = groupedMetrics(latest?.value ?? []).map(row => row.sample).filter(sample => belongs(sample, scope, inventory));
  // Dashboard history omits latest-only measurementType/partition labels.
  // CPU/RAM ownership is the actual node/service/subject/allocation tuple.
  const identities = new Set([...series, ...samples].map(row => JSON.stringify([
    row.nodeId ?? null, row.serviceId ?? null, row.subjectId ?? null, row.instance ?? null,
  ])));
  const ambiguous = identities.size > 1;
  const points: HistorySeries["points"] = [];
  const unit = samples.length === 1 || latest && !series.length ? latest?.unit : series[0]?.unit;
  if (!ambiguous) {
    for (const row of series) if (row.unit === unit) points.push(...row.points);
    for (const sample of samples) if (sample.time) points.push([sample.time, sample.value]);
  }
  const conflicts = series.some(row => row.state !== "CURRENT");
  const latestSampleTime = Math.max(-Infinity, ...samples.map(row => Date.parse(row.time ?? "")).filter(Number.isFinite));
  const historyConfirmsValue = history?.state === "CURRENT" && !model.history?.error
    && series.some(row => row.state === "CURRENT" && row.points.some(([time, value]) => value !== null && Date.parse(time) >= latestSampleTime));
  return { points, unit, ambiguous, partial: conflicts,
    historyAvailable: !!history?.value && !model.history?.error,
    loading: !history && (!!model.history?.busy || !model.data && model.busy),
    stale: (model.error || latest?.state !== "CURRENT") && !historyConfirmsValue,
    unbound: [...allHistory, ...latest?.value ?? []].filter(row => metricScope({ value: null, time: null, ...row }) === "Service instance"
      && !belongs(row, "brake", inventory) && !belongs(row, "tire", inventory)).length > 0 };
}

function Graph({ model, inventory, scope, metric, now }: { model: CloudResourcesModel; inventory?: CloudInventory; scope: Scope; metric: "cpu" | "ram"; now: number }) {
  const selected = selectGraph(model, inventory, scope, metric);
  const points = windowPoints(selected.points, now);
  const latest = windowPoints(selected.points, now, Number.MAX_SAFE_INTEGER).filter(row => row[1] !== null).at(-1);
  const divisor = metric === "ram" && ["bytes", "B"].includes(selected.unit ?? "") ? 1048576 : 1;
  const unit = divisor > 1 ? "MiB" : selected.unit ?? "unit not verified";
  const max = Math.max(1, ...points.map(point => (point[1] ?? 0) / divisor));
  const scale = Number(max.toPrecision(3));
  const x = (time: number) => 8 + (time - (now - 300000)) / 300000 * 264;
  const y = (value: number) => 53 - value / divisor / max * 43;
  const label = metric === "cpu" ? "CPU" : "Memory";
  const sampleTime = latest ? new Date(latest[0]).toISOString() : undefined;
  const segments: number[][][] = [];
  let segment: number[][] = [];
  for (const [time, value] of points) {
    if (value === null || segment.length && time - segment.at(-1)![0] > 90000) { if (segment.length) segments.push(segment); segment = []; }
    if (value !== null) segment.push([time, value]);
  }
  if (segment.length) segments.push(segment);
  return <figure className="resource-graph" aria-label={`${scope} ${label} · last five minutes`}>
    <figcaption><span>{label} · {unit}</span><strong>{selected.ambiguous ? "Multiple instances" : latest ? formatResource(latest[1], selected.unit, metric) : "Not reported"}</strong></figcaption>
    <div className="resource-plot"><svg viewBox="0 0 280 62" role="img" aria-label={`${label} samples; scale zero to ${scale} ${unit}`}>
      <path d="M8 10H272 M8 53H272" className="resource-grid" />
      {segments.map((rows, index) => <g key={index}><polyline points={rows.map(([time, value]) => `${x(time)},${y(value)}`).join(" ")} />{rows.map(([time, value]) => <circle key={time} cx={x(time)} cy={y(value)} r="2"><title>{new Date(time).toLocaleString()} · {formatResource(value, selected.unit, metric)}</title></circle>)}</g>)}
    </svg>{!points.some(point => point[1] !== null) && <span className="resource-empty">{selected.ambiguous ? "Scope is ambiguous" : !inventory?.unitId ? "Provision Test to observe" : selected.loading ? "Loading history…" : "No samples in this interval"}</span>}</div>
    <div className="resource-axis"><span>{new Date(now - 300000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span><span>0–{scale} {unit}</span><span>{new Date(now).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span></div>
    <small>{latest ? <>{selected.stale || now - latest[0] > 90000 ? "Last known" : "Sample"} · <ObservationTime compact value={sampleTime} /></> : "No confirmed value"}
      {!selected.historyAvailable && !selected.loading ? " · history unavailable" : selected.partial ? " · partial history" : ""}</small>
  </figure>;
}

export function ResourceGraphs({ model, inventory, compact = false }: { model: CloudResourcesModel; inventory?: CloudInventory; compact?: boolean }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => { const timer = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(timer); }, []);
  return <section className={`resource-charts${compact ? " is-compact" : ""}`} aria-label={compact ? "Controller resources" : "CPU and memory history"}>
    {(compact ? ["controller"] as const : ["controller", "brake", "tire"] as const).map(scope => <div className="resource-row" data-team={scope === "controller" ? "platform" : scope} key={scope}>
      {!compact && <h4>{scope === "controller" ? "Domain Controller" : scope === "brake" ? "Brake Health" : "Tire Health"}</h4>}
      <div className="resource-pair">{(["cpu", "ram"] as const).map(metric => <Graph key={metric} model={model} inventory={inventory} scope={scope} metric={metric} now={now} />)}</div>
    </div>)}
    {!compact && <><p className="studio-function-stamp">Last five minutes · source timestamps · independent scales. Controller means the guest node, not this Mac. Instance history may span software updates.</p>
      {selectGraph(model, inventory, "controller", "cpu").unbound && <p role="status">Additional history is not bound to the current Brake/Tire instance; it is not attributed to either service.</p>}
      {model.history?.reason && <p role="status">History: {model.history.reason} Latest readings remain independent.</p>}</>}
  </section>;
}
