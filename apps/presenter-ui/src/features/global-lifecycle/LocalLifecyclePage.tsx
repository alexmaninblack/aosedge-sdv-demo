import { useState } from "react";
import type { PresenterSnapshot } from "../../domain";
import { Icon, StatusBadge } from "../../shared/components";
import { usePresenterControls } from "../../app/state/PresenterControls";
import type { DemoAction } from "../../domain/presenterCommandPort";

export function LocalLifecyclePage({ snapshot, onPlatform }: { snapshot: PresenterSnapshot; onPlatform?: () => void }) {
  const view = snapshot.localDemo!;
  const controls = usePresenterControls();
  const cloudRead = [...(controls.session?.jobs ?? [])].reverse().find((job) => job.action === "cloud-access" && job.state === "COMPLETED");
  const cloud = cloudRead?.results.at(-1)?.facts.cloud as Record<string, { state?: string; reason?: string }> | undefined;
  const [selected, select] = useState("");
  const image = view.images.find((item) => item.selector === selected) ?? view.images[0];
  const steps: [string, string, DemoAction | "platform"][] = [
    ["Create vehicles", "Copy the selected Factory image once; create fresh Test and Production overlays.", "create"],
    ["Prepare baseline VDP", "Open Platform Team: prepare the next v1 release, sign, upload and approve it before provisioning. This avoids starting with the previous v3.", "platform"],
    ["Start both VMs", "Start Test and Production; initialize roles, SSH and DNS. Access uses a visible macOS dialog or Keychain.", "start-vms"],
    ["Provision vehicles", "Provision fresh identities, assign Test Vehicles / Production Vehicles and confirm Online.", "provision"],
    ["Start simulator", "Start CARLA, Controller, Gateway and telematics without selecting a vehicle.", "start-simulation"],
    ["Connect Test Vehicle", "Connect only Test and confirm the live chain. Production remains unselected.", "connect-test"],
  ];
  return <div className="global-page local-lifecycle" data-testid="local-lifecycle-page">
    <header className="page-head"><div><h1>Demo Lifecycle</h1><p>Prepare both vehicles. Demonstrate software evolution on Test.</p></div><StatusBadge status={view.available ? "LOCAL OBSERVATIONS" : "UNAVAILABLE"} /></header>
    <section className="lifecycle-block prepare-demo-primary"><h2>Prepare demo</h2>
      <label className="image-selector">Factory image<select aria-label="Factory image" value={image?.selector ?? ""} onChange={(event) => select(event.target.value)}>
        {!image && <option value="">Catalog unavailable</option>}{view.images.map((item) => <option key={item.selector} value={item.selector}>{item.version} · {item.architecture}</option>)}</select></label>
      <p>One action prepares both vehicles, VDP v1 and the simulator connected to Test. Release numbering is automatic.</p>
      <button className="button button-primary" disabled={controls.blocked || !image || image.problems.length > 0} onClick={() => controls.request({ action: "prepare-demo", image: image!.selector })}>Prepare demo</button>
      <p className="local-observed">When ready: start Autopilot, then press Safe Stop. Reloading this page only restores progress; it never restarts preparation.</p>
      {view.preparation?.phase && <div className="preparation-state" role="status"><strong>{view.preparation.phase === "READY_TO_DRIVE" ? "Ready — start Autopilot, then press Safe Stop" : `Preparation: ${view.preparation.phase}`}</strong>
        <p>VDP {view.preparation.contentProfile} · Cloud release {view.preparation.version}</p>
        {view.preparation.reason && <p>{view.preparation.reason}</p>}<small>Native run journal · {view.preparation.updatedAt ?? "current run"}</small></div>}
    </section>
    <section className="lifecycle-block local-current-state"><h2>Current environment</h2>
      <div className="local-vehicle-grid">{(["test", "production"] as const).map((role) => {
        const vehicle = view.vehicles[role];
        return <article className="life-step" key={role}><b>{role === "test" ? "Test Vehicle" : "Production Vehicle"}</b>
          <StatusBadge status={vehicle.process ?? vehicle.reason ?? "NOT OBSERVED"} />
          <p>{vehicle.imageVersion ?? "No image assigned"}</p><small>{role === "test" ? "Active demo target · Test Vehicles" : "Preparation target · Production FOTA deferred"}</small></article>;
      })}</div>
      <p>CARLA connection: {view.source.currentVehicle ?? (view.source.selectedVehicle ? `${view.source.selectedVehicle} selected · live connection not re-probed` : "none")} · Source: {view.source.state}</p>
      <p className="local-observed">Local observation: {snapshot.observedAt || "not available"}. Cloud/guest results are separate timestamped reads, not continuous monitoring.</p>
    </section>
    <details className="lifecycle-block"><summary>Engineering steps — optional</summary>
      <p>Individual commands remain available for diagnosis. Use Prepare demo for the complete operator workflow.</p>
      <div className="local-preparation-steps">{steps.map(([title, description, action], index) => <article className="life-step" key={title}>
        <span className="step-number">{index + 1}</span><div><b>{title}</b><p>{description}</p></div>
        <button className="button" disabled={action === "platform" ? !onPlatform : controls.blocked || (action === "create" && (!image || image.problems.length > 0))}
          onClick={() => action === "platform" ? onPlatform?.() : controls.request(action === "create" ? { action, image: image!.selector } : { action })}>{title}</button>
      </article>)}</div>
    </details>
    <section className="lifecycle-block"><h2>Aos access</h2><p>Access and Online checks are explicit; they are not repeated by the background local-status refresh.</p>
      <button className="button" disabled={controls.blocked} onClick={() => controls.request({ action: "cloud-access" })}>Check Cloud access and Units</button><div className="local-vehicle-grid">
      {Object.entries(view.access).map(([name, access]) => <article className="life-step" key={name}><b>{name === "oem-delivery" ? "OEM" : "Service Provider"}</b>
        <p>Local access material: {access.present ? "present" : "missing"}</p><StatusBadge status={cloud?.[name]?.state ?? "CLOUD NOT CHECKED"} />
        {cloud?.[name] && <small>Last explicit read: {cloudRead?.finishedAt ?? cloudRead?.startedAt}{cloud[name]?.reason ? ` · ${cloud[name]?.reason}` : ""}</small>}</article>)}
      {!view.available && <p>Access information unavailable.</p>}
    </div></section>
    <section className="lifecycle-block"><h2>Stop without deleting</h2><div className="local-action-row">
      <button className="button" disabled={controls.blocked} onClick={() => controls.request({ action: "stop-simulation" })}>Stop simulator</button>
      <button className="button" disabled={controls.blocked} onClick={() => controls.request({ action: "stop-vms" })}>Stop both VMs</button></div></section>
    <section className="lifecycle-block"><h2><Icon name="reset" label="Reset" />End and Reset Demo</h2><p>Stop simulation, deprovision and delete both Cloud Units, then retire local overlays and the working image copy. Original artifacts remain.</p>
      <button className="button button-warning" disabled={controls.blocked} onClick={() => controls.request({ action: "reset" })}>End and reset demo</button></section>
    <p className="local-preview-notice">Local engineering integration · real actions, no full live qualification claim.</p>
  </div>;
}
