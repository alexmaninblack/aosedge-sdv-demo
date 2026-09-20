// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { useEffect, useState } from "react";
import { object, type ProductRow } from "./backendProduct";
import { sameInstance, time } from "./backendSelection";
import { readBrakeWindow } from "../../adapters/local/LocalPresenterReadAdapter";
import { recordingLabel, windowDeliveryLabel } from "./windowPresentation";
import { stamp } from "../../app/StudioReadViews";

type Sample = { sampleIndex: number; sourceTimestamp: string; phase: "PRE" | "ACTIVE" | "POST";
  speedKph: number; brakePedalPercent: number; longitudinalAccelerationMps2: number };
type Detail = { samples: Sample[]; window: Record<string, unknown> };
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$(?![\s\S])/;
export function validateWindowDetail(value: unknown, row: ProductRow): Detail {
  const data = object(value), window = object(data.window), message = row.message;
  const provenanceMatches = message.serviceInstance ? sameInstance(window.serviceInstance, message.serviceInstance)
    : typeof message.serviceArtifactSha256 === "string" && /^[a-f0-9]{64}$(?![\s\S])/.test(message.serviceArtifactSha256)
      && window.serviceArtifactSha256 === message.serviceArtifactSha256 && window.serviceInstance === undefined;
  if (data.schemaVersion !== 2 || data.contractVersion !== "2.0.0" || data.resourceType !== "WINDOW_DETAIL"
      || data.unitSystemUid !== message.unitSystemUid || data.unitRole !== "VALIDATION"
      || window.unitSystemUid !== message.unitSystemUid || window.eventId !== message.eventId
      || window.serviceVersion !== message.serviceVersion || !provenanceMatches
      || !Array.isArray(data.samples) || data.samples.length > 150) throw new Error("WINDOW_DETAIL_MISMATCH");
  let previous = -1, previousTime = -Infinity;
  for (const raw of data.samples) {
    const sample = object(raw), stamp = time(sample.sourceTimestamp);
    if (!Number.isSafeInteger(sample.sampleIndex) || Number(sample.sampleIndex) <= previous || !Number.isFinite(stamp)
        || stamp <= previousTime || !["PRE", "ACTIVE", "POST"].includes(String(sample.phase))
        || ![sample.speedKph, sample.brakePedalPercent, sample.longitudinalAccelerationMps2].every(v => typeof v === "number" && Number.isFinite(v))
        || Number(sample.brakePedalPercent) < 0 || Number(sample.brakePedalPercent) > 100 || Number(sample.speedKph) < 0)
      throw new Error("WINDOW_SAMPLES_INVALID");
    previous = Number(sample.sampleIndex); previousTime = stamp;
  }
  return { window, samples: data.samples as Sample[] };
}
const phaseColor = { PRE: "#9ba4b4", ACTIVE: "#7356ac", POST: "#238786" };
function Trace({ samples, field, label, unit }: { samples: Sample[]; field: "speedKph" | "brakePedalPercent"; label: string; unit: string }) {
  const first = samples.length ? time(samples[0].sourceTimestamp) : 0;
  const span = Math.max(1, (samples.length ? time(samples.at(-1)?.sourceTimestamp) : first) - first);
  const maximum = field === "brakePedalPercent" ? 100 : Math.max(1, ...samples.map(sample => sample[field]));
  return <div><small>{label} · {unit}</small><svg viewBox="0 0 320 72" role="img" aria-label={`${label}: actual retained samples`} style={{ width: "100%", height: 72 }}>
    <path d="M 30 6 V 52 H 312" fill="none" stroke="#aebdca" /><text x="2" y="14" fontSize="11">{Math.ceil(maximum)}</text><text x="14" y="54" fontSize="11">0</text>
    {samples.map(sample => <circle key={sample.sampleIndex} cx={30 + (time(sample.sourceTimestamp) - first) / span * 280} cy={52 - sample[field] / maximum * 42}
      r="2.5" fill={phaseColor[sample.phase]}><title>{`${sample.phase} · ${sample.sourceTimestamp} · ${sample[field]} ${unit}`}</title></circle>)}
    <text x="32" y="68" fontSize="11">0 s</text><text x="310" y="68" textAnchor="end" fontSize="11">{(span / 1000).toFixed(1)} s</text>
  </svg></div>;
}
export function BrakeWindowDetail({ row }: { row: ProductRow }) {
  const [state, setState] = useState<{ detail?: Detail; error?: boolean; checkedAt?: string }>({});
  const [refreshKey, refresh] = useState(0);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(globalThis.innerHeight <= 800 ? 3 : 5);
  useEffect(() => {
    const resize = () => { setPageSize(globalThis.innerHeight <= 800 ? 3 : 5); setPage(0); };
    globalThis.addEventListener("resize", resize);
    return () => globalThis.removeEventListener("resize", resize);
  }, []);
  const eventId = row.message.eventId;
  useEffect(() => {
    const controller = new AbortController(); let active = true;
    setState({}); setPage(0);
    if (typeof eventId !== "string" || !uuid.test(eventId)) { setState({ error: true }); return; }
    void (async () => {
      try {
        const detail = validateWindowDetail(await readBrakeWindow(eventId, controller.signal), row);
        if (active) setState({ detail, checkedAt: new Date().toISOString() });
      } catch { if (active) setState({ error: true }); }
    })();
    return () => { active = false; controller.abort(); };
  }, [eventId, row, refreshKey]);
  const header = <div className="studio-window-read"><small>Window snapshot · checked {stamp(state.checkedAt)}</small><button disabled={!state.detail && !state.error} onClick={() => refresh(value => value + 1)}>Refresh window</button></div>;
  if (state.error) return <>{header}<p role="status">Window detail unavailable or identity changed. No samples inferred.</p></>;
  if (!state.detail) return <>{header}<p role="status">Reading retained window…</p></>;
  const { samples, window } = state.detail;
  const counts = { PRE: 0, ACTIVE: 0, POST: 0 }; samples.forEach(sample => counts[sample.phase]++);
  const missingIndices = samples.reduce((total, sample, i) => total + (i ? Math.max(0, sample.sampleIndex - samples[i - 1].sampleIndex - 1) : sample.sampleIndex), 0);
  return <section className="studio-window-detail" aria-label="Retained braking window">
    {header}
    <div className="studio-window-outcome">
      <strong>{recordingLabel(window.terminalState)}</strong>
      <span>{windowDeliveryLabel(window)}</span>
      <small>{samples.length} retained samples · {missingIndices} missing sample indices</small>
      <small>Source status: <code>{String(window.terminalState ?? "NOT_REPORTED")}</code></small>
    </div>
    <div className="studio-metrics">{(["PRE", "ACTIVE", "POST"] as const).map(phase => <article key={phase}><small style={{ color: phaseColor[phase] }}>{phase}</small><strong>{counts[phase]}</strong></article>)}</div>
    <div className="studio-window-traces"><Trace samples={samples} field="speedKph" label="Speed" unit="km/h" /><Trace samples={samples} field="brakePedalPercent" label="Brake pedal" unit="%" /></div>
    <small>Actual source times; no resampling or interpolation. V1 acquires a window, not a condition score.</small>
    <table className="studio-window-samples"><thead><tr><th>Sample</th><th>Phase</th><th>Speed km/h</th><th>Brake %</th></tr></thead><tbody>{samples.slice(page * pageSize, page * pageSize + pageSize).map(sample => <tr key={sample.sampleIndex}><td>{sample.sampleIndex}</td><td>{sample.phase}</td><td>{sample.speedKph.toFixed(1)}</td><td>{sample.brakePedalPercent.toFixed(1)}</td></tr>)}</tbody></table>
    {samples.length > pageSize && <nav className="studio-pagination" aria-label="Window sample pages"><button disabled={page === 0} onClick={() => setPage(page - 1)}>Previous samples</button><span>{page + 1} / {Math.ceil(samples.length / pageSize)}</span><button disabled={(page + 1) * pageSize >= samples.length} onClick={() => setPage(page + 1)}>Next samples</button></nav>}
  </section>;
}
