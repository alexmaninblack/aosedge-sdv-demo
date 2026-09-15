import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { Perspective, PresenterSnapshot, ServiceRelease } from "../domain";
import type { CloudComponent, CloudService } from "../domain/platformObservation";
import type { DemoCommand } from "../domain/presenterCommandPort";
import { componentIssue, failedState, serviceIssue, servicePending as hasServicePending, serviceRunning } from "../domain/softwareObservation";
import { serviceReleases, serviceCandidate, serviceProfile, teamService, versionOrder, type Profile } from "../domain/studioModel";
import { usePlatformObservation } from "./state/PresenterReadModelProvider";
import { OperationProgress, usePresenterControls } from "./state/PresenterControls";
import { Modal } from "../shared/components/Modal";
import { BackendEvidence } from "../features/service-team/BackendEvidence";
import { CloudConnectionPanel } from "./CloudConnectionPanel";
import { ClientBuildNotice } from "./ClientBuildNotice";
import { ComponentDetails, Monitoring, ServiceRows, ObservationTime, componentName, known, stamp } from "./StudioReadViews";
import "../shared/design-tokens/studio.css";

export type StudioIconName = "vehicle" | "platform" | "brake" | "tire" | "cloud" | "gateway" | "component" | "service";
export function StudioIcon({ name }: { name: StudioIconName }) { return <span aria-hidden="true" className={`b2-icon b2-${name}`} />; }
const labels = { global: "Vehicle", platform: "Platform", brake: "Brake", tire: "Tire" };
const profileText = { platform: ["Braking telemetry", "Brake analysis", "Tire & advisory"], brake: ["Braking windows", "Condition assessment", "Driver advisory"], tire: ["Tire health"] };
type Detail = { kind: "component"; row: CloudComponent } | { kind: "service"; row: CloudService } | { kind: "release"; row: ServiceRelease };

function ArchitectureWires({ element, cloudState, brake, tire }: { element: React.RefObject<HTMLDivElement | null>; cloudState: string; brake: boolean; tire: boolean }) {
  const [paths, setPaths] = useState<{ id: string; d: string }[]>([]);
  useLayoutEffect(() => {
    const root = element.current;
    if (!root) return;
    const update = () => {
      const bounds = root.getBoundingClientRect();
      const point = (id: string, bottom: boolean) => {
        const rect = root.querySelector(`[data-anchor="${id}"]`)?.getBoundingClientRect();
        return rect ? { x: rect.x + rect.width / 2 - bounds.x, y: (bottom ? rect.bottom : rect.top) - bounds.y } : null;
      };
      setPaths((["cloud", ...(brake ? ["brake"] : []), ...(tire ? ["tire"] : [])]).flatMap((id, n) => {
        const a = point(id + "-backend", true), b = point(id === "cloud" ? "controller" : id + "-service", false);
        if (!a || !b) return [];
        const mid = a.y + 18 + n * 7;
        return [{ id, d: `M ${a.x} ${a.y} V ${mid} H ${b.x} V ${b.y}` }];
      }));
    };
    const observer = new ResizeObserver(update); observer.observe(root); update();
    return () => observer.disconnect();
  }, [element, brake, tire, cloudState]);
  return <svg className="studio-wires" aria-hidden="true">{paths.map(path => <path key={path.id} className={path.id === "cloud" ? cloudState.toLowerCase() : "service"} d={path.d} />)}</svg>;
}

export function StudioWorkspace({ snapshot, perspective, navigate }: { snapshot: PresenterSnapshot; perspective: Perspective; navigate: (value: Perspective) => void }) {
  const controls = usePresenterControls(), cloud = usePlatformObservation(), local = snapshot.localDemo!;
  const [mode, setMode] = useState("story"), [selectedImage, setSelectedImage] = useState("");
  const [profiles, setProfiles] = useState<Record<"platform" | "brake" | "tire", Profile>>({ platform: "v1", brake: "v1", tire: "v1" });
  const [screen, setScreen] = useState<"main" | "monitor" | "backend">("main");
  const [monitorTab, setMonitorTab] = useState("Software");
  const [selection, setDetails] = useState<Detail | null>(null), [sessionOpen, setSessionOpen] = useState(false), [traceOpen, setTraceOpen] = useState(false);
  const [backendProof, setBackendProof] = useState<Record<string, string>>({});
  const architecture = useRef<HTMLDivElement>(null);
  const vehicle = local.vehicles.test;
  const localStateKnown = vehicle.state === "CURRENT" || (!local.runId && vehicle.state === "NOT_APPLICABLE" && vehicle.reason === "TARGET_NOT_CONFIGURED");
  const present = vehicle.state === "CURRENT" && vehicle.overlayExists === true;
  const running = present && vehicle.process === "RUNNING";
  const parked = local.lifecycle?.action === "park" && local.lifecycle.state === "COMPLETED";
  const retiring = local.lifecycle?.action === "retire" && local.lifecycle.state !== "COMPLETED";
  const connected = snapshot.vehicle.value === "test";
  const simulationRunning = connected || ["RUNNING_UNASSIGNED", "CONNECTED", "SELECTED_NOT_PROBED"].includes(local.source.state);
  const image = present ? local.images.find(row => row.version === vehicle.imageVersion)?.selector ?? ""
    : (mode === "quick" ? local.preparation?.image : local.lifecycle?.image) || selectedImage || local.images[0]?.selector || "";
  const continuation = mode === "quick" ? Boolean(local.preparation && local.preparation.phase !== "READY_TO_DRIVE")
    : local.lifecycle?.action === "create" && local.lifecycle.state !== "COMPLETED";
  const observation = cloud.observation;
  const bindingMatches = !observation?.bindingKey || Boolean(local.runId && observation.bindingKey.startsWith(local.runId + ":"));
  const value = bindingMatches ? observation?.value : null;
  const inventory = value?.inventory;
  const selectedRow = selection?.kind === "component" ? inventory?.components.value?.find(row => row.type === selection.row.type && row.reported_component_id === selection.row.reported_component_id)
    : selection?.kind === "service" ? inventory?.services.value?.find(row => row.service?.id === selection.row.service?.id && row.subject === selection.row.subject) : undefined;
  const current = bindingMatches && observation?.state === "CURRENT";
  const componentCurrent = current && (!inventory || inventory.components.state === "CURRENT");
  const servicesCurrent = current && inventory?.services.state === "CURRENT";
  const releases = serviceReleases(local, bindingMatches ? observation : null);
  const details: Detail | null = selection?.kind === "release" ? (() => { const row = releases.find(row => row.releaseHandle === selection.row.releaseHandle); return row ? { kind: "release", row } : null; })()
    : selectedRow ? { kind: selection!.kind, row: selectedRow } as Detail : null;
  useEffect(() => { setDetails(null); }, [local.runId, inventory?.unitId]);
  const jobs = (controls.session?.jobs ?? []).filter(job => local.runId && job.runId === local.runId);
  const installed = value?.installedVersion;
  const installedProfile = local.candidates?.find(row => row.version === installed)?.contentProfile
    ?? [...jobs].reverse().find(job => job.version === installed && !job.action.startsWith("service-") && job.profile)?.profile;
  const services = { brake: teamService("brake", bindingMatches ? observation : null), tire: teamService("tire", bindingMatches ? observation : null) };
  const pending = Boolean(value?.pendingVersion);
  const publishedAny = bindingMatches && (observation?.publications?.some(row => row.stage === "READY") || observation?.publication?.stage === "READY");
  const vdpIssue = componentIssue(inventory?.components.value?.find(row => row.type?.endsWith("-vehicle-data-provider"))) || (failedState(value?.updateStatus) ? value?.updateStatus : null);
  const team = perspective === "global" ? "platform" : perspective;
  const profile = profiles[team];
  const preparedJob = [...jobs].reverse().find(job => job.action === "prepare" && job.profile === profile && job.state === "COMPLETED" && job.version);
  const saved = [...local.candidates ?? []].filter(row => row.contentProfile === profile).sort((a, b) => versionOrder(a.version, b.version)).at(-1);
  const version = [preparedJob?.version, saved?.version].filter((row): row is string => Boolean(row)).sort(versionOrder).at(-1);
  const submitted = Boolean(version && (saved?.version === version && saved.submitted || jobs.some(job => job.cloudDomain === controls.session?.cloudDomain && job.version === version && ["upload", "publish"].includes(job.action) && job.state === "COMPLETED")));
  const publication = observation?.publications?.find(row => row.version === version) ?? (observation?.publication?.version === version ? observation?.publication : null);
  const published = publication?.stage === "READY";
  const service = team === "platform" ? undefined : serviceCandidate(local, releases, jobs, team, profile);
  const serviceSubmitted = Boolean(service?.submitted || jobs.some(job => job.cloudDomain === controls.session?.cloudDomain && job.release === service?.releaseHandle && job.action === "service-publish" && job.state === "COMPLETED"));
  const row = team === "platform" ? undefined : services[team];
  const serviceId = service?.serviceId ?? (team === "platform" ? undefined : inventory?.teamServiceIds?.[team]);
  const servicePending = hasServicePending(row);
  const publicationBlockedReason = controls.blockReason ?? (retiring ? "Finish the recorded retirement before preparing or publishing again." : !present ? "Create a controller first." : team === "platform"
    ? pending ? "Another component update is pending; inspect its Cloud state before publishing again." : submitted ? "This candidate was already submitted. Observe its existing publication; it will not be sent twice." : !version ? "Prepare this capability profile before signing and publishing." : null
    : servicePending ? "A service update is pending; inspect its Cloud state before publishing again." : serviceSubmitted ? "This candidate was already submitted. Refresh its publication or prepare a higher release." : !service ? "Prepare this service profile before signing and publishing." : null);
  const showBackend = screen === "backend" && (perspective === "brake" || perspective === "tire");
  const showMonitor = screen === "monitor" && perspective === "global";
  const openView = (next: Perspective, nextScreen: typeof screen = "main") => { navigate(next); setScreen(nextScreen); setDetails(null); };
  useEffect(() => {
    if (window.location.hash === "#native-header") return;
    return cloud.enter();
  }, [cloud.enter, perspective, screen]);
  useEffect(() => {
    const open = () => setSessionOpen(true);
    window.addEventListener("presenter-session", open);
    return () => window.removeEventListener("presenter-session", open);
  }, []);
  useEffect(() => { setBackendProof({}); }, [local.runId]);
  const ask = (command: DemoCommand) => {
    // A partial retirement must not revive or republish into the same run.
    // Continue only its recorded cleanup, or perform read-only observations.
    if (retiring && !["reset", "observe-test", "cloud-status", "service-observe", "inspect", "verify", "cloud-access"].includes(command.action)) return;
    controls.request(command);
  };
  const create = () => ask({ action: mode === "quick" ? "prepare-demo" : "create", image });

  // This guide explains observed state; it never starts an operation itself.
  let guide = { title: "Create your vehicle", body: "Choose the factory firmware for its domain controller.", label: mode === "quick" ? "Prepare demo" : "Create controller", disabled: !image, action: create };
  if (present && continuation) guide = { title: "Continue preparation", body: local.lifecycle?.reason ?? local.preparation?.reason ?? "Continue only the remaining recorded steps.", label: "Continue preparation", disabled: !image, action: create };
  else if (parked) guide = { title: "Demo parked", body: "Resume the same controller and Cloud identity.", label: "Resume", disabled: false, action: () => ask({ action: "resume" }) };
  else if (present && !simulationRunning) guide = { title: "Connect the local vehicle", body: "Start CARLA, Gateway and the native vehicle panels.", label: "Start simulator", disabled: !running, action: () => ask({ action: "start-simulation" }) };
  else if (present && !connected) guide = { title: "Connect the domain controller", body: "Initial connection is stationary Manual; driving remains operator-controlled.", label: "Connect in Manual", disabled: !running, action: () => ask({ action: "connect-test" }) };
  else if (present && !local.registrationComplete) {
    const hasRegistration = local.registrationStarted === true || value?.lifecycle === "provisioned";
    guide = publishedAny || hasRegistration
      ? { title: hasRegistration ? "Complete Cloud registration" : "Provision your vehicle", body: "Register this controller in Test Vehicles, preserving its local connection.", label: hasRegistration ? "Continue registration" : "Provision to Test", disabled: false, action: () => ask({ action: "provision" }) }
      : { title: "Prepare the platform release", body: "The Platform Team publishes software before the vehicle is provisioned.", label: "Open Platform", disabled: false, action: () => openView("platform") };
  } else if (present && !componentCurrent) guide = { title: "Observe the current controller", body: "Cloud state is not current. Previous reports are not live confirmation.", label: "Refresh Cloud state", disabled: cloud.loading, action: cloud.refresh };
  else if (present && vdpIssue) guide = { title: "Component update issue", body: `${vdpIssue}. Safe Stop does not resolve this reported error. Inspect the Cloud report or finish this run.`, label: "Open Platform", disabled: false, action: () => openView("platform") };
  else if (present && pending) guide = { title: "Component update pending", body: `Cloud reports ${value?.pendingVersion}. Use native Safe Stop when ready; installation is owned by the vehicle.`, label: "Open Platform", disabled: false, action: () => openView("platform") };
  else if (present && publishedAny && installed === "0.0.0") guide = { title: "First platform update", body: "Drive the vehicle, then use native Safe Stop. Observe the installed release here; no Apply button is needed.", label: "Refresh Cloud state", disabled: cloud.loading, action: cloud.refresh };
  else if (present && !servicesCurrent) guide = { title: "Observe service inventory", body: "Service reports are not current; software progress is not confirmed.", label: "Refresh Cloud state", disabled: cloud.loading, action: cloud.refresh };
  else if (present && Object.values(services).some(item => item && (serviceIssue(item) || item.service_versions?.installed_service_version?.version && !serviceRunning(item, item.service_versions.installed_service_version.version, Boolean(servicesCurrent))))) guide = {
    title: "Service runtime not confirmed", body: Object.values(services).map(serviceIssue).find(Boolean) ?? "The installed release does not yet have a current active instance report. Refresh Cloud state; Safe Stop is not required for services.", label: "Refresh Cloud state", disabled: cloud.loading, action: cloud.refresh };
  else if (present) {
    const vdpLevel = Number(installedProfile?.slice(1)) || 0;
    const brakeLevel = Number(serviceProfile(services.brake, releases)?.slice(1)) || 0;
    const tireLevel = Number(serviceProfile(services.tire, releases)?.slice(1)) || 0;
    let next: Perspective = "platform", level: Profile = "v1";
    if (vdpLevel < 1) { next = "platform"; level = "v1"; }
    else if (brakeLevel < Math.min(vdpLevel, 3)) { next = "brake"; level = (`v${Math.min(vdpLevel, 3)}` as Profile); }
    else if (services.brake && backendProof.brake !== services.brake.service_versions?.installed_service_version?.version) next = "brake";
    else if (vdpLevel < 3) { next = "platform"; level = `v${vdpLevel + 1}` as Profile; }
    else if (tireLevel < 1 || backendProof.tire !== services.tire?.service_versions?.installed_service_version?.version) next = "tire";
    else next = "global";
    const resultNeeded = next !== "global" && next !== "platform" && serviceProfile(services[next], releases) === (next === "brake" ? `v${brakeLevel}` : "v1")
      && ((next === "brake" && brakeLevel >= Math.min(vdpLevel, 3)) || (next === "tire" && tireLevel >= 1));
    guide = next === "global" ? { title: "Software story complete", body: "Installed releases and synthetic backend delivery observed. Vehicle-derived analytics/advisory remain unqualified.", label: "Open monitoring", disabled: false, action: () => openView("global", "monitor") }
      : { title: resultNeeded ? "Observe the product result" : "Next software profile", body: resultNeeded ? "Open the team's backend to inspect its durable synthetic result." : "Prepare and publish the next capability. Skipped earlier profiles are not claimed demonstrated.", label: `Open ${labels[next]}${resultNeeded ? " backend" : ` ${level}`}`, disabled: false,
        action: () => { setProfiles(previous => ({ ...previous, [next]: level })); openView(next, resultNeeded ? "backend" : "main"); } };
  }
  if (retiring) {
    const offline = current && value?.online?.toUpperCase() === "OFFLINE";
    const waitingOffline = local.lifecycle?.phase === "deprovision-test"
      && local.lifecycle.reason?.includes("CLOUD_OFFLINE") && !offline;
    guide = { title: "Retirement paused", body: waitingOffline
      ? "Waiting for Cloud to report Offline. Refresh its state before continuing; do not restart the vehicle."
      : `${local.lifecycle?.reason ? `${local.lifecycle.reason}. ` : ""}Continue only the remaining recorded cleanup; completed steps are not repeated.`,
      label: waitingOffline ? "Refresh Cloud state" : "Continue Finish", disabled: waitingOffline ? cloud.loading : controls.blocked,
      action: waitingOffline ? cloud.refresh : () => ask({ action: "reset" }) };
  }
  if (!localStateKnown && !retiring) guide = { title: "Controller state unavailable", body: "The local read did not confirm whether a controller exists. Refresh before starting another operation.", label: "Refresh state", disabled: cloud.loading, action: cloud.refresh };
  if (controls.session?.active) guide = { title: "Operation in progress", body: "Demo Control owns the current operation. Follow its actual receipt in Trace; no action is repeated automatically.", label: "View progress", disabled: false, action: () => setTraceOpen(true) };
  const title = showBackend ? `${labels[perspective]} backend` : showMonitor ? "Cloud monitoring" : perspective === "global" ? "Your vehicle" : `${labels[perspective]} Team`;
  const cloudState = current ? value?.online ?? "UNKNOWN" : "UNKNOWN";
  const cloudLabel = !localStateKnown ? "Controller state unavailable" : !present && !inventory && !value ? "No controller created" : !local.registrationComplete && !inventory?.unitId && value?.lifecycle !== "provisioned" ? local.registrationStarted ? "Registration incomplete" : "Not provisioned" : current ? cloudState : value ? "Last known Cloud report" : "Cloud unavailable";
  const scopedJob = jobs.at(-1) ?? null;
  const closeSession = () => setSessionOpen(false);
  return <div className="studio-workspace" data-testid="studio-workspace">
    <ClientBuildNotice />
    <nav className="studio-nav" aria-label="Demo perspectives">{(["global", "platform", "brake", "tire"] as const).map(name => <button key={name} aria-label={name === "global" ? "Vehicle" : `${labels[name]} Team`} aria-pressed={perspective === name} onClick={() => openView(name)}><StudioIcon name={name === "global" ? "vehicle" : name} />{labels[name]}</button>)}</nav>
    <div className="studio-topline"><h1>{title}</h1><span>Test Vehicle · {cloudLabel}</span></div>
    <div className="studio-body">
      {perspective === "global" && !showMonitor && <>
        <div className="studio-preparation"><label>Preparation <select aria-label="Preparation" value={mode} onChange={event => setMode(event.target.value)}><option value="story">Full story</option><option value="quick">Quick preparation</option></select></label><span>Production · Deferred</span></div>
        <div ref={architecture} className="studio-architecture-stage">
          <ArchitectureWires element={architecture} cloudState={cloudState} brake={Boolean(services.brake?.service_versions?.installed_service_version)} tire={Boolean(services.tire?.service_versions?.installed_service_version)} />
          <div className="studio-backends">{(["brake", "tire", "cloud"] as const).map(name => <button key={name} data-anchor={`${name}-backend`} onClick={() => name === "cloud" ? openView("global", "monitor") : openView(name, "backend")}><StudioIcon name={name} /><strong>{name === "cloud" ? "Aos Cloud" : `${labels[name]} backend`}</strong><small>{name === "cloud" ? "Unit monitoring ↗" : "Open dashboard ↗"}</small></button>)}</div>
          <div className="studio-architecture"><aside className="studio-gateway"><StudioIcon name="vehicle" /><strong>Vehicle</strong><small>Sensors & actuators</small><span>↓</span><StudioIcon name="gateway" /><strong>Vehicle Gateway</strong><small>VSS telemetry</small></aside><div className="studio-vss-line" />
            <section className="studio-controller" data-anchor="controller"><h2><StudioIcon name="platform" />Domain Controller</h2>
              <div className="studio-service-slots">{(["brake", "tire"] as const).map(name => {
                const item = services[name], release = item?.service_versions?.installed_service_version?.version;
                const empty = servicesCurrent && (!inventory?.services.value?.length || Boolean(inventory?.teamServiceIds?.[name] && !item));
                return <button key={name} data-anchor={`${name}-service`} className={!release ? "empty-slot" : ""} aria-label={empty ? `Empty ${name} service slot` : `${labels[name]} service details`} onClick={() => item ? setDetails({ kind: "service", row: item }) : openView(name)}>
                  {release ? <><StudioIcon name={name} /><strong>{labels[name]} Health</strong><small>{serviceProfile(item, releases) ?? "Service"} · {release}{servicesCurrent ? "" : " · last known"}</small></> : <span>{empty ? "Empty service slot" : "Service not observed"}</span>}
                </button>;
              })}</div>
              <button className="studio-vdp" onClick={() => { const row = inventory?.components.value?.find(row => row.type?.endsWith("-vehicle-data-provider")); if (row) setDetails({ kind: "component", row }); else openView("platform"); }}><StudioIcon name="component" /><strong>Vehicle Data Platform</strong><small>{installed ? `${installed === "0.0.0" ? "Factory baseline" : installedProfile ?? "Release"} · ${installed}${componentCurrent ? "" : " · last known"}` : "Factory slot · no Cloud report"}</small></button>
              <footer><label>Factory firmware<select aria-label="Factory image" value={image} disabled={present} onChange={event => setSelectedImage(event.target.value)}>{present && !image && <option value="">{vehicle.imageVersion ?? "Current image not reported"}</option>}{local.images.map(row => <option key={row.selector} value={row.selector}>{row.version}</option>)}</select></label></footer>
            </section></div>
        </div>
      </>}
      {perspective !== "global" && !showBackend && <section className="studio-release"><header><StudioIcon name={team === "platform" ? "component" : "service"} /><div><h2>{team === "platform" ? "Vehicle Data Platform" : `${labels[team]} Health Service`}</h2><p>{team === "platform" ? "Platform Team · OEM" : `${labels[team]} Team · Service Provider`}</p></div></header>
        <div className="studio-profile-cards" role="group" aria-label="Capability profile">{profileText[team].map((name, n) => <button key={name} aria-pressed={profile === `v${n + 1}`} onClick={() => setProfiles(previous => ({ ...previous, [team]: `v${n + 1}` as Profile }))}><strong>v{n + 1}</strong><span>{name}</span></button>)}</div>
        <div className="studio-release-stages">{["Prepared", "Published", team === "platform" ? "Installed" : "Running"].map((stage, index) => {
          const done = team === "platform" ? [Boolean(version), published, Boolean(version && componentCurrent && installed === version)]
            : [Boolean(service), service?.publication.stage === "READY", serviceRunning(row, service?.version, Boolean(servicesCurrent))];
          return <div key={stage} className={done[index] ? "complete" : ""}><span>{index + 1}</span><strong>{stage}</strong></div>;
        })}</div>
        {publicationBlockedReason && <p className="studio-action-reason">{publicationBlockedReason}</p>}
        {team === "platform" ? <><p>{version ? `Selected candidate · ${profile} · ${version}` : "No candidate prepared for this profile."}</p><div className="studio-buttons">
          <button disabled={controls.blocked || retiring || !present} onClick={() => ask({ action: "prepare", profile })}>Prepare {profile}</button>
          <button disabled={controls.blocked || retiring || !version || submitted || pending} onClick={() => ask({ action: "publish", version })}>Sign & publish</button></div>
          {submitted && !published && <p role={failedState(publication?.stage) ? "alert" : undefined}>Cloud {failedState(publication?.stage) ? "publication failed" : "processing"} · {publication?.stage ?? "Awaiting observation"}{publication?.reason ? ` · ${publication.reason}` : ""}</p>}
          <p role={vdpIssue ? "alert" : undefined}>{vdpIssue ? `Component update issue · ${vdpIssue}` : pending ? `Component ${value?.pendingVersion} is pending${componentCurrent ? ". Use native Safe Stop when ready." : " · last known report."}` : "Publication can deliver to an eligible Test immediately. No validation-batch approval step."}</p>
          <div className="studio-observed"><strong>Cloud installed · {known(installed)}{installed && !componentCurrent ? " · last known" : ""}</strong><span>Process state: not reported by Cloud.</span></div></>
        : <><div className="studio-mock-notice">Synthetic service data · KUKSA permissions pending</div><p>{service ? `Selected candidate · ${profile} · ${service.version}` : "No candidate prepared in this run."}</p><div className="studio-buttons">
          <button disabled={controls.blocked || retiring || !present} onClick={() => ask({ action: "service-prepare", team, profile })}>Prepare {profile}</button>
          <button disabled={controls.blocked || retiring || !service || serviceSubmitted || servicePending} onClick={() => ask({ action: "service-publish", release: service?.releaseHandle })}>Sign & publish</button>
          {!row && <button disabled={controls.blocked || retiring || service?.publication.stage !== "READY" || !serviceId || !local.registrationComplete || !servicesCurrent} onClick={() => ask({ action: "service-assign", serviceId })}>Deploy to Test</button>}
          {service && <button disabled={controls.readBlocked || !serviceSubmitted} onClick={() => ask({ action: "service-observe", release: service.releaseHandle })}>Refresh publication</button>}
          {service && <button onClick={() => setDetails({ kind: "release", row: service })}>Package details</button>}</div>
          {serviceSubmitted && <p>Cloud publication · {service?.publication.stage ?? "Awaiting observation"}{service?.publication.reason ? ` · ${service.publication.reason}` : ""}</p>}
          {!row && service?.publication.stage === "READY" && (!serviceId || !local.registrationComplete || !servicesCurrent) && <p>Deploy requires a Cloud service identity, completed Test registration and a current service inventory.</p>}
          <p>{row ? "This service is already assigned. Higher releases replace it without another Deploy or Safe Stop." : "After publication, Deploy binds this service's Subject to current Test. No Safe Stop is required."}</p>
          <ServiceRows current={Boolean(servicesCurrent)} rows={row ? { state: inventory?.services.state ?? "UNKNOWN", value: [row] } : undefined} onSelect={row => setDetails({ kind: "service", row })} />
          <button className="studio-text-action" onClick={() => setScreen("backend")}>Open {labels[team]} backend ↗</button></>}
      </section>}
      {showBackend && (perspective === "brake" || perspective === "tire") && <><button className="studio-text-action" onClick={() => setScreen("main")}>← {labels[perspective]} releases</button><BackendEvidence key={`${perspective}:${inventory?.systemUid ?? "none"}`} team={perspective} unitSystemUid={inventory?.systemUid} expectedVersion={services[perspective]?.service_versions?.installed_service_version?.version ?? undefined} onEvidence={version => setBackendProof(previous => previous[perspective] === version ? previous : { ...previous, [perspective]: version })} /></>}
      {showMonitor && <><div className="studio-panel-title"><button onClick={() => setScreen("main")}>← Vehicle map</button><button disabled={cloud.loading} onClick={cloud.refresh}>Refresh Cloud state</button></div>
        <div className="studio-pills">{["Software", "Resources"].map(tab => <button key={tab} aria-pressed={monitorTab === tab} onClick={() => setMonitorTab(tab)}>{tab}</button>)}</div>
        {monitorTab === "Software" ? <><h3>Components</h3><div className="studio-inventory studio-component-grid">{inventory?.components.value?.map((row, n) => <button key={n} onClick={() => setDetails({ kind: "component", row })}><strong>{componentName(row)}</strong><span>{known(row.installed_component?.version)}{componentCurrent ? "" : " · last known"}</span><small>{row.pending_component ? `Pending ${known(row.pending_component.version)}` : componentCurrent ? "No pending release" : "Pending not current"}</small></button>)}</div>
          {!inventory?.components.value?.length && <p>{!present ? "Create the controller to begin." : !local.registrationComplete ? "Provision Test to observe its Cloud software inventory." : inventory?.components.reason ?? (componentCurrent ? "No components reported by Cloud." : "Component inventory not available.")}</p>}
          <h3>Services & instances</h3><ServiceRows current={Boolean(servicesCurrent)} rows={inventory?.services} onSelect={row => setDetails({ kind: "service", row })} /></>
          : <Monitoring key={inventory?.unitId} inventory={inventory} refreshKey={cloud.refreshGeneration} />}</>}
    </div>
    <aside className="studio-guide"><div><small>DEMO STORY</small><strong>{guide.title}</strong><p>{guide.body}</p>{controls.blockReason && <small>{controls.blockReason}</small>}</div><button disabled={guide.disabled || (controls.blocked && !/^(Open |Refresh |View progress)/.test(guide.label))} onClick={guide.action}>{guide.label}</button></aside>
    <footer className="studio-footer"><span title={observation?.reason ?? undefined}>{cloud.loading ? "Reading Aos Cloud · " : `${cloudLabel} · `}<ObservationTime value={observation?.observedAt} /></span><button onClick={cloud.refresh} disabled={cloud.loading}>Refresh</button><button onClick={() => setTraceOpen(true)}>Trace · {jobs.length}</button><button className="studio-local-session" onClick={() => setSessionOpen(true)}>Session</button></footer>
    {traceOpen && <Modal title="Current run activity" subtitle="Actual Demo Control receipts · no simulated transitions" onClose={() => setTraceOpen(false)}><OperationProgress job={scopedJob} />{!jobs.length && <p>No operations recorded for the current run.</p>}{jobs.map(job => <article className="studio-trace-row" key={job.id}><strong>{job.action} · {job.state}</strong><p>{job.results.at(-1)?.message ?? job.reason}</p><small>{stamp(job.finishedAt ?? job.startedAt)}</small></article>)}</Modal>}
    {!traceOpen && (controls.error || controls.session?.active || scopedJob && !["COMPLETED", "OBSERVED"].includes(scopedJob.state)) && <OperationProgress job={controls.session?.jobs.find(job => job.id === controls.session?.active) ?? scopedJob} />}
    {sessionOpen && <Modal title="Demo session" subtitle="Current Test only · Production remains unchanged" onClose={closeSession}>
      <CloudConnectionPanel />
      <div className="studio-session-grid"><button disabled={controls.blocked || retiring || !running || pending || Object.values(services).some(hasServicePending)} onClick={() => { closeSession(); ask({ action: "park" }); }}>Park</button><p>Stop local runtimes; retain identity, disks and installed releases.</p>
      <button disabled={controls.blocked || retiring || !parked} onClick={() => { closeSession(); ask({ action: "resume" }); }}>Resume</button><p>Restart the same parked run, without provisioning or publication.</p>
      <button disabled={controls.blocked} onClick={() => { closeSession(); ask({ action: "reset" }); }}>Finish demo</button><p>Retire the owned Test and its working data. Preserve Factory originals and release continuity.</p></div></Modal>}
    {details && <Modal title={details.kind === "component" ? componentName(details.row) : details.kind === "service" ? details.row.service?.title ?? "Service" : "Prepared service package"} subtitle={details.kind === "release" ? "Demo Control · authoring metadata" : "Current Test · Aos Cloud observation"} onClose={() => setDetails(null)}>
      {details.kind === "component" ? <ComponentDetails row={details.row} current={Boolean(componentCurrent)} /> : details.kind === "service" ? <><ServiceRows rows={{ state: inventory?.services.state ?? "UNKNOWN", value: [details.row] }} current={Boolean(servicesCurrent)} /><p>Instance state is the last Cloud report, not proof of live telemetry or a product result.</p></>
      : <dl className="detail-grid"><dt>Service</dt><dd>{details.row.team}</dd><dt>Profile / release</dt><dd>{details.row.contentProfile} · {details.row.version}</dd><dt>Architecture</dt><dd>ARM64</dd><dt>Data mode</dt><dd>{details.row.demoMockedData ? "Synthetic · no KUKSA access" : "Native inputs"}</dd><dt>Instances</dt><dd>minInstances: 1</dd><dt>Offline lifetime</dt><dd>P7D</dd><dt>Publication</dt><dd>{details.row.publication.stage ?? "Not published"}</dd><dt>Signed bundle SHA-256</dt><dd>{details.row.sha256 ?? "Not signed"}</dd></dl>}
    </Modal>}
  </div>;
}
