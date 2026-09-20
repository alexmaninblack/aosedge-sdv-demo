// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { afterEach, expect, test, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { backendSummary, type BackendModel } from "../../src/features/service-team/useBackendObservation";
import { BackendEvidence } from "../../src/features/service-team/BackendEvidence";
import { BackendSummary } from "../../src/app/StudioSummaryCards";
import { binding, nativeInstance, confirmedReset } from "./backendFixture";
const now = "2026-09-19T20:00:00.000Z";
function fixture(input = "STALE", team: "brake" | "tire" = "brake") {
  const scope = { ...binding, profile: team === "brake" ? "v3" : "v1" };
  const item = { backendReceivedAt: now, authority: "FUNCTION_TEAM_REPORTED_OBSERVATION", stale: false, clockSkew: false,
    deliveryState: "DURABLY_RECEIVED", message: { schemaVersion: 3, contractVersion: "3.0.0", messageType: team.toUpperCase() + "_FUNCTION_OBSERVATION",
      unitSystemUid: scope.unitSystemUid, unitRole: "VALIDATION", serviceInstance: nativeInstance, serviceVersion: scope.serviceVersion,
      serviceProfile: scope.profile, generation: 2, sequence: 10, observedAt: now, contentSha256: "a".repeat(64), content: {
        connection: input === "WAITING" ? "STARTING" : "CONNECTED", input: { state: input, reason: input === "STALE" ? "SOURCE_GAP" : input === "RECEIVING" ? "NONE" : input === "WAITING" ? "AWAITING_INPUT" : input === "INVALID" ? "INVALID_SAMPLE" : input === "ACCESS_DENIED" ? "ACCESS_DENIED" : "TRANSPORT_LOST" },
        activity: { state: "WAITING", reason: "NOT_QUALIFIED", episodeId: null },
        delivery: { state: "IDLE", queuedMessages: 0, lastReceiptAt: null }, advisory: { state: "WAITING", requestId: null }, lastResult: null } } };
  const model: BackendModel = { busy: false, error: false, refresh() {}, data: { team, state: "OBSERVED", source: "REAL_BACKEND_HTTP", observedAt: now,
    observations: { mockData: { state: "OBSERVED", data: { source: "VEHICLE_DATA", vehicleTelemetry: true, unitSystemUid: scope.unitSystemUid, counts: [], records: [] } },
      demoReset: { state: "OBSERVED", data: { schemaVersion: 1, unitSystemUid: scope.unitSystemUid, connected: true, command: null } },
      functionObservations: { state: "OBSERVED", data: { schemaVersion: 3, contractVersion: "3.0.0", resourceType: "FUNCTION_OBSERVATION",
        unitSystemUid: scope.unitSystemUid, items: [item], truncated: false } } } } };
  return { model, scope, item };
}
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
test.each(["brake", "tire"] as const)("%s card and dialog don't prescribe driving through a source gap", team => {
  vi.spyOn(Date, "now").mockReturnValue(Date.parse(now));
  const { model, scope } = fixture("STALE", team);
  render(<><BackendSummary team={team} model={model} binding={scope} version={scope.serviceVersion} />
    <BackendEvidence team={team} observation={model} binding={scope} expectedVersion={scope.serviceVersion} unitSystemUid={scope.unitSystemUid} /></>);
  expect(screen.getAllByText(`Source data is stale. Waiting for fresh input before the next ${team === "brake" ? "recording" : "driving exercise"}.`)).toHaveLength(2);
  expect(screen.queryByText(/Waiting for a qualifying braking episode|Waiting for a completed driving exercise/)).not.toBeInTheDocument();
});
test.each(["WAITING", "DISCONNECTED", "ACCESS_DENIED", "INVALID"])("%s input cannot invite a new drive", input => {
  vi.spyOn(Date, "now").mockReturnValue(Date.parse(now));
  const { model, scope } = fixture(input);
  const summary = backendSummary(model, "brake", scope.serviceVersion, scope);
  expect(summary.status).not.toBe("Waiting for braking result");
});
test("a receiving source can request qualifying driving, but old/release-mismatched reports cannot", () => {
  vi.spyOn(Date, "now").mockReturnValue(Date.parse(now));
  const { model, scope, item } = fixture("RECEIVING");
  expect(backendSummary(model, "brake", scope.serviceVersion, scope).status).toBe("Waiting for braking result");
  item.stale = true;
  expect(backendSummary(model, "brake", scope.serviceVersion, scope).status).toBe("Input not confirmed");
  item.stale = false; item.message.serviceVersion = "6.0.0";
  expect(backendSummary(model, "brake", scope.serviceVersion, scope).status).toBe("Input not confirmed");
});
test("a confirmed reset retains the no-new-result title without hiding stale input", () => {
  vi.spyOn(Date, "now").mockReturnValue(Date.parse(now));
  const { model, scope } = fixture();
  model.data!.observations.demoReset!.data!.command = confirmedReset(scope);
  const summary = backendSummary(model, "brake", scope.serviceVersion, scope);
  expect(summary.title).toBe("No new result after reset");
  expect(summary.status).toBe("Waiting for fresh input");
});

test("Reset copy scopes absence to the reset, keeps its date, and explains lost contact", () => {
  vi.spyOn(Date, "now").mockReturnValue(Date.parse(now));
  const { model, scope } = fixture("RECEIVING");
  const reset = model.data!.observations.demoReset!.data!;
  reset.command = confirmedReset(scope); reset.connected = false;
  render(<BackendEvidence team="brake" observation={model} binding={scope} expectedVersion={scope.serviceVersion} unitSystemUid={scope.unitSystemUid} />);
  expect(screen.getByText(/No new result for release .* after the confirmed reset/)).toBeVisible();
  expect(screen.queryByText(/No result for release .* yet/)).not.toBeInTheDocument();
  expect(screen.getByText(/Reset requires Brake V3 and a connected reset channel/)).toBeVisible();
  expect(screen.getByText(/Last reset confirmed for release/)).toBeVisible();
  expect(screen.queryByText("Earlier results remain in Records.")).not.toBeInTheDocument();
});

for (const team of ["brake", "tire"] as const) test.each(["PENDING", "EXPIRED", "FAILED", "REJECTED"])(`${team} %s reset does not deny retained results or hide its outcome when disconnected`, state => {
  vi.spyOn(Date, "now").mockReturnValue(Date.parse(now));
  const { model, scope } = fixture("RECEIVING", team);
  const reset = model.data!.observations.demoReset!.data!;
  reset.command = { ...confirmedReset(scope), state, result: null }; reset.connected = false;
  const records = model.data!.observations.mockData!.data!.records;
  records.push({ backendReceivedAt: now, deliveryState: "DURABLY_RECEIVED", message: {
    messageType: team === "brake" ? "BRAKE_HEALTH_ASSESSMENT" : "TIRE_HEALTH_ASSESSMENT",
    unitSystemUid: scope.unitSystemUid, serviceVersion: scope.serviceVersion,
    serviceInstance: nativeInstance, sourceEventTime: now, content: { currentBand: "INSPECTION_RECOMMENDED" },
  } });
  const title = state === "PENDING" ? "Reset pending" : "Reset outcome unconfirmed";
  const summary = backendSummary(model, team, scope.serviceVersion, scope);
  expect(summary.title).toBe(title); expect(summary.proof).toBeUndefined();
  expect(summary.status).not.toBe(summary.title);
  render(<BackendEvidence team={team} observation={model} binding={scope} expectedVersion={scope.serviceVersion} unitSystemUid={scope.unitSystemUid} />);
  expect(screen.getByRole("heading", { name: title })).toBeVisible();
  expect(screen.queryByText(/No result for release .* yet/)).not.toBeInTheDocument();
  if (state !== "PENDING") {
    expect(screen.getByText(new RegExp(`Reset ${state.toLowerCase()} · outcome unconfirmed`))).toBeVisible();
    expect(screen.getByText(new RegExp(`Reset requires ${team === "brake" ? "Brake V3" : "Tire V1"} and a connected reset channel`))).toBeVisible();
  }
  expect(records).toHaveLength(1);
});
test.each(["PENDING", "RETRYING", "BLOCKED"])("receiving input with %s delivery does not ask for another drive", delivery => {
  vi.spyOn(Date, "now").mockReturnValue(Date.parse(now));
  const { model, scope, item } = fixture("RECEIVING");
  item.message.content.delivery.state = delivery; item.message.content.delivery.queuedMessages = 2;
  expect(backendSummary(model, "brake", scope.serviceVersion, scope).status).toBe(delivery === "BLOCKED" ? "Delivery blocked" : "Delivery pending");
});
test.each(["PRE", "ACTIVE", "POST", "COMPLETED", "SKIPPED"])("current %s activity provides guidance instead of a generic wait", activity => {
  vi.spyOn(Date, "now").mockReturnValue(Date.parse(now));
  const { model, scope, item } = fixture("RECEIVING");
  item.message.content.activity.state = activity;
  item.message.content.activity.reason = activity === "SKIPPED" ? "INSUFFICIENT_SAMPLES" : "NONE";
  expect(backendSummary(model, "brake", scope.serviceVersion, scope).status).not.toBe("Waiting for braking result");
});
test("renewal is distinct from denied access and a backend outage never claims current input", () => {
  vi.spyOn(Date, "now").mockReturnValue(Date.parse(now));
  const { model, scope, item } = fixture("WAITING");
  item.message.content.connection = "REAUTHENTICATING"; item.message.content.input.reason = "REAUTHENTICATING";
  expect(backendSummary(model, "brake", scope.serviceVersion, scope).status).toBe("Renewing input access");
  model.error = true;
  expect(backendSummary(model, "brake", scope.serviceVersion, scope).guidance).toContain("Backend read failed");
});

test("V3 without a new assessment explains retained advisory without claiming a current warning or proof", () => {
  vi.spyOn(Date, "now").mockReturnValue(Date.parse(now));
  const { model, scope } = fixture("RECEIVING");
  render(<><BackendSummary team="brake" model={model} binding={scope} version={scope.serviceVersion} />
    <BackendEvidence team="brake" observation={model} binding={scope} expectedVersion={scope.serviceVersion} unitSystemUid={scope.unitSystemUid} /></>);
  expect(screen.getAllByText(/Brake V3 can continue advisory from a retained condition/)).toHaveLength(2);
  expect(backendSummary(model, "brake", scope.serviceVersion, scope).proof).toBeUndefined();
  expect(screen.queryByText("Inspection recommended")).not.toBeInTheDocument();
});

test.each(["STALE", "WAITING", "INVALID"])("%s input keeps its diagnostic guidance without retained-advisory copy", input => {
  vi.spyOn(Date, "now").mockReturnValue(Date.parse(now));
  const { model, scope } = fixture(input);
  expect(backendSummary(model, "brake", scope.serviceVersion, scope).continuityNote).toBeUndefined();
});

test("a confirmed current reset never implies a retained condition", () => {
  vi.spyOn(Date, "now").mockReturnValue(Date.parse(now));
  const { model, scope } = fixture("RECEIVING");
  model.data!.observations.demoReset!.data!.command = confirmedReset(scope);
  expect(backendSummary(model, "brake", scope.serviceVersion, scope).continuityNote).toBeUndefined();
});

test("status-only history is not advertised as earlier assessments", () => {
  vi.spyOn(Date, "now").mockReturnValue(Date.parse(now));
  const { model, scope } = fixture("RECEIVING", "tire");
  model.data!.observations.mockData!.data!.records.push({ backendReceivedAt: now,
    message: { messageType: "TIRE_FUNCTION_STATUS", serviceVersion: scope.serviceVersion, unitSystemUid: scope.unitSystemUid } });
  render(<BackendEvidence team="tire" observation={model} binding={scope} expectedVersion={scope.serviceVersion} unitSystemUid={scope.unitSystemUid} />);
  expect(screen.queryByText("Earlier results remain in Records.")).not.toBeInTheDocument();
  expect(screen.getByText("Service records remain in Records.")).toBeVisible();
});
