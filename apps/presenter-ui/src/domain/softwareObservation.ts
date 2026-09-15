import type { CloudComponent, CloudService } from "./platformObservation";

export const failedState = (state?: string | null) => /fail|error/i.test(state ?? "");
export const componentIssue = (row?: CloudComponent) => row?.pending_component_error
  || (failedState(row?.pending_component_status) ? row!.pending_component_status : null);
export const serviceIssue = (row?: CloudService) => row?.error_message
  || (row?.error_aos_code ? `Aos error ${row.error_aos_code}` : null)
  || (row?.error_exit_code ? `Exit code ${row.error_exit_code}` : null)
  || (failedState(row?.service_versions?.pending_service_version_status) ? row!.service_versions!.pending_service_version_status : null);
export const servicePending = (row?: CloudService) => Boolean(row?.service_versions?.pending_service_version
  || row?.service_versions?.pending_service_version_id
  || row?.service_versions?.pending_service_version_status && !/^(installed|success|none)$/i.test(row.service_versions.pending_service_version_status));
export const serviceRunning = (row: CloudService | undefined, version: string | undefined, current: boolean) => Boolean(
  current && version && row?.instances.state === "CURRENT" && !serviceIssue(row)
  && row.service_versions?.installed_service_version?.version === version
  && row.instances.value?.some(instance => instance.version === version && instance.run_state === "active" && !instance.error_message));
