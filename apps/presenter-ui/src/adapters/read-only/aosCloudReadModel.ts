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

function sanitizedReason(reason: string | undefined, fallback: string): string {
  return reason && /^[A-Z0-9_]+$/.test(reason) ? reason : fallback;
}

export function normalizeContractRecord<T>(
  record: ContractRecord<T>,
  clock: Clock,
  policyId: string,
  previous?: ReadObservation<T>,
): ReadObservation<T> {
  const source = {
    owner: record.source === "AOSCLOUD_OEM" ? "AosCloud OEM" : record.source === "AOSCLOUD_BRAKE_SP1" ? "AosCloud Brake SP1" : "Brake Backend",
    sourceClass: record.source,
    contractClass: "CONTRACT_SYNTHETIC" as const,
    freshnessPolicyId: policyId,
  };
  if (record.outcome === "OK") {
    if (record.value === null) {
      return readObservation<T>({ value: null, source, sourceTimestamp: record.sourceTimestamp, readCompletedAt: clock(), state: "UNKNOWN", transport: "MALFORMED", reason: "NULL_SUCCESS_VALUE" });
    }
    return readObservation({
      value: structuredClone(record.value),
      source,
      sourceTimestamp: record.sourceTimestamp,
      readCompletedAt: clock(),
      state: record.freshness,
      transport: "AVAILABLE",
      ...(record.freshness === "STALE" ? { reason: "Current state cannot be confirmed" } : {}),
    });
  }
  if (record.outcome === "SOURCE_UNAVAILABLE" && previous?.value !== null && previous?.value !== undefined) {
    return readObservation({
      value: structuredClone(previous.value),
      source,
      sourceTimestamp: previous.sourceTimestamp,
      readCompletedAt: clock(),
      state: "STALE",
      transport: "SOURCE_UNAVAILABLE",
      reason: "Current state cannot be confirmed",
    });
  }
  return readObservation<T>({
    value: null,
    source,
    sourceTimestamp: record.sourceTimestamp,
    readCompletedAt: clock(),
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

function setsAreExact(records: AosCloudFixtureRecords, bindings: readonly VehicleBindingView[] | null): boolean {
  if (!records.unitSets.value || !bindings || records.unitSets.value.length !== 2) return false;
  for (const role of ["TEST", "PRODUCTION"] as const) {
    const binding = bindings.find((item) => item.role === role);
    const set = records.unitSets.value.find((item) => item.role === role);
    const pages = records.unitSetPages.filter((item) => item.role === role).sort((a, b) => a.page - b.page);
    if (!binding || !set || !set.complete || pages.length === 0 || pages.some((item) => item.hasNext)) return false;
    if (pages.some((item, index) => item.page !== index + 1)) return false;
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
  if (!releases || !bindings || !units) return false;
  const test = bindings.find((item) => item.role === "TEST");
  const production = bindings.find((item) => item.role === "PRODUCTION");
  const testUnit = units.find((item) => item.role === "TEST");
  const productionUnit = units.find((item) => item.role === "PRODUCTION");
  if (!test || !production || !testUnit || !productionUnit) return false;
  for (const release of releases) {
    if (release.kind === "VERIFICATION_BATCH") {
      if (release.targetFingerprints.length !== 1 || release.targetFingerprints[0] !== test.unitFingerprint) return false;
      if (!testUnit.pendingBatchFingerprints.includes(release.fingerprint) || productionUnit.pendingBatchFingerprints.includes(release.fingerprint)) return false;
    }
    if (release.kind === "CAMPAIGN" && !release.unresolvedShape) {
      if (release.targetFingerprints.length !== 1 || release.targetFingerprints[0] !== production.unitSetFingerprint) return false;
    }
  }
  return true;
}

export function aosCloudReadModel(fixture: ReadOnlyFixturePackage, clock: Clock): AosCloudReadProjection {
  const { aosCloud, policyId } = fixture;
  let session = normalizeContractRecord(aosCloud.session, clock, policyId);
  let brakeSession = normalizeContractRecord(aosCloud.brakeSession, clock, policyId);
  let bindings = normalizeContractRecord(aosCloud.bindings, clock, policyId);
  let units = normalizeContractRecord(aosCloud.units, clock, policyId);
  let unitSets = normalizeContractRecord(aosCloud.unitSets, clock, policyId);
  let releases = normalizeContractRecord(aosCloud.releases, clock, policyId);
  let unitLogs = normalizeContractRecord(aosCloud.unitLogs, clock, policyId);
  let serviceLogs = normalizeContractRecord(aosCloud.serviceLogs, clock, policyId);

  if (session.state === "CURRENT" && !sessionIsValid(session.value, "oem-delivery-read", "OEM", "owner:oem:", ["users_me", "units_list", "units_read"])) {
    session = incomplete(session, "OEM_SESSION_SCOPE_MISMATCH");
  }
  if (brakeSession.state === "CURRENT" && !sessionIsValid(brakeSession.value, "brake-sp1-read", "Service Provider", "owner:brake-sp1:", ["users_me", "service_logs_list", "service_logs_read"])) {
    brakeSession = incomplete(brakeSession, "BRAKE_SESSION_SCOPE_MISMATCH");
  }
  if (bindings.state === "CURRENT" && !bindingsAreExact(bindings.value)) bindings = incomplete(bindings, "VEHICLE_BINDING_AMBIGUOUS");
  if (unitSets.state === "CURRENT" && !setsAreExact(aosCloud, bindings.value)) unitSets = incomplete(unitSets, "UNIT_SET_MEMBERSHIP_INCOMPLETE");
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
