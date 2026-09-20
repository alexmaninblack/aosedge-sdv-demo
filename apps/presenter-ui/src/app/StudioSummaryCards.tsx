// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import type { PlatformCloudObservation } from "../domain/platformObservation";
import { cloudSoftwareSummary } from "../domain/cloudSummary";
import { backendSummary, type BackendModel, type Team } from "../features/service-team/useBackendObservation";
import { ObservationTime } from "./StudioReadViews";
import type { BackendBinding } from "../features/service-team/backendSelection";
import { readable } from "../features/service-team/useBackendObservation";

export function BackendSummary({ team, model, version, binding, noController = false }: { team: Team; model: BackendModel; version?: string; binding?: BackendBinding; noController?: boolean }) {
  const summary = backendSummary(model, team, version, binding);
  const fn = summary.functional;
  const facts = fn.item?.message.content;
  const sourceKnown = fn.state === "CURRENT";
  const title = summary.title === summary.title.toUpperCase() ? summary.title[0] + summary.title.slice(1).toLowerCase() : summary.title;
  const warning = summary.integrityConflict || /INSPECTION|REPLACEMENT/i.test(summary.title);
  if (noController) return <><span className="studio-summary-state">No controller created</span><span className="studio-summary-result">Ready for setup</span><small className="studio-summary-note">Create and provision Test, then install the service to observe its input and results.</small></>;
  return <>
    <span className={`studio-summary-state${summary.lastKnown ? " is-stale" : ""}`}>{summary.status}</span>
    <span className={`studio-summary-result${warning ? " is-warning" : ""}`}>{title}{summary.result && summary.lastKnown ? " · last known" : ""}</span>
    <span className="studio-summary-pair"><span>Input</span><strong>{sourceKnown ? readable(facts?.input.state) : fn.state === "LAST_KNOWN" ? "Last known" : "Not reported"}</strong></span>
    <span className="studio-summary-pair"><span>Activity</span><strong>{sourceKnown ? readable(facts?.activity.state) : "Not confirmed"}</strong></span>
    <small className="studio-summary-note">{summary.integrityConflict ? summary.guidance : summary.result ? summary.result.message.messageType === "WINDOW_COMPLETION" ? "Retained source recording · delivery and recording are separate" : "Vehicle signals · demo model estimate" : summary.guidance}</small>
    {summary.continuityNote && <small className="studio-summary-note">{summary.continuityNote}</small>}
    {summary.result && <small className="studio-summary-time">Latest result received · <ObservationTime compact value={summary.receivedAt} /></small>}
    <small className="studio-summary-time">{model.busy && !model.data ? "Reading backend… " : "Backend checked · "}<ObservationTime compact value={summary.observedAt} /></small>
    {!!model.data?.partialResources?.length && <small className="studio-summary-note">Partial read · details in backend</small>}
  </>;
}

export function CloudSummary({ observation, cloudLabel }: { observation?: PlatformCloudObservation | null; cloudLabel: string }) {
  const summary = cloudSoftwareSummary(observation);
  if (cloudLabel === "No controller created") return <><span className="studio-summary-state">Cloud management</span><span className="studio-summary-result">No Cloud Unit yet</span><small className="studio-summary-note">Create and provision Test to observe software and resources.</small></>;
  return <>
    <span className="studio-summary-state">Cloud management</span>
    <span className={`studio-summary-result${cloudLabel === "ONLINE" ? " is-online" : ""}`}>{cloudLabel === cloudLabel.toUpperCase() ? cloudLabel[0] + cloudLabel.slice(1).toLowerCase() : cloudLabel}</span>
    <span className="studio-summary-software"><span>Installed{summary.inventoryLastKnown ? " · last known" : ""}</span><strong>{summary.inventoryText}</strong></span>
    <span className={`studio-summary-software${summary.issue ? " is-warning" : ""}`}><span>Updates</span><strong>{summary.updatesText}</strong></span>
    <small className="studio-summary-time">Cloud checked · <ObservationTime compact value={summary.observedAt} /></small>
  </>;
}
