// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import type { CloudService } from "../../domain/platformObservation";
import { object, productSourceTime, isProductResult, completedProduct, type ProductRow } from "./backendProduct";

export type BackendBinding = { unitSystemUid: string; serviceId: string; subjectId: string;
  instanceIndex: number; serviceVersion: string; profile?: string; current: boolean };
export type ResetCommand = { commandId: string; unitSystemUid: string; state: string;
  issuedAt: string; expiresAt: string; [key: string]: unknown };
const nativeId = (value: unknown): value is string => typeof value === "string" && /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$(?![\s\S])/.test(value);
export const time = (value: unknown) => typeof value === "string" && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{3})?Z$/.test(value)
  && Number.isFinite(Date.parse(value)) ? Date.parse(value) : NaN;

/** Cloud instance_id is the native allocation index, not AOS_INSTANCE_ID. */
export function backendBinding(unitSystemUid: string | undefined, row: CloudService | undefined,
  current: boolean, profile?: string): BackendBinding | undefined {
  const version = row?.service_versions?.installed_service_version?.version;
  const instances = row?.instances.value?.filter(item => item.version === version);
  if (!nativeId(unitSystemUid) || !nativeId(row?.service?.id) || !nativeId(row?.subject)
      || !version || instances?.length !== 1 || !Number.isSafeInteger(instances[0].instance_id)
      || instances[0].instance_id! < 0) return undefined;
  return { unitSystemUid, serviceId: row.service.id, subjectId: row.subject,
    instanceIndex: instances[0].instance_id!, serviceVersion: version, profile,
    current: current && row.instances.state === "CURRENT" };
}
export function matchesBinding(message: Record<string, unknown>, binding?: BackendBinding): boolean {
  const instance = object(message.serviceInstance);
  return !!binding && message.unitSystemUid === binding.unitSystemUid && message.serviceVersion === binding.serviceVersion
    && instance.serviceId === binding.serviceId && instance.subjectId === binding.subjectId
    && instance.instanceIndex === binding.instanceIndex && nativeId(instance.instanceId);
}
export function sameInstance(a: unknown, b: unknown): boolean {
  const x = object(a), y = object(b);
  return ["serviceId", "subjectId", "instanceIndex", "instanceId"].every(key => x[key] !== undefined && x[key] === y[key]);
}

/** Command issue/expiry is never a model-reset boundary. Negative outcomes
 * can follow partial application; only a correlated CLEAR establishes one. */
export function resetBoundary(command?: ResetCommand | null, binding?: BackendBinding) {
  if (!command) return { state: "NONE" as const, after: undefined };
  if (command.state === "PENDING") return { state: "PENDING" as const, after: undefined };
  const result = object(command.result), request = object(result.clearRequest), status = object(result.gatewayStatus);
  // Validate a retained CLEAR against its own release and full correlation.
  // SOTA does not invalidate that historical outcome or make it a current Reset.
  const commandBinding = binding && typeof command.serviceVersion === "string"
    && /^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$/.test(command.serviceVersion)
    ? { ...binding, serviceVersion: command.serviceVersion } : undefined;
  const valid = command.state === "CLEARED" && matchesBinding(command, commandBinding)
    && result.result === "CLEARED" && result.commandId === command.commandId
    && result.unitSystemUid === command.unitSystemUid && result.serviceVersion === command.serviceVersion
    && result.producerEpoch === command.producerEpoch && sameInstance(result.serviceInstance, command.serviceInstance)
    && request.schemaVersion === 1 && status.schemaVersion === 1 && request.operation === "CLEAR"
    && request.reasonCode === "CONDITION_CLEARED" && request.decisionId === command.commandId
    && request.serviceVersion === command.serviceVersion && request.producerEpoch === command.producerEpoch
    && nativeId(request.requestId) && request.requestId === status.requestId
    && Number.isSafeInteger(request.sequence) && Number(request.sequence) > 0
    && request.sequence === status.sequence && request.producerEpoch === status.producerEpoch
    && status.state === "CLEARED" && status.reason === "NONE" && status.activeRecommendation === "NONE"
    && status.activeReasonCode === "NONE" && status.activeUntil === null
    && time(request.issuedAt) >= time(command.issuedAt) && time(request.issuedAt) < time(command.expiresAt)
    && time(request.expiresAt) > time(request.issuedAt) && time(request.expiresAt) - time(request.issuedAt) <= 30000
    && time(status.gatewayObservedAt) >= time(request.issuedAt) && time(status.gatewayObservedAt) <= time(request.expiresAt);
  if (valid && command.serviceVersion !== binding?.serviceVersion)
    return { state: "HISTORICAL" as const, after: undefined };
  return valid ? { state: "CLEARED" as const, after: time(status.gatewayObservedAt) }
    : { state: "UNCERTAIN" as const, after: undefined };
}

/** One selector for the card, dialog and chapter proof. Receipt history stays
 * untouched. Legacy/unbound rows remain inspectable, never current proof. */
export function selectProduct(rows: ProductRow[], team: "brake" | "tire", version?: string,
  binding?: BackendBinding, command?: ResetCommand | null, now = Date.now()) {
  const reset = resetBoundary(command, binding);
  const releaseRows = rows.filter(row => !!version && row.message.serviceVersion === version && isProductResult(row, team));
  const scoped = releaseRows.filter(row => matchesBinding(row.message, binding));
  const identities = new Set(scoped.map(row => object(row.message.serviceInstance).instanceId));
  // Cloud exposes service/Subject/index/release, not the opaque local instance.
  // Multiple process identities in one release stay ambiguous, not latest-receipt wins.
  const ambiguous = identities.size > 1;
  const eligible = ambiguous || reset.state === "PENDING" || reset.state === "UNCERTAIN" ? [] : scoped.filter(row => {
    const source = time(productSourceTime(row));
    return Number.isFinite(source) && source <= now && (reset.after === undefined || source > reset.after);
  }).sort((a, b) => time(productSourceTime(b)) - time(productSourceTime(a)));
  const result = eligible[0];
  return { rows: eligible, result, reset, ambiguous,
    proof: binding?.current && result && version && completedProduct(result, version) ? version : undefined };
}
