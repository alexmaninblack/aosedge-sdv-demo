import type { Clock, PresenterReadPort, PresenterSnapshot } from "../../domain";
import { isAcceptedDateTime } from "./aosCloudReadModel";
import { composePresenterSnapshot } from "./composePresenterSnapshot";
import {
  type PlannedFixtureRead,
  type ContractRecord,
  type ReadOnlyFixturePackage,
  type ReadRequest,
  type ReadRouteContext,
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

function recordForPlan(fixture: ReadOnlyFixturePackage, plan: ReadRequest): unknown {
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
      return fixture.aosCloud.units;
    case "OEM_UNIT_SETS_PAGE":
      return fixture.aosCloud.unitSets;
    case "OEM_UNIT_SET_DETAIL": {
      const binding = fixture.aosCloud.bindings.value?.find((item) => item.unitSetFingerprint === objectFingerprint);
      return selectOne(fixture.aosCloud.unitSets, (unitSet) => unitSet.role === binding?.role);
    }
    case "OEM_UNIT_SET_MEMBERS_PAGE":
      return fixture.aosCloud.unitSets.outcome === "OK"
        ? { ...fixture.aosCloud.unitSets, value: fixture.aosCloud.unitSetPages }
        : fixture.aosCloud.unitSets;
    case "OEM_VERIFICATION_BATCHES_PAGE":
      return selectMany(fixture.aosCloud.releases, (release) => release.kind === "VERIFICATION_BATCH");
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
      return selectMany(fixture.brake.resources, (resource) => resource.resourceType === "WINDOW");
    case "BRAKE_ASSESSMENTS":
      return selectMany(fixture.brake.resources, (resource) => resource.resourceType === "ASSESSMENT");
    case "BRAKE_EVENTS":
      return selectMany(fixture.brake.resources, (resource) => resource.resourceType === "EVENT");
    case "BRAKE_ADVISORIES":
      return selectMany(fixture.brake.resources, (resource) => resource.resourceType === "ADVISORY");
  }
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
    this.#executeDeclaredPlans(fixture, this.#clock);
    return this.#base.read().then((base) => composePresenterSnapshot(base, fixture, this.#clock));
  }

  subscribe(listener: (snapshot: Readonly<PresenterSnapshot>) => void): () => void {
    return this.#base.subscribe((base) => {
      const fixture = this.#validatedPackage();
      this.#executeDeclaredPlans(fixture, this.#clock);
      listener(composePresenterSnapshot(base, fixture, this.#clock));
    });
  }
}
