import type { GlobalLifecycleView } from "../../domain";
import { Icon, SourceStamp, StatusBadge } from "../../shared/components";

export function GlobalLifecyclePage({ view, assetFailure, eventChain, onAction }: {
  view: GlobalLifecycleView;
  assetFailure: boolean;
  eventChain: string[];
  onAction: (action: string) => void;
}) {
  const qualification = view.qualification.value;
  return (
    <div className="global-page" data-testid="global-lifecycle-page">
      <header className="page-head">
        <div><h1>Demo Lifecycle</h1><p>Qualification, preparation, current lifecycle, recovery and terminal reset.</p></div>
        <StatusBadge status={`Current lifecycle · ${view.stage}`} />
      </header>

      <section className="lifecycle-block">
        <div className="qualification-panel">
          <Icon name="qualification" label="Qualification evidence" broken={assetFailure} />
          <div><b>Qualification Status · {qualification?.status ?? "ABSENT"}</b><p>{qualification?.reason}</p></div>
          <StatusBadge status={qualification?.status ?? "ABSENT"} />
        </div>
        <SourceStamp observed={view.qualification} />
      </section>

      <section className="lifecycle-block">
        <h2><Icon name="vehicle" label="Prepare Demo" broken={assetFailure} />Prepare Demo</h2>
        <p>M0 and M1 remain separate explicit operations. Start/restore environment and workspace-layout actions remain native and are not duplicated here.</p>
        <div className="lifecycle-steps">
          <article className="life-step" data-complete={view.manufactured}><label>M0</label><b>Manufacturing output</b><p>Two fresh unprovisioned overlays; no Cloud identity; Current Vehicle remains Not assigned.</p><button className="button button-primary" onClick={() => onAction("Create M0 manufacturing result")}>Prepare M0 fixture</button></article>
          <article className="life-step" data-complete={view.provisioned}><label>M1</label><b>Provision managed vehicles</b><p>Unique Test/Production Unit and Node identities, disjoint role sets and fresh Online evidence.</p><button className="button button-primary" onClick={() => onAction("Provision M1 baseline")}>Prepare M1 fixture</button></article>
          <article className="life-step" data-complete={view.stage === "G0" || view.stage === "ACTIVE"}><label>G0</label><b>Managed baseline</b><p>Test Vehicle current with fresh exclusive source; VDP and post-SOP Services absent.</p><StatusBadge status={view.stage === "G0" || view.stage === "ACTIVE" ? "READY" : "WAITING"} /></article>
        </div>
      </section>

      <section className="lifecycle-block">
        <h2>Current global lifecycle</h2>
        <p>{view.milestone}. Derived from independent release facts; never written as an authoritative Cloud lifecycle field.</p>
        <StatusBadge status={view.stage} />
      </section>

      <section className="lifecycle-block">
        <h2><Icon name="recovery" label="Recovery" broken={assetFailure} />Global recovery</h2>
        <p>{view.recovery}. Recovery re-reads authoritative state in later increments and never guesses or blindly retries.</p>
        <button className="button" onClick={() => onAction("Reconcile interrupted fixture operation")}>Reconcile fixture presentation</button>
      </section>

      <section className="lifecycle-block">
        <h2><Icon name="reset" label="End and Reset Demo" broken={assetFailure} />End and Reset Demo (R0)</h2>
        <p>Terminal reset ends at READY_FOR_M0 with no Current Vehicle and no automatic M0 or M1. Unproven cleanup remains Recovery required.</p>
        <button className="button button-warning" onClick={() => onAction("End and reset demo fixture")}>End and reset demo</button>
      </section>

      <section className="lifecycle-block">
        <h2>Live evidence context</h2>
        <div className="event-chain">{eventChain.map((entry) => <div key={entry}>{entry}</div>)}</div>
      </section>
    </div>
  );
}
