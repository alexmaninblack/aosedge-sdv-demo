// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { usePresenterControls } from "../../app/state/PresenterControls";
import type { BackendBinding } from "./backendSelection";
import { backendSummary, recordObject, readable, type BackendModel, type Team } from "./useBackendObservation";
import { stamp } from "../../app/StudioReadViews";

export function useResetScenario(team: Team, model: BackendModel, binding?: BackendBinding, retiring = false, runId?: string | null) {
  const controls = usePresenterControls();
  const summary = backendSummary(model, team, binding?.serviceVersion, binding);
  const reset = model.data?.observations.demoReset?.state === "OBSERVED" ? model.data.observations.demoReset.data : undefined;
  const intent = controls.resetSubmissions?.[team];
  const scope = JSON.stringify([controls.session?.cloudDomain, runId, binding?.unitSystemUid, binding?.serviceId, binding?.subjectId, binding?.instanceIndex, binding?.serviceVersion]);
  const currentIntent = intent?.sessionId === controls.session?.sessionId && intent?.scope === scope && intent?.phase !== "REJECTED" ? intent : undefined;
  const job = [...controls.session?.jobs ?? []].reverse().find(row => row.action === "backend-reset" && row.team === team
    && (currentIntent ? row.id === currentIntent.id : row.id === controls.session?.active || !!runId && row.runId === runId && row.cloudDomain === controls.session?.cloudDomain));
  const commandId = job?.results.map(row => recordObject(row.facts.command).commandId).find(value => typeof value === "string");
  const waiting = !!currentIntent && !job || !!job && (["ACCEPTED", "RUNNING"].includes(job.state)
    || job.state === "COMPLETED" && (!commandId || reset?.command?.commandId !== commandId));
  const uncertain = !!job && ["FAILED", "BLOCKED"].includes(job.state) && !commandId || summary.resetState === "UNCERTAIN";
  const pending = waiting || reset?.command?.state === "PENDING";
  const compatible = !!binding?.current && (team === "brake" ? binding.profile === "v3" : binding.profile === "v1");
  const reason = pending ? currentIntent?.phase === "UNKNOWN" && !job ? "Reset submission response lost · reconciling the original request. Do not repeat it."
    : currentIntent?.phase === "SUBMITTING" && !job ? "Resetting driver advisory… · submitting the current request" : "Resetting driver advisory… · waiting for Gateway CLEAR confirmation"
    : uncertain ? `Reset ${readable(reset?.command?.state).toLowerCase()} · outcome unconfirmed; partial application is possible. History retained.${!reset?.connected ? ` Reset requires ${team === "brake" ? "Brake V3" : "Tire V1"} and a connected reset channel.` : " Inspect Trace; do not repeat blindly."}`
    : retiring ? "Reset unavailable during Finish."
    : model.error ? "Reset unavailable until backend contact is restored."
    : summary.resetState === "CLEARED" ? `Driver advisory reset · Gateway confirmed CLEAR. This is not a telemetry-readiness report. Last reset confirmed for release ${readable(reset?.command?.serviceVersion)} · ${stamp(recordObject(recordObject(reset?.command?.result).gatewayStatus).gatewayObservedAt as string)}${!reset?.connected ? `. Reset requires ${team === "brake" ? "Brake V3" : "Tire V1"} and a connected reset channel.` : ""}`
    : summary.resetState === "HISTORICAL" ? `Reset for release ${readable(reset?.command?.serviceVersion)} confirmed · historical, not a reset of the current release.`
    : !compatible || !reset?.connected ? `Reset requires ${team === "brake" ? "Brake V3" : "Tire V1"} and a connected reset channel.`
    : controls.blocked ? controls.blockReason ?? "Another operation is in progress."
    : "Start a new demo drive. History retained; no vehicle repair is implied.";
  // A routine background observation is not a mutation lock. Keep the last
  // verified capability while reading; native execution still rechecks it.
  return { pending, waiting, uncertain, reason, disabled: controls.blocked || retiring || model.busy && !model.data || model.error || !compatible || !reset?.connected || pending || uncertain,
    request: () => controls.request({ action: "backend-reset", team }, scope) };
}

export function ResetScenario({ team, model, binding, retiring, runId, action = true }: { team: Team; model: BackendModel; binding?: BackendBinding; retiring?: boolean; runId?: string | null; action?: boolean }) {
  const reset = useResetScenario(team, model, binding, retiring, runId);
  return <div className="studio-reset-scenario">
    {action && <button aria-label={`Reset Driver Advisory — ${team === "brake" ? "Brake" : "Tire"}`} disabled={reset.disabled} onClick={reset.request}>Reset Driver Advisory</button>}
    <p role="status">{reset.reason}</p>
  </div>;
}
