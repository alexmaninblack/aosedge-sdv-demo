// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import type { PlatformCloudObservation } from "./platformObservation";
import { componentIssue, componentPending, failedState, serviceIssue, servicePending } from "./softwareObservation";

const waiting = (state?: string | null) => Boolean(state && !/^(installed|success|none|complete|completed)$/i.test(state));
const countText = (count: number | undefined, noun: string) => count === undefined ? `${noun}s not reported` : `${count} ${noun}${count === 1 ? "" : "s"}`;

/** Cloud facts only. A resource read or a product assessment cannot freshen this summary. */
export function cloudSoftwareSummary(observation?: PlatformCloudObservation | null) {
  const value = observation?.value, inventory = value?.inventory;
  const components = inventory?.components, services = inventory?.services;
  const componentRows = components?.value, serviceRows = services?.value;
  const current = observation?.state === "CURRENT";
  const componentCount = componentRows ? componentRows.filter(row => row.installed_component?.version).length : undefined;
  const installedServices = serviceRows?.filter(row => row.service_versions?.installed_service_version?.version);
  const serviceCount = installedServices?.some(row => !row.service?.id) ? undefined
    : installedServices ? new Set(installedServices.map(row => row.service!.id)).size : undefined;
  const complete = current && components?.state === "CURRENT" && services?.state === "CURRENT"
    && componentRows != null && serviceRows != null && serviceRows.every(row => row.service_versions != null);
  const issue = Boolean(componentRows?.some(row => componentIssue(row)) || serviceRows?.some(row => serviceIssue(row)) || failedState(value?.updateStatus));
  const vdpPending = Boolean(value?.pendingVersion || waiting(value?.updateStatus));
  const pendingComponents = componentRows?.filter(componentPending) ?? [];
  const extraVdp = vdpPending && !pendingComponents.some(row => row.type?.endsWith("vehicle-data-provider"));
  const pending = pendingComponents.length + (extraVdp ? 1 : 0) + (serviceRows?.filter(servicePending).length ?? 0);
  const inventoryLastKnown = Boolean(inventory && (!current || components?.state !== "CURRENT" || services?.state !== "CURRENT"));
  const timestamps = [observation?.observedAt,
    components?.state === "CURRENT" ? components.readCompletedAt ?? inventory?.readCompletedAt : components?.lastKnownReadCompletedAt,
    services?.state === "CURRENT" ? services.readCompletedAt ?? inventory?.readCompletedAt : services?.lastKnownReadCompletedAt,
  ].filter((time): time is string => Boolean(time && Number.isFinite(Date.parse(time))));
  return {
    inventoryText: inventory ? `${countText(componentCount, "component")} · ${countText(serviceCount, "service")}` : "Not reported",
    inventoryLastKnown,
    updatesText: issue ? `${complete ? "" : "Last reported · "}Software issue${pending ? ` · ${pending} pending` : ""}`
      : !complete ? "Not confirmed" : pending ? `${pending} pending / in progress` : "No pending updates",
    issue,
    observedAt: timestamps.length ? timestamps.sort((a, b) => Date.parse(a) - Date.parse(b))[0] : undefined,
  };
}
