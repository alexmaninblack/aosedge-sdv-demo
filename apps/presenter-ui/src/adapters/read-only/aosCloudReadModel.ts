import type {
  Clock,
  NativeLogView,
  ReadObservation,
  ReleaseObjectView,
  SessionView,
  UnitSetView,
  UnitView,
  VehicleBindingView,
} from "../../domain";
import { readObservation } from "../../domain";
import type { AosCloudFixtureRecords, ContractRecord, ReadOnlyFixturePackage } from "./contracts";

export interface AosCloudReadProjection {
  session: ReadObservation<SessionView>;
  brakeSession: ReadObservation<SessionView>;
  bindings: ReadObservation<readonly VehicleBindingView[]>;
  units: ReadObservation<readonly UnitView[]>;
  unitSets: ReadObservation<readonly UnitSetView[]>;
  releases: ReadObservation<readonly ReleaseObjectView[]>;
  unitLogs: ReadObservation<readonly NativeLogView[]>;
  serviceLogs: ReadObservation<readonly NativeLogView[]>;
}

const outcomeMap = {
  "400": "REJECTED",
  "401": "UNAUTHENTICATED",
  "403": "FORBIDDEN",
  "404": "NOT_FOUND_OR_INACCESSIBLE",
  "422": "SCHEMA_INVALID",
  SOURCE_UNAVAILABLE: "SOURCE_UNAVAILABLE",
  MALFORMED: "MALFORMED",
} as const;

const fingerprintPattern = /^[a-z][a-z0-9-]*(?::[a-z0-9-]+){1,4}:[0-9a-f]{4}$/;
const permissionPattern = /^[a-z][a-z0-9_]*$/;
const metadataPattern = /^[A-Za-z][A-Za-z0-9 _-]{0,31}=[A-Za-z0-9 .:_-]{1,96}$/;
const readOnlyPermissions = new Set([
  "users_me",
  "units_list",
  "units_read",
  "unit_sets_list",
  "unit_sets_read",
  "verification_batch_list",
  "verification_batch_read",
  "fleet_validation_batch_read",
  "campaigns_read",
  "unit_logs_list",
  "unit_logs_read",
  "service_logs_list",
  "service_logs_read",
]);

const oemPermissions = [
  "users_me",
  "units_list",
  "units_read",
  "unit_sets_list",
  "unit_sets_read",
  "verification_batch_list",
  "verification_batch_read",
  "fleet_validation_batch_read",
  "campaigns_read",
  "unit_logs_list",
  "unit_logs_read",
] as const;

const brakePermissions = ["users_me", "service_logs_list", "service_logs_read"] as const;

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function hasExactKeys(value: Record<string, unknown>, required: readonly string[], optional: readonly string[] = []): boolean {
  const keys = Object.keys(value);
  const allowed = new Set([...required, ...optional]);
  return required.every((key) => Object.hasOwn(value, key)) && keys.every((key) => allowed.has(key));
}

export function isAcceptedDateTime(value: unknown): value is string {
  if (typeof value !== "string") return false;
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.exec(value);
  if (!match) return false;
  const [, year, month, day, hour, minute, second] = match.map((item) => Number(item));
  if (month! < 1 || month! > 12 || day! < 1 || day! > new Date(Date.UTC(year!, month!, 0)).getUTCDate()) return false;
  return hour! <= 23 && minute! <= 59 && second! <= 59 && Number.isFinite(Date.parse(value));
}

function isFingerprint(value: unknown): value is string {
  return typeof value === "string" && fingerprintPattern.test(value) && value.length <= 128;
}

function isUniqueStringArray(value: unknown, predicate: (item: string) => boolean = () => true): value is readonly string[] {
  return Array.isArray(value)
    && value.every((item) => typeof item === "string" && predicate(item))
    && new Set(value).size === value.length;
}

function sessionShapeIsValid(value: unknown): value is SessionView {
  if (!isPlainObject(value) || !hasExactKeys(value, ["routeContext", "role", "ownerFingerprint", "effectivePermissions"])) return false;
  return (value.routeContext === "oem-delivery-read" || value.routeContext === "brake-sp1-read")
    && typeof value.role === "string"
    && isFingerprint(value.ownerFingerprint)
    && isUniqueStringArray(value.effectivePermissions, (permission) => permissionPattern.test(permission) && readOnlyPermissions.has(permission));
}

function bindingShapeIsValid(value: unknown): value is VehicleBindingView {
  if (!isPlainObject(value) || !hasExactKeys(value, ["role", "label", "wireRole", "systemUidFingerprint", "unitFingerprint", "mainNodeFingerprint", "unitSetFingerprint"])) return false;
  return (value.role === "TEST" || value.role === "PRODUCTION")
    && value.label === (value.role === "TEST" ? "Test Vehicle" : "Production Vehicle")
    && value.wireRole === (value.role === "TEST" ? "VALIDATION" : "PRODUCTION")
    && [value.systemUidFingerprint, value.unitFingerprint, value.mainNodeFingerprint, value.unitSetFingerprint].every(isFingerprint);
}

function unitShapeIsValid(value: unknown): value is UnitView {
  if (!isPlainObject(value) || !hasExactKeys(value, ["role", "systemUidFingerprint", "unitFingerprint", "mainNodeFingerprint", "connectionState", "reportedState", "desiredSoftware", "actualSoftware", "pendingComponentBatchFingerprints", "pendingServiceBatchFingerprints"])) return false;
  return (value.role === "TEST" || value.role === "PRODUCTION")
    && isFingerprint(value.systemUidFingerprint)
    && isFingerprint(value.unitFingerprint)
    && isFingerprint(value.mainNodeFingerprint)
    && (value.connectionState === "Online" || value.connectionState === "Offline")
    && (value.reportedState === "ready" || value.reportedState === "error" || value.reportedState === "unknown")
    && isUniqueStringArray(value.desiredSoftware, (item) => /^(?:VDP|Brake) v[1-9][0-9]*$/.test(item))
    && isUniqueStringArray(value.actualSoftware, (item) => /^(?:VDP|Brake) v[1-9][0-9]*$/.test(item))
    && isUniqueStringArray(value.pendingComponentBatchFingerprints, (item) => isFingerprint(item))
    && isUniqueStringArray(value.pendingServiceBatchFingerprints, (item) => isFingerprint(item));
}

function unitSetShapeIsValid(value: unknown): value is UnitSetView {
  if (!isPlainObject(value) || !hasExactKeys(value, ["role", "title", "isValidationSet", "memberUnitFingerprints", "complete"])) return false;
  return (value.role === "TEST" || value.role === "PRODUCTION")
    && value.title === (value.role === "TEST" ? "AosEdge SDV Demo / Test Vehicles" : "AosEdge SDV Demo / Production Vehicles")
    && value.isValidationSet === (value.role === "TEST")
    && value.complete === true
    && isUniqueStringArray(value.memberUnitFingerprints, (item) => isFingerprint(item));
}

function unitSetPagesShapeIsValid(value: unknown): value is AosCloudFixtureRecords["unitSetPages"] {
  return Array.isArray(value) && value.every((item) => isPlainObject(item)
    && hasExactKeys(item, ["role", "page", "hasNext", "cursor", "nextCursor", "members"])
    && (item.role === "TEST" || item.role === "PRODUCTION")
    && Number.isInteger(item.page) && Number(item.page) > 0
    && typeof item.hasNext === "boolean"
    && (item.cursor === null || (typeof item.cursor === "string" && /^[A-Za-z0-9_-]{1,2048}$/.test(item.cursor)))
    && (item.nextCursor === null || (typeof item.nextCursor === "string" && /^[A-Za-z0-9_-]{1,2048}$/.test(item.nextCursor)))
    && isUniqueStringArray(item.members, (member) => isFingerprint(member)));
}

function releaseShapeIsValid(value: unknown): value is ReleaseObjectView {
  if (!isPlainObject(value) || !hasExactKeys(value, ["kind", "fingerprint", "state", "targetFingerprints"], ["result", "unresolvedShape"])) return false;
  return ["CANDIDATE", "VERIFICATION_BATCH", "FLEET_VALIDATION_BATCH", "CAMPAIGN"].includes(String(value.kind))
    && isFingerprint(value.fingerprint)
    && ["published", "waiting", "valid", "done", "preview"].includes(String(value.state))
    && isUniqueStringArray(value.targetFingerprints, (item) => isFingerprint(item))
    && (value.result === undefined || (typeof value.result === "string" && /^[0-9]+\/[0-9]+ done$/.test(value.result)))
    && (value.unresolvedShape === undefined || value.unresolvedShape === "unit_ids" || value.unresolvedShape === "units_ids");
}

function nativeLogShapeIsValid(value: unknown): value is NativeLogView {
  if (!isPlainObject(value) || !hasExactKeys(value, ["family", "owner", "scopeFingerprint", "requestFingerprint", "cloudState", "metadata", "retentionNotice"])) return false;
  return (value.family === "unit-logs" || value.family === "service-logs")
    && (value.owner === "OEM" || value.owner === "BRAKE_SP1")
    && isFingerprint(value.scopeFingerprint)
    && isFingerprint(value.requestFingerprint)
    && ["created", "sent", "waiting unit", "receiving", "done", "error", "empty log has been provided"].includes(String(value.cloudState))
    && isUniqueStringArray(value.metadata, (item) => metadataPattern.test(item))
    && value.retentionNotice === "Retention policy not exposed by current API";
}

function arrayOf<T>(value: unknown, validator: (item: unknown) => item is T): value is readonly T[] {
  return Array.isArray(value) && value.every(validator);
}

function recordEnvelopeIsValid<T>(record: ContractRecord<T>, expectedSource: ContractRecord<T>["source"]): boolean {
  const value = record as unknown;
  if (!isPlainObject(value) || !hasExactKeys(value, ["contractClass", "source", "outcome", "freshness", "sourceTimestamp", "value"], ["reasonCode"])) return false;
  return value.contractClass === "CONTRACT_SYNTHETIC"
    && value.source === expectedSource
    && ["OK", "400", "401", "403", "404", "422", "SOURCE_UNAVAILABLE", "MALFORMED", "REDACTED"].includes(String(value.outcome))
    && (value.freshness === "CURRENT" || value.freshness === "STALE")
    && (value.sourceTimestamp === null || isAcceptedDateTime(value.sourceTimestamp))
    && (value.reasonCode === undefined || (typeof value.reasonCode === "string" && /^[A-Z0-9_]+$/.test(value.reasonCode)))
    && (value.outcome === "OK" ? value.value !== null : value.value === null);
}

function sanitizedReason(reason: string | undefined, fallback: string): string {
  return reason && /^[A-Z0-9_]+$/.test(reason) ? reason : fallback;
}

export function normalizeContractRecord<T>(
  record: ContractRecord<T>,
  clock: Clock,
  policyId: string,
  previous?: ReadObservation<T>,
  expectedSource: ContractRecord<T>["source"] = record.source,
  validateValue: (value: unknown) => value is T = (_value: unknown): _value is T => true,
): ReadObservation<T> {
  const readCompletedAt = clock();
  if (!isAcceptedDateTime(readCompletedAt)) throw new Error("FIXTURE_CLOCK_MALFORMED");
  const source = {
    owner: expectedSource === "AOSCLOUD_OEM" ? "AosCloud OEM" : expectedSource === "AOSCLOUD_BRAKE_SP1" ? "AosCloud Brake SP1" : "Brake Backend",
    sourceClass: expectedSource,
    contractClass: "CONTRACT_SYNTHETIC" as const,
    freshnessPolicyId: policyId,
  };
  if (!recordEnvelopeIsValid(record, expectedSource) || (record.outcome === "OK" && !validateValue(record.value))) {
    return readObservation<T>({ value: null, source, sourceTimestamp: null, readCompletedAt, state: "INCOMPLETE", transport: "MALFORMED", reason: "CLOSED_FIXTURE_SCHEMA_MISMATCH" });
  }
  if (record.outcome === "OK") {
    if (record.value === null) {
      return readObservation<T>({ value: null, source, sourceTimestamp: record.sourceTimestamp, readCompletedAt, state: "UNKNOWN", transport: "MALFORMED", reason: "NULL_SUCCESS_VALUE" });
    }
    return readObservation({
      value: structuredClone(record.value),
      source,
      sourceTimestamp: record.sourceTimestamp,
      readCompletedAt,
      state: record.freshness,
      transport: "AVAILABLE",
      ...(record.freshness === "STALE" ? { reason: "Current state cannot be confirmed" } : {}),
    });
  }
  if (record.outcome === "REDACTED") {
    return readObservation<T>({ value: null, source, sourceTimestamp: record.sourceTimestamp, readCompletedAt, state: "REDACTED", transport: "AVAILABLE", reason: sanitizedReason(record.reasonCode, "VALUE_REDACTED") });
  }
  if (record.outcome === "SOURCE_UNAVAILABLE" && previous?.value !== null && previous?.value !== undefined) {
    return readObservation({
      value: structuredClone(previous.value),
      source,
      sourceTimestamp: previous.sourceTimestamp,
      readCompletedAt,
      state: "STALE",
      transport: "SOURCE_UNAVAILABLE",
      reason: "Current state cannot be confirmed",
    });
  }
  return readObservation<T>({
    value: null,
    source,
    sourceTimestamp: record.sourceTimestamp,
    readCompletedAt,
    state: record.outcome === "MALFORMED" ? "INCOMPLETE" : "UNKNOWN",
    transport: outcomeMap[record.outcome],
    reason: sanitizedReason(record.reasonCode, `${record.source}_READ_FAILED`),
  });
}

function incomplete<T>(observation: ReadObservation<T>, reason: string): ReadObservation<T> {
  return readObservation<T>({ ...observation, value: null, state: "INCOMPLETE", transport: "MALFORMED", reason });
}

function unavailableFromSession<T>(observation: ReadObservation<T>, session: ReadObservation<SessionView>, reason: string): ReadObservation<T> {
  return readObservation<T>({
    ...observation,
    value: null,
    state: "UNKNOWN",
    transport: session.transport,
    reason,
  });
}

function notApplicable<T>(observation: ReadObservation<T>, reason: string): ReadObservation<T> {
  return readObservation<T>({
    ...observation,
    value: null,
    state: "NOT_APPLICABLE",
    transport: "AVAILABLE",
    reason,
  });
}

function sessionIsValid(value: SessionView | null, routeContext: SessionView["routeContext"], role: string, ownerPrefix: string, permissions: readonly string[]): boolean {
  return Boolean(
    value
      && value.routeContext === routeContext
      && value.role === role
      && value.ownerFingerprint.startsWith(ownerPrefix)
      && permissions.every((permission) => value.effectivePermissions.includes(permission)),
  );
}

function bindingsAreExact(value: readonly VehicleBindingView[] | null): boolean {
  if (!value || value.length !== 2) return false;
  const test = value.find((item) => item.role === "TEST");
  const production = value.find((item) => item.role === "PRODUCTION");
  if (!test || !production || test.wireRole !== "VALIDATION" || production.wireRole !== "PRODUCTION") return false;
  const fingerprints = value.flatMap((item) => [item.systemUidFingerprint, item.unitFingerprint, item.mainNodeFingerprint, item.unitSetFingerprint]);
  return new Set(fingerprints).size === fingerprints.length;
}

function unitsAreExact(value: readonly UnitView[] | null, bindings: readonly VehicleBindingView[] | null): boolean {
  if (!value || !bindings || value.length !== 2) return false;
  for (const role of ["TEST", "PRODUCTION"] as const) {
    const unit = value.find((item) => item.role === role);
    const binding = bindings.find((item) => item.role === role);
    if (!unit || !binding
      || unit.systemUidFingerprint !== binding.systemUidFingerprint
      || unit.unitFingerprint !== binding.unitFingerprint
      || unit.mainNodeFingerprint !== binding.mainNodeFingerprint) return false;
  }
  return new Set(value.map((item) => item.role)).size === 2;
}

function setsAreExact(records: AosCloudFixtureRecords, bindings: readonly VehicleBindingView[] | null): boolean {
  if (!records.unitSets.value || !bindings || records.unitSets.value.length !== 2) return false;
  for (const role of ["TEST", "PRODUCTION"] as const) {
    const binding = bindings.find((item) => item.role === role);
    const set = records.unitSets.value.find((item) => item.role === role);
    const pages = records.unitSetPages.filter((item) => item.role === role).sort((a, b) => a.page - b.page);
    if (!binding || !set || !set.complete || pages.length === 0 || pages.at(-1)?.hasNext || pages.at(-1)?.nextCursor !== null) return false;
    if (pages.some((item, index) => item.page !== index + 1)) return false;
    if (pages[0]?.cursor !== null) return false;
    if (pages.some((item, index) => index < pages.length - 1
      && (!item.hasNext || item.nextCursor === null || item.nextCursor !== pages[index + 1]?.cursor))) return false;
    const members = pages.flatMap((item) => item.members);
    if (new Set(members).size !== members.length || members.length !== 1 || members[0] !== binding.unitFingerprint) return false;
    if (set.memberUnitFingerprints.length !== 1 || set.memberUnitFingerprints[0] !== binding.unitFingerprint) return false;
    if (set.isValidationSet !== (role === "TEST")) return false;
  }
  return true;
}

function logsAreScoped(value: readonly NativeLogView[] | null, family: NativeLogView["family"], owner: NativeLogView["owner"]): boolean {
  return Boolean(value && value.every((item) => item.family === family && item.owner === owner && item.retentionNotice === "Retention policy not exposed by current API"));
}

function releaseRecipientsAreExact(
  releases: readonly ReleaseObjectView[] | null,
  bindings: readonly VehicleBindingView[] | null,
  units: readonly UnitView[] | null,
): boolean {
  if (!releases || !bindings || !units || releases.length !== 4) return false;
  if (new Set(releases.map((item) => item.kind)).size !== 4 || new Set(releases.map((item) => item.fingerprint)).size !== 4) return false;
  const test = bindings.find((item) => item.role === "TEST");
  const production = bindings.find((item) => item.role === "PRODUCTION");
  const testUnit = units.find((item) => item.role === "TEST");
  const productionUnit = units.find((item) => item.role === "PRODUCTION");
  if (!test || !production || !testUnit || !productionUnit) return false;
  const verificationFingerprints: string[] = [];
  for (const release of releases) {
    if (release.kind === "CANDIDATE" && (release.state !== "published" || release.targetFingerprints.length !== 0)) return false;
    if (release.kind === "VERIFICATION_BATCH") {
      verificationFingerprints.push(release.fingerprint);
      if (release.state !== "waiting") return false;
      if (release.targetFingerprints.length !== 1 || release.targetFingerprints[0] !== test.unitFingerprint) return false;
      if (!testUnit.pendingServiceBatchFingerprints.includes(release.fingerprint) || productionUnit.pendingServiceBatchFingerprints.includes(release.fingerprint)) return false;
    }
    if (release.kind === "FLEET_VALIDATION_BATCH"
      && (release.state !== "valid" || release.targetFingerprints.length !== 1 || !/^fleet:demo:[0-9a-f]{4}$/.test(release.targetFingerprints[0]!))) return false;
    if (release.kind === "CAMPAIGN" && !release.unresolvedShape) {
      if (release.state !== "done" || release.targetFingerprints.length !== 1 || release.targetFingerprints[0] !== production.unitSetFingerprint) return false;
    }
  }
  if (testUnit.pendingComponentBatchFingerprints.length !== 0 || productionUnit.pendingComponentBatchFingerprints.length !== 0) return false;
  if (testUnit.pendingServiceBatchFingerprints.length !== verificationFingerprints.length
    || testUnit.pendingServiceBatchFingerprints.some((item) => !verificationFingerprints.includes(item))) return false;
  return true;
}

export function aosCloudReadModel(fixture: ReadOnlyFixturePackage, clock: Clock): AosCloudReadProjection {
  const { aosCloud, policyId } = fixture;
  let session = normalizeContractRecord(aosCloud.session, clock, policyId, undefined, "AOSCLOUD_OEM", sessionShapeIsValid);
  let brakeSession = normalizeContractRecord(aosCloud.brakeSession, clock, policyId, undefined, "AOSCLOUD_BRAKE_SP1", sessionShapeIsValid);
  let bindings = normalizeContractRecord(aosCloud.bindings, clock, policyId, undefined, "AOSCLOUD_OEM", (value): value is readonly VehicleBindingView[] => arrayOf(value, bindingShapeIsValid));
  let units = normalizeContractRecord(aosCloud.units, clock, policyId, undefined, "AOSCLOUD_OEM", (value): value is readonly UnitView[] => arrayOf(value, unitShapeIsValid));
  let unitSets = normalizeContractRecord(aosCloud.unitSets, clock, policyId, undefined, "AOSCLOUD_OEM", (value): value is readonly UnitSetView[] => arrayOf(value, unitSetShapeIsValid));
  let releases = normalizeContractRecord(aosCloud.releases, clock, policyId, undefined, "AOSCLOUD_OEM", (value): value is readonly ReleaseObjectView[] => arrayOf(value, releaseShapeIsValid));
  let unitLogs = normalizeContractRecord(aosCloud.unitLogs, clock, policyId, undefined, "AOSCLOUD_OEM", (value): value is readonly NativeLogView[] => arrayOf(value, nativeLogShapeIsValid));
  let serviceLogs = normalizeContractRecord(aosCloud.serviceLogs, clock, policyId, undefined, "AOSCLOUD_BRAKE_SP1", (value): value is readonly NativeLogView[] => arrayOf(value, nativeLogShapeIsValid));

  if (session.state === "CURRENT" && !sessionIsValid(session.value, "oem-delivery-read", "OEM", "owner:oem:", oemPermissions)) {
    session = incomplete(session, "OEM_SESSION_SCOPE_MISMATCH");
  }
  if (brakeSession.state === "CURRENT" && !sessionIsValid(brakeSession.value, "brake-sp1-read", "Service Provider", "owner:brake-sp1:", brakePermissions)) {
    brakeSession = incomplete(brakeSession, "BRAKE_SESSION_SCOPE_MISMATCH");
  }
  if (bindings.state === "CURRENT" && !bindingsAreExact(bindings.value)) bindings = incomplete(bindings, "VEHICLE_BINDING_AMBIGUOUS");
  if (units.state === "CURRENT" && !unitsAreExact(units.value, bindings.value)) units = incomplete(units, "UNIT_NODE_BINDING_MISMATCH");
  if (unitSets.state === "CURRENT" && (!unitSetPagesShapeIsValid(aosCloud.unitSetPages) || !setsAreExact(aosCloud, bindings.value))) unitSets = incomplete(unitSets, "UNIT_SET_MEMBERSHIP_INCOMPLETE");
  if (releases.state === "CURRENT" && releases.value?.some((item) => item.unresolvedShape)) releases = incomplete(releases, "CAMPAIGN_RESPONSE_SHAPE_UNRESOLVED");
  else if (releases.state === "CURRENT" && !releaseRecipientsAreExact(releases.value, bindings.value, units.value)) releases = incomplete(releases, "RELEASE_RECIPIENT_SET_MISMATCH");
  if (unitLogs.state === "CURRENT" && !logsAreScoped(unitLogs.value, "unit-logs", "OEM")) unitLogs = incomplete(unitLogs, "UNIT_LOG_SCOPE_MISMATCH");
  if (serviceLogs.state === "CURRENT" && !logsAreScoped(serviceLogs.value, "service-logs", "BRAKE_SP1")) serviceLogs = incomplete(serviceLogs, "SERVICE_LOG_SCOPE_MISMATCH");

  if (session.state !== "CURRENT") {
    bindings = unavailableFromSession(bindings, session, "OEM_SESSION_NOT_CURRENT");
    units = unavailableFromSession(units, session, "OEM_SESSION_NOT_CURRENT");
    unitSets = unavailableFromSession(unitSets, session, "OEM_SESSION_NOT_CURRENT");
    releases = unavailableFromSession(releases, session, "OEM_SESSION_NOT_CURRENT");
    unitLogs = unavailableFromSession(unitLogs, session, "OEM_SESSION_NOT_CURRENT");
  }
  if (brakeSession.state !== "CURRENT") {
    serviceLogs = unavailableFromSession(serviceLogs, brakeSession, "BRAKE_SESSION_NOT_CURRENT");
  }
  if (fixture.phase === "PRE_M1") {
    bindings = notApplicable(bindings, "NO_UNIT_BEFORE_M1");
    units = notApplicable(units, "NO_UNIT_BEFORE_M1");
    unitSets = notApplicable(unitSets, "NO_UNIT_BEFORE_M1");
    releases = notApplicable(releases, "NO_MANAGED_TARGET_BEFORE_M1");
    unitLogs = notApplicable(unitLogs, "NO_UNIT_LOG_SCOPE_BEFORE_M1");
    serviceLogs = notApplicable(serviceLogs, "NO_SERVICE_LOG_SCOPE_BEFORE_M1");
  }

  return { session, brakeSession, bindings, units, unitSets, releases, unitLogs, serviceLogs };
}
