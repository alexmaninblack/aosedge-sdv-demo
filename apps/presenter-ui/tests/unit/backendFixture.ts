import type { BackendBinding, ResetCommand } from "../../src/features/service-team/backendSelection";
export const nativeInstance = { serviceId: "brake-id", subjectId: "brake-subject", instanceIndex: 0, instanceId: "native-brake" };
export const binding: BackendBinding = { unitSystemUid: "current-test", serviceId: nativeInstance.serviceId,
  subjectId: nativeInstance.subjectId, instanceIndex: 0, serviceVersion: "7.0.0", profile: "v3", current: true };
export function confirmedReset(scope = binding, issuedAt = "2026-09-11T22:00:00.000Z", clearAt = "2026-09-11T22:00:02.000Z"): ResetCommand {
  const serviceInstance = { ...nativeInstance, serviceId: scope.serviceId, subjectId: scope.subjectId, instanceIndex: scope.instanceIndex };
  const context = { schemaVersion: 1, unitSystemUid: scope.unitSystemUid, serviceVersion: scope.serviceVersion,
    serviceInstance, producerEpoch: "91d99efb-9f04-4bca-a8a5-e017c8026962" };
  const commandId = "dbb2cbbc-93b4-42e6-958a-ebad9911cacc";
  const requestId = "56502253-f84e-4fb6-8b31-62361f4f6e23";
  return { ...context, commandId, operation: "RESET_DEMO_SCENARIO", state: "CLEARED", issuedAt,
    expiresAt: new Date(Date.parse(issuedAt) + 60000).toISOString(), result: { ...context, commandId, result: "CLEARED",
      clearRequest: { schemaVersion: 1, requestId, producerEpoch: context.producerEpoch, sequence: 3, operation: "CLEAR",
        reasonCode: "CONDITION_CLEARED", decisionId: commandId, serviceVersion: scope.serviceVersion, modelVersion: "v3",
        issuedAt, expiresAt: new Date(Date.parse(issuedAt) + 30000).toISOString() },
      gatewayStatus: { schemaVersion: 1, requestId, producerEpoch: context.producerEpoch, sequence: 3, state: "CLEARED", reason: "NONE",
        gatewayObservedAt: clearAt, activeRecommendation: "NONE", activeReasonCode: "NONE", activeUntil: null } } };
}
