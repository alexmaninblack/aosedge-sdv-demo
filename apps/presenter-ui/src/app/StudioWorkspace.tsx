import { useEffect, useState } from "react";
import type { Perspective, PresenterSnapshot } from "../domain";
import type { CloudSection, CloudService } from "../domain/platformObservation";
import { usePlatformObservation } from "./state/PresenterReadModelProvider";
import { OperationProgress, usePresenterControls } from "./state/PresenterControls";
import { Modal } from "../shared/components/Modal";
import { readCloudMonitoring } from "../adapters/local/LocalPresenterReadAdapter";
import { BackendEvidence } from "../features/service-team/BackendEvidence";
import "../shared/design-tokens/studio.css";

export type StudioIconName = "vehicle" | "platform" | "brake" | "tire" | "cloud" | "gateway" | "component" | "service";
export function StudioIcon({ name }: { name: StudioIconName }) { return <span aria-hidden="true" className={`b2-icon b2-${name}`} />; }
const known = (value: unknown): string => value === null || value === undefined ? "Not reported" : String(value);
const stamp = (value: string | null | undefined) => value ? new Date(value).toLocaleTimeString() : "Not observed";

function ServiceRows({ rows }: { rows?: CloudSection<CloudService[]> }) {
  if (!rows?.value) return <p>Service inventory: {rows?.reason ?? "Not reported"}</p>;
  if (!rows.value.length) return <p>{rows.state === "CURRENT" ? "No services reported by Cloud." : "Service inventory is incomplete; absence is not confirmed."}</p>;
  return <div className="studio-inventory">{rows.state !== "CURRENT" && <p>Service inventory · {rows.state} · {rows.reason ?? "Refresh required"}</p>}{rows.value.map((row, index) => <article key={row.service?.id ?? index}>
    <strong>{row.service?.title ?? row.service?.id ?? "Service"}</strong>
    <span>Installed {known(row.service_versions?.installed_service_version?.version)} · Instances {known(row.num_instance)}</span>
    {row.service_versions?.pending_service_version && <span>Pending {known(row.service_versions.pending_service_version.version)}</span>}
    {row.instances.value?.map((instance, n) => <small key={instance.instance_id ?? n}>Instance {known(instance.instance_id)} · {known(instance.version)} · {known(instance.run_state)}{instance.error_message ? ` · ${instance.error_message}` : ""}</small>)}
  </article>)}</div>;
}

function Monitoring({ unitId, refreshKey }: { unitId?: string; refreshKey?: number }) {
  type Metric = CloudSection<{ value: number | null; time: string | null; parameter: string | null }[]> & { unit?: string | null };
  type Read = { unitId?: string; monitoring?: CloudSection<Record<string, Metric>>; readCompletedAt?: string };
  const [data, setData] = useState<Read | null>(null);
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);
  // This view issues only the fixed Cloud monitoring read, never a guest probe.
  useEffect(() => {
    let active = true;
    if (!unitId || document.visibilityState === "hidden") { setData(null); return; }
    setBusy(true);
    void readCloudMonitoring()
      .then((value) => { if (active) {
        const incoming = value as Read;
        if (incoming.unitId !== unitId) { setData(null); setError(true); }
        else { setData(incoming); setError(false); }
      } })
      .catch(() => { if (active) setError(true); }).finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, [unitId, refreshKey]);
  return <section><h3>Resources · Aos Cloud</h3><p className="studio-stamp">{busy ? "Reading Cloud monitoring…" : error ? "Monitoring unavailable" : `Observed ${stamp(data?.readCompletedAt)}`}</p>
    <div className="studio-metrics">{["cpu", "ram", "usedDisk", "inTraffic", "outTraffic"].map((key) => {
      const metric = data?.monitoring?.value?.[key];
      const samples = metric?.value ?? [];
      const latest = [...samples].sort((a, b) => (a.time ?? "").localeCompare(b.time ?? "")).at(-1);
      const stale = error || data?.monitoring?.state !== "CURRENT" || metric?.state !== "CURRENT";
      return <article key={key}><small>{({ cpu: "CPU", ram: "Memory", usedDisk: "Disk", inTraffic: "Inbound", outTraffic: "Outbound" } as Record<string, string>)[key]}{latest && stale ? " · last known" : ""}</small>
        <strong>{known(latest?.value)} {latest?.value !== null && latest?.value !== undefined ? metric?.unit ?? "(raw; unit unverified)" : ""}</strong><small>{latest?.time ? stamp(latest.time) : metric?.reason ?? "No sample reported"}</small></article>;
    })}</div></section>;
}

export function StudioWorkspace({ snapshot, perspective, navigate }: { snapshot: PresenterSnapshot; perspective: Perspective; navigate: (value: Perspective) => void }) {
  const controls = usePresenterControls();
  const cloud = usePlatformObservation();
  const local = snapshot.localDemo!;
  const [mode, setMode] = useState("story");
  const [selectedImage, setSelectedImage] = useState("");
  const [profile, setProfile] = useState<"v1" | "v2" | "v3">("v1");
  const [details, setDetails] = useState<"vdp" | "services" | "cloud" | null>(null);
  const [monitor, setMonitor] = useState(false);
  const vehicle = local.vehicles.test;
  const present = vehicle.state === "CURRENT" && vehicle.overlayExists === true;
  // A retained Test may use a different image from the shared Production
  // backing or the first catalog row. Never display a selectable replacement.
  const image = present ? local.images.find((item) => item.version === vehicle.imageVersion)?.selector ?? ""
    : (mode === "quick" ? local.preparation?.image : local.lifecycle?.image) || selectedImage || local.images[0]?.selector || "";
  const value = cloud.observation?.value;
  const inventory = value?.inventory;
  const current = cloud.observation?.state === "CURRENT";
  const componentCurrent = current && (!inventory || inventory.components.state === "CURRENT");
  const connected = snapshot.vehicle.value === "test";
  const jobs = (controls.session?.jobs ?? []).filter((job) => local.runId && job.runId === local.runId);
  const continuation = mode === "quick" ? Boolean(local.preparation && local.preparation.phase !== "READY_TO_DRIVE")
    : local.lifecycle?.action === "create" && local.lifecycle.state !== "COMPLETED";
  const candidate = [...jobs].reverse().find((job) => job.action === "prepare" && job.profile === profile && job.state === "COMPLETED" && job.version);
  const saved = [...local.candidates ?? []].filter((row) => row.contentProfile === profile)
    .sort((a, b) => a.version.localeCompare(b.version, undefined, { numeric: true })).at(-1);
  const version = [candidate?.version, saved?.version].filter((item): item is string => Boolean(item)).sort((a, b) => a.localeCompare(b, undefined, { numeric: true })).at(-1);
  const signed = Boolean(version && ((saved?.version === version && saved.signed) || jobs.some((job) => job.version === version && job.action === "sign" && job.state === "COMPLETED")));
  const submitted = Boolean(version && ((saved?.version === version && saved.submitted) || jobs.some((job) => job.version === version && job.action === "upload" && job.state === "COMPLETED")));
  const publication = cloud.observation?.publications?.find((row) => row.version === version) ?? cloud.observation?.publication;
  const published = Boolean(version && publication?.version === version && publication.stage === "READY");
  const pending = Boolean(value?.pendingVersion);
  useEffect(() => {
    if (window.location.hash === "#native-header" || !["global", "platform", "brake", "tire"].includes(perspective)) return;
    return cloud.enter();
  }, [perspective, cloud.enter]);
  useEffect(() => { setMonitor(false); setDetails(null); }, [perspective]);
  const showMonitor = () => { navigate("global"); setMonitor(true); };
  const installed = value?.installedVersion;
  const installedProfile = local.candidates?.find((row) => row.version === installed)?.contentProfile
    ?? [...jobs].reverse().find((job) => job.version === installed && job.profile)?.profile;
  const componentLabel = installed === "0.0.0" ? "VDP · Factory baseline" : installed ? `VDP ${installedProfile ?? installed}` : "VDP · Not observed";
  const section = perspective === "global" ? monitor ? "Cloud monitoring" : "Vehicle" : `${perspective[0].toUpperCase()}${perspective.slice(1)} Team`;
  return <div className="studio-workspace" data-testid="studio-workspace">
    <div className="studio-topline"><div><small>SOFTWARE-DEFINED VEHICLE</small><h1>{section}</h1></div>
      <select aria-label="Vehicle target" value="test" onChange={() => {}}><option value="test">Test Vehicle</option><option disabled>Production · Deferred</option></select></div>
    <div className="studio-body">
      {perspective === "global" && !monitor && <>
        <div className="studio-backends">{(["brake", "tire", "cloud"] as const).map((name) => <button key={name} onClick={() => name === "cloud" ? showMonitor() : navigate(name)}>
          <StudioIcon name={name} /><strong>{name === "cloud" ? "Aos Cloud" : `${name === "brake" ? "Brake" : "Tire"} backend`}</strong><small>{name === "cloud" ? current ? known(value?.online) : "Cloud not current" : "Open dashboard"}</small></button>)}</div>
        <div className={`studio-cloud-link ${current && value?.online === "ONLINE" ? "online" : ""}`}><span>{current ? "Cloud observation" : "Connection not observed"}</span></div>
        <div className="studio-architecture"><aside className="studio-gateway"><StudioIcon name="vehicle" /><strong>Vehicle</strong><small>Sensors & actuators</small><span className="studio-arrow">↓</span><StudioIcon name="gateway" /><strong>Vehicle Gateway</strong><small>VSS telemetry</small></aside>
          <div className="studio-vss-line"><span>VSS</span></div><section className="studio-controller"><h2><StudioIcon name="platform" />Domain Controller</h2>
            <div className="studio-service-slots">{(["brake", "tire"] as const).map((team) => {
              const id = inventory?.teamServiceIds?.[team];
              const row = inventory?.services.value?.find(service => id && service.service?.id === id);
              const empty = current && inventory?.services.state === "CURRENT" && (inventory.services.value?.length === 0 || (id && !row));
              const version = row?.service_versions?.installed_service_version?.version;
              return <button key={team} className={empty ? "empty-slot" : ""} onClick={() => setDetails("services")}><StudioIcon name={team} /><strong>{team === "brake" ? "Brake Health" : "Tire Health"}</strong><small>{empty ? "Empty slot" : version ? `Installed ${version}${current && inventory?.services.state === "CURRENT" ? "" : " · last known"}` : "See Cloud inventory"}</small></button>;
            })}</div>
            <button className="studio-vdp" onClick={() => setDetails("vdp")}><StudioIcon name="component" /><strong>{componentLabel}</strong><small>{installed ? `${known(value?.updateStatus)} · release ${installed}${componentCurrent ? "" : " · last known"}` : "Cloud installation not reported"}</small></button>
            <footer><strong>Factory firmware</strong><span>{vehicle.imageVersion ?? "Choose a prepared image"}</span><small>{present ? `Local controller · ${known(vehicle.process)}` : "Not created"}</small></footer>
          </section></div>
        <section className="studio-actions"><h3>Demo lifecycle</h3><div className="studio-fields"><label>Preparation<select aria-label="Preparation" value={mode} onChange={(event) => setMode(event.target.value)}><option value="story">Full story</option><option value="quick">Quick preparation</option></select></label>
          <label>Factory image<select value={image} disabled={present} onChange={(event) => setSelectedImage(event.target.value)}>{present && !image && <option value="">{vehicle.imageVersion ?? "Current image not reported"} · Not in catalog</option>}{local.images.map((item) => <option key={item.selector} value={item.selector}>{item.version} · {item.architecture}</option>)}</select></label></div>
          <div className="studio-buttons"><button disabled={controls.blocked || !image || (present && !continuation)} onClick={() => controls.request({ action: mode === "quick" ? "prepare-demo" : "create", image })}>{continuation ? "Continue preparation" : mode === "quick" ? "Prepare demo" : "Create controller"}</button>
            <button disabled={controls.blocked || !present} onClick={() => controls.request({ action: "start-simulation" })}>Start simulator</button>
            <button disabled={controls.blocked || !present || connected} onClick={() => controls.request({ action: "connect-test" })}>Connect in Manual</button>
            <button disabled={controls.blocked || !present || local.registrationComplete} onClick={() => controls.request({ action: "provision" })}>{value?.lifecycle === "provisioned" && !local.registrationComplete ? "Continue registration" : "Provision to Test"}</button></div>
          <p>{connected ? "Test Vehicle selected. Driving and Safe Stop are controlled in the native Driving Control." : "Create the controller, then connect the simulator in stationary Manual."}</p></section>
      </>}
      {perspective === "platform" && <><section className="studio-release"><header><StudioIcon name="component" /><div><h2>Vehicle Data Platform</h2><p>Prepare → Sign → Publish → Observe</p></div></header>
        <label>Capability profile<select value={profile} onChange={(event) => setProfile(event.target.value as typeof profile)}><option value="v1">VDP v1 · Braking telemetry</option><option value="v2">VDP v2 · Brake analysis</option><option value="v3">VDP v3 · Tire & advisory</option></select></label>
        <div className="studio-release-stages">{["Prepared", "Signed", "Published", "Installed"].map((stage, index) => <div key={stage} className={[Boolean(version), signed, published, Boolean(version && componentCurrent && installed === version)][index] ? "complete" : ""}><span>{index + 1}</span><strong>{stage}</strong></div>)}</div>
        <p>{version ? `Selected candidate · ${profile} · ${version}` : "No candidate prepared in this session."}</p>
        <div className="studio-buttons"><button disabled={controls.blocked || !present} onClick={() => controls.request({ action: "prepare", profile })}>Prepare {profile}</button><button disabled={controls.blocked || !version || signed} onClick={() => controls.request({ action: "sign", version })}>Sign</button><button disabled={controls.blocked || !signed || submitted || pending} onClick={() => controls.request({ action: "upload", version })}>Publish to Cloud</button></div>
        {submitted && !published && <p>Upload accepted. Cloud processing: {publication?.version === version ? publication?.stage : "Not yet observed"}.</p>}
        {pending && <p>Cloud reports pending release {value?.pendingVersion}. Prepare/sign remain available; finish the outstanding update before publishing another.</p>}
        <p>Eligible Test Vehicles receive the component after publication. Installation follows the vehicle’s Safe Stop policy.</p></section></>}
      {(perspective === "platform" || (perspective === "global" && monitor)) && <section className="studio-cloud">{monitor && <button onClick={() => setMonitor(false)}>Vehicle map</button>}<div className="studio-panel-title"><h2><StudioIcon name="cloud" />Test Vehicle · Aos Cloud</h2><button disabled={cloud.loading} onClick={cloud.refresh}>Refresh Cloud state</button></div>
        <p className="studio-stamp">{cloud.loading ? "Reading Aos Cloud…" : `${cloud.observation?.state ?? "Not observed"} · ${stamp(cloud.observation?.observedAt)}`}</p>
        {!current && <p>Previous observation — not current.</p>}
        <strong>{installed ? `VDP ${installed} · Cloud installed${componentCurrent ? "" : " · last known"}` : "No installed VDP reported"}</strong>
        <dl className="platform-cloud-facts"><div><dt>Connection</dt><dd>{known(value?.online)}</dd></div><div><dt>Pending release</dt><dd>{known(value?.pendingVersion)}</dd></div><div><dt>VDP runtime</dt><dd>Not reported by Cloud</dd></div></dl>
        {monitor && <><h3>Components · {inventory?.components.state ?? "Not observed"}</h3><div className="studio-inventory">{inventory?.components.value?.map((row, index) => <button key={index} onClick={() => setDetails("vdp")}><strong>{row.type?.endsWith("-vehicle-data-provider") ? "Vehicle Data Platform" : row.type?.endsWith("-rootfs") ? "Root filesystem" : row.type?.endsWith("-boot") ? "Boot firmware" : row.type ?? row.reported_component_id ?? "Component"}</strong><span>Installed {known(row.installed_component?.version)} · Pending {known(row.pending_component?.version)}</span></button>) ?? <p>Not reported</p>}</div><h3>Services & instances</h3><ServiceRows rows={inventory?.services} /><Monitoring key={cloud.observation?.bindingKey ?? inventory?.unitId} unitId={inventory?.unitId} refreshKey={cloud.refreshGeneration} /></>}
      </section>}
      {(perspective === "brake" || perspective === "tire") && <><section className="studio-release"><header><StudioIcon name={perspective} /><div><h2>{section}</h2><p>Cloud runtime and product results are separate observations.</p></div></header>
        <div className="studio-panel-title"><h3>Service inventory · Aos Cloud</h3><button disabled={cloud.loading} onClick={cloud.refresh}>Refresh Cloud state</button></div>
        <p className="studio-stamp">{cloud.loading ? "Reading Aos Cloud…" : `${cloud.observation?.state ?? "Not observed"} · ${stamp(cloud.observation?.observedAt)}`}</p>
        <p>Cloud connection: {current ? known(value?.online) : "Not current"}. Active is the last reported instance state, not proof of live telemetry.</p>
        <ServiceRows rows={inventory?.services} /></section><BackendEvidence key={`${perspective}:${inventory?.systemUid ?? "none"}`} team={perspective} unitSystemUid={inventory?.systemUid} /></>}
    </div>
    <footer className="studio-session-actions"><button disabled={controls.blocked || !present} onClick={() => controls.request({ action: "park" })}>Park</button><button disabled={controls.blocked || !present} onClick={() => controls.request({ action: "resume" })}>Resume</button><button disabled={controls.blocked} onClick={() => controls.request({ action: "reset" })}>Finish demo</button><span>Test-only run</span></footer>
    <OperationProgress />
    {details && <Modal title={details === "services" ? "Cloud service inventory" : "Cloud component details"} subtitle="Current Test · Aos Cloud observation" onClose={() => setDetails(null)}><p>Read through Aos Cloud. Installed is not a claim of a running process.</p>{details === "services" ? <ServiceRows rows={inventory?.services} /> : <pre className="studio-details">{JSON.stringify(inventory?.components ?? { state: "NOT_OBSERVED" }, null, 2)}</pre>}</Modal>}
  </div>;
}
