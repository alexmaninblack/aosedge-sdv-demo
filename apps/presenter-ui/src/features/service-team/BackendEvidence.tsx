import { Fragment, useEffect, useLayoutEffect, useRef, useState } from "react";
import { Modal } from "../../shared/components/Modal";
import { useBackendObservation, backendSummary, recordObject, readable, type BackendModel, type RecordRow, type Team } from "./useBackendObservation";
import { ObservationTime, stamp } from "../../app/StudioReadViews";
import { isProductResult, productSourceTime } from "./backendProduct";
import type { BackendBinding } from "./backendSelection";
import { BrakeWindowDetail } from "./BrakeWindowDetail";
import { ResetScenario, useResetScenario } from "./ResetScenario";
import { backendLabel } from "./backendLanguage";

export function BackendEvidence({ team, unitSystemUid, expectedVersion, binding, onEvidence, retiring = false, observation, runId, unavailableReason }: { team: Team; unitSystemUid?: string; expectedVersion?: string; binding?: BackendBinding; onEvidence?: (version: string) => void; retiring?: boolean; observation?: BackendModel; runId?: string | null; unavailableReason?: string }) {
  const [detail, setDetail] = useState<RecordRow | null>(null);
  const [tab, setTab] = useState("Overview");
  const [page, setPage] = useState(0);
  const [recordFilter, setRecordFilter] = useState("all");
  const [releaseFilter, setReleaseFilter] = useState("current");
  const [mockMode, setMockMode] = useState(false);
  const [pageSize, setPageSize] = useState(globalThis.innerHeight <= 800 ? 3 : 8);
  useEffect(() => {
    const resize = () => { setPageSize(globalThis.innerHeight <= 800 ? 3 : 8); setPage(0); };
    globalThis.addEventListener("resize", resize);
    return () => globalThis.removeEventListener("resize", resize);
  }, []);
  const integrated = Boolean(observation);
  const evidenceRoot = useRef<HTMLElement>(null);
  const returnView = useRef<{ scroll: number; key: string } | null>(null);
  const inspectRecord = (row: RecordRow, key: string) => {
    returnView.current = { scroll: evidenceRoot.current?.closest(".modal-body")?.scrollTop ?? 0, key };
    setDetail(row);
  };
  useLayoutEffect(() => {
    if (!integrated) return;
    const scroller = evidenceRoot.current?.closest(".modal-body");
    if (scroller) scroller.scrollTop = detail ? 0 : returnView.current?.scroll ?? scroller.scrollTop;
    if (!detail && returnView.current) {
      const key = returnView.current.key;
      const origin = Array.from(evidenceRoot.current?.querySelectorAll<HTMLButtonElement>("button[data-record-ref]") ?? []).find(button => button.dataset.recordRef === key);
      origin?.focus({ preventScroll: true }); returnView.current = null;
    }
  }, [detail, integrated]);
  const localObservation = useBackendObservation(team, unitSystemUid, !observation || mockMode, mockMode);
  const model = mockMode || !observation ? localObservation : observation;
  const { data, error, busy, refresh } = model;
  const summary = backendSummary(model, team, expectedVersion, binding);
  const resetStatus = useResetScenario(team, model, binding, retiring, runId, unavailableReason);
  const evidenceCallback = useRef(onEvidence);
  useEffect(() => { evidenceCallback.current = onEvidence; }, [onEvidence]);
  useEffect(() => {
    setDetail(null); setPage(0); setMockMode(false); setRecordFilter("all"); setReleaseFilter("current");
  }, [team, unitSystemUid]);
  const mock = data?.observations.mockData?.data;
  const reset = data?.observations.demoReset?.state === "OBSERVED" ? data.observations.demoReset.data : undefined;
  const available = mockMode ? !error && data?.observations.mockData?.state === "OBSERVED" : summary.available;
  const total = mock?.counts.reduce((sum, row) => sum + row.count, 0) ?? 0;
  const latest = mockMode ? mock?.records[0] : resetStatus.pending || resetStatus.uncertain ? undefined : summary.result;
  const records = (mock?.records ?? []).filter(row => (recordFilter !== "windows" || row.message.messageType === "WINDOW_COMPLETION")
    && (mockMode || !expectedVersion || releaseFilter === "all" || (releaseFilter === "current" ? row.message.serviceVersion === expectedVersion : row.message.serviceVersion !== expectedVersion)));
  const hasWindows = mock?.records.some(row => row.message.messageType === "WINDOW_COMPLETION");
  const pages = Math.max(1, Math.ceil(records.length / pageSize));
  const currentPage = Math.min(page, pages - 1);
  const issue = data?.observations.mockData?.reason ?? data?.observations.readiness?.reason;
  const content = recordObject(latest?.message.content);
  const resultConflict = !mockMode && summary.integrityConflict;
  const assessment = !resultConflict && latest?.message.messageType === (team === "brake" ? "BRAKE_HEALTH_ASSESSMENT" : "TIRE_HEALTH_ASSESSMENT") ? latest : undefined;
  const assessmentContent = recordObject(assessment?.message.content);
  const resultMessage = assessment?.message ?? latest?.message;
  const resultContent = assessment ? assessmentContent : content;
  const confidence = team === "tire" && typeof resultContent.confidencePercent === "number";
  const sourceTime = resultMessage ? productSourceTime({ backendReceivedAt: "", message: resultMessage }) : undefined;
  const functionStatus = mock?.records.find(row => row.message.messageType === "TIRE_FUNCTION_STATUS" && row.message.serviceVersion === expectedVersion);
  const functionContent = recordObject(functionStatus?.message.content);
  const fn = summary.functional, facts = fn.item?.message.content;
  const functionKnown = fn.state === "CURRENT";
  const explanation = team === "brake" && (binding?.profile === "v1" || latest?.message.messageType === "WINDOW_COMPLETION")
    ? "Retained vehicle telemetry · V1 records braking windows, not a condition estimate."
    : "Demo model estimates from vehicle signals, not production diagnoses.";
  const compactExplanation = team === "brake" && (binding?.profile === "v1" || latest?.message.messageType === "WINDOW_COMPLETION")
    ? "V1 source recording · no condition estimate." : "Demo model estimate · not a diagnosis.";
  useEffect(() => {
    if (!mockMode && summary.proof) evidenceCallback.current?.(summary.proof);
  }, [mockMode, summary.proof]);
  if (detail && observation) return <section ref={evidenceRoot} className="studio-record-detail" aria-label={`${team} record details`}>
    <header className="studio-record-breadcrumb"><button className="studio-text-action" onClick={() => setDetail(null)}>← Back to {team === "brake" ? "Brake" : "Tire"} backend</button><h3>{mockMode ? "Mock product record" : "Backend product record"}</h3></header>
    {!mockMode && team === "brake" && detail.message.messageType === "WINDOW_COMPLETION" ? <BrakeWindowDetail row={detail} /> : <ProductRecordDetails row={detail} />}
    <details><summary>Record content and technical identifiers</summary><pre className="studio-details">{JSON.stringify(detail, null, 2)}</pre></details>
  </section>;
  if (!unitSystemUid && !binding?.unitSystemUid) return <section className="studio-cloud" aria-label={`${team} backend evidence`}><p>Current Test identity not observed in Cloud</p><p>Create and provision Test, then install {team === "brake" ? "Brake" : "Tire"} Health. No vehicle data is expected before setup.</p></section>;
  return <section ref={evidenceRoot} className={`studio-cloud${observation ? " is-dialog-content" : ""}`} aria-label={`${team} backend evidence`}>
    <div className="studio-panel-title">{!observation && <h2>Function backend</h2>}<button disabled={busy || !unitSystemUid} onClick={refresh}>Refresh backend</button></div>
    <p className="studio-stamp">{busy ? "Reading backend…" : !unitSystemUid ? "Current Test identity not observed in Cloud" : error ? `Backend unavailable or incomplete${mock ? " · records are last known" : " · no confirmed records"}${issue ? ` · ${issue}` : ""}` : <>Backend checked <ObservationTime value={data?.observedAt} />{!mockMode && <> · Reset channel contact: {!reset ? "not observed" : reset.connected ? "recent" : "not recent"}</>}</>}</p>
    {!!data?.partialResources?.length && <p className="studio-function-stamp" role="status">Partial backend read · {data.partialResources.join(", ")} unavailable. Independent facts retained.</p>}
    <div className="studio-mock-notice"><strong>{mockMode ? "MOCK DATA · Explicit synthetic test records" : resultConflict ? "Vehicle record · integrity conflict" : latest ? "Vehicle data · retained service result" : "Configured data path · service → backend"}</strong><p>{mockMode ? "Synthetic inputs, not vehicle telemetry." : observation ? compactExplanation : `${explanation} Backend results do not establish current in-vehicle advisory.`}</p></div>
    {(!observation || tab === "Records") && <details className="studio-engineering-history"><summary>Engineering history</summary><p>Synthetic records are separate test inputs, not vehicle evidence.</p><button className="studio-text-action" onClick={event => { setMockMode(value => !value); setDetail(null); setPage(0); setRecordFilter("all"); const disclosure = event.currentTarget.closest("details"); if (disclosure) disclosure.open = false; evidenceRoot.current?.querySelector<HTMLButtonElement>('[data-backend-tab="Records"]')?.focus(); }}>{mockMode ? "Show vehicle results" : "Show mock history"}</button></details>}
    {!mockMode && (summary.resetState !== "HISTORICAL" || tab === "Records") && <ResetScenario action={false} team={team} model={model} binding={binding} retiring={retiring} runId={runId} unavailableReason={unavailableReason} />}
    <div className="studio-pills">{["Overview", "Records"].map(name => <button key={name} data-backend-tab={name} aria-pressed={tab === name} onClick={() => setTab(name)}>{name}</button>)}</div>
    {tab === "Overview" && <>
    {mockMode ? <div className="studio-metrics"><article><small>Backend process</small><strong>{!error && data?.observations.readiness?.state === "OBSERVED" && data.observations.readiness.data?.ready ? "Ready" : "Not confirmed"}</strong></article>
      <article><small>{mockMode ? "Mock messages" : "Retained records"}{!available && mock ? " · last known" : ""}</small><strong>{mock ? total : "Not observed"}</strong></article>
      <article><small>Service release</small><strong>{expectedVersion ?? latest?.message.serviceVersion ?? "Not reported"}</strong></article></div>
      : <><h3>Now</h3><div className="studio-metrics" aria-label="Service function observation"><article><small>Input</small><strong>{functionKnown ? backendLabel(facts?.input.state, "input") : "Not confirmed"}</strong><small>{functionKnown ? backendLabel(facts?.input.reason) : readable(fn.state)}</small></article>
        <article><small>Analysis</small><strong>{functionKnown ? backendLabel(facts?.activity.state, "activity") : "Not confirmed"}</strong><small>{functionKnown ? backendLabel(facts?.activity.reason) : "No current function report"}</small></article>
        <article><small>Delivery</small><strong>{functionKnown ? backendLabel(facts?.delivery.state, "delivery") : "Not confirmed"}</strong><small>{functionKnown ? `${facts?.delivery.queuedMessages} queued` : "Last receipt is not live input"}</small></article></div>
        {fn.item && <small className="studio-function-stamp">Function report · {readable(fn.state)} · source <ObservationTime value={fn.item.message.observedAt} /> · received <ObservationTime value={fn.item.backendReceivedAt} /></small>}</>}
    {functionStatus && !fn.item && <p role="status">Legacy function report{functionStatus.stale ? " · stale report" : " · historical"}: {readable(functionContent.functionalState)} · {readable(functionContent.reason)}</p>}
    <div className="studio-result-card"><div><small>{mockMode ? "Latest mock result" : "Last assessment / recording"}{(mockMode ? !available && mock : summary.lastKnown) ? " · last known" : ""}</small><h3>{!mockMode && resetStatus.waiting ? "Resetting driver advisory…" : latest ? mockMode ? readable(assessmentContent.currentBand ?? assessmentContent.condition ?? content.status ?? latest.message.messageType) : summary.title : ["CLEARED", "PENDING", "UNCERTAIN"].includes(summary.resetState) ? summary.title : busy && !data || error && !data ? "Assessment not confirmed" : "No result yet"}</h3>
      {!mockMode && !latest && <>{expectedVersion && !["PENDING", "UNCERTAIN"].includes(summary.resetState) && <small>{summary.resetState === "CLEARED" ? `No new result for release ${expectedVersion} after the confirmed reset.` : `No result for release ${expectedVersion} yet.`}</small>}<p>{summary.guidance}</p>{summary.continuityNote && <p>{summary.continuityNote}</p>}{Boolean(mock?.records.length) && summary.resetState !== "UNCERTAIN" && <small>{mock?.records.some(row => isProductResult(row, team)) ? "Earlier results remain in Records." : "Service records remain in Records."}</small>}</>}
      {resultConflict && <p role="alert">{summary.guidance}</p>}
      {latest && !resultConflict && <p>{typeof content.receivedSampleCount === "number"
        ? `${content.receivedSampleCount} samples${typeof content.receivedChunkCount === "number"
          ? typeof content.expectedChunkCount === "number"
            ? ` · ${content.receivedChunkCount}/${content.expectedChunkCount} chunks`
            : ` · ${content.receivedChunkCount} chunks received · total pending`
          : ""}`
        : confidence ? `Confidence · ${resultContent.confidencePercent}%` : `Quality · ${readable(resultContent.quality)}`}</p>}</div>
      {typeof assessmentContent.conditionScore === "number" && <div className="studio-score"><strong>{assessmentContent.conditionScore}<small> / 100</small></strong><meter className="studio-neutral-score" min={0} max={100} value={assessmentContent.conditionScore} aria-label="Demo model condition score" /></div>}</div>
    <div className="studio-result-times"><span>Source event · <strong>{typeof sourceTime === "string" ? stamp(sourceTime) : "Not reported"}</strong></span><span>Backend received · <strong>{latest ? stamp((assessment ?? latest).backendReceivedAt) : "Not observed"}</strong></span></div>
    <p className="studio-function-stamp">Vehicle advisory · <span>See vehicle telemetry</span>{functionKnown && facts && <> · Service ACK: {readable(facts.advisory.state)}{facts.advisory.state === "CONFIRMED" && !latest ? " · a confirmed ACK may clear or activate a warning" : ""}</>}</p>
    {latest && <button className="studio-text-action" data-record-ref="latest" onClick={() => inspectRecord(assessment ?? latest, "latest")}>Inspect latest result ↗</button>}
    {!mockMode && team === "brake" && hasWindows && <button className="studio-text-action" onClick={() => { setTab("Records"); setRecordFilter("windows"); setReleaseFilter("all"); setPage(0); }}>View braking recordings & charts ↗</button>}
    </>}
    {tab === "Records" && <>
    <h3 className="studio-evidence-title">Receipt history{!available && mock ? " · last known" : ""}</h3><small>{mock ? total : busy ? "Reading" : "No"} retained records in this bounded read</small>
    {!mockMode && <label className="studio-record-filter">Service release <select aria-label="Service release" value={releaseFilter} onChange={event => { setReleaseFilter(event.target.value); setPage(0); }}><option value="current">Current release</option><option value="earlier">Earlier releases</option><option value="all">All releases</option></select></label>}
    {team === "brake" && <label className="studio-record-filter">Record type <select aria-label="Record type" value={recordFilter} onChange={event => { setRecordFilter(event.target.value); setPage(0); }}><option value="all">All records</option><option value="windows">Braking recordings & charts</option></select></label>}
    <div className="studio-inventory studio-record-list">{records.slice(currentPage * pageSize, currentPage * pageSize + pageSize).map((row, index) => <button key={`${row.backendReceivedAt}-${index}`} data-record-ref={String(index)} onClick={() => inspectRecord(row, String(index))}>
      <strong>{backendLabel(row.message.messageType ?? "Product message")}</strong><span>Release {row.message.serviceVersion ?? "not reported"} · {stamp(row.backendReceivedAt)}</span>
      <small>{mockMode ? "Mock history" : backendLabel(row.deliveryState)}</small></button>)}</div>
    {pages > 1 && <nav className="studio-pagination" aria-label="Backend record pages"><button disabled={currentPage === 0} onClick={() => setPage(currentPage - 1)}>Previous</button><span>Page {currentPage + 1} of {pages} · {records.length} records</span><button disabled={currentPage + 1 >= pages} onClick={() => setPage(currentPage + 1)}>Next</button></nav>}
    {!records.length && <p>{busy && !data ? "Reading backend history…" : error && !data ? "Backend history unavailable." : recordFilter === "windows" ? "No braking recordings in this bounded history read." : available ? "No product records in this release view." : "No current backend evidence."}</p>}
    </>}
    {detail && !observation && <Modal title={mockMode ? "Mock product record" : "Backend product record"} subtitle={`${team === "brake" ? "Brake" : "Tire"} backend · Current Test`} accent={team} onClose={() => setDetail(null)}>
      {!mockMode && team === "brake" && detail.message.messageType === "WINDOW_COMPLETION" ? <BrakeWindowDetail row={detail} />
        : <ProductRecordDetails row={detail} />}
      <details><summary>Record content and technical identifiers</summary><pre className="studio-details">{JSON.stringify(detail, null, 2)}</pre></details></Modal>}
  </section>;
}

export function ProductRecordDetails({ row }: { row: RecordRow }) {
  const content = recordObject(row.message.content);
  const fields: [string, unknown][] = [["Condition", content.currentBand ?? content.condition], ["Previous condition", content.previousBand],
    ["Condition score", content.conditionScore], ["Recommendation", content.recommendation], ["Operation", content.operation], ["Event", content.eventType],
    ["Reason", content.reasonCode], ["Quality", content.quality], ["Confidence (%)", content.confidencePercent]];
  const source = productSourceTime(row);
  return <dl className="detail-grid"><dt>Record type</dt><dd>{readable(row.message.messageType)}</dd>
    <dt>Delivery integrity</dt><dd>{readable(row.deliveryState)}{row.deliveryState === "CONFLICT" ? " · record content is not a confirmed result" : ""}</dd>
    {fields.filter(([, value]) => value !== undefined && value !== null).map(([label, value]) => <Fragment key={label}><dt>{label}</dt><dd>{readable(value)}</dd></Fragment>)}
    <dt>Service release</dt><dd>{readable(row.message.serviceVersion)}</dd><dt>Source event</dt><dd>{stamp(typeof source === "string" ? source : null)}</dd>
    <dt>Backend received</dt><dd>{stamp(row.backendReceivedAt)}</dd><dt>VDP contract</dt><dd>{readable(row.message.vdpContractVersion)}</dd><dt>Provenance</dt><dd>{readable(content.provenance ?? row.message.provenance)}</dd></dl>;
}
