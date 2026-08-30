import type { TeamView } from "../../domain";
import { Icon, ReleaseCard, SourceStamp, StatusBadge } from "../../shared/components";

export function BrakeHeading({ team }: { team: TeamView }) {
  return <div className="team-heading"><h1>{team.name}</h1><p>— {team.purpose}</p></div>;
}

export function BrakeSummaries({ team, vehicleLabel }: { team: TeamView; vehicleLabel: string }) {
  return (
    <div className="summary-grid">
      <div className="summary-card"><label>Current Vehicle</label><b>{vehicleLabel}</b><small>Audience evidence context</small></div>
      <div className="summary-card"><label>Reported Service</label><b>{team.productStatus}</b><small>Brake-owned lifecycle</small></div>
      <div className="summary-card"><label>Team lifecycle</label><b>{team.lifecycleStatus}</b><small>No Platform/Tire state transfer</small></div>
    </div>
  );
}

export function BrakeEvidence({ team, assetFailure, onLogs }: { team: TeamView; assetFailure: boolean; onLogs: () => void }) {
  const resources = team.brakeResources;
  return (
    <section className="evidence-panel">
      <div className="evidence-head"><b><Icon name="brake" label="Brake" broken={assetFailure} />{team.evidenceTitle}</b><StatusBadge status={team.backendStatus} /></div>
      <p>{team.evidenceBody}</p>
      {resources ? (
        <div className="isolation-facts" data-testid="brake-read-projection">
          {resources.value?.map((item) => (
            <span key={item.resourceType}>{item.resourceType} <b>{item.state} · {item.count}</b></span>
          )) ?? <span>Brake state <b>{resources.state} · {resources.transport}</b></span>}
        </div>
      ) : null}
      <div className="isolation-facts"><span>Approved quota <b>{team.quota}</b></span></div>
      <div className="evidence-actions"><button className="button" type="button" onClick={onLogs}><Icon name="logs" label="Operational Logs" broken={assetFailure} /> Operational Logs</button></div>
      {resources ? <SourceStamp observed={resources} /> : <SourceStamp observed={team.source} />}
    </section>
  );
}

export function BrakeReleaseStory({ team, assetFailure, onDetails, onAction }: {
  team: TeamView;
  assetFailure: boolean;
  onDetails: (releaseId: string) => void;
  onAction: (releaseId: string, action: string) => void;
}) {
  return <>{team.releases.map((item) => <ReleaseCard key={item.id} release={item} assetFailure={assetFailure} onDetails={() => onDetails(item.id)} onAction={(action) => onAction(item.id, action)} />)}</>;
}
