import type { BrakeResourceView, Clock, ReadObservation } from "../../domain";
import { readObservation } from "../../domain";
import type { ReadOnlyFixturePackage } from "./contracts";
import { isAcceptedDateTime, normalizeContractRecord } from "./aosCloudReadModel";

export interface BrakeReadProjection {
  brake: ReadObservation<readonly BrakeResourceView[]>;
  notificationRereads: number;
}

const resourceTypes = new Set(["WINDOW", "ASSESSMENT", "EVENT", "ADVISORY"]);
const states = new Set(["COMPLETE", "PARTIAL", "ASSESSED", "PENDING_ASSESSMENT_CORRELATION", "CORRELATED_ASSESSMENT", "PUBLISHED"]);
const deliveryStates = new Set(["RECEIVING", "DELAYED", "CONFLICT", "DURABLY_RECEIVED"]);
const projectionStates = new Set(["GROWING", "PARTIAL", "TERMINAL", "QUARANTINED"]);
const terminalStates = new Set(["COMPLETE", "TRUNCATED_MAX_DURATION", "INCOMPLETE_SOURCE_GAP", "ABORTED_SERVICE_STOP", "ABORTED_RESTART"]);

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function brakeResourceShapeIsValid(value: unknown): value is BrakeResourceView {
  if (!isPlainObject(value)) return false;
  const required = new Set([
    "role", "unitSystemUidFingerprint", "resourceType", "state", "deliveryState", "projectionState", "terminalState",
    "count", "limit", "nextCursor", "complete", "sourceTime", "backendReceivedAt", "vdpVersion", "vdpDigest",
  ]);
  if (Object.keys(value).length !== required.size || Object.keys(value).some((key) => !required.has(key))) return false;
  const common = (value.role === "TEST" || value.role === "PRODUCTION")
    && typeof value.unitSystemUidFingerprint === "string" && /^uid:(?:test|production):[0-9a-f]{4}$/.test(value.unitSystemUidFingerprint)
    && resourceTypes.has(String(value.resourceType))
    && states.has(String(value.state))
    && deliveryStates.has(String(value.deliveryState))
    && (value.projectionState === null || projectionStates.has(String(value.projectionState)))
    && (value.terminalState === null || terminalStates.has(String(value.terminalState)))
    && Number.isInteger(value.count) && Number(value.count) >= 0 && Number(value.count) <= 100
    && Number.isInteger(value.limit) && Number(value.limit) >= 1 && Number(value.limit) <= 100
    && (value.nextCursor === null || (typeof value.nextCursor === "string" && /^[A-Za-z0-9_-]{1,2048}$/.test(value.nextCursor)))
    && typeof value.complete === "boolean" && value.complete === (value.nextCursor === null)
    && (value.sourceTime === null || isAcceptedDateTime(value.sourceTime))
    && (value.backendReceivedAt === null || isAcceptedDateTime(value.backendReceivedAt))
    && (value.vdpVersion === null || (typeof value.vdpVersion === "string" && /^[0-9]+\.[0-9]+\.[0-9]+$/.test(value.vdpVersion)))
    && (value.vdpDigest === null || (typeof value.vdpDigest === "string" && /^sha256:[0-9a-f]{4}…[0-9a-f]{4}$/.test(value.vdpDigest)));
  if (!common) return false;
  if (value.resourceType === "WINDOW") {
    return (value.state === "COMPLETE" || value.state === "PARTIAL")
      && value.projectionState !== null
      && (value.state !== "COMPLETE" || (value.projectionState === "TERMINAL" && value.terminalState === "COMPLETE"));
  }
  if (value.projectionState !== null || value.terminalState !== null) return false;
  if (value.resourceType === "ASSESSMENT") return value.state === "ASSESSED" && value.vdpVersion !== null && value.vdpDigest !== null;
  if (value.resourceType === "EVENT") return value.state === "PENDING_ASSESSMENT_CORRELATION"
    ? value.vdpVersion === null && value.vdpDigest === null
    : value.state === "CORRELATED_ASSESSMENT" && value.vdpVersion !== null && value.vdpDigest !== null;
  return value.resourceType === "ADVISORY" && value.state === "PUBLISHED" && value.vdpVersion !== null && value.vdpDigest !== null;
}

function brakeResourcesShapeIsValid(value: unknown): value is readonly BrakeResourceView[] {
  return Array.isArray(value)
    && value.every(brakeResourceShapeIsValid)
    && value.length === 4
    && new Set(value.map((item) => item.resourceType)).size === value.length;
}

function invalid(observation: ReadObservation<readonly BrakeResourceView[]>, reason: string): ReadObservation<readonly BrakeResourceView[]> {
  return readObservation<readonly BrakeResourceView[]>({ ...observation, value: null, state: "INCOMPLETE", transport: "MALFORMED", reason });
}

export function brakeCloudReadModel(fixture: ReadOnlyFixturePackage, clock: Clock): BrakeReadProjection {
  let brake = normalizeContractRecord(fixture.brake.resources, clock, fixture.policyId, undefined, "BRAKE_BACKEND", brakeResourcesShapeIsValid);
  const role = fixture.brake.contextRole;
  const contextSystemUidFingerprint = fixture.brake.contextSystemUidFingerprint;

  if (fixture.phase === "PRE_M1") {
    brake = readObservation<readonly BrakeResourceView[]>({
      ...brake,
      value: null,
      state: "NOT_APPLICABLE",
      transport: "AVAILABLE",
      reason: "NO_CURRENT_UNIT_BEFORE_M1",
    });
  } else if (!role || !contextSystemUidFingerprint) {
    brake = readObservation<readonly BrakeResourceView[]>({
      ...brake,
      value: null,
      state: "UNKNOWN",
      transport: "SOURCE_UNAVAILABLE",
      reason: "CURRENT_UNIT_CONTEXT_UNAVAILABLE",
    });
  } else if ((brake.state === "CURRENT" || brake.state === "STALE") && brake.value) {
    const binding = fixture.aosCloud.bindings.value?.find((item) => item.role === role);
    const valid = binding?.systemUidFingerprint === contextSystemUidFingerprint && brake.value.every((item) =>
      item.role === role
      && item.unitSystemUidFingerprint === contextSystemUidFingerprint
      && resourceTypes.has(item.resourceType)
      && item.complete
      && (item.state !== "PENDING_ASSESSMENT_CORRELATION" || (item.vdpVersion === null && item.vdpDigest === null)),
    );
    if (!valid) brake = invalid(brake, "BRAKE_RESOURCE_SCOPE_MISMATCH");
  }

  if (fixture.brake.notificationCount > 0 && fixture.brake.restReadCount <= fixture.brake.notificationCount) {
    brake = invalid(brake, "NOTIFICATION_REST_REREAD_REQUIRED");
  }

  return {
    brake,
    notificationRereads: fixture.brake.notificationCount > 0 ? fixture.brake.restReadCount : 0,
  };
}
