import type { ReleaseView } from "../../domain";
import { Icon } from "./Icon";
import { StageTimeline } from "./StageTimeline";
import { StatusBadge } from "./StatusBadge";

export function ReleaseCard({ release, assetFailure, onDetails, onAction }: {
  release: ReleaseView;
  assetFailure: boolean;
  onDetails: () => void;
  onAction: (action: string) => void;
}) {
  return (
    <article className="release-card" id={`release-${release.id}`} tabIndex={-1} data-release={release.id}>
      <header className="release-head">
        <span className="version-badge">v{release.version}</span>
        <div>
          <h2><Icon name={release.team} label={release.team} broken={assetFailure} /> {release.title}</h2>
          <p>{release.subtitle}</p>
          <div className="release-policies">
            <span>{release.motionPolicy}</span>
            {release.dependency ? <span>{release.dependency}</span> : null}
          </div>
        </div>
        <StatusBadge status={release.status} />
      </header>
      <div className="release-actions">
        <button className="button" type="button" data-focus-id={`${release.id}-details`} onClick={onDetails}>Details</button>
      </div>
      <StageTimeline stages={release.stages} onAction={onAction} />
    </article>
  );
}
