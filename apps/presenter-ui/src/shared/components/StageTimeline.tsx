import type { ReleaseStage } from "../../domain";
import { StatusBadge } from "./StatusBadge";

export function StageTimeline({ stages, onAction }: { stages: ReleaseStage[]; onAction: (action: string) => void }) {
  return (
    <ol className="stage-timeline">
      {stages.map((stage, index) => (
        <li className={`stage stage-${stage.state}`} key={stage.id}>
          <span className="stage-marker" aria-hidden="true">{stage.state === "complete" ? "✓" : index + 1}</span>
          <div className="stage-copy">
            <div className="stage-title"><strong>{stage.label}</strong><span>{stage.actor}</span></div>
            <p>{stage.explanation}</p>
            <div className="stage-meta">
              <StatusBadge status={stage.state.toUpperCase()} />
              {stage.action && stage.state !== "complete" ? <button className="button button-primary" type="button" onClick={() => onAction(stage.action!)}>{stage.action}</button> : null}
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}
