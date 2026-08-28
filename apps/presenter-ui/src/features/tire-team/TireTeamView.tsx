import type { TeamView } from "../../domain";
import { Icon, ReleaseCard, SourceStamp, StatusBadge } from "../../shared/components";

export function TireHeading({ team }: { team: TeamView }) {
  return <div className="team-heading"><h1>{team.name}</h1><p>— {team.purpose}</p></div>;
}

export function TireSummaries({ team, vehicleLabel }: { team: TeamView; vehicleLabel: string }) {
  return (
    <div className="summary-grid">
      <div className="summary-card"><label>Current Vehicle</label><b>{vehicleLabel}</b><small>Audience evidence context</small></div>
      <div className="summary-card"><label>Reported Service</label><b>{team.productStatus}</b><small>Tire-owned lifecycle</small></div>
      <div className="summary-card"><label>Team lifecycle</label><b>{team.lifecycleStatus}</b><small>No Platform/Brake state transfer</small></div>
    </div>
  );
}

export function TireEvidence({ team, assetFailure, onLogs, onAction }: { team: TeamView; assetFailure: boolean; onLogs: () => void; onAction: (action: string) => void }) {
  return (
    <section className="evidence-panel">
      <div className="evidence-head"><b><Icon name="quota" label="Runtime Isolation Evidence" broken={assetFailure} />Runtime Isolation Evidence</b><StatusBadge status={team.isolation?.status ?? "NOT_READY"} /></div>
      <p>{team.evidenceBody} The proof is specific to the qualified VM baseline; AosCore remains the enforcement owner.</p>
      <p><strong>Function Backend:</strong> {team.backendStatus}</p>
      <div className="isolation-facts">
        <span>Tire CPU <b>{team.isolation?.tireCpu}</b></span><span>Brake <b>{team.isolation?.brake}</b></span><span>Platform <b>{team.isolation?.platform}</b></span><span>Quota <b>{team.quota}</b></span>
      </div>
      <div className="evidence-actions">
        <button className="button" type="button" onClick={() => onAction("Run bounded Tire isolation fixture")}><Icon name="quota" label="Isolation proof" broken={assetFailure} /> Run isolation proof</button>
        <button className="button" type="button" onClick={onLogs}><Icon name="logs" label="Operational Logs" broken={assetFailure} /> Operational Logs</button>
      </div>
      <SourceStamp observed={team.source} />
    </section>
  );
}

export function TireReleaseStory({ team, assetFailure, onDetails, onAction }: {
  team: TeamView;
  assetFailure: boolean;
  onDetails: (releaseId: string) => void;
  onAction: (releaseId: string, action: string) => void;
}) {
  return <>{team.releases.map((item) => <ReleaseCard key={item.id} release={item} assetFailure={assetFailure} onDetails={() => onDetails(item.id)} onAction={(action) => onAction(item.id, action)} />)}</>;
}
