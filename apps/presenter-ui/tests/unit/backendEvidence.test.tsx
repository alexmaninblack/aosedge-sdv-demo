import { afterEach, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { BackendEvidence } from "../../src/features/service-team/BackendEvidence";

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
const observation = (uid = "current-test") => ({state:"OBSERVED",team:"brake",source:"REAL_BACKEND_HTTP",observedAt:"2026-09-11T22:00:00Z",
  observations:{readiness:{state:"OBSERVED",data:{ready:true}},mockData:{state:"OBSERVED",data:{source:"DEMO_MOCK",vehicleTelemetry:false,unitSystemUid:uid,
    counts:[{kind:"assessment",count:2}],records:[{backendReceivedAt:"2026-09-11T21:59:00Z",message:{messageType:"brake.health.assessment",serviceVersion:"7.0.0",unitSystemUid:uid}}]}}}});

test("real backend evidence stays explicitly synthetic and uses only same-origin Demo Control", async () => {
  const fetch = vi.fn().mockResolvedValue({ok:true,json:async()=>observation()}); vi.stubGlobal("fetch",fetch);
  render(<BackendEvidence team="brake" unitSystemUid="current-test" />);
  expect(await screen.findByText("brake.health.assessment")).toBeVisible();
  expect(screen.getByText("MOCK DATA · Real service → real backend")).toBeVisible();
  expect(screen.getByText("Not connected")).toBeVisible();
  expect(screen.getByText("2")).toBeVisible();
  expect(fetch).toHaveBeenCalledWith("/api/presenter/backend/brake",expect.objectContaining({cache:"no-store"}));
});

test("wrong Test identity is never presented as received evidence", async () => {
  vi.stubGlobal("fetch",vi.fn().mockResolvedValue({ok:true,json:async()=>observation("other-unit")}));
  render(<BackendEvidence team="brake" unitSystemUid="current-test" />);
  expect(await screen.findByText(/Backend unavailable/)).toBeVisible();
  expect(screen.queryByText("brake.health.assessment")).not.toBeInTheDocument();
  expect(screen.getByText("Not confirmed")).toBeVisible();
});

test("failed manual refresh retains last-known records; identity change clears them", async () => {
  const fetch=vi.fn().mockResolvedValueOnce({ok:true,json:async()=>observation()})
    .mockRejectedValue(new Error("offline"));
  vi.stubGlobal("fetch",fetch);
  const view=render(<BackendEvidence team="brake" unitSystemUid="current-test" />);
  expect(await screen.findByText("brake.health.assessment")).toBeVisible();
  fireEvent.click(screen.getByRole("button",{name:"Refresh backend"}));
  expect(await screen.findByText(/Backend unavailable/)).toBeVisible();
  expect(screen.getByText("brake.health.assessment")).toBeVisible();
  expect(screen.getByText("Stored mock messages · last known")).toBeVisible();
  view.rerender(<BackendEvidence team="brake" />);
  await waitFor(()=>expect(screen.queryByText("brake.health.assessment")).not.toBeInTheDocument());
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
