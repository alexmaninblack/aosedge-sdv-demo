// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { actionLabels, operationStateLabel, usePresenterControls } from "./state/PresenterControls";
import type { DemoJob } from "../domain/presenterCommandPort";

/** Always reserved; detailed receipts live in Activity, never below the flex shell. */
export function StudioStatus({ onActivity, onLayout, vehicleWindowsAbsent, job, count }: { onActivity: () => void; onLayout: () => void; vehicleWindowsAbsent: boolean; job: DemoJob | null; count: number }) {
  const controls = usePresenterControls();
  const needsAttention = Boolean(controls.error || job && !["COMPLETED", "OBSERVED", "ACCEPTED", "RUNNING"].includes(job.state));
  const placement = controls.session?.workspace;
  const layoutProblem = !vehicleWindowsAbsent && placement?.state && !["CLOSED", "PLACED_AWAITING_VISUAL_REVIEW"].includes(placement.state);
  const active = Boolean(controls.session?.active);
  const reason = controls.error ?? job?.reason ?? job?.results.at(-1)?.message;
  return <div className="studio-status-dock" aria-label="Operation and workspace status">
    <button aria-label={`Operations · ${count}`} className={needsAttention ? "needs-attention" : ""} onClick={onActivity} title={controls.error ?? job?.reason ?? undefined}>
      <span role="status">{controls.error ?? (job && (active || needsAttention) ? <>{actionLabels[job.action]} · {operationStateLabel(job.state)}{needsAttention && reason && <> · <span>{reason}</span></>}</> : "No operation in progress")}</span><span>Operations · {count}</span>
    </button>
    <button aria-label={layoutProblem ? "Desktop window layout" : "Window layout"} onClick={onLayout} className={layoutProblem ? "needs-attention" : ""}>{layoutProblem ? "Window layout could not be verified" : "Window layout"}</button>
  </div>;
}
