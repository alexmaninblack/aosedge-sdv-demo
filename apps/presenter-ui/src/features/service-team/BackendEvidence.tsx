import { useEffect, useRef, useState } from "react";
import { Modal } from "../../shared/components/Modal";
import { readBackendObservation } from "../../adapters/local/LocalPresenterReadAdapter";
import { ObservationTime } from "../../app/StudioReadViews";
import { completedProduct, productRows, type ProductRow, type Resource } from "./backendProduct";
import { usePresenterControls } from "../../app/state/PresenterControls";

type Team = "brake" | "tire";
type RecordRow = { backendReceivedAt: string; deliveryState?: string; stale?: boolean; message: {
  messageType?: string; serviceVersion?: string; unitSystemUid?: string;
  serviceInstance?: { serviceId?: string; subjectId?: string; instanceIndex?: number; instanceId?: string };
  content?: unknown; [key: string]: unknown;
} };
type MockData = { source: "DEMO_MOCK" | "VEHICLE_DATA"; vehicleTelemetry: boolean; unitSystemUid: string;
  counts: { kind?: string; message_type?: string; count: number }[]; records: RecordRow[] };
type Observation = { state: string; team: Team; source: "REAL_BACKEND_HTTP"; observedAt: string; recordsObservedAt?: string;
  observations: { readiness?: { state: string; reason?: string; data?: { ready?: boolean; reason?: string } };
    mockData?: { state: string; reason?: string; data?: MockData };
    demoReset?: { state: string; data?: { schemaVersion: number; unitSystemUid: string; connected: boolean;
      command: null | { commandId: string; unitSystemUid: string; state: string; issuedAt: string; expiresAt: string } } } } };

const recordObject = (value: unknown): Record<string, unknown> => value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
const readable = (value: unknown) => typeof value === "string" ? value.replaceAll("_", " ") : typeof value === "number" ? String(value) : "Not reported";
export function BackendEvidence({ team, unitSystemUid, expectedVersion, onEvidence, retiring = false }: { team: Team; unitSystemUid?: string; expectedVersion?: string; onEvidence?: (version: string) => void; retiring?: boolean }) {
  const controls = usePresenterControls();
  const [data, setData] = useState<Observation | null>(null);
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);
  const [generation, refresh] = useState(0);
  const [detail, setDetail] = useState<RecordRow | null>(null);
  const [tab, setTab] = useState("Overview");
  const [page, setPage] = useState(0);
  const [mockMode, setMockMode] = useState(false);
  const [pageSize, setPageSize] = useState(window.innerHeight <= 800 ? 1 : 2);
  useEffect(() => { const resize = () => { setPageSize(window.innerHeight <= 800 ? 1 : 2); setPage(0); }; window.addEventListener("resize", resize); return () => window.removeEventListener("resize", resize); }, []);
  const evidenceCallback = useRef(onEvidence);
  useEffect(() => { evidenceCallback.current = onEvidence; }, [onEvidence]);
  useEffect(() => {
    setData(null); setError(false); setDetail(null); setBusy(false); setPage(0); setMockMode(false);
  }, [team, unitSystemUid]);
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    const read = async () => {
      if (!unitSystemUid || !active) return;
      if (document.visibilityState !== "hidden") {
        setBusy(true);
        try {
          const value = await readBackendObservation(team, controller.signal) as Observation;
          const suppliedMock = value.observations?.mockData?.data;
          const reset = value.observations?.demoReset?.data;
          if (reset && (reset.schemaVersion !== 1 || reset.unitSystemUid !== unitSystemUid || typeof reset.connected !== "boolean"
              || (reset.command && (reset.command.unitSystemUid !== unitSystemUid || !["PENDING", "CLEARED", "EXPIRED", "FAILED", "REJECTED"].includes(reset.command.state))))) throw new Error("BACKEND_RESET_SCOPE_MISMATCH");
          if (value.team !== team || value.source !== "REAL_BACKEND_HTTP" || !value.observations
              || (suppliedMock && (suppliedMock.source !== "DEMO_MOCK" || suppliedMock.vehicleTelemetry !== false
                || suppliedMock.unitSystemUid !== unitSystemUid || !Array.isArray(suppliedMock.records) || !Array.isArray(suppliedMock.counts)
                || suppliedMock.records.some(row => row.message.unitSystemUid !== unitSystemUid)))) throw new Error("BACKEND_SCOPE_MISMATCH");
          if (!mockMode) {
            const resources = value.observations as unknown as Record<string, Resource>;
            const rows = productRows(resources, unitSystemUid);
            const names = team === "brake" ? ["productData", "assessments", "events", "advisories"] : ["assessments", "events", "advisories", "functionStatus"];
            const current = names.every(name => resources[name]?.state === "OBSERVED");
            value.observations.mockData = { state: current ? "OBSERVED" : "UNAVAILABLE", ...(current ? { data: {
              source: "VEHICLE_DATA" as const, vehicleTelemetry: true, unitSystemUid, records: rows, counts: [{ count: rows.length }],
            } } : {}) };
            value.state = current ? "OBSERVED" : "PARTIAL";
          }
          const mock = value.observations.mockData?.data;
          if (active) {
            setData(previous => ({ ...value, recordsObservedAt: value.observations.mockData?.state === "OBSERVED" && mock ? value.observedAt : previous?.recordsObservedAt, observations: { ...value.observations,
              mockData: value.observations.mockData?.data ? value.observations.mockData : { ...value.observations.mockData, state: value.observations.mockData?.state ?? "UNAVAILABLE", data: previous?.observations.mockData?.data } } }));
            setError(value.state !== "OBSERVED");
          }
        } catch { if (active) setError(true); }
        finally { if (active) setBusy(false); }
      }
      if (active) timer = setTimeout(read, 5000);
    };
    void read();
    return () => { active = false; controller.abort(); clearTimeout(timer); };
  }, [team, unitSystemUid, generation, mockMode]);
  const mock = data?.observations.mockData?.data;
  const reset = data?.observations.demoReset?.state === "OBSERVED" ? data.observations.demoReset.data : undefined;
  const resetCommand = !mockMode ? reset?.command : undefined;
  const submittingReset = controls.session?.jobs.some(job => job.id === controls.session?.active
    && job.action === "backend-reset" && job.team === team) ?? false;
  const currentRows = mock?.records.filter(row => {
    if (!resetCommand) return true;
    // Delivery time is not event time: an old queued result can arrive after
    // reset. Keep it in Records without presenting it as the new drive.
    const source = row.message.sourceEventTime ?? row.message.windowStartTimestamp ?? row.message.assessedAt ?? row.message.capturedAt ?? row.message.createdAt ?? row.message.observedAt;
    return typeof source === "string" && Date.parse(source) > Date.parse(resetCommand.issuedAt);
  });
  const available = !error && data?.observations.mockData?.state === "OBSERVED";
  const total = mock?.counts.reduce((sum, row) => sum + row.count, 0) ?? 0;
  const latest = expectedVersion ? currentRows?.find(row => row.message.serviceVersion === expectedVersion) : currentRows?.[0];
  const pages = Math.max(1, Math.ceil((mock?.records.length ?? 0) / pageSize));
  const currentPage = Math.min(page, pages - 1);
  const issue = data?.observations.mockData?.reason ?? data?.observations.readiness?.reason;
  const content = recordObject(latest?.message.content);
  const assessment = currentRows?.find(row => row.message.messageType === (team === "brake" ? "BRAKE_HEALTH_ASSESSMENT" : "TIRE_HEALTH_ASSESSMENT") && row.message.serviceVersion === expectedVersion);
  const assessmentContent = recordObject(assessment?.message.content);
  const resultMessage = assessment?.message ?? latest?.message;
  const resultContent = assessment ? assessmentContent : content;
  const confidence = team === "tire" && typeof resultContent.confidencePercent === "number";
  const sourceTime = resultMessage?.sourceEventTime ?? resultMessage?.windowStartTimestamp ?? resultMessage?.assessedAt ?? resultMessage?.capturedAt ?? resultMessage?.createdAt ?? resultMessage?.observedAt;
  const functionStatus = currentRows?.find(row => row.message.messageType === "TIRE_FUNCTION_STATUS" && row.message.serviceVersion === expectedVersion);
  const functionContent = recordObject(functionStatus?.message.content);
  useEffect(() => {
    if (!available || !expectedVersion || mock?.source !== "VEHICLE_DATA") return;
    const completed = mock?.records.find(row => row.message.serviceVersion === expectedVersion
      && completedProduct(row as ProductRow, expectedVersion));
    if (completed) evidenceCallback.current?.(expectedVersion);
  }, [available, expectedVersion, mock]);
  return <section className="studio-cloud" aria-label={`${team} backend evidence`}>
    <div className="studio-panel-title"><h2>Function backend</h2><button disabled={busy || !unitSystemUid} onClick={() => refresh(value => value + 1)}>Refresh backend</button></div>
    <p className="studio-stamp">{busy ? "Reading backend…" : !unitSystemUid ? "Current Test identity not observed in Cloud" : error ? `Backend unavailable or incomplete${mock ? " · records are last known" : " · no confirmed records"}${issue ? ` · ${issue}` : ""}` : <>Observed <ObservationTime value={data?.observedAt} /></>}</p>
    <div className="studio-mock-notice"><strong>{mockMode ? "MOCK DATA · Explicit synthetic test records" : "Vehicle data · Real service → real backend"}</strong><p>{mockMode ? "Synthetic inputs, not vehicle telemetry." : "Model assessments are DEMO SYNTHETIC estimates from vehicle signals, not production diagnoses."} Backend results do not establish current in-vehicle advisory.</p></div>
    <button className="studio-text-action" onClick={() => { setMockMode(value => !value); setData(null); setDetail(null); setPage(0); }}>{mockMode ? "Show vehicle results" : "Show mock history"}</button>
    {!mockMode && <div className="studio-reset-scenario"><button disabled={controls.blocked || retiring || busy || error || !unitSystemUid || !reset?.connected || resetCommand?.state === "PENDING"}
      onClick={() => controls.request({ action: "backend-reset", team })}>Reset demo scenario</button>
      <p role="status">{submittingReset ? "Resetting · submitting the current request"
        : resetCommand?.state === "PENDING" ? "Resetting · waiting for Gateway CLEAR confirmation"
        : resetCommand?.state === "CLEARED" ? "Scenario reset · Gateway confirmed CLEAR. Drive again to collect a new result."
        : resetCommand ? `Reset ${readable(resetCommand.state).toLowerCase()} · completion not confirmed`
        : !reset?.connected ? "Reset available when the compatible service connects." : "Start a new demo drive. History is retained; no vehicle repair is implied."}</p></div>}
    <div className="studio-pills">{["Overview", "Records"].map(name => <button key={name} aria-pressed={tab === name} onClick={() => setTab(name)}>{name}</button>)}</div>
    {tab === "Overview" && <>
    <div className="studio-metrics"><article><small>Backend process</small><strong>{!error && data?.observations.readiness?.state === "OBSERVED" && data.observations.readiness.data?.ready ? "Ready" : "Not confirmed"}</strong></article>
      <article><small>{mockMode ? "Mock messages" : "Recent product records"}{!available && mock ? " · last known" : ""}</small><strong>{mock ? total : "Not observed"}</strong></article>
      <article><small>Service release</small><strong>{latest?.message.serviceVersion ?? "Not reported"}</strong></article></div>
    {functionStatus && <p role="status">Function status{functionStatus.stale ? " · stale report" : " · service reported"}: {readable(functionContent.functionalState)} · {readable(functionContent.reason)}</p>}
    <div className="studio-result-card"><div><small>{mockMode ? "Latest mock result" : "Latest product result"}{!available && mock ? " · last known" : ""}</small><h3>{readable(assessmentContent.currentBand ?? assessmentContent.condition ?? content.status ?? latest?.message.messageType)}</h3>
      {expectedVersion && !latest && <p>{resetCommand?.state === "CLEARED" ? "Waiting for a new drive result after reset." : `No result for release ${expectedVersion} yet.`} Earlier results remain in Records.</p>}
      <p>{typeof content.receivedSampleCount === "number"
        ? `${content.receivedSampleCount} samples${typeof content.receivedChunkCount === "number"
          ? typeof content.expectedChunkCount === "number"
            ? ` · ${content.receivedChunkCount}/${content.expectedChunkCount} chunks`
            : ` · ${content.receivedChunkCount} chunks received · total pending`
          : ""}`
        : confidence ? `Confidence · ${resultContent.confidencePercent}%` : `Quality · ${readable(resultContent.quality)}`}</p></div>
      {typeof assessmentContent.conditionScore === "number" && <div className="studio-score"><strong>{assessmentContent.conditionScore}<small> / 100</small></strong><meter min={0} max={100} value={assessmentContent.conditionScore} aria-label="Synthetic condition score" /></div>}</div>
    <div className="studio-metrics"><article><small>Source event</small><strong>{typeof sourceTime === "string" ? new Date(sourceTime).toLocaleTimeString() : "Not reported"}</strong></article><article><small>Backend received</small><strong>{latest ? new Date((assessment ?? latest).backendReceivedAt).toLocaleTimeString() : "Not observed"}</strong></article><article><small>Vehicle advisory</small><strong>See vehicle telemetry</strong></article></div>
    {latest && <button className="studio-text-action" onClick={() => setDetail(assessment ?? latest)}>Inspect latest result ↗</button>}
    </>}
    {tab === "Records" && <>
    <h3 className="studio-evidence-title">Latest received records{!available && mock ? " · last known" : ""}</h3>
    <div className="studio-inventory">{mock?.records.slice(currentPage * pageSize, currentPage * pageSize + pageSize).map((row, index) => <button key={`${row.backendReceivedAt}-${index}`} onClick={() => setDetail(row)}>
      <strong>{row.message.messageType ?? "Product message"}</strong><span>Service {row.message.serviceVersion ?? "not reported"} · received {new Date(row.backendReceivedAt).toLocaleTimeString()}</span>
      <small>Current Test · {mockMode ? "mock history" : readable(row.deliveryState)}</small></button>)}</div>
    {pages > 1 && <nav className="studio-pagination" aria-label="Backend record pages"><button disabled={currentPage === 0} onClick={() => setPage(currentPage - 1)}>Previous</button><span>Page {currentPage + 1} of {pages} · {mock?.records.length} records</span><button disabled={currentPage + 1 >= pages} onClick={() => setPage(currentPage + 1)}>Next</button></nav>}
    {!mock?.records.length && <p>{available ? "No product records received from this Test service yet." : "No current backend evidence."}</p>}
    </>}
    {detail && <Modal title={mockMode ? "Mock product record" : "Backend product record"} subtitle={`${team === "brake" ? "Brake" : "Tire"} backend · Current Test`} onClose={() => setDetail(null)}>
      <dl className="detail-grid"><dt>Result</dt><dd>{readable(detail.message.messageType)}</dd><dt>Service release</dt><dd>{readable(detail.message.serviceVersion)}</dd><dt>Backend received</dt><dd>{new Date(detail.backendReceivedAt).toLocaleString()}</dd><dt>{team === "tire" ? "Confidence (%)" : "Quality"}</dt><dd>{readable(team === "tire" ? recordObject(detail.message.content).confidencePercent : recordObject(detail.message.content).quality)}</dd><dt>VDP contract</dt><dd>{readable(detail.message.vdpContractVersion)}</dd><dt>Provenance</dt><dd>{readable(recordObject(detail.message.content).provenance ?? detail.message.provenance)}</dd></dl>
      <details><summary>Record content and technical identifiers</summary><pre className="studio-details">{JSON.stringify(detail, null, 2)}</pre></details></Modal>}
  </section>;
}
