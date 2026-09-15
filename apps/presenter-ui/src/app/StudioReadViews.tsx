import { useEffect, useState } from "react";
import type { CloudComponent, CloudInventory, CloudSection, CloudService } from "../domain/platformObservation";
import { groupedMetrics, type MetricSample } from "../domain/studioModel";
import { readCloudMonitoring } from "../adapters/local/LocalPresenterReadAdapter";
import { componentIssue, serviceIssue, servicePending } from "../domain/softwareObservation";

export const known = (value: unknown): string => value === null || value === undefined ? "Not reported" : String(value);
export const stamp = (value: string | null | undefined) => {
  if (!value || !Number.isFinite(Date.parse(value))) return "Not observed";
  const date = new Date(value);
  return date.toDateString() === new Date().toDateString() ? date.toLocaleTimeString() : date.toLocaleString();
};
export function ObservationTime({ value }: { value?: string | null }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => { const timer = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(timer); }, []);
  const seconds = value ? Math.max(0, Math.floor((now - Date.parse(value)) / 1000)) : NaN;
  return <span title={value ?? undefined}>{stamp(value)}{Number.isFinite(seconds) ? ` · ${seconds < 60 ? `${seconds}s` : `${Math.floor(seconds / 60)}m`} ago` : ""}</span>;
}
export const componentName = (row: CloudComponent) => row.type?.endsWith("-vehicle-data-provider") ? "Vehicle Data Platform"
  : row.type?.endsWith("-rootfs") ? "Root filesystem" : row.type?.endsWith("-boot") ? "Boot firmware" : row.type ?? "Component";

export function ServiceRows({ rows, current = true, onSelect }: { rows?: CloudSection<CloudService[]>; current?: boolean; onSelect?: (row: CloudService) => void }) {
  const [page, setPage] = useState(0);
  const [instancePage, setInstancePage] = useState(0);
  const pages = Math.max(1, Math.ceil((rows?.value?.length ?? 0) / 2));
  const activePage = Math.min(page, pages - 1);
  if (!rows?.value) return <p>Service inventory: {rows?.reason ?? "Not reported"}</p>;
  if (!rows.value.length) return <p>{current && rows.state === "CURRENT" ? "No services reported by Cloud." : "Service inventory is incomplete; absence is not confirmed."}</p>;
  return <><div className={`studio-inventory${onSelect ? " studio-inventory-compact" : ""}`}>{rows.value.slice(activePage * 2, activePage * 2 + 2).map((row, index) => {
    const instances = row.instances.value;
    const instancePages = Math.max(1, Math.ceil((instances?.length ?? 0) / 4));
    const activeInstancePage = Math.min(instancePage, instancePages - 1);
    const count = row.num_instance ?? (row.instances.state === "CURRENT" ? instances?.length : undefined);
    const contents = <><strong>{row.service?.title ?? "Service"}</strong>
      <span>Installed {known(row.service_versions?.installed_service_version?.version)}{current && rows.state === "CURRENT" ? "" : " · last known"}</span>
      <small>{count === undefined || count === null ? "Instance count not reported" : `${count} ${count === 1 ? "instance" : "instances"}`}</small>
      {servicePending(row) && <span>Pending {row.service_versions?.pending_service_version?.version ?? "version not yet reported"}{row.service_versions?.pending_service_version_status ? ` · ${row.service_versions.pending_service_version_status}` : ""}</span>}
      {serviceIssue(row) && <span role="alert">Service update issue · {serviceIssue(row)}</span>}
      {(onSelect ? instances?.slice(0, 1) : instances?.slice(activeInstancePage * 4, activeInstancePage * 4 + 4))?.map((instance, n) => <small key={n}>Instance {known(instance.instance_id)} · {known(instance.version)} · {known(instance.run_state)}{!current || rows.state !== "CURRENT" || row.instances.state !== "CURRENT" ? " · last known" : ""}{instance.error_message ? ` · ${instance.error_message}` : ""}</small>)}
      {onSelect && instances && instances.length > 1 && <small>Open details for all {instances.length} instances ↗</small>}
      {!onSelect && instancePages > 1 && <nav className="studio-pagination" aria-label="Instance pages"><button disabled={activeInstancePage === 0} onClick={() => setInstancePage(activeInstancePage - 1)}>Previous instances</button><span>{activeInstancePage + 1} / {instancePages}</span><button disabled={activeInstancePage + 1 >= instancePages} onClick={() => setInstancePage(activeInstancePage + 1)}>Next instances</button></nav>}
      {row.instances.reason && <small>{row.instances.reason}</small>}
      {(row.reportReadCompletedAt || rows.lastKnownReadCompletedAt || rows.readCompletedAt) && <small>Cloud report · {stamp(row.reportReadCompletedAt ?? rows.lastKnownReadCompletedAt ?? rows.readCompletedAt)}</small>}
    </>;
    return onSelect ? <button key={row.service?.id ?? index} onClick={() => onSelect(row)}>{contents}</button> : <article key={row.service?.id ?? index}>{contents}</article>;
  })}</div>{pages > 1 && <nav className="studio-pagination" aria-label="Service pages"><button disabled={activePage === 0} onClick={() => setPage(activePage - 1)}>Previous services</button><span>{activePage + 1} / {pages}</span><button disabled={activePage + 1 >= pages} onClick={() => setPage(activePage + 1)}>Next services</button></nav>}</>;
}

export function ComponentDetails({ row, current }: { row: CloudComponent; current: boolean }) {
  return <><dl className="detail-grid"><dt>Component</dt><dd>{componentName(row)}</dd><dt>Installed release</dt><dd>{known(row.installed_component?.version)}{current ? "" : " · last known"}</dd>
    <dt>Pending release</dt><dd>{row.pending_component ? known(row.pending_component.version) : current ? "None reported" : "Not current"}</dd>
    <dt>Update state</dt><dd>{known(row.pending_component_status)}</dd>{componentIssue(row) && <><dt>Update issue</dt><dd role="alert">{componentIssue(row)}</dd></>}<dt>Process state</dt><dd>Not reported by Cloud</dd></dl>
    <details><summary>Technical identifiers</summary><dl className="detail-grid"><dt>Component ID</dt><dd>{known(row.reported_component_id)}</dd><dt>Type</dt><dd>{known(row.type)}</dd></dl></details></>;
}

type Metric = CloudSection<MetricSample[]> & { unit?: string | null };
type MonitoringRead = { unitId?: string; monitoring?: CloudSection<Record<string, Metric>>; readCompletedAt?: string };
export function Monitoring({ inventory, refreshKey }: { inventory?: CloudInventory; refreshKey?: number }) {
  const [data, setData] = useState<MonitoringRead | null>(null);
  const [error, setError] = useState(false);
  const [reason, setReason] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [scope, setScope] = useState("Controller");
  const [metricKey, setMetricKey] = useState("cpu");
  const [page, setPage] = useState(0);
  useEffect(() => setPage(0), [metricKey, scope, inventory?.unitId]);
  useEffect(() => { setData(null); setError(false); setReason(null); }, [inventory?.unitId]);
  useEffect(() => {
    let active = true;
    if (!inventory?.unitId || document.visibilityState === "hidden") return;
    setBusy(true);
    void readCloudMonitoring().then(value => {
      if (!active) return;
      const incoming = value as MonitoringRead;
      if (incoming.unitId !== inventory.unitId) { setData(null); setError(true); setReason("Cloud monitoring scope changed; refresh required."); }
      else if (incoming.monitoring?.state !== "CURRENT") {
        setError(true); setReason(incoming.monitoring?.reason ?? "Cloud monitoring unavailable");
        if (incoming.monitoring?.value) setData(incoming);
      } else { setData(incoming); setError(false); setReason(null); }
    }).catch(() => { if (active) { setError(true); setReason("Cloud monitoring read failed"); } }).finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, [inventory?.unitId, refreshKey]);
  const names: Record<string, string> = { cpu: "CPU", ram: "Memory", usedDisk: "Disk", inTraffic: "Inbound", outTraffic: "Outbound" };
  const metrics = data?.monitoring?.value;
  const allScopes = [...new Set(Object.values(metrics ?? {}).flatMap(metric => groupedMetrics(metric.value ?? []).map(row => row.scope)))];
  const selectedScope = allScopes.includes(scope) ? scope : allScopes[0] ?? scope;
  const metric = metrics?.[metricKey];
  const rows = groupedMetrics(metric?.value ?? []).filter(row => row.scope === selectedScope);
  const pages = Math.max(1, Math.ceil(rows.length / 3)), activePage = Math.min(page, pages - 1);
  return <section><div className="studio-panel-title"><h3>Resources</h3><span>Aos Cloud · {busy ? "Reading…" : error ? data ? `Last known · ${stamp(data.readCompletedAt)}` : "Unavailable" : stamp(data?.readCompletedAt)}</span></div>
    {reason && <p role="alert">{reason}{data ? " · Previous samples retained." : " · No confirmed samples."}</p>}
    <div className="studio-pills" role="group" aria-label="Resource scope">{allScopes.map(name => <button key={name} aria-pressed={selectedScope === name} onClick={() => setScope(name)}>{name}</button>)}</div>
    <div className="studio-profile-cards">{Object.entries(names).map(([key, name]) => <button key={key} aria-pressed={key === metricKey} onClick={() => setMetricKey(key)}>{name}</button>)}</div>
    <div className="studio-inventory">{rows.slice(activePage * 3, activePage * 3 + 3).map(({ key, sample }) => <article key={key}><strong>{names[metricKey]} · {selectedScope}</strong>
      <span>{known(sample.value)} {sample.value !== null ? metric?.unit ?? "· unit not specified" : ""}{error || metric?.state !== "CURRENT" ? " · last known" : ""}</span>
      <small>{sample.serviceId ? inventory?.services.value?.find(row => row.service?.id === sample.serviceId)?.service?.title ?? sample.serviceId : sample.nodeId ?? "Scope not supplied by Cloud"}{sample.instance !== null && sample.instance !== undefined ? ` · instance ${sample.instance}` : ""}{sample.partition ? ` · ${sample.partition}` : ""}</small>
      <small>Sample {stamp(sample.time)} · read {stamp(data?.readCompletedAt)}</small></article>)}</div>
    {pages > 1 && <nav className="studio-pagination" aria-label="Resource pages"><button disabled={activePage === 0} onClick={() => setPage(activePage - 1)}>Previous samples</button><span>{activePage + 1} / {pages}</span><button disabled={activePage + 1 >= pages} onClick={() => setPage(activePage + 1)}>Next samples</button></nav>}
    {!rows.length && !reason && <p>{!inventory?.unitId ? "Create and provision Test to observe Cloud resources." : metric?.reason ?? "No sample reported for this scope."}</p>}
    {metric && !metric.unit && <p>Cloud has not supplied a verified unit. Values are shown unchanged, not converted to percentages or byte units.</p>}
  </section>;
}
