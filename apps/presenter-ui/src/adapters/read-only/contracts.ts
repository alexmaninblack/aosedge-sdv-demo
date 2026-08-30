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

const sourceRoutes = {
  AOSCLOUD_OEM: new Set<string>(OEM_ROUTE_IDS),
  AOSCLOUD_BRAKE_SP1: new Set<string>(BRAKE_SP1_ROUTE_IDS),
  BRAKE_BACKEND: new Set<string>(BRAKE_BACKEND_ROUTE_IDS),
} as const;

const requestKeys = new Set(["source", "routeId", "method", "selectors", "pagination"]);
const selectorKeys = new Set(["contextId", "objectFingerprint", "cursor"]);

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
  for (const key of ["objectFingerprint", "cursor"] as const) {
    if (selectors[key] !== undefined && typeof selectors[key] !== "string") throw new Error("READ_SELECTOR_MALFORMED");
  }
  return input as ReadRequest;
}

export type FixtureOutcome = "OK" | "400" | "401" | "403" | "404" | "422" | "SOURCE_UNAVAILABLE" | "MALFORMED";
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
