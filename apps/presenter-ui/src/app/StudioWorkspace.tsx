import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { WorkspacePlacement } from "./WorkspacePlacement";
import type { Perspective, PresenterSnapshot, ServiceRelease } from "../domain";
import type { CloudComponent, CloudService } from "../domain/platformObservation";
import { confirmedInstalledProfile } from "../domain/installedCompatibility";
import type { DemoCommand } from "../domain/presenterCommandPort";
import { componentIssue, componentPending, componentUpdateLabel, failedState, serviceIssue, servicePending as hasServicePending, serviceRunning } from "../domain/softwareObservation";
import { serviceReleases, serviceCandidate, serviceProfile, teamService, versionOrder, type Profile } from "../domain/studioModel";
import { usePlatformObservation } from "./state/PresenterReadModelProvider";
import { OperationProgress, preparationRecovery, usePresenterControls } from "./state/PresenterControls";
import { Modal } from "../shared/components/Modal";
import { BackendEvidence } from "../features/service-team/BackendEvidence";
import { backendSummary, useBackendObservation } from "../features/service-team/useBackendObservation";
import { backendBinding } from "../features/service-team/backendSelection";
import { BackendSummary, CloudSummary } from "./StudioSummaryCards";
import { CloudConnectionPanel } from "./CloudConnectionPanel";
import { ClientBuildNotice } from "./ClientBuildNotice";
import { FinishAcknowledgement } from "./FinishAcknowledgement";
import { ComponentDetails, ServiceCompatibility, Monitoring, ServiceRows, ObservationTime, componentName, known, stamp, useCloudResources } from "./StudioReadViews";
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
        // Route inside the actual connector gap, not through the controller
        // heading when the fixed workspace is compact.
        const ceiling = point("controller", false)?.y ?? b.y;
        const mid = a.y + Math.min(18 + n * 7, Math.max(0, ceiling - a.y) * (n + 1) / 4);
        return [{ id, d: `M ${a.x} ${a.y} V ${mid} H ${b.x} V ${b.y}` }];
      }));
    };
    const observer = new ResizeObserver(update);
    observer.observe(root);
    root.querySelectorAll("[data-anchor]").forEach(anchor => observer.observe(anchor));
    update();
    return () => observer.disconnect();
  }, [element, brake, tire, cloudState]);
  return <svg className="studio-wires" aria-hidden="true">{paths.map(path => <path key={path.id} data-team={path.id === "cloud" ? "platform" : path.id} className={path.id === "cloud" ? cloudState.toLowerCase() : "service"} d={path.d} />)}</svg>;
}

export function StudioWorkspace({ snapshot, perspective, navigate }: { snapshot: PresenterSnapshot; perspective: Perspective; navigate: (value: Perspective) => void }) {
  const controls = usePresenterControls(), cloud = usePlatformObservation(), local = snapshot.localDemo!;
  const [mode, setMode] = useState("story"), [selectedImage, setSelectedImage] = useState("");
  const [profiles, setProfiles] = useState<Record<"platform" | "brake" | "tire", Profile>>({ platform: "v1", brake: "v1", tire: "v1" });
  const [popup, setPopup] = useState<"cloud" | "brake" | "tire" | null>(null);
  const [monitorTab, setMonitorTab] = useState("Software");
  const [sessionTab, setSessionTab] = useState("Lifecycle");
  const [selection, setDetails] = useState<Detail | null>(null), [sessionOpen, setSessionOpen] = useState(false), [traceOpen, setTraceOpen] = useState(false);
  const architecture = useRef<HTMLDivElement>(null);
  const vehicle = local.vehicles.test;
  const localStateKnown = vehicle.state === "CURRENT" || (!local.runId && vehicle.state === "NOT_APPLICABLE" && vehicle.reason === "TARGET_NOT_CONFIGURED");
  const present = vehicle.state === "CURRENT" && vehicle.overlayExists === true;
  const noController = localStateKnown && !local.runId && !present;
  const running = present && vehicle.process === "RUNNING";
  const retiring = local.lifecycle?.action === "retire" && local.lifecycle.state !== "COMPLETED";
  const connected = snapshot.vehicle.value === "test";
  const simulationRunning = connected || ["RUNNING_UNASSIGNED", "CONNECTED", "SELECTED_NOT_PROBED"].includes(local.source.state);
  const vehicleWindowsAbsent = noController && !simulationRunning && ["STOPPED", "NOT_PREPARED"].includes(local.source.state);
  const image = present ? local.images.find(row => row.version === vehicle.imageVersion)?.selector ?? ""
    : (mode === "quick" ? local.preparation?.image : local.lifecycle?.image) || selectedImage || local.images[0]?.selector || "";
  const continuation = mode === "quick" ? Boolean(local.preparation && local.preparation.phase !== "READY_TO_DRIVE")
    : local.lifecycle?.action === "create" && local.lifecycle.state !== "COMPLETED";
  // Read historical checkpoints, but never offer an unsupported same-run restart.
  const interruptedRun = !retiring && (local.lifecycle?.action === "park"
    || local.lifecycle?.action === "resume" && local.lifecycle.state !== "COMPLETED"
    || present && vehicle.process === "STOPPED" && !continuation);
  const lifecycleRestricted = retiring || interruptedRun;
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
  useEffect(() => { setProfiles({ platform: "v1", brake: "v1", tire: "v1" }); }, [local.runId]);
  const jobs = (controls.session?.jobs ?? []).filter(job => local.runId && job.runId === local.runId);
  // Create can be active before it allocates a run ID; Finish outlives that ID.
  // Keep only the session's actual active operation outside the scoped history.
  const activeJob = controls.session?.jobs.find(job => job.id === controls.session?.active);
  const installed = value?.installedVersion;
  const vdpRow = inventory?.components.value?.find(row => row.type?.endsWith("-vehicle-data-provider"));
  const profileEvidence = confirmedInstalledProfile(value?.installedProfile, installed, vdpRow?.installed_component?.id);
  const installedProfile = profileEvidence?.profile ?? null;
  const services = { brake: teamService("brake", bindingMatches ? observation : null), tire: teamService("tire", bindingMatches ? observation : null) };
  const visibleWorkspace = window.location.hash !== "#native-header";
  const observationScope = `${local.runId ?? ""}:${controls.session?.cloudDomain ?? ""}:${inventory?.unitId ?? ""}`;
  const brakeObservation = useBackendObservation("brake", inventory?.systemUid, visibleWorkspace && (perspective === "global" || popup === "brake"), false, observationScope);
  const tireObservation = useBackendObservation("tire", inventory?.systemUid, visibleWorkspace && (perspective === "global" || popup === "tire"), false, observationScope);
  const resources = useCloudResources(inventory?.unitId, visibleWorkspace && popup === "cloud" && monitorTab === "Resources", cloud.refreshGeneration, observationScope);
  const backendModels = { brake: brakeObservation, tire: tireObservation };
  const backendBindings = { brake: backendBinding(inventory?.systemUid, services.brake, Boolean(servicesCurrent), serviceProfile(services.brake, releases)),
    tire: backendBinding(inventory?.systemUid, services.tire, Boolean(servicesCurrent), serviceProfile(services.tire, releases)) };
  const brakeProof = backendSummary(brakeObservation, "brake", services.brake?.service_versions?.installed_service_version?.version ?? undefined, backendBindings.brake).proof;
  const tireProof = backendSummary(tireObservation, "tire", services.tire?.service_versions?.installed_service_version?.version ?? undefined, backendBindings.tire).proof;
  const backendProof = { brake: brakeProof, tire: tireProof };
  const pending = componentPending(vdpRow) || componentPending({ pending_component: value?.pendingVersion ? { version: value.pendingVersion } : null, pending_component_status: value?.updateStatus ?? null });
  const pendingDescription = value?.pendingVersion ? `Release ${value.pendingVersion}` : "Update in progress · version not reported";
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
  const prepareJob = [...jobs].reverse().find(job => job.profile === profile && (team === "platform" ? job.action === "prepare" : job.action === "service-prepare" && job.team === team));
  const recovery = (team === "platform" ? !version : !service) ? preparationRecovery(prepareJob) : null;
  const serviceSubmitted = Boolean(service?.submitted || jobs.some(job => job.cloudDomain === controls.session?.cloudDomain && job.release === service?.releaseHandle && job.action === "service-publish" && job.state === "COMPLETED"));
  const row = team === "platform" ? undefined : services[team];
  const serviceId = service?.serviceId ?? (team === "platform" ? undefined : inventory?.teamServiceIds?.[team]);
  const servicePending = hasServicePending(row);
  const publicationBlockedReason = controls.blockReason ?? (lifecycleRestricted ? "Finish the interrupted run before preparing or publishing again." : !present ? "Create a controller first." : team === "platform"
    ? pending ? "Another component update is pending; inspect its Cloud state before publishing again." : submitted ? "This candidate was already submitted. Observe its existing publication; it will not be sent twice." : !version ? "Prepare this capability profile before signing and publishing." : null
    : servicePending ? "A service update is pending; inspect its Cloud state before publishing again." : serviceSubmitted ? "This candidate was already submitted. Refresh its publication or prepare a higher release." : !service ? "Prepare this service profile before signing and publishing." : null);
  const openView = (next: Perspective) => { navigate(next); setPopup(null); setDetails(null); };
  const openBackend = (next: "brake" | "tire" | "cloud") => { setDetails(null); setPopup(next); };
  useEffect(() => {
    if (window.location.hash === "#native-header") return;
    return cloud.enter();
  }, [cloud.enter]);
  const observedPerspective = useRef(perspective);
  useEffect(() => {
    if (observedPerspective.current === perspective) return;
    observedPerspective.current = perspective;
    // Reconcile on navigation without pretending that the workspace was hidden.
    if (window.location.hash !== "#native-header") cloud.refresh();
  }, [perspective, cloud.refresh]);
  useEffect(() => {
    const open = () => { setSessionTab("Lifecycle"); setSessionOpen(true); };
    window.addEventListener("presenter-session", open);
    return () => window.removeEventListener("presenter-session", open);
  }, []);
  const ask = (command: DemoCommand) => {
    // A partial retirement must not revive or republish into the same run.
    // Continue only its recorded cleanup, or perform read-only observations.
    if (lifecycleRestricted && !["reset", "observe-test", "cloud-status", "service-observe", "inspect", "verify", "cloud-access"].includes(command.action)) return;
    controls.request(command);
  };
  const create = () => ask({ action: mode === "quick" ? "prepare-demo" : "create", image });

  // This guide explains observed state; it never starts an operation itself.
  let guide = { title: "Create your vehicle", body: "Choose the factory firmware for its domain controller.", label: mode === "quick" ? "Prepare demo" : "Create controller", disabled: !image, action: create };
  if (interruptedRun) guide = { title: "Demo interrupted", body: `${local.lifecycle?.reason ? `${local.lifecycle.reason}. ` : ""}Same-run restart is not supported in Demo Studio. Finish this run, then create a fresh controller.`, label: "Finish demo", disabled: controls.blocked, action: () => ask({ action: "reset" }) };
  else if (present && continuation) guide = { title: "Continue preparation", body: local.lifecycle?.reason ?? local.preparation?.reason ?? "Continue only the remaining recorded steps.", label: "Continue preparation", disabled: !image, action: create };
  else if (present && !simulationRunning) guide = { title: "Start the local vehicle", body: "Start CARLA, Gateway and the native vehicle panels. The controller connects after Cloud provisioning.", label: "Start simulator", disabled: !running, action: () => ask({ action: "start-simulation" }) };
  else if (present && !local.registrationComplete) {
    const hasRegistration = local.registrationStarted === true || value?.lifecycle === "provisioned";
    guide = publishedAny || hasRegistration
      ? { title: hasRegistration ? "Complete Cloud registration" : "Provision your vehicle", body: "Register in Test Vehicles, confirm Cloud Online, then connect the running Gateway in stationary Manual. The simulator and scene stay unchanged.", label: hasRegistration ? "Continue registration" : "Provision to Test", disabled: false, action: () => ask({ action: "provision" }) }
      : { title: "Prepare the platform release", body: "The Platform Team publishes software before the vehicle is provisioned.", label: "Open Platform", disabled: false, action: () => openView("platform") };
  } else if (present && !connected) guide = { title: "Connect the domain controller", body: "Connect the provisioned controller in stationary Manual without restarting the simulator.", label: "Connect in Manual", disabled: !running, action: () => ask({ action: "connect-test" }) };
  else if (present && !componentCurrent) guide = { title: "Observe the current controller", body: "Cloud state is not current. Previous reports are not live confirmation.", label: "Refresh Cloud state", disabled: cloud.loading, action: cloud.refresh };
  else if (present && vdpIssue) guide = { title: "Component update issue", body: `${vdpIssue}. Safe Stop does not resolve this reported error. Inspect the Cloud report or finish this run.`, label: "Open Platform", disabled: false, action: () => openView("platform") };
  else if (present && pending) guide = { title: "Component update pending", body: `${pendingDescription}. Use native Safe Stop when ready; installation is owned by the vehicle.`, label: "Open Platform", disabled: false, action: () => openView("platform") };
  else if (present && publishedAny && installed === "0.0.0") guide = { title: "First platform update", body: "Drive the vehicle, then use native Safe Stop. Observe the installed release here; no Apply button is needed.", label: "Refresh Cloud state", disabled: cloud.loading, action: cloud.refresh };
  else if (present && installed && installed !== "0.0.0" && !installedProfile) guide = { title: "Installed profile not confirmed", body: `Cloud reports release ${installed}; its functional profile is not yet bound to the published package. This does not mean that the component is absent.`, label: "Open Platform", disabled: false, action: () => openView("platform") };
  else if (present && profileEvidence?.state === "STALE") guide = { title: "Refresh installed profile", body: "The profile binding is last known. Refresh Cloud state before treating software compatibility as current.", label: "Refresh Cloud state", disabled: cloud.loading, action: cloud.refresh };
  else if (present && !servicesCurrent) guide = { title: "Observe service inventory", body: "Service reports are not current; software progress is not confirmed.", label: "Refresh Cloud state", disabled: cloud.loading, action: cloud.refresh };
  else if (present && Object.values(services).some(item => item && (serviceIssue(item) || item.service_versions?.installed_service_version?.version && !serviceRunning(item, item.service_versions.installed_service_version.version, Boolean(servicesCurrent))))) guide = {
    title: "Service runtime not confirmed", body: Object.values(services).map(serviceIssue).find(Boolean) ?? "The installed release does not yet have a current active instance report. Refresh Cloud state; Safe Stop is not required for services.", label: "Refresh Cloud state", disabled: cloud.loading, action: cloud.refresh };
  else if (present && Object.values(services).some(hasServicePending)) guide = {
    title: "Service update pending", body: `${(["brake", "tire"] as const).filter(team => hasServicePending(services[team])).map(team => `${labels[team]} ${services[team]?.service_versions?.pending_service_version?.version ?? "· version not reported"}`).join("; ")}. Waiting for Cloud installation and runtime reports. Do not publish again; Safe Stop is not required for services.`,
    label: "Refresh Cloud state", disabled: cloud.loading, action: cloud.refresh };
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
    guide = next === "global" ? { title: "Software story complete", body: "Installed releases and backend results observed. Check in-vehicle advisory in native telemetry. Finish when ready; confirmation follows.", label: "Finish demo", disabled: controls.blocked, action: () => ask({ action: "reset" }) }
      : { title: resultNeeded ? `Next in the demo: ${labels[next]} result` : "Next software profile", body: resultNeeded ? "Open the team's backend to inspect input, activity and result delivery." : "Prepare and publish the next capability. Skipped earlier profiles are not claimed demonstrated.", label: `Open ${labels[next]}${resultNeeded ? " backend" : ` ${level}`}`, disabled: false,
        action: () => { if (resultNeeded && (next === "brake" || next === "tire")) openBackend(next); else { setProfiles(previous => ({ ...previous, [next]: level })); openView(next); } } };
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
  if (recovery && present && !lifecycleRestricted) guide = { title: "Preparation needs engineering setup", body: recovery, label: "View progress", disabled: false, action: () => setTraceOpen(true) };
  if (controls.session?.active) guide = { title: "Operation in progress", body: "Demo Control owns the current operation. Follow its actual receipt in Trace; no action is repeated automatically.", label: "View progress", disabled: false, action: () => setTraceOpen(true) };
  const title = perspective === "global" ? "Your vehicle" : `${labels[perspective]} Team`;
  const cloudState = current ? value?.online ?? "UNKNOWN" : "UNKNOWN";
  const cloudLabel = !localStateKnown ? "Controller state unavailable" : !present && !inventory && !value ? "No controller created" : !local.registrationComplete && !inventory?.unitId && value?.lifecycle !== "provisioned" ? local.registrationStarted ? "Registration incomplete" : "Not provisioned" : current ? cloudState : value ? "Last known Cloud report" : !observation ? "Cloud not yet observed" : "Cloud unavailable";
  const scopedJob = activeJob ?? jobs.at(-1) ?? null;
  const closeSession = () => setSessionOpen(false);
  return <div className="studio-workspace" data-testid="studio-workspace">
    <div className="studio-main" inert={Boolean(popup || details || sessionOpen || traceOpen)} aria-hidden={popup || details || sessionOpen || traceOpen ? true : undefined}>
    <ClientBuildNotice />
    <FinishAcknowledgement jobs={controls.session?.jobs ?? []} noController={noController} />
    <nav className="studio-nav" aria-label="Demo perspectives">{(["global", "platform", "brake", "tire"] as const).map(name => <button key={name} aria-label={name === "global" ? "Vehicle" : `${labels[name]} Team`} aria-pressed={perspective === name} onClick={() => openView(name)}><StudioIcon name={name === "global" ? "vehicle" : name} />{labels[name]}</button>)}</nav>
    <div className="studio-topline"><h1>{title}</h1>{perspective === "global" ? <div className="studio-preparation"><label>Preparation <select aria-label="Preparation" value={mode} onChange={event => setMode(event.target.value)}><option value="story">Full story</option><option value="quick">Quick preparation</option></select></label><div className="studio-meta"><span>Test Vehicle · {cloudLabel}</span><span>Production · Deferred</span></div></div> : <span>Test Vehicle · {cloudLabel}</span>}</div>
    <div className="studio-body">
      {perspective === "global" && <>
        <div ref={architecture} className="studio-architecture-stage">
          <ArchitectureWires element={architecture} cloudState={cloudState} brake={Boolean(services.brake?.service_versions?.installed_service_version)} tire={Boolean(services.tire?.service_versions?.installed_service_version)} />
          <div className="studio-backends">{(["brake", "tire", "cloud"] as const).map(name => <button key={name} data-team={name === "cloud" ? "platform" : name} data-anchor={`${name}-backend`} aria-label={name === "cloud" ? "Aos Cloud Unit monitoring" : `${labels[name]} backend Open dashboard`} onClick={() => openBackend(name)}>
            <span className="studio-summary-heading"><StudioIcon name={name} /><strong>{name === "cloud" ? "Aos Cloud" : `${labels[name]} backend`}</strong></span>
            {name === "cloud" ? <CloudSummary observation={bindingMatches ? observation : null} cloudLabel={cloudLabel} />
              : <BackendSummary team={name} model={backendModels[name]} noController={noController} version={services[name]?.service_versions?.installed_service_version?.version ?? undefined} binding={backendBindings[name]} />}
            <span className="studio-summary-link"><span>{name === "cloud" ? "Unit monitoring ↗" : "Backend details ↗"}</span>{name === "cloud" && <small className="studio-platform-brand">AosEdge platform</small>}</span>
          </button>)}</div>
          <div className="studio-architecture"><aside className="studio-gateway"><StudioIcon name="vehicle" /><strong>Vehicle</strong><small>Sensors & actuators</small><span>↓</span><StudioIcon name="gateway" /><strong>Vehicle Gateway</strong><small>VSS telemetry</small></aside><div className="studio-vss-line" />
            <section className="studio-controller" data-anchor="controller"><h2><StudioIcon name="platform" />Domain Controller</h2>
              <div className="studio-service-slots">{(["brake", "tire"] as const).map(name => {
                const item = services[name], release = item?.service_versions?.installed_service_version?.version;
                const empty = noController || servicesCurrent && (!inventory?.services.value?.length || Boolean(inventory?.teamServiceIds?.[name] && !item));
                return <button key={name} data-team={name} data-anchor={`${name}-service`} className={!release ? "empty-slot" : ""} aria-label={empty ? `Empty ${name} service slot` : `${labels[name]} service details`} onClick={() => item ? setDetails({ kind: "service", row: item }) : openView(name)}>
                  {release ? <><StudioIcon name={name} /><strong>{labels[name]} Health</strong><small>{serviceProfile(item, releases) ?? "Service"} · {release}{servicesCurrent ? "" : " · last known"}</small></> : <span>{empty ? "Empty service slot" : "Service not observed"}</span>}
                </button>;
              })}</div>
              <button className="studio-vdp" onClick={() => { const row = inventory?.components.value?.find(row => row.type?.endsWith("-vehicle-data-provider")); if (row) setDetails({ kind: "component", row }); else openView("platform"); }}><StudioIcon name="component" /><strong>Vehicle Data Platform</strong><small>{installed ? `${installed === "0.0.0" ? "Factory baseline" : installedProfile ?? "Release"} · ${installed}${componentCurrent && profileEvidence?.state !== "STALE" ? "" : " · last known"}` : "Factory slot · no Cloud report"}</small></button>
              <footer className="studio-factory" data-team="platform"><div className="studio-core"><StudioIcon name="service" /><div><strong>AosCore</strong><small>In-vehicle runtime</small></div><small className="studio-platform-brand">AosEdge platform</small></div><label>Factory firmware<select aria-label="Factory image" value={image} disabled={present} onChange={event => setSelectedImage(event.target.value)}>{present && !image && <option value="">{vehicle.imageVersion ?? "Current image not reported"}</option>}{local.images.map(row => <option key={row.selector} value={row.selector}>{row.version}</option>)}</select></label></footer>
            </section></div>
        </div>
      </>}
      {perspective !== "global" && <section className="studio-release"><header><StudioIcon name={team === "platform" ? "component" : "service"} /><div><h2>{team === "platform" ? "Vehicle Data Platform" : `${labels[team]} Health Service`}</h2><p>{team === "platform" ? "Platform Team · OEM" : `${labels[team]} Team · Service Provider`}</p></div></header>
        <div className="studio-profile-cards" role="group" aria-label="Capability profile">{profileText[team].map((name, n) => <button key={name} aria-pressed={profile === `v${n + 1}`} onClick={() => setProfiles(previous => ({ ...previous, [team]: `v${n + 1}` as Profile }))}><strong>v{n + 1}</strong><span>{name}</span></button>)}</div>
        <div className="studio-release-stages">{["Prepared", "Published", team === "platform" ? "Installed" : "Running"].map((stage, index) => {
          const done = team === "platform" ? [Boolean(version), published, Boolean(version && componentCurrent && installed === version)]
            : [Boolean(service), service?.publication.stage === "READY", serviceRunning(row, service?.version, Boolean(servicesCurrent))];
          return <div key={stage} className={done[index] ? "complete" : ""}><span>{index + 1}</span><strong>{stage}</strong></div>;
        })}</div>
        {publicationBlockedReason && <p className="studio-action-reason">{publicationBlockedReason}</p>}
        {team === "platform" ? <><p>{version ? `Selected candidate · ${profile} · ${version}` : "No candidate prepared for this profile."}</p><div className="studio-buttons">
          <button disabled={controls.blocked || lifecycleRestricted || !present} onClick={() => ask({ action: "prepare", profile })}>Prepare {profile}</button>
          <button disabled={controls.blocked || lifecycleRestricted || !version || submitted || pending} onClick={() => ask({ action: "publish", version })}>Sign & publish</button></div>
          {submitted && !published && <p role={failedState(publication?.stage) ? "alert" : undefined}>Cloud {failedState(publication?.stage) ? "publication failed" : "processing"} · {publication?.stage ?? "Awaiting observation"}{publication?.reason ? ` · ${publication.reason}` : ""}</p>}
          <p role={vdpIssue ? "alert" : undefined}>{vdpIssue ? `Component update issue · ${vdpIssue}` : pending ? `${pendingDescription} is pending${componentCurrent ? ". Use native Safe Stop when ready." : " · last known report."}` : "Publication can deliver to an eligible Test immediately. No validation-batch approval step."}</p>
          <div className="studio-observed"><strong>Cloud installed · {known(installed)}{installed && !componentCurrent ? " · last known" : ""}</strong><span>Process state: not reported by Cloud.</span></div></>
        : <><div className="studio-mock-notice">{service?.demoMockedData ? "Configured data path: synthetic service data · no KUKSA access" : "Configured data path: native KUKSA inputs · connection is verified separately in the backend"}</div><p>{service ? `Selected candidate · ${profile} · ${service.version}` : "No candidate prepared in this run."}</p><div className="studio-buttons">
          <button disabled={controls.blocked || lifecycleRestricted || !present} onClick={() => ask({ action: "service-prepare", team, profile })}>Prepare {profile}</button>
          <button disabled={controls.blocked || lifecycleRestricted || !service || serviceSubmitted || servicePending} onClick={() => ask({ action: "service-publish", release: service?.releaseHandle })}>Sign & publish</button>
          {!row && <button disabled={controls.blocked || lifecycleRestricted || service?.publication.stage !== "READY" || !serviceId || !local.registrationComplete || !servicesCurrent} onClick={() => ask({ action: "service-assign", serviceId })}>Deploy to Test</button>}
          {service && <button disabled={controls.readBlocked || !serviceSubmitted} onClick={() => ask({ action: "service-observe", release: service.releaseHandle })}>Refresh publication</button>}
          {service && <button onClick={() => setDetails({ kind: "release", row: service })}>Package details</button>}</div>
          {serviceSubmitted && <p>Cloud publication · {service?.publication.stage ?? "Awaiting observation"}{service?.publication.reason ? ` · ${service.publication.reason}` : ""}</p>}
          {!row && service?.publication.stage === "READY" && (!serviceId || !local.registrationComplete || !servicesCurrent) && <p>Deploy requires a Cloud service identity, completed Test registration and a current service inventory.</p>}
          <p>{row ? "This service is already assigned. Higher releases replace it without another Deploy or Safe Stop." : "After publication, Deploy binds this service's Subject to current Test. No Safe Stop is required."}</p>
          <ServiceRows current={Boolean(servicesCurrent)} rows={row ? { state: inventory?.services.state ?? "UNKNOWN", value: [row] } : undefined} onSelect={row => setDetails({ kind: "service", row })} />
          <button className="studio-text-action" onClick={() => openBackend(team)}>Open {labels[team]} backend ↗</button></>}
      </section>}
    </div>
    <aside className="studio-guide"><div><small>DEMO STORY</small><strong>{guide.title}</strong><p>{guide.body}</p>{controls.blockReason && <small>{controls.blockReason}</small>}</div><button disabled={guide.disabled || (controls.blocked && !/^(Open |Refresh |View progress)/.test(guide.label))} onClick={guide.action}>{guide.label}</button></aside>
    <footer className="studio-footer"><span title={observation?.reason ?? undefined}>{cloud.loading ? "Reading Aos Cloud · " : `${cloudLabel} · `}<ObservationTime value={observation?.observedAt} /></span><button onClick={cloud.refresh} disabled={cloud.loading}>Refresh</button><button onClick={() => setTraceOpen(true)}>Trace · {jobs.length}</button><button className="studio-local-session" onClick={() => { setSessionTab("Lifecycle"); setSessionOpen(true); }}>Session</button></footer>
    </div>
    {popup && <Modal variant="studio" accent={popup === "cloud" ? "platform" : popup} title={popup === "cloud" ? "Cloud monitoring" : (popup === "brake" ? "Brake backend" : "Tire backend")} subtitle={noController ? "No controller created · setup preview" : "Current Test · observed data"} onClose={() => { setPopup(null); setDetails(null); }}>
      {popup === "cloud" ? <>
<div className="studio-panel-title"><span>Software and resources reported by Aos Cloud</span><button disabled={cloud.loading || resources.busy} onClick={() => { cloud.refresh(); resources.refresh(); }}>Refresh Cloud state</button></div>
        <p className="studio-function-stamp">Unit connection · {cloudLabel}. Inventory and instance states are retained Cloud reports, not proof of live telemetry or a product result.</p>
        <div className="studio-pills">{["Software", "Resources"].map(tab => <button key={tab} aria-pressed={monitorTab === tab} onClick={() => setMonitorTab(tab)}>{tab}</button>)}</div>
        {monitorTab === "Software" ? <><h3>Components</h3><div className="studio-inventory studio-component-grid">{inventory?.components.value?.map((row, n) => <button key={n} onClick={() => setDetails({ kind: "component", row })}><strong>{componentName(row)}</strong><span>{known(row.installed_component?.version)}{componentCurrent ? "" : " · last known"}</span><small>{componentUpdateLabel(row, Boolean(componentCurrent))}</small></button>)}</div>
          {!inventory?.components.value?.length && <p>{!present ? "Create the controller to begin." : !local.registrationComplete ? "Provision Test to observe its Cloud software inventory." : inventory?.components.reason ?? (componentCurrent ? "No components reported by Cloud." : "Component inventory not available.")}</p>}
          <h3>Services & instances</h3><ServiceRows current={Boolean(servicesCurrent)} rows={inventory?.services} onSelect={row => setDetails({ kind: "service", row })} /></>
          : <Monitoring key={inventory?.unitId} inventory={inventory} observation={resources} />}

      </> : noController ? <p>Create and provision Test, then install {labels[popup]} Health. No vehicle data is expected before setup.</p> : <BackendEvidence key={popup + observationScope} team={popup} retiring={lifecycleRestricted} unitSystemUid={inventory?.systemUid} expectedVersion={services[popup]?.service_versions?.installed_service_version?.version ?? undefined} binding={backendBindings[popup]} observation={backendModels[popup]} />}
    </Modal>}
    {traceOpen && <Modal variant="studio" title="Current run activity" subtitle="Actual Demo Control receipts · no simulated transitions" onClose={() => setTraceOpen(false)}><OperationProgress job={scopedJob} /><FinishAcknowledgement jobs={controls.session?.jobs ?? []} noController={noController} emptyMessage={!jobs.length && !activeJob ? "No operations recorded for the current run." : undefined} />{jobs.map(job => <article className="studio-trace-row" key={job.id}><strong>{job.action} · {job.state}</strong><p>{job.results.at(-1)?.message ?? job.reason}</p><small>{stamp(job.finishedAt ?? job.startedAt)}</small></article>)}</Modal>}
    {!traceOpen && (controls.error || controls.session?.active || scopedJob && !["COMPLETED", "OBSERVED"].includes(scopedJob.state)) && <OperationProgress job={controls.session?.jobs.find(job => job.id === controls.session?.active) ?? scopedJob} />}
    {!sessionOpen && <WorkspacePlacement vehicleWindowsAbsent={vehicleWindowsAbsent} />}
    {sessionOpen && <Modal variant="studio" title="Demo session" subtitle="Current Test only · Production remains unchanged" onClose={closeSession}>
      <div className="studio-pills" role="group" aria-label="Session sections">{["Lifecycle", "Cloud", "Test setup"].map(tab => <button key={tab} aria-pressed={sessionTab === tab} onClick={() => setSessionTab(tab)}>{tab}</button>)}</div>
      {sessionTab === "Cloud" && <CloudConnectionPanel section="connection" />}
      {sessionTab === "Test setup" && <CloudConnectionPanel section="setup" />}
      {sessionTab === "Lifecycle" && <><WorkspacePlacement session vehicleWindowsAbsent={vehicleWindowsAbsent} /><p>Use Safe Stop in Driving Control for a pause; keep the controller running. Finish before shutting down. Start a fresh run next time.</p>
      <div className="studio-session-grid"><button disabled={controls.blocked} onClick={() => { closeSession(); ask({ action: "reset" }); }}>Finish demo</button><p>Retire the owned Test and its working data. Preserve Factory originals and release continuity.</p></div></>}</Modal>}
    {details && <Modal variant="studio" title={details.kind === "component" ? componentName(details.row) : details.kind === "service" ? details.row.service?.title ?? "Service" : "Prepared service package"} subtitle={details.kind === "release" ? "Demo Control · authoring metadata" : "Current Test · Aos Cloud observation"} onClose={() => setDetails(null)}>
      {details.kind === "component" ? <ComponentDetails row={details.row} current={Boolean(componentCurrent)} /> : details.kind === "service" ? <><ServiceRows rows={{ state: inventory?.services.state ?? "UNKNOWN", value: [details.row] }} current={Boolean(servicesCurrent)} /><ServiceCompatibility evidence={profileEvidence} team={details.row.service?.id ? (["brake", "tire"] as const).find(team => services[team]?.service?.id === details.row.service?.id) : undefined} profile={serviceProfile(details.row, releases)} current={Boolean(componentCurrent && servicesCurrent)} /><p>Instance state is the last Cloud report, not proof of live telemetry or a product result.</p></>
      : <dl className="detail-grid"><dt>Service</dt><dd>{details.row.team}</dd><dt>Profile / release</dt><dd>{details.row.contentProfile} · {details.row.version}</dd><dt>Architecture</dt><dd>ARM64</dd><dt>Data mode</dt><dd>{details.row.demoMockedData ? "Synthetic · no KUKSA access" : "Native inputs"}</dd><dt>Instances</dt><dd>minInstances: 1</dd><dt>Offline lifetime</dt><dd>P7D</dd><dt>Publication</dt><dd>{details.row.publication.stage ?? "Not published"}</dd><dt>Signed bundle SHA-256</dt><dd>{details.row.sha256 ?? "Not signed"}</dd></dl>}
    </Modal>}
  </div>;
}
