import type { Clock, ObservationState, PresenterSnapshot, ReadObservation } from "../../domain";
import type { ReadOnlyFixturePackage } from "./contracts";
import { aosCloudReadModel } from "./aosCloudReadModel";
import { brakeCloudReadModel } from "./brakeCloudReadModel";

function deepFreeze<T>(value: T): Readonly<T> {
  if (value && typeof value === "object" && !Object.isFrozen(value)) {
    Object.freeze(value);
    Object.values(value).forEach((entry) => deepFreeze(entry));
  }
  return value;
}

function sourceState(observation: ReadObservation<unknown>): ObservationState {
  return observation.state;
}

function sourceReason(observation: ReadObservation<unknown>): string | undefined {
  return observation.reason ?? (observation.state === "CURRENT" ? undefined : "Current state cannot be confirmed");
}

export function composePresenterSnapshot(
  base: Readonly<PresenterSnapshot>,
  fixture: ReadOnlyFixturePackage,
  clock: Clock,
): Readonly<PresenterSnapshot> {
  const snapshot = structuredClone(base) as PresenterSnapshot;
  const cloud = aosCloudReadModel(fixture, clock);
  const brake = brakeCloudReadModel(fixture, clock);
  snapshot.fixtureId = fixture.fixtureId;
  snapshot.fixtureLabel = `${base.fixtureLabel} · CONTRACT_SYNTHETIC read projection`;
  snapshot.readOnly = {
    contractClass: "CONTRACT_SYNTHETIC",
    ...cloud,
    ...brake,
  };

  const platformReason = cloud.units.state === "STALE" && base.teams.platform.source.state === "STALE"
    ? base.teams.platform.source.reason
    : sourceReason(cloud.units);

  snapshot.teams.platform.source = {
    value: cloud.units.value ? "AosCloud Unit reported state" : null,
    source: { owner: "AosCloud OEM", system: "Contract-synthetic read adapter", fixture: true },
    observedAt: cloud.units.sourceTimestamp,
    state: sourceState(cloud.units),
    ...(platformReason ? { reason: platformReason } : {}),
  };
  snapshot.teams.platform.logs = cloud.unitLogs;
  snapshot.teams.brake.source = {
    value: brake.brake.value ? "Brake Backend current-Unit projection" : null,
    source: { owner: "Brake Function Backend", system: "Contract-synthetic read adapter", fixture: true },
    observedAt: brake.brake.sourceTimestamp,
    state: sourceState(brake.brake),
    ...(sourceReason(brake.brake) ? { reason: sourceReason(brake.brake) } : {}),
  };
  snapshot.teams.brake.logs = cloud.serviceLogs;
  snapshot.teams.brake.brakeResources = brake.brake;

  const selectedRole = base.vehicle.value === "production" ? "PRODUCTION" : "TEST";
  const currentUnit = cloud.units.value?.find((item) => item.role === selectedRole);
  const currentBinding = cloud.bindings.value?.find((item) => item.role === selectedRole);
  const managedFactsCurrent = [cloud.session, cloud.bindings, cloud.units, cloud.unitSets].every((item) => item.state === "CURRENT");
  if (fixture.phase === "PRE_M1") {
    snapshot.vehicle = {
      value: "not-assigned",
      source: { owner: "AosCloud OEM", system: "Contract-synthetic read adapter", fixture: true },
      observedAt: cloud.units.sourceTimestamp,
      state: "NOT_APPLICABLE",
      reason: "NO_UNIT_BEFORE_M1",
    };
  } else if (base.vehicle.value === "changing") {
    snapshot.vehicle = structuredClone(base.vehicle);
  } else if (!managedFactsCurrent || !currentUnit || !currentBinding) {
    const limiting = [cloud.session, cloud.bindings, cloud.units, cloud.unitSets].find((item) => item.state !== "CURRENT") ?? cloud.units;
    if (!(limiting.state === "STALE" && base.teams.platform.source.state === "STALE")) {
      snapshot.teams.platform.compactStatus = `${limiting.state} · Cloud read`;
      snapshot.teams.platform.lifecycleStatus = "Current AosCloud lifecycle cannot be confirmed";
    }
    snapshot.vehicle = {
      value: "unavailable",
      source: { owner: "AosCloud OEM", system: "Contract-synthetic read adapter", fixture: true },
      observedAt: limiting.sourceTimestamp,
      state: sourceState(limiting),
      reason: sourceReason(limiting) ?? "CURRENT_UNIT_NOT_CONFIRMED",
    };
  } else {
    snapshot.vehicle = {
      value: currentBinding.role === "PRODUCTION" ? "production" : "test",
      source: { owner: "AosCloud OEM", system: "Contract-synthetic read adapter", fixture: true },
      observedAt: cloud.units.sourceTimestamp,
      state: "CURRENT",
    };
  }

  snapshot.teams.brake.compactStatus = brake.brake.state === "CURRENT"
    ? "Current Unit · Brake read"
    : `${brake.brake.state} · Brake read`;

  if (currentUnit && cloud.units.state === "CURRENT") {
    snapshot.teams.platform.productStatus = currentUnit.actualSoftware.find((item) => item.startsWith("VDP ")) ?? "VDP v—";
    snapshot.teams.brake.productStatus = currentUnit.actualSoftware.find((item) => item.startsWith("Brake ")) ?? "Service v—";
  } else {
    snapshot.teams.platform.productStatus = "VDP v—";
    snapshot.teams.brake.productStatus = "Service v—";
  }

  if (brake.brake.state === "CURRENT") {
    const total = brake.brake.value?.reduce((count, item) => count + item.count, 0) ?? 0;
    snapshot.teams.brake.backendStatus = total === 0 ? "Current Unit · no Brake data" : `Current Unit · ${total} Brake records`;
    snapshot.teams.brake.evidenceBody = total === 0
      ? "The current Unit query completed successfully with an empty page. Empty is factual and does not imply Unit failure."
      : `${base.teams.brake.evidenceBody} Brake windows, assessments, events and advisories were reread for the exact Current Unit. Backend state does not define AosCloud Unit readiness.`;
  } else {
    snapshot.teams.brake.backendStatus = `${brake.brake.state} · ${brake.brake.transport}`;
    snapshot.teams.brake.evidenceBody = brake.brake.reason ?? "Current Brake state cannot be confirmed.";
  }

  return deepFreeze(snapshot);
}
