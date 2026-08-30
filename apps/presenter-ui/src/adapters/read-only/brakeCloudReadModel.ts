import type { BrakeResourceView, Clock, ReadObservation } from "../../domain";
import { readObservation } from "../../domain";
import type { ReadOnlyFixturePackage } from "./contracts";
import { normalizeContractRecord } from "./aosCloudReadModel";

export interface BrakeReadProjection {
  brake: ReadObservation<readonly BrakeResourceView[]>;
  notificationRereads: number;
}

const resourceTypes = new Set(["windows", "assessments", "events", "advisories"]);

function invalid(observation: ReadObservation<readonly BrakeResourceView[]>, reason: string): ReadObservation<readonly BrakeResourceView[]> {
  return readObservation<readonly BrakeResourceView[]>({ ...observation, value: null, state: "INCOMPLETE", transport: "MALFORMED", reason });
}

export function brakeCloudReadModel(fixture: ReadOnlyFixturePackage, clock: Clock): BrakeReadProjection {
  let brake = normalizeContractRecord(fixture.brake.resources, clock, fixture.policyId);
  const role = fixture.brake.contextRole;

  if (fixture.phase === "PRE_M1") {
    brake = readObservation<readonly BrakeResourceView[]>({
      ...brake,
      value: null,
      state: "NOT_APPLICABLE",
      transport: "AVAILABLE",
      reason: "NO_CURRENT_UNIT_BEFORE_M1",
    });
  } else if (!role) {
    brake = readObservation<readonly BrakeResourceView[]>({
      ...brake,
      value: null,
      state: "UNKNOWN",
      transport: "SOURCE_UNAVAILABLE",
      reason: "CURRENT_UNIT_CONTEXT_UNAVAILABLE",
    });
  } else if (brake.state === "CURRENT" && brake.value) {
    const valid = brake.value.every((item) =>
      item.role === role
      && resourceTypes.has(item.resourceType)
      && item.count >= 0
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
