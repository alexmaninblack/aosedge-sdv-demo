// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { usePresenterControls } from "./state/PresenterControls";

export function WorkspacePlacement({ session = false, vehicleWindowsAbsent = false }: { session?: boolean; vehicleWindowsAbsent?: boolean }) {
  const controls = usePresenterControls();
  const placement = controls.session?.workspace;
  const state = placement?.state;
  const restoring = controls.session?.jobs?.some(job => job.id === controls.session?.active && job.action === "workspace-restore");
  // A confirmed empty lifecycle expects CARLA/Driving Control to be closed.
  // Do not turn their old placement receipt into a current recovery warning.
  // Unknown/partial lifecycle and an actual restore retain the normal path.
  if (vehicleWindowsAbsent && !restoring) return session
    ? <section aria-label="Desktop window layout"><strong>Desktop window layout</strong><p>Vehicle windows are not running. Start the simulator during preparation; no vehicle-window recovery is needed.</p></section>
    : null;
  const problem = state && !["CLOSED", "PLACED_AWAITING_VISUAL_REVIEW"].includes(state);
  if (!session && !problem && !restoring) return null;
  const text = restoring ? "Restoring and checking window positions. The demo continues running."
    : state === "WAITING_FOR_UNLOCK" ? "Window layout is waiting for the Mac to be unlocked. Placement resumes automatically; the demo remains running."
    : state === "WAITING_FOR_WINDOWS" ? "Waiting for the demo windows to become ready. Layout verification will retry shortly."
    : state === "INCOMPLETE" ? "Window layout could not be verified. The demo may still be running; restore the layout without restarting it."
    : state === "PLACED_AWAITING_VISUAL_REVIEW" ? "Window positions verified. Check visual readability on the desktop."
    : state === "CLOSED" ? "Desktop Presenter is closed. The demo is unchanged."
    : "Restore the desktop arrangement without restarting the demo.";
  return <section className="operation-progress" role={problem ? "status" : undefined} aria-label="Desktop window layout">
    <strong>Desktop window layout</strong><p>{text}</p>
    {placement?.zOrder && !restoring && <p>{placement.zOrder.state === "VERIFIED" ? "Window order verified: the background is behind the demo windows." : "Window order is not currently verified; do not treat geometry alone as a successful layout."}</p>}
    {placement?.observedAt && <small>Last placement observation: {new Date(placement.observedAt).toLocaleTimeString()}</small>}
    <p><button className="button" disabled={controls.blocked || Boolean(placement?.retryPending)} onClick={() => controls.request({ action: "workspace-restore" })}>Restore window layout</button></p>
    {problem && placement?.problems?.length ? <details><summary>Placement details</summary><ul>{placement.problems.map((value, index) => <li key={index}>{value}</li>)}</ul></details> : null}
  </section>;
}
