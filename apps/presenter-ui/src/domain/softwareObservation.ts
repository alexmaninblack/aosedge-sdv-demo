import type { CloudComponent, CloudService } from "./platformObservation";

export const failedState = (state?: string | null) => /fail|error/i.test(state ?? "");
export const componentIssue = (row?: CloudComponent) => row?.pending_component_error
  || (failedState(row?.pending_component_status) ? row!.pending_component_status : null);
export const componentPending = (row?: Pick<CloudComponent, "pending_component" | "pending_component_status">) => Boolean(row?.pending_component
  || row?.pending_component_status && !/^(installed|success|none|complete|completed)$/i.test(row.pending_component_status));
export function componentUpdateLabel(row: CloudComponent, current: boolean) {
  const text = componentIssue(row) ? `Update issue · ${componentIssue(row)}`
    : row.pending_component?.version ? `Pending ${row.pending_component.version}`
    : componentPending(row) ? "Update in progress · version not reported" : current ? "No pending release" : "Pending not current";
  return text + (!current && componentPending(row) ? " · last known" : "");
}
export const instanceIssue = (row: { error_message?: string | null; error_aos_code?: number | null; error_exit_code?: number | null }) =>
  [row.error_message, row.error_aos_code ? `Aos error ${row.error_aos_code}` : null,
    row.error_exit_code ? `Exit code ${row.error_exit_code}` : null].filter(Boolean).join(" · ") || null;
export const serviceIssue = (row?: CloudService) => (row ? instanceIssue(row) : null)
  || (failedState(row?.service_versions?.pending_service_version_status) ? row!.service_versions!.pending_service_version_status : null)
  || row?.instances.value?.map(instanceIssue).find(Boolean);
export const servicePending = (row?: CloudService) => Boolean(row?.service_versions?.pending_service_version
  || row?.service_versions?.pending_service_version_id
  || row?.service_versions?.pending_service_version_status && !/^(installed|success|none)$/i.test(row.service_versions.pending_service_version_status));
export const serviceRunning = (row: CloudService | undefined, version: string | undefined, current: boolean) => Boolean(
  current && version && row?.instances.state === "CURRENT" && !serviceIssue(row)
  && row.service_versions?.installed_service_version?.version === version
  && row.instances.value?.some(instance => instance.version === version && instance.run_state === "active" && !instanceIssue(instance)));
