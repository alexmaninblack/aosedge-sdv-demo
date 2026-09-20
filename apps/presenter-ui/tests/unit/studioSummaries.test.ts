// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { expect, test } from "vitest";
import { backendSummary as summarize, type BackendModel } from "../../src/features/service-team/useBackendObservation";
import { binding, nativeInstance, confirmedReset } from "./backendFixture";
import { controllerMetric, type CloudResourcesModel } from "../../src/app/StudioReadViews";
const scope = { ...binding, unitSystemUid: "test-a", serviceVersion: "58.0.0" };
const backendSummary = (model: BackendModel, team: "brake" | "tire", version?: string) => summarize(model, team, version, scope);

function backend(version = "58.0.0", type = "BRAKE_HEALTH_ASSESSMENT"): BackendModel {
  return { busy: false, error: false, refresh() {}, data: { team: "brake", source: "REAL_BACKEND_HTTP", state: "OBSERVED", observedAt: "2026-09-17T20:00:00Z",
    observations: { demoReset: { state: "OBSERVED", data: { schemaVersion: 1, unitSystemUid: "test-a", connected: false, command: null } }, mockData: { state: "OBSERVED", data: { source: "VEHICLE_DATA", vehicleTelemetry: true, unitSystemUid: "test-a", counts: [{ count: 1 }], records: [{
      backendReceivedAt: "2026-09-17T20:00:00Z", deliveryState: "DURABLY_RECEIVED", message: { unitSystemUid: "test-a", serviceInstance: nativeInstance, serviceVersion: version, messageType: type, sourceEventTime: "2026-09-17T19:59:00Z", content: { currentBand: "INSPECTION_RECOMMENDED" } },
    }] } } } } };
}
test("summary proof belongs to the exact installed release, not previous version or function status", () => {
  expect(backendSummary(backend(), "brake", "58.0.0").proof).toBe("58.0.0");
  expect(backendSummary(backend("57.0.0"), "brake", "58.0.0").result).toBeUndefined();
  expect(backendSummary(backend("58.0.0", "TIRE_FUNCTION_STATUS"), "tire", "58.0.0").proof).toBeUndefined();
  expect(backendSummary(backend(), "brake").result).toBeUndefined();
});
test("unavailable or mock observations retain labelled data but cannot establish proof", () => {
  const model = backend(); model.error = true;
  expect(backendSummary(model, "brake", "58.0.0").proof).toBeUndefined();
  expect(backendSummary(model, "brake", "58.0.0").status).toBe("Last known / incomplete");
  model.error = false; model.data!.observations.mockData!.data!.source = "DEMO_MOCK";
  expect(backendSummary(model, "brake", "58.0.0").proof).toBeUndefined();
});
test("reset uses source time, not a late backend receipt; history stays intact", () => {
  const model = backend(); model.data!.observations.demoReset = { state: "OBSERVED", data: {
    schemaVersion: 1, unitSystemUid: "test-a", connected: true, command: confirmedReset(scope, "2026-09-17T19:59:30.000Z", "2026-09-17T19:59:32.000Z"),
  } };
  const result = backendSummary(model, "brake", "58.0.0");
  expect(result.result).toBeUndefined(); expect(result.proof).toBeUndefined(); expect(result.title).toBe("No new result after reset");
  expect(result.status).toBe("Input not confirmed"); expect(result.contact).toBe("Recent");
  expect(model.data!.observations.mockData!.data!.records).toHaveLength(1);
});
test("incomplete V1 windows do not complete the story; a durable COMPLETE window does", () => {
  const model = backend("58.0.0", "WINDOW_COMPLETION");
  const message = model.data!.observations.mockData!.data!.records[0]!.message;
  message.content = { status: "PARTIAL", receivedSampleCount: 20 };
  expect(backendSummary(model, "brake", "58.0.0").proof).toBeUndefined();
  message.content = { status: "COMPLETE", receivedSampleCount: 20 };
  expect(backendSummary(model, "brake", "58.0.0").proof).toBe("58.0.0");
});
test("backend contact and Reset cannot establish telemetry readiness or a product assessment", () => {
  const model = backend("58.0.0", "BRAKE_ADVISORY_FACT");
  model.data!.observations.demoReset = { state: "OBSERVED", data: { schemaVersion: 1, unitSystemUid: "test-a", connected: true, command: null } };
  const summary = backendSummary(model, "brake", "58.0.0");
  expect(summary.result).toBeUndefined(); expect(summary.contact).toBe("Recent");
  expect(summary.status).toBe("Input not confirmed");
  model.error = true; expect(backendSummary(model, "brake", "58.0.0").contact).toBe("Not observed");
});
test("resource summary preserves zero/units and never sums controller and service instances", () => {
  const model: CloudResourcesModel = { busy: false, error: false, reason: null, refresh() {}, data: { monitoring: { state: "CURRENT", value: {
    cpu: { state: "CURRENT", unit: "DMIPS", value: [{ nodeId: "node-a", value: 0, time: "2026-09-17T20:00:00Z" }, { nodeId: "node-a", serviceId: "brake", subjectId: "subject-a", instance: 0, value: 500, time: "2026-09-17T20:00:00Z" }] },
  } } } };
  expect(controllerMetric(model, "cpu").text).toBe("0 DMIPS");
  model.data!.monitoring!.value!.cpu!.unit = null;
  expect(controllerMetric(model, "cpu").text).toBe("0 · unit not specified");
  model.error = true; expect(controllerMetric(model, "cpu").lastKnown).toBe(true);
  model.data!.monitoring!.value!.cpu!.value!.push({ nodeId: "node-b", value: 5, time: "2026-09-17T20:00:00Z" });
  expect(controllerMetric(model, "cpu").text).toBe("2 node samples");
});
