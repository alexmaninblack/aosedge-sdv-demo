import { afterEach, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { BackendEvidence as Evidence } from "../../src/features/service-team/BackendEvidence";
import type { ComponentProps } from "react";
import { binding, nativeInstance, confirmedReset } from "./backendFixture";
import { PresenterControls } from "../../src/app/state/PresenterControls";
import { stamp } from "../../src/app/StudioReadViews";
const BackendEvidence = (props: ComponentProps<typeof Evidence>) => <Evidence binding={props.unitSystemUid ? { ...binding, unitSystemUid: props.unitSystemUid } : undefined} {...props} />;

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
const observation = (uid = "current-test") => ({state:"OBSERVED",team:"brake",source:"REAL_BACKEND_HTTP",observedAt:"2026-09-11T22:00:00Z",
  observations:{readiness:{state:"OBSERVED",data:{ready:true}},mockData:{state:"OBSERVED",data:{source:"DEMO_MOCK",vehicleTelemetry:false,unitSystemUid:uid,
    counts:[{kind:"assessment",count:2}],records:[{backendReceivedAt:"2026-09-11T21:59:00Z",message:{messageType:"brake.health.assessment",serviceVersion:"7.0.0",unitSystemUid:uid}}]}}}});

const realObservation = (uid = "current-test") => {
  const value = observation(uid);
  const page = (items: unknown[] = []) => ({ state: "OBSERVED", data: { unitSystemUid: uid, items } });
  return { ...value, observations: { ...value.observations, productData: page(), events: page(), advisories: page(), functionStatus: page(),
    demoReset: { state: "OBSERVED", data: { schemaVersion: 1, unitSystemUid: uid, connected: true, command: null } },
    assessments: page([{ backendReceivedAt: "2026-09-11T21:59:00Z", deliveryState: "DURABLY_RECEIVED", message: {
      serviceInstance: nativeInstance, sourceEventTime: "2026-09-11T21:58:59.000Z",
      messageType: "BRAKE_HEALTH_ASSESSMENT", serviceVersion: "7.0.0", unitSystemUid: uid,
    } }]),
  } };
};

test("mock history requires explicit selection and cannot qualify the real-data story", async () => {
  const fetch = vi.fn().mockResolvedValue({ok:true,json:async()=>observation()}); vi.stubGlobal("fetch",fetch);
  const onEvidence = vi.fn();
  render(<BackendEvidence team="brake" unitSystemUid="current-test" expectedVersion="7.0.0" onEvidence={onEvidence} />);
  expect(await screen.findByText(/Partial backend read/)).toBeVisible();
  expect(screen.queryByText("brake.health.assessment")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Show mock history" }));
  expect(await screen.findByText("brake.health.assessment")).toBeVisible();
  expect(screen.getByText("MOCK DATA · Explicit synthetic test records")).toBeVisible();
  expect(screen.getByText("See vehicle telemetry")).toBeVisible();
  expect(screen.getByText("2")).toBeVisible();
  expect(onEvidence).not.toHaveBeenCalled();
  expect(fetch).toHaveBeenCalledWith("/api/presenter/backend/brake",expect.objectContaining({cache:"no-store"}));
});

test("wrong Test identity is never presented as received evidence", async () => {
  vi.stubGlobal("fetch",vi.fn().mockResolvedValue({ok:true,json:async()=>observation("other-unit")}));
  render(<BackendEvidence team="brake" unitSystemUid="current-test" />);
  expect(await screen.findByText(/Backend unavailable/)).toBeVisible();
  expect(screen.queryByText("brake.health.assessment")).not.toBeInTheDocument();
  expect(screen.getAllByText("Not confirmed")).toHaveLength(3);
});

test("reset-channel inactivity is not labelled as general service contact", async () => {
  const value = realObservation();
  value.observations.demoReset.data.connected = false;
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => value }));
  render(<BackendEvidence team="brake" unitSystemUid="current-test" expectedVersion="7.0.0" />);
  expect(await screen.findByText("BRAKE HEALTH ASSESSMENT")).toBeVisible();
  expect(screen.getByText(/Reset channel contact: not recent/)).toBeVisible();
  expect(screen.queryByText(/Service contact:/)).not.toBeInTheDocument();
  expect(screen.getByText(/Reset requires Brake V3 and a connected reset channel/)).toBeVisible();
  expect(screen.getByRole("button", { name: "Reset demo scenario" })).toBeDisabled();
});

test.each([
  [null, "20 samples · 2 chunks received · total pending"],
  [undefined, "20 samples · 2 chunks received · total pending"],
  [5, "20 samples · 2/5 chunks"],
])("partial window does not render an absent chunk total (%s)", async (total, label) => {
  const value = realObservation();
  value.observations.assessments.data.items = [];
  value.observations.productData.data.items = [{ backendReceivedAt: "2026-09-11T21:59:00Z",
    serviceInstance: nativeInstance, windowStartTimestamp: "2026-09-11T21:58:59.000Z",
    deliveryState: "DURABLY_RECEIVED", serviceVersion: "7.0.0", unitSystemUid: "current-test",
    receivedSampleCount: 20, receivedChunkCount: 2, expectedChunkCount: total }];
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ok: true, json: async () => value}));
  render(<BackendEvidence team="brake" unitSystemUid="current-test" expectedVersion="7.0.0" />);
  expect(await screen.findByText(label)).toBeVisible();
});

test("failed manual refresh retains last-known records; identity change clears them", async () => {
  const fetch=vi.fn().mockResolvedValueOnce({ok:true,json:async()=>realObservation()})
    .mockRejectedValue(new Error("offline"));
  vi.stubGlobal("fetch",fetch);
  const view=render(<BackendEvidence team="brake" unitSystemUid="current-test" expectedVersion="7.0.0" />);
  expect(await screen.findByText("BRAKE HEALTH ASSESSMENT")).toBeVisible();
  fireEvent.click(screen.getByRole("button",{name:"Refresh backend"}));
  expect(await screen.findByText(/Backend unavailable/)).toBeVisible();
  expect(screen.getByText("BRAKE HEALTH ASSESSMENT")).toBeVisible();
  expect(screen.getByText("Latest product result · last known")).toBeVisible();
  view.rerender(<BackendEvidence team="brake" />);
  await waitFor(()=>expect(screen.queryByText("BRAKE HEALTH ASSESSMENT")).not.toBeInTheDocument());
  expect(screen.getByText("Current Test identity not observed in Cloud")).toBeVisible();
  expect(fetch).toHaveBeenCalledTimes(2);
});

test("no current Test identity means no endpoint call", async () => {
  const fetch=vi.fn();vi.stubGlobal("fetch",fetch);
  render(<BackendEvidence team="tire" />);
  await waitFor(()=>expect(screen.getByText("Current Test identity not observed in Cloud")).toBeVisible());
  expect(fetch).not.toHaveBeenCalled();
});

test("mock-labelled vehicle telemetry is rejected", async () => {
  const value=observation();value.observations.mockData.data.vehicleTelemetry=true;
  vi.stubGlobal("fetch",vi.fn().mockResolvedValue({ok:true,json:async()=>value}));
  render(<BackendEvidence team="brake" unitSystemUid="current-test" />);
  expect(await screen.findByText(/Backend unavailable/)).toBeVisible();
  expect(screen.queryByText("brake.health.assessment")).not.toBeInTheDocument();
});

test("Tire result uses its actual confidence, source time and content provenance fields", async () => {
  const sourceTime = "2026-09-13T12:10:08.150Z";
  const value = { ...realObservation(), team: "tire" };
  const received = value.observations.assessments.data.items[0] as { message: Record<string, unknown> };
  Object.assign(received.message, {
    messageType: "TIRE_HEALTH_ASSESSMENT", sourceEventTime: sourceTime,
    content: { conditionScore: 40, confidencePercent: 75, currentBand: "INSPECTION_RECOMMENDED", provenance: "DEMO_SYNTHETIC" },
  });
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => value }));
  render(<BackendEvidence team="tire" unitSystemUid="current-test" expectedVersion="7.0.0" />);
  expect(await screen.findByText("Confidence · 75%")).toBeVisible();
  expect(screen.getByText(stamp(sourceTime))).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Inspect latest result ↗" }));
  expect(screen.getByRole("dialog")).toHaveTextContent("DEMO SYNTHETIC");
});

test("Tire function failure and staleness remain visible without qualifying analytics", async () => {
  const value = { ...realObservation(), team: "tire" };
  value.observations.assessments.data.items = [];
  value.observations.functionStatus.data.items = [{ backendReceivedAt: "2026-09-15T21:24:21Z", stale: true,
    deliveryState: "DURABLE_ACCEPTED", message: { unitSystemUid: "current-test", serviceVersion: "7.0.0",
      messageType: "TIRE_FUNCTION_STATUS", observedAt: "2026-09-15T21:24:20Z",
      content: { functionalState: "NOT_READY", reason: "SERVICE_ACCESS_DENIED" } } }];
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => value }));
  const onEvidence = vi.fn();
  render(<BackendEvidence team="tire" unitSystemUid="current-test" expectedVersion="7.0.0" onEvidence={onEvidence} />);
  expect(await screen.findByText("Legacy function report · stale report: NOT READY · SERVICE ACCESS DENIED")).toBeVisible();
  expect(onEvidence).not.toHaveBeenCalled();
  expect(screen.getByText("No result yet")).toBeVisible();
  expect(screen.queryByRole("button", { name: "Inspect latest result ↗" })).not.toBeInTheDocument();
});

test("reset waits for CLEAR and keeps late historical warnings out of the current result", async () => {
  const base = realObservation();
  Object.assign((base.observations.assessments.data.items[0] as { message: Record<string, unknown> }).message, {
    sourceEventTime: "2026-09-11T21:58:00Z", content: {currentBand: "INSPECTION_RECOMMENDED"},
  });
  const command = { ...confirmedReset(), state: "PENDING", result: null as unknown };
  const value = {...base, observations: {...base.observations, demoReset: {state: "OBSERVED", data: {schemaVersion: 1, unitSystemUid: "current-test", connected: true, command}}}};
  vi.stubGlobal("fetch", vi.fn().mockImplementation(async () => ({ok: true, json: async () => value})));
  render(<BackendEvidence team="brake" unitSystemUid="current-test" expectedVersion="7.0.0" />);
  expect(await screen.findByText("Resetting · waiting for Gateway CLEAR confirmation")).toBeVisible();
  expect(screen.queryByText("INSPECTION RECOMMENDED")).not.toBeInTheDocument();
  expect(screen.getByRole("button", {name: "Reset demo scenario"})).toBeDisabled();
  Object.assign(command, confirmedReset());
  fireEvent.click(screen.getByRole("button", {name: "Refresh backend"}));
  expect(await screen.findByText(/Scenario reset · Gateway confirmed CLEAR/)).toBeVisible();
  expect(screen.queryByText("INSPECTION RECOMMENDED")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", {name: "Records"}));
  expect(screen.getByText("BRAKE_HEALTH_ASSESSMENT")).toBeVisible();
});

test("a submitted reset does not display the previous command as its completion", async () => {
  const base = realObservation();
  const value = {...base, observations: {...base.observations, demoReset: {state: "OBSERVED", data: {
    schemaVersion: 1, unitSystemUid: "current-test", connected: true,
    command: {commandId: "previous", unitSystemUid: "current-test", state: "CLEARED", issuedAt: "2026-09-11T22:00:00Z", expiresAt: "2026-09-11T22:01:00Z"},
  }}}};
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ok: true, json: async () => value}));
  const session = {sessionId: "test-session", active: "new-request", uncertain: false, jobs: [{
    id: "new-request", action: "backend-reset" as const, team: "brake" as const,
    state: "RUNNING", startedAt: "2026-09-11T22:02:00Z", progress: [], results: [],
  }]};
  const port = {read: vi.fn().mockResolvedValue(session), submit: vi.fn()};
  render(<PresenterControls port={port}><BackendEvidence team="brake" unitSystemUid="current-test" expectedVersion="7.0.0" /></PresenterControls>);
  expect(await screen.findByText("Resetting · submitting the current request")).toBeVisible();
  await waitFor(() => expect(screen.getByText(/Backend checked/)).toBeVisible());
  expect(screen.queryByText(/Scenario reset · Gateway confirmed CLEAR/)).not.toBeInTheDocument();
  expect(screen.getByRole("button", {name: "Reset demo scenario"})).toBeDisabled();
});
