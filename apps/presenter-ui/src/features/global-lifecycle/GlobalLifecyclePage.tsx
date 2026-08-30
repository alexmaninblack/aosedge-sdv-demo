import type { GlobalLifecycleView } from "../../domain";
import { usePresenterReadModel } from "../../app/state/PresenterReadModelProvider";
import { Icon, SourceStamp, StatusBadge } from "../../shared/components";

const lifecycleLabels: Record<GlobalLifecycleView["stage"], string> = {
  READY_FOR_M0: "Ready to create vehicles",
  M0: "Vehicles created",
  M1: "Vehicles provisioned",
  G0: "Managed vehicles ready",
  ACTIVE: "Software evolution in progress",
  R0: "Demo reset complete",
  RECOVERY_REQUIRED: "Recovery required",
};

export function GlobalLifecyclePage({ view, assetFailure, eventChain, onAction }: {
  view: GlobalLifecycleView;
  assetFailure: boolean;
  eventChain: string[];
  onAction: (action: string) => void;
}) {
  const readOnly = usePresenterReadModel().readOnly;
  const qualification = view.qualification.value;
  const currentLifecycle = lifecycleLabels[view.stage];
  return (
    <div className="global-page" data-testid="global-lifecycle-page">
      <header className="page-head">
        <div><h1>Demo Lifecycle</h1><p>Qualification, preparation, current lifecycle, recovery and terminal reset.</p></div>
        <StatusBadge status={`Current lifecycle · ${currentLifecycle}`} />
      </header>
      <section className="lifecycle-block">
        <div className="qualification-panel">
          <Icon name="qualification" label="Qualification evidence" broken={assetFailure} />
          <div><b>Qualification Status · {qualification?.status ?? "ABSENT"}</b><p>{qualification?.reason}</p></div>
          <StatusBadge status={qualification?.status ?? "ABSENT"} />
        </div>
        <SourceStamp observed={view.qualification} />
      </section>
      {readOnly ? (
        <section className="lifecycle-block" data-testid="read-only-cloud-state">
          <h2>AosEdge source state · fixture — not live</h2>
          <p>Current facts are a contract-synthetic, GET-only projection. Friendly lifecycle labels remain a separate derived presentation.</p>
          <div className="lifecycle-steps">
            {readOnly.bindings.value?.map((binding) => (
              <article className="life-step" key={binding.role}>
                <b>{binding.label}</b>
                <p>{binding.wireRole} · {binding.unitFingerprint} · Main {binding.mainNodeFingerprint}</p>
                <StatusBadge status={readOnly.bindings.state} />
              </article>
            ))}
            <article className="life-step">
              <b>Persistent role Unit Sets</b>
              <p>{readOnly.unitSets.value?.map((set) => `${set.title}: ${set.memberUnitFingerprints.length} member`).join(" · ") ?? "Current membership cannot be confirmed"}</p>
              <StatusBadge status={readOnly.unitSets.state} />
            </article>
            <article className="life-step">
              <b>Distinct release objects</b>
              <p>{readOnly.releases.value?.map((item) => `${item.kind}: ${item.state}`).join(" · ") ?? "Current release state cannot be confirmed"}</p>
              <StatusBadge status={readOnly.releases.state} />
            </article>
          </div>
          <SourceStamp observed={readOnly.session} />
          <SourceStamp observed={readOnly.units} />
          <SourceStamp observed={readOnly.unitSets} />
        </section>
      ) : null}
      <section className="lifecycle-block">
        <h2><Icon name="vehicle" label="Prepare Demo" broken={assetFailure} />Prepare Demo</h2>
        <p>Vehicle production and provisioning remain separate explicit operations. Start/restore environment and workspace-layout actions remain native and are not duplicated here.</p>
        <div className="lifecycle-steps">
          <article className="life-step" data-complete={view.manufactured}><b>Produce Test and Production Vehicles</b><p>Create fresh Test and Production vehicles from the qualified OEM Factory Image. They do not have Cloud identities yet.</p><button className="button button-primary" onClick={() => onAction("Create Test and Production Vehicles")}>Create Vehicles</button></article>
          <article className="life-step" data-complete={view.provisioned}><b>Bring Vehicles Under AosEdge Management</b><p>Provision both produced vehicles, create fresh Unit and Node identities, assign their Test and Production groups, and confirm that they are online.</p><button className="button button-primary" onClick={() => onAction("Provision Produced Vehicles")}>Provision Vehicles</button></article>
          <article className="life-step" data-complete={view.stage === "G0" || view.stage === "ACTIVE"}><b>Managed Vehicles Ready</b><p>Both vehicles are managed by AosEdge. The Test Vehicle is current; post-SOP platform components and Services are not installed yet.</p><StatusBadge status={view.stage === "G0" || view.stage === "ACTIVE" ? "READY" : "WAITING"} /></article>
        </div>
      </section>
      <section className="lifecycle-block">
        <h2>Current global lifecycle</h2>
        <p>{view.milestone}. Derived from independent release facts; never written as an authoritative Cloud lifecycle field.</p>
        <StatusBadge status={currentLifecycle} />
      </section>
      <section className="lifecycle-block">
        <h2><Icon name="recovery" label="Recovery" broken={assetFailure} />Global recovery</h2>
        <p>{view.recovery}. Recovery re-reads authoritative state in later increments and never guesses or blindly retries.</p>
        <button className="button" onClick={() => onAction("Reconcile interrupted fixture operation")}>Reconcile fixture presentation</button>
      </section>
      <section className="lifecycle-block">
        <h2><Icon name="reset" label="End and Reset Demo" broken={assetFailure} />End and Reset Demo</h2>
        <p>Terminal reset leaves no Current Vehicle and requires the next run to explicitly create and provision new vehicles. Unproven cleanup remains Recovery required.</p>
        <button className="button button-warning" onClick={() => onAction("End and reset demo")}>End and reset demo</button>
      </section>
      <section className="lifecycle-block">
        <h2>Live evidence context</h2>
        <div className="event-chain">{eventChain.map((entry) => <div key={entry}>{entry}</div>)}</div>
      </section>
    </div>
  );
}
