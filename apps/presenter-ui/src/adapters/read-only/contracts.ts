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
  record: unknown;
}

const sourceRoutes = {
  AOSCLOUD_OEM: new Set<string>(OEM_ROUTE_IDS),
  AOSCLOUD_BRAKE_SP1: new Set<string>(BRAKE_SP1_ROUTE_IDS),
  BRAKE_BACKEND: new Set<string>(BRAKE_BACKEND_ROUTE_IDS),
} as const;

const requestKeys = new Set(["source", "routeId", "method", "selectors", "pagination"]);
const selectorKeys = new Set(["contextId", "objectFingerprint", "cursor"]);

const detailRoutes = new Set<string>([
  "OEM_UNIT_DETAIL",
  "OEM_NODE_DETAIL",
  "OEM_UNIT_SET_DETAIL",
  "OEM_VERIFICATION_BATCH_DETAIL",
  "OEM_FLEET_VALIDATION_BATCH_DETAIL",
  "OEM_CAMPAIGN_DETAIL",
  "OEM_UNIT_LOG_DETAIL",
  "BRAKE_SERVICE_LOG_DETAIL",
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

const requiredRouteCounts = new Map<string, number>([
  ...OEM_ROUTE_IDS.map((routeId) => [routeId, 1] as const),
  ...BRAKE_SP1_ROUTE_IDS.map((routeId) => [routeId, 1] as const),
  ...BRAKE_BACKEND_ROUTE_IDS.map((routeId) => [routeId, 1] as const),
  ["OEM_UNIT_DETAIL", 2],
  ["OEM_NODE_DETAIL", 2],
  ["OEM_UNIT_SET_DETAIL", 2],
]);

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
  if (detailRoutes.has(value.routeId as string) && objectFingerprint === undefined) throw new Error("READ_SELECTOR_REQUIRED");
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
  if (!Array.isArray(input.plans) || input.plans.length === 0) throw new Error("READ_PLAN_REQUIRED");
  const plans = input.plans.map(validateReadRequest);
  if (new Set(plans.map((plan) => JSON.stringify(plan))).size !== plans.length) throw new Error("READ_PLAN_DUPLICATE");
  for (const [routeId, count] of requiredRouteCounts) {
    if (plans.filter((plan) => plan.routeId === routeId).length < count) throw new Error("READ_PLAN_INCOMPLETE");
  }
  if (!exactObjectKeys(input.aosCloud, ["session", "brakeSession", "bindings", "units", "unitSets", "unitSetPages", "releases", "unitLogs", "serviceLogs"])) throw new Error("AOSCLOUD_FIXTURE_MALFORMED");
  if (!exactObjectKeys(input.brake, ["contextRole", "contextSystemUidFingerprint", "resources", "notificationCount", "restReadCount"])) throw new Error("BRAKE_FIXTURE_MALFORMED");
  const contextPairIsValid = input.brake.contextRole === null
    ? input.brake.contextSystemUidFingerprint === null
    : (input.brake.contextRole === "TEST" || input.brake.contextRole === "PRODUCTION")
      && typeof input.brake.contextSystemUidFingerprint === "string"
      && /^uid:(?:test|production):[0-9a-f]{4}$/.test(input.brake.contextSystemUidFingerprint);
  if (!contextPairIsValid) throw new Error("CURRENT_UNIT_CONTEXT_MALFORMED");
  if (!Number.isInteger(input.brake.notificationCount) || Number(input.brake.notificationCount) < 0
    || !Number.isInteger(input.brake.restReadCount) || Number(input.brake.restReadCount) < 0) throw new Error("BRAKE_REREAD_COUNT_MALFORMED");
  return input as unknown as ReadOnlyFixturePackage;
}
