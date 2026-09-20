// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { afterEach, expect, test, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { BackendSummary } from "../../src/app/StudioSummaryCards";
import { ComponentDetails, ServiceRows, Monitoring } from "../../src/app/StudioReadViews";
import { BackendEvidence, ProductRecordDetails } from "../../src/features/service-team/BackendEvidence";
import { backendSummary, mergeProductResources, type BackendModel, type BackendObservation } from "../../src/features/service-team/useBackendObservation";
import { componentPending, componentUpdateLabel, serviceRunning } from "../../src/domain/softwareObservation";
import { FinishAcknowledgement } from "../../src/app/FinishAcknowledgement";
import type { CloudComponent, CloudService } from "../../src/domain/platformObservation";
import type { DemoJob } from "../../src/domain/presenterCommandPort";
import { binding, nativeInstance } from "./backendFixture";

afterEach(() => { cleanup(); vi.useRealTimers(); });
const old = "2026-09-17T10:00:00.000Z", checked = "2026-09-19T10:00:00.000Z";
const result = () => ({ backendReceivedAt: old, deliveryState: "DURABLY_RECEIVED", message: {
  messageType: "BRAKE_HEALTH_ASSESSMENT", unitSystemUid: binding.unitSystemUid, serviceVersion: binding.serviceVersion,
  serviceInstance: nativeInstance, sourceEventTime: old, content: { currentBand: "GOOD", conditionScore: 100, quality: "VALID" },
} });
function incoming(): BackendObservation {
  const page = (items: unknown[] = []) => ({ state: "OBSERVED", data: { unitSystemUid: binding.unitSystemUid, items } });
  return { state: "OBSERVED", team: "brake", source: "REAL_BACKEND_HTTP", observedAt: checked, observations: {
    ...Object.fromEntries(["productData", "events", "advisories"].map(key => [key, page()])), assessments: page([result()]),
    demoReset: { state: "OBSERVED", data: { schemaVersion: 1, unitSystemUid: binding.unitSystemUid, connected: true, command: null } },
    functionObservations: { state: "OBSERVED", data: { schemaVersion: 3, contractVersion: "3.0.0", resourceType: "FUNCTION_OBSERVATION",
      unitSystemUid: binding.unitSystemUid, truncated: false, items: [{ backendReceivedAt: checked,
        authority: "FUNCTION_TEAM_REPORTED_OBSERVATION", stale: false, clockSkew: false, deliveryState: "DURABLY_RECEIVED",
        message: { schemaVersion: 3, contractVersion: "3.0.0", messageType: "BRAKE_FUNCTION_OBSERVATION", unitSystemUid: binding.unitSystemUid,
          unitRole: "VALIDATION", serviceVersion: binding.serviceVersion, serviceProfile: "v3", serviceInstance: nativeInstance,
          generation: 2, sequence: 1, observedAt: checked, contentSha256: "a".repeat(64), content: {
            connection: "CONNECTED", input: { state: "RECEIVING", reason: "NONE" }, activity: { state: "WAITING", reason: "NOT_QUALIFIED", episodeId: null },
            delivery: { state: "IDLE", queuedMessages: 0, lastReceiptAt: null }, advisory: { state: "WAITING", requestId: null }, lastResult: null,
          } } }] } },
  } } as BackendObservation;
}
function model(value = incoming(), prior: BackendObservation | null = null): BackendModel {
  return { data: mergeProductResources(value, prior, "brake", binding.unitSystemUid), error: false, busy: false, refresh() {} };
}
test.each([true, false])("F1 retained receipt keeps its age and current binding=%s qualification", current => {
  vi.useFakeTimers(); vi.setSystemTime(new Date(checked));
  const value = model(); render(<BackendSummary team="brake" model={value} version={binding.serviceVersion} binding={{ ...binding, current }} />);
  const receipt = screen.getByText(/Latest result received/);
  expect(receipt.querySelector("[title]")).toHaveAttribute("title", old);
  expect(screen.getByText(/Backend checked/).querySelector("[title]")).toHaveAttribute("title", checked);
  expect(screen.queryByText("Observed ·")).not.toBeInTheDocument();
  expect(backendSummary(value, "brake", binding.serviceVersion, { ...binding, current }).proof).toBe(current ? binding.serviceVersion : undefined);
  if (!current) expect(screen.getByText("Good · last known")).toBeVisible();
});
const component = (status: string | null): CloudComponent => ({ type: "demo-vehicle-data-provider", reported_component_id: "vdp", installed_component: { version: "8.0.0" }, pending_component: null, pending_component_status: status, runtimeState: "NOT_REPORTED_BY_CLOUD" });
test.each(["downloading", "pending", "installing"])("F2 status-only %s remains pending in component details", status => {
  const row = component(status); expect(componentPending(row)).toBe(true);
  render(<ComponentDetails row={row} current />);
  expect(screen.getByText("Update in progress · version not reported")).toBeVisible();
  expect(screen.queryByText(/No pending|None reported/)).not.toBeInTheDocument();
});
test("F2 failure/stale/completed remain distinct", () => {
  expect(componentUpdateLabel(component("failed"), false)).toBe("Update issue · failed · last known");
  expect(componentPending(component("completed"))).toBe(false);
  expect(componentUpdateLabel(component(null), true)).toBe("No pending release");
});
test("F3/F4 numeric instance errors prevent running and are shown as runtime evidence, not an update cause", () => {
  const row: CloudService = { reportReadCompletedAt: checked, subject: "subject", service: { id: "service", title: "Brake Health" }, num_instance: 1,
    service_versions: { installed_service_version: { version: "7.0.0" }, pending_service_version: null }, instances: { state: "CURRENT", value: [
      { instance_id: 0, version: "7.0.0", run_state: "active", error_message: null, error_aos_code: 42, error_exit_code: 137 } ] } };
  expect(serviceRunning(row, "7.0.0", true)).toBe(false);
  render(<ServiceRows rows={{ state: "CURRENT", value: [row] }} />);
  expect(screen.getByText(/Instance issue: Aos error 42 · Exit code 137/)).toBeVisible();
  expect(screen.getByText(/Cloud checked/)).toBeVisible();
  expect(screen.queryByText(/Service update issue|Cloud report/)).not.toBeInTheDocument();
  Object.assign(row.instances.value![0], { error_aos_code: 0, error_exit_code: 0 });
  expect(serviceRunning(row, "7.0.0", true)).toBe(true);
});
test("F5/O5 alternate disk data keeps parameter, node, Subject, instance and unknown units", () => {
  render(<Monitoring observation={{ error: false, busy: false, reason: null, refresh() {}, data: { readCompletedAt: checked, monitoring: { state: "CURRENT", value: {
    usedDisk: { state: "UNKNOWN", value: null, reason: "NOT_REPORTED" }, disk: { state: "CURRENT", unit: null, value: [
      { value: 12345, time: old, nodeId: "node-a", subjectId: "subject-a", serviceId: "brake", instance: 0, partition: "p1", parameter: "disk" },
      { value: 23456, time: old, nodeId: "node-b", subjectId: "subject-b", serviceId: "brake", instance: 0, partition: "p2", parameter: "disk" },
    ] } } } } }} />);
  fireEvent.click(screen.getByRole("button", { name: /^Disk$/ }));
  expect(screen.getByText("12345 · unit not specified")).toBeVisible();
  expect(screen.getByText("Node: node-a · Subject: subject-a")).toBeVisible();
  expect(screen.getByText("Node: node-b · Subject: subject-b")).toBeVisible();
  expect(screen.getAllByText("Parameter: disk")).toHaveLength(2);
  expect(screen.queryByText("NOT_REPORTED")).not.toBeInTheDocument();
});
test.each(["advisories", "demoReset"])("L2 %s failure retains valid products and independent function, but not story proof", name => {
  vi.useFakeTimers(); vi.setSystemTime(new Date(checked));
  const initial = model(), value = incoming();
  Object.assign(value.observations, { [name]: { state: "UNAVAILABLE" } }); value.state = "PARTIAL";
  const next = model(value, initial.data);
  const summary = backendSummary(next, "brake", binding.serviceVersion, binding);
  expect(summary.result).toBeDefined(); expect(summary.proof).toBeUndefined();
  expect(summary.functional.state).toBe("CURRENT");
  expect(next.data?.partialResources).toContain(name);
  expect(summary.lastKnown).toBe(name !== "demoReset");
});
test("L2 function failure does not invalidate products; failed aggregate cannot claim current function", () => {
  const value = incoming(); value.observations.functionObservations!.state = "UNAVAILABLE";
  const next = model(value); expect(backendSummary(next, "brake", binding.serviceVersion, binding).proof).toBe(binding.serviceVersion);
  next.error = true; expect(backendSummary(next, "brake", binding.serviceVersion, binding).proof).toBeUndefined();
  expect(backendSummary(next, "brake", binding.serviceVersion, binding).functional.state).not.toBe("CURRENT");
});
test("L2 wrong Unit in partial products is rejected rather than merged", () => {
  const value = incoming(); Object.assign(value.observations, { assessments: { state: "OBSERVED", data: { unitSystemUid: "other", items: [] } } });
  expect(() => model(value)).toThrow(/SCOPE/);
});
test("F7/O4 V1 is acquisition, model scores have a consistent accessible name", () => {
  const view = render(<BackendEvidence team="brake" expectedVersion={binding.serviceVersion} binding={{ ...binding, profile: "v1" }} observation={model()} />);
  expect(screen.getByText(/V1 source recording · no condition estimate/)).toBeVisible();
  expect(screen.queryByText(/Demo model estimates/)).not.toBeInTheDocument();
  view.rerender(<BackendEvidence team="brake" expectedVersion={binding.serviceVersion} binding={binding} observation={model()} />);
  expect(screen.getByRole("meter", { name: "Demo model condition score" })).toBeVisible();
});
test("O6 readable result fields include zero scores and explicit recommendation", () => {
  const row = result(); Object.assign(row.message.content, { conditionScore: 0, recommendation: "INSPECTION_RECOMMENDED", reasonCode: "WEAR" });
  render(<ProductRecordDetails row={row} />);
  expect(screen.getByText("0")).toBeVisible(); expect(screen.getByText("INSPECTION RECOMMENDED")).toBeVisible(); expect(screen.getByText("WEAR")).toBeVisible();
});
test.each(["BRAKE_HEALTH_ASSESSMENT", "WINDOW_COMPLETION"])("U1 %s conflict is explicit across summary, overview and history", messageType => {
  const value = model();
  const row = value.data!.observations.mockData!.data!.records[0];
  row.deliveryState = "CONFLICT"; row.message.messageType = messageType;
  Object.assign(row.message.content as object, { status: "COMPLETE" });
  // An older healthy record must not silently replace the conflicting head.
  value.data!.observations.mockData!.data!.records.push({ ...result(), message: { ...result().message, sourceEventTime: "2026-09-16T10:00:00Z" } });
  const summary = backendSummary(value, "brake", binding.serviceVersion, binding);
  expect(summary.proof).toBeUndefined();
  expect(summary.status).toBe("Result conflict");
  const card = render(<BackendSummary team="brake" model={value} version={binding.serviceVersion} binding={binding} />);
  expect(screen.getByText("Result conflict")).toBeVisible();
  expect(screen.queryByText("Good")).not.toBeInTheDocument();
  card.unmount();
  render(<BackendEvidence team="brake" expectedVersion={binding.serviceVersion} binding={binding} observation={value} />);
  expect(screen.getByRole("heading", { name: "Result not trusted" })).toBeVisible();
  expect(screen.queryByRole("meter")).not.toBeInTheDocument();
  expect(screen.getByText(/Conflicting content/)).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Records" }));
  expect(screen.getByText("Current Test · CONFLICT")).toBeVisible();
});
test("O3 known empty setup does not masquerade as an observation failure", () => {
  render(<BackendSummary team="brake" model={model()} noController />);
  expect(screen.getByText("No controller created")).toBeVisible(); expect(screen.queryByText("Not reported")).not.toBeInTheDocument();
});
test("O2 acknowledgement requires a recent completed retirement receipt and expires without storage", () => {
  vi.useFakeTimers(); vi.setSystemTime(new Date(checked));
  const job: DemoJob = { id: "finish", action: "reset", state: "COMPLETED", startedAt: old, finishedAt: checked, progress: [], results: [] };
  const view = render(<FinishAcknowledgement jobs={[job]} noController />);
  expect(screen.queryByText("Demo finished")).not.toBeInTheDocument();
  job.results = [{ operation: "demo.retire", state: "COMPLETED", message: "Owned Test retired", facts: {} }];
  view.rerender(<FinishAcknowledgement jobs={[job]} noController />);
  expect(screen.getByText("Demo finished")).toBeVisible();
  act(() => vi.advanceTimersByTime(61000)); expect(screen.queryByText("Demo finished")).not.toBeInTheDocument();
});
