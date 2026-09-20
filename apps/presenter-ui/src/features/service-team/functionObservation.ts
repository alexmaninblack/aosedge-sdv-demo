// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { object, type Resource } from "./backendProduct";
import { matchesBinding, sameInstance, time, type BackendBinding } from "./backendSelection";

type Axis = { state: string; reason: string };
export type FunctionItem = { backendReceivedAt: string; authority: string; stale: boolean; clockSkew: boolean; deliveryState: string;
  message: Record<string, unknown> & { observedAt: string; generation: number; sequence: number; serviceProfile: string;
    content: { connection: string; input: Axis; activity: Axis & { episodeId: string | null };
      delivery: { state: string; queuedMessages: number; lastReceiptAt: string | null };
      advisory: { state: string; requestId: string | null }; lastResult: null | { kind: string; id: string; sourceTime: string; serviceVersion: string } } } };
const closed = (value: unknown, keys: string[]) => Object.keys(object(value)).sort().join() === [...keys].sort().join();
const oneOf = (value: unknown, choices: string) => typeof value === "string" && choices.split("|").includes(value);
const safe = (value: unknown) => typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
const id = (value: unknown) => typeof value === "string" && /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$(?![\s\S])/.test(value);
const version = (value: unknown) => typeof value === "string" && value.length <= 32 && /^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$(?![\s\S])/.test(value);
const instant = (value: unknown) => Number.isFinite(time(value)) && typeof value === "string" && new Date(value).toISOString() === value;
const fail = (): never => { throw new Error("BACKEND_FUNCTION_OBSERVATION_INVALID"); };

/** Read-only projection of a digest-validated owned backend resource. This is
 * not an ingestion decoder and does not substitute for its canonical hash gate. */
export function functionPage(resource: Resource | undefined, team: "brake" | "tire", uid: string): FunctionItem[] {
  if (!resource?.data) return [];
  const data = resource.data;
  if (!closed(data, ["schemaVersion", "contractVersion", "resourceType", "unitSystemUid", "items", "truncated"])
      || data.schemaVersion !== 3 || data.contractVersion !== "3.0.0" || data.resourceType !== "FUNCTION_OBSERVATION"
      || data.unitSystemUid !== uid || typeof data.truncated !== "boolean" || !Array.isArray(data.items) || data.items.length > 10) return fail();
  for (const raw of data.items) {
    const item = object(raw), m = object(item.message), c = object(m.content), binding = object(m.serviceInstance);
    const input = object(c.input), activity = object(c.activity), delivery = object(c.delivery), advisory = object(c.advisory), result = object(c.lastResult);
    if (!closed(item, ["message", "backendReceivedAt", "authority", "stale", "clockSkew", "deliveryState"])
        || !instant(item.backendReceivedAt) || typeof item.stale !== "boolean" || typeof item.clockSkew !== "boolean"
        || item.authority !== "FUNCTION_TEAM_REPORTED_OBSERVATION" || !oneOf(item.deliveryState, "DURABLY_RECEIVED|CONFLICT")
        || !closed(m, ["schemaVersion", "contractVersion", "messageType", "unitSystemUid", "unitRole", "serviceInstance", "serviceVersion", "serviceProfile", "generation", "sequence", "observedAt", "content", "contentSha256"])
        || m.schemaVersion !== 3 || m.contractVersion !== "3.0.0" || m.messageType !== team.toUpperCase() + "_FUNCTION_OBSERVATION"
        || m.unitSystemUid !== uid || m.unitRole !== "VALIDATION" || !version(m.serviceVersion)
        || !oneOf(m.serviceProfile, team === "brake" ? "v1|v2|v3" : "v1")
        || !closed(binding, ["serviceId", "subjectId", "instanceIndex", "instanceId"])
        || !id(binding.serviceId) || !id(binding.subjectId) || !id(binding.instanceId) || !safe(binding.instanceIndex)
        || !safe(m.generation) || !m.generation || !safe(m.sequence) || !m.sequence || !instant(m.observedAt)
        || typeof m.contentSha256 !== "string" || !/^[a-f0-9]{64}$(?![\s\S])/.test(m.contentSha256)
        || JSON.stringify(m).length > 8192 || !closed(c, ["connection", "input", "activity", "delivery", "advisory", "lastResult"])
        || !oneOf(c.connection, "STARTING|CONNECTED|REAUTHENTICATING|DISCONNECTED|ACCESS_DENIED")
        || !closed(input, ["state", "reason"]) || !oneOf(input.state, "WAITING|RECEIVING|STALE|DISCONNECTED|ACCESS_DENIED|INVALID")
        || !oneOf(input.reason, "NONE|AWAITING_INPUT|SOURCE_GAP|INVALID_SAMPLE|TRANSPORT_LOST|ACCESS_DENIED|REAUTHENTICATING")
        || (input.state === "RECEIVING") !== (input.reason === "NONE")
        || !closed(activity, ["state", "reason", "episodeId"]) || !oneOf(activity.state, "WAITING|PRE|ACTIVE|POST|COMPLETED|SKIPPED")
        || !oneOf(activity.reason, "NONE|NOT_QUALIFIED|INSUFFICIENT_SAMPLES|INVALID_INPUT|SOURCE_DISCONTINUITY|REAUTHENTICATING|RESET|STORAGE_UNAVAILABLE")
        || activity.state === "SKIPPED" && activity.reason === "NONE" || activity.episodeId !== null && !id(activity.episodeId)
        || !closed(delivery, ["state", "queuedMessages", "lastReceiptAt"]) || !oneOf(delivery.state, "IDLE|PENDING|RETRYING|BLOCKED")
        || !safe(delivery.queuedMessages) || delivery.lastReceiptAt !== null && !instant(delivery.lastReceiptAt)
        || !closed(advisory, ["state", "requestId"]) || !oneOf(advisory.state, "NOT_SUPPORTED|WAITING|CONFIRMED|UNAVAILABLE|REAUTHENTICATING")
        || advisory.requestId !== null && !id(advisory.requestId) || advisory.state === "CONFIRMED" && advisory.requestId === null
        || team === "brake" && m.serviceProfile !== "v3" && (advisory.state !== "NOT_SUPPORTED" || advisory.requestId !== null)
        || (team === "tire" || m.serviceProfile === "v3") && advisory.state === "NOT_SUPPORTED"
        || c.lastResult !== null && (!closed(result, ["kind", "id", "sourceTime", "serviceVersion"])
          || !oneOf(result.kind, "WINDOW|ASSESSMENT") || !id(result.id) || !instant(result.sourceTime) || !version(result.serviceVersion))) return fail();
  }
  return data.items as FunctionItem[];
}

export function selectFunction(resource: Resource | undefined, team: "brake" | "tire", binding?: BackendBinding, now = Date.now()) {
  if (!binding) return { state: "UNREPORTED" as const };
  let items: FunctionItem[];
  try { items = functionPage(resource, team, binding.unitSystemUid); } catch { return { state: "INVALID" as const }; }
  const candidates = items.filter(item => matchesBinding(item.message, binding)
    && !!binding.profile && item.message.serviceProfile === binding.profile);
  if (candidates.some(item => !sameInstance(item.message.serviceInstance, candidates[0].message.serviceInstance)))
    return { state: "AMBIGUOUS" as const };
  const item = candidates.sort((a, b) => b.message.generation - a.message.generation || b.message.sequence - a.message.sequence)[0];
  if (!item) return { state: "UNREPORTED" as const };
  if (item.deliveryState === "CONFLICT") return { state: "CONFLICT" as const, item };
  const sourceAge = now - time(item.message.observedAt);
  return { state: binding.current && resource?.state === "OBSERVED" && resource.data?.truncated === false
      && !item.stale && !item.clockSkew && sourceAge >= 0 && sourceAge <= 90000 ? "CURRENT" as const : "LAST_KNOWN" as const, item };
}
