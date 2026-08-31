import type {
  BrakeResourceView,
  Clock,
  NativeLogView,
  PresenterReadPort,
  PresenterSnapshot,
  ReleaseObjectView,
  SessionView,
  UnitSetView,
  UnitView,
  VehicleBindingView,
} from "../../domain";
import { isAcceptedDateTime } from "./aosCloudReadModel";
import { composePresenterSnapshot } from "./composePresenterSnapshot";
import {
  type PlannedFixtureRead,
  type ContractRecord,
  type ReadOnlyFixturePackage,
  type ReadRequest,
  type ReadRouteContext,
  type UnitSetPage,
  validateReadOnlyFixturePackageEnvelope,
  validateReadRequest,
} from "./contracts";
import { readOnlyFixtureById } from "./fixtureCatalog";

const routeContexts = {
  AOSCLOUD_OEM: Object.freeze({ routeContext: "oem-delivery-read", role: "OEM" }),
  AOSCLOUD_BRAKE_SP1: Object.freeze({ routeContext: "brake-sp1-read", role: "Service Provider" }),
  BRAKE_BACKEND: Object.freeze({ routeContext: "brake-backend-read", role: "Current Unit" }),
} as const satisfies Record<ReadRequest["source"], ReadRouteContext>;

function deepFreeze<T>(value: T): Readonly<T> {
  if (value && typeof value === "object" && !Object.isFrozen(value)) {
    Object.freeze(value);
    Object.values(value).forEach((entry) => deepFreeze(entry));
  }
  return value;
}

function sameContext(actual: ReadRouteContext, expected: ReadRouteContext): boolean {
  return actual.routeContext === expected.routeContext && actual.role === expected.role;
}

function selectMany<T>(record: ContractRecord<readonly T[]>, predicate: (item: T) => boolean): ContractRecord<readonly T[]> {
  if (record.outcome !== "OK" || record.value === null) return record;
  return { ...record, value: record.value.filter(predicate) };
}

function selectOne<T>(record: ContractRecord<readonly T[]>, predicate: (item: T) => boolean): ContractRecord<T> {
  if (record.outcome !== "OK" || record.value === null) return record as unknown as ContractRecord<T>;
  const value = record.value.find(predicate);
  if (value === undefined) {
    return { ...record, outcome: "404", value: null, reasonCode: "FIXTURE_OBJECT_NOT_FOUND" };
  }
  return { ...record, value };
}

function recordForPlan(fixture: ReadOnlyFixturePackage, plan: ReadRequest): ContractRecord<unknown> {
  const objectFingerprint = plan.selectors.objectFingerprint;
  switch (plan.routeId) {
    case "OEM_USERS_ME":
      return fixture.aosCloud.session;
    case "OEM_UNITS_PAGE":
      return fixture.aosCloud.units;
    case "OEM_UNIT_DETAIL":
      return selectOne(fixture.aosCloud.units, (unit) => unit.unitFingerprint === objectFingerprint);
    case "OEM_UNIT_NODES_PAGE":
      return selectMany(fixture.aosCloud.bindings, (binding) => binding.unitFingerprint === objectFingerprint);
    case "OEM_NODE_DETAIL":
      return selectOne(fixture.aosCloud.bindings, (binding) => binding.mainNodeFingerprint === objectFingerprint);
    case "OEM_SUBJECT_SERVICES_PAGE":
      return selectMany(fixture.aosCloud.units, (unit) => unit.unitFingerprint === objectFingerprint);
    case "OEM_UNIT_SETS_PAGE":
      return fixture.aosCloud.unitSets;
    case "OEM_UNIT_SET_DETAIL": {
      const binding = fixture.aosCloud.bindings.value?.find((item) => item.unitSetFingerprint === objectFingerprint);
      return selectOne(fixture.aosCloud.unitSets, (unitSet) => unitSet.role === binding?.role);
    }
    case "OEM_UNIT_SET_MEMBERS_PAGE": {
      if (fixture.aosCloud.unitSets.outcome !== "OK") return fixture.aosCloud.unitSets;
      const binding = fixture.aosCloud.bindings.value?.find((item) => item.unitSetFingerprint === objectFingerprint);
      if (!binding) return { ...fixture.aosCloud.unitSets, outcome: "404", value: null, reasonCode: "FIXTURE_OBJECT_NOT_FOUND" };
      return { ...fixture.aosCloud.unitSets, value: fixture.aosCloud.unitSetPages.filter((page) => page.role === binding.role) };
    }
    case "OEM_VERIFICATION_BATCHES_PAGE":
      return selectMany(fixture.aosCloud.releases, (release) => release.kind === "CANDIDATE" || release.kind === "VERIFICATION_BATCH");
    case "OEM_VERIFICATION_BATCH_DETAIL":
      return selectOne(fixture.aosCloud.releases, (release) => release.kind === "VERIFICATION_BATCH" && release.fingerprint === objectFingerprint);
    case "OEM_FLEET_VALIDATION_BATCHES_PAGE":
      return selectMany(fixture.aosCloud.releases, (release) => release.kind === "FLEET_VALIDATION_BATCH");
    case "OEM_FLEET_VALIDATION_BATCH_DETAIL":
      return selectOne(fixture.aosCloud.releases, (release) => release.kind === "FLEET_VALIDATION_BATCH" && release.fingerprint === objectFingerprint);
    case "OEM_CAMPAIGNS_PAGE":
      return selectMany(fixture.aosCloud.releases, (release) => release.kind === "CAMPAIGN");
    case "OEM_CAMPAIGN_DETAIL":
      return selectOne(fixture.aosCloud.releases, (release) => release.kind === "CAMPAIGN" && release.fingerprint === objectFingerprint);
    case "OEM_UNIT_LOGS_PAGE":
      return fixture.aosCloud.unitLogs;
    case "OEM_UNIT_LOG_DETAIL":
      return selectOne(fixture.aosCloud.unitLogs, (log) => log.requestFingerprint === objectFingerprint);
    case "BRAKE_USERS_ME":
      return fixture.aosCloud.brakeSession;
    case "BRAKE_SERVICE_LOGS_PAGE":
      return fixture.aosCloud.serviceLogs;
    case "BRAKE_SERVICE_LOG_DETAIL":
      return selectOne(fixture.aosCloud.serviceLogs, (log) => log.requestFingerprint === objectFingerprint);
    case "BRAKE_WINDOWS":
      return selectMany(fixture.brake.resources, (resource) => resource.resourceType === "WINDOW" && resource.unitSystemUidFingerprint === objectFingerprint);
    case "BRAKE_ASSESSMENTS":
      return selectMany(fixture.brake.resources, (resource) => resource.resourceType === "ASSESSMENT" && resource.unitSystemUidFingerprint === objectFingerprint);
    case "BRAKE_EVENTS":
      return selectMany(fixture.brake.resources, (resource) => resource.resourceType === "EVENT" && resource.unitSystemUidFingerprint === objectFingerprint);
    case "BRAKE_ADVISORIES":
      return selectMany(fixture.brake.resources, (resource) => resource.resourceType === "ADVISORY" && resource.unitSystemUidFingerprint === objectFingerprint);
  }
}

function readsFor(reads: readonly Readonly<PlannedFixtureRead>[], ...routeIds: ReadRequest["routeId"][]): readonly Readonly<PlannedFixtureRead>[] {
  return reads.filter((read) => routeIds.includes(read.plan.routeId));
}

function singleRecord<T>(reads: readonly Readonly<PlannedFixtureRead>[], routeId: ReadRequest["routeId"]): ContractRecord<T> {
  const selected = readsFor(reads, routeId);
  if (selected.length !== 1) throw new Error("READ_EXECUTION_CARDINALITY_MISMATCH");
  return structuredClone(selected[0]!.record) as ContractRecord<T>;
}

function aggregateRecords<T>(
  gateReads: readonly Readonly<PlannedFixtureRead>[],
  valueReads: readonly Readonly<PlannedFixtureRead>[],
): ContractRecord<readonly T[]> {
  if (gateReads.length === 0 || valueReads.length === 0) throw new Error("READ_EXECUTION_CARDINALITY_MISMATCH");
  const first = gateReads[0]!.record;
  const source = gateReads[0]!.plan.source;
  if (gateReads.some((read) => read.plan.source !== source || read.record.source !== source)) throw new Error("READ_EXECUTION_SCOPE_MISMATCH");
  const failed = gateReads.find((read) => read.record.outcome !== "OK");
  if (failed) return { ...structuredClone(failed.record), value: null } as ContractRecord<readonly T[]>;
  const values: T[] = [];
  for (const read of valueReads) {
    if (read.record.outcome !== "OK" || read.record.value === null) {
      return { ...structuredClone(read.record), value: null } as ContractRecord<readonly T[]>;
    }
    if (Array.isArray(read.record.value)) values.push(...structuredClone(read.record.value) as T[]);
    else values.push(structuredClone(read.record.value) as T);
  }
  return {
    ...structuredClone(first),
    freshness: gateReads.some((read) => read.record.freshness === "STALE") ? "STALE" : "CURRENT",
    value: values,
  } as ContractRecord<readonly T[]>;
}

function materializeExecutedFixture(
  fixture: ReadOnlyFixturePackage,
  reads: readonly Readonly<PlannedFixtureRead>[],
): ReadOnlyFixturePackage {
  const unitReads = readsFor(reads, "OEM_UNITS_PAGE", "OEM_UNIT_DETAIL", "OEM_SUBJECT_SERVICES_PAGE");
  const nodeReads = readsFor(reads, "OEM_UNIT_NODES_PAGE", "OEM_NODE_DETAIL");
  const unitSetReads = readsFor(reads, "OEM_UNIT_SETS_PAGE", "OEM_UNIT_SET_DETAIL", "OEM_UNIT_SET_MEMBERS_PAGE");
  const membershipReads = readsFor(reads, "OEM_UNIT_SET_MEMBERS_PAGE");
  const releaseReads = readsFor(
    reads,
    "OEM_VERIFICATION_BATCHES_PAGE",
    "OEM_VERIFICATION_BATCH_DETAIL",
    "OEM_FLEET_VALIDATION_BATCHES_PAGE",
    "OEM_FLEET_VALIDATION_BATCH_DETAIL",
    "OEM_CAMPAIGNS_PAGE",
    "OEM_CAMPAIGN_DETAIL",
  );
  const releasePageReads = readsFor(reads, "OEM_VERIFICATION_BATCHES_PAGE", "OEM_FLEET_VALIDATION_BATCHES_PAGE", "OEM_CAMPAIGNS_PAGE");
  const unitLogReads = readsFor(reads, "OEM_UNIT_LOGS_PAGE", "OEM_UNIT_LOG_DETAIL");
  const serviceLogReads = readsFor(reads, "BRAKE_SERVICE_LOGS_PAGE", "BRAKE_SERVICE_LOG_DETAIL");
  const brakeReads = readsFor(reads, ...["BRAKE_WINDOWS", "BRAKE_ASSESSMENTS", "BRAKE_EVENTS", "BRAKE_ADVISORIES"] as const);
  const unitSets = aggregateRecords<UnitSetView>(unitSetReads, readsFor(reads, "OEM_UNIT_SET_DETAIL"));
  const materialized: ReadOnlyFixturePackage = {
    fixtureId: fixture.fixtureId,
    contractClass: fixture.contractClass,
    policyId: fixture.policyId,
    phase: fixture.phase,
    plans: structuredClone(fixture.plans),
    aosCloud: {
      session: singleRecord<SessionView>(reads, "OEM_USERS_ME"),
      brakeSession: singleRecord<SessionView>(reads, "BRAKE_USERS_ME"),
      bindings: aggregateRecords<VehicleBindingView>(nodeReads, readsFor(reads, "OEM_NODE_DETAIL")),
      units: aggregateRecords<UnitView>(unitReads, readsFor(reads, "OEM_UNIT_DETAIL")),
      unitSets,
      unitSetPages: unitSets.outcome === "OK"
        ? aggregateRecords<UnitSetPage>(membershipReads, membershipReads).value ?? []
        : [],
      releases: aggregateRecords<ReleaseObjectView>(releaseReads, releasePageReads),
      unitLogs: aggregateRecords<NativeLogView>(unitLogReads, readsFor(reads, "OEM_UNIT_LOG_DETAIL")),
      serviceLogs: aggregateRecords<NativeLogView>(serviceLogReads, readsFor(reads, "BRAKE_SERVICE_LOG_DETAIL")),
    },
    brake: {
      contextRole: fixture.brake.contextRole,
      contextSystemUidFingerprint: fixture.brake.contextSystemUidFingerprint,
      resources: brakeReads.length > 0
        ? aggregateRecords<BrakeResourceView>(brakeReads, brakeReads)
        : {
          contractClass: "CONTRACT_SYNTHETIC",
          source: "BRAKE_BACKEND",
          outcome: "SOURCE_UNAVAILABLE",
          freshness: "CURRENT",
          sourceTimestamp: null,
          reasonCode: "CURRENT_UNIT_CONTEXT_UNAVAILABLE",
          value: null,
        },
      notificationCount: fixture.brake.notificationCount,
      restReadCount: fixture.brake.restReadCount,
    },
  };
  return validateReadOnlyFixturePackageEnvelope(materialized);
}

export class FixtureReadOnlyAdapter implements PresenterReadPort {
  readonly #base: PresenterReadPort;
  readonly #fixtureId: string;
  readonly #clock: Clock;

  constructor(base: PresenterReadPort, fixtureId: string, clock: Clock) {
    this.#base = base;
    this.#fixtureId = fixtureId;
    this.#clock = clock;
    this.#validatedPackage();
  }

  #validatedPackage(): ReadOnlyFixturePackage {
    const fixture = readOnlyFixtureById(this.#fixtureId);
    return validateReadOnlyFixturePackageEnvelope(fixture);
  }

  #readPlan(planInput: ReadRequest, context: ReadRouteContext, clock: Clock, fixture: ReadOnlyFixturePackage): Readonly<PlannedFixtureRead> {
    const plan = validateReadRequest(planInput);
    if (!fixture.plans.some((candidate) => JSON.stringify(candidate) === JSON.stringify(plan))) throw new Error("READ_PLAN_NOT_DECLARED");
    if (!sameContext(context, routeContexts[plan.source])) throw new Error("READ_CONTEXT_SCOPE_MISMATCH");
    const readCompletedAt = clock();
    if (!isAcceptedDateTime(readCompletedAt)) throw new Error("FIXTURE_CLOCK_MALFORMED");
    return deepFreeze({
      plan: structuredClone(plan),
      context: structuredClone(context),
      readCompletedAt,
      record: structuredClone(recordForPlan(fixture, plan)),
    });
  }

  #executeDeclaredPlans(fixture: ReadOnlyFixturePackage, clock: Clock): readonly Readonly<PlannedFixtureRead>[] {
    const reads = fixture.plans.map((plan) => this.#readPlan(plan, routeContexts[plan.source], clock, fixture));
    for (const [index, read] of reads.entries()) {
      const record = read.record as { source?: unknown } | null;
      if (JSON.stringify(read.plan) !== JSON.stringify(fixture.plans[index])
        || !record
        || typeof record !== "object"
        || record.source !== read.plan.source) throw new Error("READ_EXECUTION_SCOPE_MISMATCH");
    }
    return reads;
  }

  read(): Promise<Readonly<PresenterSnapshot>>;
  read(plan: ReadRequest, context: ReadRouteContext, clock: Clock): Readonly<PlannedFixtureRead>;
  read(plan?: ReadRequest, context?: ReadRouteContext, clock?: Clock): Promise<Readonly<PresenterSnapshot>> | Readonly<PlannedFixtureRead> {
    const fixture = this.#validatedPackage();
    if (plan || context || clock) {
      if (!plan || !context || !clock) throw new Error("READ_INVOCATION_INCOMPLETE");
      return this.#readPlan(plan, context, clock, fixture);
    }
    const executedFixture = materializeExecutedFixture(fixture, this.#executeDeclaredPlans(fixture, this.#clock));
    return this.#base.read().then((base) => composePresenterSnapshot(base, executedFixture, this.#clock));
  }

  subscribe(listener: (snapshot: Readonly<PresenterSnapshot>) => void): () => void {
    return this.#base.subscribe((base) => {
      const fixture = this.#validatedPackage();
      const executedFixture = materializeExecutedFixture(fixture, this.#executeDeclaredPlans(fixture, this.#clock));
      listener(composePresenterSnapshot(base, executedFixture, this.#clock));
    });
  }
}
