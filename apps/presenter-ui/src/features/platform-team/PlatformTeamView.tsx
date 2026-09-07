import type { TeamView, PlatformCloudObservation } from "../../domain";
import { Icon, ReleaseCard, SourceStamp, StatusBadge } from "../../shared/components";

export function PlatformHeading({ team }: { team: TeamView }) {
  return <div className="team-heading"><h1>{team.name}</h1><p>— {team.purpose}</p></div>;
}

export function PlatformSummaries({ team, vehicleLabel }: { team: TeamView; vehicleLabel: string }) {
  return (
    <div className="summary-grid">
      <div className="summary-card"><label>Current Vehicle</label><b>{vehicleLabel}</b><small>One audience evidence context</small></div>
      <div className="summary-card"><label>Reported by AosEdge</label><b>{team.productStatus}</b><small>Observed Platform state</small></div>
      <div className="summary-card"><label>Team lifecycle</label><b>{team.lifecycleStatus}</b><small>Independent from Services</small></div>
    </div>
  );
}

export function PlatformEvidence({ team, assetFailure, onLogs, cloud }: { team: TeamView; assetFailure: boolean; onLogs: () => void;
  cloud?: { observation: PlatformCloudObservation | null; loading: boolean; refresh: () => void } }) {
  const value = cloud?.observation?.value;
  return (
    <section className="evidence-panel">
      <div className="evidence-head"><b><Icon name="platform" label="Platform" broken={assetFailure} />{team.evidenceTitle}</b><StatusBadge status={team.backendStatus} /></div>
      {cloud && <>
        <dl className={`platform-cloud-facts${cloud.observation?.state === "CURRENT" ? "" : " stale-observation"}`}>
          <div><dt>Cloud connection</dt><dd>{value?.online ?? "Not observed"}</dd></div>
          <div><dt>Unit lifecycle</dt><dd>{value?.lifecycle ?? "Not observed"}</dd></div>
          <div><dt>Installed release</dt><dd>{value?.installedVersion ?? "Not reported"}</dd></div>
          <div><dt>Pending release</dt><dd>{value?.pendingVersion ?? (value ? "None reported" : "Not observed")}</dd></div>
          <div><dt>Update state</dt><dd>{value?.updateStatus ?? "Not reported"}</dd></div>
          <div><dt>Latest published</dt><dd>{value?.latestPublishedVersion ?? "Not reported"}</dd></div>
        </dl>
        <button className="button" disabled={cloud.loading} onClick={cloud.refresh}>{cloud.loading ? "Reading Aos Cloud…" : "Refresh Cloud state"}</button>
        {cloud.observation?.state === "STALE" && <p role="status">Previous observation — not current.</p>}
      </>}
      <p>{team.evidenceBody}</p>
      <div className="evidence-actions"><button className="button" type="button" disabled={!team.source.source.fixture && !team.logs} onClick={onLogs}><Icon name="logs" label="Platform Logs" broken={assetFailure} /> Platform Logs</button></div>
      <SourceStamp observed={team.source} />
    </section>
  );
}

export function PlatformReleaseStory({ team, assetFailure, onDetails, onAction }: {
  team: TeamView;
  assetFailure: boolean;
  onDetails: (releaseId: string) => void;
  onAction: (releaseId: string, action: string) => void;
}) {
  return <>{team.releases.map((item) => <ReleaseCard key={item.id} release={item} assetFailure={assetFailure} onDetails={() => onDetails(item.id)} onAction={(action) => onAction(item.id, action)} />)}</>;
}
