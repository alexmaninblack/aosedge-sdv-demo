import type {
  BrakeResourceView,
  NativeLogView,
  ReleaseObjectView,
  SessionView,
  UnitSetView,
  UnitView,
  VehicleBindingView,
} from "../../domain";
import { requiredReadPlansForContext, type ContractRecord, type ReadOnlyFixturePackage } from "./contracts";

const SOURCE_TIME = "2026-08-30T09:00:00.000Z";

const oemSession: SessionView = {
  routeContext: "oem-delivery-read",
  role: "OEM",
  ownerFingerprint: "owner:oem:4a21",
  effectivePermissions: [
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
  ],
};

const brakeSession: SessionView = {
  routeContext: "brake-sp1-read",
  role: "Service Provider",
  ownerFingerprint: "owner:brake-sp1:1b52",
  effectivePermissions: ["users_me", "service_logs_list", "service_logs_read"],
};

const bindings: readonly VehicleBindingView[] = [
  {
    role: "TEST",
    label: "Test Vehicle",
    wireRole: "VALIDATION",
    systemUidFingerprint: "uid:test:76d2",
    unitFingerprint: "unit:test:7c91",
    mainNodeFingerprint: "node:test-main:853a",
    unitSetFingerprint: "set:test:8d0f",
  },
  {
    role: "PRODUCTION",
    label: "Production Vehicle",
    wireRole: "PRODUCTION",
    systemUidFingerprint: "uid:production:9b14",
    unitFingerprint: "unit:production:4e22",
    mainNodeFingerprint: "node:production-main:59bd",
    unitSetFingerprint: "set:production:103c",
  },
];

const units: readonly UnitView[] = [
  {
    role: "TEST",
    systemUidFingerprint: "uid:test:76d2",
    unitFingerprint: "unit:test:7c91",
    mainNodeFingerprint: "node:test-main:853a",
    connectionState: "Online",
    reportedState: "ready",
    desiredSoftware: ["VDP v2", "Brake v2"],
    actualSoftware: ["VDP v2", "Brake v2"],
    pendingComponentBatchFingerprints: [],
    pendingServiceBatchFingerprints: ["verification:brake-v3:13f8"],
  },
  {
    role: "PRODUCTION",
    systemUidFingerprint: "uid:production:9b14",
    unitFingerprint: "unit:production:4e22",
    mainNodeFingerprint: "node:production-main:59bd",
    connectionState: "Online",
    reportedState: "ready",
    desiredSoftware: ["VDP v2", "Brake v2"],
    actualSoftware: ["VDP v2", "Brake v2"],
    pendingComponentBatchFingerprints: [],
    pendingServiceBatchFingerprints: [],
  },
];

const unitSets: readonly UnitSetView[] = [
  {
    role: "TEST",
    title: "AosEdge SDV Demo / Test Vehicles",
    isValidationSet: true,
    memberUnitFingerprints: ["unit:test:7c91"],
    complete: true,
  },
  {
    role: "PRODUCTION",
    title: "AosEdge SDV Demo / Production Vehicles",
    isValidationSet: false,
    memberUnitFingerprints: ["unit:production:4e22"],
    complete: true,
  },
];

const releases: readonly ReleaseObjectView[] = [
  { kind: "CANDIDATE", fingerprint: "candidate:brake-v3:8a4f", state: "published", targetFingerprints: [] },
  { kind: "VERIFICATION_BATCH", fingerprint: "verification:brake-v3:13f8", state: "waiting", targetFingerprints: ["unit:test:7c91"] },
  { kind: "FLEET_VALIDATION_BATCH", fingerprint: "fleet-validation:brake-v2:b827", state: "valid", targetFingerprints: ["fleet:demo:ed29"] },
  { kind: "CAMPAIGN", fingerprint: "campaign:brake-v2:27a1", state: "done", targetFingerprints: ["set:production:103c"], result: "1/1 done" },
];

const logStates: readonly NativeLogView["cloudState"][] = [
  "created",
  "sent",
  "waiting unit",
  "receiving",
  "done",
  "error",
  "empty log has been provided",
];

const unitLogs: readonly NativeLogView[] = logStates.map((cloudState, index) => ({
  family: "unit-logs",
  owner: "OEM",
  scopeFingerprint: "unit:test:7c91",
  requestFingerprint: `unit-log:${index + 1}:c0de`,
  cloudState,
  metadata: ["scope=Test Vehicle", `state=${cloudState}`],
  retentionNotice: "Retention policy not exposed by current API",
}));

const serviceLogs: readonly NativeLogView[] = [
  {
    family: "service-logs",
    owner: "BRAKE_SP1",
    scopeFingerprint: "service:brake-v2:6c30",
    requestFingerprint: "service-log:1:ad24",
    cloudState: "done",
    metadata: ["scope=Brake Service", "state=done"],
    retentionNotice: "Retention policy not exposed by current API",
  },
];

const brakeResources: readonly BrakeResourceView[] = [
  { role: "TEST", unitSystemUidFingerprint: "uid:test:76d2", resourceType: "WINDOW", state: "COMPLETE", deliveryState: "DURABLY_RECEIVED", projectionState: "TERMINAL", terminalState: "COMPLETE", count: 1, limit: 50, nextCursor: null, complete: true, sourceTime: SOURCE_TIME, backendReceivedAt: "2026-08-30T09:00:01.000Z", vdpVersion: "2.0.0", vdpDigest: "sha256:3f50…a0c2" },
  { role: "TEST", unitSystemUidFingerprint: "uid:test:76d2", resourceType: "ASSESSMENT", state: "ASSESSED", deliveryState: "DURABLY_RECEIVED", projectionState: null, terminalState: null, count: 1, limit: 50, nextCursor: null, complete: true, sourceTime: SOURCE_TIME, backendReceivedAt: "2026-08-30T09:00:01.000Z", vdpVersion: "2.0.0", vdpDigest: "sha256:3f50…a0c2" },
  { role: "TEST", unitSystemUidFingerprint: "uid:test:76d2", resourceType: "EVENT", state: "PENDING_ASSESSMENT_CORRELATION", deliveryState: "DURABLY_RECEIVED", projectionState: null, terminalState: null, count: 1, limit: 50, nextCursor: null, complete: true, sourceTime: SOURCE_TIME, backendReceivedAt: "2026-08-30T09:00:01.000Z", vdpVersion: null, vdpDigest: null },
  { role: "TEST", unitSystemUidFingerprint: "uid:test:76d2", resourceType: "ADVISORY", state: "PUBLISHED", deliveryState: "DURABLY_RECEIVED", projectionState: null, terminalState: null, count: 1, limit: 50, nextCursor: null, complete: true, sourceTime: SOURCE_TIME, backendReceivedAt: "2026-08-30T09:00:01.000Z", vdpVersion: "2.0.0", vdpDigest: "sha256:3f50…a0c2" },
];

function record<T>(source: "AOSCLOUD_OEM" | "AOSCLOUD_BRAKE_SP1" | "BRAKE_BACKEND", value: T) {
  return {
    contractClass: "CONTRACT_SYNTHETIC" as const,
    source,
    outcome: "OK" as const,
    freshness: "CURRENT" as const,
    sourceTimestamp: SOURCE_TIME,
    value,
  };
}

function basePackage(): ReadOnlyFixturePackage {
  return {
    fixtureId: "ready",
    contractClass: "CONTRACT_SYNTHETIC",
    policyId: "FIXTURE_POLICY_EXPLICIT_V1",
    phase: "MANAGED",
    plans: requiredReadPlansForContext("TEST", "uid:test:76d2"),
    aosCloud: {
      session: record("AOSCLOUD_OEM", structuredClone(oemSession)),
      brakeSession: record("AOSCLOUD_BRAKE_SP1", structuredClone(brakeSession)),
      bindings: record("AOSCLOUD_OEM", structuredClone(bindings)),
      units: record("AOSCLOUD_OEM", structuredClone(units)),
      unitSets: record("AOSCLOUD_OEM", structuredClone(unitSets)),
      unitSetPages: [
        { role: "TEST", page: 1, hasNext: false, cursor: null, nextCursor: null, members: ["unit:test:7c91"] },
        { role: "PRODUCTION", page: 1, hasNext: false, cursor: null, nextCursor: null, members: ["unit:production:4e22"] },
      ],
      releases: record("AOSCLOUD_OEM", structuredClone(releases)),
      unitLogs: record("AOSCLOUD_OEM", structuredClone(unitLogs)),
      serviceLogs: record("AOSCLOUD_BRAKE_SP1", structuredClone(serviceLogs)),
    },
    brake: {
      contextRole: "TEST",
      contextSystemUidFingerprint: "uid:test:76d2",
      resources: record("BRAKE_BACKEND", structuredClone(brakeResources)),
      notificationCount: 0,
      restReadCount: 1,
    },
  };
}

const variants = {
  ready: () => basePackage(),
  m0: () => {
    const value = basePackage();
    value.fixtureId = "m0";
    value.phase = "PRE_M1";
    value.aosCloud.bindings.value = [];
    value.aosCloud.units.value = [];
    value.aosCloud.unitSets.value = [];
    value.aosCloud.unitSetPages = [];
    value.aosCloud.releases.value = [];
    value.aosCloud.unitLogs.value = [];
    value.aosCloud.serviceLogs.value = [];
    value.brake.contextRole = null;
    value.brake.contextSystemUidFingerprint = null;
    value.brake.resources.value = [];
    return value;
  },
  production: () => {
    const value = basePackage();
    value.fixtureId = "production";
    value.brake.contextRole = "PRODUCTION";
    value.brake.contextSystemUidFingerprint = "uid:production:9b14";
    value.brake.resources.value = brakeResources.map((item) => ({ ...item, role: "PRODUCTION", unitSystemUidFingerprint: "uid:production:9b14" }));
    return value;
  },
  stale: () => {
    const value = basePackage();
    value.fixtureId = "stale";
    value.aosCloud.units.freshness = "STALE";
    return value;
  },
  offline: () => {
    const value = basePackage();
    value.fixtureId = "offline";
    value.aosCloud.units.value = units.map((item) => ({ ...item, connectionState: "Offline" }));
    return value;
  },
  "read-only-stale": () => {
    const value = basePackage();
    value.fixtureId = "read-only-stale";
    value.aosCloud.units.freshness = "STALE";
    return value;
  },
  "read-only-unauthenticated": () => {
    const value = basePackage();
    value.fixtureId = "read-only-unauthenticated";
    value.aosCloud.session = { ...value.aosCloud.session, outcome: "401", value: null, reasonCode: "SESSION_UNAUTHENTICATED" };
    return value;
  },
  "read-only-forbidden": () => {
    const value = basePackage();
    value.fixtureId = "read-only-forbidden";
    value.aosCloud.unitLogs = { ...value.aosCloud.unitLogs, outcome: "403", value: null, reasonCode: "UNIT_LOG_SCOPE_FORBIDDEN" };
    return value;
  },
  "read-only-not-found": () => {
    const value = basePackage();
    value.fixtureId = "read-only-not-found";
    value.aosCloud.releases = { ...value.aosCloud.releases, outcome: "404", value: null, reasonCode: "RELEASE_NOT_FOUND_OR_INACCESSIBLE" };
    return value;
  },
  "read-only-rejected": () => {
    const value = basePackage();
    value.fixtureId = "read-only-rejected";
    value.aosCloud.units = { ...value.aosCloud.units, outcome: "400", value: null, reasonCode: "READ_REJECTED" };
    return value;
  },
  "read-only-schema-invalid": () => {
    const value = basePackage();
    value.fixtureId = "read-only-schema-invalid";
    value.brake.resources = { ...value.brake.resources, outcome: "422", value: null, reasonCode: "BRAKE_SCHEMA_INVALID" };
    return value;
  },
  "read-only-source-unavailable": () => {
    const value = basePackage();
    value.fixtureId = "read-only-source-unavailable";
    value.brake.resources = { ...value.brake.resources, outcome: "SOURCE_UNAVAILABLE", value: null, reasonCode: "BRAKE_SOURCE_UNAVAILABLE" };
    return value;
  },
  "read-only-truncated-membership": () => {
    const value = basePackage();
    value.fixtureId = "read-only-truncated-membership";
    value.aosCloud.unitSetPages = [
      { ...value.aosCloud.unitSetPages[0]!, hasNext: true },
      ...value.aosCloud.unitSetPages.slice(1),
    ];
    return value;
  },
  "read-only-paginated-membership": () => {
    const value = basePackage();
    value.fixtureId = "read-only-paginated-membership";
    value.aosCloud.unitSetPages = [
      { role: "TEST", page: 1, hasNext: true, cursor: null, nextCursor: "test_page_2", members: [] },
      { role: "TEST", page: 2, hasNext: false, cursor: "test_page_2", nextCursor: null, members: ["unit:test:7c91"] },
      ...value.aosCloud.unitSetPages.filter((item) => item.role === "PRODUCTION"),
    ];
    return value;
  },
  "read-only-crossed-membership": () => {
    const value = basePackage();
    value.fixtureId = "read-only-crossed-membership";
    value.aosCloud.unitSetPages = [
      { role: "TEST", page: 1, hasNext: false, cursor: null, nextCursor: null, members: ["unit:production:4e22"] },
      { role: "PRODUCTION", page: 1, hasNext: false, cursor: null, nextCursor: null, members: ["unit:test:7c91"] },
    ];
    return value;
  },
  "read-only-wrong-owner": () => {
    const value = basePackage();
    value.fixtureId = "read-only-wrong-owner";
    value.aosCloud.brakeSession.value = { ...brakeSession, ownerFingerprint: "owner:other-provider:5f11" };
    return value;
  },
  "read-only-wrong-role": () => {
    const value = basePackage();
    value.fixtureId = "read-only-wrong-role";
    value.aosCloud.session.value = { ...oemSession, role: "Fleet Owner" };
    return value;
  },
  "read-only-missing-permission": () => {
    const value = basePackage();
    value.fixtureId = "read-only-missing-permission";
    value.aosCloud.session.value = { ...oemSession, effectivePermissions: oemSession.effectivePermissions.filter((item) => item !== "units_read") };
    return value;
  },
  "read-only-missing-campaign-permission": () => {
    const value = basePackage();
    value.fixtureId = "read-only-missing-campaign-permission";
    value.aosCloud.session.value = { ...oemSession, effectivePermissions: oemSession.effectivePermissions.filter((item) => item !== "campaigns_read") };
    return value;
  },
  "read-only-missing-unit": () => {
    const value = basePackage();
    value.fixtureId = "read-only-missing-unit";
    value.aosCloud.units.value = value.aosCloud.units.value?.filter((item) => item.role !== "TEST") ?? null;
    return value;
  },
  "read-only-ambiguous-unit": () => {
    const value = basePackage();
    value.fixtureId = "read-only-ambiguous-unit";
    value.aosCloud.units.value = value.aosCloud.units.value ? [...value.aosCloud.units.value, { ...value.aosCloud.units.value[0]! }] : null;
    return value;
  },
  "read-only-wrong-main-node": () => {
    const value = basePackage();
    value.fixtureId = "read-only-wrong-main-node";
    value.aosCloud.units.value = value.aosCloud.units.value?.map((item) => item.role === "TEST" ? { ...item, mainNodeFingerprint: "node:other-main:0bad" } : item) ?? null;
    return value;
  },
  "read-only-wrong-log-family": () => {
    const value = basePackage();
    value.fixtureId = "read-only-wrong-log-family";
    value.aosCloud.serviceLogs.value = [{ ...unitLogs[0]!, family: "unit-logs", owner: "OEM" }];
    return value;
  },
  "read-only-missing-log-detail": () => {
    const value = basePackage();
    value.fixtureId = "read-only-missing-log-detail";
    value.aosCloud.unitLogs.value = value.aosCloud.unitLogs.value?.filter((item) => item.requestFingerprint !== "unit-log:1:c0de") ?? null;
    return value;
  },
  "read-only-campaign-unit-ids": () => {
    const value = basePackage();
    value.fixtureId = "read-only-campaign-unit-ids";
    value.aosCloud.releases.value = [...releases, { kind: "CAMPAIGN", fingerprint: "campaign:shape:a312", state: "preview", targetFingerprints: [], unresolvedShape: "unit_ids" }];
    return value;
  },
  "read-only-campaign-units-ids": () => {
    const value = basePackage();
    value.fixtureId = "read-only-campaign-units-ids";
    value.aosCloud.releases.value = [...releases, { kind: "CAMPAIGN", fingerprint: "campaign:shape:b462", state: "preview", targetFingerprints: [], unresolvedShape: "units_ids" }];
    return value;
  },
  "read-only-brake-empty": () => {
    const value = basePackage();
    value.fixtureId = "read-only-brake-empty";
    value.brake.resources.value = brakeResources.map((item) => ({ ...item, count: 0 }));
    return value;
  },
  "read-only-brake-not-current": () => {
    const value = basePackage();
    value.fixtureId = "read-only-brake-not-current";
    value.brake.resources = { ...value.brake.resources, outcome: "404", value: null, reasonCode: "UNIT_NOT_CURRENT" };
    return value;
  },
  "read-only-brake-context-unavailable": () => {
    const value = basePackage();
    value.fixtureId = "read-only-brake-context-unavailable";
    value.brake.contextRole = null;
    value.brake.contextSystemUidFingerprint = null;
    value.brake.resources = { ...value.brake.resources, outcome: "SOURCE_UNAVAILABLE", value: null, reasonCode: "CURRENT_UNIT_CONTEXT_UNAVAILABLE" };
    return value;
  },
  "read-only-brake-wrong-unit": () => {
    const value = basePackage();
    value.fixtureId = "read-only-brake-wrong-unit";
    value.brake.contextSystemUidFingerprint = "uid:production:9b14";
    return value;
  },
  "read-only-brake-partial-window": () => {
    const value = basePackage();
    value.fixtureId = "read-only-brake-partial-window";
    value.brake.resources.value = value.brake.resources.value?.map((item) => item.resourceType === "WINDOW"
      ? { ...item, state: "PARTIAL", deliveryState: "RECEIVING", projectionState: "PARTIAL", terminalState: null }
      : item) ?? null;
    return value;
  },
  "read-only-brake-incomplete-page": () => {
    const value = basePackage();
    value.fixtureId = "read-only-brake-incomplete-page";
    value.brake.resources.value = value.brake.resources.value?.map((item) => item.resourceType === "WINDOW"
      ? { ...item, complete: false, nextCursor: "page_2" }
      : item) ?? null;
    return value;
  },
  "read-only-invalid-date": () => {
    const value = basePackage();
    value.fixtureId = "read-only-invalid-date";
    value.aosCloud.units.sourceTimestamp = "2026-02-30T09:00:00.000Z";
    return value;
  },
  "read-only-unknown-enum": () => {
    const value = basePackage();
    value.fixtureId = "read-only-unknown-enum";
    const first = value.aosCloud.units.value?.[0];
    if (first) (first as { connectionState: string }).connectionState = "CONNECTED_MAYBE";
    return value;
  },
  "read-only-notification": () => {
    const value = basePackage();
    value.fixtureId = "read-only-notification";
    value.brake.notificationCount = 1;
    value.brake.restReadCount = 2;
    return value;
  },
  "read-only-duplicate-membership": () => {
    const value = basePackage();
    value.fixtureId = "read-only-duplicate-membership";
    value.aosCloud.unitSetPages = [
      { role: "TEST", page: 1, hasNext: false, cursor: null, nextCursor: null, members: ["unit:test:7c91", "unit:test:7c91"] },
      ...value.aosCloud.unitSetPages.filter((item) => item.role === "PRODUCTION"),
    ];
    return value;
  },
  "read-only-prior-run-membership": () => {
    const value = basePackage();
    value.fixtureId = "read-only-prior-run-membership";
    value.aosCloud.unitSetPages = [
      { role: "TEST", page: 1, hasNext: false, cursor: null, nextCursor: null, members: ["unit:prior-run:44aa"] },
      ...value.aosCloud.unitSetPages.filter((item) => item.role === "PRODUCTION"),
    ];
    return value;
  },
  "read-only-extra-pending-recipient": () => {
    const value = basePackage();
    value.fixtureId = "read-only-extra-pending-recipient";
    value.aosCloud.releases.value = releases.map((item) => item.kind === "VERIFICATION_BATCH"
      ? { ...item, targetFingerprints: ["unit:test:7c91", "unit:production:4e22"] }
      : item);
    return value;
  },
  "read-only-missing-pending-recipient": () => {
    const value = basePackage();
    value.fixtureId = "read-only-missing-pending-recipient";
    value.aosCloud.releases.value = releases.map((item) => item.kind === "VERIFICATION_BATCH"
      ? { ...item, targetFingerprints: [] }
      : item);
    return value;
  },
  "read-only-stale-batch": () => {
    const value = basePackage();
    value.fixtureId = "read-only-stale-batch";
    value.aosCloud.releases.freshness = "STALE";
    return value;
  },
  "read-only-malformed": () => {
    const value = basePackage();
    value.fixtureId = "read-only-malformed";
    value.aosCloud.bindings = { ...value.aosCloud.bindings, outcome: "MALFORMED", reasonCode: "DUPLICATE_BINDING", value: null };
    return value;
  },
  "read-only-redacted": () => {
    const value = basePackage();
    value.fixtureId = "read-only-redacted";
    value.aosCloud.unitLogs = { ...value.aosCloud.unitLogs, outcome: "REDACTED", value: null, reasonCode: "LOG_METADATA_REDACTED" };
    return value;
  },
} satisfies Record<string, () => ReadOnlyFixturePackage>;

export const readOnlyFixtureIds = Object.freeze(Object.keys(variants));

const readyAliases = new Set([
  "blocked", "submitting", "uncertain", "reconciling", "failed", "safe-stop", "reconnected", "asset-failure", "m1",
  "qualification-absent", "qualification-stale", "qualification-withdrawn", "not-qualified",
]);

function unavailablePackage(id: string): ReadOnlyFixturePackage {
  const value = basePackage();
  const unavailable = <T>(recordValue: ContractRecord<T>): ContractRecord<T> => ({
    ...recordValue,
    outcome: "SOURCE_UNAVAILABLE",
    value: null,
    reasonCode: "FIXTURE_CONTEXT_UNAVAILABLE",
  });
  value.fixtureId = id;
  value.aosCloud.session = unavailable(value.aosCloud.session);
  value.aosCloud.brakeSession = unavailable(value.aosCloud.brakeSession);
  value.aosCloud.bindings = unavailable(value.aosCloud.bindings);
  value.aosCloud.units = unavailable(value.aosCloud.units);
  value.aosCloud.unitSets = unavailable(value.aosCloud.unitSets);
  value.aosCloud.releases = unavailable(value.aosCloud.releases);
  value.aosCloud.unitLogs = unavailable(value.aosCloud.unitLogs);
  value.aosCloud.serviceLogs = unavailable(value.aosCloud.serviceLogs);
  value.brake.contextRole = null;
  value.brake.contextSystemUidFingerprint = null;
  value.brake.resources = { ...value.brake.resources, outcome: "SOURCE_UNAVAILABLE", value: null, reasonCode: "CURRENT_UNIT_CONTEXT_UNAVAILABLE" };
  return value;
}

export function readOnlyFixtureById(id: string): ReadOnlyFixturePackage {
  const factory = variants[id as keyof typeof variants];
  let value: ReadOnlyFixturePackage;
  if (factory) value = factory();
  else if (readyAliases.has(id)) value = basePackage();
  else if (id === "r0") value = variants.m0();
  else value = unavailablePackage(id);
  value.fixtureId = id;
  value.plans = requiredReadPlansForContext(value.brake.contextRole, value.brake.contextSystemUidFingerprint);
  return value;
}
