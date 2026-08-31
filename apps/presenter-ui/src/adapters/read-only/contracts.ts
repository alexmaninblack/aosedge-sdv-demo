import type {
  AudienceVehicleRole,
  BrakeResourceView,
  NativeLogView,
  ReleaseObjectView,
  SessionView,
  UnitSetView,
  UnitView,
  VehicleBindingView,
} from "../../domain";

export const OEM_ROUTE_IDS = [
  "OEM_USERS_ME",
  "OEM_UNITS_PAGE",
  "OEM_UNIT_DETAIL",
  "OEM_UNIT_NODES_PAGE",
  "OEM_NODE_DETAIL",
  "OEM_SUBJECT_SERVICES_PAGE",
  "OEM_UNIT_SETS_PAGE",
  "OEM_UNIT_SET_DETAIL",
  "OEM_UNIT_SET_MEMBERS_PAGE",
  "OEM_VERIFICATION_BATCHES_PAGE",
  "OEM_VERIFICATION_BATCH_DETAIL",
  "OEM_FLEET_VALIDATION_BATCHES_PAGE",
  "OEM_FLEET_VALIDATION_BATCH_DETAIL",
  "OEM_CAMPAIGNS_PAGE",
  "OEM_CAMPAIGN_DETAIL",
  "OEM_UNIT_LOGS_PAGE",
  "OEM_UNIT_LOG_DETAIL",
] as const;

export const BRAKE_SP1_ROUTE_IDS = [
  "BRAKE_USERS_ME",
  "BRAKE_SERVICE_LOGS_PAGE",
  "BRAKE_SERVICE_LOG_DETAIL",
] as const;

export const BRAKE_BACKEND_ROUTE_IDS = [
  "BRAKE_WINDOWS",
  "BRAKE_ASSESSMENTS",
  "BRAKE_EVENTS",
  "BRAKE_ADVISORIES",
] as const;

export type OemRouteId = (typeof OEM_ROUTE_IDS)[number];
export type BrakeSp1RouteId = (typeof BRAKE_SP1_ROUTE_IDS)[number];
export type BrakeBackendRouteId = (typeof BRAKE_BACKEND_ROUTE_IDS)[number];

export interface ReadSelectors {
  contextId: string;
  objectFingerprint?: string;
  cursor?: string;
}

interface ReadRequestBase<RouteId extends string, Source extends string> {
  source: Source;
  routeId: RouteId;
  method: "GET";
  selectors: ReadSelectors;
  pagination: "SINGLE" | "COMPLETE";
}

export type ReadRequest =
  | ReadRequestBase<OemRouteId, "AOSCLOUD_OEM">
  | ReadRequestBase<BrakeSp1RouteId, "AOSCLOUD_BRAKE_SP1">
  | ReadRequestBase<BrakeBackendRouteId, "BRAKE_BACKEND">;

export type ReadRouteContext =
  | Readonly<{ routeContext: "oem-delivery-read"; role: "OEM" }>
  | Readonly<{ routeContext: "brake-sp1-read"; role: "Service Provider" }>
  | Readonly<{ routeContext: "brake-backend-read"; role: "Current Unit" }>;

export interface PlannedFixtureRead {
  plan: ReadRequest;
  context: ReadRouteContext;
  readCompletedAt: string;
  record: ContractRecord<unknown>;
}

const sourceRoutes = {
  AOSCLOUD_OEM: new Set<string>(OEM_ROUTE_IDS),
  AOSCLOUD_BRAKE_SP1: new Set<string>(BRAKE_SP1_ROUTE_IDS),
  BRAKE_BACKEND: new Set<string>(BRAKE_BACKEND_ROUTE_IDS),
} as const;

const requestKeys = new Set(["source", "routeId", "method", "selectors", "pagination"]);
const selectorKeys = new Set(["contextId", "objectFingerprint", "cursor"]);

const objectSelectedRoutes = new Set<string>([
  "OEM_UNIT_DETAIL",
  "OEM_UNIT_NODES_PAGE",
  "OEM_NODE_DETAIL",
  "OEM_SUBJECT_SERVICES_PAGE",
  "OEM_UNIT_SET_DETAIL",
  "OEM_UNIT_SET_MEMBERS_PAGE",
  "OEM_VERIFICATION_BATCH_DETAIL",
  "OEM_FLEET_VALIDATION_BATCH_DETAIL",
  "OEM_CAMPAIGN_DETAIL",
  "OEM_UNIT_LOG_DETAIL",
  "BRAKE_SERVICE_LOG_DETAIL",
  ...BRAKE_BACKEND_ROUTE_IDS,
]);

const completeRoutes = new Set<string>([
  "OEM_UNITS_PAGE",
  "OEM_UNIT_NODES_PAGE",
  "OEM_SUBJECT_SERVICES_PAGE",
  "OEM_UNIT_SETS_PAGE",
  "OEM_UNIT_SET_MEMBERS_PAGE",
  "OEM_VERIFICATION_BATCHES_PAGE",
  "OEM_FLEET_VALIDATION_BATCHES_PAGE",
  "OEM_CAMPAIGNS_PAGE",
  "OEM_UNIT_LOGS_PAGE",
  "BRAKE_SERVICE_LOGS_PAGE",
  ...BRAKE_BACKEND_ROUTE_IDS,
]);

const cloudReadPlans: readonly ReadRequest[] = [
  { source: "AOSCLOUD_OEM", routeId: "OEM_USERS_ME", method: "GET", selectors: { contextId: "oem-session" }, pagination: "SINGLE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_UNITS_PAGE", method: "GET", selectors: { contextId: "vehicle-inventory" }, pagination: "COMPLETE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_UNIT_DETAIL", method: "GET", selectors: { contextId: "vehicle-inventory", objectFingerprint: "unit:test:7c91" }, pagination: "SINGLE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_UNIT_DETAIL", method: "GET", selectors: { contextId: "vehicle-inventory", objectFingerprint: "unit:production:4e22" }, pagination: "SINGLE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_UNIT_NODES_PAGE", method: "GET", selectors: { contextId: "vehicle-inventory", objectFingerprint: "unit:test:7c91" }, pagination: "COMPLETE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_UNIT_NODES_PAGE", method: "GET", selectors: { contextId: "vehicle-inventory", objectFingerprint: "unit:production:4e22" }, pagination: "COMPLETE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_NODE_DETAIL", method: "GET", selectors: { contextId: "vehicle-inventory", objectFingerprint: "node:test-main:853a" }, pagination: "SINGLE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_NODE_DETAIL", method: "GET", selectors: { contextId: "vehicle-inventory", objectFingerprint: "node:production-main:59bd" }, pagination: "SINGLE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_SUBJECT_SERVICES_PAGE", method: "GET", selectors: { contextId: "pending-recipients", objectFingerprint: "unit:test:7c91" }, pagination: "COMPLETE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_SUBJECT_SERVICES_PAGE", method: "GET", selectors: { contextId: "pending-recipients", objectFingerprint: "unit:production:4e22" }, pagination: "COMPLETE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_UNIT_SETS_PAGE", method: "GET", selectors: { contextId: "role-sets" }, pagination: "COMPLETE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_UNIT_SET_DETAIL", method: "GET", selectors: { contextId: "role-sets", objectFingerprint: "set:test:8d0f" }, pagination: "SINGLE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_UNIT_SET_DETAIL", method: "GET", selectors: { contextId: "role-sets", objectFingerprint: "set:production:103c" }, pagination: "SINGLE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_UNIT_SET_MEMBERS_PAGE", method: "GET", selectors: { contextId: "role-sets", objectFingerprint: "set:test:8d0f" }, pagination: "COMPLETE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_UNIT_SET_MEMBERS_PAGE", method: "GET", selectors: { contextId: "role-sets", objectFingerprint: "set:production:103c" }, pagination: "COMPLETE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_VERIFICATION_BATCHES_PAGE", method: "GET", selectors: { contextId: "release-chain" }, pagination: "COMPLETE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_VERIFICATION_BATCH_DETAIL", method: "GET", selectors: { contextId: "release-chain", objectFingerprint: "verification:brake-v3:13f8" }, pagination: "SINGLE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_FLEET_VALIDATION_BATCHES_PAGE", method: "GET", selectors: { contextId: "release-chain" }, pagination: "COMPLETE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_FLEET_VALIDATION_BATCH_DETAIL", method: "GET", selectors: { contextId: "release-chain", objectFingerprint: "fleet-validation:brake-v2:b827" }, pagination: "SINGLE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_CAMPAIGNS_PAGE", method: "GET", selectors: { contextId: "release-chain" }, pagination: "COMPLETE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_CAMPAIGN_DETAIL", method: "GET", selectors: { contextId: "release-chain", objectFingerprint: "campaign:brake-v2:27a1" }, pagination: "SINGLE" },
  { source: "AOSCLOUD_OEM", routeId: "OEM_UNIT_LOGS_PAGE", method: "GET", selectors: { contextId: "unit-log-metadata" }, pagination: "COMPLETE" },
  ...Array.from({ length: 7 }, (_, index): ReadRequest => ({
    source: "AOSCLOUD_OEM",
    routeId: "OEM_UNIT_LOG_DETAIL",
    method: "GET",
    selectors: { contextId: "unit-log-metadata", objectFingerprint: `unit-log:${index + 1}:c0de` },
    pagination: "SINGLE",
  })),
  { source: "AOSCLOUD_BRAKE_SP1", routeId: "BRAKE_USERS_ME", method: "GET", selectors: { contextId: "brake-session" }, pagination: "SINGLE" },
  { source: "AOSCLOUD_BRAKE_SP1", routeId: "BRAKE_SERVICE_LOGS_PAGE", method: "GET", selectors: { contextId: "brake-service-log-metadata" }, pagination: "COMPLETE" },
  { source: "AOSCLOUD_BRAKE_SP1", routeId: "BRAKE_SERVICE_LOG_DETAIL", method: "GET", selectors: { contextId: "brake-service-log-metadata", objectFingerprint: "service-log:1:ad24" }, pagination: "SINGLE" },
];

export function requiredReadPlansForContext(
  role: AudienceVehicleRole | null,
  systemUidFingerprint: string | null,
): readonly ReadRequest[] {
  const plans: ReadRequest[] = [...structuredClone(cloudReadPlans)];
  if (role && systemUidFingerprint) {
    const contextId = role === "TEST" ? "current-test-unit" : "current-production-unit";
    for (const routeId of BRAKE_BACKEND_ROUTE_IDS) {
      plans.push({
        source: "BRAKE_BACKEND",
        routeId,
        method: "GET",
        selectors: { contextId, objectFingerprint: systemUidFingerprint },
        pagination: "COMPLETE",
      });
    }
  }
  return plans;
}

export function validateReadRequest(input: unknown): ReadRequest {
  if (!input || typeof input !== "object" || Array.isArray(input)) throw new Error("READ_PLAN_MALFORMED");
  const value = input as Record<string, unknown>;
  if (Object.keys(value).some((key) => !requestKeys.has(key))) throw new Error("READ_PLAN_FIELD_FORBIDDEN");
  if (value.method !== "GET") throw new Error("READ_METHOD_FORBIDDEN");
  if (value.source !== "AOSCLOUD_OEM" && value.source !== "AOSCLOUD_BRAKE_SP1" && value.source !== "BRAKE_BACKEND") {
    throw new Error("READ_SOURCE_FORBIDDEN");
  }
  if (typeof value.routeId !== "string" || !sourceRoutes[value.source].has(value.routeId)) throw new Error("READ_ROUTE_FORBIDDEN");
  if (value.pagination !== "SINGLE" && value.pagination !== "COMPLETE") throw new Error("READ_PAGINATION_REQUIRED");
  if (!value.selectors || typeof value.selectors !== "object" || Array.isArray(value.selectors)) throw new Error("READ_SELECTOR_REQUIRED");
  const selectors = value.selectors as Record<string, unknown>;
  if (Object.keys(selectors).some((key) => !selectorKeys.has(key))) throw new Error("READ_SELECTOR_FORBIDDEN");
  if (typeof selectors.contextId !== "string" || !selectors.contextId) throw new Error("READ_CONTEXT_REQUIRED");
  if (!/^[a-z][a-z0-9-]{1,63}$/.test(selectors.contextId)) throw new Error("READ_CONTEXT_MALFORMED");
  const objectFingerprint = selectors.objectFingerprint;
  const cursor = selectors.cursor;
  if (objectFingerprint !== undefined && (typeof objectFingerprint !== "string" || !/^[a-z][a-z0-9-]*(?::[a-z0-9-]+){1,4}:[0-9a-f]{4}$/.test(objectFingerprint))) throw new Error("READ_SELECTOR_MALFORMED");
  if (cursor !== undefined && (typeof cursor !== "string" || !/^[A-Za-z0-9_-]{1,2048}$/.test(cursor))) throw new Error("READ_SELECTOR_MALFORMED");
  if (objectSelectedRoutes.has(value.routeId as string) && objectFingerprint === undefined) throw new Error("READ_SELECTOR_REQUIRED");
  if (value.pagination !== (completeRoutes.has(value.routeId as string) ? "COMPLETE" : "SINGLE")) throw new Error("READ_PAGINATION_MISMATCH");
  return input as ReadRequest;
}

export type FixtureOutcome = "OK" | "400" | "401" | "403" | "404" | "422" | "SOURCE_UNAVAILABLE" | "MALFORMED" | "REDACTED";
export type FixtureFreshness = "CURRENT" | "STALE";

export interface ContractRecord<T> {
  contractClass: "CONTRACT_SYNTHETIC";
  source: "AOSCLOUD_OEM" | "AOSCLOUD_BRAKE_SP1" | "BRAKE_BACKEND";
  outcome: FixtureOutcome;
  freshness: FixtureFreshness;
  sourceTimestamp: string | null;
  reasonCode?: string;
  value: T | null;
}

export interface UnitSetPage {
  role: AudienceVehicleRole;
  page: number;
  hasNext: boolean;
  cursor: string | null;
  nextCursor: string | null;
  members: readonly string[];
}

export interface AosCloudFixtureRecords {
  session: ContractRecord<SessionView>;
  brakeSession: ContractRecord<SessionView>;
  bindings: ContractRecord<readonly VehicleBindingView[]>;
  units: ContractRecord<readonly UnitView[]>;
  unitSets: ContractRecord<readonly UnitSetView[]>;
  unitSetPages: readonly UnitSetPage[];
  releases: ContractRecord<readonly ReleaseObjectView[]>;
  unitLogs: ContractRecord<readonly NativeLogView[]>;
  serviceLogs: ContractRecord<readonly NativeLogView[]>;
}

export interface BrakeFixtureRecords {
  contextRole: AudienceVehicleRole | null;
  contextSystemUidFingerprint: string | null;
  resources: ContractRecord<readonly BrakeResourceView[]>;
  notificationCount: number;
  restReadCount: number;
}

export interface ReadOnlyFixturePackage {
  fixtureId: string;
  contractClass: "CONTRACT_SYNTHETIC";
  policyId: "FIXTURE_POLICY_EXPLICIT_V1";
  phase: "PRE_M1" | "MANAGED";
  plans: readonly ReadRequest[];
  aosCloud: AosCloudFixtureRecords;
  brake: BrakeFixtureRecords;
}

function exactObjectKeys(value: unknown, keys: readonly string[]): value is Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  return Object.keys(value).length === keys.length
    && Object.keys(value).every((key) => keys.includes(key))
    && keys.every((key) => Object.hasOwn(value, key));
}

export function validateReadOnlyFixturePackageEnvelope(input: unknown): ReadOnlyFixturePackage {
  if (!exactObjectKeys(input, ["fixtureId", "contractClass", "policyId", "phase", "plans", "aosCloud", "brake"])) throw new Error("FIXTURE_PACKAGE_MALFORMED");
  if (typeof input.fixtureId !== "string" || !/^[a-z0-9][a-z0-9-]{0,95}$/.test(input.fixtureId)) throw new Error("FIXTURE_ID_MALFORMED");
  if (input.contractClass !== "CONTRACT_SYNTHETIC" || input.policyId !== "FIXTURE_POLICY_EXPLICIT_V1") throw new Error("FIXTURE_PROVENANCE_REQUIRED");
  if (input.phase !== "PRE_M1" && input.phase !== "MANAGED") throw new Error("FIXTURE_PHASE_MALFORMED");
  if (!exactObjectKeys(input.aosCloud, ["session", "brakeSession", "bindings", "units", "unitSets", "unitSetPages", "releases", "unitLogs", "serviceLogs"])) throw new Error("AOSCLOUD_FIXTURE_MALFORMED");
  if (!exactObjectKeys(input.brake, ["contextRole", "contextSystemUidFingerprint", "resources", "notificationCount", "restReadCount"])) throw new Error("BRAKE_FIXTURE_MALFORMED");
  const contextPairIsValid = input.brake.contextRole === null
    ? input.brake.contextSystemUidFingerprint === null
    : (input.brake.contextRole === "TEST" || input.brake.contextRole === "PRODUCTION")
      && typeof input.brake.contextSystemUidFingerprint === "string"
      && /^uid:(?:test|production):[0-9a-f]{4}$/.test(input.brake.contextSystemUidFingerprint);
  if (!contextPairIsValid) throw new Error("CURRENT_UNIT_CONTEXT_MALFORMED");
  if (!Array.isArray(input.plans) || input.plans.length === 0) throw new Error("READ_PLAN_REQUIRED");
  const plans = input.plans.map(validateReadRequest);
  const planKeys = plans.map((plan) => JSON.stringify(plan));
  if (new Set(planKeys).size !== plans.length) throw new Error("READ_PLAN_DUPLICATE");
  const expectedKeys = new Set(requiredReadPlansForContext(
    input.brake.contextRole as AudienceVehicleRole | null,
    input.brake.contextSystemUidFingerprint as string | null,
  ).map((plan) => JSON.stringify(plan)));
  if (planKeys.some((key) => !expectedKeys.has(key))) throw new Error("READ_PLAN_UNEXPECTED");
  if (planKeys.length !== expectedKeys.size || [...expectedKeys].some((key) => !planKeys.includes(key))) throw new Error("READ_PLAN_INCOMPLETE");
  if (!Number.isInteger(input.brake.notificationCount) || Number(input.brake.notificationCount) < 0
    || !Number.isInteger(input.brake.restReadCount) || Number(input.brake.restReadCount) < 0) throw new Error("BRAKE_REREAD_COUNT_MALFORMED");
  return input as unknown as ReadOnlyFixturePackage;
}
